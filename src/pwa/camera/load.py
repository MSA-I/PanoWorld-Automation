"""Load one immutable scene_geometry 1.0.0 payload into SceneGeometry.

The payload is assumed schema-valid (the caller validates the envelope before
this runs); this loader only lifts the geometry fields and applies the
PLAN-004 resource bounds and finiteness guards. It does not mutate or renumber
anything — entity IDs are carried through verbatim.
"""

from __future__ import annotations

import math

from pwa.camera.config import MAX_COORDINATE_MAGNITUDE_M, MAX_OPENINGS, MAX_POLYGON_VERTICES, MAX_ROOMS
from pwa.camera.findings import CameraError
from pwa.camera.types import Opening, Room, SceneGeometry, Wall


def _finite_point(value: object, source_ref: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise CameraError("CAM_RESOURCE_LIMIT", "coordinate must be a 2-element array", source_ref=source_ref)
    x, y = value
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise CameraError("CAM_RESOURCE_LIMIT", "coordinates must be numeric", source_ref=source_ref)
    if not math.isfinite(float(x)) or not math.isfinite(float(y)):
        raise CameraError("CAM_RESOURCE_LIMIT", "coordinates must be finite", source_ref=source_ref)
    if abs(float(x)) > MAX_COORDINATE_MAGNITUDE_M or abs(float(y)) > MAX_COORDINATE_MAGNITUDE_M:
        raise CameraError("CAM_RESOURCE_LIMIT", "coordinates exceed configured bounds", source_ref=source_ref)
    return float(x), float(y)


def _string(value: object, field: str, source_ref: str) -> str:
    if not isinstance(value, str) or not value:
        raise CameraError("CAM_RESOURCE_LIMIT", f"{field} must be a non-empty string", source_ref=source_ref)
    return value


def load_scene_geometry(payload: dict) -> SceneGeometry:
    """Extract the planner projection from a `scene_geometry` 1.0.0 payload."""
    rooms = payload.get("rooms") or []
    walls = payload.get("walls") or []
    openings = payload.get("openings") or []
    if not isinstance(rooms, list) or not isinstance(walls, list) or not isinstance(openings, list):
        raise CameraError("CAM_RESOURCE_LIMIT", "geometry arrays must be lists")
    if len(rooms) > MAX_ROOMS or len(openings) > MAX_OPENINGS:
        raise CameraError("CAM_RESOURCE_LIMIT", "geometry exceeds configured entity limits")
    if not rooms:
        raise CameraError("CAM_EMPTY_GEOMETRY", "scene geometry payload contains no rooms")

    parsed_rooms: list[Room] = []
    for room in rooms:
        rid = _string(room.get("id"), "room.id", "room")
        polygon_raw = room.get("polygon")
        if not isinstance(polygon_raw, list) or len(polygon_raw) < 3:
            raise CameraError("CAM_RESOURCE_LIMIT", "room polygon must have at least 3 points", source_ref=rid)
        if len(polygon_raw) > MAX_POLYGON_VERTICES:
            raise CameraError("CAM_RESOURCE_LIMIT", "room polygon exceeds configured vertex limit", source_ref=rid)
        polygon = tuple(_finite_point(point, rid) for point in polygon_raw)
        parsed_rooms.append(Room(id=rid, polygon=polygon))

    parsed_walls: list[Wall] = []
    for wall in walls:
        wid = _string(wall.get("id"), "wall.id", "wall")
        start = _finite_point(wall.get("start"), wid)
        end = _finite_point(wall.get("end"), wid)
        thickness = wall.get("thickness_m")
        if not isinstance(thickness, (int, float)) or not math.isfinite(float(thickness)) or float(thickness) <= 0:
            raise CameraError("CAM_RESOURCE_LIMIT", "wall thickness_m must be positive and finite", source_ref=wid)
        parsed_walls.append(Wall(id=wid, start=start, end=end, thickness_m=float(thickness)))

    parsed_openings: list[Opening] = []
    for opening in openings:
        oid = _string(opening.get("id"), "opening.id", "opening")
        otype = opening.get("type")
        if otype not in {"door", "window"}:
            raise CameraError("CAM_RESOURCE_LIMIT", "opening type must be door or window", source_ref=oid)
        wall_id = _string(opening.get("wall_id"), "opening.wall_id", oid)
        center = _finite_point(opening.get("center"), oid)
        parsed_openings.append(Opening(id=oid, type=otype, wall_id=wall_id, center=center))

    return SceneGeometry(rooms=tuple(parsed_rooms), walls=tuple(parsed_walls), openings=tuple(parsed_openings))