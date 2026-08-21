"""raster_auto (Product B-AUTO) emitter and FX1-truth scorer.

The emitter converts ``raster_auto_worker.extract_raster_auto`` geometry (mm,
FX1 truth space) into a ``floorplan_parse`` 1.2.0 payload with
``source_class: "raster_auto"``, satisfying the frozen recognition invariants
before emission (fail-closed). The scorer binds product walls against the FX1
frozen truth using the frozen WP1 evaluator's exact-by-key canonical matcher.

The two-anchor scale fit (U-2), the fixed symbol/style guide (U-5), and the
arc bounds (U-3) remain BLOCKED decisions; this module implements the shape the
contract requires and never fabricates truth or scale.
"""

from __future__ import annotations

import math

from pwa.evaluator import metrics as M
from pwa.evaluator import projection as P
from pwa.floorplan import recognition


def _quant_m(value_m: float) -> float:
    """Quantize a metre value onto the frozen evaluator grid (0.01 mm), returned in metres."""
    return M.quantize(float(value_m) * 1000.0, M.QUANTIZE_MM) / 1000.0


def _quant_mm(value_mm: float) -> float:
    return M.quantize(float(value_mm), M.QUANTIZE_MM)


def _int_mm(value_m: float) -> int | float:
    """Return an integer millimetre when the quantized value is integral."""
    mm = round(float(value_m) * 1000.0, 6)
    return int(mm) if mm == int(mm) else mm


def _wall_id_for(wall_id: object) -> str:
    """Stringify an opening's host-wall reference into the emitted wall id space.

    Walls are emitted as ``w-{index:04d}``; the worker references a host wall by
    its integer index. The 1.2.0 schema requires ``openings[].wall_id`` to be a
    non-empty STRING, and the reference must resolve to an emitted wall id.
    """
    if wall_id is None:
        return ""
    if isinstance(wall_id, str) and wall_id.startswith("w-"):
        return wall_id
    try:
        return f"w-{int(wall_id):04d}"
    except (TypeError, ValueError):
        return str(wall_id)


def emit_raster_auto_parse(walls: list[dict], rooms: list[dict], openings: list[dict], *,
                           scale_m_per_px: float | None = None) -> tuple[dict, list[str]]:
    """Emit a floorplan_parse 1.2.0 payload (source_class raster_auto).

    Inputs are in metres. Every wall must carry a sourced thickness (> 0) and
    open ings must satisfy the passage span bound. ``scale_m_per_px``, when
    supplied, is emitted as the validated source scale (review 2026-08-19 #13:
    the resolved scale was previously dropped and the field hardcoded to None).
    Returns ``(payload, findings)``.
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
            "confidence": float(wall.get("confidence", 1.0)),
            "provenance": {
                "source_kind": "raster_auto",
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
                "confidence": float(room.get("confidence", 1.0)),
                "area_m2": room.get("area_m2"),
                "provenance": {
                    "source_kind": "raster_auto",
                    "source_ref": room["source_ref"],
                    "source_polygon": [list(p) for p in room["polygon"]],
                },
            }
        )

    out_openings = []
    for opening in openings:
        if opening["kind"] == "passage":
            recognition_findings.extend(recognition.check_passage_span(opening["width_m"]))
        else:
            # door/window span is bounded by the frozen support taxonomy too (F-6):
            # an over-wide door or window is unsupported and must fail closed.
            recognition_findings.extend(recognition.check_opening_span(opening["width_m"]))
        out_openings.append(
            {
                "id": f"o-{opening['index']:04d}",
                "type": opening["kind"],
                "wall_id": _wall_id_for(opening.get("wall_id")),
                "center": [_quant_m(opening["center"][0]), _quant_m(opening["center"][1])],
                "width_m": float(opening["width_m"]),
                "confidence": float(opening.get("confidence", 1.0)),
                "provenance": {
                    "source_kind": "raster_auto",
                    "source_ref": opening["source_ref"],
                    "source_center": [opening["center"][0], opening["center"][1]],
                },
            }
        )

    payload = {
        "units": "m",
        "source_class": "raster_auto",
        "scale_m_per_px": scale_m_per_px,
        "rooms": out_rooms,
        "walls": out_walls,
        "openings": out_openings,
    }
    if recognition_findings:
        # Fail-closed (W-17 / AT-18): never emit geometry alongside a blocking
        # recognition finding. The contract layer must hold the same property as
        # the worker's source-error channel.
        return _empty_payload(), recognition_findings
    return payload, recognition_findings


def parse_raster_auto(path, *, derive_scale: bool) -> tuple[dict, list[str], list[dict]]:
    """End-to-end Product B-AUTO: raster -> raster_auto floorplan_parse 1.2.0.

    Returns ``(payload, recognition_findings, source_errors)``. The worker
    recovers mm geometry; the emitter converts to metres. Fail-closed: if the
    worker reports any blocking source error, the emitted geometry is EMPTY —
    a hallucinated partial plan is never produced (W-17 / AT-18).
    """
    from pwa.floorplan.raster_auto_worker import extract_raster_auto

    raw = extract_raster_auto(path, derive_scale=derive_scale)
    source_errors = raw["errors"]
    if source_errors:
        # Fail closed: do not emit any geometry on a blocking source finding.
        empty = _empty_payload()
        return empty, [], source_errors
    mm_per_px = float(raw["frame"].get("scale_m_per_px") or 0.0) * 1000.0 if raw["frame"].get("scale_m_per_px") else None
    m_per_px = raw["frame"].get("scale_m_per_px")
    walls_m = [_wall_to_metres(w, mm_per_px) for w in raw["walls"] if w.get("start_mm") is not None]
    rooms_m = [_room_to_metres(r, mm_per_px) for r in raw["rooms"] if r.get("polygon") is not None]
    openings_m = [_opening_to_metres(o, mm_per_px) for o in raw["openings"] if o.get("center") is not None]
    payload, findings = emit_raster_auto_parse(walls_m, rooms_m, openings_m, scale_m_per_px=m_per_px)
    return payload, findings, source_errors


def _empty_payload() -> dict:
    return {
        "units": "m",
        "source_class": "raster_auto",
        "scale_m_per_px": None,
        "rooms": [],
        "walls": [],
        "openings": [],
    }


def _wall_to_metres(wall: dict, mm_per_px: float | None) -> dict:
    out = {
        "index": wall["index"],
        "source_ref": wall["source_ref"],
        "kind": wall["kind"],
        "start": [wall["start_mm"][0] / 1000.0, wall["start_mm"][1] / 1000.0],
        "end": [wall["end_mm"][0] / 1000.0, wall["end_mm"][1] / 1000.0],
        "thickness_m": wall.get("thickness_m"),
        "confidence": wall.get("confidence", 1.0),
    }
    if wall["kind"] == "circular_arc" and wall.get("arc"):
        arc_mm = wall["arc"]
        out["arc"] = {
            "center": [arc_mm["center"][0] / 1000.0, arc_mm["center"][1] / 1000.0],
            "radius_m": arc_mm["radius_mm"] / 1000.0,
            "start_deg": arc_mm.get("start_deg", 0.0),
            "end_deg": arc_mm.get("end_deg", 0.0),
            "sweep": arc_mm.get("sweep", "ccw"),
            "bulge": arc_mm.get("bulge", 0.0),
            "max_sagitta_px": arc_mm.get("max_sagitta_px", 0.5),
        }
    return out


def _room_to_metres(room: dict, mm_per_px: float | None) -> dict:
    return {
        "index": room["index"],
        "source_ref": room["source_ref"],
        "polygon": [[p[0] / 1000.0, p[1] / 1000.0] for p in room["polygon"]],
        "area_m2": room.get("area_m2"),
    }


def _opening_to_metres(opening: dict, mm_per_px: float | None) -> dict:
    return {
        "index": opening["index"],
        "source_ref": opening["source_ref"],
        "kind": opening["kind"],
        "center": [opening["center"][0] / 1000.0, opening["center"][1] / 1000.0],
        "width_m": opening["width_m"],
        "wall_id": opening.get("wall_id"),
    }


# --- FX1 truth binding ------------------------------------------------------


# Evaluator-owned projection (review 2026-08-19 #11): the recognizer authors no
# projection of its own. ``truth_record_from_wall`` IS
# ``pwa.evaluator.projection.project_prediction_wall`` (kept under the
# historical name for backwards-compatible imports); truth is projected by the
# same evaluator-owned function at scoring time.
truth_record_from_wall = P.project_prediction_wall


def score_against_truth(walls: list[dict], truth: dict) -> dict:
    """Score raster_auto walls against the FX1 frozen truth (exact-by-key).

    BOTH sides are projected by the evaluator-owned projector
    (``pwa.evaluator.projection``) before the frozen matcher compares them —
    the scorer never runs on a recognizer-authored reduction of truth.
    """
    truth_walls = [P.project_truth_wall(w) for w in truth.get("walls", [])]
    pred_walls = [P.project_prediction_wall(w) for w in walls]
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


# --- evidence rendering -----------------------------------------------------


def _fmt(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text if text not in {"-0", "-0.0", ""} else "0"


def render_raster_auto_svg(walls: list[dict], rooms: list[dict], openings: list[dict]) -> bytes:
    """Deterministic SVG evidence overlay for raster_auto geometry (metres)."""
    lines: list[str] = []
    for wall in walls:
        if wall["kind"] == "circular_arc":
            arc = wall["arc"]
            cx, cy, r = arc["center"][0], arc["center"][1], arc["radius_m"]
            sx = _fmt(cx + r * math.cos(math.radians(arc["start_deg"])))
            sy = _fmt(-(cy + r * math.sin(math.radians(arc["start_deg"]))))
            ex = _fmt(cx + r * math.cos(math.radians(arc["end_deg"])))
            ey = _fmt(-(cy + r * math.sin(math.radians(arc["end_deg"]))))
            sweep = 0 if arc["sweep"] == "ccw" else 1
            lines.append(f'<path d="M {sx},{sy} A {_fmt(r)},{_fmt(r)} 0 0 {sweep} {ex},{ey}" fill="none" stroke="#166534"/>')
        else:
            sx = _fmt(wall["start"][0])
            sy = _fmt(-wall["start"][1])
            ex = _fmt(wall["end"][0])
            ey = _fmt(-wall["end"][1])
            lines.append(f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="#166534"/>')
    for room in rooms:
        pts = " ".join(f"{_fmt(p[0])},{_fmt(-p[1])}" for p in room["polygon"])
        lines.append(f'<polygon points="{pts}" fill="none" stroke="#2563eb"/>')
    for opening in openings:
        cx = _fmt(opening["center"][0])
        cy = _fmt(-opening["center"][1])
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="0.1" fill="#b45309"/>')
    return ("<svg xmlns=\"http://www.w3.org/2000/svg\">\n" + "\n".join(lines) + "\n</svg>\n").encode("utf-8")
