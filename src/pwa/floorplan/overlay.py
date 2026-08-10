"""Deterministic source-aligned SVG overlay rendering."""

from __future__ import annotations

import base64
import json
from xml.sax.saxutils import escape, quoteattr

from pwa.floorplan.config import (
    MAX_OVERLAY_BYTES,
    MAX_SOURCE_PIXELS,
    MAX_SOURCE_RASTER_BYTES,
    OVERLAY_FONT_SIZE_FRACTION,
    OVERLAY_MARGIN_FRACTION,
    OVERLAY_OPENING_RADIUS_FRACTION,
    QUANTUM_M,
)
from pwa.floorplan.types import NormalizedGeometry


def fmt(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    if text in {"-0", "-0.0", ""}:
        return "0"
    return text


def _metadata(geometry: NormalizedGeometry, source: dict) -> str:
    return json.dumps(
        {
            "source_sha256": source["source_sha256"],
            "adapter": source["kind"],
            "quantum_m": QUANTUM_M,
            "normalization": geometry.normalization,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _inverse_raster(point: tuple[float, float], geometry: NormalizedGeometry) -> tuple[float, float]:
    scale = geometry.normalization["scale_m_per_px"]
    tx, ty = geometry.normalization["translation_m"]
    height = geometry.normalization["source_height_px"]
    x = (point[0] + tx) / scale
    y = height - ((point[1] + ty) / scale)
    return x, y


def _inverse_dxf(point: tuple[float, float], geometry: NormalizedGeometry) -> tuple[float, float]:
    scale = geometry.normalization["source_unit_scale_m"]
    tx, ty = geometry.normalization["translation_m"]
    return (point[0] + tx) / scale, (point[1] + ty) / scale


def _legend_lines(source: dict) -> list[str]:
    labels = [str(label) for label in source.get("labels", []) if str(label)]
    if not labels:
        return ['<g id="legend"></g>']
    lines = ['<g id="legend">']
    for index, label in enumerate(labels):
        lines.append(f'<text x="8" y="{20 + (index * 16)}">{escape(label)}</text>')
    lines.append("</g>")
    return lines


def _ids_and_confidence_lines(
    geometry: NormalizedGeometry, inverse, *, font_size: float | None = None
) -> tuple[list[str], list[str]]:
    """m-9 (spatial review, 2026-08-10): `#ids`/`#confidence` used to be
    unconditional empty placeholder groups in both renderers -- the letter
    of §10 ("layers distinguish ... IDs, confidence ...") was satisfied
    while carrying no actual information. Render each entity's id and
    confidence as deterministically-ordered, XML-escaped <text> labels at
    the entity's own inverse-transformed anchor, so a human G1 reviewer can
    tell e.g. a 0.6-confidence annotated wall from a 1.0 DXF wall.

    D (OpenAI cross-provider rework review, 2026-08-10): an explicit
    ``font_size`` (source units) may be supplied so the DXF renderer -- whose
    viewBox is real-world units, not pixels -- does not fall back to an
    SVG-default text size that would dwarf a small metre-scale plan. The
    raster renderer keeps passing ``None`` (unchanged, pixel viewBoxes make
    the default size reasonable already).
    """
    font_attr = f' font-size="{fmt(font_size)}"' if font_size is not None else ""
    id_lines = ['<g id="ids">']
    confidence_lines = ['<g id="confidence">']
    for wall in geometry.walls:
        anchor = inverse(((wall.start[0] + wall.end[0]) / 2, (wall.start[1] + wall.end[1]) / 2), geometry)
        id_lines.append(f'<text x="{fmt(anchor[0])}" y="{fmt(anchor[1])}"{font_attr}>{escape(wall.id)}</text>')
        confidence_lines.append(f'<text x="{fmt(anchor[0])}" y="{fmt(anchor[1])}"{font_attr}>{fmt(wall.confidence)}</text>')
    for room in geometry.rooms:
        cx = sum(point[0] for point in room.polygon) / len(room.polygon)
        cy = sum(point[1] for point in room.polygon) / len(room.polygon)
        anchor = inverse((cx, cy), geometry)
        id_lines.append(f'<text x="{fmt(anchor[0])}" y="{fmt(anchor[1])}"{font_attr}>{escape(room.id)}</text>')
        confidence_lines.append(f'<text x="{fmt(anchor[0])}" y="{fmt(anchor[1])}"{font_attr}>{fmt(room.confidence)}</text>')
    for opening in geometry.openings:
        anchor = inverse(opening.center, geometry)
        id_lines.append(f'<text x="{fmt(anchor[0])}" y="{fmt(anchor[1])}"{font_attr}>{escape(opening.id)}</text>')
        confidence_lines.append(f'<text x="{fmt(anchor[0])}" y="{fmt(anchor[1])}"{font_attr}>{fmt(opening.confidence)}</text>')
    id_lines.append("</g>")
    confidence_lines.append("</g>")
    return id_lines, confidence_lines


def _raster_svg(geometry: NormalizedGeometry, source: dict) -> bytes:
    image_bytes = source["image_bytes"]
    if len(image_bytes) > MAX_SOURCE_RASTER_BYTES:
        raise ValueError("source_raster_exceeds_limits")
    width = source["width_px"]
    height = source["height_px"]
    if width * height > MAX_SOURCE_PIXELS:
        raise ValueError("source_raster_exceeds_limits")
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    # m-4 / M-5 (code+spatial review, 2026-08-10): derive the media type from
    # the verified source bytes instead of hardcoding image/png -- a JPEG
    # source declared as image/png fails to render in strict SVG
    # rasterizers that honour the declared MIME type.
    media_type = source.get("media_type", "image/png")
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        f"<metadata>{escape(_metadata(geometry, source))}</metadata>",
        f'<g id="source"><image x="0" y="0" width="{width}" height="{height}" href="data:{media_type};base64,{image_b64}"/></g>',
        '<g id="walls">',
    ]
    for wall in geometry.walls:
        start = _inverse_raster(wall.start, geometry)
        end = _inverse_raster(wall.end, geometry)
        lines.append(
            f'<polyline points="{fmt(start[0])},{fmt(start[1])} {fmt(end[0])},{fmt(end[1])}" stroke="#14532d" fill="none"/>'
        )
    lines.append("</g>")
    lines.append('<g id="rooms">')
    for room in geometry.rooms:
        points = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (_inverse_raster(point, geometry) for point in room.polygon))
        lines.append(f'<polygon points="{points}" fill="none" stroke="#2563eb"/>')
    lines.append("</g>")
    lines.append('<g id="doors">')
    for opening in geometry.openings:
        if opening.type != "door":
            continue
        center = _inverse_raster(opening.center, geometry)
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="6" fill="#b45309" data-center="{fmt(center[0])},{fmt(center[1])}"/>'
        )
    lines.append("</g>")
    lines.append('<g id="windows">')
    for opening in geometry.openings:
        if opening.type != "window":
            continue
        center = _inverse_raster(opening.center, geometry)
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="6" fill="#0891b2" data-center="{fmt(center[0])},{fmt(center[1])}"/>'
        )
    lines.append("</g>")
    id_lines, confidence_lines = _ids_and_confidence_lines(geometry, _inverse_raster)
    lines.extend(id_lines)
    lines.extend(confidence_lines)
    lines.extend(_legend_lines(source))
    lines.append("</svg>\n")
    svg = "\n".join(lines).encode("utf-8")
    if len(svg) > MAX_OVERLAY_BYTES:
        raise ValueError("overlay_exceeds_max_bytes")
    return svg


def _primitive_points(primitive: dict) -> list[tuple[float, float]]:
    if primitive["type"] == "polyline":
        return [(point[0], point[1]) for point in primitive["points"]]
    return [(primitive["start"][0], primitive["start"][1]), (primitive["end"][0], primitive["end"][1])]


def _dxf_svg(geometry: NormalizedGeometry, source: dict) -> bytes:
    primitives = source["primitives"]
    xs = [point[0] for primitive in primitives for point in _primitive_points(primitive)]
    ys = [point[1] for primitive in primitives for point in _primitive_points(primitive)]
    # D (OpenAI cross-provider rework review, 2026-08-10): bounds used to come
    # only from the source primitives, so a normalized detection that
    # genuinely disagrees with the source enough to fall outside those bounds
    # was silently clipped and invisible -- precisely the disagreement this
    # overlay exists to reveal. Extend the bounds to also cover every
    # normalized wall/room/opening point, inverse-transformed back into the
    # same source-unit space the primitives are already in.
    detected_points = [_inverse_dxf(point, geometry) for wall in geometry.walls for point in (wall.start, wall.end)]
    detected_points.extend(_inverse_dxf(point, geometry) for room in geometry.rooms for point in room.polygon)
    detected_points.extend(_inverse_dxf(opening.center, geometry) for opening in geometry.openings)
    xs.extend(point[0] for point in detected_points)
    ys.extend(point[1] for point in detected_points)
    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)
    margin = OVERLAY_MARGIN_FRACTION * max(max_x - min_x, max_y - min_y)
    width = (max_x - min_x) + (2 * margin)
    height = (max_y - min_y) + (2 * margin)
    # D: the opening-marker radius and id/confidence label font-size used to
    # be fixed source-unit magic numbers (r="20", SVG-default text size).
    # For a metre-unit DXF that dwarfs the whole plan; scale both with the
    # geometry extent instead, mirroring how the margin itself is computed.
    opening_radius = OVERLAY_OPENING_RADIUS_FRACTION * max(width, height)
    font_size = OVERLAY_FONT_SIZE_FRACTION * max(width, height)

    def map_source(point: tuple[float, float]) -> tuple[float, float]:
        return point[0] - (min_x - margin), (max_y + margin) - point[1]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(width)} {fmt(height)}">',
        f"<metadata>{escape(_metadata(geometry, source))}</metadata>",
        '<g id="source">',
    ]
    for primitive in primitives:
        points = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (map_source(point) for point in _primitive_points(primitive)))
        if primitive["type"] == "polyline":
            lines.append(f'<polygon points="{points}" fill="none" stroke="#94a3b8"/>')
        else:
            lines.append(f'<polyline points="{points}" stroke="#94a3b8" fill="none"/>')
    lines.append("</g>")
    lines.append('<g id="walls">')
    for wall in geometry.walls:
        start = map_source(_inverse_dxf(wall.start, geometry))
        end = map_source(_inverse_dxf(wall.end, geometry))
        lines.append(
            f'<polyline points="{fmt(start[0])},{fmt(start[1])} {fmt(end[0])},{fmt(end[1])}" stroke="#14532d" fill="none"/>'
        )
    lines.append("</g>")
    # M-4 / M-11 (spatial + code review, 2026-08-10): rooms and doors used to
    # be unconditional empty placeholder groups for the DXF renderer -- 4 of
    # 11 Layer-A detections were simply missing from the overlay a human
    # reviews at the §20 visual-evidence gate. Render them the same way the
    # raster renderer does.
    lines.append('<g id="rooms">')
    for room in geometry.rooms:
        points = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (map_source(_inverse_dxf(point, geometry)) for point in room.polygon))
        lines.append(f'<polygon points="{points}" fill="none" stroke="#2563eb"/>')
    lines.append("</g>")
    lines.append('<g id="doors">')
    for opening in geometry.openings:
        if opening.type != "door":
            continue
        center = map_source(_inverse_dxf(opening.center, geometry))
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(opening_radius)}" fill="#b45309" data-center="{fmt(center[0])},{fmt(center[1])}"/>'
        )
    lines.append("</g>")
    lines.append('<g id="windows">')
    for opening in geometry.openings:
        if opening.type != "window":
            continue
        center = map_source(_inverse_dxf(opening.center, geometry))
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(opening_radius)}" fill="#0891b2" data-center="{fmt(center[0])},{fmt(center[1])}"/>'
        )
    lines.append("</g>")
    id_lines, confidence_lines = _ids_and_confidence_lines(
        geometry, lambda point, geom: map_source(_inverse_dxf(point, geom)), font_size=font_size
    )
    lines.extend(id_lines)
    lines.extend(confidence_lines)
    lines.extend(_legend_lines(source))
    lines.append("</svg>\n")
    svg = "\n".join(lines).encode("utf-8")
    if len(svg) > MAX_OVERLAY_BYTES:
        raise ValueError("overlay_exceeds_max_bytes")
    return svg


def render_overlay(geometry: NormalizedGeometry, source: dict) -> bytes:
    if source["kind"] == "raster":
        return _raster_svg(geometry, source)
    if source["kind"] == "dxf":
        return _dxf_svg(geometry, source)
    raise ValueError(f"unsupported overlay source kind: {quoteattr(str(source['kind']))}")
