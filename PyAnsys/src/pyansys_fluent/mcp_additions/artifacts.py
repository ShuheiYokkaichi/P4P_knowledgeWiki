"""Bounded data exports and reproducible native Fluent contour figures."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import tempfile
from pathlib import Path
import uuid
from datetime import datetime, timezone
from typing import Literal

import numpy as np
from ansys.fluent.core.fields.field_data_interfaces import ScalarFieldDataRequest

from .geometry import _geometry, field_metadata
from .session import local_fluent_directory


def _identity(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def export_surface_data(solver, surfaces: list[str], field: str, output: str,
                        max_faces: int = 100000, sampling: Literal["face", "node"] = "face") -> dict:
    """Write geometry-linked scalar data to indexed, hashed NPZ and JSON files.

    The response stays small. Local arrays retain exact connectivity and
    invalid values; invalid data are counted rather than replaced with zero.
    Node sampling aligns with vertices. Face sampling follows boundary-face
    ordering; Fluent can supply adjacent-cell values when a boundary value is
    unavailable, so values need not equal evaluation at the geometric centroid.
    max_faces limits the exported selection after retrieval, not RPC memory.
    """
    if isinstance(max_faces, bool) or not 1 <= max_faces <= 1000000:
        raise ValueError("max_faces must be between 1 and 1000000")
    if sampling not in ("face", "node"):
        raise ValueError("sampling must be face or node")
    destination = Path(output).expanduser().resolve()
    if destination.suffix != ".npz":
        raise ValueError("output must end in .npz")
    sidecar = destination.with_suffix(".json")
    if destination.exists() or sidecar.exists():
        raise FileExistsError("Choose new data and metadata paths")
    geometry = _geometry(solver, surfaces)
    if sum(len(g.face_centroids) for g in geometry.values()) > max_faces:
        raise ValueError("Selected surfaces exceed max_faces; select fewer surfaces")
    values = solver.fields.field_data.get_field_data(ScalarFieldDataRequest(
        surfaces=surfaces, field_name=field, node_value=sampling == "node", boundary_value=True))
    arrays, index = {}, {}
    for i, (name, g) in enumerate(geometry.items()):
        v = np.asarray(values[name]).reshape(-1)
        expected = len(g.vertices) if sampling == "node" else len(g.face_centroids)
        if len(v) != expected:
            raise ValueError(f"Scalar/{sampling} alignment failed: {name}")
        prefix = f"s{i}"
        arrays.update({f"{prefix}_vertices": g.vertices,
                       f"{prefix}_connectivity": g.connectivity,
                       f"{prefix}_centroids": g.face_centroids,
                       f"{prefix}_values": v})
        index[name] = {"prefix": prefix, "faces": len(g.face_centroids), "vertices": len(g.vertices),
                       "samples": len(v), "nonfinite": int((~np.isfinite(v)).sum())}
    metadata = field_metadata(solver, field)
    observation = {"captured_at_utc": datetime.now(timezone.utc).isoformat(),
                   "iteration_expression": float(solver.fields.reduction.maximum(expression="Iteration", locations=[surfaces[0]])),
                   "flow_time_s": solver.rp_vars("flow-time")}
    destination.parent.mkdir(parents=True, exist_ok=True)
    created = []
    record = {"schema": "fluent.surface-dataset.v1", "field": field, "coordinates": "m",
              "field_metadata": metadata, "observation": observation,
              "sampling": sampling, "boundary_values": True, "surfaces": index,
              "sampling_basis": "vertex-aligned" if sampling == "node" else "boundary-face-indexed; boundary or adjacent-cell values, not guaranteed centroid evaluation",
              "connectivity": "flat: vertex count followed by zero-based vertex IDs for each face"}
    try:
        with destination.open("xb") as stream:
            created.append(destination)
            np.savez_compressed(stream, **arrays)
        record["artifact"] = _identity(destination)
        with sidecar.open("x", encoding="utf-8") as stream:
            created.append(sidecar)
            json.dump(record, stream, indent=2)
    except Exception:
        # Remove only files exclusively created by this operation. A racing
        # writer's existing file is never included in this list.
        for path in reversed(created):
            path.unlink(missing_ok=True)
        raise
    return {**record, "metadata": _identity(sidecar)}


def export_contour(solver, surfaces: list[str], field: str, output: str,
                   case_file: str, data_file: str,
                   minimum: float, maximum: float, view: str = "front",
                   width: int = 1200, height: int = 800) -> dict:
    """Create a native PNG with fixed scale and settings/camera provenance.

    Explicitly load the supplied saved pair before plotting. This replaces
    unsaved live state: preserve it before calling. A temporary contour/view is
    deleted after export. Output files are never overwritten. The displayed
    window changes, as it does for upstream screenshot workflows.
    """
    if not (math.isfinite(minimum) and math.isfinite(maximum) and minimum < maximum):
        raise ValueError("Provide finite, increasing contour limits")
    if not (200 <= width <= 4096 and 200 <= height <= 4096):
        raise ValueError("Image dimensions must be between 200 and 4096 pixels")
    destination = Path(output).expanduser().resolve()
    sidecar = destination.with_suffix(".json")
    view_file = destination.with_suffix(".vw")
    if destination.suffix.lower() != ".png" or any(p.exists() for p in (destination, sidecar, view_file)):
        raise ValueError("Provide a new .png path and unused .json sidecar")
    if solver.settings.solution.run_calculation.iterating():
        raise RuntimeError("Wait for the active solve before loading a figure source")
    local_fluent_directory(solver)
    sources = [Path(p).expanduser().resolve() for p in (case_file, data_file)]
    if not all(p.is_file() for p in sources):
        raise FileNotFoundError("Both source case and data must exist on the local Fluent host")
    source_identity = {"case": _identity(sources[0]), "data": _identity(sources[1])}
    solver.settings.file.read_case(file_name=str(sources[0]))
    solver.settings.file.read_data(file_name=str(sources[1]))
    _geometry(solver, surfaces)  # Validate names before creating graphics objects.
    graphics = solver.settings.results.graphics
    contours = graphics.contour
    name = "mcp-figure-" + uuid.uuid4().hex[:12]
    picture_before = {}
    mode_before = solver.settings.setup.general.solver.get_state()
    destination.parent.mkdir(parents=True, exist_ok=True)
    view_saved = False
    primary = None
    cleanup_errors = {}
    published = []
    scratch = Path(tempfile.mkdtemp(prefix=".mcp-figure-", dir=destination.parent))
    native_png, native_view = scratch / "figure.png", scratch / "camera.vw"
    try:
        contours.create(name=name)
        obj = contours[name]
        obj.set_state({"field": field, "surfaces_list": surfaces,
                       "options": {"filled": True, "node_values": False, "boundary_values": True},
                       "range_options": {"global_range": False, "auto_range": False,
                                         "clip_to_range": False, "minimum": minimum, "maximum": maximum}})
        obj.display()
        graphics.views.restore_view(view_name=view)
        graphics.views.auto_scale()
        for key, value in (("use_window_resolution", False), ("x_resolution", width), ("y_resolution", height)):
            node = getattr(graphics.picture, key)
            if key == "use_window_resolution" and not node.is_active():
                continue  # Headless graphics has no window-resolution control.
            if not node.is_active():
                raise RuntimeError("Native picture export requires a graphics-enabled Fluent session")
            picture_before[key] = node.get_state()
            node.set_state(value)
        graphics.views.save_view(view_name=name)
        view_saved = True
        graphics.views.write_views(file_name=str(native_view), view_list=[name])
        record = {"field": field, "surfaces": surfaces, "view": view,
                  "source_pair": source_identity, "source_loaded": True,
                  "contour": obj.get_state(), "camera_file": {**_identity(native_view), "path": str(view_file)},
                  "picture": graphics.picture.get_state(), "native": True,
                  "field_metadata": field_metadata(solver, field), "location": "face"}
        graphics.picture.save_picture(file_name=str(native_png))
        data = native_png.read_bytes()
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Fluent did not write a PNG")
        record["artifact"] = {**_identity(native_png), "path": str(destination)}
        record["resolution"] = [int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")]
        if record["resolution"] != [width, height]:
            raise RuntimeError(f"Unexpected PNG dimensions: {record['resolution']}")
        if solver.settings.setup.general.solver.get_state() != mode_before:
            raise RuntimeError("Solver mode changed during graphics export")
    except Exception as exc:
        primary = exc
    # Each restoration is independent. Keep the original operation error even
    # when Fluent rejects a cleanup command; expose every cleanup failure.
    actions = [("contour", lambda: contours.delete(name_list=[name])
                if name in contours.get_object_names() else None)]
    if view_saved:
        actions.append(("view", lambda: graphics.views.delete_view(view_name=name)))
    actions.extend(("picture." + key, lambda k=key, v=value: getattr(graphics.picture, k).set_state(v))
                   for key, value in reversed(tuple(picture_before.items())))
    for label, action in actions:
        try:
            action()
        except Exception as exc:
            cleanup_errors[label] = f"{type(exc).__name__}: {exc}"
    scratch_attempted = False

    def cleanup_scratch():
        nonlocal scratch_attempted
        if scratch_attempted:
            return
        scratch_attempted = True
        try:
            if scratch.resolve().parent != destination.parent.resolve() or not scratch.name.startswith(".mcp-figure-"):
                raise RuntimeError("Refuse cleanup outside the operation's scratch directory")
            shutil.rmtree(scratch)
        except Exception as exc:
            cleanup_errors["scratch"] = f"{scratch}: {type(exc).__name__}: {exc}"

    try:
        if primary is not None:
            raise primary
        # Native writes stay in a private scratch directory. Publish each
        # validated output exclusively; never overwrite a racing writer.
        for original, target in ((native_view, view_file), (native_png, destination)):
            with target.open("xb") as stream:
                published.append(target)
                with original.open("rb") as source:
                    shutil.copyfileobj(source, stream)
        cleanup_scratch()
        record["cleanup"] = {"status": "partial" if cleanup_errors else "complete", "errors": cleanup_errors,
                             "scratch_directory": str(scratch) if "scratch" in cleanup_errors else None}
        with sidecar.open("x", encoding="utf-8") as stream:
            published.append(sidecar)
            json.dump(record, stream, indent=2)
        return {**record, "metadata": _identity(sidecar)}
    except Exception as exc:
        for path in reversed(published):
            try:
                path.unlink(missing_ok=True)
            except Exception as cleanup:
                cleanup_errors["file." + str(path)] = str(cleanup)
        cleanup_scratch()
        if cleanup_errors:
            exc.add_note("Figure cleanup failures: " + json.dumps(cleanup_errors))
        raise
