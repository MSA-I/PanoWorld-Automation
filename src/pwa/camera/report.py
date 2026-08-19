"""PLAN-004 coverage report (§7.4, §7.5) and camera run report builders.

The coverage report is raw evidence (not an envelope): per-room coverage,
collision and adjacency checks, plus the gate results the G3 gate reads.
"""

from __future__ import annotations

from pwa.camera.findings import Finding
from pwa.camera.types import SceneGeometry, Viewpoint


def coverage_report(
    geometry: SceneGeometry,
    viewpoints: tuple[Viewpoint, ...],
    edges: list[list[str]],
    start_viewpoint: str | None,
    findings: list[Finding],
) -> dict:
    viewpoint_by_room: dict[str, list[str]] = {}
    for vp in viewpoints:
        viewpoint_by_room.setdefault(vp.room_id, []).append(vp.id)

    per_room = []
    for room in sorted(geometry.rooms, key=lambda r: r.id):
        per_room.append(
            {
                "room_id": room.id,
                "viewpoints": sorted(viewpoint_by_room.get(room.id, [])),
                "covered": room.id in viewpoint_by_room,
            }
        )

    error_codes = [f.code for f in findings if f.severity == "error"]
    warn_codes = [f.code for f in findings if f.severity == "warn"]

    return {
        "report_version": 1,
        "metrics": {
            "rooms": len(geometry.rooms),
            "viewpoints": len(viewpoints),
            "edges": len(edges),
            "uncovered_rooms": sum(1 for r in per_room if not r["covered"]),
        },
        "per_room": per_room,
        "edges": edges,
        "start_viewpoint": start_viewpoint,
        "checks": {
            "every_room_covered": all(r["covered"] for r in per_room) and len(per_room) > 0,
            "no_collision_errors": "CAM_VIEWPOINT_COLLIDES_WALL" not in error_codes
            and "CAM_VIEWPOINT_COLLIDES_OPENING" not in error_codes
            and "CAM_VIEWPOINT_OUTSIDE_ROOM" not in error_codes,
            "extrinsics_valid": "CAM_EXTRINSICS_INVALID" not in error_codes,
            "no_uncovered_rooms": "CAM_UNCOVERED_ROOM" not in error_codes,
            "no_duplicate_entities": "CAM_DUPLICATE_ENTITY" not in error_codes,
        },
        "findings": [
            {
                "code": f.code,
                "severity": f.severity,
                "tier": f.tier,
                "source_ref": f.source_ref,
                "message": f.message,
            }
            for f in findings
        ],
    }


def camera_report(
    cam_run_id: str,
    source_artifact_id: str,
    outcome: str,
    cli_exit: int,
    limits: dict,
    metrics: dict,
    findings: list[Finding],
) -> dict:
    return {
        "report_version": 1,
        "cam_run_id": cam_run_id,
        "source_artifact_id": source_artifact_id,
        "outcome": outcome,
        "cli_exit": cli_exit,
        "limits": limits,
        "metrics": metrics,
        "findings": [
            {
                "code": f.code,
                "severity": f.severity,
                "tier": f.tier,
                "source_ref": f.source_ref,
                "message": f.message,
            }
            for f in findings
        ],
    }