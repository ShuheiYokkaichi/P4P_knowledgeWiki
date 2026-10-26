"""Opt-in registration on upstream SolveMCP; preserve its backend lifecycle."""
from __future__ import annotations

import asyncio
from functools import partial
import inspect
from threading import Lock
from typing import Annotated, get_type_hints
import uuid

from pydantic import Field

from .artifacts import export_contour, export_surface_data
from .geometry import boundary_fingerprint, surface_field_summary, surface_geometry
from .session import route_report_files, solver_progress
from .schemas import HistorySegment, JoinedHistory, MonitorHistory, ReportHistory, RoutingReceipt, SolverProgress
from .schemas import BoundaryFingerprint, SurfaceFieldSummary, SurfaceGeometry
from .schemas import ArtifactBundle, DatasetComparison, MeshAtlas


def register_additions(server, *, include_experimental=False):
    """Add the contribution tools to an existing official SolveMCP instance.

    This laboratory bridge uses the backend's public run_code namespace to
    execute trusted helpers under its existing lock. It does not expose an
    unrestricted import or arbitrary file reader. Final upstream extraction
    can move each helper behind its own Backend method without this bridge.
    """
    from .histories import read_live_monitor_history, read_report_file_history
    from .segments import join_history_segments
    from .mesh_file import inspect_mesh_file
    from .dataset_comparison import compare_surface_datasets
    from .artifact_bundle import bundle_artifacts

    bundles = {}
    bundle_lock = Lock()
    bundle_jobs = set()

    @server.resource("artifact://mcp-additions/bundles/{artifact_id}", mime_type="application/zip",
                     description="Read a bundle created by bundle_artifacts; arbitrary paths are not accepted")
    def read_bundle(artifact_id: str):
        import hashlib
        from pathlib import Path
        from fastmcp.resources import ResourceContent, ResourceResult
        with bundle_lock:
            expected = bundles.get(artifact_id)
        if expected is None:
            raise FileNotFoundError("Unknown or expired bundle resource")
        # Read at most the recorded size plus one byte, even if another process
        # replaces/grows the file after publication. Verify before disclosure.
        with Path(expected["path"]).open("rb") as stream:
            data = stream.read(expected["bytes"] + 1)
        if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
            raise RuntimeError("Bundle bytes changed after publication")
        return ResourceResult([ResourceContent(data, mime_type="application/zip")])

    live = [export_surface_data, read_live_monitor_history, solver_progress,
            route_report_files, export_contour]
    offline = [read_report_file_history, join_history_segments,
               inspect_mesh_file, compare_surface_datasets, bundle_artifacts]
    if include_experimental:
        live += [surface_geometry, boundary_fingerprint, surface_field_summary]
    for function in live + offline:
        _register(server, function, function in live, bundles, bundle_lock, bundle_jobs)
    return [f.__name__ for f in live + offline]


def _register(server, function, needs_solver, bundles=None, bundle_lock=None, bundle_jobs=None):
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
    if function.__name__ == "inspect_mesh_file":
        limits.update({"max_file_bytes": (1, 1073741824), "max_read_bytes": (1, 536870912),
                       "max_nodes": (1, 5000000), "max_faces": (1, 20000000),
                       "max_cells": (1, 10000000), "max_boundary_faces": (1, 1000000),
                       "max_zones": (1, 4096), "max_blocks": (1, 4096),
                       "max_connectivity_values": (1, 100000000), "max_vertices_per_face": (3, 1024)})
    elif function.__name__ == "compare_surface_datasets":
        limits.update({"max_file_bytes": (1, 536870912), "max_array_bytes": (1, 1073741824),
                       "max_samples": (1, 1000000)})
        parameters = [p.replace(annotation=Annotated[p.annotation, Field(ge=0, allow_inf_nan=False)])
                      if p.name == "absolute_tolerance" else p for p in parameters]
    elif function.__name__ == "bundle_artifacts":
        limits.update({"max_total_bytes": (1, 16777216), "max_expanded_bytes": (1, 16777216)})
        parameters = [p.replace(annotation=Annotated[p.annotation, Field(min_length=1, max_length=32)])
                      if p.name == "files" else p for p in parameters]
    parameters = [p.replace(annotation=Annotated[p.annotation, Field(ge=limits[p.name][0], le=limits[p.name][1])])
                  if p.name in limits else p for p in parameters]
    output = {"read_live_monitor_history": MonitorHistory,
              "read_report_file_history": ReportHistory,
              "join_history_segments": JoinedHistory, "route_report_files": RoutingReceipt,
              "solver_progress": SolverProgress, "surface_geometry": SurfaceGeometry,
              "boundary_fingerprint": BoundaryFingerprint,
              "surface_field_summary": SurfaceFieldSummary, "inspect_mesh_file": MeshAtlas,
              "compare_surface_datasets": DatasetComparison, "bundle_artifacts": ArtifactBundle}.get(function.__name__, dict)

    async def invoke(reservation, **kwargs):
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
                # Upstream keeps exception notes (including cleanup failures)
                # in stderr, while message contains only the primary error.
                diagnostics = [value for value in (result.message, result.stderr) if value]
                raise RuntimeError("\n".join(diagnostics) or "Fluent operation failed")
            receipt = result.return_value
        else:
            receipt = await asyncio.to_thread(function, **kwargs)
        if function.__name__ == "bundle_artifacts":
            import json
            from fastmcp.tools.tool import ToolResult
            from mcp.types import ResourceLink, TextContent
            artifact = receipt["zip"]
            resource_id = artifact["sha256"]
            with bundle_lock:
                bundles.pop(reservation, None)
                bundles[resource_id] = dict(artifact)
            receipt["resource_uri"] = "artifact://mcp-additions/bundles/" + resource_id
            return ToolResult(structured_content=receipt, content=[
                TextContent(type="text", text=json.dumps(receipt)),
                ResourceLink(type="resource_link", name="Fluent artifact bundle", uri=receipt["resource_uri"],
                             mimeType="application/zip", size=artifact["bytes"]),
            ])
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

    async def call(**kwargs):
        if function.__name__ != "bundle_artifacts":
            return await invoke(None, **kwargs)
        if bundles is None or bundle_lock is None or bundle_jobs is None:
            raise RuntimeError("Bundle resource registry is unavailable")
        with bundle_lock:
            if len(bundles) >= 128:
                raise RuntimeError("Bundle resource registry is full; start a fresh MCP server")
            reservation = "pending-" + uuid.uuid4().hex
            bundles[reservation] = None

        async def finish_bundle():
            try:
                return await invoke(reservation, **kwargs)
            finally:
                with bundle_lock:
                    bundles.pop(reservation, None)

        def finished(job):
            bundle_jobs.discard(job)
            if not job.cancelled() and (error := job.exception()) is not None:
                import logging
                logging.getLogger(__name__).error("Bundle publication failed", exc_info=error)

        # A cancelled request cannot stop a running thread. Keep ownership and
        # its capacity reservation until publication/registration has finished.
        # The server retains the task even when its requesting client leaves.
        job = asyncio.create_task(finish_bundle())
        bundle_jobs.add(job)
        job.add_done_callback(finished)
        return await asyncio.shield(job)

    call.__name__ = function.__name__
    call.__doc__ = function.__doc__
    if function.__name__ == "bundle_artifacts":
        call.__doc__ += "\nMCP returns a resource_uri and resource link for ZIP retrieval. The hash-checked registry holds at most 128 bundles, including pending calls, and lasts for this server process. Request cancellation does not stop an accepted publication: while the server runs, it retains ownership until failure cleanup or resource registration finishes. A cancelled successful publication still occupies a registry slot; its URI is artifact://mcp-additions/bundles/{zip_sha256}."
    call.__signature__ = inspect.Signature(parameters, return_annotation=output)
    call.__annotations__ = {p.name: p.annotation for p in parameters}
    call.__annotations__["return"] = output
    server.tool(name=function.__name__, description=call.__doc__, annotations={
        "readOnlyHint": function.__name__ not in {"route_report_files", "export_contour", "export_surface_data", "read_live_monitor_history", "bundle_artifacts"},
    })(call)
