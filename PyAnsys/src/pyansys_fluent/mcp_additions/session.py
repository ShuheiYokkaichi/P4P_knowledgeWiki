"""Factual progress and safe routing of inherited Report File outputs."""
from __future__ import annotations

from pathlib import Path


def solver_progress(solver, reference_surface: str) -> dict:
    """Separate native iteration/time evidence from configured run controls.

    Iteration is Fluent's expression value, not a zero-based count of work
    completed by this tool. No stream, background poll, or solve is started.
    The reference surface supplies a location for the read-only reduction.
    """
    out = {"source": "live Fluent", "errors": {}}
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
    return out


def route_report_files(solver, names: list[str], directory: str) -> dict:
    """Route selected existing Report Files into a fresh local directory.

    Preserve activation, definition mapping, and sampling frequency. An empty
    new directory prevents an inherited filename from appending to prior work.
    Fluent can add run/iteration suffixes; return its effective readback.
    """
    if solver.settings.solution.run_calculation.iterating():
        raise RuntimeError("Wait for the active solve before routing report files")
    if not names or len(names) > 64 or len(set(names)) != len(names):
        raise ValueError("Select 1 to 64 distinct Report File names")
    files = solver.settings.solution.monitor.report_files
    available = files.get_object_names()
    if set(names) - set(available):
        raise ValueError(f"Unknown Report Files: {sorted(set(names) - set(available))}")
    target = Path(directory).expanduser().resolve()
    if target.exists():
        raise FileExistsError("Use a new output directory to preserve existing results")
    before = {name: files[name].get_state() for name in names}
    # Avoid platform-specific name sanitization collisions. Numbered files are
    # mapped to the original report object explicitly in the receipt.
    destinations = {name: target / f"report-{i:03}.out" for i, name in enumerate(names, 1)}
    target.mkdir(parents=True, exist_ok=False)
    applied = []
    try:
        for name in names:
            files[name].file_name = str(destinations[name])
            applied.append(name)
        after = {name: files[name].get_state() for name in names}
        invariants = ("report_defs", "active", "frequency_of", "frequency", "flow_frequency")
        for name in names:
            if any(before[name].get(k) != after[name].get(k) for k in invariants):
                raise RuntimeError(f"Report sampling or definition mapping changed: {name}")
            if Path(after[name]["file_name"]).parent.resolve() != target:
                raise RuntimeError(f"Report output did not move to requested directory: {name}")
    except Exception as original:
        rollback_errors = {}
        for name in reversed(applied):
            try:
                files[name].file_name = before[name]["file_name"]
            except Exception as exc:
                rollback_errors[name] = str(exc)
        raise RuntimeError(f"Routing failed: {original}; rollback errors: {rollback_errors}") from original
    return {"status": "routed", "directory": str(target), "before": before, "after": after,
            "scope": "local Fluent host only; directory preserved even on failure"}
