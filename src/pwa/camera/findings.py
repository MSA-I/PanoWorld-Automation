"""Deterministic finding primitives for PLAN-004 (camera planner)."""

from __future__ import annotations

from dataclasses import dataclass

# Append-only CAM_* vocabulary (ADR-0008). Mirrors the GEOM_* table's
# (severity, tier) shape. Consumes match on codes, never message text.
_FINDING_SPECS = {
    "CAM_SOURCE_HASH_MISMATCH": ("error", 0),
    "CAM_RESOURCE_LIMIT": ("error", 0),
    "CAM_EMPTY_GEOMETRY": ("error", 2),
    "CAM_DUPLICATE_ENTITY": ("error", 2),
    "CAM_UNCOVERED_ROOM": ("error", 3),
    "CAM_VIEWPOINT_OUTSIDE_ROOM": ("error", 3),
    "CAM_VIEWPOINT_COLLIDES_WALL": ("error", 3),
    "CAM_VIEWPOINT_COLLIDES_OPENING": ("error", 3),
    "CAM_EXTRINSICS_INVALID": ("error", 3),
    "CAM_CAMERA_HEIGHT_OUT_OF_RANGE": ("error", 3),
    "CAM_MAP_ADJACENCY_UNRESOLVED": ("warn", 4),
}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    tier: int
    source_ref: str | None
    message: str


class CameraError(ValueError):
    def __init__(self, code: str, message: str, *, source_ref: str | None = None):
        spec = finding_spec(code)
        self.finding = Finding(code=code, severity=spec[0], tier=spec[1], source_ref=source_ref, message=message)
        super().__init__(message)


def finding_spec(code: str) -> tuple[str, int]:
    if code not in _FINDING_SPECS:
        raise KeyError(f"Unknown finding code: {code}")
    return _FINDING_SPECS[code]


def make_finding(code: str, message: str, *, source_ref: str | None = None) -> Finding:
    severity, tier = finding_spec(code)
    return Finding(code=code, severity=severity, tier=tier, source_ref=source_ref, message=message)


def sort_findings(findings: list[Finding]) -> list[Finding]:
    unique = {(f.code, f.source_ref, f.message): f for f in findings}
    return sorted(unique.values(), key=lambda f: (f.tier, f.code, f.source_ref or "", f.message))