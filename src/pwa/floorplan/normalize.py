"""Deterministic normalization and canonical projection."""

from __future__ import annotations

import hashlib
import math
from decimal import Decimal, ROUND_HALF_EVEN

from pwa.floorplan.config import DIMENSION_TIE_M, MAX_COORDINATE_MAGNITUDE_M, OPENING_OFFSET_M, QUANTUM_M
from pwa.floorplan.findings import FloorplanError
from pwa.floorplan.types import (
    NormOpening,
    NormRoom,
    NormWall,
    NormalizedGeometry,
    Point,
    RawGeometry,
)

_QUANTUM = Decimal("0.0001")


def q(value: float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)


def emit(value: Decimal) -> float:
    return 0.0 if value == 0 else float(value)


def key(value: Decimal) -> str:
    return "0.0000" if value == 0 else f"{value:.4f}"


def _point_key(point: tuple[Decimal, Decimal]) -> tuple[Decimal, Decimal]:
    return point[0], point[1]


def _to_metric(raw: tuple[float, float], frame) -> tuple[Decimal, Decimal]:
    if not math.isfinite(raw[0]) or not math.isfinite(raw[1]):
        raise FloorplanError("PARSE_RESOURCE_LIMIT", "source coordinates must be finite")
    x = q(Decimal(str(raw[0])) * Decimal(str(frame.unit_scale_m)))
    if frame.y_down:
        if frame.height_px is None:
            raise FloorplanError("PARSE_RESOURCE_LIMIT", "raster source missing height")
        y = q((Decimal(str(frame.height_px)) - Decimal(str(raw[1]))) * Decimal(str(frame.unit_scale_m)))
    else:
        y = q(Decimal(str(raw[1])) * Decimal(str(frame.unit_scale_m)))
    if abs(x) > Decimal(str(MAX_COORDINATE_MAGNITUDE_M)) or abs(y) > Decimal(str(MAX_COORDINATE_MAGNITUDE_M)):
        raise FloorplanError("PARSE_RESOURCE_LIMIT", "normalized coordinates exceed configured bounds")
    return x, y


def _normalize_point(point: tuple[Decimal, Decimal], tx: Decimal, ty: Decimal) -> tuple[Decimal, Decimal]:
    x = q(point[0] - tx)
    y = q(point[1] - ty)
    # m-8 (spatial review, 2026-08-10): MAX_COORDINATE_MAGNITUDE_M was only
    # checked pre-translation (in _to_metric). Geometry whose individual
    # endpoints are each within bounds can still land far outside the bound
    # once translated relative to the anchor (e.g. x in [-99000, 99000] ->
    # translated span up to 198000). Re-check post-translation too.
    if abs(x) > Decimal(str(MAX_COORDINATE_MAGNITUDE_M)) or abs(y) > Decimal(str(MAX_COORDINATE_MAGNITUDE_M)):
        raise FloorplanError("PARSE_RESOURCE_LIMIT", "normalized coordinates exceed configured bounds")
    return x, y


def _polygon_area(points: tuple[tuple[Decimal, Decimal], ...]) -> Decimal:
    total = Decimal("0")
    for index, point in enumerate(points):
        nxt = points[(index + 1) % len(points)]
        total += (point[0] * nxt[1]) - (nxt[0] * point[1])
    return total / Decimal("2")


def _canonical_polygon(points: tuple[tuple[Decimal, Decimal], ...]) -> tuple[tuple[Decimal, Decimal], ...]:
    if points[0] == points[-1]:
        points = points[:-1]
    area = _polygon_area(points)
    if area < 0:
        points = tuple(reversed(points))
    rotations = [points[index:] + points[:index] for index in range(len(points))]
    return min(rotations, key=lambda candidate: tuple(_point_key(p) for p in candidate))


def _wall_identity(start: tuple[Decimal, Decimal], end: tuple[Decimal, Decimal]) -> str:
    encoded = f"wall|{key(start[0])}|{key(start[1])}|{key(end[0])}|{key(end[1])}".encode("utf-8")
    return "w-" + hashlib.sha256(encoded).hexdigest()[:12]


def _room_identity(polygon: tuple[tuple[Decimal, Decimal], ...]) -> str:
    coords = [key(component) for point in polygon for component in point]
    encoded = f"room|{'|'.join(coords)}".encode("utf-8")
    return "r-" + hashlib.sha256(encoded).hexdigest()[:12]


def _opening_identity(kind: str, wall_id: str | None, center: tuple[Decimal, Decimal], width_m: Decimal) -> str:
    encoded = (
        f"opening|{kind}|{wall_id or '__pending__'}|{key(center[0])}|{key(center[1])}|{key(width_m)}".encode("utf-8")
    )
    return "o-" + hashlib.sha256(encoded).hexdigest()[:12]


_PENDING_DXF_WALL_ID = "__dxf_probe__"


def _span_collinear_with_wall(span: tuple[tuple[float, float], tuple[float, float]], sx: float, sy: float, ux: float, uy: float) -> bool:
    # §6: "Every opening line must be collinear with exactly one wall segment
    # within tolerance." Both span endpoints (not just the opening centre)
    # must lie within OPENING_OFFSET_M of the wall's infinite line.
    for point in span:
        dx = point[0] - sx
        dy = point[1] - sy
        if abs(dx * uy - dy * ux) > OPENING_OFFSET_M:
            return False
    return True


def _resolve_wall_id(
    walls: tuple[NormWall, ...],
    center: tuple[Decimal, Decimal],
    span: tuple[tuple[Decimal, Decimal], tuple[Decimal, Decimal]] | None = None,
) -> str:
    candidates: list[tuple[float, str]] = []
    cx = emit(center[0])
    cy = emit(center[1])
    span_float = (
        ((emit(span[0][0]), emit(span[0][1])), (emit(span[1][0]), emit(span[1][1])))
        if span is not None
        else None
    )
    for wall in walls:
        sx, sy = wall.start
        ex, ey = wall.end
        vx = ex - sx
        vy = ey - sy
        length = math.hypot(vx, vy)
        if length == 0:
            continue
        ux = vx / length
        uy = vy / length
        dx = cx - sx
        dy = cy - sy
        t = dx * ux + dy * uy
        distance = abs(dx * uy - dy * ux)
        if distance <= OPENING_OFFSET_M and -QUANTUM_M <= t <= length + QUANTUM_M:
            if span_float is not None and not _span_collinear_with_wall(span_float, sx, sy, ux, uy):
                continue
            candidates.append((t, wall.id))
    if len(candidates) == 0:
        raise FloorplanError("PARSE_UNKNOWN_WALL_REF", "opening does not resolve to any wall")
    if len(candidates) > 1:
        raise FloorplanError("PARSE_AMBIGUOUS_WALL_REF", "opening resolves to multiple walls")
    return candidates[0][1]


def _projected_opening_width_m(
    span: tuple[tuple[Decimal, Decimal], tuple[Decimal, Decimal]],
    wall: NormWall,
) -> Decimal:
    """GC-6 (PLAN-002 revision 2, 2026-08-10): §6 now requires opening width
    to be the span projected onto the matched wall's direction, computed
    AFTER wall resolution succeeds -- not the raw span length. The
    independent OpenAI review showed the raw length diverges without bound
    as the span shortens (a 0.05 m span within the OPENING_OFFSET_M=0.02
    endpoint tolerance projects to 0.03 m, a 67% excess) and can even flip
    PARSE_OPENING_WIDTH_EXCEEDS_WALL at a realistic 0.9 m opening. Project
    each span endpoint onto the wall's unit direction vector (the same "t"
    parameter used to resolve/validate the wall match) and take the
    difference -- this is exactly the wall-parallel extent of the opening,
    independent of any perpendicular offset noise in the raw span.
    """
    sx, sy = wall.start
    ex, ey = wall.end
    vx = ex - sx
    vy = ey - sy
    length = math.hypot(vx, vy)
    ux = vx / length
    uy = vy / length
    p0x, p0y = emit(span[0][0]), emit(span[0][1])
    p1x, p1y = emit(span[1][0]), emit(span[1][1])
    t0 = (p0x - sx) * ux + (p0y - sy) * uy
    t1 = (p1x - sx) * ux + (p1y - sy) * uy
    return q(abs(t1 - t0))


def _points_match(left: tuple[float, float], right: tuple[float, float], *, tolerance: float = DIMENSION_TIE_M) -> bool:
    return abs(left[0] - right[0]) <= tolerance and abs(left[1] - right[1]) <= tolerance


def _dimension_tied_entities(
    *,
    raw: RawGeometry,
    walls: list[NormWall],
    rooms: list[NormRoom],
    dimensions: list[tuple[tuple[float, float], tuple[float, float], float]],
) -> tuple[set[str], set[str]]:
    tied_walls: set[str] = set()
    tied_rooms: set[str] = set()
    if raw.frame.kind != "raster":
        return tied_walls, tied_rooms
    for start, end, declared in dimensions:
        measured = math.hypot(end[0] - start[0], end[1] - start[1])
        tolerance = max(0.02, abs(declared) * 0.01)
        if abs(measured - declared) > tolerance:
            continue
        for wall in walls:
            if (
                (_points_match(wall.start, start) and _points_match(wall.end, end))
                or (_points_match(wall.start, end) and _points_match(wall.end, start))
            ):
                tied_walls.add(wall.id)
        for room in rooms:
            has_start = any(_points_match(vertex, start) for vertex in room.polygon)
            has_end = any(_points_match(vertex, end) for vertex in room.polygon)
            if has_start and has_end:
                tied_rooms.add(room.id)
    return tied_walls, tied_rooms


def normalize(raw: RawGeometry) -> NormalizedGeometry:
    walls_metric = []
    for wall in raw.walls:
        start = _to_metric(wall.start, raw.frame)
        end = _to_metric(wall.end, raw.frame)
        if _point_key(end) < _point_key(start):
            start, end = end, start
        walls_metric.append((wall, start, end))
    tx = min(point[0] for _, start, end in walls_metric for point in (start, end))
    ty = min(point[1] for _, start, end in walls_metric for point in (start, end))

    normalized_walls: list[NormWall] = []
    raw_wall_ids: dict[int, str] = {}
    for wall, start, end in sorted(walls_metric, key=lambda item: (*item[1], *item[2])):
        norm_start = _normalize_point(start, tx, ty)
        norm_end = _normalize_point(end, tx, ty)
        wall_id = _wall_identity(norm_start, norm_end)
        raw_wall_ids[wall.index] = wall_id
        normalized_walls.append(
            NormWall(
                id=wall_id,
                start=(emit(norm_start[0]), emit(norm_start[1])),
                end=(emit(norm_end[0]), emit(norm_end[1])),
                confidence=1.0,
                provenance={
                    "source_kind": raw.frame.kind if raw.frame.kind == "dxf" else "annotation",
                    "source_ref": wall.source_ref,
                    "source_start": [wall.start[0], wall.start[1]],
                    "source_end": [wall.end[0], wall.end[1]],
                },
            )
        )

    normalized_rooms: list[NormRoom] = []
    for room in sorted(raw.rooms, key=lambda item: item.source_ref):
        polygon = tuple(_normalize_point(_to_metric(point, raw.frame), tx, ty) for point in room.polygon)
        canonical = _canonical_polygon(polygon)
        normalized_rooms.append(
            NormRoom(
                id=_room_identity(canonical),
                polygon=tuple((emit(x), emit(y)) for x, y in canonical),
                confidence=1.0,
                provenance={
                    "source_kind": raw.frame.kind if raw.frame.kind == "dxf" else "annotation",
                    "source_ref": room.source_ref,
                    "source_polygon": [[point[0], point[1]] for point in room.polygon],
                },
            )
        )
    normalized_rooms.sort(key=lambda room: tuple(component for point in room.polygon for component in point))

    normalized_openings: list[NormOpening] = []
    for opening in raw.openings:
        if not math.isfinite(opening.width_m) or opening.width_m <= 0:
            raise FloorplanError("PARSE_RESOURCE_LIMIT", "opening width must be finite and positive", source_ref=opening.source_ref)
        center = _normalize_point(_to_metric(opening.center, raw.frame), tx, ty)
        span_decimal: tuple[tuple[Decimal, Decimal], tuple[Decimal, Decimal]] | None = None
        if opening.span is not None:
            span_decimal = (
                _normalize_point(_to_metric(opening.span[0], raw.frame), tx, ty),
                _normalize_point(_to_metric(opening.span[1], raw.frame), tx, ty),
            )
        span_metric: tuple[Point, Point] | None = (
            ((emit(span_decimal[0][0]), emit(span_decimal[0][1])), (emit(span_decimal[1][0]), emit(span_decimal[1][1])))
            if span_decimal is not None
            else None
        )
        if opening.wall_index is None:
            try:
                wall_id = _resolve_wall_id(tuple(normalized_walls), center, span_decimal)
            except FloorplanError as exc:
                if exc.finding.code in {"PARSE_UNKNOWN_WALL_REF", "PARSE_AMBIGUOUS_WALL_REF"}:
                    wall_id = _PENDING_DXF_WALL_ID
                else:
                    raise
        else:
            wall_id = raw_wall_ids.get(opening.wall_index, f"__missing_wall_index__:{opening.wall_index}")

        # GC-6: width is derived from the span projected onto the matched
        # wall, computed only now that wall resolution has succeeded. This
        # only applies to adapters that carry a raw span (DXF); annotation
        # openings have no span geometry to project and keep their declared
        # metre width, as do DXF openings whose wall resolution is still
        # pending (validate() will re-check and raise the appropriate
        # PARSE_UNKNOWN_WALL_REF/PARSE_AMBIGUOUS_WALL_REF finding for those).
        matched_wall = (
            next((wall for wall in normalized_walls if wall.id == wall_id), None)
            if span_decimal is not None and wall_id != _PENDING_DXF_WALL_ID
            else None
        )
        if matched_wall is not None:
            width_m = _projected_opening_width_m(span_decimal, matched_wall)
        else:
            width_m = q(opening.width_m)
        if width_m <= 0:
            # A span that is collinear-enough to resolve to a wall but has
            # (near-)zero extent along that wall's direction (e.g. a line
            # drawn perpendicular to, and centred on, the wall) is a
            # degenerate opening, not a valid zero/negative-width one. Reuse
            # the same finding already used above for a non-finite/
            # non-positive declared width rather than emitting a degenerate
            # opening or inventing a new error code.
            raise FloorplanError(
                "PARSE_RESOURCE_LIMIT",
                "opening width must be finite and positive",
                source_ref=opening.source_ref,
            )
        normalized_openings.append(
            NormOpening(
                id=_opening_identity(opening.kind, wall_id, center, width_m),
                type=opening.kind,
                wall_id=wall_id,
                center=(emit(center[0]), emit(center[1])),
                width_m=emit(width_m),
                confidence=1.0,
                span_m=span_metric,
                provenance={
                    "source_kind": raw.frame.kind if raw.frame.kind == "dxf" else "annotation",
                    "source_ref": opening.source_ref,
                    "source_center": [opening.center[0], opening.center[1]],
                    **(
                        {"source_span": [[opening.span[0][0], opening.span[0][1]], [opening.span[1][0], opening.span[1][1]]]}
                        if opening.span is not None
                        else {}
                    ),
                },
            )
        )
    normalized_openings.sort(key=lambda item: (item.center[0], item.center[1], item.width_m, item.type, item.wall_id))

    dimensions = []
    for dimension in raw.dimensions:
        a = _normalize_point(_to_metric(dimension.a, raw.frame), tx, ty)
        b = _normalize_point(_to_metric(dimension.b, raw.frame), tx, ty)
        dimensions.append(((emit(a[0]), emit(a[1])), (emit(b[0]), emit(b[1])), emit(q(dimension.declared_length_m))))

    tied_walls, tied_rooms = _dimension_tied_entities(
        raw=raw,
        walls=normalized_walls,
        rooms=normalized_rooms,
        dimensions=dimensions,
    )
    if raw.frame.kind == "raster":
        normalized_walls = [
            NormWall(wall.id, wall.start, wall.end, 0.9 if wall.id in tied_walls else 0.6, wall.provenance)
            for wall in normalized_walls
        ]
        normalized_rooms = [
            NormRoom(room.id, room.polygon, 0.9 if room.id in tied_rooms else 0.6, room.provenance)
            for room in normalized_rooms
        ]
        wall_confidence = {wall.id: wall.confidence for wall in normalized_walls}
        normalized_openings = [
            NormOpening(
                opening.id,
                opening.type,
                opening.wall_id,
                opening.center,
                opening.width_m,
                wall_confidence.get(opening.wall_id, 0.6),
                opening.provenance,
            )
            for opening in normalized_openings
        ]

    return NormalizedGeometry(
        units="m",
        walls=tuple(normalized_walls),
        rooms=tuple(normalized_rooms),
        openings=tuple(normalized_openings),
        dimensions_m=tuple(dimensions),
        normalization={
            "quantum_m": QUANTUM_M,
            "source_units": raw.frame.source_units,
            "source_unit_scale_m": raw.frame.unit_scale_m,
            "translation_m": [emit(tx), emit(ty)],
            "y_axis": "flipped_from_raster" if raw.frame.y_down else "up",
            "source_height_px": raw.frame.height_px,
            "scale_m_per_px": raw.frame.unit_scale_m if raw.frame.y_down else None,
        },
        frame=raw.frame,
    )


def canonical_projection(geometry: NormalizedGeometry) -> dict[str, object]:
    return {
        "units": geometry.units,
        "rooms": [[list(point) for point in room.polygon] for room in geometry.rooms],
        "walls": [[list(wall.start), list(wall.end)] for wall in geometry.walls],
        "openings": [
            [opening.type, opening.wall_id, list(opening.center), opening.width_m]
            for opening in geometry.openings
        ],
    }
