"""Frozen in-memory floorplan types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pwa.floorplan.findings import Finding

Point = tuple[float, float]


@dataclass(frozen=True)
class SourceFrame:
    kind: Literal["dxf", "raster"]
    unit_scale_m: float
    y_down: bool
    height_px: int | None
    source_units: str


@dataclass(frozen=True)
class RawWall:
    index: int
    source_ref: str
    start: Point
    end: Point


@dataclass(frozen=True)
class RawRoom:
    index: int
    source_ref: str
    polygon: tuple[Point, ...]


@dataclass(frozen=True)
class RawOpening:
    index: int
    source_ref: str
    kind: Literal["door", "window"]
    center: Point
    width_m: float
    span: tuple[Point, Point] | None
    wall_index: int | None


@dataclass(frozen=True)
class RawDimension:
    index: int
    source_ref: str
    a: Point
    b: Point
    declared_length_m: float


@dataclass(frozen=True)
class RawGeometry:
    frame: SourceFrame
    walls: tuple[RawWall, ...]
    rooms: tuple[RawRoom, ...]
    openings: tuple[RawOpening, ...]
    dimensions: tuple[RawDimension, ...]
    scanned_entities: int
    unmapped: tuple[Finding, ...]
    errors: tuple[Finding, ...] = ()


@dataclass(frozen=True)
class NormWall:
    id: str
    start: Point
    end: Point
    confidence: float
    provenance: dict


@dataclass(frozen=True)
class NormRoom:
    id: str
    polygon: tuple[Point, ...]
    confidence: float
    provenance: dict


@dataclass(frozen=True)
class NormOpening:
    id: str
    type: Literal["door", "window"]
    wall_id: str | None
    center: Point
    width_m: float
    confidence: float
    provenance: dict
    # Normalized (metric, post-translation) opening span, DXF-only. Not
    # serialized into the schema-validated payload -- it exists purely so
    # validate() can re-check §6 collinearity without re-deriving metric
    # coordinates from the raw (source-unit) provenance span. None for the
    # annotation adapter, which never carries an opening span at all.
    span_m: tuple[Point, Point] | None = None


@dataclass(frozen=True)
class NormalizedGeometry:
    units: Literal["m"]
    walls: tuple[NormWall, ...]
    rooms: tuple[NormRoom, ...]
    openings: tuple[NormOpening, ...]
    dimensions_m: tuple[tuple[Point, Point, float], ...]
    normalization: dict
    frame: SourceFrame
