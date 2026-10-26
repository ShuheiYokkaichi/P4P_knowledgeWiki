"""Independent, unregistered history helpers for an official MCP host.

Candidate A reads an existing PyFluent monitor buffer once; it never manages
streams or solves. Candidate B reads a native Report File on THIS host, not a
remote Fluent filesystem. Neither reader changes Fluent or writes files.
Only ``export_monitor_history_png`` writes, to an explicit new local PNG.

Invalid limits/paths raise ValueError. Runtime/data failures have JSON status
``error``; absent live samples have status ``unavailable``. File status
``partial`` means reported issues require review, even if rows are returned.
Counts describe the inspected buffer/window, never an assumed full solve.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import math
from numbers import Real
import os
from pathlib import Path
import re
import socket
import stat
from typing import Any


__all__ = [
    "read_live_monitor_history", "export_monitor_history_png", "read_report_file_history"
]
_MAX_POINTS = 10_000
_MAX_SERIES = 128
_MAX_ISSUES = 20
_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')
_NUMBER = re.compile(rb"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eEdD][+-]?[0-9]+)?\Z")
_NUMBER_PREFIX = re.compile(rb"[+-]?(?:(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eEdD][+-]?)?|\.)?\Z")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _limit(name: str, value: int, maximum: int, minimum: int = 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _local_path(path: str | os.PathLike[str]) -> Path:
    result = Path(path)
    if not result.is_absolute() or str(result).startswith(("\\\\", "//")):
        raise ValueError("Supply an absolute local-host path, not a URI or UNC path")
    return result


def _error(result: dict[str, Any], code: str, detail: Any) -> dict[str, Any]:
    return {**result, "status": "error", "error": {"code": code, "detail": str(detail)}}


def _finite_vector(values: Any, name: str, expected: int) -> list[float]:
    if isinstance(values, (str, bytes, Mapping)) or len(values) != expected:
        raise ValueError(f"{name}: expected {expected} aligned values")
    output = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError(f"{name}[{index}]: expected a real number")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"{name}[{index}]: nonfinite value")
        output.append(number)
    return output


def read_live_monitor_history(
    solver: Any,
    monitor_set: str,
    *,
    max_points: int = 1_000,
    max_scan_points: int = 10_000,
    max_series: int = 32,
    output_prefix: str | None = None,
    logarithmic: bool = False,
) -> dict[str, Any]:
    """Read one bounded tail snapshot without starting/stopping shared streams.

    Optional output_prefix exports this exact snapshot as JSON, CSV and PNG
    with hashes. The MCP bridge also returns the PNG as image content. Use
    logarithmic=True for positive residual curves; zero/negative values cause
    an explicit export error rather than being clipped. Tail statistics are
    descriptive only; they do not establish convergence.

    Requires public ``get_monitor_set_data(..., start_index=...)`` support.
    One extra point detects truncation at the scan cap. Above that cap the
    exact total is unavailable: ``total_points`` is null and its lower bound
    is explicit. Totals refer only to this client's current monitor buffer.
    All fetched values, including those outside the returned tail, must be
    aligned and finite. An oversized series set is rejected, not filtered.
    PyFluent allocates arrays for every series before this helper can cap them.
    """
    _limit("max_points", max_points, _MAX_POINTS)
    _limit("max_scan_points", max_scan_points, 100_000, max_points)
    _limit("max_series", max_series, _MAX_SERIES)
    if not isinstance(monitor_set, str) or not monitor_set.strip():
        raise ValueError("monitor_set must be a nonempty string")
    result: dict[str, Any] = {
        "source": "live_monitor", "monitor_set": monitor_set,
        "captured_at_utc": _utc(), "x_label": "unknown",
        "x_label_source": "unknown", "total_scope": "client_monitor_buffer",
        "max_points": max_points, "max_scan_points": max_scan_points,
        "total_points": None, "total_points_lower_bound": 0,
        "returned_points": 0, "truncated": False, "x": [], "series": {},
    }
    try:
        manager = solver.monitors
        if monitor_set not in manager.get_monitor_set_names():
            return {**result, "status": "unavailable", "reason": "monitor_set_not_exposed"}
        x_raw, series_raw = manager.get_monitor_set_data(
            monitor_set_name=monitor_set, start_index=-(max_scan_points + 1)
        )
    except Exception as exc:
        return _error(result, "monitor_read_failed", f"{type(exc).__name__}: {exc}")
    result["captured_at_utc"] = _utc()
    try:
        count = len(x_raw)
        if count > max_scan_points + 1:
            raise ValueError("monitor API did not respect the requested scan bound")
        if not isinstance(series_raw, Mapping) or len(series_raw) > max_series:
            raise ValueError(f"expected a mapping with at most {max_series} series")
        if count and not series_raw:
            raise ValueError("coordinates were returned without any series")
        x = _finite_vector(x_raw, "x", count)
        series = {}
        for name, values in series_raw.items():
            if not isinstance(name, str):
                raise ValueError("monitor series names must be strings")
            series[name] = _finite_vector(values, name, count)
    except (TypeError, ValueError, OverflowError) as exc:
        return _error(result, "invalid_monitor_data", exc)
    result.update(
        total_points=count if count <= max_scan_points else None,
        total_points_lower_bound=count, scanned_points=count,
        returned_points=min(count, max_points), truncated=count > max_points,
        scan_truncated=count > max_scan_points,
    )
    if not count:
        return {**result, "status": "unavailable", "reason": "no_samples"}
    metadata = getattr(manager, "get_monitor_set_prop", None)
    if callable(metadata):
        try:
            label = metadata(monitor_set_name=monitor_set, property="xlabel")
            if isinstance(label, str) and label.strip():
                result.update(x_label=label, x_label_source="monitor_metadata.xlabel")
        except Exception as exc:
            result["metadata_warning"] = f"{type(exc).__name__}: {exc}"
    result = {
        **result, "status": "ok", "x": x[-max_points:],
        "series": {name: values[-max_points:] for name, values in series.items()},
    }
    result["tail_statistics"] = {}
    for name, values in result["series"].items():
        change = values[-1] - values[0]
        dx = result["x"][-1] - result["x"][0]
        result["tail_statistics"][name] = {"first": values[0], "last": values[-1],
            "minimum": min(values), "maximum": max(values),
            "endpoint_change": change if math.isfinite(change) else None,
            "endpoint_slope_per_x": change / dx if dx > 0 and math.isfinite(change / dx) else None}
    if output_prefix is not None:
        result["artifacts"] = _export_snapshot(result, output_prefix, logarithmic)
    return result


def export_monitor_history_png(
    history: Mapping[str, Any], path: str | os.PathLike[str], *, dpi: int = 150,
    logarithmic: bool = False,
) -> dict[str, Any]:
    """Plot candidate A's returned snapshot; embed provenance in PNG metadata.

    Uses the requested y scale and supplied axis label, including ``unknown``.
    Does not fetch new data, change Matplotlib's global backend, create parent
    directories, or overwrite a file. Matplotlib is an optional dependency.
    """
    _limit("dpi", dpi, 300, 50)
    target = _local_path(path)
    if target.suffix.lower() != ".png":
        raise ValueError("PNG output path must end in .png")
    result = {"source": "live_monitor_png", "path": str(target)}
    try:
        if history.get("status") != "ok" or history.get("source") != "live_monitor":
            raise ValueError("export requires an ok live_monitor snapshot")
        count = _limit("returned_points", history["returned_points"], _MAX_POINTS)
        x = _finite_vector(history["x"], "x", count)
        raw_series = history["series"]
        if not isinstance(raw_series, Mapping) or not 1 <= len(raw_series) <= _MAX_SERIES:
            raise ValueError("export requires 1 to 128 series")
        series = {name: _finite_vector(values, str(name), count)
                  for name, values in raw_series.items()}
        if logarithmic and any(v <= 0 for values in series.values() for v in values):
            raise ValueError("Logarithmic plots require positive values; no samples were clipped")
        encoded = json.dumps(dict(history), sort_keys=True, allow_nan=False).encode("utf-8")
        provenance = {
            key: history.get(key) for key in (
                "source", "monitor_set", "captured_at_utc", "x_label", "x_label_source",
                "total_scope", "total_points", "total_points_lower_bound",
                "returned_points", "truncated", "scan_truncated",
            )
        }
        provenance.update(snapshot_sha256=hashlib.sha256(encoded).hexdigest(),
                          exported_at_utc=_utc(), axis_scale="log" if logarithmic else "linear")
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure

        figure = Figure(figsize=(8, 4), layout="constrained")
        FigureCanvasAgg(figure)
        axis = figure.subplots()
        for name, values in series.items():
            axis.plot(x, values, label=name, linewidth=1)
        if logarithmic:
            axis.set_yscale("log")
        axis.set(xlabel=history.get("x_label", "unknown"), ylabel="Monitor value",
                 title=history["monitor_set"])
        axis.grid(True, alpha=0.25)
        axis.legend()
        with BytesIO() as image:
            figure.savefig(image, format="png", dpi=dpi, metadata={
                "Description": json.dumps(provenance, sort_keys=True, allow_nan=False)
            })
            with target.open("xb") as stream:
                stream.write(image.getvalue())
        return {**result, "status": "ok", "provenance": provenance}
    except Exception as exc:
        return _error(result, "png_export_failed", f"{type(exc).__name__}: {exc}")


def _export_snapshot(history, prefix, logarithmic):
    import csv
    base = _local_path(prefix)
    paths = {suffix: Path(str(base) + "." + suffix) for suffix in ("json", "csv", "png")}
    if any(p.exists() for p in paths.values()):
        raise FileExistsError("Snapshot outputs already exist")
    created = []
    try:
        for suffix in ("json", "csv"):
            with paths[suffix].open("x", encoding="utf-8", newline="") as stream:
                created.append(paths[suffix])
                if suffix == "json":
                    json.dump(history, stream, indent=2, allow_nan=False)
                else:
                    writer = csv.writer(stream)
                    writer.writerow([history["x_label"], *history["series"]])
                    writer.writerows(zip(history["x"], *history["series"].values()))
        image = export_monitor_history_png(history, paths["png"], logarithmic=logarithmic)
        if image["status"] != "ok":
            raise RuntimeError(str(image["error"]))
        created.append(paths["png"])
        return {k: {"path": str(p), "bytes": p.stat().st_size,
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for k, p in paths.items()}
    except Exception:
        for p in reversed(created):
            p.unlink(missing_ok=True)
        raise


def _quoted_fields(text: str) -> list[str]:
    fields, end = [], 0
    for match in _QUOTED.finditer(text):
        gap = text[end:match.start()]
        if gap.strip() or (fields and not gap):
            raise ValueError("expected whitespace-separated quoted strings")
        fields.append(re.sub(r'\\(["\\])', r'\1', match.group(1)))
        end = match.end()
    if not fields or text[end:].strip():
        raise ValueError("expected quoted strings")
    return fields


def _report_header(raw: bytes, complete: bool) -> tuple[str, list[str], int]:
    lines, offset = [], 0
    for line in raw.splitlines(keepends=True):
        offset += len(line)
        if not line.strip():
            continue
        if not complete and not line.endswith(b"\n"):
            raise ValueError("title/header exceeds the bounded header window")
        lines.append(line.decode("utf-8-sig").strip())
        # Fluent 25.2 writes a title, an unparenthesized display-label row,
        # then the parenthesized machine column row. Other writers omit the
        # display-label row. Stop at the explicit machine header in either.
        if len(lines) >= 2 and lines[-1].startswith("("):
            break
        if len(lines) > 3:
            break
    if len(lines) not in (2, 3):
        raise ValueError("expected a title string line and a quoted column header line")
    titles = _quoted_fields(lines[0])
    if len(titles) != 1 or not lines[-1].startswith("(") or not lines[-1].endswith(")"):
        raise ValueError("expected one title string followed by a parenthesized header")
    if len(lines) == 3:
        _quoted_fields(lines[1])
    columns = _quoted_fields(lines[-1][1:-1])
    if (not 2 <= len(columns) <= _MAX_SERIES + 1 or len(set(columns)) != len(columns)
            or any(not label.strip() for label in columns)):
        raise ValueError("expected 2 to 129 distinct nonempty column labels")
    return titles[0], columns, offset


def read_report_file_history(
    path: str | os.PathLike[str],
    *,
    max_bytes: int = 4 * 1024 * 1024,
    max_points: int = 1_000,
    coordinate_column: str | None = None,
    max_cells: int = 100_000,
) -> dict[str, Any]:
    """Read a UTF-8/ASCII native Fluent Report File on the local MCP host.

    Accepts a title string, then e.g. ("Iteration" "outlet-temp" "flow-time"),
    then whitespace numeric rows (also Fortran D exponents). All columns are
    retained as floats; the default coordinate is the first column. No integer
    iteration assumption, sorting, filling, or interpolation is applied.

    Reads at most max_bytes: the whole snapshot when it fits, otherwise a header
    prefix (at most 64 KiB) and an aligned tail. Older rows/errors are NOT audited
    in that case and the full point total is unknown. Errors in the inspected
    window remain explicit even when outside the returned tail. At most 20
    issue details are returned, with exact issue and rejection counts.

    Every repeated/decreased coordinate starts a segment; this flags a possible
    restart, not its cause. Segment indexes are zero-based and end-exclusive
    within returned rows. A valid final row without newline is returned with
    partial status because a live writer could still extend its last token.
    No remote reads, path discovery, MCP registration, or access sandbox here:
    the official MCP caller must enforce its own filesystem access policy.
    """
    _limit("max_bytes", max_bytes, 64 * 1024 * 1024, 256)
    _limit("max_points", max_points, _MAX_POINTS)
    _limit("max_cells", max_cells, 1_000_000)
    if coordinate_column is not None and not isinstance(coordinate_column, str):
        raise ValueError("coordinate_column must be a header label or None")
    target = _local_path(path)
    result: dict[str, Any] = {
        "source": "native_report_file", "path": str(target),
        "host": socket.gethostname(), "captured_at_utc": _utc(),
        "max_bytes": max_bytes, "max_points": max_points,
        "total_points": None, "returned_points": 0, "rows": [],
    }
    try:
        target = _local_path(target.resolve(strict=True))
        result["path"] = str(target)
        if not stat.S_ISREG(target.stat().st_mode):
            return _error(result, "not_regular_file", "Only regular files are supported")
        with target.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode):
                return _error(result, "not_regular_file", "Only regular files are supported")
            size = before.st_size
            complete = size <= max_bytes
            prefix = stream.read(size if complete else min(65_536, max_bytes // 2))
            title, columns, data_start = _report_header(
                prefix[:65_536], complete and len(prefix) <= 65_536
            )
            if coordinate_column is not None and coordinate_column not in columns:
                raise ValueError(f"coordinate column {coordinate_column!r} is not in the header")
            coordinate_index = columns.index(coordinate_column) if coordinate_column is not None else 0
            effective_points = min(max_points, max_cells // len(columns))
            if not effective_points:
                raise ValueError("max_cells must allow at least one complete row")
            if complete:
                body, start, bytes_read, discarded = prefix[data_start:], data_start, len(prefix), 0
            else:
                # Include a preceding byte to distinguish a row boundary from
                # a partial leading row, while keeping the combined byte cap.
                tail_budget = max_bytes - len(prefix)
                start = max(data_start, size - tail_budget + 1)
                stream.seek(start - 1 if start > data_start else start)
                body = stream.read(size - stream.tell())
                bytes_read = len(prefix) + len(body)
                discarded = 0
                if start > data_start:
                    if body.startswith(b"\n"):
                        body = body[1:]
                    else:
                        boundary = body.find(b"\n")
                        if boundary < 0:
                            return _error(result, "row_exceeds_byte_window", "No complete tail row fits")
                        discarded = boundary  # Excludes the preceding context byte.
                        body = body[boundary + 1:]
                        start += discarded
            after = os.fstat(stream.fileno())
    except (OSError, ValueError) as exc:
        return _error(result, "file_read_failed", f"{type(exc).__name__}: {exc}")

    result.update(
        title=title, columns=columns, coordinate_column=columns[coordinate_index],
        file_size_bytes=size, bytes_read=bytes_read, byte_truncated=not complete,
        data_window_start_byte=start, data_window_end_byte=start + len(body),
        leading_fragment_bytes_discarded=discarded,
        data_window_sha256=hashlib.sha256(body).hexdigest(),
        header_sha256=hashlib.sha256(prefix[:data_start]).hexdigest(),
        mtime_ns_before=before.st_mtime_ns, mtime_ns_after=after.st_mtime_ns,
        count_scope="whole_file" if complete else "bounded_tail_window",
        point_count_basis="finite_parsed_rows",
    )
    issues: list[dict[str, Any]] = []
    issue_count = rejected = valid = data_rows = segment = events_count = 0
    records: deque[Any] = deque(maxlen=effective_points)
    events: deque[Any] = deque(maxlen=max_points)
    previous: float | None = None

    def issue(code: str, offset: int, detail: str) -> None:
        nonlocal issue_count
        issue_count += 1
        if len(issues) < _MAX_ISSUES:
            issues.append({"code": code, "byte_offset": offset, "detail": detail[:200]})

    if (size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        issue("file_changed_during_read", 0, "File size/mtime changed; snapshot extent uses initial size")
    if start + len(body) != size:
        issue("short_read", start + len(body), "File shrank or the snapshot read was incomplete")
    offset = start
    for line in body.splitlines(keepends=True):
        row_offset, offset = offset, offset + len(line)
        if not line.strip():
            continue
        data_rows += 1
        unterminated = not line.endswith(b"\n") and offset == start + len(body)
        tokens = line.split(maxsplit=len(columns))
        if len(tokens) != len(columns):
            incomplete = (unterminated and len(tokens) < len(columns)
                          and all(_NUMBER.fullmatch(token) for token in tokens[:-1])
                          and (_NUMBER.fullmatch(tokens[-1]) is not None
                               or (_NUMBER_PREFIX.fullmatch(tokens[-1]) is not None
                                   and not line.endswith((b" ", b"\t", b"\r")))))
            issue("incomplete_trailing_row" if incomplete else "malformed_row", row_offset,
                  f"Expected {len(columns)} fields, got {len(tokens)}; raw={line[:100]!r}")
            rejected += 1
            continue
        try:
            row = [float(token.replace(b"D", b"e").replace(b"d", b"e")) for token in tokens]
        except (ValueError, OverflowError):
            incomplete = (unterminated and not line.endswith((b" ", b"\t", b"\r"))
                          and all(_NUMBER.fullmatch(token) for token in tokens[:-1])
                          and _NUMBER_PREFIX.fullmatch(tokens[-1]) is not None)
            issue("incomplete_trailing_row" if incomplete else "malformed_row", row_offset,
                  f"Invalid numeric token; raw={line[:100]!r}")
            rejected += 1
            continue
        if not all(math.isfinite(value) for value in row):
            bad_columns = [columns[i] for i, value in enumerate(row) if not math.isfinite(value)]
            issue("nonfinite_data", row_offset, f"Nonfinite column(s): {bad_columns}")
            rejected += 1
            continue
        if not all(_NUMBER.fullmatch(token) for token in tokens):
            issue("malformed_row", row_offset, f"Invalid numeric syntax; raw={line[:100]!r}")
            rejected += 1
            continue
        if unterminated:
            issue("unterminated_trailing_row", row_offset, "Row included, but final token may still be extending")
        coordinate = row[coordinate_index]
        if previous is not None and coordinate <= previous:
            segment += 1
            events_count += 1
            events.append({"byte_offset": row_offset, "segment": segment,
                           "kind": "decrease" if coordinate < previous else "repeat",
                           "previous_coordinate": previous, "coordinate": coordinate})
        records.append((row, row_offset, segment, unterminated))
        valid += 1
        previous = coordinate
    segments: list[dict[str, Any]] = []
    for index, (row, row_offset, segment_id, _) in enumerate(records):
        if not segments or segments[-1]["segment"] != segment_id:
            segments.append({"segment": segment_id, "start_index": index, "end_index": index + 1})
        else:
            segments[-1]["end_index"] = index + 1
    first_offset = records[0][1] if records else offset
    return {
        **result, "status": "partial" if issue_count else ("ok" if valid else "unavailable"),
        "reason": "review_issues" if issue_count else ("samples_available" if valid else "no_samples"),
        "total_points": valid if complete else None, "total_points_lower_bound": valid,
        "total_data_rows": data_rows if complete else None, "scanned_data_rows": data_rows,
        "valid_points_scanned": valid, "rejected_rows": rejected,
        "returned_points": len(records), "truncated": not complete or valid > len(records),
        "rows": [record[0] for record in records],
        "row_byte_offsets": [record[1] for record in records],
        "row_provisional": [record[3] for record in records],
        "segments": segments, "segment_range_scope": "returned_rows", "segment_id_scope": "scanned_data",
        "max_cells": max_cells, "effective_max_points": effective_points,
        "segment_count_scanned": segment + 1 if valid else 0,
        "nonmonotonic_events_scanned": events_count,
        "nonmonotonic_events": [event for event in events if event["byte_offset"] >= first_offset],
        "issues": issues, "issue_count": issue_count, "issues_truncated": issue_count > len(issues),
    }
