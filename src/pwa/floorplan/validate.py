"""Geometry invariant validation for normalized floorplans."""

from __future__ import annotations

import math
from decimal import Decimal

from pwa.floorplan.config import DEGENERATE_WALL_M, LOW_CONFIDENCE_THRESHOLD, MAX_POLYGON_VERTICES, OPENING_OFFSET_M, QUANTUM_M
from pwa.floorplan.findings import Finding, make_finding, sort_findings
from pwa.floorplan.types import NormOpening, NormRoom, NormWall, NormalizedGeometry

_PENDING_DXF_WALL_ID = "__dxf_probe__"


def _to_int(point: tuple[float, float]) -> tuple[int, int]:
    return round(point[0] * 10_000), round(point[1] * 10_000)


def orient(a: tuple[int, int], b: tuple[int, int], c: tuple[int, int]) -> int:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _edges(points: tuple[tuple[float, float], ...]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    ints = [_to_int(point) for point in points]
    return list(zip(ints, ints[1:] + ints[:1]))


def seg_proper_cross(
    p1: tuple[int, int],
    p2: tuple[int, int],
    q1: tuple[int, int],
    q2: tuple[int, int],
) -> bool:
    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def seg_intersects_non_adjacent(
    p1: tuple[int, int],
    p2: tuple[int, int],
    q1: tuple[int, int],
    q2: tuple[int, int],
) -> bool:
    """Full segment-intersection predicate for one room's own non-adjacent
    edges (§8.2/AC-9: "no non-adjacent segment intersection", not merely "no
    proper crossing"). Unlike `seg_proper_cross`, this also flags collinear
    overlaps and one-sided vertex-on-edge touches.

    Deliberately NOT used for `_room_pair_warning` below: two *different*
    rooms legitimately sharing a wall produce an exactly-coincident (or
    overlapping) collinear edge pair, which is the normal adjacent-rooms
    case, not a boundary defect.
    """
    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)
    if o1 == 0 and o2 == 0 and o3 == 0 and o4 == 0:
        # Collinear: the two segments intersect (more than at a shared
        # endpoint) exactly when their 1-D projections onto their common
        # axis overlap in more than a point.
        return _collinear_segments_overlap(p1, p2, q1, q2)
    if o1 == 0 and _on_segment(p1, p2, q1):
        return True
    if o2 == 0 and _on_segment(p1, p2, q2):
        return True
    if o3 == 0 and _on_segment(q1, q2, p1):
        return True
    if o4 == 0 and _on_segment(q1, q2, p2):
        return True
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _on_segment(a: tuple[int, int], b: tuple[int, int], point: tuple[int, int]) -> bool:
    # Caller guarantees `point` is collinear with segment a-b; this only
    # checks bounding-box containment, i.e. that `point` lies *between* a
    # and b rather than on their infinite extension.
    return min(a[0], b[0]) <= point[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= point[1] <= max(a[1], b[1])


def _collinear_segments_overlap(
    p1: tuple[int, int],
    p2: tuple[int, int],
    q1: tuple[int, int],
    q2: tuple[int, int],
) -> bool:
    lo_p, hi_p = min(p1, p2), max(p1, p2)
    lo_q, hi_q = min(q1, q2), max(q1, q2)
    overlap_lo = max(lo_p, lo_q)
    overlap_hi = min(hi_p, hi_q)
    return overlap_lo < overlap_hi


def _distance_to_wall(opening: NormOpening, wall: NormWall) -> tuple[float, float, float]:
    sx, sy = wall.start
    ex, ey = wall.end
    vx = ex - sx
    vy = ey - sy
    length = math.hypot(vx, vy)
    ux = vx / length
    uy = vy / length
    dx = opening.center[0] - sx
    dy = opening.center[1] - sy
    t = dx * ux + dy * uy
    distance = abs(dx * uy - dy * ux)
    return distance, t, length


def _span_collinear_with_wall(span: tuple[tuple[float, float], tuple[float, float]], wall: NormWall) -> bool:
    sx, sy = wall.start
    ex, ey = wall.end
    vx = ex - sx
    vy = ey - sy
    length = math.hypot(vx, vy)
    if length == 0:
        return False
    ux = vx / length
    uy = vy / length
    for point in span:
        dx = point[0] - sx
        dy = point[1] - sy
        if abs(dx * uy - dy * ux) > OPENING_OFFSET_M:
            return False
    return True


def resolve_opening_wall(
    walls: tuple[NormWall, ...],
    center: tuple[float, float],
    width_m: float,
    declared_wall_id: str | None,
    span: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> tuple[str | None, list[Finding]]:
    findings: list[Finding] = []
    opening = NormOpening("__probe__", "door", declared_wall_id or "", center, width_m, 1.0, {"source_ref": None})
    declared_wall = next((wall for wall in walls if wall.id == declared_wall_id), None)
    if declared_wall_id is not None and declared_wall is None:
        return None, [make_finding("PARSE_UNKNOWN_WALL_REF", "opening references unknown wall")]
    candidates: list[NormWall] = []
    for wall in walls:
        distance, t, length = _distance_to_wall(opening, wall)
        if distance <= OPENING_OFFSET_M and -QUANTUM_M <= t <= length + QUANTUM_M:
            if span is not None and not _span_collinear_with_wall(span, wall):
                continue
            candidates.append(wall)
    if declared_wall is not None:
        distance, t, length = _distance_to_wall(opening, declared_wall)
        if distance > OPENING_OFFSET_M:
            return None, [make_finding("PARSE_OPENING_OFF_WALL", "opening is offset from declared wall")]
        if span is not None and not _span_collinear_with_wall(span, declared_wall):
            return None, [make_finding("PARSE_OPENING_OFF_WALL", "opening is not collinear with declared wall")]
        if t < (width_m / 2) - QUANTUM_M or (length - t) < (width_m / 2) - QUANTUM_M:
            return None, [make_finding("PARSE_OPENING_WIDTH_EXCEEDS_WALL", "opening width exceeds wall span")]
        # m-6 (spatial review, 2026-08-10): an explicit declaration that
        # itself passes the distance/collinearity/half-width tests is
        # accepted outright -- it must not be second-guessed against
        # `candidates[0]`, which is merely the first proximity match in
        # `walls` order, not necessarily "the" match (e.g. a double-wall
        # ~1cm apart legitimately produces multiple proximity candidates).
        return declared_wall.id, []
    if not candidates:
        return None, [make_finding("PARSE_UNKNOWN_WALL_REF", "opening does not resolve to any wall")]
    if len(candidates) > 1:
        return None, [make_finding("PARSE_AMBIGUOUS_WALL_REF", "opening resolves to multiple walls")]
    wall = candidates[0]
    distance, t, length = _distance_to_wall(opening, wall)
    if t < (width_m / 2) - QUANTUM_M or (length - t) < (width_m / 2) - QUANTUM_M:
        return None, [make_finding("PARSE_OPENING_WIDTH_EXCEEDS_WALL", "opening width exceeds wall span")]
    return wall.id, findings


def _validate_room(room: NormRoom) -> list[Finding]:
    findings: list[Finding] = []
    points = room.polygon
    if len(points) > MAX_POLYGON_VERTICES:
        return [make_finding("PARSE_RESOURCE_LIMIT", "room polygon exceeds configured vertex limit", source_ref=room.provenance.get("source_ref"))]
    if len(points) < 3:
        return [make_finding("PARSE_OPEN_POLYGON", "room polygon needs at least 3 vertices", source_ref=room.provenance.get("source_ref"))]
    if len(set(points)) != len(points):
        code = "PARSE_OPEN_POLYGON" if any(points[i] == points[i + 1] for i in range(len(points) - 1)) else "PARSE_SELF_INTERSECTING_POLYGON"
        return [make_finding(code, "room polygon repeats a vertex", source_ref=room.provenance.get("source_ref"))]
    ints = [_to_int(point) for point in points]
    area2 = 0
    for index, point in enumerate(ints):
        nxt = ints[(index + 1) % len(ints)]
        area2 += point[0] * nxt[1] - nxt[0] * point[1]
    if area2 == 0:
        return [make_finding("PARSE_SELF_INTERSECTING_POLYGON", "room polygon has zero area", source_ref=room.provenance.get("source_ref"))]
    if len(points) > 3:
        edges = _edges(points)
        for left in range(len(edges)):
            for right in range(left + 1, len(edges)):
                if right in {left, (left + 1) % len(edges)} or left == (right + 1) % len(edges):
                    continue
                if seg_intersects_non_adjacent(*edges[left], *edges[right]):
                    findings.append(
                        make_finding(
                            "PARSE_SELF_INTERSECTING_POLYGON",
                            "room polygon self-intersects",
                            source_ref=room.provenance.get("source_ref"),
                        )
                    )
                    return findings
    return findings


def _room_pair_warning(left: NormRoom, right: NormRoom) -> list[Finding]:
    if left.polygon == right.polygon:
        return []
    left_edges = _edges(left.polygon)
    right_edges = _edges(right.polygon)
    for edge_a in left_edges:
        for edge_b in right_edges:
            if seg_proper_cross(*edge_a, *edge_b):
                return [
                    make_finding(
                        "PARSE_ROOM_BOUNDARY_UNMATCHED",
                        "room boundaries cross",
                        source_ref=min(left.provenance.get("source_ref", ""), right.provenance.get("source_ref", "")),
                    )
                ]
    return []


def validate(geometry: NormalizedGeometry) -> list[Finding]:
    findings: list[Finding] = []
    seen_walls: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    usable_wall_ids: set[str] = set()
    for wall in geometry.walls:
        length = math.hypot(wall.end[0] - wall.start[0], wall.end[1] - wall.start[1])
        if length < DEGENERATE_WALL_M:
            findings.append(make_finding("PARSE_DEGENERATE_WALL", "wall is shorter than minimum", source_ref=wall.provenance.get("source_ref")))
        key = (wall.start, wall.end)
        duplicate = key in seen_walls
        if duplicate:
            findings.append(make_finding("PARSE_DUPLICATE_ENTITY", "duplicate wall geometry", source_ref=wall.provenance.get("source_ref")))
        seen_walls.add(key)
        if length >= DEGENERATE_WALL_M and not duplicate:
            usable_wall_ids.add(wall.id)
        if wall.confidence < LOW_CONFIDENCE_THRESHOLD:
            findings.append(make_finding("PARSE_LOW_CONFIDENCE", "wall confidence below threshold", source_ref=wall.provenance.get("source_ref")))

    seen_rooms: set[tuple[tuple[float, float], ...]] = set()
    usable_room_ids: set[str] = set()
    for room in geometry.rooms:
        room_findings = _validate_room(room)
        findings.extend(room_findings)
        duplicate = room.polygon in seen_rooms
        if duplicate:
            findings.append(make_finding("PARSE_DUPLICATE_ENTITY", "duplicate room geometry", source_ref=room.provenance.get("source_ref")))
        seen_rooms.add(room.polygon)
        if not room_findings and not duplicate:
            usable_room_ids.add(room.id)
        if room.confidence < LOW_CONFIDENCE_THRESHOLD:
            findings.append(make_finding("PARSE_LOW_CONFIDENCE", "room confidence below threshold", source_ref=room.provenance.get("source_ref")))

    for left in range(len(geometry.rooms)):
        for right in range(left + 1, len(geometry.rooms)):
            findings.extend(_room_pair_warning(geometry.rooms[left], geometry.rooms[right]))

    seen_openings: set[tuple[str, str | None, tuple[float, float], float]] = set()
    for opening in geometry.openings:
        declared_wall_id = opening.wall_id
        if opening.provenance.get("source_kind") == "dxf" and declared_wall_id == _PENDING_DXF_WALL_ID:
            declared_wall_id = None
        _, opening_findings = resolve_opening_wall(
            geometry.walls, opening.center, opening.width_m, declared_wall_id, opening.span_m
        )
        findings.extend(opening_findings)
        # C-1 (spatial review, 2026-08-10): §7 requires collision/duplicate
        # geometry to fail (no suffix, no merge) for every entity kind, but
        # only walls and rooms were checked. Two coincident openings collide
        # on `id` (same identity tuple) with zero findings otherwise. Key on
        # the same (type, wall_id, center, width_m) tuple used by
        # normalize.py's `_opening_identity`.
        key = (opening.type, opening.wall_id, opening.center, opening.width_m)
        if key in seen_openings:
            findings.append(make_finding("PARSE_DUPLICATE_ENTITY", "duplicate opening geometry", source_ref=opening.provenance.get("source_ref")))
        seen_openings.add(key)
        if opening.confidence < LOW_CONFIDENCE_THRESHOLD:
            findings.append(make_finding("PARSE_LOW_CONFIDENCE", "opening confidence below threshold", source_ref=opening.provenance.get("source_ref")))

    for start, end, declared in geometry.dimensions_m:
        measured = Decimal(str(math.hypot(end[0] - start[0], end[1] - start[1])))
        declared_dec = Decimal(str(declared))
        tolerance = max(Decimal("0.02"), abs(declared_dec) * Decimal("0.01"))
        if abs(measured - declared_dec) > tolerance:
            findings.append(make_finding("PARSE_DIMENSION_INCONSISTENT", "declared dimension differs from measured geometry"))

    if geometry.walls and geometry.rooms and (not usable_wall_ids and not usable_room_ids):
        findings.append(make_finding("PARSE_EMPTY_GEOMETRY", "no usable geometry remains after validation"))

    return sort_findings(findings)
