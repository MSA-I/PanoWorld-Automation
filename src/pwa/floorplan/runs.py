"""Derived parse-run filesystem helpers."""

from __future__ import annotations

import os
from pathlib import Path

from pwa.files import copy_immutable, is_link_or_reparse


def resolve_contained_run(runs_root: Path, candidate: Path) -> Path:
    runs_root = Path(runs_root).resolve(strict=True)
    candidate = Path(candidate)
    # Reject raw ".." components regardless of whether candidate is absolute or
    # relative: an absolute path containing ".." must not silently walk back out
    # of runs_root before the lexical containment check below ever runs.
    if any(part == ".." for part in candidate.parts):
        raise ValueError("source_run must stay within runs_root")
    if not candidate.is_absolute():
        candidate = runs_root / candidate
    # Resolve symlinks/reparse points in the candidate itself before the
    # containment check, so a symlinked ancestor cannot lexically appear
    # contained while actually pointing outside runs_root.
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(runs_root)
    except ValueError as exc:
        raise ValueError("source_run must stay within runs_root") from exc
    if not relative.parts:
        raise ValueError("source_run must not equal runs_root")
    cursor = runs_root
    for part in relative.parts:
        cursor = cursor / part
        if not cursor.exists():
            raise ValueError("source_run does not exist")
        if is_link_or_reparse(cursor):
            raise ValueError("source_run traverses a link or reparse point")
    return cursor


def resolve_contained_relpath(root: Path, relpath: str, *, must_exist: bool = True) -> Path:
    """Resolve ``relpath`` under ``root`` and reject any escape or reparse point.

    Unlike :func:`resolve_contained_run`, ``relpath`` is always required to be a
    *relative* path (never absolute, never containing ``..``), matching the
    manifest-declared ``inputs[].path`` shape. The full ancestor chain from
    ``root`` down to the leaf is walked and checked for symlinks/reparse
    points, per D-013's "every ancestor from runs_root to the file" rule.
    """
    # Not strict: the destination side (staging_run/"project") may not exist yet
    # on the first write, whereas the source side is already a verified,
    # existing, resolved run directory. Either way `root` itself is never
    # attacker-controlled here (it is either the already-contained source run
    # or our own freshly created staging directory).
    root = Path(root).resolve(strict=False)
    candidate = Path(relpath)
    if candidate.is_absolute() or not candidate.parts or any(part == ".." for part in candidate.parts):
        raise ValueError("path must be a contained relative path")
    joined = root / candidate
    resolved = joined.resolve(strict=False)
    try:
        relative = resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes containment root") from exc
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        exists = cursor.exists()
        if must_exist and not exists:
            raise ValueError("path does not exist")
        if exists and is_link_or_reparse(cursor):
            raise ValueError("path traverses a link or reparse point")
    return cursor


def copy_source_inventory(source_run: Path, staging_run: Path, manifest: dict) -> None:
    staging_project = staging_run / "project"
    for item in manifest["payload"]["inputs"]:
        source_item = resolve_contained_relpath(source_run, item["path"])
        destination_item = resolve_contained_relpath(staging_project, item["path"], must_exist=False)
        copy_immutable(source_item, destination_item)


def copy_artifact(source: Path, destination: Path) -> None:
    copy_immutable(source, destination)


def finalize_run(staging_run: Path, final_run: Path) -> None:
    final_run.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staging_run, final_run)
