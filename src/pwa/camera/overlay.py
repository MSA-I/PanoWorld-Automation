"""Top-down camera coverage overlay (deterministic, no Blender).

Renders the scene geometry with placed camera viewpoints as a flat Z=0
top-down view: walls as strokes, rooms as outlined polygons, openings as
coloured markers, and camera viewpoints as filled circles. Produces SVG for
the G3 camera gate (AC-8). Fully deterministic: same input -> identical bytes.
"""

from __future__ import annotations

from pwa.camera.config import (
    MAX_OVERLAY_BYTES,
    OVERLAY_CAMERA_RADIUS_FRACTION,
    OVERLAY_FONT_SIZE_FRACTION,
    OVERLAY_MARGIN_FRACTION,
    OVERLAY_OPENING_RADIUS_FRACTION,
)
from pwa.camera.types import SceneGeometry, Viewpoint


def fmt(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    if text in {"-0", "-0.0", ""}:
        return "0"
    return text


def _bounds(geometry: SceneGeometry, viewpoints: tuple[Viewpoint, ...]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for wall in geometry.walls:
        xs.extend((wall.start[0], wall.end[0]))
        ys.extend((wall.start[1], wall.end[1]))
    for room in geometry.rooms:
        for point in room.polygon:
            xs.append(point[0])
            ys.append(point[1])
    for opening in geometry.openings:
        xs.append(opening.center[0])
        ys.append(opening.center[1])
    for vp in viewpoints:
        xs.append(vp.position[0])
        ys.append(vp.position[1])
    if not xs:
        return 0.0, 0.0, 1.0, 1.0
    return min(xs), max(xs), min(ys), max(ys)


def _mapping(geometry: SceneGeometry, viewpoints: tuple[Viewpoint, ...]):
    min_x, max_x, min_y, max_y = _bounds(geometry, viewpoints)
    extent = max(max_x - min_x, max_y - min_y, 1e-6)
    margin = OVERLAY_MARGIN_FRACTION * extent
    width = (max_x - min_x) + 2 * margin
    height = (max_y - min_y) + 2 * margin

    def mapper(point):
        x = point[0] - (min_x - margin)
        y = (max_y + margin) - point[1]
        return x, y

    return width, height, mapper


def render_overlay_svg(geometry: SceneGeometry, viewpoints: tuple[Viewpoint, ...]) -> bytes:
    width, height, mapper = _mapping(geometry, viewpoints)
    opening_radius = OVERLAY_OPENING_RADIUS_FRACTION * max(width, height)
    camera_radius = OVERLAY_CAMERA_RADIUS_FRACTION * max(width, height)
    font_size = OVERLAY_FONT_SIZE_FRACTION * max(width, height)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(width)} {fmt(height)}">',
        '<g id="walls">',
    ]
    for wall in geometry.walls:
        start = mapper(wall.start)
        end = mapper(wall.end)
        lines.append(
            f'<polyline points="{fmt(start[0])},{fmt(start[1])} {fmt(end[0])},{fmt(end[1])}" '
            f'stroke="#14532d" stroke-width="{fmt(wall.thickness_m)}" fill="none"/>'
        )
    lines.append("</g>")
    lines.append('<g id="rooms">')
    for room in geometry.rooms:
        points = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in (mapper(p) for p in room.polygon))
        lines.append(f'<polygon points="{points}" fill="none" stroke="#2563eb"/>')
    lines.append("</g>")
    lines.append('<g id="doors">')
    for opening in geometry.openings:
        if opening.type != "door":
            continue
        center = mapper(opening.center)
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(opening_radius)}" fill="#b45309"/>'
        )
    lines.append("</g>")
    lines.append('<g id="windows">')
    for opening in geometry.openings:
        if opening.type != "window":
            continue
        center = mapper(opening.center)
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(opening_radius)}" fill="#0891b2"/>'
        )
    lines.append("</g>")
    lines.append('<g id="cameras">')
    for vp in viewpoints:
        center = mapper(vp.position)
        lines.append(
            f'<circle cx="{fmt(center[0])}" cy="{fmt(center[1])}" r="{fmt(camera_radius)}" fill="#dc2626" '
            f'data-viewpoint="{vp.id}" data-room="{vp.room_id}"/>'
        )
    lines.append("</g>")
    lines.append('<g id="ids">')
    for vp in viewpoints:
        center = mapper(vp.position)
        lines.append(f'<text x="{fmt(center[0])}" y="{fmt(center[1])}" font-size="{fmt(font_size)}" fill="#7f1d1d">{vp.id}</text>')
    for room in geometry.rooms:
        cx = sum(p[0] for p in room.polygon) / len(room.polygon)
        cy = sum(p[1] for p in room.polygon) / len(room.polygon)
        center = mapper((cx, cy))
        lines.append(f'<text x="{fmt(center[0])}" y="{fmt(center[1])}" font-size="{fmt(font_size)}">{room.id}</text>')
    lines.append("</g>")
    lines.append("</svg>\n")
    svg = "\n".join(lines).encode("utf-8")
    if len(svg) > MAX_OVERLAY_BYTES:
        raise ValueError("overlay_exceeds_max_bytes")
    return svg