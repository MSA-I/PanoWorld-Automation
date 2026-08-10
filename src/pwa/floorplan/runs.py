"""Derived parse-run filesystem helpers."""

from __future__ import annotations

import os
from pathlib import Path

from pwa.files import copy_immutable, is_link_or_reparse


def resolve_contained_run(runs_root: Path, candidate: Path) -> Path:
    runs_root_raw = Path(runs_root)
    # GC-2 (OpenAI cross-provider rework review, 2026-08-10): a runs_root
    # that is itself a symlink/junction must be rejected before
    # resolve(strict=True) below erases it -- the previous code resolved
    # runs_root as its very first step with no check at all.
    if is_link_or_reparse(runs_root_raw):
        raise ValueError("runs_root must not be a link or reparse point")
    runs_root = runs_root_raw.resolve(strict=True)
    candidate = Path(candidate)
    # Reject raw ".." components regardless of whether candidate is absolute or
    # relative: an absolute path containing ".." must not silently walk back out
    # of runs_root before the lexical containment check below ever runs.
    if any(part == ".." for part in candidate.parts):
        raise ValueError("source_run must stay within runs_root")
    if not candidate.is_absolute():
        candidate = runs_root_raw / candidate
    # GC-2: walk the ORIGINAL lexical candidate -- never a resolve()d one --
    # ancestor by ancestor from runs_root down, so an intermediate
    # symlink/junction is inspected before it is substituted away, even when
    # its resolved target would itself remain lexically under runs_root
    # (e.g. runs/alias -> runs/actual). Resolving the whole candidate first
    # (the pre-fix approach) let exactly that case through, because the
    # ancestor walk then only ever saw the already-substituted "actual"
    # component, never the "alias" junction itself.
    try:
        relative = candidate.relative_to(runs_root_raw)
    except ValueError as exc:
        raise ValueError("source_run must stay within runs_root") from exc
    if not relative.parts:
        raise ValueError("source_run must not equal runs_root")
    cursor = runs_root_raw
    for part in relative.parts:
        cursor = cursor / part
        if not cursor.exists():
            raise ValueError("source_run does not exist")
        if is_link_or_reparse(cursor):
            raise ValueError("source_run traverses a link or reparse point")
    # Independently confirm the fully resolved destination is still
    # contained under the resolved root, as defense in depth (e.g. against
    # case-folding oddities the lexical walk above cannot observe). Every
    # ancestor was just proven not to be a link/reparse point, so this
    # resolve() cannot substitute anything away.
    resolved = cursor.resolve(strict=True)
    try:
        resolved.relative_to(runs_root)
    except ValueError as exc:
        raise ValueError("source_run must stay within runs_root") from exc
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
    root_raw = Path(root)
    # GC-2 (OpenAI cross-provider rework review, 2026-08-10): mirror
    # resolve_contained_run()'s fix here too -- this helper is the exact
    # containment routine GC-3 routes the manifest/quality-report reads
    # through, so it must not share the same defect. `root` itself is
    # checked for reparse-ness only if it already exists (the destination
    # side may not exist yet on the very first write).
    if root_raw.exists() and is_link_or_reparse(root_raw):
        raise ValueError("containment root must not be a link or reparse point")
    candidate = Path(relpath)
    if candidate.is_absolute() or not candidate.parts or any(part == ".." for part in candidate.parts):
        raise ValueError("path must be a contained relative path")
    # GC-2: walk the ORIGINAL lexical candidate -- never a resolve()d one --
    # ancestor by ancestor from root, so an intermediate symlink/junction is
    # inspected before it is substituted away, even when its resolved target
    # would itself remain lexically under root.
    cursor = root_raw
    for part in candidate.parts:
        cursor = cursor / part
        exists = cursor.exists()
        if must_exist and not exists:
            raise ValueError("path does not exist")
        if exists and is_link_or_reparse(cursor):
            raise ValueError("path traverses a link or reparse point")
    # Independently confirm the fully resolved destination is still
    # contained under the resolved root, as defense in depth. Every ancestor
    # was just proven not to be a link/reparse point, so this resolve()
    # cannot substitute anything away.
    root_resolved = root_raw.resolve(strict=False)
    resolved = cursor.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("path escapes containment root") from exc
    return cursor


def copy_source_inventory(source_run: Path, staging_run: Path, manifest: dict) -> None:
    staging_project = staging_run / "project"
    for item in manifest["payload"]["inputs"]:
        source_item = resolve_contained_relpath(source_run, item["path"])
        destination_item = resolve_contained_relpath(staging_project, item["path"], must_exist=False)
        copied_hash = copy_immutable(source_item, destination_item)
        # A (OpenAI cross-provider rework review, 2026-08-10): preflight
        # hashes the source, then this copies it -- but copy_immutable()'s
        # own hash check only proves the destination matches what it *just*
        # read from source, not what the manifest declared at preflight
        # time. Reverify against the manifest-declared hash so a file that
        # changes on disk between the preflight check and this copy is
        # caught instead of silently finalizing with a stale hash (D-013's
        # "reverified hashes").
        if copied_hash != item["sha256"]:
            raise ValueError("source inventory item changed between preflight and copy")


def copy_artifact(source: Path, destination: Path) -> None:
    copy_immutable(source, destination)


def finalize_run(staging_run: Path, final_run: Path) -> None:
    final_run.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staging_run, final_run)
