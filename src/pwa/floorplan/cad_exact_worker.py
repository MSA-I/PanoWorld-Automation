"""cad_exact (Product A) DXF extraction worker.

Product A parses CAD/DXF geometry *exactly* and natively — the additive
capability over the historical ``dxf_worker`` (which rejects ARC/SPLINE/bulge
as ``PARSE_UNSUPPORTED_FEATURE``). In addition to the historical LINE walls,
zero-bulge LWPOLYLINE rooms and LINE doors/windows, this worker:

- keeps native ARC walls (bounded circular arcs) as ``kind: circular_arc`` with
  an ``arc`` sub-object (centre/radius/start/end/sweep/bulge/sagitta),
- keeps LWPOLYLINE rooms WITH bulge, tessellated per the FX1 sagitta rule,
- reads *sourced* thickness from PWA XDATA (code 1000 ``THICKNESS_M`` + 1040),
  fail-closed ``RECOGNITION_THICKNESS_MISSING`` when a product wall lacks it,
- recognises ``PWA-PASSAGE`` as the third opening type (span bound 3.0 m).

This is deterministic, pure (no model call, no I/O beyond the DXF), and emits
product output only against the frozen WP2 contract surface. Routes remain
default-off.
"""

from __future__ import annotations

import math
from pathlib import Path

import ezdxf

from pwa.floorplan import cad_exact_geometry as G
from pwa.floorplan.config import (
    DEGENERATE_WALL_M,
    DXF_UNITS,
    MAX_DXF_BYTES,
    MAX_DXF_ENTITIES,
)
from pwa.floorplan.recognition import PASSAGE_SPAN_MAX_M
from pwa.floorplan.validate import (
    _to_int,
    seg_intersects_non_adjacent,
)

_KNOWN_LAYERS = {"PWA-WALL", "PWA-ROOM", "PWA-DOOR", "PWA-WINDOW", "PWA-PASSAGE"}

# Same disposition table as the historical dxf_worker: these kinds are hard
# errors regardless of layer (external data / unbounded curves are never
# resolved).
_SECURITY_UNSUPPORTED_KINDS = {"SPLINE", "INSERT", "IMAGE", "OLE2FRAME"}

_UNIT_SCALE_M = {"mm": 0.001, "cm": 0.01, "m": 1.0}


def _thickness_m(entity) -> float | None:
    """Read sourced thickness (metres) from an entity's PWA XDATA, if present.

    Contract: the CAD author declares thickness explicitly as XDATA under the
    registered ``PWA`` app: ``(1000, "THICKNESS_M"), (1040, metres)``. No value
    is ever inferred or defaulted — absence yields ``None`` and the caller
    emits ``RECOGNITION_THICKNESS_MISSING`` (fail-closed).
    """
    xdata = None
    try:
        xdata = entity.get_xdata("PWA")
    except Exception:
        return None
    if not xdata:
        return None
    for code, value in xdata:
        if code == 1000 and value == "THICKNESS_M":
            continue
        if code == 1040:
            try:
                metres = float(value)
            except (TypeError, ValueError):
                return None
            return metres if metres > 0 else None
    return None


def _finding(code: str, message: str, *, source_ref: str | None = None) -> dict:
    return {"code": code, "severity": "error", "tier": 0, "source_ref": source_ref, "message": message}


def _arc_from_entity(entity) -> dict:
    """Build the frozen ``arc`` sub-object from a native ezdxf ARC entity.

    ezdxf exposes an arc's sweep/bulge only via geometry, so the deterministic
    sweep + bulge are derived here from centre/radius/start/end using the frozen
    ``cad_exact_geometry`` rules. A native ARC has no signed direction stored in
    DXF (it is always CCW in ezdxf's internal model), so sweep is ``ccw`` and the
    bulge is positive by the frozen convention.
    """
    center = (float(entity.dxf.center.x), float(entity.dxf.center.y))
    radius = float(entity.dxf.radius)
    start_deg = float(entity.dxf.start_angle)
    end_deg = float(entity.dxf.end_angle)
    # A full-circle ARC (|end - start| == 360) is unbounded for a wall: reject
    # at the caller; here we compute a bounded sweep assumed < 360.
    sweep, angle_rad = G.sweep_from_endpoints(start_deg, end_deg, "ccw")
    n_segments = G.min_segments_for_sagitta(radius, angle_rad, 0.5, 5.0)
    max_sagitta_px = G.sagitta_px(radius, angle_rad, n_segments, 5.0)
    bulge = G.bulge_for_sweep("ccw", theta_rad=angle_rad)
    return {
        "center": [center[0], center[1]],
        "radius_mm": radius,
        "start_deg": start_deg,
        "end_deg": end_deg,
        "sweep": sweep,
        "bulge": bulge,
        "max_sagitta_px": max_sagitta_px,
        "n_segments": n_segments,
    }


def _room_area_m2(polygon_mm: list[list[float]]) -> float:
    """Centreline shoelace area of a room polygon, mm -> m^2."""
    area2 = 0.0
    n = len(polygon_mm)
    for i in range(n):
        x0, y0 = polygon_mm[i]
        x1, y1 = polygon_mm[(i + 1) % n]
        area2 += x0 * y1 - x1 * y0
    return abs(area2) / 2.0 / 1e6  # mm^2 -> m^2


def _self_intersecting(polygon_mm: list[list[float]]) -> bool:
    """True iff a closed room polygon self-intersects on non-adjacent edges.

    Reuses the frozen ``validate`` segment-intersection predicate (which flags
    proper crossings, collinear overlaps and vertex-on-edge touches) so the
    cad_exact path enforces the same topology rule as the historical path.
    """
    n = len(polygon_mm)
    if n < 4:
        return False
    ints = [_to_int((float(p[0]), float(p[1]))) for p in polygon_mm]
    edges = list(zip(ints, ints[1:] + ints[:1]))
    for left in range(len(edges)):
        for right in range(left + 1, len(edges)):
            if right in {left, (left + 1) % len(edges)} or left == (right + 1) % len(edges):
                continue
            if seg_intersects_non_adjacent(*edges[left], *edges[right]):
                return True
    return False


def _has_nonzero_z(entity) -> bool:
    start = getattr(entity.dxf, "start", None)
    end = getattr(entity.dxf, "end", None)
    if start is None or end is None:
        return False
    return any(abs(value) > 0 for value in (getattr(start, "z", 0.0), getattr(end, "z", 0.0)))


def _tessellate_polyline(points_xyb: list[tuple[float, float, float]]) -> list[list[float]]:
    """Tessellate a bulged LWPOLYLINE ring into a sampled polygon (mm).

    Zero-bulge edges convert 1:1; a bulged edge is replaced by the vertices of
    the circular arc it represents, sampled per the frozen FX1 sagitta rule
    (``SAGITTA_MAX_PX`` 0.5, mm_per_px 5.0) via ``G.tessellate_arc``. The bulge
    sign follows the frozen convention (bulge > 0 == ccw). Deterministic:
    identical inputs produce identical vertices.
    """
    import ezdxf.math as ezm

    if not points_xyb:
        return []
    # ezdxf already closes visually; we work on the explicit vertex ring.
    out: list[list[float]] = []
    n = len(points_xyb)
    for i in range(n):
        x0, y0, bulge = points_xyb[i]
        x1, y1, _ = points_xyb[(i + 1) % n]
        out.append([float(x0), float(y0)])
        if abs(float(bulge)) > 0:
            center = ezm.bulge_center((x0, y0), (x1, y1), float(bulge))
            radius = ezm.bulge_radius((x0, y0), (x1, y1), float(bulge))
            start_deg = math.degrees(math.atan2(y0 - center.y, x0 - center.x))
            end_deg = math.degrees(math.atan2(y1 - center.y, x1 - center.x))
            _, sweep_rad = G.sweep_from_endpoints(start_deg, end_deg, "ccw" if float(bulge) > 0 else "cw")
            n_seg = G.min_segments_for_sagitta(radius, sweep_rad, 0.5, 5.0)
            verts = G.tessellate_arc(
                (float(center.x), float(center.y)), radius, start_deg, end_deg,
                "ccw" if float(bulge) > 0 else "cw", n_seg,
            )
            # verts[0] ~= (x0,y0) already appended above; insert the interior
            # samples (excluding the duplicated endpoint verts[0]/verts[-1]).
            for vx, vy in verts[1:-1]:
                out.append([float(vx), float(vy)])
    return out


def extract_cad_exact(path: Path) -> dict:
    """Parse a DXF into cad_exact product geometry.

    Returns a payload dict with ``walls`` (segment + circular_arc, sourced
    thickness), ``rooms`` (bulge-capable, area_m2), ``openings``
    (door/window/passage), and ``errors`` (fail-closed findings).
    """
    if path.stat().st_size > MAX_DXF_BYTES:
        return {"frame": {}, "walls": [], "rooms": [], "openings": [], "errors": [_finding("PARSE_RESOURCE_LIMIT", "DXF exceeds byte limit")]}
    document = ezdxf.readfile(path)
    modelspace = document.modelspace()
    if len(modelspace) > MAX_DXF_ENTITIES:
        return {"frame": {}, "walls": [], "rooms": [], "openings": [], "errors": [_finding("PARSE_RESOURCE_LIMIT", "DXF exceeds entity limit")]}
    units_code = int(document.header.get("$INSUNITS", 0))
    units = DXF_UNITS.get(units_code)
    if units is None:
        return {"frame": {}, "walls": [], "rooms": [], "openings": [], "errors": [_finding("PARSE_UNITS_MISMATCH", "unsupported DXF units")]}

    scale = _UNIT_SCALE_M[units]
    walls: list[dict] = []
    rooms: list[dict] = []
    openings: list[dict] = []
    errors: list[dict] = []
    seen_walls: set[tuple[tuple[float, float], tuple[float, float]]] = set()

    for entity in modelspace:
        layer = entity.dxf.layer
        kind = entity.dxftype()
        handle = entity.dxf.handle
        source_ref = f"dxf:modelspace/{layer}#{handle}"

        if kind in _SECURITY_UNSUPPORTED_KINDS:
            errors.append(_finding("PARSE_UNSUPPORTED_FEATURE", f"{kind} is unsupported", source_ref=source_ref))
            continue
        if layer not in _KNOWN_LAYERS:
            continue  # unmapped layers are ignored (matching dxf_worker semantics)

        if layer == "PWA-WALL":
            if kind == "LINE":
                if _has_nonzero_z(entity):
                    errors.append(_finding("PARSE_UNSUPPORTED_FEATURE", "walls must be 2D LINE entities", source_ref=source_ref))
                    continue
                sx, sy = float(entity.dxf.start.x), float(entity.dxf.start.y)
                ex, ey = float(entity.dxf.end.x), float(entity.dxf.end.y)
                thickness = _thickness_m(entity)
                length_mm = math.hypot(ex - sx, ey - sy)
                if length_mm < DEGENERATE_WALL_M * 1000.0:
                    errors.append(_finding("PARSE_DEGENERATE_WALL", "wall is shorter than minimum", source_ref=source_ref))
                key = (tuple([sx, sy]), tuple([ex, ey]))
                if key in seen_walls:
                    errors.append(_finding("PARSE_DUPLICATE_ENTITY", "duplicate wall geometry", source_ref=source_ref))
                seen_walls.add(key)
                wall = {
                    "index": len(walls),
                    "source_ref": source_ref,
                    "kind": "segment",
                    "start": [sx, sy],
                    "end": [ex, ey],
                    "thickness_m": thickness,
                }
                if thickness is None:
                    errors.append(_finding("RECOGNITION_THICKNESS_MISSING", "wall lacks sourced thickness", source_ref=source_ref))
                walls.append(wall)
            elif kind == "ARC":
                delta = abs(float(entity.dxf.end_angle) - float(entity.dxf.start_angle))
                if delta >= 360.0:
                    errors.append(_finding("RECOGNITION_ARC_NO_SAGITTA_BOUND", "full-circle ARC is not a bounded arc", source_ref=source_ref))
                    continue
                arc = _arc_from_entity(entity)
                thickness = _thickness_m(entity)
                wall = {
                    "index": len(walls),
                    "source_ref": source_ref,
                    "kind": "circular_arc",
                    "start": [arc["center"][0] + arc["radius_mm"] * math.cos(math.radians(arc["start_deg"])), arc["center"][1] + arc["radius_mm"] * math.sin(math.radians(arc["start_deg"]))],
                    "end": [arc["center"][0] + arc["radius_mm"] * math.cos(math.radians(arc["end_deg"])), arc["center"][1] + arc["radius_mm"] * math.sin(math.radians(arc["end_deg"]))],
                    "arc": arc,
                    "thickness_m": thickness,
                }
                if thickness is None:
                    errors.append(_finding("RECOGNITION_THICKNESS_MISSING", "wall lacks sourced thickness", source_ref=source_ref))
                walls.append(wall)
            else:
                errors.append(_finding("PARSE_UNSUPPORTED_FEATURE", f"{kind} is unsupported on PWA-WALL", source_ref=source_ref))
            continue

        if layer == "PWA-ROOM":
            if kind != "LWPOLYLINE":
                errors.append(_finding("PARSE_UNSUPPORTED_FEATURE", "rooms must be LWPOLYLINE entities", source_ref=source_ref))
                continue
            if not entity.closed:
                errors.append(_finding("PARSE_OPEN_POLYGON", "room polygon is not closed", source_ref=source_ref))
                continue
            points_xyb = entity.get_points("xyb")
            has_bulge = any(abs(point[2]) > 0 for point in points_xyb)
            # Tessellate bulged edges per the FX1 sagitta rule; zero-bulge
            # LWPOLYLINE converts 1:1.
            polygon_mm: list[list[float]] = _tessellate_polyline([tuple(p) for p in points_xyb])
            if len(polygon_mm) < 3:
                errors.append(_finding("PARSE_OPEN_POLYGON", "room needs >= 3 vertices", source_ref=source_ref))
                continue
            if _self_intersecting(polygon_mm):
                errors.append(_finding("PARSE_SELF_INTERSECTING_POLYGON", "room polygon self-intersects", source_ref=source_ref))
            rooms.append(
                {
                    "index": len(rooms),
                    "source_ref": source_ref,
                    "polygon_mm": polygon_mm,
                    "has_bulge": has_bulge,
                    "area_m2": _room_area_m2(polygon_mm),
                }
            )
            continue

        if layer in {"PWA-DOOR", "PWA-WINDOW", "PWA-PASSAGE"}:
            if kind != "LINE":
                errors.append(_finding("PARSE_UNSUPPORTED_FEATURE", "openings must be 2D LINE entities", source_ref=source_ref))
                continue
            if _has_nonzero_z(entity):
                errors.append(_finding("PARSE_UNSUPPORTED_FEATURE", "openings must be 2D LINE entities", source_ref=source_ref))
                continue
            sx, sy = float(entity.dxf.start.x), float(entity.dxf.start.y)
            ex, ey = float(entity.dxf.end.x), float(entity.dxf.end.y)
            width_m = math.hypot(ex - sx, ey - sy) * scale
            opening_kind = "door" if layer == "PWA-DOOR" else "window" if layer == "PWA-WINDOW" else "passage"
            opening = {
                "index": len(openings),
                "source_ref": source_ref,
                "kind": opening_kind,
                "center": [(sx + ex) / 2, (sy + ey) / 2],
                "width_m": width_m,
                "span": [[sx, sy], [ex, ey]],
            }
            if opening_kind == "passage" and width_m > PASSAGE_SPAN_MAX_M:
                errors.append(_finding("RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND", "passage span exceeds 3.0 m", source_ref=source_ref))
            openings.append(opening)
            continue

    return {
        "frame": {"kind": "cad_exact", "source_units": units, "unit_scale_m": scale, "y_down": False},
        "walls": walls,
        "rooms": rooms,
        "openings": openings,
        "scanned_entities": len(modelspace),
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    import json
    import sys

    argv = argv or sys.argv[1:]
    payload = extract_cad_exact(Path(argv[0]))
    Path(argv[1]).write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
