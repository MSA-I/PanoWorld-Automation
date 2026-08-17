"""Top-down white-model overlay rendering (deterministic, no Blender).

Renders the compiled scene_geometry as a flat Z=0 top-down view: walls as
thick rectilinear strokes/boxes, rooms as outlined polygons, openings as
coloured markers. Produces both SVG (for the G2 gate) and a pinned PNG
rendering via Pillow. Fully deterministic: same compiled geometry → identical
bytes.
"""

from __future__ import annotations

import io

from PIL import Image, ImageDraw

from pwa.geometry.config import (
    MAX_OVERLAY_BYTES,
    OVERLAY_FONT_SIZE_FRACTION,
    OVERLAY_MARGIN_FRACTION,
    OVERLAY_OPENING_RADIUS_FRACTION,
    OVERLAY_PNG_SCALE,
)
from pwa.geometry.types import CompiledGeometry


def fmt(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    if text in {"-0", "-0.0", ""}:
        return "0"
    return text


def _bounds(compiled: CompiledGeometry) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for wall in compiled.walls:
        xs.extend((wall.start[0], wall.end[0]))
        ys.extend((wall.start[1], wall.end[1]))
    for room in compiled.rooms:
        for point in room.polygon:
            xs.append(point[0])
            ys.append(point[1])
    for opening in compiled.openings:
        xs.append(opening.center[0])
        ys.append(opening.center[1])
    if not xs:
        return 0.0, 0.0, 1.0, 1.0
    return min(xs), max(xs), min(ys), max(ys)


def _mapping(
    compiled: CompiledGeometry,
) -> tuple[float, float, callable]:
    """Return (width, height, coordinate mapper).

    The mapper transforms world (x, y) metres into SVG viewBox coordinates
    (y flipped so up is up on screen), matching PLAN-002's DXF overlay.
    """
    min_x, max_x, min_y, max_y = _bounds(compiled)
    extent = max(max_x - min_x, max_y - min_y, 1e-6)
    margin = OVERLAY_MARGIN_FRACTION * extent
    width = (max_x - min_x) + 2 * margin
    height = (max_y - min_y) + 2 * margin

    def mapper(point: tuple[float, float]) -> tuple[float, float]:
        x = point[0] - (min_x - margin)
        y = (max_y + margin) - point[1]
        return x, y

    return width, height, mapper


def render_svg(compiled: CompiledGeometry) -> bytes:
    width, height, mapper = _mapping(compiled)
    opening_radius = OVERLAY_OPENING_RADIUS_FRACTION * max(width, height)
    font_size = OVERLAY_FONT_SIZE_FRACTION * max(width, height)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(width)} {fmt(height)}">',
        '<g id="walls">',
    ]
    for wall in compiled.walls:
        start = mapper(wall.start)
        end = mapper(wall.end)
        lines.append(
            f'<polyline points="{fmt(start[0])},{fmt(start[1])} {fmt(end[0])},{fmt(end[1])}" '
            f'stroke="#14532d" stroke-width="{fmt(wall.thickness_m)}" fill="none"/>'
        )
    lines.append("</g>")
    lines.append('<g id="rooms">')
    for room in compiled.rooms:
        points = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (mapper(p) for p in room.polygon))
        lines.append(f'<polygon points="{points}" fill="none" stroke="#2563eb"/>')
    lines.append("</g>")
    lines.append('<g id="doors">')
    for opening in compiled.openings:
        if opening.type != "door":
            continue
        center = mapper(opening.center)
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(opening_radius)}" '
            f'fill="#b45309" data-center="{fmt(center[0])},{fmt(center[1])}"/>'
        )
    lines.append("</g>")
    lines.append('<g id="windows">')
    for opening in compiled.openings:
        if opening.type != "window":
            continue
        center = mapper(opening.center)
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(opening_radius)}" '
            f'fill="#0891b2" data-center="{fmt(center[0])},{fmt(center[1])}"/>'
        )
    lines.append("</g>")
    lines.append('<g id="ids">')
    for wall in compiled.walls:
        center = mapper(((wall.start[0] + wall.end[0]) / 2, (wall.start[1] + wall.end[1]) / 2))
        lines.append(f'<text x="{fmt(center[0])}" y="{fmt(center[1])}" font-size="{fmt(font_size)}">{wall.id}</text>')
    for room in compiled.rooms:
        cx = sum(p[0] for p in room.polygon) / len(room.polygon)
        cy = sum(p[1] for p in room.polygon) / len(room.polygon)
        center = mapper((cx, cy))
        lines.append(f'<text x="{fmt(center[0])}" y="{fmt(center[1])}" font-size="{fmt(font_size)}">{room.id}</text>')
    for opening in compiled.openings:
        center = mapper(opening.center)
        lines.append(f'<text x="{fmt(center[0])}" y="{fmt(center[1])}" font-size="{fmt(font_size)}">{opening.id}</text>')
    lines.append("</g>")
    lines.append("</svg>\n")
    svg = "\n".join(lines).encode("utf-8")
    if len(svg) > MAX_OVERLAY_BYTES:
        raise ValueError("overlay_exceeds_max_bytes")
    return svg


def render_png(compiled: CompiledGeometry) -> bytes:
    """Deterministic PNG render of the same top-down view (pinned settings)."""
    width, height, mapper = _mapping(compiled)
    scale = OVERLAY_PNG_SCALE
    px_width = max(1, int(round(width * scale)))
    px_height = max(1, int(round(height * scale)))
    image = Image.new("RGB", (px_width, px_height), "white")
    draw = ImageDraw.Draw(image)

    def px(point: tuple[float, float]) -> tuple[float, float]:
        sx, sy = mapper(point)
        return sx * scale, sy * scale

    for wall in compiled.walls:
        stroke_px = max(1, int(round(wall.thickness_m * scale)))
        draw.line([px(wall.start), px(wall.end)], fill=(20, 83, 45), width=stroke_px)
    for room in compiled.rooms:
        draw.polygon([px(p) for p in room.polygon], outline=(37, 99, 235))
    r = max(1, int(round(OVERLAY_OPENING_RADIUS_FRACTION * max(width, height) * scale)))
    for opening in compiled.openings:
        color = (180, 83, 9) if opening.type == "door" else (8, 145, 178)
        cx, cy = px(opening.center)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=6)
    return buffer.getvalue()
