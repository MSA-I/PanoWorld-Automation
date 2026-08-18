"""PLAN-004 adjacency graph and Map JSON draft (§7.7).

Edges encode room adjacency through shared doors: a door opening (type "door")
whose host wall separates two covered rooms produces an edge
[roomA_viewpoint, roomB_viewpoint]. start_viewpoint is the viewpoint of the
first room in deterministic order (sorted by room id).

A wall "separates" two rooms when it lies on the boundary of exactly two
distinct covered rooms. We detect boundary membership by a collinear-overlap
test: a room edge supports a wall if the wall centreline is collinear with the
edge (both wall endpoints within tolerance of the edge's infinite line) and
overlaps it (the wall's projection interval intersects the edge's interval).
This correctly handles walls that span the boundary of two abutting rooms.

The map.json draft follows the golden map_panoworld0.json shape:
{ "<start_id>": [<neighbor_ids...>] }.
"""

from __future__ import annotations

import math

from pwa.camera.findings import Finding, make_finding
from pwa.camera.types import SceneGeometry, Viewpoint

_COLLINEAR_TOLERANCE_M = 0.02


def _point_on_segment_line(point, a, b) -> float:
    """Perpendicular distance from ``point`` to the infinite line through a-b."""
    ax, ay = a
    bx, by = b
    px, py = point
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-12:
        return math.hypot(px - ax, py - ay)
    return abs(dy * px - dx * py + bx * ay - by * ax) / math.sqrt(length_sq)


def _project_t(point, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-12:
        return 0.0
    return ((point[0] - ax) * dx + (point[1] - ay) * dy) / math.sqrt(length_sq)


def _wall_on_room_boundary(wall, room) -> bool:
    """True if the wall centreline is collinear with and overlaps any edge of
    the room polygon."""
    for i, p in enumerate(room.polygon):
        q = room.polygon[(i + 1) % len(room.polygon)]
        # Collinearity: both wall endpoints near the edge's infinite line.
        if _point_on_segment_line(wall.start, p, q) > _COLLINEAR_TOLERANCE_M:
            continue
        if _point_on_segment_line(wall.end, p, q) > _COLLINEAR_TOLERANCE_M:
            continue
        # Overlap: wall's projected interval intersects the edge's [0, len].
        edge_len = math.hypot(q[0] - p[0], q[1] - p[1])
        t0 = _project_t(wall.start, p, q)
        t1 = _project_t(wall.end, p, q)
        tmin = min(t0, t1)
        tmax = max(t0, t1)
        if -_COLLINEAR_TOLERANCE_M <= tmin <= edge_len + _COLLINEAR_TOLERANCE_M and -_COLLINEAR_TOLERANCE_M <= tmax <= edge_len + _COLLINEAR_TOLERANCE_M:
            return True
    return False


def _rooms_adjacent_via_wall(geometry: SceneGeometry, wall_id: str, viewpoint_by_room: dict[str, Viewpoint]) -> tuple[str, str] | None:
    """Return (vpa, vpb) ids of the two covered rooms separated by the wall,
    or None if the wall does not separate exactly two distinct covered rooms."""
    host_walls = {w.id: w for w in geometry.walls}
    if wall_id not in host_walls:
        return None
    wall = host_walls[wall_id]
    room_ids = {
        room.id
        for room in geometry.rooms
        if room.id in viewpoint_by_room and _wall_on_room_boundary(wall, room)
    }
    if len(room_ids) != 2:
        return None
    ids = sorted(room_ids)
    return viewpoint_by_room[ids[0]].id, viewpoint_by_room[ids[1]].id


def build_adjacency(
    geometry: SceneGeometry,
    viewpoints: tuple[Viewpoint, ...],
) -> tuple[list[list[str]], str | None, list[Finding]]:
    """Return (edges, start_viewpoint, findings).

    edges are [[a, b], ...] with viewpoint ids. start_viewpoint is the
    viewpoint of the first room in deterministic order, or None when empty.
    """
    viewpoint_by_room = {vp.room_id: vp for vp in viewpoints}
    findings: list[Finding] = []
    edges: list[list[str]] = []
    seen_edges: set[frozenset] = set()

    doors = [o for o in geometry.openings if o.type == "door"]
    for door in sorted(doors, key=lambda o: o.id):
        pair = _rooms_adjacent_via_wall(geometry, door.wall_id, viewpoint_by_room)
        if pair is None:
            findings.append(make_finding("CAM_MAP_ADJACENCY_UNRESOLVED", "door does not resolve to two covered rooms", source_ref=door.id))
            continue
        edge = [pair[0], pair[1]]
        key = frozenset(edge)
        if key not in seen_edges:
            seen_edges.add(key)
            edges.append(edge)

    ordered_rooms = sorted(geometry.rooms, key=lambda r: r.id)
    start_viewpoint = None
    for room in ordered_rooms:
        if room.id in viewpoint_by_room:
            start_viewpoint = viewpoint_by_room[room.id].id
            break

    return edges, start_viewpoint, findings