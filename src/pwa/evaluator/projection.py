"""Evaluator-owned truth/prediction projection (review 2026-08-19 #11).

The frozen WP1 evaluator's exact-by-key matcher is defined over mm-only
geometry records. Raw inputs on both sides carry extra fields:

- FX1 truth walls carry pixel-space presentation fields (``a_px``/``b_px``)
  and, for arcs, ``tessellation_rule``/``vertices_mm``.
- Recognizer-emitted walls are metre-native (``start``/``end`` in m; arcs as
  ``arc`` sub-dicts) and must be mapped onto the same mm shape.

Projection previously lived inside each recognizer module as a private truth
reducer (``_truth_mm_record``), so the scorer matched against a
recognizer-authored reduction of truth. The projection belongs to the
evaluator: BOTH sides are projected here, by these functions, identically,
before ``metrics.match_wall`` compares canonical keys. Deterministic and pure.
"""

from __future__ import annotations


def _int_or_float(value: float) -> int | float:
    """Coerce an integral float to int so canonical JSON matches FX1 truth.

    FX1 authors coordinates/degrees as integer millimetres/degrees (``1000``,
    not ``1000.0``); the evaluator's canonical key is exact-by-key JSON, so a
    value must serialize identically on both sides of the match.
    """
    v = float(value)
    return int(v) if v == int(v) else v


def _canonical_endpoint_order(a: list[float], b: list[float]) -> tuple[list[float], list[float]]:
    """Order a segment's endpoints lexicographically smaller-first.

    The FX1 truth authors every segment with its lexicographically-smaller
    endpoint as ``a_mm``, and the matcher is order-sensitive. A recovered wall
    names endpoints in scan order, so BOTH sides canonicalize to the same order
    here — direction never turns a hit into a miss.
    """
    if tuple(a) > tuple(b):
        return b, a
    return a, b


def project_truth_wall(truth_wall: dict) -> dict:
    """Project a raw FX1 truth wall onto the mm-only canonical geometry record.

    Keeps exactly the fields the frozen evaluator's canonical key is defined
    over (``kind`` + ``a_mm``/``b_mm`` or ``center_mm``/``radius_mm``/
    ``start_deg``/``end_deg``) and discards raster presentation fields
    (``a_px``/``b_px``, ``tessellation_rule``, ``vertices_mm``).
    """
    if truth_wall.get("kind") == "circular_arc":
        return {
            "kind": "circular_arc",
            "center_mm": [_int_or_float(truth_wall["center_mm"][0]), _int_or_float(truth_wall["center_mm"][1])],
            "radius_mm": _int_or_float(truth_wall["radius_mm"]),
            "start_deg": _int_or_float(truth_wall["start_deg"]),
            "end_deg": _int_or_float(truth_wall["end_deg"]),
        }
    a, b = _canonical_endpoint_order(list(truth_wall["a_mm"]), list(truth_wall["b_mm"]))
    return {
        "kind": "segment",
        "a_mm": [_int_or_float(a[0]), _int_or_float(a[1])],
        "b_mm": [_int_or_float(b[0]), _int_or_float(b[1])],
    }


def project_prediction_wall(wall: dict) -> dict:
    """Project an emitted recognizer wall (metres) onto the same mm record shape.

    Accepts the emitted payload shape (``start``/``end`` in metres; arcs as an
    ``arc`` sub-dict with ``center``/``radius_m``/``start_deg``/``end_deg``) and
    maps it onto the identical mm-only record ``project_truth_wall`` produces,
    so the matcher always compares like with like.
    """
    if wall.get("kind") == "circular_arc":
        arc = wall["arc"]
        return {
            "kind": "circular_arc",
            "center_mm": [_int_or_float(arc["center"][0] * 1000.0), _int_or_float(arc["center"][1] * 1000.0)],
            "radius_mm": _int_or_float(arc["radius_m"] * 1000.0),
            "start_deg": _int_or_float(arc["start_deg"]),
            "end_deg": _int_or_float(arc["end_deg"]),
        }
    a, b = _canonical_endpoint_order(
        [wall["start"][0] * 1000.0, wall["start"][1] * 1000.0],
        [wall["end"][0] * 1000.0, wall["end"][1] * 1000.0],
    )
    return {
        "kind": "segment",
        "a_mm": [_int_or_float(a[0]), _int_or_float(a[1])],
        "b_mm": [_int_or_float(b[0]), _int_or_float(b[1])],
    }
