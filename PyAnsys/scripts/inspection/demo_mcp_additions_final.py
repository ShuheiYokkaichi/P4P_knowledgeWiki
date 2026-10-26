"""Live qualification of the retained MCP additions on an owned Fluent session.

Supply an attached official SolveMCP and a saved mixing-elbow pair. No mocks,
unit tests, session creation or session-fleet ownership are used here.
"""
from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
import base64
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import threading
import zipfile

from fastmcp import Client


async def demonstrate(solver, server, runtime_dir, case_file, data_file):
    out = Path(runtime_dir) / ("final-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    out.mkdir(exist_ok=False)
    calls, checks = [], {}

    def dump(name, value):
        (out / name).write_text(json.dumps(value, indent=2, default=str, allow_nan=False), encoding="utf-8")

    import ansys.fluent.mcp.solve.backends.pyfluent as upstream
    loaded = Path(inspect.getfile(upstream)).resolve()
    upstream_root = next(p for p in loaded.parents if (p / ".git").exists())
    package = Path(__file__).resolve().parents[2] / "src/pyansys_fluent/mcp_additions"
    dump("identity.json", {"fluent": str(solver.get_fluent_version()), "python": sys.version,
        "loaded_upstream_file": str(loaded), "loaded_upstream_file_sha256": hashlib.sha256(loaded.read_bytes()).hexdigest(),
        "upstream_sha": subprocess.check_output(["git", "-C", str(upstream_root), "rev-parse", "HEAD"], text=True).strip(),
        "upstream_status": subprocess.check_output(["git", "-C", str(upstream_root), "status", "--porcelain"], text=True),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in package.glob("*.py")},
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    solver.settings.file.read_case(file_name=str(case_file))
    solver.settings.file.read_data(file_name=str(data_file))
    solver.settings.file.write_case(file_name=str(out / "native.cas.h5"))
    checks["live_boundary_geometry"] = {name: {
        "area_m2": float(solver.fields.reduction.area(locations=[name])),
        "centroid_m": list(solver.fields.reduction.centroid(locations=[name]))}
        for name in solver.fields.field_data.surfaces.allowed_values()}

    async with Client(server) as client:
        dump("schemas.json", [t.model_dump(mode="json") for t in await client.list_tools()])

        async def call(name, arguments, label=None):
            sent = deepcopy(arguments)
            result = await client.call_tool(name, arguments, raise_on_error=False)
            calls.append({"name": name, "label": label or name, "arguments": sent,
                "is_error": result.is_error, "structured_content": deepcopy(result.structured_content),
                "content": [c.model_dump(mode="json") for c in result.content]})
            dump("calls.json", calls)
            print("FINAL_DEMO", label or name, "ERROR" if result.is_error else "RETURNED", flush=True)
            return result.structured_content or calls[-1]

        await call("inspect_mesh_file", {"path": str(out / "native.cas.h5"), "allowed_root": str(out)})
        a = await call("export_surface_data", {"surfaces": ["outlet"], "field": "temperature",
            "output": str(out / "before.npz"), "sampling": "face"})
        await call("export_surface_data", {"surfaces": ["outlet"], "field": "temperature",
            "output": str(out / "nodes-before.npz"), "sampling": "node"})
        solver.settings.mesh.reorder.reorder_domain()
        await call("export_surface_data", {"surfaces": ["outlet"], "field": "temperature",
            "output": str(out / "reordered.npz"), "sampling": "face"})
        await call("compare_surface_datasets", {"path_a": str(out / "before.npz"),
            "path_b": str(out / "reordered.npz")}, "comparison_after_native_reorder")
        await call("export_surface_data", {"surfaces": ["outlet"], "field": "temperature",
            "output": str(out / "nodes-reordered.npz"), "sampling": "node"})
        await call("compare_surface_datasets", {"path_a": str(out / "nodes-before.npz"),
            "path_b": str(out / "nodes-reordered.npz")}, "node_comparison_after_native_reorder")
        solver.settings.solution.initialization.patch.calculate_patch(
            cell_zones=["elbow-fluid"], variable="temperature", value=310)
        b = await call("export_surface_data", {"surfaces": ["outlet"], "field": "temperature",
            "output": str(out / "patched.npz"), "sampling": "face"})
        await call("compare_surface_datasets", {"path_a": str(out / "before.npz"),
            "path_b": str(out / "patched.npz")}, "comparison_after_native_patch")
        solver.settings.mesh.scale(x_scale=1.01, y_scale=1, z_scale=1)
        await call("export_surface_data", {"surfaces": ["outlet"], "field": "temperature",
            "output": str(out / "changed-geometry.npz"), "sampling": "face"})
        await call("compare_surface_datasets", {"path_a": str(out / "before.npz"),
            "path_b": str(out / "changed-geometry.npz")}, "refuse_changed_geometry_comparison")
        checks["export_hashes"] = [hashlib.sha256(Path(v["artifact"]["path"]).read_bytes()).hexdigest() == v["artifact"]["sha256"] for v in (a, b)]

        # Restore a saved field before a short monitor-contract smoke check.
        solver.settings.file.read_case(file_name=str(case_file))
        solver.settings.file.read_data(file_name=str(data_file))
        reports = solver.settings.solution.report_definitions.surface
        if "mcp-hot-temperature" not in reports.get_object_names():
            reports.create(name="mcp-hot-temperature")
        reports["mcp-hot-temperature"].set_state({"report_type": "surface-areaavg", "field": "temperature",
            "surface_names": ["hot-inlet"], "create_report_plot": True})
        plots = solver.settings.solution.monitor.report_plots
        plots["mcp-outlet-temperature-rplot"].report_defs = ["mcp-outlet-temperature", "mcp-hot-temperature"]
        solver.monitors.refresh(solver, None)  # Refresh only this demo-owned client's stream metadata.
        backend_solver = server.backend._pyfluent._solver
        backend_solver.monitors.refresh(backend_solver, None)
        files = solver.settings.solution.monitor.report_files
        main = "mcp-outlet-temperature-rfile"
        files[main].report_defs = ["mcp-outlet-temperature", "mcp-outlet-pressure", "mcp-physical-time"]
        route = await call("route_report_files", {"names": [main], "directory": str(out / "reports")})
        if route.get("status") != "routed":
            raise RuntimeError("Routing did not succeed; the dependent smoke solve was not started")
        before = await call("solver_progress", {"reference_surface": "outlet"})
        solver.settings.solution.run_calculation.dual_time_iterate(time_step_count=12, max_iter_per_step=1)
        await call("solver_progress", {"reference_surface": "outlet", "previous": before})
        history = await call("read_live_monitor_history", {"monitor_set": "mcp-outlet-temperature-rplot",
            "max_points": 3, "max_scan_points": 10, "output_prefix": str(out / "monitor")})
        checks["history_coordinate_semantics"] = {k: history.get(k) for k in (
            "x", "x_label", "native_display_label", "coordinate_semantics", "coordinate_unit")}
        native = Path(route["effective_paths"][main])
        report = await call("read_report_file_history", {"path": str(native), "coordinate_column": "mcp-physical-time"})
        (out / "native-history.out").write_bytes(native.read_bytes())
        digest = hashlib.sha256(native.read_bytes()).hexdigest()
        rows, columns = report["rows"], report["columns"]

        def segment(label, selected, source_rows):
            return {"source_id": label, "sha256": digest, "axis": {"name": "physical-time", "unit": "s"},
                "units": {"temperature": "K", "unavailable": "1"}, "source_rows": source_rows,
                "x": [r[columns.index("mcp-physical-time")] for r in selected],
                "series": {"temperature": [r[columns.index("mcp-outlet-temperature")] for r in selected]}}
        await call("join_history_segments", {"segments": [segment("left", rows[:7], list(range(7))),
            segment("right", rows[6:], list(range(6, len(rows))))], "expected_step": 0.01, "step_tolerance": 1e-12})

        solver.settings.file.write_case(file_name=str(out / "figure-source.cas.h5"))
        solver.settings.file.write_data(file_name=str(out / "figure-source.dat.h5"))
        arguments = {"surfaces": ["symmetry-xyplane"], "field": "temperature", "minimum": 290, "maximum": 315,
            "case_file": str(out / "figure-source.cas.h5"), "data_file": str(out / "figure-source.dat.h5"),
            "output": str(out / "figure.png")}
        stopped = threading.Event()
        obstruction = out / "figure.json"

        def obstruct_publication():
            while not stopped.wait(0.001):
                if any(out.glob(".mcp-figure-*/figure.png")):
                    obstruction.mkdir()
                    return
        worker = threading.Thread(target=obstruct_publication, daemon=True)
        picture = solver.settings.results.graphics.picture.get_state()
        worker.start()
        try:
            await call("export_contour", arguments, "figure_publication_obstruction")
        finally:
            stopped.set()
            worker.join(timeout=5)
        checks["figure_publication_rollback"] = not (out / "figure.png").exists() and not (out / "figure.vw").exists()
        checks["figure_obstruction_preserved"] = obstruction.is_dir()
        if obstruction.is_dir():
            obstruction.rmdir()  # Only this empty, explicitly created demo obstacle.
        figure = await call("export_contour", arguments, "figure_retry_after_publication_failure")
        checks["figure_picture_restored"] = picture == solver.settings.results.graphics.picture.get_state()
        checks["figure_cleanup"] = figure.get("cleanup")

        # Hold a real Windows file handle without FILE_SHARE_DELETE. Native
        # rendering can finish, but scratch removal must report partial cleanup.
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create_file = kernel.CreateFileW
        create_file.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                               wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create_file.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        release_handle, handle_acquired = threading.Event(), threading.Event()
        locked_paths = []

        def hold_camera_file():
            while not release_handle.wait(0.001):
                for path in out.glob(".mcp-figure-*/camera.vw"):
                    handle = create_file(str(path), 0x80000000, 3, None, 3, 128, None)
                    if handle != ctypes.c_void_p(-1).value:
                        locked_paths.append(str(path))
                        handle_acquired.set()
                        release_handle.wait(120)
                        kernel.CloseHandle(handle)
                        return

        worker = threading.Thread(target=hold_camera_file, daemon=True)
        worker.start()
        try:
            locked = await call("export_contour", {**arguments, "output": str(out / "locked-figure.png")},
                                "figure_scratch_removal_blocked_by_real_handle")
        finally:
            release_handle.set()
            worker.join(timeout=5)
        checks["scratch_handle_acquired"] = handle_acquired.is_set()
        checks["scratch_locked_paths"] = locked_paths
        checks["scratch_cleanup_receipt"] = locked.get("cleanup")
        locked_sidecar = json.loads((out / "locked-figure.json").read_text(encoding="utf-8"))
        checks["scratch_cleanup_sidecar_matches_reply"] = locked_sidecar["cleanup"] == locked.get("cleanup")
        remaining = (locked.get("cleanup") or {}).get("scratch_directory")
        if remaining:
            owned_scratch = Path(remaining).resolve()
            if owned_scratch.parent != out.resolve() or not owned_scratch.name.startswith(".mcp-figure-"):
                raise RuntimeError("Refuse demo cleanup outside the explicitly owned scratch directory")
            shutil.rmtree(owned_scratch)
            checks["scratch_removed_after_handle_release"] = not owned_scratch.exists()

        bundle = await call("bundle_artifacts", {"root": str(out),
            "files": ["figure.png", "figure.json", "figure.vw", "native-history.out", "before.npz", "before.json", "monitor.csv"],
            "output": str(out / "evidence.zip")})
        resources = await client.read_resource(bundle["resource_uri"])
        payload = b"".join(base64.b64decode(resource.blob) for resource in resources)
        with zipfile.ZipFile(BytesIO(payload)) as archive:
            checks["bundle_members"] = archive.namelist()
            checks["bundle_zip_integrity"] = archive.testzip() is None
        checks["bundle_resource_sha256"] = hashlib.sha256(payload).hexdigest()
        checks["bundle_resource_matches_artifact"] = checks["bundle_resource_sha256"] == bundle["zip"]["sha256"]
        changed = await call("bundle_artifacts", {"root": str(out), "files": ["native-history.out"],
            "output": str(out / "changed-after-publication.zip")}, "bundle_for_resource_integrity_refusal")
        with Path(changed["zip"]["path"]).open("ab") as stream:
            stream.write(b"deliberate post-publication modification")
        try:
            await client.read_resource(changed["resource_uri"])
            checks["changed_resource_refused"] = False
        except Exception as exc:
            checks["changed_resource_refused"] = True
            checks["changed_resource_error"] = f"{type(exc).__name__}: {exc}"
        dump("checks.json", checks)
    print("FINAL_DEMO_RECEIPT", out, flush=True)
    return str(out)
