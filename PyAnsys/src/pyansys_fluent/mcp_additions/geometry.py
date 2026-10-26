"""Quantitative surface evidence, without inferring CAD features from names."""
from __future__ import annotations

import hashlib

import numpy as np
from ansys.fluent.core.fields.field_data_interfaces import (
    ScalarFieldDataRequest, SurfaceDataType, SurfaceFieldDataRequest,
)


def field_metadata(solver, field):
    """Keep the native quantity/domain; unknown unit mappings stay unknown."""
    info = solver.fields._field_info._get_scalar_fields_info()[field]
    units = {"temperature": "K", "velocity": "m/s", "pressure": "Pa",
             "density": "kg/m^3", "length": "m", "dimensionless": "1"}
    return {**info, "unit_si": units.get(info.get("quantity_name")),
            "unit_basis": "SI quantity mapping; null means not mapped"}


def _geometry(solver, surfaces: list[str]):
    if not surfaces or len(surfaces) > 32 or len(set(surfaces)) != len(surfaces):
        raise ValueError("Select 1 to 32 distinct surface names")
    available = solver.fields.field_data.surfaces.allowed_values()
    missing = sorted(set(surfaces) - set(available))
    if missing:
        raise ValueError(f"Unknown surfaces: {missing}")
    return solver.fields.field_data.get_field_data(SurfaceFieldDataRequest(
        surfaces=surfaces, flatten_connectivity=True,
        data_types=[SurfaceDataType.Vertices, SurfaceDataType.FacesConnectivity,
                    SurfaceDataType.FacesCentroid, SurfaceDataType.FacesNormal],
    ))


def _faces(data):
    raw = np.asarray(data.connectivity)
    offset = 0
    while offset < len(raw):
        count = int(raw[offset])
        if count < 3 or offset + count >= len(raw):
            raise ValueError("Invalid or incomplete face connectivity")
        ids = raw[offset + 1:offset + 1 + count]
        if np.any(ids < 0) or np.any(ids >= len(data.vertices)):
            raise ValueError("Face references an unavailable vertex")
        yield ids
        offset += count + 1


def _area_vectors(data):
    # Field-service face normals are not documented as area vectors. Measure
    # polygon area from connectivity instead of using their magnitude as area.
    result = []
    for face in _faces(data):
        p = np.asarray(data.vertices[face], dtype=float)
        result.append(np.cross(p[1:-1] - p[0], p[2:] - p[0]).sum(axis=0) / 2)
    vectors = np.asarray(result)
    if len(vectors) != len(data.face_centroids) or not np.isfinite(vectors).all():
        raise ValueError("Incomplete or nonfinite polygon areas")
    return vectors


def surface_geometry(solver, surfaces: list[str]) -> dict:
    """Return SI bounds, area-weighted centroid, and orientation per surface.

    Fluent field-service coordinates use SI, independent of display units.
    A normal resultant near zero is expected for a closed or curved surface;
    it is not a reliable direction for such a surface.
    """
    records = {}
    for name, data in _geometry(solver, surfaces).items():
        xyz = np.asarray(data.vertices, dtype=float)
        normals = np.asarray(data.face_normals, dtype=float)
        centres = np.asarray(data.face_centroids, dtype=float)
        if not len(xyz) or not len(normals) or not all(np.isfinite(a).all() for a in (xyz, normals, centres)):
            raise ValueError(f"Empty or nonfinite geometry: {name}")
        if len(normals) != len(centres):
            raise ValueError(f"Incomplete face geometry: {name}")
        vectors = _area_vectors(data)
        weights = np.linalg.norm(vectors, axis=1)
        area = float(weights.sum())
        if area <= 0:
            raise ValueError(f"Surface has no positive area: {name}")
        # Keep Fluent's normal orientation, using measured areas for weighting.
        lengths = np.linalg.norm(normals, axis=1)
        if np.any(lengths <= 0):
            raise ValueError(f"Undefined face normal: {name}")
        resultant = (normals / lengths[:, None] * weights[:, None]).sum(axis=0)
        magnitude = float(np.linalg.norm(resultant))
        records[name] = {
            "faces": len(normals), "vertices": len(xyz),
            "bounds_m": [xyz.min(axis=0).tolist(), xyz.max(axis=0).tolist()],
            "span_m": np.ptp(xyz, axis=0).tolist(),
            "area_m2": float(solver.fields.reduction.area(locations=[name])),
            "area_centroid_m": list(solver.fields.reduction.centroid(locations=[name])),
            "area_centroid_source": "Fluent native reduction",
            "polygon_area_m2": area,
            "normal_coherence": magnitude / area,
            "resultant_direction": (resultant / magnitude).tolist() if magnitude > area * 1e-12 else None,
        }
    return {"source": "Fluent surface field service", "coordinates": "SI", "surfaces": records}


def boundary_fingerprint(solver, surfaces: list[str]) -> dict:
    """Detect exact boundary tessellation changes independent of vertex/face IDs.

    Each face hashes sorted SI coordinates, then the sorted face hashes are
    hashed. Duplicates are retained. This detects tessellation as well as shape
    changes; it is not a tolerance-based CAD-equivalence test.
    """
    records = {}
    for name, data in _geometry(solver, surfaces).items():
        xyz = np.asarray(data.vertices, dtype="<f8")
        if not np.isfinite(xyz).all():
            raise ValueError(f"Nonfinite coordinates: {name}")
        xyz[xyz == 0] = 0  # Normalize negative zero only; retain all other bits.
        digests = []
        for face in _faces(data):
            points = xyz[face]
            order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
            digests.append(hashlib.sha256(points[order].tobytes()).digest())
        if len(digests) != len(data.face_centroids):
            raise ValueError(f"Incomplete boundary connectivity: {name}")
        records[name] = {"faces": len(digests), "sha256": hashlib.sha256(b"".join(sorted(digests))).hexdigest()}
    return {"algorithm": "sorted-face-coordinate-sha256-v1", "units": "m", "surfaces": records}


def surface_field_summary(solver, surfaces: list[str], field: str) -> dict:
    """Screen face scalar data before choosing a plot range; preserve invalids."""
    geometry = _geometry(solver, surfaces)
    values = solver.fields.field_data.get_field_data(ScalarFieldDataRequest(
        surfaces=surfaces, field_name=field, node_value=False, boundary_value=True,
    ))
    result = {}
    for name, data in geometry.items():
        a = np.asarray(values[name], dtype=float).reshape(-1)
        weights = np.linalg.norm(_area_vectors(data), axis=1)
        if len(a) != len(weights) or not len(a):
            raise ValueError(f"Scalar/geometry sample mismatch: {name}")
        finite = np.isfinite(a)
        valid = a[finite]
        covered = float(weights[finite].sum())
        result[name] = {
            "samples": len(a), "nonfinite": int((~finite).sum()),
            "minimum": float(valid.min()) if len(valid) else None,
            "maximum": float(valid.max()) if len(valid) else None,
            "polygon_area_weighted_mean": float(np.average(valid, weights=weights[finite])) if covered > 0 else None,
            "finite_area_fraction": covered / float(weights.sum()) if weights.sum() else None,
            "status": "complete" if finite.all() else "incomplete",
        }
    return {"field": field, "location": "face", "boundary_values": True,
            "metadata": field_metadata(solver, field), "surfaces": result}
