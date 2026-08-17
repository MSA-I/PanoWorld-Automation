"""Deterministic finding primitives for PLAN-003 (geometry compiler)."""

from __future__ import annotations

from dataclasses import dataclass

# Append-only GEOM_* vocabulary (PLAN-003 §5). Mirrors the PARSE_* table's
# (severity, tier) shape. Consumes match on codes, never message text.
_FINDING_SPECS = {
    "GEOM_SOURCE_HASH_MISMATCH": ("error", 0),
    "GEOM_RESOURCE_LIMIT": ("error", 0),
    "GEOM_EMPTY_GEOMETRY": ("error", 2),
    "GEOM_DUPLICATE_ENTITY": ("error", 2),
    "GEOM_OPEN_POLYGON": ("error", 3),
    "GEOM_SELF_INTERSECTING_POLYGON": ("error", 3),
    "GEOM_DEGENERATE_WALL": ("error", 3),
    "GEOM_OPENING_UNRESOLVED_WALL": ("error", 3),
    "GEOM_OPENING_AMBIGUOUS_WALL_REF": ("error", 3),
    "GEOM_OPENING_OFF_WALL": ("error", 3),
    "GEOM_OPENING_WIDTH_EXCEEDS_WALL": ("error", 3),
    "GEOM_OPENING_ABOVE_WALL": ("error", 3),
    "GEOM_OPEN_ROOM_BOUNDARY": ("warn", 4),
}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    tier: int
    source_ref: str | None
    message: str


class GeometryError(ValueError):
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
