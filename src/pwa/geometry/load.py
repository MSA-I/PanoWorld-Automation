"""Load one immutable floorplan_parse artifact into ParseGeometry."""

from __future__ import annotations

import math

from pwa.geometry.config import MAX_COORDINATE_MAGNITUDE_M, MAX_OPENINGS, MAX_POLYGON_VERTICES, MAX_ROOMS, MAX_WALLS
from pwa.geometry.findings import GeometryError
from pwa.geometry.types import ParseGeometry, ParseOpening, ParseRoom, ParseWall


def _finite_point(value: object, source_ref: str) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise GeometryError("GEOM_RESOURCE_LIMIT", "coordinate must be a 2-element array", source_ref=source_ref)
    x, y = value
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise GeometryError("GEOM_RESOURCE_LIMIT", "coordinates must be numeric", source_ref=source_ref)
    if not math.isfinite(float(x)) or not math.isfinite(float(y)):
        raise GeometryError("GEOM_RESOURCE_LIMIT", "coordinates must be finite", source_ref=source_ref)
    if abs(float(x)) > MAX_COORDINATE_MAGNITUDE_M or abs(float(y)) > MAX_COORDINATE_MAGNITUDE_M:
        raise GeometryError("GEOM_RESOURCE_LIMIT", "coordinates exceed configured bounds", source_ref=source_ref)
    return float(x), float(y)


def _string(value: object, field: str, source_ref: str) -> str:
    if not isinstance(value, str) or not value:
        raise GeometryError("GEOM_RESOURCE_LIMIT", f"{field} must be a non-empty string", source_ref=source_ref)
    return value


def load_parse_geometry(payload: dict) -> ParseGeometry:
    """Extract the canonical projection from a `floorplan_parse` 1.1.0 payload.

    The payload is assumed schema-valid (the caller validates the envelope
    before this runs); this loader only lifts the geometry fields and applies
    the PLAN-003 resource bounds and finiteness guards. It does not mutate or
    renumber anything — entity IDs are carried through verbatim.
    """
    walls = payload.get("walls") or []
    rooms = payload.get("rooms") or []
    openings = payload.get("openings") or []
    if not isinstance(walls, list) or not isinstance(rooms, list) or not isinstance(openings, list):
        raise GeometryError("GEOM_RESOURCE_LIMIT", "geometry arrays must be lists")
    if len(walls) > MAX_WALLS or len(rooms) > MAX_ROOMS or len(openings) > MAX_OPENINGS:
        raise GeometryError("GEOM_RESOURCE_LIMIT", "geometry exceeds configured entity limits")
    if not walls or not rooms:
        raise GeometryError("GEOM_EMPTY_GEOMETRY", "parse payload did not contain at least one wall and room")

    parsed_walls: list[ParseWall] = []
    for wall in walls:
        wid = _string(wall.get("id"), "wall.id", "wall")
        start = _finite_point(wall.get("start"), wid)
        end = _finite_point(wall.get("end"), wid)
        thickness = wall.get("thickness_m")
        if thickness is not None and (not isinstance(thickness, (int, float)) or not math.isfinite(float(thickness)) or float(thickness) <= 0):
            raise GeometryError("GEOM_RESOURCE_LIMIT", "wall thickness_m must be positive and finite", source_ref=wid)
        parsed_walls.append(
            ParseWall(
                id=wid,
                start=start,
                end=end,
                thickness_m=float(thickness) if thickness is not None else None,
            )
        )

    parsed_rooms: list[ParseRoom] = []
    for room in rooms:
        rid = _string(room.get("id"), "room.id", "room")
        polygon_raw = room.get("polygon")
        if not isinstance(polygon_raw, list) or len(polygon_raw) < 3:
            raise GeometryError("GEOM_RESOURCE_LIMIT", "room polygon must have at least 3 points", source_ref=rid)
        if len(polygon_raw) > MAX_POLYGON_VERTICES:
            raise GeometryError("GEOM_RESOURCE_LIMIT", "room polygon exceeds configured vertex limit", source_ref=rid)
        polygon = tuple(_finite_point(point, rid) for point in polygon_raw)
        parsed_rooms.append(ParseRoom(id=rid, polygon=polygon))

    parsed_openings: list[ParseOpening] = []
    for opening in openings:
        oid = _string(opening.get("id"), "opening.id", "opening")
        otype = opening.get("type")
        if otype not in {"door", "window"}:
            raise GeometryError("GEOM_RESOURCE_LIMIT", "opening type must be door or window", source_ref=oid)
        wall_id = _string(opening.get("wall_id"), "opening.wall_id", oid)
        center = _finite_point(opening.get("center"), oid)
        width_m = opening.get("width_m")
        if not isinstance(width_m, (int, float)) or not math.isfinite(float(width_m)) or float(width_m) <= 0:
            raise GeometryError("GEOM_RESOURCE_LIMIT", "opening width_m must be positive and finite", source_ref=oid)
        parsed_openings.append(
            ParseOpening(id=oid, type=otype, wall_id=wall_id, center=center, width_m=float(width_m))
        )

    return ParseGeometry(
        units="m",
        walls=tuple(parsed_walls),
        rooms=tuple(parsed_rooms),
        openings=tuple(parsed_openings),
    )
