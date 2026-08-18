"""In-memory PLAN-004 camera-planner types.

Input side mirrors the frozen `scene_geometry` 1.0.0 payload (rooms, walls,
openings); output side mirrors the frozen `camera_plan` 1.0.0 payload
(viewpoints, edges, start_viewpoint, resolution, batch). Coordinates stay in
the same metre Z-up frame as the geometry output (PLAN-004 §7.1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Point = tuple[float, float]


@dataclass(frozen=True)
class Room:
    id: str
    polygon: tuple[Point, ...]


@dataclass(frozen=True)
class Wall:
    id: str
    start: Point
    end: Point
    thickness_m: float


@dataclass(frozen=True)
class Opening:
    id: str
    type: Literal["door", "window"]
    wall_id: str
    center: Point


@dataclass(frozen=True)
class SceneGeometry:
    """The projection of a scene_geometry 1.0.0 payload the planner needs."""

    rooms: tuple[Room, ...]
    walls: tuple[Wall, ...]
    openings: tuple[Opening, ...]


@dataclass(frozen=True)
class Viewpoint:
    """A placed camera viewpoint (Z-up world, camera height applied)."""

    id: str
    position: Point  # floor-plane (x, y); camera z == camera_height_m
    yaw_rad: float
    room_id: str
    camera_height_m: float