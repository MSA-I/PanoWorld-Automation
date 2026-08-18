"""Central PLAN-004 camera-planner limits, defaults and tolerances.

Numeric defaults here are the normative camera defaults from PLAN-004 §7
(camera height, wall clearance, opening clearance) and ADR-0008 (resolution,
batch). A change to any of these is a critical Camera-gate change
(PLAN-004 §13.4) requiring a revised plan and Moshe approval.
"""

from __future__ import annotations

# PLAN-004 §7.2 camera height and clearances (recorded in assumptions.json).
CAMERA_HEIGHT_M = 1.35
CAMERA_HEIGHT_MIN_M = 0.5
CAMERA_HEIGHT_MAX_M = 3.0
WALL_CLEARANCE_M = 0.35
OPENING_CLEARANCE_M = 0.20

# PLAN-004 §7.3 free-space placement.
POINT_IN_POLYGON_EPSILON_M = 1e-6
# Maximum inward pull-back distance for an invalid centroid, before the room
# is reported CAM_UNCOVERED_ROOM.
MAX_PULLBACK_M = 2.0

# PLAN-004 §7.6 default yaw (radians about Z); camera +Z forward to world +X.
DEFAULT_YAW_RAD = 0.0

# ADR-0008 defaults: resolution 2048x1024 (width == 2*height), batch 8.
RESOLUTION_WIDTH = 2048
RESOLUTION_HEIGHT = 1024
MAX_VIEWS_PER_LRM_BATCH = 8

# Resource bounds for camera runs (mirror the geometry compiler's guard shape).
MAX_ROOMS = 5_000
MAX_OPENINGS = 20_000
MAX_POLYGON_VERTICES = 10_000
MAX_COORDINATE_MAGNITUDE_M = 100_000
MAX_OVERLAY_BYTES = 70 * 1024 * 1024

# Top-down coverage overlay fractions (mirror PLAN-003).
OVERLAY_MARGIN_FRACTION = 0.05
OVERLAY_CAMERA_RADIUS_FRACTION = 0.012
OVERLAY_FONT_SIZE_FRACTION = 0.02
OVERLAY_OPENING_RADIUS_FRACTION = 0.01
OVERLAY_SVG_ONLY = True  # PLAN-004 AC-8 requires an SVG/PNG overlay; SVG suffices.


def limits_snapshot() -> dict[str, object]:
    return {
        "CAMERA_HEIGHT_M": CAMERA_HEIGHT_M,
        "CAMERA_HEIGHT_MIN_M": CAMERA_HEIGHT_MIN_M,
        "CAMERA_HEIGHT_MAX_M": CAMERA_HEIGHT_MAX_M,
        "WALL_CLEARANCE_M": WALL_CLEARANCE_M,
        "OPENING_CLEARANCE_M": OPENING_CLEARANCE_M,
        "POINT_IN_POLYGON_EPSILON_M": POINT_IN_POLYGON_EPSILON_M,
        "MAX_PULLBACK_M": MAX_PULLBACK_M,
        "DEFAULT_YAW_RAD": DEFAULT_YAW_RAD,
        "RESOLUTION_WIDTH": RESOLUTION_WIDTH,
        "RESOLUTION_HEIGHT": RESOLUTION_HEIGHT,
        "MAX_VIEWS_PER_LRM_BATCH": MAX_VIEWS_PER_LRM_BATCH,
        "MAX_ROOMS": MAX_ROOMS,
        "MAX_OPENINGS": MAX_OPENINGS,
        "MAX_POLYGON_VERTICES": MAX_POLYGON_VERTICES,
        "MAX_COORDINATE_MAGNITUDE_M": MAX_COORDINATE_MAGNITUDE_M,
        "MAX_OVERLAY_BYTES": MAX_OVERLAY_BYTES,
    }