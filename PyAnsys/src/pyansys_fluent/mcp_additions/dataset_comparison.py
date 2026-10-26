"""Offline scalar comparison of local ``fluent.surface-dataset.v1`` exports.

Uses the saved contract in artifacts.export_surface_data and the exact face
coordinate method in P4P's mesh_boundary_fingerprint.py. It does not import
PyFluent, register a tool, write files, interpolate, or identify physical roles.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import zipfile

import numpy as np


__all__ = ["compare_surface_datasets"]

_SCHEMA = "fluent.surface-dataset.v1"
_CONNECTIVITY = "flat: vertex count followed by zero-based vertex IDs for each face"
_SAMPLING = {
    "node": "vertex-aligned",
    "face": "boundary-face-indexed; boundary or adjacent-cell values, not guaranteed centroid evaluation",
}
_SIDECAR_BYTES = 1024 * 1024
_HEADER_BYTES = 10000
_LIMITATIONS = [
    "Only explicit v1 exports with float32/float64 geometry and scalars and "
    "integer flat connectivity are supported. Older exports need a new export; "
    "missing schema, sampling or units are not inferred.",
    "Exact equality is of stored numeric coordinates, widened losslessly to "
    "float64 with signed zero normalized. No geometry tolerance, nearest-point "
    "match, interpolation, unit conversion or surface-name aliasing is used.",
    "The topology check covers the multiset of boundary face-coordinate sets "
    "and vertex-coordinate multiplicities. Winding, node sharing, normals, "
    "interior topology and boundary-condition settings are not compared. "
    "Centroids must be finite and aligned in size but are not matching keys.",
    "Coincident samples are comparable only when their multiplicities match "
    "and each input group has one exact scalar value or one nonfinite class. "
    "This does not establish identities of individual coincident nodes/faces.",
    "Deltas are B minus A and means give each exported sample equal weight. "
    "Only pairs with two finite values enter delta statistics and changed counts. "
    "NaN and signed infinities retain separate counts; they are never zeroed. "
    "Finite subtraction or aggregation overflow refuses comparison.",
    "Face values follow boundary-face ordering; Fluent may supply adjacent-cell "
    "values. They are not guaranteed evaluations at geometric centroids. "
    "Nodal and face sampling cannot be compared.",
    "A matching sidecar hash checks NPZ integrity, not provenance authenticity. "
    "The sidecar itself is not authenticated. Stored artifact paths are never "
    "opened; the caller selects local files and owns access authorization.",
    "Use closed, saved pairs. Hash and file-identity checks detect ordinary "
    "changes but do not lock out writers. Bounds apply per input to file size, "
    "decoded array bytes, array count, faces, vertices and samples; they are "
    "not a hard process-memory, ZIP-metadata or CPU-time limit.",
    "Matching exports do not prove common case origin, physical meaning, "
    "convergence or scientific validity. Observation metadata are reported, "
    "not required to be equal or interpreted as a time sequence.",
]


def _limit(name: str, value: int, ceiling: int) -> None:
    if type(value) is not int or not 1 <= value <= ceiling:
        raise ValueError(f"{name} must be an integer in [1, {ceiling}]")


def _local_pair(path: str) -> tuple[Path, Path]:
    if not isinstance(path, str) or not path or "\x00" in path:
        raise ValueError("Select an absolute local .npz path")
    selected = Path(path)
    if (not selected.is_absolute() or path.startswith(("\\\\", "//"))
            or ":" in path[len(selected.drive):] or selected.suffix != ".npz"):
        raise ValueError("Select an absolute local .npz path, not a URI, UNC or stream")
    parent = selected.parent.resolve(strict=True)
    pair = (parent / selected.name, parent / selected.with_suffix(".json").name)
    for item in pair:
        resolved = item.resolve(strict=True)
        if (item.is_symlink() or resolved.parent != parent
                or str(resolved).startswith(("\\\\", "//"))
                or not stat.S_ISREG(resolved.stat().st_mode)):
            raise ValueError("NPZ and inferred JSON must be regular local files in the selected directory")
    return pair


def _stamp(info: os.stat_result) -> tuple:
    # Windows/Python 3.13 can report different ctime through stat and fstat
    # for the same stable file. Keep cross-API identity to these four fields;
    # before/after content hashes supply the byte-integrity check.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def _unchanged(stream, path: Path, before: os.stat_result) -> None:
    if (not stat.S_ISREG(os.fstat(stream.fileno()).st_mode) or path.is_symlink()
            or _stamp(os.fstat(stream.fileno())) != _stamp(before)
            or _stamp(path.stat()) != _stamp(before)):
        raise ValueError(f"Input changed while reading: {path}")


def _digest(stream, maximum: int) -> str:
    stream.seek(0)
    digest, total = hashlib.sha256(), 0
    while block := stream.read(min(1024 * 1024, maximum - total + 1)):
        total += len(block)
        if total > maximum:
            raise ValueError("Input exceeds its byte limit")
        digest.update(block)
    return digest.hexdigest()


def _unique_object(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite_json(value, depth: int = 0) -> None:
    if depth > 32:
        raise ValueError("JSON nesting exceeds 32 levels")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Sidecar metadata must contain only finite numbers")
    if isinstance(value, dict):
        for item in value.values():
            _finite_json(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _finite_json(item, depth + 1)


def _text(value, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        raise ValueError(f"Missing or invalid {name}")


def _metadata(raw: bytes, max_samples: int) -> dict:
    record = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    _finite_json(record)
    if not isinstance(record, dict) or record.get("schema") != _SCHEMA:
        raise ValueError("Require explicit fluent.surface-dataset.v1 metadata; legacy exports are unsupported")
    sampling = record.get("sampling")
    if (sampling not in ("face", "node") or record.get("coordinates") != "m"
            or record.get("boundary_values") is not True
            or record.get("sampling_basis") != _SAMPLING[sampling]
            or record.get("connectivity") != _CONNECTIVITY):
        raise ValueError("Unsupported coordinates, sampling, connectivity or boundary-value policy")
    _text(record.get("field"), "field")
    metadata = record.get("field_metadata")
    if not isinstance(metadata, dict):
        raise ValueError("Require explicit field_metadata")
    for key in ("domain", "quantity_name", "unit_si", "unit_basis"):
        _text(metadata.get(key), f"field_metadata.{key}; unmapped units cannot be compared")
    observation = record.get("observation")
    if not isinstance(observation, dict):
        raise ValueError("Require the export observation record")
    _text(observation.get("captured_at_utc"), "observation.captured_at_utc")
    for key in ("iteration_expression", "flow_time_s"):
        if type(observation.get(key)) not in (int, float):
            raise ValueError(f"Require numeric observation.{key}")
    surfaces = record.get("surfaces")
    if not isinstance(surfaces, dict) or not 1 <= len(surfaces) <= 32:
        raise ValueError("Require 1 to 32 explicit surfaces")
    prefixes, totals = set(), dict.fromkeys(("faces", "vertices", "samples"), 0)
    for name, entry in surfaces.items():
        _text(name, "surface name")
        if not isinstance(entry, dict):
            raise ValueError(f"Invalid surface record: {name}")
        prefix = entry.get("prefix")
        if (not isinstance(prefix, str) or re.fullmatch(r"s(?:[0-9]|[12][0-9]|3[01])", prefix) is None
                or prefix in prefixes):
            raise ValueError("Require distinct native s0..s31 array prefixes")
        prefixes.add(prefix)
        for key in totals:
            count = entry.get(key)
            if type(count) is not int or not 1 <= count <= max_samples:
                raise ValueError(f"Invalid or excessive {key}: {name}")
            totals[key] += count
        if (entry["samples"] != entry["vertices" if sampling == "node" else "faces"]
                or type(entry.get("nonfinite")) is not int
                or not 0 <= entry["nonfinite"] <= entry["samples"]):
            raise ValueError(f"Invalid sample/nonfinite counts: {name}")
    if prefixes != {f"s{i}" for i in range(len(surfaces))}:
        raise ValueError("Surface prefixes must cover the native contiguous index")
    if any(count > max_samples for count in totals.values()):
        raise ValueError("Total faces, vertices or samples exceed max_samples")
    artifact = record.get("artifact")
    if (not isinstance(artifact, dict) or type(artifact.get("bytes")) is not int
            or artifact["bytes"] <= 0 or not isinstance(artifact.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]) is None):
        raise ValueError("Require native artifact byte count and SHA256")
    # artifact.path is provenance text only, never an input path.
    return record


def _header(member) -> tuple:
    version = np.lib.format.read_magic(member)
    if version == (1, 0):
        length_size, reader = 2, np.lib.format.read_array_header_1_0
    elif version == (2, 0):
        length_size, reader = 4, np.lib.format.read_array_header_2_0
    else:
        raise ValueError("Only native NPY v1/v2 members are supported")
    # NumPy checks max_header_size after reading the declared header. Bound
    # that declaration first, so a corrupt length cannot request a huge read.
    length_bytes = member.read(length_size)
    if len(length_bytes) != length_size:
        raise ValueError("Truncated NPY header length")
    length = int.from_bytes(length_bytes, "little")
    if not 0 < length <= _HEADER_BYTES:
        raise ValueError("NPY header exceeds its byte limit")
    raw = member.read(length)
    if len(raw) != length:
        raise ValueError("Truncated NPY header")
    return reader(io.BytesIO(length_bytes + raw), max_header_size=_HEADER_BYTES)


def _array_index(archive: zipfile.ZipFile, record: dict, maximum: int) -> dict:
    expected = {}
    for entry in record["surfaces"].values():
        for suffix, shape in (("vertices", (entry["vertices"], 3)),
                              ("centroids", (entry["faces"], 3)),
                              ("values", (entry["samples"],)), ("connectivity", None)):
            expected[f"{entry['prefix']}_{suffix}.npy"] = (suffix, shape, entry["faces"])
    members = archive.infolist()
    if len(members) != len(expected) or {item.filename for item in members} != set(expected):
        raise ValueError("NPZ must contain exactly the four native arrays per surface, without duplicates")
    if sum(item.file_size for item in members) > maximum:
        raise ValueError("Decoded NPZ members exceed max_array_bytes")
    index = {}
    for info in members:
        if (info.flag_bits & 1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                or info.file_size <= 0 or info.file_size > maximum):
            raise ValueError("Unsupported or excessive NPZ member storage")
        suffix, expected_shape, faces = expected[info.filename]
        with archive.open(info) as member:
            shape, fortran, dtype = _header(member)
            offset = member.tell()
        if (dtype.hasobject or dtype.fields is not None or dtype.subdtype is not None
                or any(type(n) is not int or n <= 0 for n in shape)):
            raise ValueError("Only nonempty, plain numeric arrays are supported")
        if suffix == "connectivity":
            valid = (len(shape) == 1 and shape[0] >= 4 * faces
                     and dtype.kind in "iu" and dtype.itemsize in (1, 2, 4, 8))
        else:
            valid = shape == expected_shape and dtype.kind == "f" and dtype.itemsize in (4, 8)
        if not valid:
            raise ValueError(f"Invalid shape or dtype: {info.filename}")
        nbytes = math.prod(shape) * dtype.itemsize
        if nbytes > maximum or offset + nbytes != info.file_size:
            raise ValueError(f"Invalid shape, dtype or payload extent: {info.filename}")
        index[info.filename] = (info, shape, fortran, dtype, offset, nbytes)
    return index


def _array(archive: zipfile.ZipFile, index: dict, name: str) -> np.ndarray:
    info, shape, fortran, dtype, offset, nbytes = index[name + ".npy"]
    with archive.open(info) as member:
        if len(member.read(offset)) != offset:
            raise ValueError("Truncated NPY header")
        payload = member.read(nbytes + 1)
        if len(payload) != nbytes:
            raise ValueError("Truncated or excess NPY payload")
    return np.frombuffer(payload, dtype=dtype).reshape(shape, order="F" if fortran else "C")


@contextmanager
def _dataset(path: str, max_file_bytes: int, max_array_bytes: int, max_samples: int):
    npz_path, json_path = _local_pair(path)
    with npz_path.open("rb") as data, json_path.open("rb") as sidecar:
        data_stat, json_stat = os.fstat(data.fileno()), os.fstat(sidecar.fileno())
        for info, maximum in ((data_stat, max_file_bytes), (json_stat, _SIDECAR_BYTES)):
            if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= maximum:
                raise ValueError("Input is not a nonempty regular file within its byte limit")
        raw = sidecar.read(_SIDECAR_BYTES + 1)
        if len(raw) != json_stat.st_size:
            raise ValueError("Sidecar changed or exceeds its byte limit")
        record = _metadata(raw, max_samples)
        data_hash, json_hash = _digest(data, max_file_bytes), hashlib.sha256(raw).hexdigest()
        if (record["artifact"]["bytes"] != data_stat.st_size
                or record["artifact"]["sha256"] != data_hash):
            raise ValueError(f"NPZ does not match sidecar bytes/SHA256: {npz_path}")
        _unchanged(data, npz_path, data_stat)
        _unchanged(sidecar, json_path, json_stat)
        with zipfile.ZipFile(data) as archive:
            index = _array_index(archive, record, max_array_bytes)
            identity = {
                "npz": {"path": str(npz_path), "bytes": data_stat.st_size, "sha256": data_hash},
                "json": {"path": str(json_path), "bytes": json_stat.st_size, "sha256": json_hash},
                "observation": {key: record["observation"][key] for key in
                                ("captured_at_utc", "iteration_expression", "flow_time_s")},
            }
            yield record, archive, index, identity
        for stream, selected, before, maximum, digest in (
                (data, npz_path, data_stat, max_file_bytes, data_hash),
                (sidecar, json_path, json_stat, _SIDECAR_BYTES, json_hash)):
            if _digest(stream, maximum) != digest:
                raise ValueError(f"Input bytes changed while comparing: {selected}")
            _unchanged(stream, selected, before)


def _kind(value: float) -> str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "positive_infinity" if value > 0 else "negative_infinity"
    return "finite"


def _add(groups: dict, key: bytes, value: float, name: str) -> None:
    if key in groups:
        previous = groups[key][1]
        if not (value == previous or (math.isnan(value) and math.isnan(previous))):
            raise ValueError(f"Ambiguous coincident samples have differing values: {name}")
        groups[key][0] += 1
    else:
        groups[key] = [1, value]


def _surface(dataset: tuple, name: str) -> tuple:
    record, archive, index, _ = dataset
    entry = record["surfaces"][name]
    prefix = entry["prefix"]
    xyz = np.array(_array(archive, index, prefix + "_vertices"), dtype="<f8", copy=True)
    centres = _array(archive, index, prefix + "_centroids")
    values = _array(archive, index, prefix + "_values")
    connectivity = _array(archive, index, prefix + "_connectivity")
    if not np.isfinite(xyz).all() or not np.isfinite(centres).all():
        raise ValueError(f"Nonfinite geometry: {name}")
    if int((~np.isfinite(values)).sum()) != entry["nonfinite"]:
        raise ValueError(f"Sidecar nonfinite count disagrees with scalar array: {name}")
    xyz[xyz == 0] = 0  # Normalize signed zero, without coordinate rounding.
    nodes, faces, groups = {}, {}, {}
    for i, point in enumerate(xyz):
        key = point.tobytes()
        nodes[key] = nodes.get(key, 0) + 1
        if record["sampling"] == "node":
            _add(groups, key, float(values[i]), name)
    offset, face = 0, 0
    while offset < len(connectivity):
        count = int(connectivity[offset])
        if (count < 3 or count > len(xyz) or offset + count >= len(connectivity)
                or face >= entry["faces"]):
            raise ValueError(f"Require complete 3D polygon face connectivity: {name}")
        ids = connectivity[offset + 1:offset + count + 1]
        if np.any(ids < 0) or np.any(ids >= len(xyz)):
            raise ValueError(f"Face references an unavailable vertex: {name}")
        points = xyz[ids]
        order = np.lexsort((points[:, 2], points[:, 1], points[:, 0]))
        ordered = points[order]
        if np.any(np.all(ordered[1:] == ordered[:-1], axis=1)):
            raise ValueError(f"Repeated coordinates within one polygon are unsupported: {name}")
        key = ordered.tobytes()
        faces[key] = faces.get(key, 0) + 1
        if record["sampling"] == "face":
            _add(groups, key, float(values[face]), name)
        offset += count + 1
        face += 1
    if face != entry["faces"]:
        raise ValueError(f"Decoded face count differs from metadata: {name}")
    return nodes, faces, groups


def _statistics(a: dict, b: dict, tolerance: float, name: str) -> dict:
    if a.keys() != b.keys() or any(a[key][0] != b[key][0] for key in a):
        raise ValueError(f"Exact sample geometry/multiplicity mismatch: {name}")
    invalid_a = dict.fromkeys(("nan", "positive_infinity", "negative_infinity"), 0)
    invalid_b = invalid_a.copy()
    finite, changed, invalid_changed, deltas = 0, 0, 0, []
    for key, (count, value_a) in a.items():
        value_b = b[key][1]
        kind_a, kind_b = _kind(value_a), _kind(value_b)
        if kind_a != "finite":
            invalid_a[kind_a] += count
        if kind_b != "finite":
            invalid_b[kind_b] += count
        if kind_a != kind_b:
            invalid_changed += count
        if kind_a == kind_b == "finite":
            delta = value_b - value_a
            if not math.isfinite(delta):
                raise ValueError(f"Finite scalar subtraction overflows float64: {name}")
            finite += count
            changed += count if abs(delta) > tolerance else 0
            deltas.append((delta, count))
    maximum = mean_absolute = mean_signed = None
    if finite:
        maximum = max(abs(delta) for delta, _ in deltas)
        # Weight before summation to avoid overflow of an otherwise finite mean.
        try:
            mean_absolute = math.fsum(abs(delta) * (count / finite) for delta, count in deltas)
            mean_signed = math.fsum(delta * (count / finite) for delta, count in deltas)
        except OverflowError as exc:
            raise ValueError(f"Delta aggregation overflows float64: {name}") from exc
        if not all(math.isfinite(value) for value in (maximum, mean_absolute, mean_signed)):
            raise ValueError(f"Delta aggregation is nonfinite: {name}")
    samples = sum(count for count, _ in a.values())
    nonfinite_a, nonfinite_b = sum(invalid_a.values()), sum(invalid_b.values())
    return {
        "samples": samples, "matched_groups": len(a),
        "coincident_groups": sum(count > 1 for count, _ in a.values()),
        "finite_a": samples - nonfinite_a, "finite_b": samples - nonfinite_b,
        "finite_pairs": finite, "nonfinite_pairs": samples - finite,
        "nonfinite_a": nonfinite_a, "nonfinite_b": nonfinite_b,
        "nonfinite_kinds_a": invalid_a, "nonfinite_kinds_b": invalid_b,
        "changed_finite_pairs": changed, "nonfinite_status_changed": invalid_changed,
        "max_absolute_delta": maximum, "mean_absolute_delta": mean_absolute,
        "signed_mean_delta": mean_signed,
        "status": "complete" if finite == samples else "incomplete",
    }


def compare_surface_datasets(
    path_a: str,
    path_b: str,
    *,
    absolute_tolerance: float = 0.0,
    max_file_bytes: int = 64 * 1024 * 1024,
    max_array_bytes: int = 256 * 1024 * 1024,
    max_samples: int = 100000,
) -> dict:
    """Compare scalar values after exact geometry matching, with no solver.

    Select two absolute local .npz files. Each .json is inferred from that
    selected filename in the same directory; JSON paths are never followed.
    Verify NPZ bytes/SHA256, require identical explicit surface names, field,
    complete field_metadata (including mapped SI units/domain), sampling and
    boundary-value policy, then audit decoded boundary geometry in both modes.

    Faces match by sorted exact 3D vertex-coordinate sets, with multiplicity.
    Nodes match by exact coordinate groups, with multiplicity. Every duplicate
    group within either input must have identical values (all NaNs count as
    one invalid class); differing duplicate values refuse comparison even when
    their multisets happen to agree. No pairing by row number is used.

    absolute_tolerance must be finite/nonnegative. Only abs(B-A) > tolerance
    counts as a changed finite pair; it never changes geometry or statistics.
    Delta statistics use finite pairs only, give every sample equal weight,
    and are None when no finite pair exists. Nonfinite coverage remains explicit.

    Limits apply separately to each input. max_file_bytes (hard cap 512 MiB)
    bounds compressed NPZ size; JSON has a fixed 1 MiB cap. max_array_bytes
    (hard cap 1 GiB) bounds the SUM of decoded NPY members, including headers.
    There are at most 128 arrays with 10000-byte headers. max_samples (hard cap
    1000000) bounds each of total samples, total vertices and total faces.
    Decoded extents/dtypes/shapes are checked before any array payload is read.

    Raises ValueError for unsupported, ambiguous, incompatible, corrupt,
    changing or excessive inputs. Filesystem errors may propagate. Successful
    comparison proves only this recorded boundary-sampling contract; see the
    returned limitations. This function writes no output and changes no files.
    """
    _limit("max_file_bytes", max_file_bytes, 512 * 1024 * 1024)
    _limit("max_array_bytes", max_array_bytes, 1024 * 1024 * 1024)
    _limit("max_samples", max_samples, 1000000)
    if type(absolute_tolerance) not in (int, float):
        raise ValueError("absolute_tolerance must be a finite nonnegative number")
    try:
        tolerance = float(absolute_tolerance)
    except OverflowError as exc:
        raise ValueError("absolute_tolerance must be finite") from exc
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("absolute_tolerance must be finite and nonnegative")
    try:
        with (_dataset(path_a, max_file_bytes, max_array_bytes, max_samples) as a,
              _dataset(path_b, max_file_bytes, max_array_bytes, max_samples) as b):
            meta_a, meta_b = a[0], b[0]
            for key in ("field", "coordinates", "field_metadata", "sampling", "sampling_basis",
                        "boundary_values", "connectivity"):
                if meta_a[key] != meta_b[key]:
                    raise ValueError(f"Dataset metadata mismatch: {key}")
            if meta_a["surfaces"].keys() != meta_b["surfaces"].keys():
                raise ValueError("Require the same explicit surface names")
            results = {}
            for name in sorted(meta_a["surfaces"]):
                nodes_a, faces_a, groups_a = _surface(a, name)
                nodes_b, faces_b, groups_b = _surface(b, name)
                if nodes_a != nodes_b or faces_a != faces_b:
                    raise ValueError(f"Exact boundary geometry/topology mismatch: {name}")
                results[name] = _statistics(groups_a, groups_b, tolerance, name)
            metadata = meta_a["field_metadata"]
            result = {
                "schema": "fluent.surface-dataset-comparison.v1",
                "inputs": {"a": a[3], "b": b[3]},
                "field": meta_a["field"], "sampling": meta_a["sampling"],
                "field_metadata": {key: metadata[key] for key in
                                   ("domain", "quantity_name", "unit_si", "unit_basis")},
                "boundary_values": True, "sampling_basis": meta_a["sampling_basis"],
                "coverage_complete": all(item["status"] == "complete" for item in results.values()),
                "surfaces": results,
                "matching_contract": {
                    "surfaces": "exact names; prefixes and row IDs are not identities",
                    "coordinates": "exact numeric 3D metres; float64 widening; signed zero normalized",
                    "geometry_tolerance_m": 0,
                    "topology": "equal multisets of decoded sorted face-coordinate sets and vertex coordinates",
                    "sample_key": "sorted face-coordinate set" if meta_a["sampling"] == "face" else "vertex coordinate",
                    "duplicates": "equal multiplicities; one exact value or nonfinite class per input group",
                    "field_metadata": "entire field_metadata objects must match; unmapped units refused",
                    "delta": "B minus A; equal weight per exported sample; finite pairs only",
                    "changed": "abs(B-A) > absolute_tolerance, for finite pairs only",
                    "absolute_tolerance": tolerance, "tolerance_unit": metadata["unit_si"],
                    "nonfinite_status_changed": "count of pairs whose finite/NaN/+inf/-inf classes differ",
                    "bounds_per_input": {"file_bytes": max_file_bytes, "sidecar_bytes": _SIDECAR_BYTES,
                                         "decoded_array_bytes": max_array_bytes, "arrays": 128,
                                         "samples_faces_vertices_each": max_samples},
                },
                "limitations": list(_LIMITATIONS),
            }
    except (zipfile.BadZipFile, EOFError, UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"Invalid NPZ/JSON dataset: {exc}") from exc
    return result
