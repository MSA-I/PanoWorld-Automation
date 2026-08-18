"""PLAN-004 camera placement, free-space resolution, coverage and collision.

Normative section §7.3-§7.5:
- primary candidate per room is the area-weighted planar centroid
- free-space validity: inside room polygon (boundary rejected), wall clearance
  >= thickness/2 + 0.35 m, opening clearance >= 0.20 m
- invalid centroid is pulled inward along the vector from the nearest violated
  wall, bounded by MAX_PULLBACK_M; if no valid point exists the room is
  reported CAM_UNCOVERED_ROOM (fail-closed)
- coverage target: every room covered by >= 1 viewpoint
- collision-free == free-space valid; errors fail closed

Fully deterministic: pure functions of the input geometry.
"""

from __future__ import annotations

import math

from pwa.camera.config import (
    CAMERA_HEIGHT_M,
    DEFAULT_YAW_RAD,
    MAX_PULLBACK_M,
    OPENING_CLEARANCE_M,
    WALL_CLEARANCE_M,
)
from pwa.camera.findings import Finding, make_finding
from pwa.camera.geometry import centroid, distance_point_to_point, distance_point_to_segment, point_in_polygon
from pwa.camera.types import Point, SceneGeometry, Viewpoint

_PULLBACK_STEP_M = 0.05


def wall_clearance_required(thickness_m: float) -> float:
    """Minimum centreline distance to a wall of the given thickness."""
    return thickness_m / 2.0 + WALL_CLEARANCE_M


def _nearest_wall_distance(point: Point, geometry: SceneGeometry) -> tuple[float, Wall | None]:
    best_dist = math.inf
    best_wall = None
    for wall in geometry.walls:
        d = distance_point_to_segment(point, wall.start, wall.end)
        if d < best_dist:
            best_dist = d
            best_wall = wall
    return best_dist, best_wall


def _nearest_opening_distance(point: Point, geometry: SceneGeometry) -> tuple[float, Opening | None]:
    best_dist = math.inf
    best_opening = None
    for opening in geometry.openings:
        d = distance_point_to_point(point, opening.center)
        if d < best_dist:
            best_dist = d
            best_opening = opening
    return best_dist, best_opening


def free_space_violations(
    point: Point,
    room,
    geometry: SceneGeometry,
) -> list[Finding]:
    """Return the CAM_* collision findings for a point against a room.

    An empty list means the point is free-space valid (§7.3.2).
    """
    findings: list[Finding] = []
    inside = point_in_polygon(point, room.polygon)
    if not inside:
        findings.append(make_finding("CAM_VIEWPOINT_OUTSIDE_ROOM", "viewpoint lies outside or on the room boundary", source_ref=room.id))

    for wall in geometry.walls:
        d = distance_point_to_segment(point, wall.start, wall.end)
        if d < wall_clearance_required(wall.thickness_m):
            findings.append(make_finding("CAM_VIEWPOINT_COLLIDES_WALL", "viewpoint is too close to a wall centreline", source_ref=wall.id))

    for opening in geometry.openings:
        d = distance_point_to_point(point, opening.center)
        if d < OPENING_CLEARANCE_M:
            findings.append(make_finding("CAM_VIEWPOINT_COLLIDES_OPENING", "viewpoint is too close to an opening centre", source_ref=opening.id))

    return findings


def _pull_inward(point: Point, room, geometry: SceneGeometry) -> Point:
    """Pull an invalid candidate to a free-space-valid point.

    Iteratively steps away from the nearest violating wall or opening (a small
    deterministic step), staying inside the room polygon, until free-space
    valid or MAX_PULLBACK_M from the origin is exhausted. Deterministic: fixed
    step, no randomness. Mirrors PLAN-004 §7.3.2 (thin-room and opening-near-
    centroid pull-back).
    """
    current = point
    origin = point
    max_steps = int(math.ceil(MAX_PULLBACK_M / _PULLBACK_STEP_M))
    step = 0
    while step < max_steps:
        if not point_in_polygon(current, room.polygon):
            return current
        move_dir = _nearest_violation_direction(current, room, geometry)
        if move_dir is None:
            # No violation remains -> free-space valid.
            break
        current = (current[0] + move_dir[0] * _PULLBACK_STEP_M, current[1] + move_dir[1] * _PULLBACK_STEP_M)
        if distance_point_to_point(origin, current) > MAX_PULLBACK_M:
            return current
        step += 1
    return current


def _nearest_violation_direction(point: Point, room, geometry: SceneGeometry) -> tuple[float, float] | None:
    """Return a unit direction to step away from the nearest wall/opening
    violation, or None if the point is free-space valid."""
    best_dist = math.inf
    best_dir: tuple[float, float] | None = None

    for wall in geometry.walls:
        req = wall_clearance_required(wall.thickness_m)
        d = distance_point_to_segment(point, wall.start, wall.end)
        if d < req:
            deficit = req - d
            if deficit > best_dist:
                continue
            best_dist = deficit
            best_dir = _away_from_segment(point, wall.start, wall.end)

    for opening in geometry.openings:
        d = distance_point_to_point(point, opening.center)
        if d < OPENING_CLEARANCE_M:
            deficit = OPENING_CLEARANCE_M - d
            if deficit > best_dist:
                continue
            best_dist = deficit
            # Direction away from the opening centre.
            nx = point[0] - opening.center[0]
            ny = point[1] - opening.center[1]
            n = math.hypot(nx, ny)
            if n < 1e-12:
                best_dir = (1.0, 0.0)
            else:
                best_dir = (nx / n, ny / n)

    return best_dir


def _away_from_segment(point: Point, a: Point, b: Point) -> tuple[float, float]:
    """Unit direction from a segment toward ``point``, floored to X/Y axes when
    near-collinear (avoids numeric noise); deterministic."""
    ax, ay = a
    bx, by = b
    px, py = point
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-12:
        # Degenerate segment: direction from a to point.
        d = distance_point_to_point(point, a)
        if d < 1e-12:
            return (1.0, 0.0)
        return ((px - ax) / d, (py - ay) / d)
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    cx = ax + t * dx
    cy = ay + t * dy
    nx = px - cx
    ny = py - cy
    n = math.hypot(nx, ny)
    if n < 1e-12:
        # Point is on the segment: push along the segment normal.
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        return (-uy, ux)
    return (nx / n, ny / n)


def place_viewpoints(geometry: SceneGeometry, *, camera_height_m: float = CAMERA_HEIGHT_M) -> tuple[tuple[Viewpoint, ...], list[Finding]]:
    """Place one deterministic viewpoint per room (planar centroid, pulled
    inward if needed). Returns (viewpoints, findings).

    Viewpoint IDs are zero-padded ordinals in deterministic room order (sorted
    by room id). A room with no valid placement yields CAM_UNCOVERED_ROOM and
    no viewpoint for that room.
    """
    findings: list[Finding] = []
    viewpoints: list[Viewpoint] = []
    ordered_rooms = sorted(geometry.rooms, key=lambda r: r.id)

    for room in ordered_rooms:
        candidate = centroid(room.polygon)
        violations = free_space_violations(candidate, room, geometry)
        if not violations:
            valid = candidate
        else:
            # Pull inward from the nearest violating wall, then re-validate.
            pulled = _pull_inward(candidate, room, geometry)
            pulled_violations = free_space_violations(pulled, room, geometry)
            if not pulled_violations:
                valid = pulled
            else:
                # Fail-closed: this room has no valid placement.
                findings.append(make_finding("CAM_UNCOVERED_ROOM", "room has zero valid viewpoint placements", source_ref=room.id))
                continue

        viewpoint = Viewpoint(
            id=f"{len(viewpoints):04d}",
            position=valid,
            yaw_rad=DEFAULT_YAW_RAD,
            room_id=room.id,
            camera_height_m=camera_height_m,
        )
        viewpoints.append(viewpoint)

    # Duplicate position guard (CAM_DUPLICATE_ENTITY, fail-closed).
    seen_positions: dict[Point, str] = {}
    for vp in viewpoints:
        key = (round(vp.position[0], 6), round(vp.position[1], 6))
        if key in seen_positions:
            findings.append(make_finding("CAM_DUPLICATE_ENTITY", "viewpoint positions collided within one run", source_ref=vp.id))
        else:
            seen_positions[key] = vp.id

    return tuple(viewpoints), findings