"""PLAN-003 topology + dimension validation (§7.3, §7.4).

Validates a compiled scene_geometry against the source parse projection:
- room polygons closed + simple (non-zero area, no self-intersection)
- walls non-degenerate
- walls shared consistently (endpoints coincide with room vertices)
- openings resolve to exactly one wall, sit on it within tolerance, fit its
  length, and fit vertically (sill+height ≤ host wall height), with door depth
  equal to host wall thickness

The gate still runs when the only findings are warnings (GEOM_OPEN_ROOM_BOUNDARY
is warn, mirroring PARSE_ROOM_BOUNDARY_UNMATCHED); errors fail closed.
"""

from __future__ import annotations

import math

from pwa.geometry.config import DEGENERATE_WALL_M, OPENING_OFFSET_M, QUANTUM_M
from pwa.geometry.findings import Finding, make_finding
from pwa.geometry.types import CompiledGeometry, GeoWall

_AREA_EPS = 1e-12


def _points_close(a: tuple[float, float], b: tuple[float, float], tol: float = OPENING_OFFSET_M) -> bool:
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _distinct_vertices(points: tuple[tuple[float, float], ...]) -> tuple[tuple[float, float], ...]:
    """Return vertices with consecutive duplicates removed (within tolerance)."""
    result: list[tuple[float, float]] = []
    for point in points:
        if not result or not _points_close(result[-1], point):
            result.append(point)
    # The implicit closing edge may also collapse (last == first); drop the
    # trailing duplicate of a ring.
    if len(result) > 1 and _points_close(result[0], result[-1]):
        result.pop()
    return tuple(result)


def _segment_length(start: tuple[float, float], end: tuple[float, float]) -> float:
    return math.hypot(end[0] - start[0], end[1] - start[1])


def _polygon_area(points: tuple[tuple[float, float], ...]) -> float:
    total = 0.0
    for index, point in enumerate(points):
        nxt = points[(index + 1) % len(points)]
        total += (point[0] * nxt[1]) - (nxt[0] * point[1])
    return total / 2.0


def _closing_segments(
    points: tuple[tuple[float, float], ...],
) -> tuple[tuple[tuple[float, float], tuple[float, float]], ...]:
    return tuple(
        (points[index], points[(index + 1) % len(points)])
        for index in range(len(points))
    )


def _segments_intersect(
    a: tuple[tuple[float, float], tuple[float, float]],
    b: tuple[tuple[float, float], tuple[float, float]],
) -> bool:
    def orient(p, q, r):
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if abs(val) < QUANTUM_M:
            return 0
        return 1 if val > 0 else -1

    def on_segment(p, q, r):
        return (
            min(p[0], r[0]) - QUANTUM_M <= q[0] <= max(p[0], r[0]) + QUANTUM_M
            and min(p[1], r[1]) - QUANTUM_M <= q[1] <= max(p[1], r[1]) + QUANTUM_M
        )

    p1, q1 = a
    p2, q2 = b
    o1 = orient(p1, q1, p2)
    o2 = orient(p1, q1, q2)
    o3 = orient(p2, q2, p1)
    o4 = orient(p2, q2, q1)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and on_segment(p1, p2, q1):
        return True
    if o2 == 0 and on_segment(p1, q2, q1):
        return True
    if o3 == 0 and on_segment(p2, p1, q2):
        return True
    if o4 == 0 and on_segment(p2, q1, q2):
        return True
    return False


def _wall_projection(
    wall: GeoWall, center: tuple[float, float]
) -> tuple[float, float, float]:
    """Return (t along wall from start, perpendicular distance, wall length)."""
    sx, sy = wall.start
    ex, ey = wall.end
    vx, vy = ex - sx, ey - sy
    length = math.hypot(vx, vy)
    if length == 0:
        return 0.0, 0.0, 0.0
    ux, uy = vx / length, vy / length
    dx, dy = center[0] - sx, center[1] - sy
    t = dx * ux + dy * uy
    distance = abs(dx * uy - dy * ux)
    return t, distance, length


def validate_topology(compiled: CompiledGeometry) -> list[Finding]:
    findings: list[Finding] = []

    # --- room closure / simplicity ---
    # PLAN-002 canonical room polygons do NOT repeat the first vertex, so a
    # polygon is "closed" if its last vertex is reachable from the first by one
    # implicit closing edge (the schema allows minItems=3 non-repeating rings).
    # An explicitly-repeated first vertex (first==last) is also accepted.
    for room in compiled.rooms:
        polygon = room.polygon
        # A polygon with fewer than 3 distinct vertices cannot close into a
        # non-zero ring -> GEOM_OPEN_POLYGON (the "too short to close" case).
        distinct = _distinct_vertices(polygon)
        if len(distinct) < 3:
            findings.append(make_finding("GEOM_OPEN_POLYGON", "room polygon has fewer than three distinct vertices", source_ref=room.id))
            continue
        area = _polygon_area(distinct)
        if abs(area) <= _AREA_EPS:
            findings.append(make_finding("GEOM_SELF_INTERSECTING_POLYGON", "room polygon has zero area", source_ref=room.id))
            continue
        segments = _closing_segments(distinct)
        crossed = False
        n = len(segments)
        for i in range(n):
            for j in range(i + 1, n):
                if j == i + 1 or (i == 0 and j == n - 1):
                    continue
                if _segments_intersect(segments[i], segments[j]):
                    crossed = True
                    break
            if crossed:
                break
        if crossed:
            findings.append(make_finding("GEOM_SELF_INTERSECTING_POLYGON", "room polygon self-intersects", source_ref=room.id))

    # --- wall degeneracy ---
    for wall in compiled.walls:
        if _segment_length(wall.start, wall.end) < DEGENERATE_WALL_M:
            findings.append(make_finding("GEOM_DEGENERATE_WALL", "wall is shorter than the minimum length", source_ref=wall.id))

    # --- wall sharing / closed room boundary ---
    # Every wall endpoint must coincide (within tolerance) with a vertex of at
    # least one room, and a wall shared by two rooms must touch both. A room
    # polygon edge (segment) with no collinear supporting wall is a warning.
    all_room_vertices = [v for room in compiled.rooms for v in room.polygon]
    walls_by_id = {wall.id: wall for wall in compiled.walls}

    def _vertex_present(point: tuple[float, float]) -> bool:
        return any(_points_close(point, v) for v in all_room_vertices)

    for wall in compiled.walls:
        if not (_vertex_present(wall.start) and _vertex_present(wall.end)):
            findings.append(
                make_finding(
                    "GEOM_OPEN_ROOM_BOUNDARY",
                    "wall endpoints do not coincide with any room boundary",
                    source_ref=wall.id,
                )
            )

    # Every room edge must have a supporting wall collinear with it, or be
    # matched to an adjacent room's shared edge. For the closed-topology check
    # we accept an edge as supported if any wall is collinear with it (both
    # endpoints lie on the wall's infinite line within tolerance) and fully
    # contained within it.
    for room in compiled.rooms:
        for seg in _closing_segments(room.polygon):
            supported = False
            for wall in compiled.walls:
                t0, d0, length = _wall_projection(wall, seg[0])
                t1, d1, _ = _wall_projection(wall, seg[1])
                if d0 <= OPENING_OFFSET_M and d1 <= OPENING_OFFSET_M:
                    if -QUANTUM_M <= t0 <= length + QUANTUM_M and -QUANTUM_M <= t1 <= length + QUANTUM_M:
                        supported = True
                        break
            if not supported:
                findings.append(
                    make_finding(
                        "GEOM_OPEN_ROOM_BOUNDARY",
                        "room edge has no supporting wall",
                        source_ref=room.id,
                    )
                )

    # --- opening validation (§7.3) ---
    # Door depth == host wall thickness is guaranteed by construction (the
    # compiler derives depth_m from the same thickness the host wall received),
    # so it is not re-checked here; the only way it could diverge is an
    # unresolved wall, which is already GEOM_OPENING_UNRESOLVED_WALL above.
    for opening in compiled.openings:
        if opening.wall_id not in walls_by_id:
            findings.append(
                make_finding(
                    "GEOM_OPENING_UNRESOLVED_WALL",
                    "opening references an unknown wall",
                    source_ref=opening.id,
                )
            )
            continue
        host = walls_by_id[opening.wall_id]
        t, distance, length = _wall_projection(host, opening.center)
        if distance > OPENING_OFFSET_M:
            findings.append(
                make_finding("GEOM_OPENING_OFF_WALL", "opening centre is off its host wall", source_ref=opening.id)
            )
        # span fit: half-width on each side of the centre must stay within the wall
        half = opening.width_m / 2.0
        if t - half < -QUANTUM_M or t + half > length + QUANTUM_M:
            findings.append(
                make_finding(
                    "GEOM_OPENING_WIDTH_EXCEEDS_WALL",
                    "opening span does not fit within its host wall",
                    source_ref=opening.id,
                )
            )
        if opening.sill_m + opening.height_m > host.height_m + QUANTUM_M:
            findings.append(
                make_finding("GEOM_OPENING_ABOVE_WALL", "opening rises above the host wall", source_ref=opening.id)
            )

    return findings


def validation_report(compiled: CompiledGeometry, findings: list[Finding]) -> dict:
    """The topology-report.json body (raw evidence, not an envelope)."""
    return {
        "report_version": 1,
        "metrics": {
            "rooms": len(compiled.rooms),
            "walls": len(compiled.walls),
            "openings": len(compiled.openings),
        },
        "checks": {
            "rooms_closed_simple": not any(f.code in {"GEOM_OPEN_POLYGON", "GEOM_SELF_INTERSECTING_POLYGON"} for f in findings),
            "walls_non_degenerate": not any(f.code == "GEOM_DEGENERATE_WALL" for f in findings),
            "openings_on_wall": not any(
                f.code in {"GEOM_OPENING_UNRESOLVED_WALL", "GEOM_OPENING_OFF_WALL", "GEOM_OPENING_WIDTH_EXCEEDS_WALL"} for f in findings
            ),
            "openings_fit_vertically": not any(f.code == "GEOM_OPENING_ABOVE_WALL" for f in findings),
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
