"""Opt-in registration on upstream SolveMCP; preserve its backend lifecycle."""
from __future__ import annotations

import asyncio
from functools import partial
import inspect
from typing import Annotated, get_type_hints

from pydantic import Field

from .artifacts import export_contour, export_surface_data
from .geometry import boundary_fingerprint, surface_field_summary, surface_geometry
from .session import route_report_files, solver_progress
from .schemas import HistorySegment, JoinedHistory, MonitorHistory, ReportHistory, RoutingReceipt, SolverProgress
from .schemas import BoundaryFingerprint, SurfaceFieldSummary, SurfaceGeometry


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
    if function.__name__ == "join_history_segments":
        parameters = [p.replace(annotation=list[HistorySegment]) if p.name == "segments" else p for p in parameters]
    reference_type = {"boundary_fingerprint": BoundaryFingerprint,
                      "surface_field_summary": SurfaceFieldSummary}.get(function.__name__)
    if reference_type:
        parameters = [p.replace(annotation=reference_type | None) if p.name == "reference" else p for p in parameters]
    if function.__name__ == "solver_progress":
        parameters = [p.replace(annotation=SolverProgress | None) if p.name == "previous" else p for p in parameters]
    parameters = [p.replace(annotation=Annotated[p.annotation, Field(min_length=1, max_length=32)])
                  if p.name == "surfaces" else p for p in parameters]
    limits = {"max_points": (1, 10000), "max_scan_points": (1, 100000),
              "max_series": (1, 128), "max_bytes": (256, 67108864),
              "max_cells": (1, 100000 if function.__name__ == "join_history_segments" else 1000000),
              "max_rows": (1, 10000), "max_faces": (1, 1000000),
              "width": (200, 4096), "height": (200, 4096)}
    parameters = [p.replace(annotation=Annotated[p.annotation, Field(ge=limits[p.name][0], le=limits[p.name][1])])
                  if p.name in limits else p for p in parameters]
    output = {"read_live_monitor_history": MonitorHistory,
              "read_report_file_history": ReportHistory,
              "join_history_segments": JoinedHistory, "route_report_files": RoutingReceipt,
              "solver_progress": SolverProgress, "surface_geometry": SurfaceGeometry,
              "boundary_fingerprint": BoundaryFingerprint,
              "surface_field_summary": SurfaceFieldSummary}.get(function.__name__, dict)

    async def call(**kwargs):
        if reference_type and kwargs.get("reference") is not None and hasattr(kwargs["reference"], "model_dump"):
            kwargs["reference"] = kwargs["reference"].model_dump(exclude_none=True)
        if function.__name__ == "solver_progress" and kwargs.get("previous") is not None and hasattr(kwargs["previous"], "model_dump"):
            kwargs["previous"] = kwargs["previous"].model_dump(exclude_none=True)
        if function.__name__ == "join_history_segments":
            kwargs["segments"] = [v.model_dump(exclude_none=True) if isinstance(v, HistorySegment) else v
                                  for v in kwargs["segments"]]
        if needs_solver:
            if not server.backend.is_connected():
                raise RuntimeError("Connect to Fluent before using this tool")
            # Bind objects; user input never becomes generated source code.
            try:
                result = await server.backend.run_code(
                    "candidate(solver)", namespace={"candidate": partial(function, **kwargs)})
            finally:
                if function.__name__ == "export_contour":
                    # The helper can load another case even if a later step
                    # fails. Upstream's source-text heuristic cannot see the
                    # nested read_case, so invalidate through its public API.
                    server.backend.invalidate_live_caches()
                    server.backend.invalidate_mesh_cache()
            if result.status != "ok":
                raise RuntimeError(result.message or result.stderr or "Fluent operation failed")
            receipt = result.return_value
        else:
            receipt = await asyncio.to_thread(function, **kwargs)
        png = receipt.get("artifacts", {}).get("png") if function.__name__ == "read_live_monitor_history" else (
            receipt.get("artifact") if function.__name__ == "export_contour" else None)
        if png:
            import base64
            import json
            from pathlib import Path
            from fastmcp.tools.tool import ToolResult
            from mcp.types import ImageContent, TextContent
            return ToolResult(structured_content=receipt, content=[
                TextContent(type="text", text=json.dumps(receipt)),
                ImageContent(type="image", mimeType="image/png", data=base64.b64encode(Path(png["path"]).read_bytes()).decode("ascii")),
            ])
        return receipt

    call.__name__ = function.__name__
    call.__doc__ = function.__doc__
    call.__signature__ = inspect.Signature(parameters, return_annotation=output)
    call.__annotations__ = {p.name: p.annotation for p in parameters}
    call.__annotations__["return"] = output
    server.tool(name=function.__name__, description=function.__doc__, annotations={
        "readOnlyHint": function.__name__ not in {"route_report_files", "export_contour", "export_surface_data", "read_live_monitor_history"},
    })(call)
