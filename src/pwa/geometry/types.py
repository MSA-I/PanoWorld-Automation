"""In-memory PLAN-003 geometry types.

Input side mirrors the frozen `floorplan_parse` 1.1.0 payload; output side
mirrors the frozen `scene_geometry` 1.0.0 payload. Coordinates stay in the
same metre frame as the parse output (PLAN-003 §7.1: straight 2D→3D lift).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Point = tuple[float, float]


@dataclass(frozen=True)
class ParseWall:
    """A parse wall centreline (2D), plus the optional thickness if present."""

    id: str
    start: Point
    end: Point
    thickness_m: float | None


@dataclass(frozen=True)
class ParseRoom:
    id: str
    polygon: tuple[Point, ...]


@dataclass(frozen=True)
class ParseOpening:
    id: str
    type: Literal["door", "window"]
    wall_id: str
    center: Point
    width_m: float


@dataclass(frozen=True)
class ParseGeometry:
    """Canonical projection extracted from one immutable floorplan_parse doc."""

    units: Literal["m"]
    walls: tuple[ParseWall, ...]
    rooms: tuple[ParseRoom, ...]
    openings: tuple[ParseOpening, ...]


@dataclass(frozen=True)
class GeoWall:
    """A compiled solid wall: centreline + thickness + height (Z-up)."""

    id: str
    start: Point
    end: Point
    height_m: float
    thickness_m: float


@dataclass(frozen=True)
class GeoRoom:
    id: str
    polygon: tuple[Point, ...]
    floor_z: float
    ceiling_z: float


@dataclass(frozen=True)
class GeoOpening:
    id: str
    type: Literal["door", "window"]
    wall_id: str
    center: Point
    width_m: float
    height_m: float
    sill_m: float
    depth_m: float  # door depth == host wall thickness; window carries wall too


@dataclass(frozen=True)
class CompiledGeometry:
    units: Literal["m"]
    up_axis: Literal["z"]
    default_ceiling_height_m: float
    rooms: tuple[GeoRoom, ...]
    walls: tuple[GeoWall, ...]
    openings: tuple[GeoOpening, ...]
