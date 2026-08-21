"""Review 2026-08-19 #11 — the evaluator owns truth/prediction projection.

The scorer previously matched against a RECOGNIZER-AUTHORED reduced truth
projection (``_truth_mm_record`` lived in raster_auto.py / cad_exact.py and
stripped orientation/tessellation/vertices before hashing). Projection belongs
in the evaluator package; BOTH sides must be projected by the same
evaluator-owned function so the exact-by-key matcher never runs on a
recognizer-authored reduction of truth.
"""

import inspect

import pytest

from pwa.evaluator import metrics as M
from pwa.evaluator import projection as P


# --- truth side ---------------------------------------------------------------


def test_project_truth_wall_strips_presentation_fields():
    # FX1 truth carries pixel-space presentation fields (a_px/b_px); the
    # evaluator projects onto the mm-only geometry the canonical key is defined
    # over. The projection is evaluator-owned, not recognizer-authored.
    truth = {
        "id": "W-S",
        "kind": "segment",
        "a_mm": [1000, 1500],
        "b_mm": [9000, 1500],
        "a_px": [200, 1700],
        "b_px": [1800, 1700],
    }
    assert P.project_truth_wall(truth) == {
        "kind": "segment",
        "a_mm": [1000, 1500],
        "b_mm": [9000, 1500],
    }


def test_project_truth_arc_drops_tessellation_and_vertices():
    truth = {
        "id": "W-APSE",
        "kind": "circular_arc",
        "center_mm": [9000, 3250],
        "radius_mm": 1500,
        "start_deg": -90,
        "end_deg": 90,
        "tessellation_rule": {"segments": 32, "max_sagitta_px": 0.5},
        "vertices_mm": [[9000.0, 1750.0], [10500.0, 3250.0]],
    }
    assert P.project_truth_wall(truth) == {
        "kind": "circular_arc",
        "center_mm": [9000, 3250],
        "radius_mm": 1500,
        "start_deg": -90,
        "end_deg": 90,
    }


def test_project_truth_segment_canonicalizes_endpoint_order():
    # Same physical wall authored either way projects to ONE canonical record.
    big_first = P.project_truth_wall({"kind": "segment", "a_mm": [9000, 1500], "b_mm": [1000, 1500]})
    small_first = P.project_truth_wall({"kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]})
    assert big_first == small_first


# --- prediction side ----------------------------------------------------------


def test_project_prediction_wall_maps_metres_to_mm_shape():
    pred = {"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]}
    assert P.project_prediction_wall(pred) == {
        "kind": "segment",
        "a_mm": [1000, 1500],
        "b_mm": [9000, 1500],
    }


def test_project_prediction_arc_maps_metres_to_mm_shape():
    pred = {
        "kind": "circular_arc",
        "arc": {"center": [9.0, 3.25], "radius_m": 1.5, "start_deg": -90, "end_deg": 90},
    }
    assert P.project_prediction_wall(pred) == {
        "kind": "circular_arc",
        "center_mm": [9000, 3250],
        "radius_mm": 1500,
        "start_deg": -90,
        "end_deg": 90,
    }


# --- both sides through the SAME projector ------------------------------------


def test_both_sides_project_identically_and_match():
    # The core #11 invariant: truth and prediction go through the SAME
    # evaluator-owned projector, then the frozen matcher compares them.
    truth = {"kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500], "a_px": [200, 1700]}
    pred = {"kind": "segment", "start": [9.0, 1.5], "end": [1.0, 1.5]}  # reversed direction
    assert M.match_wall(P.project_truth_wall(truth), P.project_prediction_wall(pred))


def test_both_sides_project_arcs_identically_and_match():
    truth = {"kind": "circular_arc", "center_mm": [9000, 3250], "radius_mm": 1500,
             "start_deg": -90, "end_deg": 90, "vertices_mm": [[0.0, 0.0]]}
    pred = {"kind": "circular_arc",
            "arc": {"center": [9.0, 3.25], "radius_m": 1.5, "start_deg": -90, "end_deg": 90}}
    assert M.match_wall(P.project_truth_wall(truth), P.project_prediction_wall(pred))


def test_recognizers_no_longer_author_their_own_projection():
    # The defect itself: recognizer modules carried private truth reducers.
    # After the fix the reducer lives ONLY in the evaluator; the recognizer
    # modules expose no private ``_truth_mm_record`` of their own.
    import inspect

    from pwa.floorplan import cad_exact, raster_auto

    for mod in (raster_auto, cad_exact):
        assert not hasattr(mod, "_truth_mm_record"), (
            f"{mod.__name__} still authors its own truth projection"
        )
        # and the public names they keep are evaluator-owned aliases
        assert mod.truth_record_from_wall is P.project_prediction_wall
        assert mod.score_against_truth.__module__ == mod.__name__
    assert inspect.isfunction(P.project_truth_wall)


def test_scorer_actually_delegates_to_the_evaluator_projector(monkeypatch):
    # Behavioural ownership proof: intercepting the evaluator projector MUST
    # change both scorers' output — i.e. the scorers really route every wall
    # through the evaluator-owned projection, not a private copy.
    import pytest

    from pwa.floorplan import raster_auto

    truth = {"walls": [{"kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]}]}
    walls = [{"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]}]
    baseline = raster_auto.score_against_truth(walls, truth)
    assert baseline["correct"] == 1

    import pwa.evaluator.projection as P

    def refuse(wall):
        raise AssertionError("scorer bypassed the evaluator projector")

    monkeypatch.setattr(P, "project_truth_wall", refuse)
    monkeypatch.setattr(P, "project_prediction_wall", refuse)
    with pytest.raises(AssertionError, match="bypassed"):
        raster_auto.score_against_truth(walls, truth)


def test_cad_scorer_actually_delegates_to_the_evaluator_projector(monkeypatch):
    from pwa.floorplan import cad_exact

    truth = {"walls": [{"kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]}]}
    walls = [{"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]}]
    baseline = cad_exact.score_against_truth(walls, truth)
    assert baseline["correct"] == 1

    import pwa.evaluator.projection as P

    def refuse(wall):
        raise AssertionError("scorer bypassed the evaluator projector")

    monkeypatch.setattr(P, "project_truth_wall", refuse)
    monkeypatch.setattr(P, "project_prediction_wall", refuse)
    with pytest.raises(AssertionError, match="bypassed"):
        cad_exact.score_against_truth(walls, truth)
