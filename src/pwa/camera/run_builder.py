"""PLAN-004 camera-run orchestration (immutable derived run).

Consumes ONE immutable scene_geometry 1.0.0 artifact from a finalized PLAN-003
geometry run and emits a schema-valid camera_plan 1.0.0 plus per-viewpoint
camera-to-world extrinsics, assumptions, coverage/collision report, camera run
report, a draft map.json, and a top-down coverage overlay. Mirrors PLAN-003's
immutable-derived-run discipline: the source geometry is byte-copied (never
mutated), outputs are staged then atomically finalized, and every destination
write is containment-checked.

Run layout (ADR-0008):

    runs/<cam-run-id>/
      project/source-geometry.json
      camera/camera_plan.json
      camera/assumptions.json
      camera/coverage-report.json
      camera/camera-report.json
      camera/map.json
      camera/extrinsics/<viewpoint-id>.txt
      camera/overlay-cameras.svg
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from os import replace as atomic_replace
from pathlib import Path

from pwa.camera.adjacency import build_adjacency
from pwa.camera.config import (
    CAMERA_HEIGHT_M,
    CAMERA_HEIGHT_MAX_M,
    CAMERA_HEIGHT_MIN_M,
    DEFAULT_YAW_RAD,
    MAX_VIEWS_PER_LRM_BATCH,
    OPENING_CLEARANCE_M,
    RESOLUTION_HEIGHT,
    RESOLUTION_WIDTH,
    WALL_CLEARANCE_M,
    limits_snapshot,
)
from pwa.camera.extrinsics import build_and_validate, format_extrinsics
from pwa.camera.findings import CameraError, Finding, sort_findings
from pwa.camera.load import load_scene_geometry
from pwa.camera.overlay import render_overlay_svg
from pwa.camera.placement import place_viewpoints
from pwa.camera.report import camera_report, coverage_report
from pwa.camera.types import SceneGeometry, Viewpoint
from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import write_json_exclusive
from pwa.floorplan.runs import (
    create_contained_directory,
    resolve_contained_relpath,
    validate_contained_destination,
    write_bytes_contained,
)

_CAM_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _is_valid_cam_run_id(value: object) -> bool:
    return isinstance(value, str) and bool(_CAM_RUN_ID_RE.match(value))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class CameraRunResult:
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
            "agent": "plan004-camera-planner",
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


def _finding_errors(findings: list[Finding]) -> list[dict]:
    return [{"code": f.code, "message": f.message} for f in findings]


def _write_staged_json(path: Path, document: dict) -> None:
    write_json_exclusive(path, document, create_parents=False)


def _camera_plan_payload(
    geometry: SceneGeometry,
    viewpoints: tuple[Viewpoint, ...],
    edges: list[list[str]],
    start_viewpoint: str | None,
) -> dict:
    return {
        "resolution": {"width": RESOLUTION_WIDTH, "height": RESOLUTION_HEIGHT},
        "camera_height_m": CAMERA_HEIGHT_M,
        "viewpoints": [
            {
                "id": vp.id,
                "position": [vp.position[0], vp.position[1], vp.camera_height_m],
                "yaw_deg": math.degrees(vp.yaw_rad),
                "room_id": vp.room_id,
            }
            for vp in viewpoints
        ],
        "edges": edges,
        "start_viewpoint": start_viewpoint,
        "max_views_per_lrm_batch": MAX_VIEWS_PER_LRM_BATCH,
    }


def _map_draft(edges: list[list[str]], start_viewpoint: str | None) -> dict:
    adjacency: dict[str, list[str]] = {}
    if start_viewpoint is not None:
        adjacency.setdefault(start_viewpoint, [])
    for a, b in edges:
        adjacency.setdefault(a, [])
        adjacency.setdefault(b, [])
        if b not in adjacency[a]:
            adjacency[a].append(b)
        if a not in adjacency[b]:
            adjacency[b].append(a)
    return adjacency


def _assumption_entries() -> list[dict]:
    def add(key: str, value: str, reason: str) -> dict:
        return {"key": key, "value": value, "reason": reason, "source": "default", "requires_human_ack": False}

    return [
        add("camera.height_m", f"{CAMERA_HEIGHT_M:.2f}", "camera height default (matches camera_plan schema default and golden fixture)"),
        add("camera.wall_clearance_m", f"{WALL_CLEARANCE_M:.2f}", "wall clearance default (lens out of wall body + usable frustum depth)"),
        add("camera.opening_clearance_m", f"{OPENING_CLEARANCE_M:.2f}", "opening clearance default (viewpoints never block or sit inside an opening)"),
        add("camera.yaw_rad", f"{DEFAULT_YAW_RAD:.1f}", "default yaw 0 (no per-room override in Part 1)"),
        add("camera.resolution", f"{RESOLUTION_WIDTH}x{RESOLUTION_HEIGHT}", "default render resolution (width == 2 * height)"),
        add("camera.max_views_per_lrm_batch", f"{MAX_VIEWS_PER_LRM_BATCH}", "mirrors verified PanoWorld viewpoint_max_view default 8"),
    ]


def build_camera_run(
    *,
    runs_root: Path,
    source_geometry: Path,
    cam_run_id: str,
) -> CameraRunResult:
    runs_root = Path(runs_root)
    if not _is_valid_cam_run_id(cam_run_id):
        return CameraRunResult(
            cli_exit=2,
            final_run=runs_root / ".rejected-cam-run-id",
            staging_run=runs_root / ".staging" / ".rejected-cam-run-id",
            diagnostic={"report_version": 1, "cam_run_id": str(cam_run_id), "outcome": "operational", "cli_exit": 2, "reason": "invalid_camera_run_id"},
        )

    try:
        source_geometry_resolved = resolve_contained_relpath(runs_root, source_geometry)
    except (ValueError, OSError):
        return CameraRunResult(
            cli_exit=2,
            final_run=runs_root / cam_run_id,
            staging_run=runs_root / ".staging" / cam_run_id,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_geometry_unresolvable"},
        )

    final_run = runs_root / cam_run_id
    staging_run = runs_root / ".staging" / cam_run_id
    try:
        final_run.relative_to(runs_root)
        staging_run.relative_to(runs_root)
        validate_contained_destination(runs_root, cam_run_id)
        validate_contained_destination(runs_root, Path(".staging") / cam_run_id)
    except (ValueError, OSError):
        return CameraRunResult(
            cli_exit=2,
            final_run=runs_root / ".rejected-cam-run-id",
            staging_run=runs_root / ".staging" / ".rejected-cam-run-id",
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "destination_invalid"},
        )

    try:
        if final_run.exists() or staging_run.exists():
            return CameraRunResult(
                cli_exit=2,
                final_run=final_run,
                staging_run=staging_run,
                diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "destination_exists"},
            )
    except OSError:
        return CameraRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "destination_unreachable"},
        )

    # Load + verify the source geometry document.
    try:
        geo_bytes = source_geometry_resolved.read_bytes()
        source_geo_file_hash = "sha256:" + hashlib.sha256(geo_bytes).hexdigest()
        source_geo_document = json.loads(geo_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return CameraRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_geometry_unreadable"},
        )

    if not isinstance(source_geo_document, dict):
        return CameraRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_geometry_not_object"},
        )
    try:
        invalid = bool(validate_artifact(source_geo_document))
    except (ValueError, KeyError):
        invalid = True
    if invalid:
        return CameraRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_geometry_invalid"},
        )
    if source_geo_document.get("schema_id") != "scene_geometry":
        return CameraRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_not_scene_geometry"},
        )
    if source_geo_document["content_hash"] != compute_content_hash(source_geo_document):
        return CameraRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "source_geometry_hash_mismatch"},
        )

    project_id = source_geo_document["project_id"]
    source_input = {
        "artifact_id": source_geo_document["artifact_id"],
        "content_hash": source_geo_document["content_hash"],
    }

    try:
        staging_run = create_contained_directory(runs_root, Path(".staging") / cam_run_id)
        create_contained_directory(staging_run, "project")
        create_contained_directory(staging_run, "camera")
        create_contained_directory(staging_run, Path("camera") / "extrinsics")
    except (OSError, ValueError):
        return CameraRunResult(
            cli_exit=2,
            final_run=final_run,
            staging_run=staging_run,
            diagnostic={"report_version": 1, "cam_run_id": cam_run_id, "outcome": "operational", "cli_exit": 2, "reason": "staging_create_failed"},
        )

    try:
        # Byte-copy the consumed geometry artifact (immutable input binding).
        write_bytes_contained(staging_run, "project/source-geometry.json", geo_bytes, create_parents=False)

        geometry = load_scene_geometry(source_geo_document["payload"])

        # Camera height range guard (CAM_CAMERA_HEIGHT_OUT_OF_RANGE).
        if not (CAMERA_HEIGHT_MIN_M <= CAMERA_HEIGHT_M <= CAMERA_HEIGHT_MAX_M) or not math.isfinite(CAMERA_HEIGHT_M):
            raise CameraError("CAM_CAMERA_HEIGHT_OUT_OF_RANGE", "camera height is outside the allowed range", source_ref=None)

        # Place viewpoints + coverage/collision findings.
        viewpoints, placement_findings = place_viewpoints(geometry, camera_height_m=CAMERA_HEIGHT_M)
        findings: list[Finding] = list(placement_findings)

        # Build and validate extrinsics per viewpoint.
        for vp in viewpoints:
            matrix = build_and_validate(vp)
            text = format_extrinsics(matrix).encode("utf-8")
            write_bytes_contained(staging_run, f"camera/extrinsics/{vp.id}.txt", text, create_parents=False)

        # Adjacency graph + map draft.
        edges, start_viewpoint, adjacency_findings = build_adjacency(geometry, viewpoints)
        findings.extend(adjacency_findings)

        findings = sort_findings(findings)
        has_errors = any(f.severity == "error" for f in findings)
        # The G3 gate is coverage + no-collision + extrinsics (all error tier).
        # CAM_MAP_ADJACENCY_UNRESOLVED is a tier-4 warn (an exterior door, or a
        # door that does not connect two covered rooms) — informational, not a
        # gate failure, so it does not downgrade the run to "partial".
        status = "failed" if has_errors else "complete"
        cli_exit = 3 if has_errors else 0

        camera_plan = _artifact(
            "camera_plan",
            "1.0.0",
            _camera_plan_payload(geometry, viewpoints, edges, start_viewpoint),
            project_id=project_id,
            run_id=cam_run_id,
            status=status,
            inputs=[source_input],
            errors=_finding_errors(findings),
        )
        assumptions = _artifact(
            "assumptions",
            "1.0.0",
            {"stage": "camera", "entries": _assumption_entries()},
            project_id=project_id,
            run_id=cam_run_id,
            status=status,
            inputs=[{"artifact_id": camera_plan["artifact_id"], "content_hash": camera_plan["content_hash"]}],
            errors=_finding_errors(findings),
        )
        coverage = coverage_report(geometry, viewpoints, edges, start_viewpoint, findings)
        report = camera_report(
            cam_run_id=cam_run_id,
            source_artifact_id=source_geo_document["artifact_id"],
            outcome=status,
            cli_exit=cli_exit,
            limits=limits_snapshot(),
            metrics={
                "rooms": len(geometry.rooms),
                "viewpoints": len(viewpoints),
                "edges": len(edges),
                "openings": len(geometry.openings),
                "openings_doors": sum(1 for o in geometry.openings if o.type == "door"),
                "openings_windows": sum(1 for o in geometry.openings if o.type == "window"),
            },
            findings=findings,
        )
        map_draft = _map_draft(edges, start_viewpoint)

        overlay_svg = render_overlay_svg(geometry, viewpoints)

        write_bytes_contained(staging_run, "camera/overlay-cameras.svg", overlay_svg, create_parents=False)
        _write_staged_json(staging_run / "camera" / "camera_plan.json", camera_plan)
        _write_staged_json(staging_run / "camera" / "assumptions.json", assumptions)
        _write_staged_json(staging_run / "camera" / "coverage-report.json", coverage)
        _write_staged_json(staging_run / "camera" / "camera-report.json", report)
        _write_staged_json(staging_run / "camera" / "map.json", map_draft)

        finalize_camera_run(staging_run, final_run, _manifest_for_finalize(source_geo_file_hash))
        return CameraRunResult(cli_exit=cli_exit, final_run=final_run, staging_run=staging_run, diagnostic=report)
    except CameraError as exc:
        return _staged_operational_result(
            cam_run_id=cam_run_id,
            final_run=final_run,
            staging_run=staging_run,
            finding=exc.finding,
        )
    except Exception:
        return _staged_operational_result(
            cam_run_id=cam_run_id,
            final_run=final_run,
            staging_run=staging_run,
            finding=None,
        )


def _manifest_for_finalize(source_geo_file_hash: str) -> dict:
    return {
        "payload": {
            "inputs": [
                {"path": "project/source-geometry.json", "sha256": source_geo_file_hash}
            ]
        }
    }


def _verify_camera_run(run_root: Path, manifest: dict) -> None:
    from pwa.files import sha256_file
    from pwa.floorplan.runs import _load_json_document, _verify_envelope

    for item in manifest["payload"]["inputs"]:
        declared_path = resolve_contained_relpath(run_root, item["path"])
        if sha256_file(declared_path) != item["sha256"]:
            raise ValueError("finalized inventory hash mismatch")
    for relpath in ("camera/camera_plan.json", "camera/assumptions.json"):
        document = _load_json_document(run_root, relpath)
        _verify_envelope(document, "finalized envelope content hash mismatch")
    overlay_path = resolve_contained_relpath(run_root, "camera/overlay-cameras.svg")
    if overlay_path.stat().st_size == 0:
        raise ValueError("finalized overlay is empty")


def finalize_camera_run(staging_run: Path, final_run: Path, manifest: dict) -> None:
    import os

    runs_root = final_run.parent
    staging_relative = staging_run.relative_to(runs_root)
    resolve_contained_relpath(runs_root, staging_relative.as_posix())
    validate_contained_destination(runs_root, final_run.name)
    if final_run.exists() or final_run.is_symlink():
        raise FileExistsError(str(final_run))
    _verify_camera_run(staging_run, manifest)
    os.replace(staging_run, final_run)
    try:
        _verify_camera_run(final_run, manifest)
    except (OSError, ValueError):
        try:
            os.replace(final_run, staging_run)
        except OSError:
            pass
        raise


def _staged_operational_result(
    *,
    cam_run_id: str,
    final_run: Path,
    staging_run: Path,
    finding,
) -> CameraRunResult:
    report = {
        "report_version": 1,
        "cam_run_id": cam_run_id,
        "outcome": "operational",
        "cli_exit": 2,
        "terminal_finding": (
            {"code": finding.code, "severity": finding.severity, "source_ref": finding.source_ref}
            if finding is not None
            else None
        ),
    }
    try:
        report_path = staging_run / "camera" / "camera-report.json"
        if staging_run.is_dir() and staging_run.joinpath("camera").is_dir():
            if report_path.exists():
                replacement = report_path.with_name("camera-report.operational-failure.tmp")
                _write_staged_json(replacement, report)
                atomic_replace(replacement, report_path)
            else:
                _write_staged_json(report_path, report)
    except (OSError, ValueError):
        pass
    return CameraRunResult(cli_exit=2, final_run=final_run, staging_run=staging_run, diagnostic=report)