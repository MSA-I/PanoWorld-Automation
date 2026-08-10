"""Deterministic finding primitives for PLAN-002."""

from __future__ import annotations

from dataclasses import dataclass

_FINDING_SPECS = {
    "PARSE_SOURCE_UNSUPPORTED": ("error", 0),
    "PARSE_SOURCE_HASH_MISMATCH": ("error", 0),
    "PARSE_RESOURCE_LIMIT": ("error", 0),
    "PARSE_TIMEOUT": ("error", 0),
    "PARSE_UNITS_MISMATCH": ("error", 1),
    "PARSE_UNSUPPORTED_FEATURE": ("error", 1),
    "PARSE_SCALE_UNKNOWN": ("error", 1),
    "PARSE_EMPTY_GEOMETRY": ("error", 2),
    "PARSE_DUPLICATE_ENTITY": ("error", 2),
    "PARSE_OPEN_POLYGON": ("error", 3),
    "PARSE_SELF_INTERSECTING_POLYGON": ("error", 3),
    "PARSE_DEGENERATE_WALL": ("error", 3),
    "PARSE_UNKNOWN_WALL_REF": ("error", 3),
    "PARSE_AMBIGUOUS_WALL_REF": ("error", 3),
    "PARSE_OPENING_OFF_WALL": ("error", 3),
    "PARSE_OPENING_WIDTH_EXCEEDS_WALL": ("error", 3),
    "PARSE_DIMENSION_INCONSISTENT": ("error", 3),
    "PARSE_LOW_CONFIDENCE": ("warn", 4),
    "PARSE_UNMAPPED_SOURCE_ENTITY": ("warn", 4),
    "PARSE_ROOM_BOUNDARY_UNMATCHED": ("warn", 4),
}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    tier: int
    source_ref: str | None
    message: str


class FloorplanError(ValueError):
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
