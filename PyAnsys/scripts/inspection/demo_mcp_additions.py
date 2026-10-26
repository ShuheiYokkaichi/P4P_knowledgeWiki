"""Real Fluent/MCP demonstration; no mocks, fixtures, or unit-test acceptance.

Call ``await demonstrate(solver, server, runtime_dir)`` from the persistent
direct-fluent-use controller after its machine/version gate. The supplied
server is the unmodified official SolveMCP with register_additions applied.
Its backend must be attached to this owned session. Client shutdown follows
the official lifecycle and exits Fluent. Save valuable state before calling.
"""
from __future__ import annotations

from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import platform

import numpy as np
from fastmcp import Client


async def demonstrate(solver, server, runtime_dir):
    work = Path(runtime_dir)
    out = work / ("demo-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    calls, checks = [], {}

    def dump(name, payload):
        (out / name).write_text(json.dumps(payload, indent=2, default=str, allow_nan=False), encoding="utf-8")

    package = Path(__file__).resolve().parents[2] / "src/pyansys_fluent/mcp_additions"
    dump("identity.json", {"python": sys.executable, "python_version": sys.version,
        "host": platform.node(), "fluent": str(solver.get_fluent_version()),
        "upstream_sha": "f56e540931fbcdf5b9f81871a21934589f256d91",
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in package.glob("*.py")},
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})

    async with Client(server) as client:
        tools = await client.list_tools()
        dump("schemas.json", [t.model_dump(mode="json") for t in tools])

        async def call(name, arguments, label=None):
            result = await client.call_tool(name, arguments, raise_on_error=False)
            raw = {"name": name, "arguments": deepcopy(arguments), "is_error": result.is_error,
                   "content": [c.model_dump(mode="json") for c in result.content],
                   "structured_content": deepcopy(result.structured_content)}
            calls.append(raw)
            dump("calls.json", calls)
            print("MCP_DEMO", label or name, "ERROR" if result.is_error else "RETURNED", flush=True)
            return result.structured_content or (json.loads(result.content[0].text) if not result.is_error else raw)

        chosen = ["cold-inlet", "hot-inlet", "outlet"]
        g = await call("surface_geometry", {"surfaces": chosen})
        checks["geometry"] = {}
        for name in chosen:
            area = float(solver.fields.reduction.area(locations=[name]))
            checks["geometry"][name] = {"native_area_m2": area,
                "returned_area_m2": g["surfaces"][name]["area_m2"],
                "native_centroid_m": list(solver.fields.reduction.centroid(locations=[name]))}
        await call("surface_geometry", {"surfaces": ["not-a-real-zone"]}, "geometry_missing_zone")
        fingerprint = await call("boundary_fingerprint", {"surfaces": chosen})
        solver.settings.mesh.scale(x_scale=1.01, y_scale=1, z_scale=1)
        changed = await call("boundary_fingerprint", {"surfaces": chosen}, "fingerprint_scaled_mesh")
        checks["fingerprint_changed"] = {n: fingerprint["surfaces"][n]["sha256"] != changed["surfaces"][n]["sha256"] for n in chosen}
        solver.settings.file.read_case(file_name=str(work / "baseline.cas.h5"))
        solver.settings.file.read_data(file_name=str(work / "baseline.dat.h5"))
        restored = await call("boundary_fingerprint", {"surfaces": chosen}, "fingerprint_reopened")
        checks["fingerprint_restored"] = fingerprint == restored

        summary = await call("surface_field_summary", {"surfaces": ["outlet"], "field": "temperature"})
        checks["field_native_extrema"] = {
            "minimum": float(solver.fields.reduction.minimum(expression="StaticTemperature", locations=["outlet"])),
            "maximum": float(solver.fields.reduction.maximum(expression="StaticTemperature", locations=["outlet"])),
            "summary": summary}
        dataset = await call("export_surface_data", {"surfaces": chosen, "field": "temperature", "output": str(out / "surfaces.npz")})
        with np.load(out / "surfaces.npz", allow_pickle=False) as arrays:
            checks["data_export"] = {name: {"faces": len(arrays[entry["prefix"] + "_values"]),
                "aligned": len(arrays[entry["prefix"] + "_values"]) == len(arrays[entry["prefix"] + "_centroids"])}
                for name, entry in dataset["surfaces"].items()}
        await call("export_surface_data", {"surfaces": chosen, "field": "temperature", "output": str(out / "too-small.npz"), "max_faces": 1}, "data_limit")

        await call("solver_progress", {"reference_surface": "cold-inlet"}, "progress_before")
        await call("read_live_monitor_history", {"monitor_set": "missing-monitor"}, "missing_live_history")
        names = solver.settings.solution.monitor.report_files.get_object_names()
        routing = await call("route_report_files", {"names": names, "directory": str(out / "routed")})
        await call("route_report_files", {"names": names, "directory": str(out / "routed")}, "routing_refuses_existing")
        dump("routing.json", routing)

        # Disable automatic convergence stops for this fixed-budget demo. Each
        # equation's original criterion remains in the saved baseline pair.
        residual = solver.settings.solution.monitor.residual
        for equation in residual.equations.get_object_names():
            residual.equations[equation].check_convergence = False
        dump("demo-residual-settings.json", residual.get_state())
        # One uninterrupted fixed-input native command. The transcript/report
        # tail establishes the actual completed horizon.
        solver.settings.solution.run_calculation.iterate(iter_count=1000)
        progress = await call("solver_progress", {"reference_surface": "cold-inlet"}, "progress_after")
        history = await call("read_live_monitor_history", {"monitor_set": "mcp-outlet-temperature-rplot", "max_points": 5})
        dump("monitor-history.json", history)
        from pyansys_fluent.mcp_additions.histories import export_monitor_history_png
        checks["history_plot"] = export_monitor_history_png(history, str(out / "history.png"))

        # Routing must survive save/reopen and produce an actual native file.
        solver.settings.file.write_case(file_name=str(out / "result.cas.h5"))
        solver.settings.file.write_data(file_name=str(out / "result.dat.h5"))
        effective = solver.settings.solution.monitor.report_files.get_state()
        dump("report-files-after-solve.json", effective)
        # Fluent can rewrite absolute names relative to its launch directory
        # while saving. This controller runs in that same explicit directory.
        path = Path(next(iter(effective.values()))["file_name"]).resolve()
        checks["routed_file_exists"] = path.is_file()
        report = await call("read_report_file_history", {"path": str(path), "max_points": 1000})
        dump("report-history.json", report)
        native_copy = out / "native-report.out"
        shutil.copyfile(path, native_copy)
        await call("read_report_file_history", {"path": str(native_copy), "max_bytes": 256, "max_points": 3}, "bounded_file_tail")
        partial = out / "interrupted-report.out"
        partial.write_bytes(native_copy.read_bytes()[:-8])
        await call("read_report_file_history", {"path": str(partial)}, "interrupted_native_file_copy")

        # Join overlapping captures from the actual native report. Deliberate
        # omissions expose coverage gaps; no sample values are synthesized.
        rows = report["rows"]
        digest = hashlib.sha256(native_copy.read_bytes()).hexdigest()
        column = report["columns"][1]
        def segment(label, selected):
            return {"source_id": label, "sha256": digest,
                    "axis": {"name": report["coordinate_column"], "unit": "1"},
                    "units": {column: "K", "unrecorded-equation": "1"},
                    "x": [r[0] for r in selected], "series": {column: [r[1] for r in selected]}}
        cut = max(1, len(rows) // 2)
        joined = await call("join_history_segments", {"segments": [segment("first-capture", rows[:cut + 1]), segment("overlapping-capture", rows[cut:])], "expected_step": 1})
        checks["join_retains_native_values"] = joined["series"][column] == [r[1] for r in rows]
        if len(rows) > 4:
            await call("join_history_segments", {"segments": [segment("gap-left", rows[:2]), segment("gap-right", rows[-2:])], "expected_step": 1}, "join_gap")

        figure = await call("export_contour", {"surfaces": ["symmetry-xyplane"], "field": "temperature",
            "case_file": str(out / "result.cas.h5"), "data_file": str(out / "result.dat.h5"),
            "output": str(out / "temperature.png"), "minimum": 290, "maximum": 315, "view": "front"})
        dump("figure.json", figure)
        checks["routing_reopened"] = solver.settings.solution.monitor.report_files.get_state() == effective
        checks["final_progress"] = progress
        checks["no_temporary_contour"] = not any(n.startswith("mcp-figure-") for n in solver.settings.results.graphics.contour.get_object_names())
        dump("checks.json", checks)
        print("LIVE_DEMO_RECEIPT", out, flush=True)
    dump("cleanup.json", {"official_backend_connected_after_client_exit": server.backend.is_connected(),
                          "note": "Backend disconnection alone is not process-exit proof; verify owned Fluent process separately."})
    return str(out)


async def demonstrate_followup(solver, server, runtime_dir):
    """Qualify review repairs with saved fields and one transient smoke check."""
    work = Path(runtime_dir)
    source = work / "demo-20261026T062525Z"
    out = work / ("followup-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(exist_ok=False)
    calls, checks = [], {}
    def dump(name, value):
        (out / name).write_text(json.dumps(value, indent=2, default=str, allow_nan=False), encoding="utf-8")
    package = Path(__file__).resolve().parents[2] / "src/pyansys_fluent/mcp_additions"
    dump("identity.json", {"python": sys.executable, "fluent": str(solver.get_fluent_version()),
        "ui_mode": "hidden_gui", "graphics_driver": "msw", "source_pair": str(source),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in package.glob("*.py")}})
    async with Client(server) as client:
        dump("schemas.json", [t.model_dump(mode="json") for t in await client.list_tools()])
        async def call(name, args, label=None):
            result = await client.call_tool(name, args, raise_on_error=False)
            record = {"name": name, "label": label or name, "arguments": deepcopy(args),
                      "is_error": result.is_error,
                      "content": [c.model_dump(mode="json") for c in result.content],
                      "structured_content": deepcopy(result.structured_content)}
            calls.append(record)
            dump("calls.json", calls)
            print("FOLLOWUP", record["label"], "ERROR" if result.is_error else "RETURNED", flush=True)
            return result.structured_content or record

        names = solver.fields.field_data.surfaces.allowed_values()
        geometry = await call("surface_geometry", {"surfaces": names}, "geometry_curved_and_closed_set")
        checks["geometry"] = geometry
        reference = await call("boundary_fingerprint", {"surfaces": ["cold-inlet", "outlet"]})
        from pyansys_fluent.mcp_additions.geometry import _geometry
        def ordering():
            raw = _geometry(solver, ["cold-inlet"])["cold-inlet"]
            return {key: hashlib.sha256(np.asarray(getattr(raw, key)).tobytes()).hexdigest()
                    for key in ("vertices", "connectivity")}
        order_before = ordering()
        try:
            solver.settings.mesh.reorder.reorder_domain()
            checks["reorder"] = {"before": order_before, "after": ordering()}
            await call("boundary_fingerprint", {"surfaces": ["cold-inlet", "outlet"], "reference": reference}, "fingerprint_after_native_reorder")
        except Exception as exc:
            checks["reorder_error"] = str(exc)
        solver.settings.mesh.scale(x_scale=1.01, y_scale=1, z_scale=1)
        await call("boundary_fingerprint", {"surfaces": ["cold-inlet", "outlet"], "reference": reference}, "fingerprint_changed_comparison")
        solver.settings.file.read_case(file_name=str(source / "result.cas.h5"))
        solver.settings.file.read_data(file_name=str(source / "result.dat.h5"))

        dataset = await call("export_surface_data", {"surfaces": names, "field": "x-coordinate", "output": str(out / "coordinates.npz")})
        with np.load(out / "coordinates.npz", allow_pickle=False) as arrays:
            checks["pointwise_coordinate_error_m"] = {name: float(np.max(np.abs(
                arrays[r["prefix"] + "_values"] - arrays[r["prefix"] + "_centroids"][:, 0])))
                for name, r in dataset["surfaces"].items()}
        before_hash = hashlib.sha256((out / "coordinates.npz").read_bytes()).hexdigest()
        await call("export_surface_data", {"surfaces": names, "field": "x-coordinate", "output": str(out / "coordinates.npz")}, "data_overwrite_refused")
        checks["existing_dataset_preserved"] = before_hash == hashlib.sha256((out / "coordinates.npz").read_bytes()).hexdigest()

        figure = await call("export_contour", {"surfaces": ["symmetry-xyplane"], "field": "temperature",
            "case_file": str(source / "result.cas.h5"), "data_file": str(source / "result.dat.h5"),
            "output": str(out / "temperature.png"), "minimum": 290, "maximum": 315, "view": "front"})
        dump("figure.json", figure)

        solver.settings.setup.general.solver.time = "unsteady-2nd-order"
        controls = solver.settings.solution.run_calculation.transient_controls
        controls.time_step_size = 0.01
        solver.settings.solution.report_definitions.surface.create(name="mcp-outlet-pressure")
        solver.settings.solution.report_definitions.surface["mcp-outlet-pressure"].set_state({
            "report_type": "surface-areaavg", "field": "pressure", "surface_names": ["outlet"]})
        files = solver.settings.solution.monitor.report_files
        report_name = "mcp-outlet-temperature-rfile"
        files[report_name].report_defs = ["mcp-outlet-temperature", "mcp-outlet-pressure"]
        routes = await call("route_report_files", {"names": [report_name], "directory": str(out / "transient-reports")})
        dump("transient-settings.json", {"run": solver.settings.solution.run_calculation.get_state(),
             "reports": files.get_state(), "routing": routes})
        solver.settings.solution.run_calculation.dual_time_iterate(time_step_count=3, max_iter_per_step=5)
        history = await call("read_live_monitor_history", {"monitor_set": "mcp-outlet-temperature-rplot",
            "max_points": 5, "max_scan_points": 10, "output_prefix": str(out / "monitor"), "logarithmic": False}, "history_scan_cap_and_mcp_artifacts")
        dump("monitor-receipt.json", history)
        native_path = Path(files[report_name].file_name()).resolve()
        shutil.copyfile(native_path, out / "native-transient.out")
        recovered = await call("read_report_file_history", {"path": str(native_path), "max_points": 1000})
        dump("transient-history.json", recovered)
        if "flow-time" in recovered.get("columns", []):
            await call("read_report_file_history", {"path": str(native_path), "coordinate_column": "flow-time", "max_cells": 12}, "history_flow_time_coordinate_and_cell_cap")
        await call("solver_progress", {"reference_surface": "outlet"}, "native_physical_clock")

        # Preserve native restart rows: concatenate two authentic snapshots.
        raw = (out / "native-transient.out").read_bytes()
        lines = raw.splitlines(keepends=True)
        header_end = next(i for i, line in enumerate(lines) if line.lstrip().startswith(b"(")) + 1
        restart = out / "native-restarted-copy.out"
        restart.write_bytes(raw + b"".join(lines[header_end:]))
        await call("read_report_file_history", {"path": str(restart)}, "native_rows_with_reset")
        malformed = out / "native-interrupted-copy.out"
        malformed.write_bytes(raw + b"broken native file row\n" + lines[-1].split()[0] + b" ")
        await call("read_report_file_history", {"path": str(malformed)}, "native_copy_malformed_and_partial_rows")

        # Conflicting real observations at a repeated flow-time coordinate:
        # compare different inner iterations; no measured values are altered.
        rows, columns = recovered.get("rows", []), recovered.get("columns", [])
        if "flow-time" in columns and len(rows) >= 2:
            x_index = columns.index("flow-time")
            digest = hashlib.sha256(raw).hexdigest()
            segments = [{"source_id": "native-inner-row-" + str(i), "sha256": digest,
                "axis": {"name": "flow-time", "unit": "s"},
                "units": {columns[1]: "K", "not-recorded": "1"},
                "x": [r[x_index]], "series": {columns[1]: [r[1]]}} for i, r in enumerate(rows[:2])]
            await call("join_history_segments", {"segments": segments}, "native_repeated_time_conflict")
        solver.settings.file.write_case(file_name=str(out / "transient.cas.h5"))
        solver.settings.file.write_data(file_name=str(out / "transient.dat.h5"))
        dump("checks.json", checks)
    print("FOLLOWUP_RECEIPT", out, flush=True)
    return str(out)


async def demonstrate_contracts(solver, server, runtime_dir):
    """Current-source checks for schemas, artifacts, time axes and conflicts."""
    out = Path(runtime_dir) / ("contracts-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(exist_ok=False)
    calls, checks = [], {}
    def dump(name, value):
        path = out / name
        path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False), encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()
    package = Path(__file__).resolve().parents[2] / "src/pyansys_fluent/mcp_additions"
    import inspect
    import subprocess
    import ansys.fluent.mcp.solve.backends.pyfluent as upstream
    loaded_upstream = Path(inspect.getfile(upstream)).resolve()
    upstream_root = next(p for p in loaded_upstream.parents if (p / ".git").exists())
    dump("identity.json", {"fluent": str(solver.get_fluent_version()), "python": sys.version,
        "loaded_upstream_file": str(loaded_upstream),
        "loaded_upstream_file_sha256": hashlib.sha256(loaded_upstream.read_bytes()).hexdigest(),
        "upstream_sha": subprocess.check_output(["git", "-C", str(upstream_root), "rev-parse", "HEAD"], text=True).strip(),
        "upstream_status": subprocess.check_output(["git", "-C", str(upstream_root), "status", "--porcelain"], text=True),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in package.glob("*.py")}})
    async with Client(server) as client:
        dump("schemas.json", [t.model_dump(mode="json") for t in await client.list_tools()])
        async def call(name, args, label=None):
            result = await client.call_tool(name, args, raise_on_error=False)
            calls.append({"name": name, "label": label or name, "arguments": deepcopy(args),
                "is_error": result.is_error, "structured_content": deepcopy(result.structured_content),
                "content": [c.model_dump(mode="json") for c in result.content]})
            dump("calls.json", calls)
            print("CONTRACT", label or name, "ERROR" if result.is_error else "RETURNED", flush=True)
            return result.structured_content or calls[-1]

        names = solver.fields.field_data.surfaces.allowed_values()
        geometry = await call("surface_geometry", {"surfaces": names})
        checks["geometry_area_relative_errors"] = {name: abs(record["polygon_area_m2"] / record["area_m2"] - 1)
            for name, record in geometry["surfaces"].items()}
        # Native reordering changes serialization but must preserve the exact
        # multiset fingerprint. Then change the physical geometry and restore.
        from pyansys_fluent.mcp_additions.geometry import _geometry
        selected = ["cold-inlet", "outlet"]
        reference = await call("boundary_fingerprint", {"surfaces": selected})
        def raw_ordering():
            raw = _geometry(solver, ["cold-inlet"])["cold-inlet"]
            return {key: hashlib.sha256(np.asarray(getattr(raw, key)).tobytes()).hexdigest()
                    for key in ("vertices", "connectivity")}
        checks["raw_order_before"] = raw_ordering()
        solver.settings.mesh.reorder.reorder_domain()
        checks["raw_order_after"] = raw_ordering()
        reference["surfaces"]["cold-inlet"]["note"] = "caller baseline annotation"
        await call("boundary_fingerprint", {"surfaces": selected, "reference": reference}, "fingerprint_reordered_with_extra_metadata")
        restore_case = out / "geometry-restore.cas.h5"
        restore_data = out / "geometry-restore.dat.h5"
        solver.settings.file.write_case(file_name=str(restore_case))
        solver.settings.file.write_data(file_name=str(restore_data))
        solver.settings.mesh.scale(x_scale=1.01, y_scale=1, z_scale=1)
        await call("boundary_fingerprint", {"surfaces": selected, "reference": reference}, "fingerprint_scaled")
        solver.settings.file.read_case(file_name=str(restore_case))
        solver.settings.file.read_data(file_name=str(restore_data))
        await call("boundary_fingerprint", {"surfaces": selected, "reference": reference}, "fingerprint_restored")
        summary = await call("surface_field_summary", {"surfaces": ["outlet"], "field": "temperature"})
        checks["native_temperature_mean"] = float(solver.fields.reduction.area_average(
            expression="StaticTemperature", locations=["outlet"]))
        checks["polygon_temperature_mean"] = summary["surfaces"]["outlet"]["polygon_area_weighted_mean"]
        data = await call("export_surface_data", {"surfaces": names, "field": "x-coordinate",
            "sampling": "node", "output": str(out / "nodes.npz")})
        with np.load(out / "nodes.npz", allow_pickle=False) as arrays:
            checks["node_coordinate_max_error_m"] = {name: float(np.max(np.abs(
                arrays[r["prefix"] + "_values"] - arrays[r["prefix"] + "_vertices"][:, 0])))
                for name, r in data["surfaces"].items()}
        await call("export_surface_data", {"surfaces": names, "field": "temperature",
            "sampling": "face", "output": str(out / "nodes.npz")}, "refuse_existing_dataset")
        checks["dataset_hash_preserved"] = hashlib.sha256((out / "nodes.npz").read_bytes()).hexdigest() == data["artifact"]["sha256"]

        files = solver.settings.solution.monitor.report_files
        main = "mcp-outlet-temperature-rfile"
        files[main].report_defs = ["mcp-outlet-temperature", "mcp-outlet-pressure", "mcp-physical-time"]
        for name in ("mcp-paused", "mcp-unselected"):
            if name not in files.get_object_names():
                files.create(name=name)
            files[name].report_defs = ["mcp-outlet-temperature"]
            files[name].active = False
            files[name].frequency = 3
        untouched = files["mcp-unselected"].get_state()
        route = await call("route_report_files", {"names": [main, "mcp-paused"], "directory": str(out / "reports")})
        if route.get("status") != "routed":
            dump("routing-failure.json", route)
            raise RuntimeError("Routing failed; dependent solve was not started")
        checks["unselected_unchanged"] = untouched == files["mcp-unselected"].get_state()
        checks["inactive_and_frequency_preserved"] = files["mcp-paused"].active() is False and files["mcp-paused"].frequency() == 3
        await call("route_report_files", {"names": [main], "directory": str(out / "reports")}, "refuse_existing_routing_directory")
        # A real filesystem obstacle appears after directory creation, while
        # Fluent performs the first writes. This exercises native readback and
        # multi-object rollback without replacing any API with a test double.
        import threading
        import time
        obstruction = out / "obstructed-reports"
        stop_obstruction = threading.Event()
        def obstruct_second_path():
            while not obstruction.exists() and not stop_obstruction.wait(0.001):
                pass
            if obstruction.exists():
                (obstruction / "report-002.out").mkdir(exist_ok=True)
        worker = threading.Thread(target=obstruct_second_path, daemon=True)
        route_before_failure = {n: files[n].get_state() for n in (main, "mcp-paused")}
        worker.start()
        try:
            await call("route_report_files", {"names": [main, "mcp-paused"], "directory": str(obstruction)}, "native_filesystem_obstruction_rollback")
        finally:
            stop_obstruction.set()
            worker.join(timeout=5)
        checks["routing_rollback_states"] = {n: files[n].get_state() for n in (main, "mcp-paused")}
        checks["routing_rollback_before"] = route_before_failure
        before = await call("solver_progress", {"reference_surface": "outlet"})
        # A single short smoke check supplies enough native points to cross
        # the history reader's scan cap; settings stay fixed within the call.
        solver.settings.solution.run_calculation.dual_time_iterate(time_step_count=12, max_iter_per_step=1)
        await call("solver_progress", {"reference_surface": "outlet", "previous": before}, "progress_observation_delta")
        history = await call("read_live_monitor_history", {"monitor_set": "mcp-outlet-temperature-rplot",
            "max_points": 3, "max_scan_points": 10, "output_prefix": str(out / "snapshot")}, "bounded_history_with_artifacts")
        if "artifacts" in history:
            checks["snapshot_hashes"] = {kind: hashlib.sha256(Path(entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
                                        for kind, entry in history["artifacts"].items()}
        path = Path(route["effective_paths"][main])
        shutil.copyfile(path, out / "native-multicolumn.out")
        recovered = await call("read_report_file_history", {"path": str(path), "coordinate_column": "mcp-physical-time", "max_cells": 12})
        checks["fractional_time_axis"] = recovered
        full = await call("read_report_file_history", {"path": str(path), "coordinate_column": "mcp-physical-time"}, "complete_native_multicolumn")
        rows, columns = full["rows"], full["columns"]
        digest = hashlib.sha256((out / "native-multicolumn.out").read_bytes()).hexdigest()
        def native_slice(label, start, end):
            selected_rows = rows[start:end]
            return {"source_id": label, "sha256": digest,
                "axis": {"name": "physical-time", "unit": "s"},
                "units": {"temperature": "K", "unavailable": "1"},
                "x": [r[columns.index("mcp-physical-time")] for r in selected_rows],
                "series": {"temperature": [r[columns.index("mcp-outlet-temperature")] for r in selected_rows]},
                "source_rows": list(range(start, min(end, len(rows))))}
        await call("join_history_segments", {"segments": [native_slice("left", 0, 7), native_slice("right", 6, len(rows))],
            "expected_step": 0.01, "step_tolerance": 1e-12}, "native_overlapping_slices")
        await call("join_history_segments", {"segments": [native_slice("gap-left", 0, 2), native_slice("gap-right", len(rows)-2, len(rows))],
            "expected_step": 0.01, "step_tolerance": 1e-12}, "native_gap_slices")
        solver.settings.file.write_case(file_name=str(out / "before-patch.cas.h5"))
        solver.settings.file.write_data(file_name=str(out / "before-patch.dat.h5"))
        expected_routing = solver.settings.solution.monitor.report_files.get_state()

        # Two native report evaluations at the same physical time, separated
        # by a deliberate field patch, supply genuine conflicting observations.
        reports = ["mcp-outlet-temperature", "mcp-physical-time"]
        raw_before = solver.settings.solution.report_definitions.compute(report_defs=reports)
        hash_before = dump("observation-before.json", raw_before)
        try:
            solver.settings.solution.initialization.patch.calculate_patch(
                cell_zones=["elbow-fluid"], variable="temperature", value=310)
            await call("surface_field_summary", {"surfaces": ["outlet"], "field": "temperature",
                "reference": summary}, "shared_range_after_native_patch")
            await call("surface_field_summary", {"surfaces": ["outlet"], "field": "pressure",
                "reference": summary}, "reject_incompatible_range_reference")
            raw_after = solver.settings.solution.report_definitions.compute(report_defs=reports)
            hash_after = dump("observation-after.json", raw_after)
            def observed(source, raw, digest):
                measured = {k: v for block in raw if isinstance(block, dict) for k, v in block.items()}
                return {"source_id": source, "sha256": digest,
                    "axis": {"name": "physical-time", "unit": "s"},
                    "units": {"outlet-temperature": "K", "unavailable-channel": "1"},
                    "x": [measured["mcp-physical-time"][0]],
                    "series": {"outlet-temperature": [measured["mcp-outlet-temperature"][0]]}, "source_rows": [0]}
            segments = [observed("observation-before.json", raw_before, hash_before), observed("observation-after.json", raw_after, hash_after)]
            await call("join_history_segments", {"segments": segments}, "real_field_patch_conflict")
            segments[0]["stage"], segments[1]["stage"] = "before-patch", "after-patch"
            await call("join_history_segments", {"segments": segments}, "explicit_separate_stages")
            await call("join_history_segments", {"segments": segments, "max_rows": 1}, "join_budget_refusal")
        except Exception as exc:
            checks["native_patch_error"] = str(exc)
        solver.settings.file.write_case(file_name=str(out / "after-patch.cas.h5"))
        solver.settings.file.write_data(file_name=str(out / "after-patch.dat.h5"))
        figure_arguments = {"surfaces": ["symmetry-xyplane"], "field": "temperature",
            "case_file": str(out / "before-patch.cas.h5"), "data_file": str(out / "before-patch.dat.h5"),
            "output": str(out / "native-temperature.png"), "minimum": 290, "maximum": 315}
        # Warm the real upstream mesh cache, then force a native graphics
        # configuration error. Cache and file cleanup must also work on failure.
        checks["mesh_counts_before_figure"] = await server.backend.mesh_counts()
        checks["mesh_cache_populated_before_failure"] = bool(server.backend._pyfluent._mesh_cache)
        picture_before_figure = solver.settings.results.graphics.picture.get_state()
        await call("export_contour", {**figure_arguments, "view": "not-a-real-view"}, "figure_native_error")
        checks["mesh_cache_empty_after_failure"] = not server.backend._pyfluent._mesh_cache
        checks["failed_figure_outputs_absent"] = not any((out / ("native-temperature" + ext)).exists() for ext in (".png", ".json", ".vw"))
        checks["picture_restored_after_failure"] = picture_before_figure == solver.settings.results.graphics.picture.get_state()
        checks["mesh_counts_after_failure"] = await server.backend.mesh_counts()
        await call("export_contour", figure_arguments, "figure_retry_same_output")
        checks["mesh_cache_empty_after_success"] = not server.backend._pyfluent._mesh_cache
        checks["picture_restored_after_success"] = picture_before_figure == solver.settings.results.graphics.picture.get_state()
        checks["temporary_contours_absent"] = not any(n.startswith("mcp-figure-") for n in solver.settings.results.graphics.contour.get_object_names())
        checks["report_routing_reopened"] = expected_routing == solver.settings.solution.monitor.report_files.get_state()
        await call("solver_progress", {"reference_surface": "not-a-real-surface"}, "progress_partial_probe")
        high_counter = await call("solver_progress", {"reference_surface": "outlet"}, "progress_before_baseline_reload")
        solver.settings.file.read_case(file_name=str(Path(runtime_dir) / "baseline.cas.h5"))
        solver.settings.file.read_data(file_name=str(Path(runtime_dir) / "baseline.dat.h5"))
        await call("solver_progress", {"reference_surface": "outlet", "previous": high_counter}, "progress_counter_decrease_after_reload")
        dump("checks.json", checks)
    print("CONTRACT_RECEIPT", out, flush=True)
    return str(out)
