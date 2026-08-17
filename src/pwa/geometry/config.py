"""Central PLAN-003 geometry-compiler limits, defaults and tolerances.

Numeric defaults here are the normative geometry defaults from PLAN-003 §7
(thickness/height, opening height/sill) and the tolerances it inherits from
PLAN-002 (opening offset, degenerate wall). A change to any of these is a
critical Geometry-gate change (PLAN-003 §14.4) requiring a revised plan and
Moshe approval.
"""

from __future__ import annotations

QUANTUM_M = 1e-4
# PLAN-003 §7.2 thumbs: interior wall thickness default (DR-001) and
# full-height wall height default. Both recorded in assumptions.json.
WALL_THICKNESS_M = 0.10
WALL_HEIGHT_M = 2.60
DEFAULT_CEILING_HEIGHT_M = 2.60
# PLAN-003 §7.3 vertical placement defaults.
DOOR_HEIGHT_M = 2.10
DOOR_SILL_M = 0.00
WINDOW_HEIGHT_M = 1.20
WINDOW_SILL_M = 0.90
# Inherited tolerances (PLAN-002 §6, upheld by PLAN-003 §7.3).
OPENING_OFFSET_M = 0.02
DEGENERATE_WALL_M = 0.05
# PLAN-003 §7.1 bounding guard (reuse PLAN-002's magnitude cap).
MAX_COORDINATE_MAGNITUDE_M = 100_000
# Resource bounds for geometry runs.
MAX_WALLS = 20_000
MAX_ROOMS = 5_000
MAX_OPENINGS = 20_000
MAX_POLYGON_VERTICES = 10_000
MAX_OVERLAY_BYTES = 70 * 1024 * 1024

# Top-down overlay geometry-scale fractions (mirror PLAN-002).
OVERLAY_MARGIN_FRACTION = 0.05
OVERLAY_OPENING_RADIUS_FRACTION = 0.01
OVERLAY_FONT_SIZE_FRACTION = 0.02
OVERLAY_PNG_SCALE = 100  # pixels per metre of the overlay PNG render


def limits_snapshot() -> dict[str, object]:
    return {
        "QUANTUM_M": QUANTUM_M,
        "WALL_THICKNESS_M": WALL_THICKNESS_M,
        "WALL_HEIGHT_M": WALL_HEIGHT_M,
        "DEFAULT_CEILING_HEIGHT_M": DEFAULT_CEILING_HEIGHT_M,
        "DOOR_HEIGHT_M": DOOR_HEIGHT_M,
        "DOOR_SILL_M": DOOR_SILL_M,
        "WINDOW_HEIGHT_M": WINDOW_HEIGHT_M,
        "WINDOW_SILL_M": WINDOW_SILL_M,
        "OPENING_OFFSET_M": OPENING_OFFSET_M,
        "DEGENERATE_WALL_M": DEGENERATE_WALL_M,
        "MAX_COORDINATE_MAGNITUDE_M": MAX_COORDINATE_MAGNITUDE_M,
        "MAX_WALLS": MAX_WALLS,
        "MAX_ROOMS": MAX_ROOMS,
        "MAX_OPENINGS": MAX_OPENINGS,
        "MAX_POLYGON_VERTICES": MAX_POLYGON_VERTICES,
        "MAX_OVERLAY_BYTES": MAX_OVERLAY_BYTES,
        "OVERLAY_MARGIN_FRACTION": OVERLAY_MARGIN_FRACTION,
        "OVERLAY_OPENING_RADIUS_FRACTION": OVERLAY_OPENING_RADIUS_FRACTION,
        "OVERLAY_FONT_SIZE_FRACTION": OVERLAY_FONT_SIZE_FRACTION,
        "OVERLAY_PNG_SCALE": OVERLAY_PNG_SCALE,
    }
