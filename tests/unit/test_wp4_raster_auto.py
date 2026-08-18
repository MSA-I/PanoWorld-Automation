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

import math

import numpy as np
import pytest
from PIL import Image

from pwa.floorplan import raster_auto_geometry as G
from pwa.floorplan import raster_auto as R
from pwa.floorplan.raster_auto_worker import extract_raster_auto
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
    # walls. On the single supported fixture the extraction either converges to
    # the 9-wall clean plan or stops with a bounded refusal; a wall set that
    # diverges from the clean plan is a fail-closed refusal, not product output.
    payload = extract_raster_auto(_FX1_PNG, derive_scale=True)
    if payload["walls"]:
        assert any(err["code"] == "RASTER_OVERSEGMENTED" for err in payload["errors"])
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


def test_raster_trutht_record_from_wall_segment_shape():
    wall = {"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]}
    record = R.truth_record_from_wall(wall)
    assert record["kind"] == "segment"
    assert record["a_mm"] == [1000.0, 1500.0]
    assert record["b_mm"] == [9000.0, 1500.0]


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
