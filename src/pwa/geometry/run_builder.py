"""PLAN-003 geometry-run orchestration (immutable derived run).

Consumes ONE immutable floorplan_parse artifact from a finalized PLAN-002
parse run and emits a schema-valid scene_geometry 1.0.0 white model plus
assumptions, topology+dimension report, geometry run report, and a top-down
overlay. Mirrors PLAN-002's immutable-derived-run discipline: the source parse
is byte-copied (never mutated), outputs are staged then atomically finalized,
and every destination write is containment-checked.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from os import replace as atomic_replace
from pathlib import Path

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import write_json_exclusive
from pwa.floorplan.runs import (
    create_contained_directory,
    resolve_contained_relpath,
    validate_contained_destination,
    write_bytes_contained,
)
from pwa.geometry.compiler import assumption_entries, compile_geometry
from pwa.geometry.config import limits_snapshot
from pwa.geometry.findings import GeometryError
from pwa.geometry.load import load_parse_geometry
from pwa.geometry.overlay import render_png, render_svg
from pwa.geometry.topology import validate_topology, validation_report

_GEOM_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _is_valid_geom_run_id(value: object) -> bool:
    return isinstance(value, str) and bool(_GEOM_RUN_ID_RE.match(value))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class GeometryRunResult:
    cli_exit: int
    final_run: Path
    staging_run: Path
    diagnostic: dict | None = None


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
            "agent": "plan003-geometry-compiler",
            "provider": "local",
            "model": "deterministic-python",
            "effort": "MAX",
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


def _finding_errors(findings) -> list[dict]:
    return [{"code": finding.code, "message": finding.message} for finding in findings]


def _write_staged_json(path: Path, document: dict) -> None:
    write_json_exclusive(path, document, create_parents=False)


def _scene_geometry_payload(compiled) -> dict:
    return {
        "units": "m",
        "up_axis": "z",
        "default_ceiling_height_m": compiled.default_ceiling_height_m,
        "rooms": [
            {
                "id": room.id,
                "polygon": [list(point) for point in room.polygon],
                "floor_z": room.floor_z,
                "ceiling_z": room.ceiling_z,
            }
            for room in compiled.rooms
        ],
        "walls": [
            {
                "id": wall.id,
                "start": list(wall.start),
                "end": list(wall.end),
                "height_m": wall.height_m,
                "thickness_m": wall.thickness_m,
            }
            for wall in compiled.walls
        ],
        "openings": [
            {
                "id": opening.id,
                "type": opening.type,
                "wall_id": opening.wall_id,
                "center": list(opening.center),
                "width_m": opening.width_m,
                "height_m": opening.height_m,
                "sill_m": opening.sill_m,
            }
            for opening in compiled.openings
        ],
    }


def build_geometry_run(
    *,
    runs_root: Path,
    source_parse: Path,
    geo_run_id: str,
    export_blender: bool = False,
) -> GeometryRunResult:
    runs_root = Path(runs_root)
    if not _is_valid_geom_run_id(geo_run_id):
        diagnostic = {
            "report_version": 1,
            "geo_run_id": str(geo_run_id),
            "outcome": "operational",
            "cli_exit": 2,
            "reason": "invalid_geometry_run_id",
        }
        return GeometryRunResult(
            cli_exit=2,
            final_run=runs_root / ".rejected-geo-run-id",
            staging_run=runs_root / ".staging" / ".rejected-geo-run-id",
            diagnostic=diagnostic,
        )

    try:
        source_parse_resolved = resolve_contained_relpath(runs_root, source_parse)
    except (ValueError, OSError):
        return GeometryRunResult(
            cli_exit=2,
            final_run=runs_root / geo_run_id,
            staging_run=runs_root / ".staging" / geo_run_id,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_parse_unresolvable"},
        )

    final_run = runs_root / geo_run_id
    staging_run = runs_root / ".staging" / geo_run_id
    try:
        final_run.relative_to(runs_root)
        staging_run.relative_to(runs_root)
        validate_contained_destination(runs_root, geo_run_id)
        validate_contained_destination(runs_root, Path(".staging") / geo_run_id)
    except (ValueError, OSError):
        return GeometryRunResult(
            cli_exit=2,
            final_run=runs_root / ".rejected-geo-run-id",
            staging_run=runs_root / ".staging" / ".rejected-geo-run-id",
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "destination_invalid"},
        )

    try:
        if final_run.exists() or staging_run.exists():
            return GeometryRunResult(
                cli_exit=2,
                final_run=final_run,
                staging_run=staging_run,
                diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "destination_exists"},
            )
    except OSError:
        return GeometryRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "destination_unreachable"},
        )

    # Load + verify the source parse document.
    try:
        parse_bytes = source_parse_resolved.read_bytes()
        source_parse_file_hash = "sha256:" + hashlib.sha256(parse_bytes).hexdigest()
        source_parse_document = json.loads(parse_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return GeometryRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_parse_unreadable"},
        )

    if not isinstance(source_parse_document, dict):
        return GeometryRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_parse_not_object"},
        )
    try:
        invalid = bool(validate_artifact(source_parse_document))
    except (ValueError, KeyError):
        invalid = True
    if invalid:
        return GeometryRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_parse_invalid"},
        )
    if source_parse_document.get("schema_id") != "floorplan_parse":
        return GeometryRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_not_floorplan_parse"},
        )
    if source_parse_document["content_hash"] != compute_content_hash(source_parse_document):
        return GeometryRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_parse_hash_mismatch"},
        )

    project_id = source_parse_document["project_id"]
    source_input = {
        "artifact_id": source_parse_document["artifact_id"],
        "content_hash": source_parse_document["content_hash"],
    }

    try:
        staging_run = create_contained_directory(runs_root, Path(".staging") / geo_run_id)
        create_contained_directory(staging_run, "project")
        create_contained_directory(staging_run, "geometry")
    except (OSError, ValueError):
        return GeometryRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "geo_run_id": geo_run_id, "outcome": "operational", "cli_exit": 2, "reason": "staging_create_failed"},
        )

    try:
        # Byte-copy the consumed parse artifact (immutable input binding).
        write_bytes_contained(staging_run, "project/source-parse.json", parse_bytes, create_parents=False)

        geometry = load_parse_geometry(source_parse_document["payload"])
        compiled = compile_geometry(geometry)
        findings = validate_topology(compiled)
        has_errors = any(finding.severity == "error" for finding in findings)
        has_warnings = any(finding.severity == "warn" for finding in findings)
        status = "failed" if has_errors else "partial" if has_warnings else "complete"
        cli_exit = 3 if has_errors else 1 if has_warnings else 0

        scene_geometry = _artifact(
            "scene_geometry",
            "1.0.0",
            _scene_geometry_payload(compiled),
            project_id=project_id,
            run_id=geo_run_id,
            status=status,
            inputs=[source_input],
            errors=_finding_errors(findings),
        )
        assumptions = _artifact(
            "assumptions",
            "1.0.0",
            {"stage": "geometry", "entries": assumption_entries(geometry)},
            project_id=project_id,
            run_id=geo_run_id,
            status=status,
            inputs=[{"artifact_id": scene_geometry["artifact_id"], "content_hash": scene_geometry["content_hash"]}],
            errors=_finding_errors(findings),
        )
        topology_report = validation_report(compiled, findings)
        geometry_report = {
            "report_version": 1,
            "geo_run_id": geo_run_id,
            "source_artifact_id": source_parse_document["artifact_id"],
            "outcome": "failed" if has_errors else "partial" if has_warnings else "complete",
            "cli_exit": cli_exit,
            "limits": limits_snapshot(),
            "metrics": {
                "walls": len(compiled.walls),
                "rooms": len(compiled.rooms),
                "openings": len(compiled.openings),
                "openings_doors": sum(1 for o in compiled.openings if o.type == "door"),
                "openings_windows": sum(1 for o in compiled.openings if o.type == "window"),
            },
            "findings": [
                {"code": f.code, "severity": f.severity, "tier": f.tier, "source_ref": f.source_ref, "message": f.message}
                for f in findings
            ],
            "export": {"blender_requested": export_blender, "blender_completed": False},
        }

        overlay_svg = render_svg(compiled)
        overlay_png = render_png(compiled)

        # Write overlay + JSON artifacts (exclusive, containment-checked).
        write_bytes_contained(staging_run, "geometry/overlay-topdown.svg", overlay_svg, create_parents=False)
        write_bytes_contained(staging_run, "geometry/overlay-topdown.png", overlay_png, create_parents=False)
        _write_staged_json(staging_run / "geometry" / "scene_geometry.json", scene_geometry)
        _write_staged_json(staging_run / "geometry" / "assumptions.json", assumptions)
        _write_staged_json(staging_run / "geometry" / "topology-report.json", topology_report)
        _write_staged_json(staging_run / "geometry" / "geometry-report.json", geometry_report)

        # Blender export is default-off in PLAN-003 (best-effort evidence only;
        # a missing/failed Blender run never fails the geometry gate).
        if export_blender:
            try:
                from pwa.geometry.blender_stub import blend_completed

                if blend_completed(staging_run, compiled):
                    geometry_report["export"]["blender_completed"] = True
                    _write_staged_json(staging_run / "geometry" / "geometry-report.json", geometry_report)
            except Exception:
                pass

        finalize_geometry_run(staging_run, final_run, _manifest_for_finalize(source_parse_file_hash))
        return GeometryRunResult(cli_exit=cli_exit, final_run=final_run, staging_run=staging_run, diagnostic=geometry_report)
    except GeometryError as exc:
        return _staged_operational_result(
            geo_run_id=geo_run_id,
            final_run=final_run,
            staging_run=staging_run,
            finding=exc.finding,
        )
    except Exception:
        return _staged_operational_result(
            geo_run_id=geo_run_id,
            final_run=final_run,
            staging_run=staging_run,
            finding=None,
        )


def _manifest_for_finalize(source_parse_file_hash: str) -> dict:
    """A minimal manifest document used only to drive geometry finalization's
    inventory verification. It is not written to disk as an output artifact."""
    return {
        "payload": {
            "inputs": [
                {"path": "project/source-parse.json", "sha256": source_parse_file_hash}
            ]
        }
    }


def _verify_geometry_run(run_root: Path, manifest: dict) -> None:
    """Verify a staged/finalized geometry run has complete, consistent, valid
    envelopes and a source-parse byte-copy matching its declared file hash."""
    from pwa.files import sha256_file
    from pwa.floorplan.runs import _load_json_document, _verify_envelope

    for item in manifest["payload"]["inputs"]:
        declared_path = resolve_contained_relpath(run_root, item["path"])
        if sha256_file(declared_path) != item["sha256"]:
            raise ValueError("finalized inventory hash mismatch")
    for relpath in (
        "geometry/scene_geometry.json",
        "geometry/assumptions.json",
        "geometry/topology-report.json",
        "geometry/geometry-report.json",
    ):
        document = _load_json_document(run_root, relpath)
        # topology/geometry reports are raw evidence, not envelopes; only the
        # schema-id'd artifacts carry an envelope.
        if relpath.endswith("scene_geometry.json") or relpath.endswith("assumptions.json"):
            _verify_envelope(document, "finalized envelope content hash mismatch")
    # Overlays must exist and be non-empty.
    for relpath in ("geometry/overlay-topdown.svg", "geometry/overlay-topdown.png"):
        path = resolve_contained_relpath(run_root, relpath)
        if path.stat().st_size == 0:
            raise ValueError("finalized overlay is empty")


def finalize_geometry_run(staging_run: Path, final_run: Path, manifest: dict) -> None:
    """Atomically promote a staged geometry run to finalized.

    Mirrors PLAN-002's finalize_run() but with the geometry run layout; the
    shared finalize_run() is PLAN-002-specific (hardcodes the parse/ layout).
    """
    import os

    runs_root = final_run.parent
    staging_relative = staging_run.relative_to(runs_root)
    resolve_contained_relpath(runs_root, staging_relative.as_posix())
    validate_contained_destination(runs_root, final_run.name)
    if final_run.exists() or final_run.is_symlink():
        raise FileExistsError(str(final_run))
    _verify_geometry_run(staging_run, manifest)
    os.replace(staging_run, final_run)
    try:
        _verify_geometry_run(final_run, manifest)
    except (OSError, ValueError):
        try:
            os.replace(final_run, staging_run)
        except OSError:
            pass
        raise


def _staged_operational_result(
    *,
    geo_run_id: str,
    final_run: Path,
    staging_run: Path,
    finding,
) -> GeometryRunResult:
    report = {
        "report_version": 1,
        "geo_run_id": geo_run_id,
        "outcome": "operational",
        "cli_exit": 2,
        "terminal_finding": (
            {"code": finding.code, "severity": finding.severity, "source_ref": finding.source_ref}
            if finding is not None
            else None
        ),
    }
    try:
        report_path = staging_run / "geometry" / "geometry-report.json"
        if staging_run.is_dir() and staging_run.joinpath("geometry").is_dir():
            if report_path.exists():
                replacement = report_path.with_name("geometry-report.operational-failure.tmp")
                _write_staged_json(replacement, report)
                atomic_replace(replacement, report_path)
            else:
                _write_staged_json(report_path, report)
    except (OSError, ValueError):
        pass
    return GeometryRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=report)
