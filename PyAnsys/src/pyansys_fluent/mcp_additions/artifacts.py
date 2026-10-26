"""Bounded data exports and reproducible native Fluent contour figures."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import uuid

import numpy as np
from ansys.fluent.core.fields.field_data_interfaces import ScalarFieldDataRequest

from .geometry import _geometry, field_metadata


def _identity(path: Path) -> dict:
    return {"path": str(path), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def export_surface_data(solver, surfaces: list[str], field: str, output: str,
                        max_faces: int = 100000) -> dict:
    """Write geometry-linked face values to NPZ with a JSON index and hashes.

    The response stays small. Local arrays retain exact connectivity and
    invalid values; invalid data are counted rather than replaced with zero.
    Face ordering is the field service's ordering within each selected surface.
    """
    if isinstance(max_faces, bool) or not 1 <= max_faces <= 1000000:
        raise ValueError("max_faces must be between 1 and 1000000")
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
        surfaces=surfaces, field_name=field, node_value=False, boundary_value=True))
    arrays, index = {}, {}
    for i, (name, g) in enumerate(geometry.items()):
        v = np.asarray(values[name]).reshape(-1)
        if len(v) != len(g.face_centroids):
            raise ValueError(f"Scalar/face alignment failed: {name}")
        prefix = f"s{i}"
        arrays.update({f"{prefix}_vertices": g.vertices,
                       f"{prefix}_connectivity": g.connectivity,
                       f"{prefix}_centroids": g.face_centroids,
                       f"{prefix}_values": v})
        index[name] = {"prefix": prefix, "faces": len(v), "nonfinite": int((~np.isfinite(v)).sum())}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    record = {"field": field, "coordinates": "m", "field_metadata": field_metadata(solver, field),
              "location": "face", "boundary_values": True, "surfaces": index,
              "connectivity": "flat: vertex count followed by zero-based vertex IDs for each face",
              "artifact": _identity(destination)}
    with sidecar.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
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
    picture_before = graphics.picture.get_state()
    mode_before = solver.settings.setup.general.solver.get_state()
    destination.parent.mkdir(parents=True, exist_ok=True)
    contours.create(name=name)
    try:
        obj = contours[name]
        obj.set_state({"field": field, "surfaces_list": surfaces,
                       "options": {"filled": True, "node_values": False, "boundary_values": True},
                       "range_options": {"global_range": False, "auto_range": False,
                                         "clip_to_range": False, "minimum": minimum, "maximum": maximum}})
        obj.display()
        graphics.views.restore_view(view_name=view)
        graphics.views.auto_scale()
        graphics.picture.use_window_resolution = False
        graphics.picture.x_resolution = width
        graphics.picture.y_resolution = height
        graphics.views.save_view(view_name=name)
        graphics.views.write_views(file_name=str(view_file), view_list=[name])
        record = {"field": field, "surfaces": surfaces, "view": view,
                  "source_pair": source_identity, "source_loaded": True,
                  "contour": obj.get_state(), "camera_file": _identity(view_file),
                  "picture": graphics.picture.get_state(), "native": True,
                  "field_metadata": field_metadata(solver, field), "location": "face"}
        graphics.picture.save_picture(file_name=str(destination))
        data = destination.read_bytes()
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Fluent did not write a PNG")
        record["artifact"] = _identity(destination)
        record["resolution"] = [int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")]
        if record["resolution"] != [width, height]:
            raise RuntimeError(f"Unexpected PNG dimensions: {record['resolution']}")
        if solver.settings.setup.general.solver.get_state() != mode_before:
            raise RuntimeError("Solver mode changed during graphics export")
        with sidecar.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, indent=2)
        return {**record, "metadata": _identity(sidecar)}
    finally:
        contours.delete(name_list=[name])
        graphics.views.delete_view(view_name=name)
        graphics.picture.set_state(picture_before)
