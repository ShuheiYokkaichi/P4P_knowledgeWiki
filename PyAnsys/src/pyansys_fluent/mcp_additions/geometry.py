"""Quantitative surface evidence, without inferring CAD features from names."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

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
    result = solver.fields.field_data.get_field_data(SurfaceFieldDataRequest(
        surfaces=surfaces, flatten_connectivity=True,
        data_types=[SurfaceDataType.Vertices, SurfaceDataType.FacesConnectivity,
                    SurfaceDataType.FacesCentroid, SurfaceDataType.FacesNormal],
    ))
    if set(result) != set(surfaces):
        raise ValueError("Fluent returned incomplete surface coverage")
    return result


def _faces(data):
    raw = np.asarray(data.connectivity)
    offset = 0
    while offset < len(raw):
        count = int(raw[offset])
        if count < 2 or offset + count >= len(raw):
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
        if len(face) < 3:
            raise ValueError("Surface area/orientation requires 3D polygon faces; 2D edges are unsupported here")
        p = np.asarray(data.vertices[face], dtype=float)
        result.append(np.cross(p[1:-1] - p[0], p[2:] - p[0]).sum(axis=0) / 2)
    vectors = np.asarray(result)
    if len(vectors) != len(data.face_centroids) or not np.isfinite(vectors).all():
        raise ValueError("Incomplete or nonfinite polygon areas")
    return vectors


def surface_geometry(solver, surfaces: list[str]) -> dict:
    """Characterize selected 3D polygon surfaces for geometry-aware decisions.

    Return SI bounds/spans, native area/centroid, principal axes, fitted-plane
    deviations and normal coherence. These are measured geometry descriptors,
    not inferred CAD features. Principal axes can rotate in symmetric planes.
    Fits weight each returned vertex equally; mesh density and duplicate
    vertices can change the axes and plane metrics without changing CAD.
    A near-zero normal resultant is not a reliable direction. The selected-set
    balance describes normal cancellation; it does not prove watertightness.
    Fluent field-service coordinates are SI, independent of display units.
    """
    records, all_points, set_resultants = {}, [], []
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
        centred = xyz - xyz.mean(axis=0)
        _, _, axes = np.linalg.svd(centred, full_matrices=False)
        projected = centred @ axes.T
        set_resultants.append(resultant)
        all_points.append(xyz)
        records[name] = {
            "faces": len(normals), "vertices": len(xyz),
            "bounds_m": [xyz.min(axis=0).tolist(), xyz.max(axis=0).tolist()],
            "span_m": np.ptp(xyz, axis=0).tolist(),
            "area_m2": float(solver.fields.reduction.area(locations=[name])),
            "area_centroid_m": list(solver.fields.reduction.centroid(locations=[name])),
            "area_centroid_source": "Fluent native reduction",
            "polygon_area_m2": area,
            "principal_axes": axes.tolist(),
            "fit_basis": "equal weight per returned vertex, including duplicates; mesh-density dependent",
            "principal_spans_m": np.ptp(projected, axis=0).tolist(),
            "plane_fit_max_distance_m": float(np.abs(projected[:, -1]).max()),
            "plane_fit_rms_distance_m": float(np.sqrt(np.mean(projected[:, -1] ** 2))),
            "normal_coherence": magnitude / area,
            "resultant_direction": (resultant / magnitude).tolist() if magnitude > area * 1e-12 else None,
        }
    combined = np.concatenate(all_points)
    total_area = sum(r["polygon_area_m2"] for r in records.values())
    return {"source": "Fluent surface field service plus native reductions", "coordinates": "SI",
            "surfaces": records, "selected_set": {
                "bounds_m": [combined.min(axis=0).tolist(), combined.max(axis=0).tolist()],
                "normal_balance_ratio": float(np.linalg.norm(np.sum(set_resultants, axis=0)) / total_area),
                "normal_balance_basis": "polygon-area-weighted native face normals; cancellation is not closure proof"}}


def boundary_fingerprint(solver, surfaces: list[str], reference: dict | None = None) -> dict:
    """Detect exact boundary tessellation changes independent of vertex/face IDs.

    Each face hashes sorted SI coordinates, then the sorted face hashes are
    hashed. Duplicates are retained. This detects tessellation as well as shape
    changes; it is not a tolerance-based CAD-equivalence test. Equal hashes
    mean equal multisets of face-coordinate sets. Winding, cyclic ordering,
    node sharing, normals, boundary conditions and interior topology are not
    compared. The binary-digest algorithm differs from the older P4P HDF5
    script. Optional reference comparison requires identical surface names.
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
        if not digests or len(digests) != len(data.face_centroids):
            raise ValueError(f"Incomplete boundary connectivity: {name}")
        records[name] = {"faces": len(digests), "sha256": hashlib.sha256(b"".join(sorted(digests))).hexdigest()}
    result = {"algorithm": "sorted-face-coordinate-sha256-v1", "units": "m", "surfaces": records}
    if reference is not None:
        if reference.get("algorithm") != result["algorithm"] or reference.get("units") != "m":
            raise ValueError("Reference algorithm and coordinate units must match")
        previous = reference.get("surfaces")
        if not isinstance(previous, dict) or not previous:
            raise ValueError("Reference must contain nonempty surface fingerprints")
        if set(previous) != set(records):
            raise ValueError("Compare the same explicit surface selection; renaming/removal requires a separate inventory check")
        for name, item in previous.items():
            if (not isinstance(item, dict) or type(item.get("faces")) is not int or item["faces"] <= 0
                    or not isinstance(item.get("sha256"), str) or re.fullmatch("[0-9a-f]{64}", item["sha256"]) is None):
                raise ValueError(f"Invalid reference fingerprint: {name}")
        differences = {}
        for name in sorted(set(previous) | set(records)):
            if name not in previous:
                differences[name] = "added"
            elif name not in records:
                differences[name] = "missing"
            elif any(previous[name][key] != records[name][key] for key in ("faces", "sha256")):
                differences[name] = "face_coordinates_changed"
        result["comparison"] = {"status": "changed" if differences else "identical",
                                "differences": differences, "surface_mapping": "exact names"}
    return result


def surface_field_summary(solver, surfaces: list[str], field: str, reference: dict | None = None) -> dict:
    """Measure 3D face scalar ranges, invalid coverage and area-weighted means.

    Return per-surface extrema, nonfinite counts, finite polygon-area coverage
    and a polygon-area-weighted mean. Sampling requests boundary face values;
    adjacent-cell fallback is possible. These ranges need not match nodal
    contours or contours with boundary values disabled. No values are clipped.

    An optional earlier summary yields one shared observed range for the same
    explicit surfaces/field/domain/units/sampling, useful for comparable figure
    scales. Unknown units or incompatible metadata refuse comparison. This is
    an observed range, not a recommended physical bound or convergence test.
    Caller must establish common physical meaning across cases/stages.
    """
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
    finite_records = [r for r in result.values() if r["minimum"] is not None]
    observed_range = ([min(r["minimum"] for r in finite_records), max(r["maximum"] for r in finite_records)]
                      if finite_records else None)
    out = {"field": field, "location": "face", "boundary_values": True,
            "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "sampling_basis": "boundary-face-indexed values; Fluent may use adjacent-cell values where a boundary value is unavailable",
            "metadata": field_metadata(solver, field), "surfaces": result,
            "observed_range": observed_range,
            "coverage_complete": all(r["status"] == "complete" for r in result.values())}
    if reference is not None:
        for key in ("field", "location", "boundary_values", "sampling_basis"):
            if reference.get(key) != out[key]:
                raise ValueError(f"Incompatible range reference: {key}")
        metadata = reference.get("metadata", {})
        for key in ("domain", "quantity_name", "unit_si", "unit_basis"):
            if metadata.get(key) != out["metadata"].get(key):
                raise ValueError(f"Incompatible range reference metadata: {key}")
        if out["metadata"].get("unit_si") is None:
            raise ValueError("Cannot compare ranges with unmapped units")
        previous = reference.get("surfaces", {})
        if set(previous) != set(result):
            raise ValueError("Range comparison requires the same explicit surface selection")
        limits = []
        for record in list(previous.values()) + list(result.values()):
            low, high = record.get("minimum"), record.get("maximum")
            if low is None and high is None:
                continue
            if (type(low) not in (int, float) or type(high) not in (int, float)
                    or not np.isfinite([low, high]).all() or low > high):
                raise ValueError("Invalid reference range")
            limits.append((low, high))
        out["shared_observed_range"] = [min(v[0] for v in limits), max(v[1] for v in limits)] if limits else None
        out["comparison_scope"] = "current and caller-supplied reference; invalid samples excluded, no physical bounds inferred"
        out["reference_captured_at_utc"] = reference.get("captured_at_utc")
    return out
