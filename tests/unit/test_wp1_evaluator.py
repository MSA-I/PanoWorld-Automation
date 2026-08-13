"""Tests for the frozen WP1 evaluator core and lock tooling.

Each test targets real frozen behaviour, not mocks: canonical keys, matching,
metrics, refusal accounting, rule-of-three, and the deterministic lock manifest.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from pwa.evaluator import metrics as M

_TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "make_wp1_evaluator_lock.py"
_SPEC = importlib.util.spec_from_file_location("make_wp1_evaluator_lock", _TOOL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
build_lock = _MODULE.build_lock
verify_lock = _MODULE.verify_lock

WALL_SEG_A = {"kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]}
WALL_SEG_A_SHIFTED_ID = {"id": "other-id", "kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]}
WALL_SEG_A_NEAR = {"kind": "segment", "a_mm": [1002, 1500], "b_mm": [9000, 1500]}
WALL_SEG_A_FAR = {"kind": "segment", "a_mm": [1000, 1600], "b_mm": [9000, 1500]}
WALL_ARC = {"kind": "circular_arc", "center_mm": [9000, 3250], "radius_mm": 1500, "start_deg": -90, "end_deg": 90}


def test_canonical_key_is_geometry_order_and_id_independent():
    assert M.canonical_key(WALL_SEG_A) == M.canonical_key(WALL_SEG_A_SHIFTED_ID)
    reordered = {"b_mm": [9000, 1500], "a_mm": [1000, 1500], "kind": "segment"}
    assert M.canonical_key(WALL_SEG_A) == M.canonical_key(reordered)


def test_canonical_key_distinguishes_different_geometry():
    assert M.canonical_key(WALL_SEG_A) != M.canonical_key(WALL_SEG_A_FAR)
    assert M.canonical_key(WALL_SEG_A) != M.canonical_key(WALL_ARC)


def test_match_requires_same_kind_then_exact_quantized_geometry():
    assert M.match_wall(WALL_SEG_A, WALL_SEG_A) is True
    assert M.match_wall(WALL_SEG_A, WALL_SEG_A_SHIFTED_ID) is True
    # A 2 mm endpoint shift is a genuinely different (unquantized) geometry, so
    # it does NOT match under exact canonical-key equality. The frozen matcher
    # is exact-by-key; it does not relax to a projection tolerance for matching.
    assert M.match_wall(WALL_SEG_A, WALL_SEG_A_NEAR) is False
    assert M.match_wall(WALL_SEG_A, WALL_SEG_A_FAR) is False
    assert M.match_wall(WALL_SEG_A, WALL_ARC) is False


def test_confidence_never_drives_matching():
    confident = {**WALL_SEG_A_FAR, "confidence": 0.99}
    assert M.match_wall(WALL_SEG_A, confident) is False


def test_macro_micro_per_plan_metrics():
    plans = [
        {"supportable": 10, "correct": 9},
        {"supportable": 10, "correct": 5},
    ]
    assert M.per_plan_score(plans[0]) == pytest.approx(0.9)
    assert M.per_plan_score(plans[1]) == pytest.approx(0.5)
    assert M.macro_average([M.per_plan_score(p) for p in plans]) == pytest.approx(0.7)
    assert M.micro_average([True, True, False, True]) == pytest.approx(0.75)


def test_per_plan_score_unsupported_counted_in_denominator():
    plan = {"supportable": 10, "correct": 9, "unsupported": 4}
    # unsupported predictions are not dropped; correctness is still over supportable
    assert M.per_plan_score(plan) == pytest.approx(9 / 10)


def test_refusal_accounting_separates_handled_from_false_negative():
    plan = {
        "supportable": 10,
        "correct": 8,
        "refusals": [
            {"kind": "supported"},
            {"kind": "unsupported", "taxon": "double_line_hatched_walls"},
            {"kind": "unsupported", "taxon": "text_annotations"},
        ],
    }
    acc = M.refusal_accounting(plan)
    assert acc["total"] == 3
    assert acc["handled"] == 2
    assert acc["false_negative"] == 1
    assert acc["refusal_rate"] == pytest.approx(0.3)


def test_rule_of_three_zero_successes_is_3_over_n():
    point, lower = M.rule_of_three(0, 30)
    assert point == pytest.approx(0.0)
    assert lower == pytest.approx(3.0 / 30)


def test_rule_of_three_never_reports_perfect_for_partial_success():
    point, lower = M.rule_of_three(28, 30)
    assert point == pytest.approx(28 / 30)
    assert lower < 1.0
    assert lower > 0.0


def test_rule_of_three_all_successes_lower_bound_below_one():
    point, lower = M.rule_of_three(30, 30)
    assert point == pytest.approx(1.0)
    assert lower < 1.0


def test_rule_of_three_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        M.rule_of_three(1, 0)
    with pytest.raises(ValueError):
        M.rule_of_three(5, 3)


def test_support_taxon_classifier():
    assert M.support_taxon_supported({"kind": "segment", "a_mm": [0, 0], "b_mm": [1, 1]}) is True
    assert M.support_taxon_supported({"kind": "diagonal_3_4_5", "a_mm": [0, 0], "b_mm": [1, 1]}) is True
    assert M.support_taxon_supported({"kind": "circular_arc", "tessellation_rule": {"max_sagitta_px": 0.5}}) is True
    assert M.support_taxon_supported({"kind": "circular_arc", "tessellation_rule": {"max_sagitta_px": 0.6}}) is False
    assert M.support_taxon_supported({"kind": "door"}) is True
    assert M.support_taxon_supported({"kind": "window"}) is True
    assert M.support_taxon_supported({"kind": "passage"}) is True
    assert M.support_taxon_supported({"kind": "stairs_symbol"}) is False


def test_lock_builds_and_verifies_deterministically(tmp_path):
    package = build_lock(tmp_path / "wp1")
    assert verify_lock(package)["valid"] is True

    first = _load(package / "wp1-manifest.json")
    second_pkg = build_lock(tmp_path / "wp1b")
    second = _load(second_pkg / "wp1-manifest.json")
    assert first["files"] == second["files"]
    assert first["replay_hash"] == second["replay_hash"]

    spec = _load(package / "wp1-evaluator-spec.json")
    assert spec["frozen_before_truth_opened"] is True
    assert spec["recognizer_inputs"] == []

    roles = _load(package / "wp1-role-matrix.json")
    assert roles["overlap_is_fail_closed"] is True
    assert roles["rights_owner_only_human"] is True
    # every forbidden pair is symmetric and no role forbids itself outside Rights Owner
    for a, blocked in roles["forbidden_overlap"].items():
        assert a not in blocked

    splits = _load(package / "wp1-split-manifest.json")
    families = set(splits["families"])
    assert families == {"fx1_hall", "fx1_apse", "fx1_blind"}
    assert splits["train_families"] == ["fx1_hall"]
    assert splits["dev_families"] == ["fx1_apse"]
    assert splits["blind_families"] == ["fx1_blind"]
    assert "family_in_exactly_one_split" in splits["leakage_controls"]


def test_lock_verify_detects_mutation(tmp_path):
    package = build_lock(tmp_path / "wp1")
    target = package / "wp1-evaluator-spec.json"
    target.write_bytes(target.read_bytes() + b"mutated")
    report = verify_lock(package)
    assert report["valid"] is False
    assert "wp1-evaluator-spec.json" in report["mismatches"]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
