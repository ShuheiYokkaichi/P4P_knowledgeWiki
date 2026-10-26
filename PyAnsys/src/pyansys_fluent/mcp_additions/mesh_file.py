"""Read a bounded, local Fluent HDF5 mesh atlas without a solver.

Layout evidence: native Fluent 25.2 ``baseline.cas.h5`` and
``contracts-*/before-patch.cas.h5`` (mesh version 2, combined connectivity),
and ``Separator-purnanto-60k.msh.h5`` (version 2, split connectivity).
The geometry method follows P4P's ``inspect_fluent_mesh_h5.py`` and the
face-ID intersection correction in ``inspect_phase07b_geometry.py``.
This module neither imports PyFluent nor registers an MCP tool.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
from typing import Any

import h5py
import numpy as np


__all__ = ["inspect_mesh_file"]

_FACE_TYPES = {2: "interior", 3: "wall", 5: "pressure-outlet",
               7: "symmetry", 10: "velocity-inlet"}
_LIMITATIONS = [
    "Only native Fluent 25.2, mesh version 2, single 3D mesh, zero ID offsets; "
    "no lightweight, hierarchical, periodic/shadow, external or virtual storage.",
    "Areas are magnitudes of Newell polygon area vectors, summed over faces. "
    "Warped polygons give projected vector areas, not a native triangulated surface area.",
    "Centres are area-weighted arithmetic vertex centroids of faces; they are "
    "not Fluent face centroids, cell centroids, volume centroids or volume integrals.",
    "Normals follow stored vertex winding; outward direction is not verified. "
    "Coherence is norm(sum(area vectors))/sum(area magnitudes), not mesh quality. "
    "Cancellation is expected on curved or closed boundaries.",
    "Coordinates and areas remain in raw stored coordinate units and their square. "
    "The mesh units attribute is returned verbatim; it does not prove coordinate "
    "scaling or SI units. Missing units remain unknown.",
    "Interior face connectivity is not fully audited and interior geometry is not "
    "computed. Cell counts and types are topology metadata; no cell volumes, "
    "quality, solution fields, physical flow roles or scientific validity are inferred.",
    "Use a closed, saved file. Hash and stat checks detect changes but do not lock "
    "out writers. Byte bounds cover file size and decoded datasets/read selections, "
    "not all HDF5 metadata, decompression I/O, CPU time or process memory. "
    "This is not a sandbox for hostile HDF5 files; the MCP host owns access policy.",
]


def _limit(name: str, value: int, ceiling: int) -> None:
    if type(value) is not int or not 1 <= value <= ceiling:
        raise ValueError(f"{name} must be an integer in [1, {ceiling}]")


def _local(path: str) -> Path:
    if not isinstance(path, str) or not path or "\x00" in path:
        raise ValueError("Use a nonempty absolute local-host path")
    p = Path(path)
    # Reject UNC/device paths, URIs and NTFS alternate data streams.
    if (not p.is_absolute() or path.startswith(("\\\\", "//"))
            or ":" in path[len(p.drive):]):
        raise ValueError("Use an absolute local-host path, not a URI, UNC or stream")
    resolved = p.resolve(strict=True)
    if str(resolved).startswith(("\\\\", "//")):
        raise ValueError("The resolved path must be local")
    return resolved


def _object(parent: h5py.Group, path: str, kind: type) -> Any:
    current = parent
    for part in path.split("/"):
        if not isinstance(current, h5py.Group):
            raise ValueError(f"Expected group before {path}")
        if not isinstance(current.get(part, getlink=True), h5py.HardLink):
            raise ValueError(f"Missing or nonlocal HDF5 object: {current.name}/{part}")
        current = current[part]
    if not isinstance(current, kind):
        raise ValueError(f"Unsupported HDF5 object: {current.name}")
    return current


class _Reader:
    """Bound decoded dataset extent, read payload, chunks and fixed metadata."""

    def __init__(self, maximum: int, blocks: int):
        self.maximum = maximum
        self.blocks = blocks
        self.declared = 0
        self.read_bytes = 0
        self.seen: set[str] = set()

    def charge(self, amount: int) -> None:
        if amount < 0 or self.read_bytes + amount > self.maximum:
            raise ValueError("Decoded reads exceed max_read_bytes")
        self.read_bytes += amount

    def dataset(self, group: h5py.Group, path: str) -> h5py.Dataset:
        d = _object(group, path, h5py.Dataset)
        if (d.shape is None or d.dtype.kind not in "iufS" or d.dtype.itemsize < 1
                or d.is_virtual or d.external):
            raise ValueError(f"Unsupported dataset storage or dtype: {d.name}")
        # Only unfiltered or native deflate storage is evidenced here.
        if d.compression not in (None, "gzip") or d.scaleoffset is not None:
            raise ValueError(f"Unsupported dataset filter: {d.name}")
        plist = d.id.get_create_plist()
        if any(plist.get_filter(i)[0] != 1 for i in range(plist.get_nfilters())):
            raise ValueError(f"Unsupported dataset filter pipeline: {d.name}")
        size = math.prod(d.shape) * d.dtype.itemsize
        chunk = math.prod(d.chunks) * d.dtype.itemsize if d.chunks else 0
        if chunk > min(self.maximum, 64 * 1024 * 1024):
            raise ValueError(f"Decoded HDF5 chunk is too large: {d.name}")
        if d.name not in self.seen:
            if self.declared + size > self.maximum:
                raise ValueError("Dataset extents exceed max_read_bytes")
            self.declared += size
            self.seen.add(d.name)
        return d

    def read(self, d: h5py.Dataset, start: int = 0, stop: int | None = None) -> np.ndarray:
        if not d.shape:
            self.charge(d.dtype.itemsize)
            return np.asarray(d[()])
        stop = d.shape[0] if stop is None else stop
        if not 0 <= start <= stop <= d.shape[0]:
            raise ValueError(f"Invalid dataset slice: {d.name}")
        self.charge((stop - start) * math.prod(d.shape[1:]) * d.dtype.itemsize)
        return np.asarray(d[start:stop])

    def attribute(self, group: Any, name: str) -> int | str:
        if name not in group.attrs:
            raise ValueError(f"Missing attribute {group.name}@{name}")
        a = group.attrs.get_id(name)
        if (a.shape is None or math.prod(a.shape) != 1 or a.dtype.kind not in "iuS"
                or a.dtype.itemsize > 65536):
            raise ValueError(f"Unsupported scalar attribute {group.name}@{name}")
        self.charge(a.dtype.itemsize)
        value = np.asarray(group.attrs[name]).reshape(-1)[0]
        return bytes(value).decode("utf-8", "strict") if a.dtype.kind == "S" else int(value)

    def integer(self, group: Any, name: str) -> int:
        value = self.attribute(group, name)
        if type(value) is not int:
            raise ValueError(f"Expected integer attribute {group.name}@{name}")
        return value

    def text(self, group: h5py.Group, path: str) -> str:
        d = self.dataset(group, path)
        if d.dtype.kind != "S" or d.shape not in ((), (1,)) or d.dtype.itemsize > 65536:
            raise ValueError(f"Expected bounded fixed UTF-8 string: {d.name}")
        text = bytes(self.read(d).reshape(-1)[0]).decode("utf-8", "strict")
        if "\x00" in text:
            raise ValueError(f"Embedded NUL in {d.name}")
        return text

    def vector(self, group: h5py.Group, path: str, size: int) -> np.ndarray:
        d = self.dataset(group, path)
        if d.shape != (size,) or d.dtype.kind not in "iu" or d.dtype.itemsize > 8:
            raise ValueError(f"Expected integer vector of length {size}: {d.name}")
        v = self.read(d)
        if v.dtype.kind == "u" and np.any(v > np.iinfo(np.int64).max):
            raise ValueError(f"Integer exceeds signed 64-bit range: {d.name}")
        return v.astype(np.int64)

    def children(self, group: h5py.Group) -> list[str]:
        if not 1 <= len(group) <= self.blocks:
            raise ValueError(f"Empty group or max_blocks exceeded: {group.name}")
        return sorted(group)


def _partition(records: list[dict], total: int, label: str) -> None:
    cursor = 1
    for record in sorted(records, key=lambda x: x["first"]):
        if record["first"] != cursor or not cursor <= record["last"] <= total:
            raise ValueError(f"{label}: ranges overlap, have gaps or exceed declared count")
        cursor = record["last"] + 1
    if cursor != total + 1:
        raise ValueError(f"{label}: incomplete ID coverage")


def _zones(r: _Reader, mesh: h5py.Group, kind: str, total: int, maximum: int) -> list[dict]:
    g = _object(mesh, f"{kind}/zoneTopology", h5py.Group)
    count = r.integer(g, "nZones")
    if not 1 <= count <= maximum:
        raise ValueError(f"{kind}: max_zones exceeded or empty topology")
    values = {key: r.vector(g, key, count) for key in ("id", "dimension", "minId", "maxId")}
    optional = ("zoneType", "childZoneId", "shadowZoneId", "flags", "faceType", "cellType", "c0", "c1")
    values.update({key: r.vector(g, key, count) for key in optional if key in g})
    for key in ("childZoneId", "shadowZoneId", "flags"):
        if key in values and np.any(values[key] != 0):
            raise ValueError(f"Unsupported {kind} topology: nonzero {key}")
    if len(set(values["id"].tolist())) != count or np.any(values["id"] <= 0):
        raise ValueError(f"{kind}: zone IDs must be distinct and positive")
    if np.any(values["dimension"] != 3):
        raise ValueError(f"{kind}: only dimension-3 zone topology is evidenced")
    names: list[str | None] = [None] * count
    if "name" in g:
        decoded = r.text(g, "name").split(";")
        if decoded[-1] == "":
            decoded.pop()
        if len(decoded) != count or any(not n or len(n) > 1024 for n in decoded):
            raise ValueError(f"{kind}: invalid semicolon-delimited zone names")
        names = decoded
    records = []
    for i in range(count):
        code = int(values["zoneType"][i]) if "zoneType" in values else None
        if kind == "faces" and code not in _FACE_TYPES:
            raise ValueError(f"Unsupported face zone type: {code}")
        record = {"id": int(values["id"][i]), "name": names[i],
                  "dimension": int(values["dimension"][i]),
                  "first": int(values["minId"][i]), "last": int(values["maxId"][i]),
                  "zone_type_code": code,
                  "zone_type": (_FACE_TYPES[code] if kind == "faces" else
                                "fluid" if kind == "cells" and code == 1 else None)}
        record["count"] = record["last"] - record["first"] + 1
        record[{"faces": "face_count", "cells": "cell_count", "nodes": "node_count"}[kind]] = record["count"]
        record["source"] = g.name
        record["stored_properties"] = {key: int(values[key][i]) for key in optional if key in values}
        records.append(record)
    _partition(records, total, g.name)
    return records


def _coordinates(r: _Reader, mesh: h5py.Group, count: int) -> tuple[np.ndarray, list[dict]]:
    group = _object(mesh, "nodes/coords", h5py.Group)
    sections = []
    for key in r.children(group):
        d = r.dataset(group, key)
        first, last = r.integer(d, "minId"), r.integer(d, "maxId")
        if d.shape != (last - first + 1, 3) or d.dtype.kind != "f" or d.dtype.itemsize != 8:
            raise ValueError(f"Expected native (N, 3) float64 coordinates: {d.name}")
        sections.append({"first": first, "last": last, "source": d.name, "dataset": d})
    _partition(sections, count, group.name)
    if count * 3 * 8 > r.maximum:
        raise ValueError("Coordinate allocation exceeds max_read_bytes")
    coordinates = np.empty((count, 3), dtype=np.float64)
    for section in sections:
        data = r.read(section.pop("dataset"))
        if not np.all(np.isfinite(data)):
            raise ValueError(f"Nonfinite coordinates: {section['source']}")
        coordinates[section["first"] - 1:section["last"]] = data
    return coordinates, sections


def _geometry(r: _Reader, mesh: h5py.Group, points: np.ndarray, zones: list[dict],
              faces: int, max_values: int, max_vertices: int) -> list[dict]:
    group = _object(mesh, "faces/nodes", h5py.Group)
    sections = []
    values_total = 0
    for key in r.children(group):
        g = _object(group, key, h5py.Group)
        first, last = r.integer(g, "minId"), r.integer(g, "maxId")
        counts, ids = r.dataset(g, "nnodes"), r.dataset(g, "nodes")
        if (counts.shape != (last - first + 1,) or counts.dtype.kind not in "iu"
                or counts.dtype.itemsize > 8 or len(ids.shape) != 1
                or ids.dtype.kind not in "iu" or ids.dtype.itemsize > 8):
            raise ValueError(f"Unsupported face connectivity: {g.name}")
        values_total += ids.shape[0]
        if values_total > max_values:
            raise ValueError("Connectivity extent exceeds max_connectivity_values")
        sections.append({"first": first, "last": last, "source": g.name,
                         "counts": counts, "ids": ids})
    _partition(sections, faces, group.name)
    boundaries = [z for z in zones if z["zone_type_code"] != 2]
    states = {z["id"]: {"area": 0.0, "vector": np.zeros(3), "centre": np.zeros(3),
                         "minimum": np.full(3, np.inf), "maximum": np.full(3, -np.inf),
                         "faces": 0, "area_min": math.inf, "area_max": 0.0,
                         "slices": [], "nodes_per_face": {}} for z in boundaries}
    for section in sorted(sections, key=lambda s: s["first"]):
        intersections = [(z, max(z["first"], section["first"]), min(z["last"], section["last"]))
                         for z in boundaries
                         if z["first"] <= section["last"] and z["last"] >= section["first"]]
        if not intersections:
            continue  # No interior node-ID payload or geometry is needed.
        d = section["counts"]
        counts = r.vector(d.parent, d.name.rsplit("/", 1)[1], d.shape[0])
        if np.any(counts < 3) or np.any(counts > max_vertices):
            raise ValueError(f"Face vertex count outside [3, max_vertices_per_face]: {d.name}")
        offsets = np.empty(len(counts) + 1, dtype=np.int64)
        offsets[0] = 0
        np.cumsum(counts, out=offsets[1:])
        if int(offsets[-1]) != section["ids"].shape[0]:
            raise ValueError(f"Face-node count mismatch: {section['source']}")
        for zone, low, high in intersections:
            start, stop = low - section["first"], high - section["first"] + 1
            node_start, node_stop = int(offsets[start]), int(offsets[stop])
            ids = r.read(section["ids"], node_start, node_stop)
            if np.any(ids < 1) or np.any(ids > len(points)):
                raise ValueError(f"Out-of-range boundary node ID: {section['source']}")
            ids = ids.astype(np.int64)
            state = states[zone["id"]]
            for index in range(start, stop):
                begin, end = int(offsets[index]) - node_start, int(offsets[index + 1]) - node_start
                local = ids[begin:end]
                if len(np.unique(local)) != len(local):
                    raise ValueError(f"Repeated vertex on face {section['first'] + index}")
                p = points[local - 1]
                shifted = p - p[0]
                vector = 0.5 * np.cross(shifted, np.roll(shifted, -1, axis=0)).sum(axis=0)
                area = math.hypot(*vector)
                if not math.isfinite(area) or area <= 0:
                    raise ValueError(f"Degenerate/nonfinite boundary face {section['first'] + index}")
                centre = p[0] + shifted.mean(axis=0)
                total = state["area"] + area
                state["centre"] += (centre - state["centre"]) * (area / total)
                state["area"] = total
                state["vector"] += vector
                state["minimum"] = np.minimum(state["minimum"], p.min(axis=0))
                state["maximum"] = np.maximum(state["maximum"], p.max(axis=0))
                state["area_min"] = min(state["area_min"], area)
                state["area_max"] = max(state["area_max"], area)
                state["faces"] += 1
                n = str(len(local))
                state["nodes_per_face"][n] = state["nodes_per_face"].get(n, 0) + 1
            state["slices"].append({"source": section["source"], "face_ids_inclusive": [low, high],
                                     "flat_nodes_slice_half_open": [node_start, node_stop]})
    result = []
    for zone in boundaries:
        s = states[zone["id"]]
        if s["faces"] != zone["count"] or not math.isfinite(s["area"]) or s["area"] <= 0:
            raise ValueError(f"Incomplete or nonfinite geometry: zone {zone['id']}")
        magnitude = math.hypot(*s["vector"])
        coherence = magnitude / s["area"]
        if not math.isfinite(coherence) or coherence > 1 + 1e-10:
            raise ValueError(f"Invalid normal coherence: zone {zone['id']}")
        # Very small sums have no stable mean direction; preserve their vector.
        direction = (s["vector"] / magnitude).tolist() if coherence > 1e-12 else None
        result.append({"zone_id": zone["id"], "face_count": s["faces"],
                       "bounds": _bounds(s["minimum"], s["maximum"]),
                       "area": s["area"],
                       "face_area": {"minimum": s["area_min"], "maximum": s["area_max"],
                                     "mean": s["area"] / s["faces"]},
                       "area_weighted_vertex_centroid": s["centre"].tolist(),
                       "oriented_area_vector": s["vector"].tolist(),
                       "area_weighted_mean_normal": (s["vector"] / s["area"]).tolist(),
                       "mean_normal_direction": direction, "normal_coherence": coherence,
                       "direction_coherence_floor": 1e-12,
                       "nodes_per_face": s["nodes_per_face"], "source_slices": s["slices"]})
    return result


def _bounds(minimum: np.ndarray, maximum: np.ndarray) -> dict:
    return {"minimum": minimum.tolist(), "maximum": maximum.tolist(),
            "span": (maximum - minimum).tolist()}


def _fingerprint(s: os.stat_result) -> tuple[int, ...]:
    # Windows/Python 3.13 path stat and descriptor fstat expose different
    # st_ctime meanings. Identity, length, mtime and two content hashes agree.
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def _sha256(stream: Any, size: int) -> str:
    stream.seek(0)
    digest = hashlib.sha256()
    remaining = size
    while remaining:
        block = stream.read(min(1024 * 1024, remaining))
        if not block:
            raise RuntimeError("Source file shrank during hashing")
        digest.update(block)
        remaining -= len(block)
    if stream.read(1):
        raise RuntimeError("Source file grew during hashing")
    return digest.hexdigest()


def inspect_mesh_file(
    path: str,
    *,
    allowed_root: str,
    expected_sha256: str | None = None,
    max_file_bytes: int = 256 * 1024 * 1024,
    max_read_bytes: int = 128 * 1024 * 1024,
    max_nodes: int = 2_000_000,
    max_faces: int = 5_000_000,
    max_cells: int = 2_000_000,
    max_boundary_faces: int = 200_000,
    max_zones: int = 512,
    max_blocks: int = 128,
    max_connectivity_values: int = 20_000_000,
    max_vertices_per_face: int = 128,
) -> dict[str, Any]:
    """Return topology, raw-coordinate extents and boundary geometry with provenance.

    ``path`` and ``allowed_root`` must be absolute local paths on the MCP host.
    The resolved regular file must stay below the resolved caller-owned root.
    The caller must choose an authorized root; this function cannot establish
    authorization. Symlink escapes, UNC/device/URI paths and data streams fail.

    Only the evidenced Fluent 25.2 version-2 layouts in ``.cas.h5`` and
    ``.msh.h5`` are accepted. Every node and zone ID range must form an exact,
    disjoint partition starting at 1. Boundary geometry uses intersections of
    face-zone ranges and connectivity-block ranges, regardless of block names.
    All boundary faces are inspected or the call fails; there is no sampling,
    partial-success truncation, or automatic increase of resource limits.

    ``max_file_bytes`` bounds each of two full SHA-256 passes.
    ``max_read_bytes`` independently bounds the sum of declared decoded extents
    of accessed datasets, and cumulative selected dataset/attribute bytes read.
    Coordinate arrays, integer offsets and HDF5 caches add memory overhead.
    Counts, total zones, blocks per group, connectivity extent and vertices per face have
    separate limits. Interior-only blocks are checked structurally but their
    payloads are not read; mixed blocks require all vertex counts for offsets.

    Units are metadata, not an implicit conversion. Area and centroid methods,
    normal winding limitations and uninspected interior semantics are returned
    in ``limitations``. Unknown cell/node type labels remain null. Names never
    determine a zone's type or flow role. No native volume semantics are used.

    Requires h5py and numpy only. Raises ValueError for unsupported/invalid data
    or limits, PermissionError for a root escape, RuntimeError for detected
    source changes, and native I/O/HDF5 errors for unreadable/corrupt files.
    """
    limits = {
        "max_file_bytes": (max_file_bytes, 1024 * 1024 * 1024),
        "max_read_bytes": (max_read_bytes, 512 * 1024 * 1024),
        "max_nodes": (max_nodes, 5_000_000), "max_faces": (max_faces, 20_000_000),
        "max_cells": (max_cells, 10_000_000),
        "max_boundary_faces": (max_boundary_faces, 1_000_000),
        "max_zones": (max_zones, 4096), "max_blocks": (max_blocks, 4096),
        "max_connectivity_values": (max_connectivity_values, 100_000_000),
        "max_vertices_per_face": (max_vertices_per_face, 1024),
    }
    for name, (value, ceiling) in limits.items():
        _limit(name, value, ceiling)
    if max_vertices_per_face < 3:
        raise ValueError("max_vertices_per_face must be at least 3")
    if expected_sha256 is not None and (not isinstance(expected_sha256, str)
            or re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256) is None):
        raise ValueError("expected_sha256 must be 64 hexadecimal characters")
    root, target = _local(allowed_root), _local(path)
    if not root.is_dir():
        raise ValueError("allowed_root must be an existing directory")
    if not target.is_relative_to(root):
        raise PermissionError("Resolved mesh file is outside allowed_root")
    if not target.name.lower().endswith((".cas.h5", ".msh.h5")):
        raise ValueError("Only native .cas.h5 and .msh.h5 files are supported")
    before_open = target.stat()
    if not stat.S_ISREG(before_open.st_mode) or not 1 <= before_open.st_size <= max_file_bytes:
        raise ValueError("Expected a nonempty regular file within max_file_bytes")
    r = _Reader(max_read_bytes, max_blocks)
    with target.open("rb") as stream:
        initial = os.fstat(stream.fileno())
        if not stat.S_ISREG(initial.st_mode) or not 1 <= initial.st_size <= max_file_bytes:
            raise ValueError("Expected a nonempty regular file within max_file_bytes")
        if (_fingerprint(before_open) != _fingerprint(initial)
                or target.resolve(strict=True) != target):
            raise RuntimeError("Source file or resolved path changed while opening")
        digest = _sha256(stream, initial.st_size)
        if expected_sha256 is not None and digest != expected_sha256.lower():
            raise ValueError("Source SHA-256 does not match expected_sha256")
        stream.seek(0)
        try:
            with h5py.File(stream, "r") as handle, np.errstate(over="raise", invalid="raise", divide="raise"):
                meshes = _object(handle, "meshes", h5py.Group)
                if len(meshes) != 1 or "1" not in meshes:
                    raise ValueError("Only a single mesh at /meshes/1 is supported")
                mesh = _object(meshes, "1", h5py.Group)
                if r.integer(mesh, "version") != 2 or r.integer(mesh, "dimension") != 3:
                    raise ValueError("Only Fluent mesh version 2, dimension 3 is supported")
                for key in ("cellOffset", "faceOffset", "nodeOffset"):
                    if r.integer(mesh, key) != 0:
                        raise ValueError("Only zero mesh ID offsets are supported")
                if "lightweight" in mesh.attrs and r.integer(mesh, "lightweight") != 0:
                    raise ValueError("Lightweight meshes are unsupported")
                settings = _object(handle, "settings", h5py.Group)
                metadata = {key.lower(): r.text(settings, key) for key in ("Version", "Solver", "Origin")}
                if (metadata["version"] != "25.2" or metadata["solver"] not in
                        ("ANSYS_FLUENT", "ANSYS_FLUENT_MESHING")):
                    raise ValueError("Only evidenced Fluent/Fluent Meshing 25.2 writers are supported")
                counts = {kind: r.integer(mesh, key) for kind, key in
                          (("nodes", "nodeCount"), ("faces", "faceCount"), ("cells", "cellCount"))}
                for kind, maximum in (("nodes", max_nodes), ("faces", max_faces), ("cells", max_cells)):
                    if not 1 <= counts[kind] <= maximum:
                        raise ValueError(f"Invalid {kind} count or max_{kind} exceeded")
                zones = {kind: _zones(r, mesh, kind, counts[kind], max_zones)
                         for kind in ("nodes", "faces", "cells")}
                if sum(len(v) for v in zones.values()) > max_zones:
                    raise ValueError("Combined zone inventory exceeds max_zones")
                boundary_count = sum(z["count"] for z in zones["faces"] if z["zone_type_code"] != 2)
                if boundary_count > max_boundary_faces:
                    raise ValueError("Boundary faces exceed max_boundary_faces")
                points, coordinate_sources = _coordinates(r, mesh, counts["nodes"])
                boundaries = _geometry(r, mesh, points, zones["faces"], counts["faces"],
                                       max_connectivity_values, max_vertices_per_face)
                units = r.attribute(mesh, "units") if "units" in mesh.attrs else None
                result = {
                    "schema": "fluent.mesh-file-atlas.v1", "source_kind": "native_fluent_hdf5",
                    "captured_at_utc": datetime.now(timezone.utc).isoformat(),
                    "source": {"path": str(target), "allowed_root": str(root), "host": socket.gethostname(),
                               "size_bytes": initial.st_size, "sha256": digest,
                               "mtime_ns": initial.st_mtime_ns, "mesh_path": mesh.name,
                               "mesh_version": 2, "dimension": 3, "writer": metadata,
                               "coordinate_datasets": coordinate_sources},
                    "units": {"stored_value": units,
                              "source": f"{mesh.name}@units" if units is not None else None,
                              "coordinate_basis": "raw stored values; scale to SI not established",
                              "area_basis": "square of raw coordinate units", "conversion_applied": False},
                    "counts": {**counts, "boundary_faces": boundary_count,
                               "interior_faces": counts["faces"] - boundary_count},
                    "bounds": _bounds(points.min(axis=0), points.max(axis=0)),
                    "zones": zones, "boundaries": boundaries,
                    "methods": {"area": "sum of magnitudes of translated Newell polygon area vectors",
                                "centre": "area-weighted arithmetic vertex centroid of each face",
                                "normal": "stored winding; outward direction unverified",
                                "coherence": "norm(sum(area vectors))/sum(area magnitudes)"},
                    "limits": {key: value for key, (value, _) in limits.items()},
                    "read_accounting": {"declared_dataset_bytes": r.declared,
                                        "selected_dataset_and_attribute_bytes": r.read_bytes,
                                        "hash_passes": 2, "hash_bytes_per_pass": initial.st_size},
                    "limitations": list(_LIMITATIONS),
                }
                # Reject any nonfinite derived value rather than emitting NaN/Infinity.
                json.dumps(result, allow_nan=False)
        except FloatingPointError as exc:
            raise ValueError("Nonfinite or overflowing mesh geometry arithmetic") from exc
        if (_fingerprint(initial) != _fingerprint(os.fstat(stream.fileno()))
                or _fingerprint(initial) != _fingerprint(target.stat())
                or target.resolve(strict=True) != target):
            raise RuntimeError("Source file or resolved path changed during inspection")
        if _sha256(stream, initial.st_size) != digest:
            raise RuntimeError("Source file bytes changed during inspection")
        if (_fingerprint(initial) != _fingerprint(os.fstat(stream.fileno()))
                or _fingerprint(initial) != _fingerprint(target.stat())):
            raise RuntimeError("Source file changed during final identity check")
    result["source"]["stability_check"] = "matching SHA-256 before/after inspection and matching stat identity"
    return result
