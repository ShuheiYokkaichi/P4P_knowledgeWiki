"""Join explicit history captures without changing their coordinates or values.

Native input is a nonempty list of dictionaries with these keys::

    {
        "source_id": "continuation/report.out",
        "sha256": "<64 hexadecimal characters, computed from source bytes>",
        "axis": {"name": "iteration", "unit": "1"},
        "units": {"continuity": "1", "energy": "1"},
        "x": [100, 101],
        "series": {"continuity": [0.01, 0.009]},
        "stage": "conditioning",  # optional string; omission means None
    }

Axis metadata must contain name/unit strings; other string metadata is allowed.
Every segment must declare identical axis metadata and the same full units
mapping. That mapping defines the output columns, including equations absent
from all captures. A series may be omitted, or contain None: both become null
in the aligned output. Null means unavailable, not a measured zero. To mark an
inactive equation, the caller must omit it or pass None, not a numeric sentinel.
Coordinates must be nondecreasing within each segment; equal coordinates are
allowed so repeated native rows can be checked. Numbers are native Python int
or finite float, excluding bool. Arrays are lists or tuples; use .tolist() for
NumPy data. Coordinates cannot be null. Empty segments are recorded and allowed.

Stages are independent coordinate domains, ordered by their first appearance.
Within each stage, output rows are sorted by x. No overlap or gap is inferred
between different stages. Use distinct stage identities when counters restart;
the function cannot infer a restart or prove that two sources share a lineage.
It never offsets, rebases, interpolates, fills a gap, or averages values.

At equal stage/x, only exactly equal *aligned* value vectors are collapsed
(Python numeric equality, no tolerance; absent and explicit null are equal).
All distinct variants remain as repeated x rows with explicit errors. Each
retained row lists every contributing segment and zero-based source row. Thus
deduplication preserves the provenance of all repeated captures. Conflicts are
returned, not raised; callers must inspect status/errors before using the data.
Malformed input raises ValueError before any result is returned.

No files are opened. SHA-256 digests are mandatory caller assertions, validated
for syntax but not checked against bytes or parsed arrays. Hash the exact source
bytes before parsing; source_id is an opaque label, not a path to read. Selecting
and parsing exact segments, unit/axis truth, and scientific acceptance remain
the caller's responsibility.
"""
from __future__ import annotations

from fractions import Fraction
import math
import re
from typing import Any


def _number(value: Any, label: str) -> None:
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        raise ValueError(f"{label} must be a finite int or float, not bool")


def _strings(value: Any, label: str) -> None:
    if not isinstance(value, dict) or not value or not all(
        isinstance(k, str) and k.strip() and isinstance(v, str) and v.strip()
        for k, v in value.items()
    ):
        raise ValueError(f"{label} must be a nonempty mapping of nonempty strings")


def join_history_segments(
    segments: list[dict[str, Any]],
    *,
    expected_step: int | float | None = None,
    step_tolerance: int | float = 0,
    max_rows: int = 2000,
    max_cells: int = 20000,
) -> dict[str, Any]:
    """Join bounded captured histories; retain conflicts and unavailable values.

    Each segment requires source_id, sha256, axis{name,unit}, units, x and
    aligned series arrays. Optional stage separates reset counters; optional
    source_rows maps submitted samples to original source row indices. Hashes
    are caller assertions. Establish common lineage, definitions, scaling,
    units and equation activity first. Null means unavailable, never zero.
    Equal coordinates collapse only exactly equal complete aligned vectors;
    distinct variants remain with explicit errors. No interpolation/rebasing.

    Gap detection is disabled unless expected_step is a positive number. With
    it enabled, a gap is an adjacent unique-coordinate span strictly greater
    than expected_step + step_tolerance in one stage. step_tolerance is an
    explicit nonnegative absolute allowance in axis units, used ONLY for gap
    checks. The default is exact; supply an allowance for rounded time axes.
    Arithmetic uses exact ratios of the supplied numbers to avoid overflow or
    rounding during the check. No missing coordinates are generated or counted,
    and no regular grid or expected start/end is inferred.

    coverage describes only the observed range of each stage. Per-column
    nonnull/null counts refer to retained output rows, including conflicting
    variants. duplicate_overlaps identifies collapsed rows; provenance.rows
    contains all their source references. errors contains the output indices
    and differing columns for each conflicting stage/x. status is 'conflict'
    when errors exist, otherwise 'joined'; neither implies complete coverage
    or live Fluent acceptance. Empty stages have null bounds.
    """
    if not isinstance(segments, list) or not segments:
        raise ValueError("segments must be a nonempty list of segment dictionaries")
    if len(segments) > 32:
        raise ValueError("At most 32 segments may be joined")
    for name, value, maximum in (("max_rows", max_rows, 10000), ("max_cells", max_cells, 100000)):
        if type(value) is not int or not 1 <= value <= maximum:
            raise ValueError(f"{name} must be an integer between 1 and {maximum}")
    total_rows = 0
    _number(step_tolerance, "step_tolerance")
    if step_tolerance < 0 or (expected_step is None and step_tolerance != 0):
        raise ValueError("step_tolerance must be nonnegative and needs expected_step")
    gap_limit = None
    if expected_step is not None:
        _number(expected_step, "expected_step")
        if expected_step <= 0:
            raise ValueError("expected_step must be positive")
        gap_limit = Fraction(expected_step) + Fraction(step_tolerance)

    required = {"source_id", "sha256", "axis", "units", "x", "series"}
    axis, units = None, None
    sources: list[dict[str, Any]] = []
    # stage -> coordinate -> aligned value vector -> source row references
    groups: dict[Any, dict[Any, dict[tuple, list[dict[str, int]]]]] = {}
    for index, segment in enumerate(segments):
        label = f"segment {index}"
        if not isinstance(segment, dict) or not required.issubset(segment) or (
            set(segment) - required - {"stage", "source_rows"}
        ):
            raise ValueError(f"{label}: required keys are {sorted(required)}; stage/source_rows are optional")
        source_id, digest = segment["source_id"], segment["sha256"]
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"{label}: source_id must be a nonempty string")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-fA-F]{64}", digest) is None:
            raise ValueError(f"{label}: sha256 must contain exactly 64 hexadecimal characters")
        stage = segment.get("stage")
        if stage is not None and (not isinstance(stage, str) or not stage.strip()):
            raise ValueError(f"{label}: stage must be a nonempty string or None")
        _strings(segment["axis"], f"{label} axis")
        _strings(segment["units"], f"{label} units")
        if not {"name", "unit"}.issubset(segment["axis"]):
            raise ValueError(f"{label}: axis must declare name and unit")
        if axis is None:
            axis, units = dict(segment["axis"]), dict(segment["units"])
        elif segment["axis"] != axis or segment["units"] != units:
            raise ValueError(f"{label}: axis metadata and the full units mapping must match exactly")
        x, series = segment["x"], segment["series"]
        if not isinstance(x, (list, tuple)) or not isinstance(series, dict):
            raise ValueError(f"{label}: x must be an array and series must be a mapping")
        total_rows += len(x)
        if total_rows > max_rows or total_rows * len(units) > max_cells:
            raise ValueError("Join exceeds row/cell budget; select a smaller explicit window")
        source_rows = segment.get("source_rows")
        if source_rows is not None and (not isinstance(source_rows, (list, tuple)) or len(source_rows) != len(x)
                or any(type(v) is not int or v < 0 for v in source_rows)):
            raise ValueError(f"{label}: source_rows must contain one nonnegative integer per sample")
        if set(series) - set(units):
            raise ValueError(f"{label}: every series must have a declared unit")
        for column, values in series.items():
            if not isinstance(values, (list, tuple)) or len(values) != len(x):
                raise ValueError(f"{label} {column}: values must be an array aligned with x")
            for row, value in enumerate(values):
                if value is not None:
                    _number(value, f"{label} {column}[{row}]")
        for row, coordinate in enumerate(x):
            _number(coordinate, f"{label} x[{row}]")
            if row and coordinate < x[row - 1]:
                raise ValueError(f"{label}: x must be nondecreasing; split counter resets into stages")
        sources.append({
            "segment": index, "source_id": source_id, "sha256": digest.lower(),
            "stage": stage, "rows": len(x), "columns": list(series),
            "first_x": x[0] if x else None, "last_x": x[-1] if x else None,
        })
        coordinates = groups.setdefault(stage, {})
        for row, coordinate in enumerate(x):
            vector = tuple(series[name][row] if name in series else None for name in units)
            variants = coordinates.setdefault(coordinate, {})
            variants.setdefault(vector, []).append({"segment": index, "submitted_row": row,
                                                    "source_row": source_rows[row] if source_rows is not None else None})

    result: dict[str, Any] = {
        "status": "joined", "axis": axis, "units": units,
        "x": [], "stage": [], "series": {name: [] for name in units},
        "provenance": {"hash_verification": "caller_supplied_not_verified",
                       "row_index_basis": "submitted_row indexes the supplied segment; source_row is caller-supplied or null",
                       "sources": sources, "rows": []},
        "coverage": [], "gaps": [], "duplicate_overlaps": [], "errors": [],
    }
    for stage, coordinates in groups.items():
        ordered = sorted(coordinates)
        start_row = len(result["x"])
        conflicts = removed = 0
        counts = {name: 0 for name in units}
        for coordinate in ordered:
            variants = coordinates[coordinate]
            output_rows = []
            for vector, references in variants.items():
                output_row = len(result["x"])
                output_rows.append(output_row)
                result["x"].append(coordinate)
                result["stage"].append(stage)
                result["provenance"]["rows"].append(references)
                for name, value in zip(units, vector):
                    result["series"][name].append(value)
                    counts[name] += value is not None
                if len(references) > 1:
                    removed += len(references) - 1
                    result["duplicate_overlaps"].append({
                        "stage": stage, "x": coordinate, "output_row": output_row,
                        "removed_rows": len(references) - 1,
                    })
            if len(variants) > 1:
                conflicts += 1
                vectors = list(variants)
                result["errors"].append({
                    "code": "conflicting_overlap", "stage": stage, "x": coordinate,
                    "output_rows": output_rows,
                    "columns": [name for column, name in enumerate(units)
                                if len({v[column] for v in vectors}) > 1],
                })
        stage_gaps = []
        if gap_limit is not None:
            stage_gaps = [
                {"stage": stage, "left": left, "right": right}
                for left, right in zip(ordered, ordered[1:])
                if Fraction(right) - Fraction(left) > gap_limit
            ]
            result["gaps"].extend(stage_gaps)
        rows = len(result["x"]) - start_row
        result["coverage"].append({
            "stage": stage, "observed_only": True,
            "first_x": ordered[0] if ordered else None,
            "last_x": ordered[-1] if ordered else None,
            "input_rows": rows + removed, "output_rows": rows,
            "unique_coordinates": len(ordered), "duplicate_rows_removed": removed,
            "conflicting_coordinates": conflicts,
            "gap_detection_enabled": gap_limit is not None,
            "expected_step": expected_step, "step_tolerance": step_tolerance,
            "gap_count": len(stage_gaps) if gap_limit is not None else None,
            "series": {name: {"nonnull_rows": count, "null_rows": rows - count}
                       for name, count in counts.items()},
        })
    if result["errors"]:
        result["status"] = "conflict"
    return result
