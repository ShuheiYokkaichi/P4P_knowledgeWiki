"""Real Fluent/MCP demonstration; no mocks, fixtures, or unit-test acceptance.

Call ``await demonstrate(solver, server, runtime_dir)`` from the persistent
direct-fluent-use controller after its machine/version gate. The supplied
server is the unmodified official SolveMCP with register_additions applied.
Its backend must be attached to this owned session. Client shutdown follows
the official lifecycle and exits Fluent. Save valuable state before calling.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from fastmcp import Client


async def demonstrate(solver, server, runtime_dir):
    work = Path(runtime_dir)
    out = work / ("demo-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(parents=True, exist_ok=False)
    calls, checks = [], {}

    def dump(name, payload):
        (out / name).write_text(json.dumps(payload, indent=2, default=str, allow_nan=False), encoding="utf-8")

    async with Client(server) as client:
        tools = await client.list_tools()
        dump("schemas.json", [t.model_dump(mode="json") for t in tools])

        async def call(name, arguments, label=None):
            result = await client.call_tool(name, arguments, raise_on_error=False)
            raw = {"name": name, "arguments": arguments, "is_error": result.is_error,
                   "content": [c.model_dump(mode="json") for c in result.content],
                   "structured_content": result.structured_content}
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
        path = Path(next(iter(effective.values()))["file_name"])
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
