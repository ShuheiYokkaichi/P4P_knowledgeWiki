"""Factual progress and safe routing of inherited Report File outputs."""
from __future__ import annotations

from pathlib import Path
import os
import socket
from datetime import datetime, timezone


def local_fluent_directory(solver) -> Path:
    """Verify the live controller host and directory before native file writes."""
    info = solver._fluent_connection.application_runtime.get_controller_process_info()
    aliases = {socket.gethostname().casefold(), os.environ.get("COMPUTERNAME", "").casefold()}
    if info.hostname.casefold() not in aliases:
        raise RuntimeError("This file operation requires Fluent on the local MCP host")
    path = Path(info.working_directory)
    if not path.is_absolute() or not path.is_dir():
        raise RuntimeError("Fluent did not expose an accessible absolute working directory")
    return path.resolve()


def solver_progress(solver, reference_surface: str, previous: dict | None = None) -> dict:
    """Separate native iteration/time evidence from configured run controls.

    Iteration is Fluent's expression value, not a zero-based count of work
    completed by this tool. No stream, background poll, or solve is started.
    The reference surface supplies a location for the read-only reduction.
    """
    out = {"source": "live Fluent", "reference_surface": reference_surface,
           "captured_at_utc": datetime.now(timezone.utc).isoformat(), "errors": {}}
    probes = {
        "iteration_expression": lambda: solver.fields.reduction.maximum(
            expression="Iteration", locations=[reference_surface]),
        "flow_time_s": lambda: solver.rp_vars("flow-time"),
        "time_step_index": lambda: solver.rp_vars("time-step"),
        "iterating": lambda: solver.settings.solution.run_calculation.iterating(),
        "configured_run_controls": lambda: solver.settings.solution.run_calculation.get_state(),
    }
    for key, call in probes.items():
        try:
            out[key] = call()
        except Exception as exc:
            out[key] = None
            out["errors"][key] = f"{type(exc).__name__}: {exc}"
    out["status"] = "partial" if out["errors"] else "complete"
    out["iteration_basis"] = "Fluent expression Iteration at the selected surface; not configured iter_count"
    if previous is not None:
        changes = {}
        for key in ("iteration_expression", "flow_time_s", "time_step_index"):
            a, b = previous.get(key), out.get(key)
            if type(a) not in (int, float) or type(b) not in (int, float):
                changes[key] = {"change": None, "basis": "one observation unavailable"}
            else:
                changes[key] = {"change": b - a if b >= a else None,
                                "counter_decreased": b < a}
        out["observed_changes"] = changes
        out["change_scope"] = "difference between caller-supplied observations; counter decrease can mean reload/reset or another case"
    return out


def route_report_files(solver, names: list[str], directory: str) -> dict:
    """Route selected existing Report Files into a fresh local directory.

    Preserve activation, definition mapping, and sampling frequency. An empty
    new directory prevents an inherited filename from appending to prior work.
    Redirect future writes; existing histories stay at their original paths.
    Return requested/effective paths and verified rollback evidence on failure.
    """
    if solver.settings.solution.run_calculation.iterating():
        raise RuntimeError("Wait for the active solve before routing report files")
    if not names or len(names) > 64 or len(set(names)) != len(names):
        raise ValueError("Select 1 to 64 distinct Report File names")
    files = solver.settings.solution.monitor.report_files
    available = files.get_object_names()
    if set(names) - set(available):
        raise ValueError(f"Unknown Report Files: {sorted(set(names) - set(available))}")
    fluent_cwd = local_fluent_directory(solver)
    target = Path(directory).expanduser()
    if not target.is_absolute():
        raise ValueError("Use an absolute local output directory")
    target = target.resolve()
    if target.exists():
        raise FileExistsError("Use a new output directory to preserve existing results")
    before = {name: files[name].get_state() for name in names}
    # Avoid platform-specific name sanitization collisions. Numbered files are
    # mapped to the original report object explicitly in the receipt.
    destinations = {name: target / f"report-{i:03}.out" for i, name in enumerate(names, 1)}
    target.mkdir(parents=True, exist_ok=False)
    applied = []
    writable = ("file_name", "report_defs", "frequency_of", "frequency", "flow_frequency",
                "print", "active", "write_instantaneous_values")
    def resolved(state):
        path = Path(state["file_name"])
        return (path if path.is_absolute() else fluent_cwd / path).resolve()
    try:
        for name in names:
            applied.append(name)
            # Close a live Report File writer before changing its destination.
            # Fluent can otherwise accept the setter but retain the open path.
            files[name].active = False
            files[name].file_name = str(destinations[name])
            files[name].active = before[name]["active"]
        after = {name: files[name].get_state() for name in names}
        invariants = ("report_defs", "active", "frequency_of", "frequency", "flow_frequency")
        for name in names:
            if any(before[name].get(k) != after[name].get(k) for k in invariants):
                raise RuntimeError(f"Report sampling or definition mapping changed: {name}")
            if resolved(after[name]) != destinations[name]:
                raise RuntimeError(f"Report output did not move to requested path: {name}")
            if destinations[name].exists() and not destinations[name].is_file():
                raise RuntimeError(f"Report output path is not a regular file: {name}")
        if len({resolved(state) for state in after.values()}) != len(names):
            raise RuntimeError("Fluent routed multiple reports to the same effective filename")
    except Exception as original:
        rollback_errors, final, differences = {}, {}, {}
        for name in reversed(applied):
            try:
                files[name].active = False
                for key in writable:
                    if key != "active" and key in before[name] and getattr(files[name], key).is_active():
                        getattr(files[name], key).set_state(before[name][key])
                files[name].active = before[name]["active"]
                final[name] = files[name].get_state()
                changed = [k for k in writable if k in before[name] and k != "file_name"
                           and before[name][k] != final[name].get(k)]
                if resolved(before[name]) != resolved(final[name]):
                    changed.append("file_name")
                if changed:
                    differences[name] = changed
            except Exception as exc:
                rollback_errors[name] = str(exc)
        return {"status": "error", "error": str(original), "directory": str(target),
                "attempted": applied, "before": before, "final": final,
                "rollback": {"status": "partial" if rollback_errors or differences else "verified",
                             "errors": rollback_errors, "differences": differences,
                             "scope": "selected writable report fields; managed run/index counters are not restored"}}
    return {"status": "routed", "directory": str(target), "before": before, "after": after,
            "requested_paths": {n: str(p) for n, p in destinations.items()},
            "effective_paths": {n: str(resolved(s)) for n, s in after.items()},
            "fluent_working_directory": str(fluent_cwd), "working_directory_source": "live controller process RPC",
            "transition": "deactivate writer, set destination, restore original activation, verify",
            "scope": "local Fluent host only; directory preserved even on failure"}
