"""Pure stdlib 2D geometry helpers for the camera planner (no shapely).

point-in-polygon and segment-distance are implemented with locked numpy/stdlib
per PLAN-004 §6 (no new dependency). All functions are deterministic pure
functions of their inputs.
"""

from __future__ import annotations

import math

from pwa.camera.types import Point

EPS = 1e-12


def polygon_area(points: tuple[Point, ...]) -> float:
    total = 0.0
    n = len(points)
    for i, point in enumerate(points):
        nxt = points[(i + 1) % n]
        total += (point[0] * nxt[1]) - (nxt[0] * point[1])
    return total / 2.0


def centroid(points: tuple[Point, ...]) -> Point:
    """Area-weighted planar centroid (signed shoelace formula).

    For a simple (non-self-intersecting) polygon this returns the actual
    centroid; for the Part-1 Layer-A fixture the polygon is axis-aligned.
    """
    n = len(points)
    area2 = 0.0  # twice the signed area
    cx = 0.0
    cy = 0.0
    for i in range(n):
        p = points[i]
        q = points[(i + 1) % n]
        cross = p[0] * q[1] - q[0] * p[1]
        area2 += cross
        cx += (p[0] + q[0]) * cross
        cy += (p[1] + q[1]) * cross
    if abs(area2) < EPS:
        # Degenerate (zero-area) polygon: fall back to the arithmetic mean.
        return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)
    return (cx / (3.0 * area2), cy / (3.0 * area2))


def point_in_polygon(point: Point, polygon: tuple[Point, ...], epsilon: float = 1e-6) -> bool:
    """Ray-casting point-in-polygon; boundary treated as *inside* (within
    epsilon). Returns False when the point is on the boundary within epsilon
    (PLAN-004 §7.3: on-boundary is rejected by the caller).
    """
    x, y = point
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        # On-boundary check (distance to the segment), within epsilon.
        if _distance_point_to_segment(point, (xi, yi), (xj, yj)) <= epsilon:
            return False
        if (yi > y) != (yj > y):
            x_int = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_int:
                inside = not inside
        j = i
    return inside


def _distance_point_to_segment(p: Point, a: Point, b: Point) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < EPS:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    px_proj = ax + t * dx
    py_proj = ay + t * dy
    return math.hypot(px - px_proj, py - py_proj)


def distance_point_to_segment(p: Point, a: Point, b: Point) -> float:
    """Perpendicular distance from point ``p`` to segment ``a``-``b`` (2D)."""
    return _distance_point_to_segment(p, a, b)


def distance_point_to_point(a: Point, b: Point) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])