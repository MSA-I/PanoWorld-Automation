"""PLAN-003 geometry compiler: parse projection → compiled scene_geometry.

Pure, deterministic Python. Applies the §7 normative geometry:
- walls gain thickness_m (default 0.10 m) and height_m (2.60 m)
- openings gain height_m/sill_m (door 2.10/0.00; window 1.20/0.90)
- doors take depth == host wall thickness
- ID derivation is stable per input (content-derived), matching PLAN-002's
  content-hash rule; a collision fails closed (GEOM_DUPLICATE_ENTITY).
"""

from __future__ import annotations

import hashlib

from pwa.geometry.config import (
    DEFAULT_CEILING_HEIGHT_M,
    DOOR_HEIGHT_M,
    DOOR_SILL_M,
    WALL_HEIGHT_M,
    WALL_THICKNESS_M,
    WINDOW_HEIGHT_M,
    WINDOW_SILL_M,
)
from pwa.geometry.findings import GeometryError, make_finding
from pwa.geometry.types import CompiledGeometry, GeoOpening, GeoRoom, GeoWall, ParseGeometry


def _fmt(value: float) -> str:
    return f"{value:.4f}"


def derive_wall_id(wall_id: str) -> str:
    """Stable geometry wall id derived from the stable input wall id."""
    digest = hashlib.sha256(f"geom-wall|{wall_id}".encode("utf-8")).hexdigest()
    return f"gw-{digest[:12]}"


def derive_room_id(room_id: str) -> str:
    digest = hashlib.sha256(f"geom-room|{room_id}".encode("utf-8")).hexdigest()
    return f"gr-{digest[:12]}"


def derive_opening_id(opening_id: str) -> str:
    digest = hashlib.sha256(f"geom-opening|{opening_id}".encode("utf-8")).hexdigest()
    return f"go-{digest[:12]}"


def _check_unique_ids(ids: list[str], kind: str) -> None:
    seen: set[str] = set()
    for entity_id in ids:
        if entity_id in seen:
            raise GeometryError(
                "GEOM_DUPLICATE_ENTITY",
                f"derived geometry {kind} id collision: {entity_id}",
                source_ref=entity_id,
            )
        seen.add(entity_id)


def build_walls(geometry: ParseGeometry) -> tuple[tuple[GeoWall, ...], dict[str, float]]:
    """Compile walls, returning walls and a thickness-by-input-id lookup.

    Per-wall thickness defaults to WALL_THICKNESS_M unless the parse wall
    carried an explicit (positive) thickness_m — the frozen 1.1.0 schema
    exposes that optional field but no Part-1 fixture fills it.
    """
    walls: list[GeoWall] = []
    thickness_by_input: dict[str, float] = {}
    for wall in geometry.walls:
        thick = wall.thickness_m if wall.thickness_m is not None else WALL_THICKNESS_M
        walls.append(
            GeoWall(
                id=derive_wall_id(wall.id),
                start=wall.start,
                end=wall.end,
                height_m=WALL_HEIGHT_M,
                thickness_m=thick,
            )
        )
        thickness_by_input[wall.id] = thick
    _check_unique_ids([w.id for w in walls], "wall")
    return tuple(walls), thickness_by_input


def build_rooms(geometry: ParseGeometry) -> tuple[GeoRoom, ...]:
    rooms = [
        GeoRoom(
            id=derive_room_id(room.id),
            polygon=room.polygon,
            floor_z=0.0,
            ceiling_z=DEFAULT_CEILING_HEIGHT_M,
        )
        for room in geometry.rooms
    ]
    _check_unique_ids([r.id for r in rooms], "room")
    return tuple(rooms)


def build_openings(
    geometry: ParseGeometry,
    thickness_by_input: dict[str, float],
    derived_wall_id_by_input: dict[str, str],
) -> tuple[GeoOpening, ...]:
    openings: list[GeoOpening] = []
    for opening in geometry.openings:
        if opening.type == "door":
            height_m = DOOR_HEIGHT_M
            sill_m = DOOR_SILL_M
        else:
            height_m = WINDOW_HEIGHT_M
            sill_m = WINDOW_SILL_M
        depth_m = thickness_by_input.get(opening.wall_id, WALL_THICKNESS_M)
        openings.append(
            GeoOpening(
                id=derive_opening_id(opening.id),
                type=opening.type,
                wall_id=derived_wall_id_by_input.get(opening.wall_id, opening.wall_id),
                center=opening.center,
                width_m=opening.width_m,
                height_m=height_m,
                sill_m=sill_m,
                depth_m=depth_m,
            )
        )
    _check_unique_ids([o.id for o in openings], "opening")
    return tuple(openings)


def compile_geometry(geometry: ParseGeometry) -> CompiledGeometry:
    """Compile a parsed projection into a scene_geometry white model."""
    walls, thickness_by_input = build_walls(geometry)
    derived_wall_id_by_input = {
        wall.id: derive_wall_id(wall.id) for wall in geometry.walls
    }
    rooms = build_rooms(geometry)
    openings = build_openings(geometry, thickness_by_input, derived_wall_id_by_input)
    return CompiledGeometry(
        units="m",
        up_axis="z",
        default_ceiling_height_m=DEFAULT_CEILING_HEIGHT_M,
        rooms=rooms,
        walls=walls,
        openings=openings,
    )


def assumption_entries(geometry: ParseGeometry) -> list[dict]:
    """Deterministic defaults applied, for assumptions.json (PLAN-003 §7/AC-2).

    Each entry follows the assumptions 1.0.0 entry shape
    (key/value/reason/source/requires_human_ack).
    """
    entries: list[dict] = []
    any_wall_defaulted = any(wall.thickness_m is None for wall in geometry.walls)

    def add(key: str, value: str, reason: str) -> None:
        entries.append(
            {
                "key": key,
                "value": value,
                "reason": reason,
                "source": "default",
                "requires_human_ack": False,
            }
        )

    add("wall.thickness_m", f"{WALL_THICKNESS_M:.2f}", "DR-001 interior wall thickness default")
    add("wall.height_m", f"{WALL_HEIGHT_M:.2f}", "full-height wall default")
    add(
        "default_ceiling_height_m",
        f"{DEFAULT_CEILING_HEIGHT_M:.2f}",
        "bound to wall height default (PLAN-003 review F3)",
    )
    add("door.height_m", f"{DOOR_HEIGHT_M:.2f}", "door head height default")
    add("door.sill_m", f"{DOOR_SILL_M:.2f}", "door sill at floor level")
    add("door.depth_m", "host_wall_thickness", "DR-001: door depth equals host wall thickness")
    add("window.height_m", f"{WINDOW_HEIGHT_M:.2f}", "window head height default")
    add("window.sill_m", f"{WINDOW_SILL_M:.2f}", "window sill height default")
    return entries
