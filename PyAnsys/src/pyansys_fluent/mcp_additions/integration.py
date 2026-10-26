"""Opt-in registration on upstream SolveMCP; preserve its backend lifecycle."""
from __future__ import annotations

import asyncio
from functools import partial
import inspect
from typing import get_type_hints

from .artifacts import export_contour, export_surface_data
from .geometry import boundary_fingerprint, surface_field_summary, surface_geometry
from .session import route_report_files, solver_progress


def register_additions(server):
    """Add the contribution tools to an existing official SolveMCP instance.

    This laboratory bridge uses the backend's public run_code namespace to
    execute trusted helpers under its existing lock. It does not expose an
    unrestricted import or arbitrary file reader. Final upstream extraction
    can move each helper behind its own Backend method without this bridge.
    """
    from .histories import read_live_monitor_history, read_report_file_history
    from .segments import join_history_segments

    live = [surface_geometry, boundary_fingerprint, surface_field_summary,
            export_surface_data, read_live_monitor_history, solver_progress,
            route_report_files, export_contour]
    offline = [read_report_file_history, join_history_segments]
    for function in live + offline:
        _register(server, function, function in live)
    return [f.__name__ for f in live + offline]


def _register(server, function, needs_solver):
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    parameters = list(signature.parameters.values())[1 if needs_solver else 0:]
    parameters = [p.replace(annotation=hints.get(p.name, p.annotation)) for p in parameters]

    async def call(**kwargs):
        if not needs_solver:
            return await asyncio.to_thread(function, **kwargs)
        if not server.backend.is_connected():
            raise RuntimeError("Connect to Fluent before using this tool")
        # Bind values as Python objects, never interpolate user input into code.
        result = await server.backend.run_code(
            "candidate(solver)", namespace={"candidate": partial(function, **kwargs)})
        if result.status != "ok":
            raise RuntimeError(result.message or result.stderr or "Fluent operation failed")
        return result.return_value

    call.__name__ = function.__name__
    call.__doc__ = function.__doc__
    call.__signature__ = inspect.Signature(parameters, return_annotation=dict)
    call.__annotations__ = {p.name: p.annotation for p in parameters}
    call.__annotations__["return"] = dict
    server.tool(name=function.__name__, description=function.__doc__)(call)
