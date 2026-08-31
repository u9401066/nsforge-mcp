"""Validated filesystem paths for repository and exported artifacts.

Paths entering an MCP handler are untrusted.  This module centralises lexical
validation and resolved-path containment so adapters cannot accidentally turn a
category, identifier, or output filename into an arbitrary filesystem write.
"""

from __future__ import annotations

import re
from pathlib import Path

_STORAGE_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class UnsafeStoragePath(ValueError):
    """Raised when an untrusted path would escape its configured root."""


def validate_storage_segment(value: str, *, field: str) -> str:
    """Return an opaque storage segment after strict lexical validation."""
    if value in {"", ".", ".."} or _STORAGE_SEGMENT.fullmatch(value) is None:
        raise UnsafeStoragePath(
            f"{field} must be 1-128 ASCII letters, digits, '.', '_' or '-' "
            "and must not contain path separators"
        )
    return value


def contained_path(root: Path, candidate: str | Path, *, field: str) -> Path:
    """Resolve *candidate* and require it to remain beneath *root*.

    Existing symlinks in either the parent path or the final component are
    resolved before the containment check, which also blocks symlink escapes.
    Absolute paths are accepted only when they already point inside ``root``;
    this preserves legacy callers that pass an absolute temporary path while
    retaining a real security boundary.
    """
    resolved_root = root.resolve()
    raw = Path(candidate)
    resolved = (raw if raw.is_absolute() else resolved_root / raw).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise UnsafeStoragePath(f"{field} must stay within {resolved_root}")
    return resolved


def contained_output_path(
    root: Path,
    candidate: str | Path,
    *,
    suffixes: frozenset[str],
) -> Path:
    """Resolve a contained output file and enforce an expected file suffix."""
    path = contained_path(root, candidate, field="output_path")
    if path.suffix.lower() not in suffixes:
        expected = ", ".join(sorted(suffixes))
        raise UnsafeStoragePath(f"output_path must use one of: {expected}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
