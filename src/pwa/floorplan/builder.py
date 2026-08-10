"""PLAN-002 parse-run orchestration."""

from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from PIL import Image

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import copy_immutable, sha256_file, write_json_exclusive
from pwa.floorplan.annotation_source import AnnotationSource
from pwa.floorplan.config import (
    MAX_ANNOTATION_BYTES,
    MAX_COORDINATE_MAGNITUDE_M,
    MAX_DXF_BYTES,
    MAX_OPENINGS,
    MAX_OVERLAY_BYTES,
    MAX_POLYGON_VERTICES,
    MAX_ROOMS,
    MAX_WALLS,
    limits_snapshot,
)
from pwa.floorplan.dxf_source import DxfSource
from pwa.floorplan.findings import Finding, FloorplanError, make_finding, sort_findings
from pwa.floorplan.normalize import canonical_projection, normalize
from pwa.floorplan.overlay import render_overlay
from pwa.floorplan.runs import (
    copy_artifact,
    copy_source_inventory,
    finalize_run,
    resolve_contained_relpath,
    resolve_contained_run,
)
from pwa.floorplan.validate import validate


# GC-1 (OpenAI cross-provider rework review, 2026-08-10): a closed allowlist
# grammar for --parse-run-id. It must resolve to exactly one path segment: no
# path separators (`/` or `\`), no drive letter/UNC prefix (no `:`), and --
# because the first character must be alphanumeric -- no `.`/`..` either.
# Joining a Path with an absolute or drive-relative operand silently discards
# the left-hand prefix (Path.__truediv__ semantics), so an unvalidated
# parse_run_id could previously make `runs_root / parse_run_id` resolve
# anywhere on the filesystem; this grammar is checked before any path is
# constructed from the value at all.
_PARSE_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _is_valid_parse_run_id(value: object) -> bool:
    return isinstance(value, str) and bool(_PARSE_RUN_ID_RE.match(value))


@dataclass(frozen=True)
class ParseRunResult:
    cli_exit: int
    final_run: Path
    staging_run: Path
    diagnostic: dict | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _artifact(
    schema_id: str,
    schema_version: str,
    payload: dict,
    *,
    project_id: str,
    run_id: str,
    status: str,
    inputs: list[dict] | None = None,
    errors: list[dict] | None = None,
) -> dict:
    document = {
        "schema_id": schema_id,
        "schema_version": schema_version,
        "artifact_id": f"{run_id}:{schema_id}",
        "project_id": project_id,
        "run_id": run_id,
        "created_at": _now(),
        "producer": {
            "agent": "plan002-floorplan-parser",
            "provider": "local",
            "model": "deterministic-python",
            "effort": "HIGH",
        },
        "inputs": inputs or [],
        "content_hash": "sha256:" + "0" * 64,
        "status": status,
        "errors": errors or [],
        "payload": payload,
    }
    document["content_hash"] = compute_content_hash(document)
    schema_errors = validate_artifact(document)
    if schema_errors:
        raise ValueError(schema_errors[0].message)
    return document


def _finding_errors(findings: list[Finding]) -> list[dict]:
    return [{"code": finding.code, "message": finding.message} for finding in findings]


def _projection_hash(projection: dict) -> str:
    canonical = json.dumps(projection, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _diagnostic(
    *,
    parse_run_id: str,
    source_run_id: str | None,
    adapter: str,
    cli_exit: int,
    outcome: str,
    finding: Finding | None,
    findings: list[Finding] | None = None,
    overlay_omitted_reason: str = "no_normalized_geometry",
) -> dict:
    findings = findings or ([finding] if finding is not None else [])
    return {
        "report_version": 1,
        "parse_run_id": parse_run_id,
        "source_run_id": source_run_id,
        "adapter": adapter,
        "outcome": outcome,
        "cli_exit": cli_exit,
        "terminal_finding": (
            {"code": finding.code, "severity": finding.severity, "source_ref": finding.source_ref}
            if finding is not None
            else None
        ),
        "limits": limits_snapshot(),
        "metrics": {"walls": 0, "rooms": 0, "openings": 0, "dimensions": 0, "source_entities_scanned": 0},
        "findings": [
            {
                "code": item.code,
                "severity": item.severity,
                "tier": item.tier,
                "source_ref": item.source_ref,
                "message": item.message,
            }
            for item in findings
        ],
        "overlay": {"overlay_omitted_reason": overlay_omitted_reason},
        "canonical_projection_sha256": None,
    }


def _failed_scale_artifacts(
    *,
    source_manifest: dict,
    source_quality: dict,
    parse_run_id: str,
    adapter: str = "annotation",
    finding: Finding | None = None,
    overlay_omitted_reason: str = "no_normalized_geometry",
    source_unit_scale_m: float | None = None,
    source_height_px: int | None = None,
    annotation_input: dict | None = None,
) -> tuple[dict, dict, dict, dict, dict]:
    finding = finding or make_finding("PARSE_SCALE_UNKNOWN", "annotation scale contradicts source manifest scale")
    source_scale = source_manifest["payload"]["scale"].get("m_per_px")
    source_units = "px" if adapter == "annotation" else source_manifest["payload"]["units"]
    # `normalization` is optional in the 1.1.0 schema. When the source units/scale
    # cannot be determined (e.g. manifest units == "unknown"), omit the block
    # entirely instead of fabricating a value or raising out of parse_run().
    normalization_block: dict | None = None
    if adapter == "annotation":
        effective_scale = source_unit_scale_m if source_unit_scale_m and source_unit_scale_m > 0 else source_scale
        if effective_scale is not None and float(effective_scale) > 0:
            resolved_source_unit_scale_m = float(effective_scale)
            normalization_block = {
                "quantum_m": 0.0001,
                "source_units": source_units,
                "source_unit_scale_m": resolved_source_unit_scale_m,
                "translation_m": [0.0, 0.0],
                "y_axis": "flipped_from_raster",
                "source_height_px": source_height_px,
                "scale_m_per_px": resolved_source_unit_scale_m,
            }
    else:
        resolved_source_unit_scale_m = {"mm": 0.001, "cm": 0.01, "m": 1.0}.get(source_manifest["payload"]["units"])
        if resolved_source_unit_scale_m is not None:
            normalization_block = {
                "quantum_m": 0.0001,
                "source_units": source_units,
                "source_unit_scale_m": resolved_source_unit_scale_m,
                "translation_m": [0.0, 0.0],
                "y_axis": "up",
                "source_height_px": None,
                "scale_m_per_px": None,
            }
    derived_manifest = _artifact(
        "project_manifest",
        "1.0.0",
        {**source_manifest["payload"], "contracts_bundle_version": "1.1.0"},
        project_id=source_manifest["project_id"],
        run_id=parse_run_id,
        status="complete",
        inputs=[
            {"artifact_id": source_manifest["artifact_id"], "content_hash": source_manifest["content_hash"]},
            {"artifact_id": source_quality["artifact_id"], "content_hash": source_quality["content_hash"]},
        ],
    )
    derived_quality = _artifact(
        "input_quality_report",
        "1.0.0",
        source_quality["payload"],
        project_id=source_quality["project_id"],
        run_id=parse_run_id,
        status="complete",
        inputs=[{"artifact_id": source_quality["artifact_id"], "content_hash": source_quality["content_hash"]}],
    )
    failed_payload: dict = {
        "units": "m",
        "scale_m_per_px": None,
        "rooms": [],
        "walls": [],
        "openings": [],
    }
    if normalization_block is not None:
        failed_payload["normalization"] = normalization_block
    # GC-4 (OpenAI cross-provider rework review, 2026-08-10): D-013 requires
    # the annotation artifact ID/hash to be bound into the parse outputs'
    # inputs[] too, not just the derived manifest/quality report, so the
    # finalized artifact records which annotation produced it.
    floorplan_parse_inputs = [
        {"artifact_id": derived_manifest["artifact_id"], "content_hash": derived_manifest["content_hash"]},
        {"artifact_id": derived_quality["artifact_id"], "content_hash": derived_quality["content_hash"]},
    ]
    if annotation_input is not None:
        floorplan_parse_inputs.append(annotation_input)
    floorplan_parse = _artifact(
        "floorplan_parse",
        "1.1.0",
        failed_payload,
        project_id=source_manifest["project_id"],
        run_id=parse_run_id,
        status="failed",
        inputs=floorplan_parse_inputs,
        errors=_finding_errors([finding]),
    )
    assumptions = _artifact(
        "assumptions",
        "1.0.0",
        {"stage": "parsing", "entries": []},
        project_id=source_manifest["project_id"],
        run_id=parse_run_id,
        status="failed",
        inputs=[{"artifact_id": floorplan_parse["artifact_id"], "content_hash": floorplan_parse["content_hash"]}],
        errors=_finding_errors([finding]),
    )
    parse_report = {
        "report_version": 1,
        "parse_run_id": parse_run_id,
        "source_run_id": source_manifest["run_id"],
        "adapter": adapter,
        "outcome": "failed",
        "cli_exit": 3,
        "terminal_finding": {"code": finding.code, "severity": finding.severity, "source_ref": finding.source_ref},
        "limits": limits_snapshot(),
        "metrics": {"walls": 0, "rooms": 0, "openings": 0, "dimensions": 0, "source_entities_scanned": 0},
        "findings": [
            {
                "code": finding.code,
                "severity": finding.severity,
                "tier": finding.tier,
                "source_ref": finding.source_ref,
                "message": finding.message,
            }
        ],
        "overlay": {"overlay_omitted_reason": overlay_omitted_reason},
        "canonical_projection_sha256": None,
    }
    return derived_manifest, derived_quality, floorplan_parse, assumptions, parse_report


_MEDIA_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg"}

# GC-7 (PLAN-002 revision 2, 2026-08-10): §10 now requires the raster overlay
# to embed only the decoded pixel data of the verified source raster,
# stripped of EXIF and every other metadata block (GPS, author, camera
# model, ICC profile, PNG text chunks, ...). Pillow never forwards
# `image.info`/EXIF back out of save() unless a caller explicitly passes
# `exif=`/`pnginfo=`/`icc_profile=`, so re-encoding the already-decoded
# image through Pillow -- without forwarding any of that -- is sufficient
# sanitization. The encoder settings are pinned (not left at whatever
# Pillow's current default happens to be) so two runs over the same source
# bytes produce byte-identical sanitized output.
_SANITIZED_JPEG_QUALITY = 95
_SANITIZED_PNG_COMPRESS_LEVEL = 6


def _sanitize_raster_bytes(image: Image.Image, media_type: str) -> bytes:
    buffer = io.BytesIO()
    if media_type == "image/jpeg":
        image.save(buffer, format="JPEG", quality=_SANITIZED_JPEG_QUALITY)
    else:
        image.save(buffer, format="PNG", compress_level=_SANITIZED_PNG_COMPRESS_LEVEL)
    return buffer.getvalue()


def _source_binding(source_path: Path, raw) -> dict:
    if raw.frame.kind == "raster":
        with Image.open(source_path) as image:
            width, height = image.width, image.height
            # M-5 (spatial review, 2026-08-10): the overlay used to hardcode
            # data:image/png regardless of the verified source format, even
            # though intake.py accepts JPEG floorplans too. Derive the media
            # type from the decoded bytes instead.
            media_type = _MEDIA_TYPES.get(image.format)
            if media_type is None:
                raise FloorplanError("PARSE_SOURCE_UNSUPPORTED", "raster source image format is unsupported")
            sanitized_bytes = _sanitize_raster_bytes(image, media_type)
        return {
            "kind": "raster",
            # GC-7: bind the ORIGINAL source file's hash, never the
            # sanitized copy's -- the sanitized bytes differ from the
            # original whenever metadata was present, and the hash exists
            # to prove which verified input produced this overlay.
            "source_sha256": sha256_file(source_path),
            "image_bytes": sanitized_bytes,
            "media_type": media_type,
            "width_px": width,
            "height_px": height,
            "labels": sorted({item.source_ref for item in raw.unmapped if item.source_ref}),
        }
    # M-4 (spatial review, 2026-08-10): build the "source" primitives from
    # the raw adapter output (the accepted DXF entities), not from the
    # normalized walls' own provenance. The old approach re-projected
    # `source` from `geometry.walls[*].provenance`, so `source` and `walls`
    # were coincident by construction and could never disagree -- AC-14's
    # source-alignment claim was unfalsifiable for DXF. Room and door/window
    # source primitives are also carried through so `#rooms`/`#doors` are no
    # longer always-empty placeholders.
    primitives: list[dict] = [
        {"type": "line", "start": [wall.start[0], wall.start[1]], "end": [wall.end[0], wall.end[1]]}
        for wall in raw.walls
    ]
    primitives.extend(
        {"type": "polyline", "points": [[point[0], point[1]] for point in room.polygon]}
        for room in raw.rooms
    )
    primitives.extend(
        {"type": "line", "start": [opening.span[0][0], opening.span[0][1]], "end": [opening.span[1][0], opening.span[1][1]]}
        for opening in raw.openings
        if opening.span is not None
    )
    return {
        "kind": "dxf",
        "source_sha256": sha256_file(source_path),
        "primitives": primitives,
        "labels": sorted({item.source_ref for item in raw.unmapped if item.source_ref}),
    }


_FAILED_DOMAIN_CODES = {
    "PARSE_TIMEOUT",
    "PARSE_RESOURCE_LIMIT",
    "PARSE_UNITS_MISMATCH",
    "PARSE_UNSUPPORTED_FEATURE",
    "PARSE_SCALE_UNKNOWN",
    "PARSE_EMPTY_GEOMETRY",
    "PARSE_DUPLICATE_ENTITY",
    "PARSE_OPEN_POLYGON",
    "PARSE_SELF_INTERSECTING_POLYGON",
    "PARSE_DEGENERATE_WALL",
    "PARSE_UNKNOWN_WALL_REF",
    "PARSE_AMBIGUOUS_WALL_REF",
    "PARSE_OPENING_OFF_WALL",
    "PARSE_OPENING_WIDTH_EXCEEDS_WALL",
    "PARSE_DIMENSION_INCONSISTENT",
}


def _prevalidate_raw(raw) -> None:
    # C (OpenAI cross-provider rework review, 2026-08-10): this used to raise
    # immediately on the first cardinality problem found, discarding
    # raw.errors entirely -- so a DXF whose only wall-like entity is an
    # unsupported ARC (raw.walls ends up empty) reported only
    # PARSE_EMPTY_GEOMETRY (tier 2), losing the higher-precedence
    # PARSE_UNSUPPORTED_FEATURE (tier 1) already recorded in raw.errors.
    # Only raise for an *actual* cardinality problem (same trigger
    # conditions as before -- healthy geometry with unrelated raw.errors
    # entries must still fall through to the normal
    # normalize()/validate()/sort_findings() path unraised), but when one
    # does apply, pick the highest-precedence (lowest tier) finding from the
    # combination of raw.errors and the cardinality problem(s) themselves,
    # matching section 6's finding precedence instead of whichever
    # cardinality check happened to run first.
    cardinality_findings: list[Finding] = []
    if len(raw.walls) > MAX_WALLS or len(raw.rooms) > MAX_ROOMS or len(raw.openings) > MAX_OPENINGS:
        cardinality_findings.append(make_finding("PARSE_RESOURCE_LIMIT", "raw geometry exceeds configured entity limits"))
    if not raw.walls or not raw.rooms:
        cardinality_findings.append(
            make_finding("PARSE_EMPTY_GEOMETRY", "parsed source did not contain at least one wall and room")
        )
    for room in raw.rooms:
        if len(room.polygon) > MAX_POLYGON_VERTICES:
            cardinality_findings.append(
                make_finding("PARSE_RESOURCE_LIMIT", "raw room exceeds configured vertex limit", source_ref=room.source_ref)
            )
    if cardinality_findings:
        terminal = sort_findings([*raw.errors, *cardinality_findings])[0]
        raise FloorplanError(terminal.code, terminal.message, source_ref=terminal.source_ref)


def _first_terminal_finding(findings: list[Finding]) -> Finding | None:
    return findings[0] if findings else None


def _annotation_input(document: dict | None) -> dict | None:
    if document is None:
        return None
    return {"artifact_id": document["artifact_id"], "content_hash": document["content_hash"]}


def parse_run(
    *,
    runs_root: Path,
    source_run: Path,
    parse_run_id: str,
    annotation: Path | None = None,
) -> ParseRunResult:
    runs_root = Path(runs_root)
    adapter = "annotation" if annotation is not None else "dxf"
    raw = None
    annotation_document: dict | None = None
    # GC-1 (OpenAI cross-provider rework review, 2026-08-10): validate the raw
    # parse_run_id grammar before constructing ANY path from it -- an
    # absolute or drive-relative value previously reached
    # `runs_root / parse_run_id` unchecked, which Path.__truediv__ resolves
    # to the absolute/drive-relative value itself, discarding runs_root
    # entirely. Reject before any filesystem operation.
    if not _is_valid_parse_run_id(parse_run_id):
        diagnostic = _diagnostic(
            parse_run_id=str(parse_run_id),
            source_run_id=None,
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        # A rejected ID cannot be safely joined into any path (that is
        # exactly the defect being closed), so the reported final/staging
        # locations are fixed, inert placeholders rather than anything
        # derived from the rejected value.
        return ParseRunResult(
            cli_exit=2,
            final_run=runs_root / ".rejected-parse-run-id",
            staging_run=runs_root / ".staging" / ".rejected-parse-run-id",
            diagnostic=diagnostic,
        )
    try:
        source_run = resolve_contained_run(runs_root, Path(source_run))
    except ValueError:
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=None,
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        return ParseRunResult(
            cli_exit=2,
            final_run=Path(runs_root) / parse_run_id,
            staging_run=Path(runs_root) / ".staging" / parse_run_id,
            diagnostic=diagnostic,
        )
    final_run = runs_root / parse_run_id
    staging_run = runs_root / ".staging" / parse_run_id
    # GC-1: independently prove containment rather than trust the grammar
    # check alone -- unreachable given _is_valid_parse_run_id's allowlist,
    # but defense in depth per the review's explicit requirement.
    try:
        final_run.relative_to(runs_root)
        staging_run.relative_to(runs_root)
    except ValueError:
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=None,
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        return ParseRunResult(
            cli_exit=2,
            final_run=runs_root / ".rejected-parse-run-id",
            staging_run=runs_root / ".staging" / ".rejected-parse-run-id",
            diagnostic=diagnostic,
        )
    if final_run.exists() or staging_run.exists():
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=None,
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    # GC-3 (OpenAI cross-provider rework review, 2026-08-10): the manifest and
    # quality-report paths were previously read directly
    # (`source_run / "project" / "..."`), so their "project" ancestor and
    # artifact leaves never passed through the containment/reparse-point
    # helper. Route both through resolve_contained_relpath() before reading.
    try:
        manifest_path = resolve_contained_relpath(source_run, "project/project_manifest.json")
        quality_path = resolve_contained_relpath(source_run, "project/input_quality_report.json")
        source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_quality = json.loads(quality_path.read_text(encoding="utf-8"))
    except (ValueError, OSError, json.JSONDecodeError):
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=None,
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    # B (OpenAI cross-provider rework review, 2026-08-10): validate_artifact()
    # raises ValueError/KeyError for a document with no string schema
    # id/version or an unknown schema/version (e.g. a manifest containing
    # "{}") -- that call sat outside any handler, so parse_run() must
    # classify it itself instead of letting it propagate.
    try:
        manifest_or_quality_invalid = bool(validate_artifact(source_manifest) or validate_artifact(source_quality))
    except (ValueError, KeyError):
        manifest_or_quality_invalid = True
    if manifest_or_quality_invalid:
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=source_manifest.get("run_id"),
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    if source_manifest["content_hash"] != compute_content_hash(source_manifest):
        finding = make_finding("PARSE_SOURCE_HASH_MISMATCH", "source project_manifest hash mismatch")
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=source_manifest["run_id"],
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=finding,
        )
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    if source_quality["content_hash"] != compute_content_hash(source_quality):
        finding = make_finding("PARSE_SOURCE_HASH_MISMATCH", "source input_quality_report hash mismatch")
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=source_manifest["run_id"],
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=finding,
        )
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    if source_quality["status"] != "complete" or source_quality["payload"].get("blockers"):
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=source_manifest["run_id"],
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    for item in source_manifest["payload"]["inputs"]:
        try:
            input_path = resolve_contained_relpath(source_run, item["path"])
        except ValueError:
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=None,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
        if sha256_file(input_path) != item["sha256"]:
            finding = make_finding("PARSE_SOURCE_HASH_MISMATCH", "source inventory hash mismatch", source_ref=item["path"])
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=finding,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    floorplan_entry = next(item for item in source_manifest["payload"]["inputs"] if item["kind"] == "floorplan")
    try:
        source_floorplan = resolve_contained_relpath(source_run, floorplan_entry["path"])
    except ValueError:
        diagnostic = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=source_manifest["run_id"],
            adapter=adapter,
            cli_exit=2,
            outcome="operational",
            finding=None,
        )
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    if annotation is not None:
        if not AnnotationSource().accepts(annotation):
            finding = make_finding("PARSE_SOURCE_UNSUPPORTED", "annotation source is unsupported")
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=finding,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
        # B (OpenAI cross-provider rework review, 2026-08-10): Path(annotation).stat()
        # sat outside the main staging try, so --annotation pointing at a
        # nonexistent (or otherwise unreadable) file raised FileNotFoundError
        # out of parse_run() instead of returning the documented CLI 2.
        try:
            annotation_size = Path(annotation).stat().st_size
        except OSError:
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=None,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
        if annotation_size > MAX_ANNOTATION_BYTES:
            finding = make_finding("PARSE_RESOURCE_LIMIT", "annotation exceeds byte limit")
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=finding,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
        try:
            annotation_document = json.loads(Path(annotation).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            annotation_document = None
        # B: validate_artifact() itself can raise ValueError/KeyError (see
        # the manifest/quality handling above) -- classify that the same way
        # instead of letting it propagate out of parse_run().
        try:
            annotation_invalid = annotation_document is None or bool(validate_artifact(annotation_document))
        except (ValueError, KeyError):
            annotation_invalid = True
        if annotation_invalid:
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=None,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
    else:
        if not DxfSource().accepts(source_floorplan):
            finding = make_finding("PARSE_SOURCE_UNSUPPORTED", "floorplan source is unsupported", source_ref=source_floorplan.name)
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=finding,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)
        if source_floorplan.stat().st_size > MAX_DXF_BYTES:
            finding = make_finding("PARSE_RESOURCE_LIMIT", "DXF exceeds byte limit", source_ref=source_floorplan.name)
            diagnostic = _diagnostic(
                parse_run_id=parse_run_id,
                source_run_id=source_manifest["run_id"],
                adapter=adapter,
                cli_exit=2,
                outcome="operational",
                finding=finding,
            )
            return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=diagnostic)

    staging_run.mkdir(parents=True, exist_ok=False)
    try:
        copy_source_inventory(source_run, staging_run, source_manifest)
        copy_artifact(manifest_path, staging_run / "project" / "source-manifest.json")
        copy_artifact(quality_path, staging_run / "project" / "source-quality-report.json")

        if annotation is not None:
            inventory_by_path = {item["path"]: item for item in source_manifest["payload"]["inputs"]}
            raw = AnnotationSource().extract(annotation, source_root=source_run, source_inventory=inventory_by_path)
            copied_annotation = staging_run / "parse" / "annotation.json"
            copy_immutable(annotation, copied_annotation)
            # `annotation_document` was already read and schema-validated
            # during preflight above; reuse it instead of re-reading the
            # file (it is also what GC-4's lineage binding below reads
            # artifact_id/content_hash from).
            source_image = source_run / annotation_document["payload"]["image"]["source_image_ref"]
            source_scale_info = source_manifest["payload"]["scale"]
            source_scale = source_scale_info.get("m_per_px")
            if (
                not source_scale_info.get("known")
                or source_scale is None
                or Decimal(str(raw.frame.unit_scale_m)) != Decimal(str(source_scale))
            ):
                derived_manifest, derived_quality, floorplan_parse, assumptions, parse_report = _failed_scale_artifacts(
                    source_manifest=source_manifest,
                    source_quality=source_quality,
                    parse_run_id=parse_run_id,
                    adapter="annotation",
                    source_unit_scale_m=raw.frame.unit_scale_m,
                    source_height_px=raw.frame.height_px,
                    annotation_input=_annotation_input(annotation_document),
                )
                write_json_exclusive(staging_run / "project" / "project_manifest.json", derived_manifest)
                write_json_exclusive(staging_run / "project" / "input_quality_report.json", derived_quality)
                write_json_exclusive(staging_run / "parse" / "floorplan_parse.json", floorplan_parse)
                write_json_exclusive(staging_run / "parse" / "assumptions.json", assumptions)
                write_json_exclusive(staging_run / "parse" / "parse-report.json", parse_report)
                finalize_run(staging_run, final_run)
                return ParseRunResult(cli_exit=3, final_run=final_run, staging_run=staging_run, diagnostic=parse_report)
        else:
            raw = DxfSource().extract(source_floorplan)
            source_image = source_floorplan
            manifest_units = source_manifest["payload"]["units"]
            if manifest_units == "unknown" or raw.frame.source_units != manifest_units:
                raise FloorplanError("PARSE_UNITS_MISMATCH", "DXF units do not match source manifest units")
        _prevalidate_raw(raw)

        geometry = normalize(raw)
        findings = sort_findings([*raw.errors, *validate(geometry), *raw.unmapped])
        projection = canonical_projection(geometry)
        source_binding = _source_binding(source_image, raw)
        try:
            overlay_bytes = render_overlay(geometry, source_binding)
        except ValueError as exc:
            reason = "source_raster_exceeds_limits" if str(exc) == "source_raster_exceeds_limits" else "overlay_exceeds_max_bytes"
            derived_manifest, derived_quality, floorplan_parse, assumptions, parse_report = _failed_scale_artifacts(
                source_manifest=source_manifest,
                source_quality=source_quality,
                parse_run_id=parse_run_id,
                adapter="annotation" if annotation is not None else "dxf",
                finding=make_finding("PARSE_RESOURCE_LIMIT", "overlay bytes exceed MAX_OVERLAY_BYTES"),
                overlay_omitted_reason=reason,
                source_unit_scale_m=raw.frame.unit_scale_m if raw.frame.kind == "raster" else None,
                source_height_px=raw.frame.height_px if raw.frame.kind == "raster" else None,
                annotation_input=_annotation_input(annotation_document),
            )
            write_json_exclusive(staging_run / "project" / "project_manifest.json", derived_manifest)
            write_json_exclusive(staging_run / "project" / "input_quality_report.json", derived_quality)
            write_json_exclusive(staging_run / "parse" / "floorplan_parse.json", floorplan_parse)
            write_json_exclusive(staging_run / "parse" / "assumptions.json", assumptions)
            write_json_exclusive(staging_run / "parse" / "parse-report.json", parse_report)
            finalize_run(staging_run, final_run)
            return ParseRunResult(cli_exit=3, final_run=final_run, staging_run=staging_run, diagnostic=parse_report)
        if len(overlay_bytes) > MAX_OVERLAY_BYTES:
            derived_manifest, derived_quality, floorplan_parse, assumptions, parse_report = _failed_scale_artifacts(
                source_manifest=source_manifest,
                source_quality=source_quality,
                parse_run_id=parse_run_id,
                adapter="annotation" if annotation is not None else "dxf",
                finding=make_finding("PARSE_RESOURCE_LIMIT", "overlay bytes exceed MAX_OVERLAY_BYTES"),
                overlay_omitted_reason="overlay_exceeds_max_bytes",
                source_unit_scale_m=raw.frame.unit_scale_m if raw.frame.kind == "raster" else None,
                source_height_px=raw.frame.height_px if raw.frame.kind == "raster" else None,
                annotation_input=_annotation_input(annotation_document),
            )
            write_json_exclusive(staging_run / "project" / "project_manifest.json", derived_manifest)
            write_json_exclusive(staging_run / "project" / "input_quality_report.json", derived_quality)
            write_json_exclusive(staging_run / "parse" / "floorplan_parse.json", floorplan_parse)
            write_json_exclusive(staging_run / "parse" / "assumptions.json", assumptions)
            write_json_exclusive(staging_run / "parse" / "parse-report.json", parse_report)
            finalize_run(staging_run, final_run)
            return ParseRunResult(cli_exit=3, final_run=final_run, staging_run=staging_run, diagnostic=parse_report)
        overlay_hash = "sha256:" + hashlib.sha256(overlay_bytes).hexdigest()
        projection_hash = _projection_hash(projection)

        has_errors = any(finding.severity == "error" for finding in findings)
        has_warnings = any(finding.severity == "warn" for finding in findings)
        cli_exit = 3 if has_errors else 1 if has_warnings else 0
        status = "failed" if has_errors else "partial" if has_warnings else "complete"

        derived_manifest = _artifact(
            "project_manifest",
            "1.0.0",
            {
                **source_manifest["payload"],
                "contracts_bundle_version": "1.1.0",
            },
            project_id=source_manifest["project_id"],
            run_id=parse_run_id,
            status="complete",
            inputs=[
                {"artifact_id": source_manifest["artifact_id"], "content_hash": source_manifest["content_hash"]},
                {"artifact_id": source_quality["artifact_id"], "content_hash": source_quality["content_hash"]},
            ],
        )
        derived_quality = _artifact(
            "input_quality_report",
            "1.0.0",
            source_quality["payload"],
            project_id=source_quality["project_id"],
            run_id=parse_run_id,
            status="complete",
            inputs=[{"artifact_id": source_quality["artifact_id"], "content_hash": source_quality["content_hash"]}],
        )
        floorplan_parse = _artifact(
            "floorplan_parse",
            "1.1.0",
            {
                "units": "m",
                "scale_m_per_px": geometry.normalization["scale_m_per_px"],
                "normalization": geometry.normalization,
                "overlay": {"path": "parse/overlay.svg", "sha256": overlay_hash},
                "rooms": [
                    {
                        "id": room.id,
                        "polygon": [list(point) for point in room.polygon],
                        "confidence": room.confidence,
                        "provenance": room.provenance,
                    }
                    for room in geometry.rooms
                ],
                "walls": [
                    {
                        "id": wall.id,
                        "start": list(wall.start),
                        "end": list(wall.end),
                        "confidence": wall.confidence,
                        "provenance": wall.provenance,
                    }
                    for wall in geometry.walls
                ],
                "openings": [
                    {
                        "id": opening.id,
                        "type": opening.type,
                        "wall_id": opening.wall_id,
                        "center": list(opening.center),
                        "width_m": opening.width_m,
                        "confidence": opening.confidence,
                        "provenance": opening.provenance,
                    }
                    for opening in geometry.openings
                ],
            },
            project_id=source_manifest["project_id"],
            run_id=parse_run_id,
            status=status,
            # GC-4 (OpenAI cross-provider rework review, 2026-08-10): bind
            # the annotation artifact ID/hash into the parse outputs too, so
            # the finalized artifact records which annotation produced it
            # (D-013 immutable lineage).
            inputs=[
                {"artifact_id": derived_manifest["artifact_id"], "content_hash": derived_manifest["content_hash"]},
                {"artifact_id": derived_quality["artifact_id"], "content_hash": derived_quality["content_hash"]},
                *([_annotation_input(annotation_document)] if annotation_document is not None else []),
            ],
            errors=_finding_errors(findings),
        )
        assumptions = _artifact(
            "assumptions",
            "1.0.0",
            {"stage": "parsing", "entries": []},
            project_id=source_manifest["project_id"],
            run_id=parse_run_id,
            status=status,
            inputs=[{"artifact_id": floorplan_parse["artifact_id"], "content_hash": floorplan_parse["content_hash"]}],
            errors=_finding_errors(findings),
        )
        parse_report = {
            "report_version": 1,
            "parse_run_id": parse_run_id,
            "source_run_id": source_manifest["run_id"],
            "adapter": "annotation" if annotation is not None else "dxf",
            "outcome": "failed" if has_errors else "partial" if has_warnings else "complete",
            "cli_exit": cli_exit,
            "terminal_finding": (
                {
                    "code": _first_terminal_finding(findings).code,
                    "severity": _first_terminal_finding(findings).severity,
                    "source_ref": _first_terminal_finding(findings).source_ref,
                }
                if _first_terminal_finding(findings) is not None
                else None
            ),
            "limits": limits_snapshot(),
            "metrics": {
                "walls": len(geometry.walls),
                "rooms": len(geometry.rooms),
                "openings": len(geometry.openings),
                "dimensions": len(geometry.dimensions_m),
                "source_entities_scanned": raw.scanned_entities,
            },
            "findings": [
                {
                    "code": finding.code,
                    "severity": finding.severity,
                    "tier": finding.tier,
                    "source_ref": finding.source_ref,
                    "message": finding.message,
                }
                for finding in findings
            ],
            "overlay": {"path": "parse/overlay.svg", "sha256": overlay_hash},
            "canonical_projection_sha256": projection_hash,
        }

        # E (OpenAI cross-provider rework review, 2026-08-10): unlike every
        # other staged output (write_json_exclusive uses O_EXCL "x" mode),
        # this used to be a plain write_bytes() -- neither exclusive nor
        # no-follow. A pre-planted file/symlink at the predictable staging
        # path would be silently followed/truncated. Use the same
        # exclusive-create discipline as the JSON writers.
        #
        # Written FIRST, before the envelope JSON artifacts below: if this
        # exclusive write fails, the `except Exception` handler further down
        # writes parse-report.json itself to report the operational failure.
        # That handler assumes parse-report.json does not already exist yet
        # -- true only if the overlay write (the one write in this block
        # that can newly fail this way) happens before, not after, the
        # envelope writes.
        overlay_path = staging_run / "parse" / "overlay.svg"
        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        with overlay_path.open("xb") as stream:
            stream.write(overlay_bytes)
        write_json_exclusive(staging_run / "project" / "project_manifest.json", derived_manifest)
        write_json_exclusive(staging_run / "project" / "input_quality_report.json", derived_quality)
        write_json_exclusive(staging_run / "parse" / "floorplan_parse.json", floorplan_parse)
        write_json_exclusive(staging_run / "parse" / "assumptions.json", assumptions)
        write_json_exclusive(staging_run / "parse" / "parse-report.json", parse_report)
        finalize_run(staging_run, final_run)
        return ParseRunResult(cli_exit=cli_exit, final_run=final_run, staging_run=staging_run, diagnostic=parse_report)
    except FloorplanError as exc:
        if exc.finding.code in _FAILED_DOMAIN_CODES:
            derived_manifest, derived_quality, floorplan_parse, assumptions, parse_report = _failed_scale_artifacts(
                source_manifest=source_manifest,
                source_quality=source_quality,
                parse_run_id=parse_run_id,
                adapter="annotation" if annotation is not None else "dxf",
                finding=exc.finding,
                source_unit_scale_m=raw.frame.unit_scale_m if raw is not None and raw.frame.kind == "raster" else None,
                source_height_px=raw.frame.height_px if raw is not None and raw.frame.kind == "raster" else None,
                annotation_input=_annotation_input(annotation_document),
            )
            write_json_exclusive(staging_run / "project" / "project_manifest.json", derived_manifest)
            write_json_exclusive(staging_run / "project" / "input_quality_report.json", derived_quality)
            write_json_exclusive(staging_run / "parse" / "floorplan_parse.json", floorplan_parse)
            write_json_exclusive(staging_run / "parse" / "assumptions.json", assumptions)
            write_json_exclusive(staging_run / "parse" / "parse-report.json", parse_report)
            finalize_run(staging_run, final_run)
            return ParseRunResult(cli_exit=3, final_run=final_run, staging_run=staging_run, diagnostic=parse_report)
        parse_report = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=source_manifest["run_id"],
            adapter=adapter,
            cli_exit=2,
            outcome="operational_failure",
            finding=exc.finding,
        )
        write_json_exclusive(staging_run / "parse" / "parse-report.json", parse_report)
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=parse_report)
    except Exception:
        parse_report = _diagnostic(
            parse_run_id=parse_run_id,
            source_run_id=source_manifest["run_id"],
            adapter=adapter,
            cli_exit=2,
            outcome="operational_failure",
            finding=None,
        )
        write_json_exclusive(staging_run / "parse" / "parse-report.json", parse_report)
        return ParseRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=parse_report)
