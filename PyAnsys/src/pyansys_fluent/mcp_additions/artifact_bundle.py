"""Offline, explicit-selection Fluent evidence bundles; no solver or MCP access."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
from io import BytesIO, StringIO
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import stat
from typing import Any
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile


__all__ = ["bundle_artifacts"]
_MAX_BYTES = 16 * 1024 * 1024
_MAX_MANIFEST_BYTES = 256 * 1024
_EXTENSIONS = {".png", ".json", ".csv", ".out", ".vw", ".npz", ".html"}
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eEdD][+-]?[0-9]+)?\Z")
_NONFINITE = re.compile(r"[+-]?(?:nan|inf(?:inity)?)(?:\.0)?\Z", re.IGNORECASE)
_TOKENS = re.compile(r'"(?:[^"\\]|\\.)*"|[^\s(),\[\]#]+')
_LIMITATIONS = [
    "Caller grouping does not prove common case/data lineage or scientific completeness.",
    "Separate file reads are not an atomic multi-file snapshot. Unchanged stat metadata "
    "does not prove a writer has finished or exclude undetected concurrent edits.",
    "Hashes identify the exact archived bytes, not the current or final source files.",
    "Receipts are copied without trusting or following their paths, hashes or claims. "
    "Embedded absolute paths and external references are not rewritten or fetched.",
    "CSV/OUT/VW checks cover standalone numeric tokens, not report grammar, units, "
    "coordinate meaning, convergence, array alignment or physical validity.",
    "PNG signatures are checked without decoding images. HTML is opaque and is not "
    "rendered or checked for active content. No dependent assets are collected.",
    "Retrieve output only after successful return. Process termination can leave "
    "an incomplete ZIP at the exclusively created output path.",
    "Path and handle checks detect ordinary escapes and replacement; callers must "
    "prevent hostile concurrent directory reparenting. This is not a filesystem sandbox.",
]


def _limit(name: str, value: int) -> None:
    if type(value) is not int or not 1 <= value <= _MAX_BYTES:
        raise ValueError(f"{name} must be an integer in [1, {_MAX_BYTES}]")


def _local_path(value: str) -> Path:
    if not isinstance(value, str) or not value.strip() or len(value) > 4096 or "\x00" in value:
        raise ValueError("Paths must be nonempty local strings of at most 4096 characters")
    windows = PureWindowsPath(value)
    if (value.startswith(("\\\\", "//")) or "://" in value
            or windows.drive.startswith("\\\\")):
        raise ValueError("URI, UNC and device paths are not supported")
    # Reject device names, aliasing suffixes and alternate data streams too.
    parts = windows.parts[1:] if windows.anchor else windows.parts
    if any(":" in part or PureWindowsPath(part).is_reserved()
           or part.endswith((" ", ".")) for part in parts):
        raise ValueError("Reserved names, trailing dots/spaces and data streams are not supported")
    path = Path(value)
    if ".." in path.parts or ".." in windows.parts:
        raise ValueError("Parent traversal is not supported")
    if path.drive and not path.is_absolute():
        raise ValueError("Drive-relative paths are not supported")
    return path


def _inside(root: Path, path: Path) -> Path:
    _local_path(str(path))
    if not path.is_relative_to(root):
        raise ValueError("Resolved path is outside root")
    return path


def _resolve_source(root: Path, selected: Path) -> Path:
    if root.resolve(strict=True) != root:
        raise ValueError("Root changed during bundling")
    return _inside(root, selected.resolve(strict=True))


def _stat_record(info: os.stat_result) -> dict[str, int]:
    # Windows path stat and descriptor fstat can disagree on ctime for the
    # same stable file. Keep cross-API comparisons to these identity fields.
    return {"device": info.st_dev, "inode": info.st_ino, "bytes": info.st_size,
            "mtime_ns": info.st_mtime_ns}


def _finite_number(token: str) -> bool:
    if _NONFINITE.fullmatch(token):
        raise ValueError("Nonfinite numeric token in selected artifact")
    if _NUMBER.fullmatch(token):
        if not math.isfinite(float(token.replace("D", "e").replace("d", "e"))):
            raise ValueError("Nonfinite or overflowing numeric token in selected artifact")
        return True
    return False


def _json_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("Nonfinite JSON number in selected artifact")
    return value


def _json_constant(token: str) -> None:
    raise ValueError(f"Nonfinite JSON constant: {token}")


def _check_npz(data: bytes, remaining: int) -> dict[str, Any]:
    # Import only for NPZ selections. Never allow pickle or extract members.
    import numpy as np

    arrays = []
    with ZipFile(BytesIO(data)) as archive:
        members = archive.infolist()
        if not 1 <= len(members) <= 128:
            raise ValueError("An NPZ must contain between 1 and 128 arrays")
        names: set[str] = set()
        expanded = sum(item.file_size for item in members)
        if expanded > remaining:
            raise ValueError("Selected NPZ contents exceed max_expanded_bytes")
        for item in members:
            name = item.filename
            if (not name.endswith(".npy") or len(name) > 255 or "/" in name
                    or "\\" in name or ":" in name or name.casefold() in names
                    or item.flag_bits & 1 or item.compress_type not in (ZIP_STORED, ZIP_DEFLATED)):
                raise ValueError("NPZ requires unique flat, unencrypted .npy members")
            names.add(name.casefold())
            with archive.open(item) as source:
                raw = source.read(item.file_size + 1)
            if len(raw) != item.file_size:
                raise ValueError("NPZ member size does not match its receipt")
            stream = BytesIO(raw)
            version = np.lib.format.read_magic(stream)
            if version == (1, 0):
                shape, _, dtype = np.lib.format.read_array_header_1_0(stream, max_header_size=10000)
            elif version == (2, 0):
                shape, _, dtype = np.lib.format.read_array_header_2_0(stream, max_header_size=10000)
            else:
                raise ValueError("Only NPY versions 1 and 2 are supported")
            if dtype.kind not in "biufc" or dtype.hasobject or not dtype.itemsize:
                raise ValueError("NPZ arrays must have plain numeric or boolean dtypes")
            if len(shape) > 32 or any(type(size) is not int or size < 0 for size in shape):
                raise ValueError("NPY shape must have at most 32 nonnegative integer dimensions")
            count = math.prod(shape)
            if count * dtype.itemsize != len(raw) - stream.tell():
                raise ValueError("NPY shape/dtype does not match its bounded payload")
            values = np.frombuffer(raw, dtype=dtype, count=count, offset=stream.tell())
            if not bool(np.isfinite(values).all()):
                raise ValueError(f"Nonfinite NPZ values in {name}")
            arrays.append({"name": name, "shape": list(shape), "dtype": str(dtype), "values": count})
    return {"kind": "numeric_npz", "finite_data": "all_array_values_checked",
            "expanded_bytes": expanded, "arrays": arrays}


def _check_content(suffix: str, data: bytes, expanded_remaining: int) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    if suffix == ".npz":
        return _check_npz(data, expanded_remaining), issues
    if suffix == ".png":
        if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n") or data[12:16] != b"IHDR":
            raise ValueError("Selected PNG lacks a PNG/IHDR signature")
        return {"kind": "png_signature_only", "finite_data": "not_assessed"}, issues
    if suffix == ".html":
        return {"kind": "opaque_html", "finite_data": "not_assessed"}, issues
    text = data.decode("utf-8-sig")
    if suffix == ".json":
        try:
            payload = json.loads(text, parse_float=_json_float, parse_constant=_json_constant)
        except RecursionError as exc:
            raise ValueError("Selected JSON exceeds parser nesting capacity") from exc
        flags: dict[str, Any] = {}
        if isinstance(payload, dict):
            for key in ("truncated", "scan_truncated", "byte_truncated", "in_progress", "partial"):
                if payload.get(key) is True:
                    flags[key] = True
                    issues.append(f"source_declares_{key}")
            status = payload.get("status")
            if status in ("partial", "in_progress", "error", "unavailable"):
                flags["status"] = status
                issues.append("source_declares_" + status)
            if payload.get("errors"):
                flags["errors_present"] = True
                issues.append("source_declares_errors")
        return {"kind": "json", "finite_data": "all_json_numbers_checked",
                "source_declared_flags": flags}, issues
    tokens = 0
    if suffix == ".csv":
        for row in csv.reader(StringIO(text, newline=""), strict=True):
            for cell in row:
                tokens += _finite_number(cell.strip())
    else:
        for match in _TOKENS.finditer(text):
            token = match.group()
            if not token.startswith('"'):
                tokens += _finite_number(token)
    if suffix in (".csv", ".out") and data and not data.endswith(b"\n"):
        issues.append("unterminated_last_line_may_be_in_progress")
    if not data:
        issues.append("empty_source")
    return {"kind": "numeric_token_scan", "finite_data": "standalone_numeric_tokens_checked",
            "numeric_tokens_checked": tokens}, issues


def _output_path(root: Path, requested: Path) -> Path:
    parent = _inside(root, requested.parent.resolve(strict=True))
    if not parent.is_dir():
        raise ValueError("Output parent must be an existing directory within root")
    target = parent / requested.name
    if target.suffix.lower() != ".zip":
        raise ValueError("Output must end in .zip")
    # lstat also rejects dangling symlinks; publication itself is exclusive.
    if os.path.lexists(target):
        raise FileExistsError("Output already exists; choose a new .zip path")
    return target


def _check_output_parent(root: Path, target: Path) -> None:
    if root.resolve(strict=True) != root or target.parent.resolve(strict=True) != target.parent:
        raise ValueError("Output parent changed during bundling")
    _inside(root, target)


def bundle_artifacts(
    root: str,
    files: list[str],
    output: str,
    *,
    max_total_bytes: int = _MAX_BYTES,
    max_expanded_bytes: int = _MAX_BYTES,
) -> dict[str, Any]:
    """Create a new bounded ZIP with ``manifest.json`` and explicit artifact bytes.

    ``root`` must be an absolute local directory. Input/output paths may be
    absolute or relative to it; resolved paths must remain inside it. The
    output parent must already exist. No traversal, UNC/device paths, directory
    crawling, remote fetching, implicit sidecars or overwrites are permitted.
    Select 1..32 regular PNG/JSON/CSV/OUT/VW/NPZ/HTML files explicitly. Numbered
    members (``artifacts/001.png`` etc.) map to root-relative source paths in
    the manifest; identical basenames cannot collide. Duplicate source paths
    or file identities are rejected. Source bytes are copied without changes.

    Both byte limits are positive integers capped at 16 MiB. max_total_bytes
    bounds the summed initial source extents; growing files are not chased.
    max_expanded_bytes separately bounds the sum of uncompressed NPY members
    across all selected NPZ files. NPZ needs NumPy and supports at most 128
    flat numeric/boolean NPY v1/v2 members per file, with pickle forbidden.
    JSON must parse; text must be UTF-8 (optional BOM). Nonfinite JSON/NPZ
    numbers and standalone nonfinite/overflowing CSV/OUT/VW numbers fail.
    PNG/HTML and arbitrary text syntax have the limitations in the manifest.

    Each hash covers the exact bytes read from one identity-checked handle.
    Before/after stat records, source-declared truncation/error flags and
    incomplete text endings expose observed uncertainty. Source completion is
    always unknown: packaging status ``ok`` proves neither finality nor shared
    scientific lineage. Malformed JSON/NPZ cannot be validated and must be
    retried after their writer finishes. A detected escape/replacement fails.

    All selected content is checked before exclusively creating output. ZIP
    source data is bounded as above; its manifest is capped at 256 KiB plus ZIP
    overhead. The response contains ``zip`` (local path, relative path, bytes,
    SHA-256), ``manifest`` and ``manifest_sha256``. MCP resource registration
    and client retrieval belong to the caller. No Fluent dependency is loaded.
    On failure, cleanup removes only the file exclusively created here when
    its path still identifies our inode; cleanup failures annotate the error.
    Validation and OS/decoder failures propagate; no partial success is hidden.
    """
    _limit("max_total_bytes", max_total_bytes)
    _limit("max_expanded_bytes", max_expanded_bytes)
    if type(files) is not list or not 1 <= len(files) <= 32:
        raise ValueError("files must be an explicit list of 1..32 paths")
    root_path = _local_path(root)
    if not root_path.is_absolute():
        raise ValueError("root must be an absolute local directory")
    root_path = _local_path(str(root_path.resolve(strict=True)))
    if not root_path.is_dir():
        raise ValueError("root must be a directory")
    requested_output = _local_path(output)
    if not requested_output.is_absolute():
        requested_output = root_path / requested_output
    target = _output_path(root_path, requested_output)
    selected = []
    seen_paths: set[Path] = set()
    seen_identities: set[tuple[int, int]] = set()
    initial_bytes = 0
    for value in files:
        path = _local_path(value)
        path = path if path.is_absolute() else root_path / path
        resolved = _resolve_source(root_path, path)
        suffix = resolved.suffix.lower()
        if suffix not in _EXTENSIONS:
            raise ValueError("Selected extension is not PNG/JSON/CSV/OUT/VW/NPZ/HTML")
        info = resolved.stat()
        identity = (info.st_dev, info.st_ino)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Select regular files only")
        if resolved in seen_paths or identity in seen_identities:
            raise ValueError("Duplicate source path or file identity")
        seen_paths.add(resolved)
        seen_identities.add(identity)
        initial_bytes += info.st_size
        if initial_bytes > max_total_bytes:
            raise ValueError("Selected sources exceed max_total_bytes")
        selected.append((path, resolved, info, suffix))

    captured = []
    records = []
    expanded = read_bytes = 0
    for index, (path, resolved, planned, suffix) in enumerate(selected, 1):
        if _resolve_source(root_path, path) != resolved:
            raise ValueError("Selected path changed before read")
        with resolved.open("rb") as source:
            before = os.fstat(source.fileno())
            if not stat.S_ISREG(before.st_mode) or not os.path.samestat(planned, before):
                raise ValueError("Source identity changed before read")
            # Use the preflight extent, even if an active writer has appended.
            data = source.read(planned.st_size)
            after = os.fstat(source.fileno())
        if _resolve_source(root_path, path) != resolved or not os.path.samestat(after, resolved.stat()):
            raise ValueError("Selected source was replaced during read")
        validation, issues = _check_content(suffix, data, max_expanded_bytes - expanded)
        expanded += validation.get("expanded_bytes", 0)
        if _stat_record(planned) != _stat_record(before):
            issues.append("source_changed_since_selection")
        if _stat_record(before) != _stat_record(after):
            issues.append("source_changed_during_read")
        if len(data) != planned.st_size:
            issues.append("short_read")
        member = f"artifacts/{index:03d}{suffix}"
        records.append({"source_relative": resolved.relative_to(root_path).as_posix(),
                        "member": member, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "planned": _stat_record(planned), "before": _stat_record(before),
                        "after": _stat_record(after), "completion": "unknown",
                        "status": "partial" if issues else "ok", "issues": issues,
                        "validation": validation})
        read_bytes += len(data)
        captured.append((member, data))

    manifest = {"schema": "fluent.artifact-bundle.v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "partial" if any(r["issues"] for r in records) else "ok",
                "status_scope": "packaging_only", "grouping_basis": "caller_explicit_selection",
                "common_case_lineage": "not_established", "scientific_completeness": "not_assessed",
                "source_completion": "unknown", "atomic_multi_file_snapshot": False,
                "file_count": len(records), "initial_source_bytes": initial_bytes,
                "archived_source_bytes": read_bytes, "expanded_npz_bytes": expanded,
                "limits": {"files": 32, "max_total_bytes": max_total_bytes,
                           "max_expanded_bytes": max_expanded_bytes,
                           "max_manifest_bytes": _MAX_MANIFEST_BYTES},
                "files": records, "limitations": list(_LIMITATIONS)}
    manifest_data = (json.dumps(manifest, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
    if len(manifest_data) > _MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds 256 KiB; select fewer/smaller NPZ member sets")
    manifest_sha256 = hashlib.sha256(manifest_data).hexdigest()
    owned = None
    try:
        _check_output_parent(root_path, target)
        with target.open("x+b") as stream:
            owned = os.fstat(stream.fileno())
            with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
                archive.writestr("manifest.json", manifest_data)
                for member, data in captured:
                    archive.writestr(member, data)
            stream.flush()
            os.fsync(stream.fileno())
            stream.seek(0)
            digest = hashlib.sha256()
            while chunk := stream.read(65536):
                digest.update(chunk)
            final = os.fstat(stream.fileno())
            _check_output_parent(root_path, target)
            if not os.path.samestat(final, target.lstat()):
                raise ValueError("Output was replaced during publication")
        return {"status": manifest["status"],
                "zip": {"path": str(target), "relative_path": target.relative_to(root_path).as_posix(),
                        "bytes": final.st_size, "sha256": digest.hexdigest()},
                "manifest_member": "manifest.json", "manifest_sha256": manifest_sha256,
                "manifest": manifest}
    except Exception as exc:
        if owned is not None:
            try:
                _check_output_parent(root_path, target)
                if os.path.samestat(owned, target.lstat()):
                    target.unlink()
                else:
                    exc.add_note("Output path no longer identifies this operation's file; left untouched")
            except FileNotFoundError:
                pass
            except Exception as cleanup:
                exc.add_note(f"Could not remove operation-owned output: {type(cleanup).__name__}: {cleanup}")
        raise
