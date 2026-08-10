"""Derived parse-run filesystem helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import copy_immutable, is_link_or_reparse, sha256_file
from pwa.floorplan.findings import FloorplanError


class FinalizedRunLeftBehindError(OSError):
    """Finalization failed and the published directory could not be rolled back."""


def _contained_parts(relpath: str | Path) -> tuple[str, ...]:
    candidate = Path(relpath)
    invalid_component = any(
        part in {"", ".", ".."} or ":" in part
        for part in candidate.parts
    )
    if candidate.is_absolute() or not candidate.parts or invalid_component:
        raise ValueError("path must be a contained relative path")
    return candidate.parts


def validate_contained_destination(root: Path, relpath: str | Path) -> Path:
    """Validate an output path without trusting a not-yet-existing root.

    Every existing component is inspected lexically before ``resolve()`` can
    erase a junction or symlink. Missing components are permitted because this
    helper is used before staging is created.
    """
    root = Path(root)
    if not root.exists() or not root.is_dir() or is_link_or_reparse(root):
        raise ValueError("destination root must be an existing regular directory")
    cursor = root
    for part in _contained_parts(relpath):
        cursor = cursor / part
        if cursor.exists() or cursor.is_symlink():
            if is_link_or_reparse(cursor):
                raise ValueError("destination traverses a link or reparse point")
    root_resolved = root.resolve(strict=True)
    resolved = cursor.resolve(strict=False)
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("path escapes containment root") from exc
    return cursor


def create_contained_directory(root: Path, relpath: str | Path) -> Path:
    """Create a destination directory one checked component at a time."""
    root = Path(root)
    validate_contained_destination(root, relpath)
    parts = _contained_parts(relpath)
    cursor = root
    for index, part in enumerate(parts):
        cursor = cursor / part
        if cursor.exists() or cursor.is_symlink():
            if is_link_or_reparse(cursor) or not cursor.is_dir():
                raise ValueError("destination traverses a non-directory or reparse point")
            if index == len(parts) - 1:
                raise FileExistsError(str(cursor))
            continue
        cursor.mkdir()
        if is_link_or_reparse(cursor) or not cursor.is_dir():
            raise ValueError("created destination directory is not a regular directory")
    return cursor


def resolve_contained_output(root: Path, relpath: str | Path) -> Path:
    """Return a new output leaf after checking/creating its parent chain."""
    parts = _contained_parts(relpath)
    if len(parts) > 1:
        parent_relative = Path(*parts[:-1])
        parent_path = Path(root) / parent_relative
        if parent_path.exists() or parent_path.is_symlink():
            validate_contained_destination(root, parent_relative)
            if not parent_path.is_dir():
                raise ValueError("destination parent must be a directory")
        else:
            create_contained_directory(root, parent_relative)
    leaf = validate_contained_destination(root, Path(*parts))
    if leaf.exists() or leaf.is_symlink():
        raise FileExistsError(str(leaf))
    return leaf


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
    if len(relative.parts) != 1 or relative.parts[0].startswith("."):
        raise ValueError("source_run must be a direct finalized child of runs_root")
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
    if not cursor.is_dir():
        raise ValueError("source_run must be a directory")
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
    for item in manifest["payload"]["inputs"]:
        source_item = resolve_contained_relpath(source_run, item["path"])
        destination_item = resolve_contained_output(staging_run, item["path"])
        copied_hash = copy_immutable(source_item, destination_item, create_parents=False)
        # The source manifest is the preflight declaration. copy_immutable()
        # proves the staged bytes match its one source read; this comparison
        # also proves that snapshot matches the immutable declared hash.
        if copied_hash != item["sha256"]:
            raise FloorplanError(
                "PARSE_SOURCE_HASH_MISMATCH",
                "source inventory item does not match its declared hash",
                source_ref=item["path"],
            )


def write_bytes_contained(
    root: Path,
    relpath: str | Path,
    data: bytes,
    *,
    create_parents: bool = True,
) -> Path:
    if create_parents:
        destination = resolve_contained_output(root, relpath)
    else:
        destination = validate_contained_destination(root, relpath)
        if not destination.parent.is_dir() or is_link_or_reparse(destination.parent):
            raise ValueError("destination parent must be an existing regular directory")
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(str(destination))
    with destination.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return destination


def verify_run_inventory(run_root: Path, manifest: dict) -> None:
    for item in manifest["payload"]["inputs"]:
        declared_path = resolve_contained_relpath(run_root, item["path"])
        if sha256_file(declared_path) != item["sha256"]:
            raise ValueError("finalized inventory hash mismatch")


_REQUIRED_ENVELOPE_PATHS = (
    "project/source-manifest.json",
    "project/source-quality-report.json",
    "project/project_manifest.json",
    "project/input_quality_report.json",
    "parse/floorplan_parse.json",
    "parse/assumptions.json",
)


def _load_json_document(run_root: Path, relpath: str) -> dict:
    path = resolve_contained_relpath(run_root, relpath)
    try:
        document = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("finalized JSON document is unreadable") from exc
    if not isinstance(document, dict):
        raise ValueError("finalized JSON document must be an object")
    return document


def _verify_envelope(document: dict, message: str) -> None:
    try:
        errors = validate_artifact(document)
        content_hash_matches = document.get("content_hash") == compute_content_hash(document)
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        raise ValueError(message) from exc
    if errors or not content_hash_matches:
        raise ValueError(message)


def verify_run_derived_artifacts(run_root: Path) -> None:
    envelopes: dict[str, dict] = {}
    for relpath in _REQUIRED_ENVELOPE_PATHS:
        document = _load_json_document(run_root, relpath)
        _verify_envelope(document, "finalized envelope content hash mismatch")
        envelopes[relpath] = document

    annotation_path = resolve_contained_relpath(
        run_root,
        "parse/annotation.json",
        must_exist=False,
    )
    if annotation_path.exists():
        annotation = _load_json_document(run_root, "parse/annotation.json")
        _verify_envelope(annotation, "finalized annotation content hash mismatch")

    parse_report = _load_json_document(run_root, "parse/parse-report.json")
    overlay_declarations = [
        envelopes["parse/floorplan_parse.json"].get("payload", {}).get("overlay"),
        parse_report.get("overlay"),
    ]
    for declaration in overlay_declarations:
        if not isinstance(declaration, dict) or "path" not in declaration:
            continue
        overlay_relpath = declaration["path"]
        overlay_sha256 = declaration.get("sha256")
        if not isinstance(overlay_relpath, str) or not isinstance(overlay_sha256, str):
            raise ValueError("finalized overlay declaration is invalid")
        overlay_path = resolve_contained_relpath(run_root, overlay_relpath)
        if sha256_file(overlay_path) != overlay_sha256:
            raise ValueError("finalized overlay hash mismatch")


def finalize_run(staging_run: Path, final_run: Path, manifest: dict) -> None:
    runs_root = final_run.parent
    staging_relative = staging_run.relative_to(runs_root)
    resolve_contained_relpath(runs_root, staging_relative.as_posix())
    validate_contained_destination(runs_root, final_run.name)
    if final_run.exists() or final_run.is_symlink():
        raise FileExistsError(str(final_run))
    verify_run_inventory(staging_run, manifest)
    verify_run_derived_artifacts(staging_run)
    os.replace(staging_run, final_run)
    try:
        verify_run_inventory(final_run, manifest)
        verify_run_derived_artifacts(final_run)
    except (OSError, ValueError):
        try:
            os.replace(final_run, staging_run)
        except OSError as rollback_error:
            raise FinalizedRunLeftBehindError(
                "finalized directory left behind after rollback failure"
            ) from rollback_error
        raise
