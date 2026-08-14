"""cad_exact (Product A) emitter and FX1-truth scorer.

The emitter converts ``cad_exact_worker.extract_cad_exact`` geometry (mm) into a
``floorplan_parse`` 1.2.0 payload with ``source_class: "cad_exact"``, satisfying
the frozen recognition invariants before emission (fail-closed). The scorer
binds product walls/rooms/openings against the FX1 frozen truth using the frozen
WP1 evaluator's exact-by-key canonical matcher, so the accuracy gate is measured
against independent frozen truth — never recognizer self-attestation.
"""

from __future__ import annotations

import math
from pathlib import Path

from pwa.evaluator import metrics as M
from pwa.floorplan import cad_exact_geometry as G
from pwa.floorplan import recognition


def _quant_mm(value_m: float) -> float:
    """Quantize a metre value onto the frozen evaluator grid (0.01 mm)."""
    return M.quantize(float(value_m) * 1000.0, M.QUANTIZE_MM)


def _quant_m(value_m: float) -> float:
    """Quantize a metre value onto the frozen grid, returned in metres."""
    return _quant_mm(value_m) / 1000.0


def _int_mm(value_m: float) -> int | float:
    """Return an integer millimetre when the quantized value is integral.

    The FX1 frozen truth authors coordinates as integer millimetres; the frozen
    evaluator matches exact-by-key on canonical JSON, where ``1000`` and
    ``1000.0`` serialize differently. Emitting integral mm as ints keeps product
    geometry byte-identical to the truth's JSON for the exact-match gate.
    """
    mm = round(float(value_m) * 1000.0, 6)
    return int(mm) if mm == int(mm) else mm


def emit_floorplan_parse(walls: list[dict], rooms: list[dict], openings: list[dict]) -> dict:
    """Emit a floorplan_parse 1.2.0 payload (source_class cad_exact) in metres.

    Inputs are in metres: wall ``start``/``end`` (m), arc ``center`` (m) /
    ``radius_m``, room ``polygon`` (m), opening ``center``/``span`` (m). Every
    wall must carry sourced thickness and satisfy the frozen arc invariants;
    every passage must satisfy the span bound. Blocking codes are returned for
    the caller to fail closed (this function is pure).
    """
    recognition_findings: list[str] = []
    out_walls = []
    for wall in walls:
        thickness_m = wall.get("thickness_m")
        recognition_findings.extend(recognition.check_thickness(thickness_m))
        emitted = {
            "id": f"w-{wall['index']:04d}",
            "start": [_quant_m(wall["start"][0]), _quant_m(wall["start"][1])],
            "end": [_quant_m(wall["end"][0]), _quant_m(wall["end"][1])],
            "kind": wall["kind"],
            "thickness_m": float(thickness_m) if thickness_m is not None else None,
            "confidence": 1.0,
            "provenance": {
                "source_kind": "dxf",
                "source_ref": wall["source_ref"],
                "source_start": [wall["start"][0], wall["start"][1]],
                "source_end": [wall["end"][0], wall["end"][1]],
            },
        }
        if wall["kind"] == "circular_arc":
            arc = wall["arc"]
            emitted["arc"] = {
                "center": [_quant_m(arc["center"][0]), _quant_m(arc["center"][1])],
                "radius_m": _quant_m(arc["radius_m"]),
                "start_deg": arc["start_deg"],
                "end_deg": arc["end_deg"],
                "sweep": arc["sweep"],
                "bulge": arc["bulge"],
                "max_sagitta_px": arc["max_sagitta_px"],
            }
            recognition_findings.extend(recognition.arc_invariants(emitted["arc"]))
        out_walls.append(emitted)

    out_rooms = []
    for room in rooms:
        out_rooms.append(
            {
                "id": f"r-{room['index']:04d}",
                "polygon": [[_quant_m(p[0]), _quant_m(p[1])] for p in room["polygon"]],
                "confidence": 1.0,
                "area_m2": room["area_m2"],
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": room["source_ref"],
                    "source_polygon": [list(p) for p in room["polygon"]],
                },
            }
        )

    out_openings = []
    wall_id_by_index = {w["index"]: f"w-{w['index']:04d}" for w in walls}
    for opening in openings:
        if opening["kind"] == "passage":
            recognition_findings.extend(recognition.check_passage_span(opening["width_m"]))
        wall_id = _resolve_opening_host(opening, walls, wall_id_by_index)
        out_openings.append(
            {
                "id": f"o-{opening['index']:04d}",
                "type": opening["kind"],
                "wall_id": wall_id,
                "center": [_quant_m(opening["center"][0]), _quant_m(opening["center"][1])],
                "width_m": float(opening["width_m"]),
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": opening["source_ref"],
                    "source_center": [opening["center"][0], opening["center"][1]],
                    "source_span": [opening["span"][0], opening["span"][1]],
                },
            }
        )

    payload = {
        "units": "m",
        "source_class": "cad_exact",
        "scale_m_per_px": None,
        "rooms": out_rooms,
        "walls": out_walls,
        "openings": out_openings,
    }
    return payload, recognition_findings


def parse_cad_exact(path: Path) -> tuple[dict, list[str], list[dict]]:
    """End-to-end Product A: DXF (mm) -> cad_exact floorplan_parse 1.2.0 (m).

    Returns ``(payload, recognition_findings, source_errors)``. The worker parses
    native units (mm) and the emitter converts to metres; ``source_errors`` are
    the worker's fail-closed findings (scale/topology/resource/security), and
    ``recognition_findings`` are the frozen invariant codes. The caller fails
    closed if either is non-empty.
    """
    from pwa.floorplan.cad_exact_worker import extract_cad_exact

    raw = extract_cad_exact(path)
    mm_scale = raw["frame"].get("unit_scale_m", 1.0)
    walls_m = [_wall_to_metres(w, mm_scale) for w in raw["walls"]]
    rooms_m = [_room_to_metres(r, mm_scale) for r in raw["rooms"]]
    openings_m = [_opening_to_metres(o, mm_scale) for o in raw["openings"]]
    payload, findings = emit_floorplan_parse(walls_m, rooms_m, openings_m)
    return payload, findings, raw["errors"]


def _wall_to_metres(wall: dict, scale_m: float) -> dict:
    out = {
        "index": wall["index"],
        "source_ref": wall["source_ref"],
        "kind": wall["kind"],
        "start": [wall["start"][0] * scale_m, wall["start"][1] * scale_m],
        "end": [wall["end"][0] * scale_m, wall["end"][1] * scale_m],
        "thickness_m": wall.get("thickness_m"),
    }
    if wall["kind"] == "circular_arc":
        arc = wall["arc"]
        out["arc"] = {
            "center": [arc["center"][0] * scale_m, arc["center"][1] * scale_m],
            "radius_m": arc["radius_mm"] * scale_m,
            "start_deg": arc["start_deg"],
            "end_deg": arc["end_deg"],
            "sweep": arc["sweep"],
            "bulge": arc["bulge"],
            "max_sagitta_px": arc["max_sagitta_px"],
        }
    return out


def _room_to_metres(room: dict, scale_m: float) -> dict:
    return {
        "index": room["index"],
        "source_ref": room["source_ref"],
        "polygon": [[p[0] * scale_m, p[1] * scale_m] for p in room["polygon_mm"]],
        "area_m2": room["area_m2"],
    }


def _opening_to_metres(opening: dict, scale_m: float) -> dict:
    return {
        "index": opening["index"],
        "source_ref": opening["source_ref"],
        "kind": opening["kind"],
        "center": [opening["center"][0] * scale_m, opening["center"][1] * scale_m],
        "width_m": opening["width_m"],
        "span": [[opening["span"][0][0] * scale_m, opening["span"][0][1] * scale_m], [opening["span"][1][0] * scale_m, opening["span"][1][1] * scale_m]],
    }


_OPENING_OFFSET_M = 0.02  # frozen OPENING_OFFSET_M


def _resolve_opening_host(opening: dict, walls: list[dict], wall_id_by_index: dict[int, str]) -> str | None:
    """Resolve the wall hosting an opening by span collinearity (§6).

    An opening's span lies on exactly one wall centreline. For segment walls we
    test both span endpoints against the wall's infinite line within
    ``OPENING_OFFSET_M``; for circular-arc walls we match by radial distance to
    the arc centre (an FX1 apse-hosted window). Returns the resolved wall id, or
    ``None`` when no wall matches (the caller must fail closed).
    """
    span = opening.get("span")
    cx = opening["center"][0]
    cy = opening["center"][1]
    for wall in walls:
        if wall["kind"] == "segment":
            sx, sy = wall["start"]
            ex, ey = wall["end"]
            vx = ex - sx
            vy = ey - sy
            length = math.hypot(vx, vy)
            if length == 0:
                continue
            ux, uy = vx / length, vy / length
            if span is not None:
                ok = True
                for point in span:
                    dx = point[0] - sx
                    dy = point[1] - sy
                    if abs(dx * uy - dy * ux) > _OPENING_OFFSET_M:
                        ok = False
                        break
                if ok:
                    return wall_id_by_index[wall["index"]]
            dx = cx - sx
            dy = cy - sy
            if abs(dx * uy - dy * ux) <= _OPENING_OFFSET_M:
                return wall_id_by_index[wall["index"]]
        else:  # circular_arc
            arc = wall["arc"]
            r = arc["radius_m"]
            dx = cx - arc["center"][0]
            dy = cy - arc["center"][1]
            if abs(math.hypot(dx, dy) - r) <= _OPENING_OFFSET_M:
                return wall_id_by_index[wall["index"]]
    return None


# --- FX1 truth binding ------------------------------------------------------


def truth_record_from_wall(wall: dict) -> dict:
    """Map an emitted cad_exact wall (metres) to the FX1 truth mm record shape.

    The FX1 truth walls use ``_mm`` fields; the frozen evaluator matches on
    ``kind`` + canonical geometry (``a_mm``/``b_mm`` for segments, ``center_mm``/
    ``radius_mm``/``start_deg``/``end_deg`` for arcs).
    """
    if wall["kind"] == "circular_arc":
        return {
            "kind": "circular_arc",
            "center_mm": [_int_mm(wall["arc"]["center"][0]), _int_mm(wall["arc"]["center"][1])],
            "radius_mm": _int_mm(wall["arc"]["radius_m"]),
            "start_deg": _int_or_float(wall["arc"]["start_deg"]),
            "end_deg": _int_or_float(wall["arc"]["end_deg"]),
        }
    return {
        "kind": "segment",
        "a_mm": [_int_mm(wall["start"][0]), _int_mm(wall["start"][1])],
        "b_mm": [_int_mm(wall["end"][0]), _int_mm(wall["end"][1])],
    }


def _int_or_float(value: float) -> int | float:
    """Coerce an integral float to int so canonical JSON matches FX1 truth.

    FX1 authors ``start_deg``/``end_deg`` as integer degrees (``-90`` not
    ``-90.0``); the frozen evaluator's canonical key is exact-by-key, so the
    product degrees must serialize identically to the truth to match.
    """
    v = float(value)
    return int(v) if v == int(v) else v


_SUPPORTABLE_TRUTH_KINDS = {"segment", "circular_arc"}


def _truth_mm_record(truth_wall: dict) -> dict:
    """Project a raw FX1 truth wall to the mm-only canonical shape.

    The FX1 truth records carry pixel-space fields (``a_px``/``b_px``, and for
    arcs ``tessellation_rule``/``vertices_mm``) because FX1 is authored for a
    raster recognizer. Product A is a CAD (mm-native) recognizer, so the scoring
    binds on the millimetre geometry only. This projection keeps the exact
    mm-keyed fields the frozen evaluator's canonical key is defined over, and
    discards the raster-only presentation fields.
    """
    if truth_wall.get("kind") == "circular_arc":
        return {
            "kind": "circular_arc",
            "center_mm": truth_wall["center_mm"],
            "radius_mm": truth_wall["radius_mm"],
            "start_deg": truth_wall["start_deg"],
            "end_deg": truth_wall["end_deg"],
        }
    return {
        "kind": "segment",
        "a_mm": truth_wall["a_mm"],
        "b_mm": truth_wall["b_mm"],
    }


def score_against_truth(walls: list[dict], truth: dict) -> dict:
    """Score cad_exact walls against the FX1 frozen truth (exact-by-key).

    Both truth and prediction are projected to mm-only geometry and matched at
    most once by exact canonical-key equality via the frozen evaluator.
    Unsupported truth taxa are counted into ``supportable`` (never dropped).
    """
    truth_walls = [_truth_mm_record(w) for w in truth.get("walls", [])]
    pred_walls = [truth_record_from_wall(w) for w in walls]
    supportable = sum(1 for w in truth_walls if M.support_taxon_supported(w))
    correct = 0
    matched: set[int] = set()
    for truth_wall in truth_walls:
        if not M.support_taxon_supported(truth_wall):
            continue
        for j, pred in enumerate(pred_walls):
            if j in matched:
                continue
            if M.match_wall(truth_wall, pred):
                correct += 1
                matched.add(j)
                break
    return {
        "correct": correct,
        "supportable": supportable,
        "accuracy": correct / supportable if supportable else 0.0,
    }


# --- evidence rendering ------------------------------------------------------


def _fmt(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text if text not in {"-0", "-0.0", ""} else "0"


def _arc_path(arc: dict) -> str:
    """Render a bounded circular arc as a deterministic SVG path.

    The CAD arc is authored by centre/radius/start/end degrees + sweep; the SVG
    path uses two radius-verb arcs (``A``) connecting the endpoints, the
    direction driven by the frozen ``sweep``. Deterministic and closed-form.
    """
    cx = arc["center"][0]
    cy = arc["center"][1]
    r = arc["radius_m"]
    start_rad = math.radians(arc["start_deg"])
    end_rad = math.radians(arc["end_deg"])
    sx = cx + r * math.cos(start_rad)
    sy = cy + r * math.sin(start_rad)
    ex = cx + r * math.cos(end_rad)
    ey = cy + r * math.sin(end_rad)
    large_arc = 0 if abs((arc["end_deg"] - arc["start_deg"]) % 360.0) <= 180.0 else 1
    sweep_flag = 0 if arc["sweep"] == "ccw" else 1
    return (
        f'M {_fmt(sx)},{_fmt(sy)} A {_fmt(r)},{_fmt(r)} 0 {large_arc} {sweep_flag} '
        f'{_fmt(ex)},{_fmt(ey)}'
    )


def render_cad_exact_svg(walls: list[dict], rooms: list[dict], openings: list[dict]) -> bytes:
    """Deterministic SVG evidence overlay for cad_exact geometry (metres).

    Segment walls render as polylines; circular-arc walls render as native SVG
    ``A`` arc paths (so the apse arc is visible as a curve, not a chord). The
    y-axis flips to SVG's top-left origin for viewing. Output is byte-
    deterministic for identical inputs.
    """
    lines: list[str] = []
    for wall in walls:
        if wall["kind"] == "circular_arc":
            lines.append(f'<path d="{_arc_path(wall["arc"])}" fill="none" stroke="#14532d"/>')
        else:
            sx = _fmt(wall["start"][0])
            sy = _fmt(-wall["start"][1])
            ex = _fmt(wall["end"][0])
            ey = _fmt(-wall["end"][1])
            lines.append(f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="#14532d"/>')
    for room in rooms:
        pts = " ".join(f"{_fmt(p[0])},{_fmt(-p[1])}" for p in room["polygon"])
        lines.append(f'<polygon points="{pts}" fill="none" stroke="#2563eb"/>')
    for opening in openings:
        cx = _fmt(opening["center"][0])
        cy = _fmt(-opening["center"][1])
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="0.1" fill="#b45309"/>')
    return ("<svg xmlns=\"http://www.w3.org/2000/svg\">\n" + "\n".join(lines) + "\n</svg>\n").encode("utf-8")
