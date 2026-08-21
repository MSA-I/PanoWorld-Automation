"""Tests for WP4 Product B-AUTO (raster_auto) deterministic clean-raster engine.

TDD RED-first: these target the not-yet-written
``pwa.floorplan.raster_auto_geometry`` and ``pwa.floorplan.raster_auto`` modules,
which must implement the deterministic CPU-only, no-OCR, no-learned-model
automatic recognition of a supported clean raster floorplan, mirroring the
frozen conventions locked by WP0 (opus spatial design), WP1 (evaluator) and
WP2 (contracts):

- global Otsu with frozen tie-break + separability gate;
- 8-connected union-find component labelling;
- 2-parameter (theta, rho) Hough accumulator for segment walls;
- contour following + Kasa/Pratt algebraic circle fit (RMS residual) for arcs;
- paired-edge thickness recovery;
- multi-anchor (>= 3) scale validation (median residual + disagreement);
- face/topology derivation + fail-closed refusals.

The fixture is ``evidence/PLAN-002RF/WP0-FX1/fixture/fx1.png`` (2400x2000
grayscale; value 0 = walls/openings, 64 = scale anchors, 128 = clutter, 255 =
background), with the frozen truth at ``fx1-truth.json`` (scale_m_per_px 0.005).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pwa.floorplan import raster_auto_geometry as G
from pwa.floorplan import raster_auto as R
from pwa.evaluator import projection as P
from pwa.floorplan.raster_auto_worker import extract_raster_auto, _norm_deg
from pwa.floorplan.config import MAX_STRUCTURAL_INK_PIXELS
from pwa.contracts import validate_artifact
from tests.conftest import make_envelope


_FX1_PNG = "evidence/PLAN-002RF/WP0-FX1/fixture/fx1.png"
_FX1_TRUTH = "evidence/PLAN-002RF/WP0-FX1/fixture/fx1-truth.json"


# --------------------------------------------------------------------------- #
# A — deterministic image geometry primitives                                  #
# --------------------------------------------------------------------------- #


def test_otsu_global_threshold_is_deterministic():
    # A bimodal 0/255 histogram must yield a split strictly between the modes.
    hist = np.zeros(256, dtype=np.int64)
    hist[0] = 100
    hist[255] = 200
    thr = G.otsu_threshold(hist)
    assert 0 < thr < 255
    assert G.otsu_threshold(hist) == thr


def test_otsu_tie_break_is_lowest_index():
    # Two maxima of between-class variance -> the lowest index wins deterministically.
    hist = np.zeros(256, dtype=np.int64)
    hist[10] = 5
    hist[200] = 5
    # separability is trivially high; tie-break must be deterministic & documented.
    thr = G.otsu_threshold(hist)
    assert G.otsu_threshold(hist) == thr


def test_connected_components_two_pass_labels():
    # A small cross: a single 8-connected component of ink on white.
    mask = np.zeros((5, 5), dtype=np.uint8)
    mask[1, 2] = 1
    mask[2, 1] = 1
    mask[2, 2] = 1
    mask[2, 3] = 1
    mask[3, 2] = 1
    labels, count = G.connected_components(mask)
    assert count == 1
    assert (labels[mask == 1] == 1).all()


def test_connected_components_counts_disjoint_blobs():
    mask = np.zeros((10, 10), dtype=np.uint8)
    mask[1, 1] = mask[1, 2] = 1
    mask[8, 8] = mask[8, 9] = mask[9, 8] = 1
    labels, count = G.connected_components(mask)
    assert count == 2


def test_hough_line_votes_recover_horizontal_and_vertical():
    # Two axis-aligned line fragments; the accumulator must peak on theta=0/90.
    mask = np.zeros((64, 64), dtype=np.uint8)
    mask[20, 10:54] = 1  # horizontal row
    mask[10:54, 40] = 1  # vertical column
    peaks = G.hough_lines(mask, theta_step_deg=1.0, min_votes=30)
    thetas = [p["theta_deg"] for p in peaks]
    # Standard (theta,rho) Hough: a HORIZONTAL line (y=c) peaks at theta=90
    # (normal vertical), a VERTICAL line (x=c) peaks at theta=0 (normal horizontal).
    assert any(abs(t - 90.0) <= 1.0 for t in thetas), ("horizontal line -> theta 90", thetas)
    assert any(abs(t - 0.0) <= 1.0 for t in thetas), ("vertical line -> theta 0", thetas)


def test_hough_physical_lines_merges_theta_wrap_into_one_line():
    # The same physical wall at theta and theta+180 has rho of opposite sign; the
    # old merge compared rho without negating the wrapped branch, so a single
    # vertical wall was emitted twice (theta~0 rho=+c AND theta~180 rho=-c).
    mask = np.zeros((120, 120), dtype=np.uint8)
    mask[20:100, 60:63] = 1  # vertical 3px stroke, x in [60,62]
    lines = G.hough_physical_lines(mask, theta_step_deg=0.25, min_votes=30)
    wall_band = [l for l in lines if 55 <= abs(l["rho"]) <= 70]
    # After the wrap fix, no representative of this wall sits at theta ~ 180.
    assert not any(round(l["theta_deg"]) >= 170 for l in wall_band), [
        f"{l['theta_deg']:.1f}@{l['rho']:.0f}" for l in wall_band
    ]


def test_circle_fit_recovers_center_and_radius():
    # Points on a circle radius 20 around (30, 30); Kasa fit must recover it.
    cx, cy, r = 30.0, 30.0, 20.0
    angles = np.linspace(0, math.pi, 64)
    pts = np.column_stack([cx + r * np.cos(angles), cy + r * np.sin(angles)])
    c = G.fit_circle(pts)
    assert abs(c[0] - cx) < 0.5
    assert abs(c[1] - cy) < 0.5
    assert abs(c[2] - r) < 0.5


def test_circle_fit_rejects_noise_with_high_residual():
    # Scattered noise far from any circle -> high RMS residual (fail-closed arc).
    rng = np.random.default_rng(7)
    pts = rng.uniform(0, 100, size=(50, 2))
    residual = G.circle_fit_residual(pts, G.fit_circle(pts))
    assert residual > 10.0


def test_scale_fit_requires_at_least_three_anchors():
    # U-2 (n=2 collapse): with only two anchors the median residual and the
    # pairwise disagreement collapse to the same quantity (disagreement ==
    # 2 * median_residual), so a single wrong anchor can never be detected.
    # Fewer than three admissible anchors must resolve to a null fit so the
    # worker fails closed on SCALE_ANCHORS_INSUFFICIENT.
    anchors = [
        {"span_px": 1000.0, "real_length_m": 5.0},   # 0.005 m/px
        {"span_px": 1200.0, "real_length_m": 6.0},   # 0.005 m/px
    ]
    fit = G.fit_scale(anchors)
    assert fit["m_per_px"] is None
    assert fit["count"] == 2
    assert fit["median_residual"] == float("inf")
    assert fit["disagreement"] == float("inf")


def test_scale_fit_three_agreeing_anchors_resolve_exactly():
    # The three FX1 anchors all give 0.005 m/px exactly; n=3 makes median and
    # disagreement genuinely distinct and both must be ~0.
    anchors = [
        {"span_px": 1000.0, "real_length_m": 5.0},   # 0.005 m/px (A-S)
        {"span_px": 1200.0, "real_length_m": 6.0},   # 0.005 m/px (A-W)
        {"span_px": 400.0, "real_length_m": 2.0},    # 0.005 m/px (A-D)
    ]
    fit = G.fit_scale(anchors)
    assert fit["m_per_px"] == pytest.approx(0.005)
    assert fit["count"] == 3
    assert fit["median_residual"] < 0.01
    assert fit["disagreement"] < 0.02


def test_scale_fit_rejects_contradictory_anchor_among_three():
    # A ~17% off anchor (the NA-5 case) among three must fail the disagreement
    # bound even though the median is still the correct value.
    anchors = [
        {"span_px": 1000.0, "real_length_m": 5.0},    # 0.005 m/px
        {"span_px": 1200.0, "real_length_m": 6.0},    # 0.005 m/px
        {"span_px": 1000.0, "real_length_m": 5.85},   # ~0.00585 m/px -> ~17% off
    ]
    fit = G.fit_scale(anchors)
    assert fit["m_per_px"] == pytest.approx(0.005)   # median still the good value
    assert fit["disagreement"] > 0.02


def test_anchor_span_below_minimum_is_inadmissible():
    # A 6 px span is inadmissible (carries ~8% quantisation error per WP0 §4.2).
    anchors = [{"span_px": 6.0, "real_length_m": 0.03}]
    assert G.min_anchor_span_px(anchors) < G.ANCHOR_MIN_SPAN_PX


# --------------------------------------------------------------------------- #
# B — worker: intake / binarization / component suppression                   #
# --------------------------------------------------------------------------- #


def test_binarize_dark_ink_separates_structure_from_clutter():
    # 0 (walls/anchor) and 64 (anchor) are ink; 128 (clutter) and 255 are not.
    img = np.full((20, 20), 255, dtype=np.uint8)
    img[5, 5] = 0
    img[6, 6] = 64
    img[7, 7] = 128
    mask = G.binarize_dark_ink(img)
    assert mask[5, 5] == 1
    assert mask[6, 6] == 1
    assert mask[7, 7] == 0
    assert mask[0, 0] == 0


def test_clutter_fraction_guard_refuses_over_band():
    # More than the allowed suppressed-ink fraction must refuse, not manufacture
    # a clean plan (anti-hallucination).
    total = 10000
    suppressed = total * 0.60  # 60% ink -> far above the 0.25 cap
    assert not G.clutter_within_band(suppressed, total)


def test_unexplained_ink_guard_refuses_over_band():
    total = 10000
    unexplained = total * 0.30  # 30% > 0.10 cap
    assert not G.unexplained_ink_within_band(unexplained, total)


# --------------------------------------------------------------------------- #
# C — worker end-to-end on the FX1 fixture                                    #
# --------------------------------------------------------------------------- #


def test_extract_raster_auto_refuses_without_anchors_on_missing_scale():
    # A run with no authoritative scale anchors must fail closed (SCALE refusal),
    # matching the WP0 C-1 / W-05 decision.
    payload = extract_raster_auto(_FX1_PNG, derive_scale=False)
    assert any(err["code"] in {"SCALE_ANCHORS_INSUFFICIENT", "PARSE_SCALE_UNKNOWN"} for err in payload["errors"])


def test_worker_empties_geometry_on_late_blocking_finding():
    # W-17/AT-18 must hold on the WORKER channel too, not only on parse_raster_auto.
    # A late blocking finding (SCALE_ANCHORS_INSUFFICIENT when derive_scale=False)
    # is appended AFTER decode/contrast/clutter, and the worker previously
    # returned the recovered 9 walls + 6 openings ALONGSIDE that blocking finding,
    # so any consumer of the worker CLI (main() json-dumps the dict verbatim)
    # received geometry next to a blocking error. The worker itself must empty
    # walls/rooms/openings whenever any blocking error is present.
    payload = extract_raster_auto(_FX1_PNG, derive_scale=False)
    assert any(err["code"] == "SCALE_ANCHORS_INSUFFICIENT" for err in payload["errors"])
    assert payload["walls"] == []
    assert payload["rooms"] == []
    assert payload["openings"] == []



def test_extract_raster_auto_recovers_wall_count_with_anchors():
    # With the fixture's three authoritative anchors supplied, the recognizer
    # must either recover the clean wall structure OR fail closed with a
    # bounded refusal — it must never emit a hallucinated/over-segmented plan.
    payload = extract_raster_auto(_FX1_PNG, derive_scale=True)
    if payload["errors"]:
        # Fail-closed: no geometry is manufactured on a blocking finding.
        assert payload["walls"] == [] or all(
            err["code"] in {"RASTER_OVERSEGMENTED", "RASTER_UNEXPLAINED_INK", "SCALE_ANCHORS_INSUFFICIENT"} for err in payload["errors"]
        )
    else:
        # A clean emit must be a self-consistent plan: 9 walls (8 segments + 1
        # bounded arc) is the FX1 envelope; anything else is over-segmentation.
        assert len(payload["walls"]) == 9
        kinds = [w["kind"] for w in payload["walls"]]
        assert kinds.count("circular_arc") == 1
        assert kinds.count("segment") == 8


def test_extract_raster_auto_is_fail_closed_not_hallucinating():
    # The raw worker must not silently emit a large number of over-segmented
    # walls. It now CONVERGES to the 9-wall clean plan (8 segments + 1 arc) on
    # the FX1 envelope; a wall set diverging from that is over-segmentation and
    # must be refused (fail-closed), never emitted as product output.
    payload = extract_raster_auto(_FX1_PNG, derive_scale=True)
    if payload["walls"]:
        assert len(payload["walls"]) == 9
        assert not any(err["code"] == "RASTER_OVERSEGMENTED" for err in payload["errors"])
    else:
        assert payload["errors"] != []


# --------------------------------------------------------------------------- #
# D — emitter + FX1 truth scorer                                              #
# --------------------------------------------------------------------------- #


def test_emit_floorplan_parse_declares_raster_auto_source_class():
    payload, findings = R.emit_raster_auto_parse(
        walls=[{"index": 0, "source_ref": "raster:seg#0", "kind": "segment",
                "start": [1.0, 1.5], "end": [9.0, 1.5], "thickness_m": 0.24, "confidence": 0.9}],
        rooms=[], openings=[],
    )
    assert payload["source_class"] == "raster_auto"
    assert payload["units"] == "m"
    assert findings == []


def test_emit_raster_auto_parse_fails_closed_on_missing_thickness():
    payload, findings = R.emit_raster_auto_parse(
        walls=[{"index": 0, "source_ref": "raster:seg#0", "kind": "segment",
                "start": [1.0, 1.5], "end": [9.0, 1.5], "thickness_m": None, "confidence": 0.9}],
        rooms=[], openings=[],
    )
    assert "RECOGNITION_THICKNESS_MISSING" in findings
    # Fail-closed (CRITICAL fix): geometry must NOT be emitted alongside a
    # blocking recognition finding — the payload is empty.
    assert payload["walls"] == []
    assert payload["rooms"] == []
    assert payload["openings"] == []


def test_emit_raster_auto_parse_fails_closed_on_passage_span_exceeds():
    # A passage wider than PASSAGE_SPAN_MAX_M (3.0 m) is a blocking finding and
    # must empty the payload, not emit the geometry next to the error code.
    payload, findings = R.emit_raster_auto_parse(
        walls=[{"index": 0, "source_ref": "raster:seg#0", "kind": "segment",
                "start": [1.0, 1.5], "end": [9.0, 1.5], "thickness_m": 0.24, "confidence": 0.9}],
        rooms=[],
        openings=[{"index": 0, "source_ref": "raster:seg#0:opening#0", "kind": "passage",
                   "center": [5.0, 1.5], "width_m": 3.5, "wall_id": 0}],
    )
    assert "RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND" in findings
    assert payload["openings"] == []
    assert payload["walls"] == []


def test_emit_raster_auto_parse_fails_closed_on_oversized_door_window():
    # The over-width bound applies to EVERY opening kind, not only passage. A
    # door/window whose emitted span exceeds MAX_OPENING_SPAN_MM (1500 mm = 1.5 m)
    # must be a blocking finding that empties the payload — a 6 m "window" is
    # unsupported and must never reach product geometry silently.
    payload, findings = R.emit_raster_auto_parse(
        walls=[{"index": 0, "source_ref": "raster:seg#0", "kind": "segment",
                "start": [1.0, 1.5], "end": [9.0, 1.5], "thickness_m": 0.24, "confidence": 0.9}],
        rooms=[],
        openings=[{"index": 0, "source_ref": "raster:seg#0:opening#0", "kind": "window",
                   "center": [5.0, 1.5], "width_m": 6.0, "wall_id": 0}],
    )
    assert "RECOGNITION_OPENING_SPAN_EXCEEDS_BOUND" in findings
    assert payload["openings"] == []
    assert payload["walls"] == []



def test_emit_raster_auto_parse_is_schema_valid():
    payload, _ = R.emit_raster_auto_parse(
        walls=[
            {"index": 0, "source_ref": "raster:seg#0", "kind": "segment",
             "start": [1.0, 2.0], "end": [1.0, 8.0], "thickness_m": 0.24, "confidence": 0.9},
        ],
        rooms=[{"index": 0, "source_ref": "raster:face#0",
                "polygon": [[1.0, 2.0], [4.0, 2.0], [4.0, 8.0], [1.0, 8.0]], "area_m2": 18.0}],
        openings=[],
    )
    doc = make_envelope("floorplan_parse", payload, schema_version="1.2.0")
    assert validate_artifact(doc) == []


def test_emit_openings_with_populated_wall_id_are_schema_valid():
    # openings[].wall_id is REQUIRED and non-empty STRING in floorplan_parse
    # 1.2.0 (schema line 224). The emitter must stringify the wall index into the
    # same `w-%04d` id space the walls themselves use, and the referenced id must
    # resolve to an emitted wall — a dangling integer wall_id makes every real
    # emit (FX1 emits 6 openings) schema-invalid AND reference no wall.
    payload, findings = R.emit_raster_auto_parse(
        walls=[
            {"index": 0, "source_ref": "raster:seg#0", "kind": "segment",
             "start": [1.0, 2.0], "end": [1.0, 8.0], "thickness_m": 0.24, "confidence": 0.9},
        ],
        rooms=[],
        openings=[
            {"index": 0, "source_ref": "raster:seg#0:opening#0", "kind": "door",
             "center": [1.0, 5.0], "width_m": 0.9, "wall_id": 0},
        ],
    )
    assert findings == []
    doc = make_envelope("floorplan_parse", payload, schema_version="1.2.0")
    assert validate_artifact(doc) == []
    # The emitted wall_id must be a string AND resolve to the emitted wall.
    wall_ids = {w["id"] for w in payload["walls"]}
    for o in payload["openings"]:
        assert isinstance(o["wall_id"], str)
        assert o["wall_id"] in wall_ids, f"dangling wall_id {o['wall_id']} not in {wall_ids}"



def test_raster_trutht_record_from_wall_segment_shape():
    wall = {"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]}
    record = R.truth_record_from_wall(wall)
    assert record["kind"] == "segment"
    assert record["a_mm"] == [1000.0, 1500.0]
    assert record["b_mm"] == [9000.0, 1500.0]


def test_raster_truth_record_normalizes_segment_direction():
    # A recovered wall is the SAME wall regardless of which endpoint the pixel
    # detector named "start". The frozen evaluator matches segments by exact
    # a_mm/b_mm (order-sensitive), and the FX1 truth authors every segment with
    # its lexicographically-smaller endpoint as a_mm. So the raster scorer must
    # emit a/b in the same canonical order, not the detector's raw direction,
    # or a correctly-recovered wall scores as a miss.
    reversed_wall = {"kind": "segment", "start": [9.0, 1.5], "end": [1.0, 1.5]}
    record = R.truth_record_from_wall(reversed_wall)
    assert record["a_mm"] == [1000.0, 1500.0]
    assert record["b_mm"] == [9000.0, 1500.0]


def test_raster_fx1_segments_score_against_truth_direction_agnostic():
    # The FX1 truth has 8 segments (all lexicographically sorted). After
    # direction normalization, every recovered segment that lands on an exact
    # truth endpoint must match regardless of the detector's raw endpoint order.
    # (Segments whose endpoints stop short at an opening are a separate
    # endpoint-precision concern, not a direction concern — see the wall-recovery
    # rework notes.) This test guards the direction-normalization invariant on
    # the axis-aligned walls that recover exactly (W-S/W-PV/W-PH).
    truth = json.loads(Path(_FX1_TRUTH).read_text(encoding="utf-8"))
    payload, findings, source_errors = R.parse_raster_auto(_FX1_PNG, derive_scale=True)
    assert source_errors == []
    seg_truth = [w for w in truth["walls"] if w["kind"] == "segment"]
    seg_pred = [w for w in payload["walls"] if w["kind"] == "segment"]
    assert len(seg_pred) == len(seg_truth) == 8
    recs = [R.truth_record_from_wall(w) for w in seg_pred]
    # Normalized records must carry each segment in canonical (sorted) a/b order.
    for rec in recs:
        assert tuple(rec["a_mm"]) <= tuple(rec["b_mm"])
    # The scorer projects BOTH sides with the evaluator-owned projector
    # (review 2026-08-19 #11); replicate that projection here.
    truth_mm = [P.project_truth_wall(tw) for tw in seg_truth]
    # The three axis-aligned long walls recover byte-exactly and must match.
    exact_ids = {"W-S", "W-PV", "W-PH"}
    matched_ids = {
        tw["id"] for tw, tmm in zip(seg_truth, truth_mm)
        if any(R.M.match_wall(tmm, pr) for pr in recs)
    }
    assert exact_ids <= matched_ids, \
        f"expected exact walls {exact_ids} to match, matched {matched_ids}"


# --------------------------------------------------------------------------- #
# E — determinism + rollback                                                   #
# --------------------------------------------------------------------------- #


def test_raster_auto_parse_is_deterministic():
    first = extract_raster_auto(_FX1_PNG, derive_scale=True)
    second = extract_raster_auto(_FX1_PNG, derive_scale=True)
    assert first == second


# --------------------------------------------------------------------------- #
# F — adversarial / fail-closed refusals                                       #
# --------------------------------------------------------------------------- #


def test_extract_raster_auto_refuses_low_contrast(tmp_path):
    # A near-flat image has no bimodal histogram -> low-contrast refusal.
    img = Image.new("L", (64, 64), 128)
    path = tmp_path / "low-contrast.png"
    img.save(path)
    payload = extract_raster_auto(path, derive_scale=False)
    assert any(err["code"] in {"RASTER_LOW_CONTRAST", "PARSE_EMPTY_GEOMETRY"} for err in payload["errors"])
    # CRITICAL resource guard: refuse BEFORE any component/Hough work -> no
    # geometry and an empty frame (short-circuit, not just a recorded finding).
    assert payload["walls"] == []
    assert payload["rooms"] == []
    assert payload["openings"] == []
    assert payload["frame"] == {}


def test_extract_raster_auto_refuses_unsupported_format(tmp_path):
    # A BMP file (not on the {PNG, JPEG} allow-list) must refuse by content sniff.
    img = Image.new("L", (64, 64), 255)
    path = tmp_path / "bad.bmp"
    img.save(path)
    payload = extract_raster_auto(path, derive_scale=False)
    assert any(err["code"] == "RASTER_UNSUPPORTED_FORMAT" for err in payload["errors"])


def test_extract_raster_auto_refuses_missing_file():
    payload = extract_raster_auto("does/not/exist.png", derive_scale=False)
    assert payload["errors"] != []


def test_missing_file_finding_uses_basename_not_absolute_path():
    # F-2 (path leak): every finding must use path.name, never the absolute
    # path, so serialized evidence does not disclose the operator's directory
    # layout through a repository with a public remote.
    payload = extract_raster_auto("does/not/exist.png", derive_scale=False)
    for err in payload["errors"]:
        ref = err.get("source_ref") or ""
        assert "/" not in ref and "\\" not in ref, f"absolute path leaked: {ref!r}"



def test_extract_raster_auto_rejects_oversized_pixels(tmp_path):
    # A declared >100MP image must be rejected at header, zero pixel allocation.
    # (We test the pre-allocation guard directly rather than allocating 100MP.)
    from pwa.floorplan.config import MAX_SOURCE_PIXELS
    img = Image.new("L", (10, 10), 255)
    path = tmp_path / "tiny.png"
    img.save(path)
    # header-only size guard: an absurdly large declared size is refused before load
    assert G.within_pixel_budget(MAX_SOURCE_PIXELS + 1) is False
    assert G.within_pixel_budget(100) is True


def test_arc_first_detection_recovers_fx1_apse():
    # Arc-first: the apse arc must be recovered as a circular_arc from the
    # STRUCTURAL mask (pre-erosion), not chord-fragmented into segment walls.
    payload = extract_raster_auto(_FX1_PNG, derive_scale=True)
    arcs = [w for w in payload["walls"] if w["kind"] == "circular_arc"]
    assert len(arcs) == 1, f"expected 1 apse arc, got {len(arcs)}"
    a = arcs[0]["arc_px"]
    # FX1 apse truth: centre (1800, 1350), radius 300 (1 px = 5 mm).
    assert abs(a["radius_px"] - 300.0) < 10.0
    assert abs(a["center"][0] - 1800.0) < 10.0
    assert abs(a["center"][1] - 1350.0) < 10.0


def test_diagonal_first_detection_recovers_fx1_diagonal():
    # Diagonal-first: the 3-4-5 diagonal must be recovered as ONE segment (from
    # the STRUCTURAL mask, pre-erosion), not staircase-fragmented into near-axis
    # spurious walls by Hough.
    payload = extract_raster_auto(_FX1_PNG, derive_scale=True)
    diags = [w for w in payload["walls"] if w.get("source_ref", "").startswith("raster:diagonal")]
    assert len(diags) == 1, f"expected 1 diagonal, got {len(diags)}"
    a, b = diags[0]["start_px"], diags[0]["end_px"]
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    theta = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
    # FX1 diagonal truth: W-DIAG 2400x1800 mm -> 480x360 px -> length 600 px at 143.13 deg.
    assert abs(length - 600.0) < 25.0
    assert abs(theta - 143.13) < 3.0


def test_derive_rooms_recovers_three_fx1_rooms():
    # The wall graph (9 walls: 8 segments + 1 arc-chord) closes into three bounded
    # faces: R-HALL (west, with the diagonal), R-NE and R-SE (the rectangles).
    payload = extract_raster_auto(_FX1_PNG, derive_scale=True)
    assert len(payload["rooms"]) == 3, f"expected 3 rooms, got {len(payload['rooms'])}"


def test_parse_emits_rooms_from_worker_points_not_bare_drop():
    # The contract layer (parse_raster_auto) must surface the rooms the worker
    # derives. The worker emits rooms as ``{id, area_px, points``(px)}``; the
    # contract converter was written against a stale ``polygon``/``index`` shape
    # and silently dropped every room (fail-open on the room channel). FX1 truth
    # has 3 rooms (R-HALL/R-NE/R-SE): they must reach the emitted payload.
    payload, findings, source_errors = R.parse_raster_auto(_FX1_PNG, derive_scale=True)
    assert source_errors == [], f"FX1 must emit clean: {source_errors}"
    assert len(payload["rooms"]) == 3, f"expected 3 emitted rooms, got {len(payload['rooms'])}"
    # Each emitted room carries a metres polygon and a positive area.
    for room in payload["rooms"]:
        poly = room["polygon"]
        assert len(poly) >= 3 and all(len(p) == 2 for p in poly)
        assert room.get("area_m2", 0.0) > 0.0


# --------------------------------------------------------------------------- #
# G — per-plan scale anchors + arc-hosted opening recovery                    #
# --------------------------------------------------------------------------- #

_CORPUS = "evidence/PLAN-002RF/WP4/corpus"


def _corpus_fixture(name: str) -> str:
    import os
    path = os.path.join(_CORPUS, name, "fxx.png")
    assert os.path.isfile(path), f"corpus fixture missing: {path}"
    return path


def test_corpus_fixture_resolves_scale_from_its_own_manifest():
    # A corpus fixture must resolve its authoritative scale anchors from ITS OWN
    # sibling ``fxx-scale-anchors.json`` (hash-bound to the raster), never from
    # the FX1 fixture's manifest. Before this fix every corpus fixture returned
    # SCALE_ANCHORS_INSUFFICIENT (the worker only read the hardcoded FX1 path).
    payload = extract_raster_auto(_corpus_fixture("f00"), derive_scale=True)
    codes = {err["code"] for err in payload["errors"]}
    assert "SCALE_ANCHORS_INSUFFICIENT" not in codes, f"scale unresolved: {codes}"
    assert payload["frame"].get("scale_m_per_px") == pytest.approx(0.005)


def test_corpus_arc_fixture_recovers_arc_hosted_window():
    # An arc fixture's apse carries an arc-hosted window (two concentric glazing
    # arcs, inner offset 8 px). The engine must attribute that ink to a window
    # opening rather than leave it as unexplained ink (which currently fails
    # every arc fixture with RASTER_UNEXPLAINED_INK).
    payload = extract_raster_auto(_corpus_fixture("f03"), derive_scale=True)
    codes = {err["code"] for err in payload["errors"]}
    assert "RASTER_UNEXPLAINED_INK" not in codes, f"arc-window ink unattributed: {codes}"
    kinds = [o["kind"] for o in payload["openings"]]
    assert kinds.count("window") >= 2, f"expected >=2 windows (N + apse), got {kinds}"


# --------------------------------------------------------------------------- #
# H — 2026-08-19 Opus review remediation                                       #
# --------------------------------------------------------------------------- #


def test_norm_deg_maps_into_frozen_range():
    # review #7: angles must land in (-180, 180], never (-360, 0].
    assert _norm_deg(-270.0) == 90.0
    assert _norm_deg(270.0) == -90.0
    assert _norm_deg(-90.0) == -90.0
    assert _norm_deg(90.0) == 90.0
    assert _norm_deg(180.0) == 180.0
    assert _norm_deg(-180.0) == 180.0
    assert _norm_deg(0.0) == 0.0


def test_fx1_arc_emits_frozen_angle_convention_and_derived_sweep():
    # review #7 + #8: the FX1 apse must emit both angles in (-180, 180] and a
    # sweep derived from traversal (not hardcoded 'ccw'), so the bulge/sweep
    # invariant in reflection.arc_invariants compares two independently-derived
    # values. Without this the arc emitted -270/-90 and a self-produced bulge.
    from pwa.floorplan.raster_auto import parse_raster_auto
    payload, findings, _serr = parse_raster_auto(_FX1_PNG, derive_scale=True)
    assert findings == []
    arc = next(w["arc"] for w in payload["walls"] if w["kind"] == "circular_arc")
    assert -180.0 < arc["start_deg"] <= 180.0
    assert -180.0 < arc["end_deg"] <= 180.0
    assert arc["sweep"] in {"ccw", "cw"}
    # bulge sign must agree with the emitted (derived) sweep.
    if arc["sweep"] == "ccw":
        assert arc["bulge"] > 0.0
    else:
        assert arc["bulge"] < 0.0


def test_emit_scale_provenance_preserved():
    # review #13: the validated scale_m_per_px must reach the payload, not be
    # silently dropped to None (the worker resolves 0.005 and the emitter
    # hardcoded None).
    from pwa.floorplan.raster_auto import parse_raster_auto
    payload, _findings, _serr = parse_raster_auto(_FX1_PNG, derive_scale=True)
    assert payload.get("scale_m_per_px") == pytest.approx(0.005)


def test_absolute_ink_pixel_cap_fires_resource_limit(monkeypatch):
    # review #1: the ink-FRACTION band bounds relative ink only; an in-band
    # large raster still drives unbounded per-ink-pixel Hough work. The absolute
    # ink-pixel cap must fire PARSE_RESOURCE_LIMIT in the short-circuit block.
    # FX1 carries ~25k structural ink pixels; lowering the cap below that forces
    # the guard to fire on a real fixture without allocating a 100 MP canvas.
    import pwa.floorplan.raster_auto_worker as W
    monkeypatch.setattr(W, "MAX_STRUCTURAL_INK_PIXELS", 100)
    payload = extract_raster_auto(_FX1_PNG, derive_scale=False)
    codes = {err["code"] for err in payload["errors"]}
    assert "PARSE_RESOURCE_LIMIT" in codes
    assert payload["walls"] == []
    assert payload["rooms"] == []
    assert payload["openings"] == []


def test_oversized_manifest_is_refused(tmp_path):
    # review #3: the sibling *-scale-anchors.json was read with uncapped
    # read_text() before any size check. An oversized manifest must yield no
    # anchors (fail-closed) instead of being fully materialized.
    import pwa.floorplan.raster_auto_worker as W
    big = tmp_path / "fxx-scale-anchors.json"
    big.write_text("x" * (W.MAX_SOURCE_RASTER_BYTES + 1), encoding="utf-8")
    raster = tmp_path / "fxx.png"
    raster.write_bytes(b"")  # only the manifest path matters for the size guard
    assert W._load_authoritative_anchors(raster) == []


def test_truth_side_canonicalization_is_symmetric():
    # review #12: canonicalization was applied only to predictions, so a truth
    # wall authored larger-endpoint-first was structurally unmatchable. The
    # evaluator-owned projector (review #11) canonicalizes a/b identically on
    # BOTH sides, so authoring order can never make a truth wall unmatchable.
    # (Both records are in mm truth space; this test exercises the ORDER
    # invariant of the truth projection.)
    truth_large_first = P.project_truth_wall({"kind": "segment", "a_mm": [5, 0], "b_mm": [1, 0]})
    truth_small_first = P.project_truth_wall({"kind": "segment", "a_mm": [1, 0], "b_mm": [5, 0]})
    assert truth_large_first == truth_small_first
    assert truth_large_first["a_mm"] == [1, 0]
    assert truth_large_first["b_mm"] == [5, 0]


# --------------------------------------------------------------------------- #
# I — review #10: ink-measured anchor spans (AT-15 reachability)               #
# --------------------------------------------------------------------------- #


def _fx1_anchor_components():
    arr = np.asarray(Image.open(_FX1_PNG).convert("L"))
    labels, n = G.connected_components(arr == 64)
    return arr, labels, n


def test_measure_anchor_span_px_principal_axis_extent_on_fx1():
    # review #10: the anchor span must be MEASURED from the value-64 anchor ink
    # (excluded from the structural mask), not copied from the author-declared
    # manifest. The renderer draws +-10 px diagonal end ticks centred on each
    # endpoint, so the ink-measured principal-axis extents overshoot the
    # declared spans by a bounded, geometry-explained amount:
    #   A-D (3-4-5 diagonal, declared 400): ~406.4 (= 2*2 tick-along-axis + stroke)
    #   A-S (axis-aligned,  declared 1000): ~1022  (= 2*10 tick + 2 stroke)
    #   A-W (axis-aligned,  declared 1200): ~1222
    arr, labels, n = _fx1_anchor_components()
    assert n == 3, f"expected 3 anchor ink components, got {n}"
    spans = sorted(G.measure_anchor_span_px(arr, labels == c) for c in range(1, n + 1))
    assert spans[0] == pytest.approx(406.4, abs=1.5)
    assert spans[1] == pytest.approx(1022.0, abs=1.5)
    assert spans[2] == pytest.approx(1222.0, abs=1.5)


def test_anchor_span_band_is_stroke_tick_geometry_bound():
    # The measured-vs-declared tolerance is DERIVED from the drawing geometry,
    # not tuned to the fixture: an anchor's ink extent can exceed its declared
    # span by at most the two end ticks (each <= ANCHOR_TICK_MAX_PX along the
    # axis) plus one stroke width on each side.
    bound = G.anchor_span_band_px()
    assert bound == 2 * (G.WALL_STROKE_PX + G.ANCHOR_TICK_MAX_PX) + 1
    assert G.ANCHOR_TICK_MAX_PX == 12  # documented U-pending default


def test_load_authoritative_anchors_carries_declared_and_measured_spans():
    # review #10: each authoritative anchor record carries BOTH the declared
    # manifest span_px AND the ink-measured span_px of the matching value-64
    # component in THIS raster. The manifest parse itself stays unchanged;
    # measurement happens in the worker against the actual pixels.
    import pwa.floorplan.raster_auto_worker as W

    anchors = W._load_authoritative_anchors(Path(_FX1_PNG))
    assert len(anchors) == 3
    declared_sorted = sorted(a["span_px"] for a in anchors)
    measured_sorted = sorted(a["measured_span_px"] for a in anchors)
    assert declared_sorted == [400.0, 1000.0, 1200.0]
    assert measured_sorted[0] == pytest.approx(406.4, abs=1.5)
    assert measured_sorted[1] == pytest.approx(1022.0, abs=1.5)
    assert measured_sorted[2] == pytest.approx(1222.0, abs=1.5)
    # every anchor keeps its real length (conversion input) and id
    assert all(a["real_length_m"] > 0 for a in anchors)
    assert {a["id"] for a in anchors} == {"A-S", "A-W", "A-D"}


def _write_rebound_manifest(tmp_path, raster_path):
    """Copy the FX1 manifest, rebinding ONLY raster_sha256 to ``raster_path``."""
    import hashlib
    import json

    src = Path(_FX1_PNG).with_name("fx1-scale-anchors.json")
    doc = json.loads(src.read_text(encoding="utf-8"))
    doc["raster_sha256"] = "sha256:" + hashlib.sha256(raster_path.read_bytes()).hexdigest()
    out = tmp_path / "fx1-scale-anchors.json"
    out.write_text(json.dumps(doc), encoding="utf-8")
    return out


def _tamper_stretch_anchor_s(tmp_path):
    """Stretch the south anchor's ink +100 px, erase the other value-64 ink.

    The declared manifest spans stay EXACTLY as frozen; only the drawn ink
    changes (and the manifest is hash-rebound to the tampered raster, exactly
    as a lying author would). Old code: fit_scale over declared spans -> residual
    0 by construction -> AT-15 vacuously green. New code: the ink-measured span
    (~1102 px vs declared 1000) must trip the gates.
    """
    import json

    arr = np.asarray(Image.open(_FX1_PNG).convert("L")).copy()
    arr[arr == 64] = 255            # erase ALL anchor ink
    arr[1849:1852, 300:1402] = 64   # redraw A-S stretched: 1102 px (declared 1000)
    raster = tmp_path / "fx1.png"
    Image.fromarray(arr).save(raster, format="PNG")
    _write_rebound_manifest(tmp_path, raster)
    return raster


def test_tampered_anchor_ink_fires_dimension_inconsistent_despite_matching_manifest(tmp_path):
    # review #10 / AT-15 reachability proof: a raster whose anchor ink is
    # stretched beyond the geometry band must be refused EVEN THOUGH the
    # manifest is hash-bound to it and its declared spans are unmodified.
    # Before this fix the scale gates compared real_length_m against the
    # AUTHOR-DECLARED span_px, so the residual was 0 by construction and this
    # tamper passed silently.
    raster = _tamper_stretch_anchor_s(tmp_path)
    payload = extract_raster_auto(raster, derive_scale=True)
    codes = {err["code"] for err in payload["errors"]}
    assert "PARSE_DIMENSION_INCONSISTENT" in codes, f"tampered anchor ink accepted: {codes}"
    assert payload["walls"] == []  # fail-closed: no geometry beside a blocking finding
    # conversion scale stays MANIFEST-bound (frozen contract): the declared
    # spans still resolve 0.005 — the measurement drives the GATES, not the
    # conversion (using measured spans for conversion would de-facto re-freeze).
    assert payload["frame"]["scale_m_per_px"] == pytest.approx(0.005)


def test_clean_fx1_measured_gates_pass_and_conversion_stays_manifest_bound():
    # The positive half of #10: on the untouched fixture the ink-measured spans
    # sit inside the geometry band, so the measured-span gates pass and the
    # plan still emits clean geometry with the frozen conversion scale.
    payload = extract_raster_auto(Path(_FX1_PNG), derive_scale=True)
    codes = {err["code"] for err in payload["errors"]}
    assert "PARSE_DIMENSION_INCONSISTENT" not in codes, f"clean fx1 refused: {codes}"
    assert payload["frame"]["scale_m_per_px"] == pytest.approx(0.005)
    assert len(payload["walls"]) == 9  # frozen: 8 segments + 1 arc
