"""DXF extraction worker."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import ezdxf

from pwa.floorplan.config import DXF_UNITS, MAX_DXF_ENTITIES
from pwa.floorplan.findings import make_finding

_UNIT_SCALE_M = {"mm": 0.001, "cm": 0.01, "m": 1.0}
_KNOWN_LAYERS = {"PWA-WALL", "PWA-ROOM", "PWA-DOOR", "PWA-WINDOW", "PWA-DIM"}
# §6 disposition table: IMAGE/XREF/OLE/INSERT/ARC/SPLINE are hard errors
# "regardless of layer" -- never resolve external data, whatever layer they
# sit on. TEXT/MTEXT (and any other wrong entity kind) are only an error when
# they sit on a *known* PWA-* layer; on an unknown layer they fall through to
# the ordinary "unmapped/warn" row like any other entity.
_SECURITY_UNSUPPORTED_KINDS = {"ARC", "SPLINE", "INSERT", "IMAGE", "OLE2FRAME"}
_LAYER_SCOPED_UNSUPPORTED_KINDS = {"TEXT", "MTEXT"}


def _opaque_name(value: str, tokens: dict[str, str], prefix: str) -> str:
    token = tokens.get(value)
    if token is None:
        token = f"{prefix}-{len(tokens) + 1:04d}"
        tokens[value] = token
    return token


def _finding_dict(code: str, message: str, *, source_ref: str | None = None) -> dict[str, object]:
    finding = make_finding(code, message, source_ref=source_ref)
    return {
        "code": finding.code,
        "severity": finding.severity,
        "tier": finding.tier,
        "source_ref": finding.source_ref,
        "message": finding.message,
    }


def _unmapped(source_ref: str, layer: str) -> dict[str, object]:
    return _finding_dict("PARSE_UNMAPPED_SOURCE_ENTITY", f"ignored unmapped entity on layer {layer}", source_ref=source_ref)


def _unsupported(source_ref: str, detail: str) -> dict[str, object]:
    return _finding_dict("PARSE_UNSUPPORTED_FEATURE", detail, source_ref=source_ref)


def _open_polygon(source_ref: str) -> dict[str, object]:
    return _finding_dict("PARSE_OPEN_POLYGON", "room polygon is not closed", source_ref=source_ref)


def _has_nonzero_line_z(entity) -> bool:
    start = getattr(entity.dxf, "start", None)
    end = getattr(entity.dxf, "end", None)
    if start is None or end is None:
        return False
    return any(abs(value) > 0 for value in (start.z, end.z))


def _room_has_bulge(entity) -> bool:
    return any(abs(point[2]) > 0 for point in entity.get_points("xyb"))


def _scan_layout(
    layout,
    *,
    include_geometry: bool,
    units: str,
    walls: list[dict],
    rooms: list[dict],
    openings: list[dict],
    errors: list[dict],
    unmapped: list[dict],
    scanned_before: int = 0,
    layout_tokens: dict[str, str] | None = None,
    layer_tokens: dict[str, str] | None = None,
) -> int:
    layout_tokens = layout_tokens if layout_tokens is not None else {}
    layer_tokens = layer_tokens if layer_tokens is not None else {}
    scanned = 0
    for entity in layout:
        if scanned_before + scanned >= MAX_DXF_ENTITIES:
            raise ValueError("PARSE_RESOURCE_LIMIT")
        scanned += 1
        layer = entity.dxf.layer
        kind = entity.dxftype()
        handle = entity.dxf.handle
        safe_layout = (
            layout.name
            if layout.name == "Model"
            else _opaque_name(layout.name, layout_tokens, "unknown-layout")
        )
        safe_layer = layer if layer in _KNOWN_LAYERS else _opaque_name(layer, layer_tokens, "unknown-layer")
        source_ref = f"dxf:{safe_layout}/{safe_layer}#{handle}"
        if layout.name != "Model":
            errors.append(_unsupported(source_ref, "paperspace or additional layout entities are unsupported"))
            continue
        # M-7 (code review, 2026-08-10): IMAGE/XREF/OLE/INSERT/ARC/SPLINE
        # must fail loudly regardless of layer -- checked before the
        # "unknown layer" test so a scanned raster underlay placed on layer
        # 0 (the overwhelmingly common real-world convention) cannot
        # downgrade to a silently-ignored warning.
        if kind in _SECURITY_UNSUPPORTED_KINDS:
            errors.append(_unsupported(source_ref, f"{kind} is unsupported on layer {safe_layer}"))
            continue
        if layer not in _KNOWN_LAYERS:
            unmapped.append(_unmapped(source_ref, safe_layer))
            continue
        if layer == "PWA-DIM":
            errors.append(_unsupported(source_ref, "reserved PWA-DIM entities are unsupported"))
            continue
        if kind in _LAYER_SCOPED_UNSUPPORTED_KINDS:
            errors.append(_unsupported(source_ref, f"{kind} is unsupported on layer {safe_layer}"))
            continue
        if layer == "PWA-WALL":
            if kind != "LINE" or _has_nonzero_line_z(entity):
                errors.append(_unsupported(source_ref, "walls must be 2D LINE entities"))
                continue
            if include_geometry:
                walls.append(
                    {
                        "index": len(walls),
                        "source_ref": source_ref,
                        "start": [entity.dxf.start.x, entity.dxf.start.y],
                        "end": [entity.dxf.end.x, entity.dxf.end.y],
                    }
                )
            continue
        if layer == "PWA-ROOM":
            if kind != "LWPOLYLINE":
                errors.append(_unsupported(source_ref, "rooms must be LWPOLYLINE entities"))
                continue
            if _room_has_bulge(entity):
                errors.append(_unsupported(source_ref, "room polylines with bulge are unsupported"))
                continue
            if not entity.closed:
                errors.append(_open_polygon(source_ref))
                continue
            if include_geometry:
                rooms.append(
                    {
                        "index": len(rooms),
                        "source_ref": source_ref,
                        "polygon": [[point[0], point[1]] for point in entity.get_points("xy")],
                    }
                )
            continue
        if layer in {"PWA-DOOR", "PWA-WINDOW"}:
            if kind != "LINE" or _has_nonzero_line_z(entity):
                errors.append(_unsupported(source_ref, "openings must be 2D LINE entities"))
                continue
            if include_geometry:
                sx, sy = entity.dxf.start.x, entity.dxf.start.y
                ex, ey = entity.dxf.end.x, entity.dxf.end.y
                openings.append(
                    {
                        "index": len(openings),
                        "source_ref": source_ref,
                        "kind": "door" if layer == "PWA-DOOR" else "window",
                        "center": [(sx + ex) / 2, (sy + ey) / 2],
                        "width_m": math.hypot(ex - sx, ey - sy) * _UNIT_SCALE_M[units],
                        "span": [[sx, sy], [ex, ey]],
                    }
                )
            continue
    return scanned


def extract_dxf(path: Path) -> dict:
    document = ezdxf.readfile(path)
    modelspace = document.modelspace()
    if len(modelspace) > MAX_DXF_ENTITIES:
        raise ValueError("PARSE_RESOURCE_LIMIT")
    units_code = int(document.header.get("$INSUNITS", 0))
    units = DXF_UNITS.get(units_code)
    if units is None:
        raise ValueError("PARSE_UNITS_MISMATCH")

    walls: list[dict[str, object]] = []
    rooms: list[dict[str, object]] = []
    openings: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    unmapped: list[dict[str, object]] = []
    layout_tokens: dict[str, str] = {}
    layer_tokens: dict[str, str] = {}
    scanned_entities = _scan_layout(
        modelspace,
        include_geometry=True,
        units=units,
        walls=walls,
        rooms=rooms,
        openings=openings,
        errors=errors,
        unmapped=unmapped,
        layout_tokens=layout_tokens,
        layer_tokens=layer_tokens,
    )

    for layout in document.layouts:
        if layout.name == "Model":
            continue
        if len(layout):
            scanned_entities += _scan_layout(
                layout,
                include_geometry=False,
                units=units,
                walls=walls,
                rooms=rooms,
                openings=openings,
                errors=errors,
                unmapped=unmapped,
                scanned_before=scanned_entities,
                layout_tokens=layout_tokens,
                layer_tokens=layer_tokens,
            )

    return {
        "frame": {
            "kind": "dxf",
            "unit_scale_m": _UNIT_SCALE_M[units],
            "y_down": False,
            "height_px": None,
            "source_units": units,
        },
        "walls": walls,
        "rooms": rooms,
        "openings": openings,
        "dimensions": [],
        "scanned_entities": scanned_entities,
        "unmapped": unmapped,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    input_path = Path(argv[0])
    output_path = Path(argv[1])
    try:
        payload = extract_dxf(input_path)
    except ValueError as exc:
        payload = {"fatal_error_code": str(exc), "message": str(exc)}
    output_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
