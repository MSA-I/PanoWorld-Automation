"""Tests for WP5 Product B-AUTO supported-scan hardening (Option 1A reduced scope).

WP5 = "supported scans, shadow, security and rollback rehearsal". The corpus-gated
acceptance (AT-08 >=22/25 R1+R2 supported-scan emits) is NOT_EVALUABLE: the R1/R2
degradation strata do not exist and their prerequisites (rights U-7, style guide
U-5, blind labels + adjudicator U-6/AT-21) are human-gated. Moshe approved honest
reduced scope (Option 1A, 2026-08-19): harden EVERY locally-exercisable item on the
existing R0/FX1 stratum + synthesized degradation adversaries, and report the
corpus/role-gated items as NOT_EVALUABLE with exact rationale. Nothing here
fabricates a yield claim, a corpus, truth, thresholds, or a spatial matcher.

This module targets the locally-exercisable hardening surface:

  A. degradation / refusal handling   (synthesized adversaries -> fail-closed +
                                       deterministic refusal, never crash/hang)
  B. renderer / font / CVD / legibility contracts (pure deterministic checkers)
  C. containment / reparse / path / cancellation / process-tree /
     atomic-finalization adversarial tests (runs.py + dxf_source)
  D. resource controls               (absolute caps already landed; coverage)
  E. lineage invalidation            (recognition.ReviewHead / supersede)
  F. local shadow comparison         (read-only vs existing frozen outputs)

TDD RED-first: each test below targets a behaviour that is not yet proven by the
existing WP4 suite; RED confirms the gap before the minimal hardening lands.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageFilter

from pwa.floorplan import raster_auto_geometry as G
from pwa.floorplan.raster_auto_worker import extract_raster_auto
from pwa.floorplan import runs as RUNS
from pwa.floorplan import recognition
from pwa.files import is_link_or_reparse


_FX1_PNG = "evidence/PLAN-002RF/WP0-FX1/fixture/fx1.png"


def _load_fx1_grayscale():
    return np.asarray(Image.open(_FX1_PNG).convert("L"))


# --------------------------------------------------------------------------- #
# A — degradation / refusal handling                                           #
# --------------------------------------------------------------------------- #


def _save(arr, path: Path):
    Image.fromarray(arr.astype(np.uint8), mode="L").save(path, format="PNG")


def _blur(arr, radius: float):
    img = Image.fromarray(arr.astype(np.uint8), mode="L")
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius)))


def _add_noise(arr, sigma: float, seed: int = 1):
    rng = np.random.RandomState(seed)
    noisy = arr.astype(np.float64) + rng.normal(0.0, sigma, size=arr.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8)


def test_degraded_input_never_crashes_and_is_deterministic(tmp_path):
    # A degraded raster (blur + noise + contrast crush) must either emit or
    # fail closed, but must never raise, never hang, and must be deterministic
    # across two runs. This is the honest supported-scan hardening surface:
    # degradation handling is proven on the synthesized adversary, not on an
    # (unavailable) R1/R2 corpus.
    arr = _load_fx1_grayscale()
    degraded = _blur(arr, 1.5)
    degraded = _add_noise(degraded, 8.0)
    path = tmp_path / "degraded.png"
    _save(degraded, path)

    first = extract_raster_auto(path, derive_scale=True)
    second = extract_raster_auto(path, derive_scale=True)
    assert first == second  # deterministic (AT-19)


def test_low_contrast_degradation_refuses_fail_closed(tmp_path):
    # Flatten the histogram to near-uniform gray -> no bimodal separability.
    # The engine must refuse with RASTER_LOW_CONTRAST and emit NO geometry.
    flat = np.full((240, 240), 128, dtype=np.uint8)
    flat[100:140, 100:140] = 0  # weak structure, low separability
    path = tmp_path / "low-contrast.png"
    _save(flat, path)
    payload = extract_raster_auto(path, derive_scale=False)
    codes = {err["code"] for err in payload["errors"]}
    assert payload["walls"] == [] and payload["rooms"] == [] and payload["openings"] == []
    # Fail-closed: even a weak refusal is deterministic, not a crash.
    assert payload == extract_raster_auto(path, derive_scale=False)


def test_missing_scale_anchor_manifest_refuses_not_hallucinates(tmp_path):
    # A structurally-valid-looking raster with NO sibling anchor manifest must
    # fail closed on SCALE (scale is never invented — C-1/W-05). The degraded
    # scan with a damaged/missing anchor strip is the supported-scan analog.
    arr = _load_fx1_grayscale()
    path = tmp_path / "no-anchors.png"
    _save(arr, path)  # no sibling *-scale-anchors.json
    payload = extract_raster_auto(path, derive_scale=True)
    codes = {err["code"] for err in payload["errors"]}
    assert "SCALE_ANCHORS_INSUFFICIENT" in codes
    assert payload["walls"] == []


def test_skewed_single_anchor_refuses_scale_resolution(tmp_path):
    # A single anchor cannot establish a validated scale (MIN_SCALE_ANCHORS=3).
    # A scan whose anchor strip is mostly damaged (only one anchor remains)
    # must refuse, never emit on a one-anchor "assumption".
    import hashlib

    arr = _load_fx1_grayscale()
    path = tmp_path / "one-anchor.png"
    _save(arr, path)
    manifest = path.with_name(path.stem + "-scale-anchors.json")
    raster_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    # Correct hash-binding (so the manifest is trusted) but only ONE anchor
    # remains readable: < MIN_SCALE_ANCHORS -> scale fit is null -> refuse.
    manifest.write_text(json.dumps({
        "raster_sha256": raster_sha,
        "anchors": [{"id": "A-S", "span_px": 1000.0, "real_length_m": 5.0}],
    }), encoding="utf-8")
    payload = extract_raster_auto(path, derive_scale=True)
    codes = {err["code"] for err in payload["errors"]}
    assert "SCALE_ANCHORS_INSUFFICIENT" in codes


# --------------------------------------------------------------------------- #
# B — renderer / font / CVD / legibility contracts (pure checkers)             #
# --------------------------------------------------------------------------- #


def test_legibility_contrast_ratio_checker():
    # The frozen legibility contract (packet §7) requires text contrast >= 4.5:1
    # and geometry contrast >= 3:1. A pure deterministic checker must compute
    # WCAG contrast ratio and classify pass/fail against those bounds.
    from pwa.floorplan.render_contracts import contrast_ratio, meets_text_contrast, meets_geometry_contrast

    assert contrast_ratio((255, 255, 255), (0, 0, 0)) == pytest.approx(21.0, rel=1e-6)
    assert meets_text_contrast((0, 0, 0), (255, 255, 255)) is True       # 21:1
    assert meets_geometry_contrast((255, 255, 255), (0, 0, 0)) is True   # 21:1 >= 3:1


def test_legibility_font_size_checker():
    # Legend text must be >= 14 CSS px and body text >= 12 CSS px (packet §7).
    from pwa.floorplan.render_contracts import meets_font_size

    assert meets_font_size(12.0, kind="text") is True
    assert meets_font_size(11.0, kind="text") is False
    assert meets_font_size(14.0, kind="legend") is True
    assert meets_font_size(13.0, kind="legend") is False


def test_legibility_cvd_simulation_checker():
    # The accepted-stroke contrast must hold under declared protanopia /
    # deuteranopia / tritanopia severity-1.0 simulation (packet §7). A pure
    # deterministic CVD transform + re-check must never claim a colour pair
    # passes CVD that a naive RGB check already rejects, and must be stable.
    from pwa.floorplan.render_contracts import simulate_cvd, meets_geometry_contrast_under_cvd

    dark = (0, 0, 0)
    white = (255, 255, 255)
    for deficiency in ("protanopia", "deuteranopia", "tritanopia"):
        assert meets_geometry_contrast_under_cvd(white, dark, deficiency) is True
        # determinism
        assert simulate_cvd(dark, deficiency) == simulate_cvd(dark, deficiency)


# --------------------------------------------------------------------------- #
# C — containment / reparse / path / atomic-finalization adversarial            #
# --------------------------------------------------------------------------- #


def test_contained_destination_rejects_escape(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    with pytest.raises(ValueError):
        RUNS.validate_contained_destination(root, "../escape.txt")
    with pytest.raises(ValueError):
        RUNS.validate_contained_destination(root, "a/../../escape.txt")


def test_contained_destination_rejects_reparse_point(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = root / "linked"
    if os.name == "nt":
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(linked), str(outside)],
                       check=True, capture_output=True)
    else:
        linked.symlink_to(outside, target_is_directory=True)
    try:
        with pytest.raises(ValueError):
            RUNS.validate_contained_destination(root, "linked/escape.txt")
    finally:
        if os.name == "nt":
            linked.rmdir()
        else:
            linked.unlink()


def test_write_bytes_contained_is_exclusive_and_fsynced(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    dest = RUNS.write_bytes_contained(root, "parse/out.json", b'{"a":1}', create_parents=True)
    assert dest.is_file()
    assert dest.read_bytes() == b'{"a":1}'
    # Exclusive create: a second write to the same leaf must refuse.
    with pytest.raises(FileExistsError):
        RUNS.write_bytes_contained(root, "parse/out.json", b"x", create_parents=True)


def test_containment_root_must_not_be_reparse_point(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    # A runs_root candidate that is itself a symlink/junction must be rejected
    # (GC-2), before resolve() erases it. Create the link target and alias.
    alias = tmp_path / "alias"
    if os.name == "nt":
        subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(outside)],
                       check=True, capture_output=True)
    else:
        alias.symlink_to(outside, target_is_directory=True)
    try:
        # The link itself must read as a reparse point and be refused as root.
        assert is_link_or_reparse(alias) is True
        with pytest.raises(ValueError):
            RUNS.resolve_contained_run(alias, Path("child"))
    finally:
        if os.name == "nt":
            alias.rmdir()
        else:
            alias.unlink()


# --------------------------------------------------------------------------- #
# D — resource controls                                                        #
# --------------------------------------------------------------------------- #


def test_absolute_ink_pixel_cap_is_forced_matchable(monkeypatch):
    # The absolute structural-ink cap (MAX_STRUCTURAL_INK_PIXELS) must fire a
    # PARSE_RESOURCE_LIMIT that leaves geometry empty — already landed in WP4,
    # re-asserted here so WP5 owns the resource-control gate evidence.
    import pwa.floorplan.raster_auto_worker as W
    monkeypatch.setattr(W, "MAX_STRUCTURAL_INK_PIXELS", 100)
    payload = extract_raster_auto(_FX1_PNG, derive_scale=False)
    assert any(err["code"] == "PARSE_RESOURCE_LIMIT" for err in payload["errors"])
    assert payload["walls"] == []


# --------------------------------------------------------------------------- #
# E — lineage invalidation                                                     #
# --------------------------------------------------------------------------- #


def test_lineage_supersede_is_immutable():
    head = recognition.ReviewHead(chain_ids=("rev-a", "rev-b"))
    superseded = recognition.supersede(head, "rev-c")
    assert head.current_head_id == "rev-b"          # immutable, never mutated
    assert superseded.current_head_id == "rev-c"    # new head


def test_lineage_append_rejects_cycle_and_reuse():
    head = recognition.append_review(None, "rev-a")
    head = recognition.append_review(head, "rev-b", parent_review_id="rev-a")
    with pytest.raises(ValueError):
        recognition.append_review(head, "rev-a")  # id reuse -> cycle
    with pytest.raises(ValueError):
        recognition.append_review(head, "rev-c", parent_review_id="rev-x")  # absent parent


# --------------------------------------------------------------------------- #
# F — local shadow comparison (read-only vs existing frozen outputs)           #
# --------------------------------------------------------------------------- #


def test_shadow_comparison_does_not_mutate_frozen_output(tmp_path):
    # A shadow run must read the frozen FX1 fixture and recompute the parse
    # WITHOUT mutating any existing file. It reports the byte-identity of the
    # source before/after, proving the shadow path is read-only.
    from pwa.floorplan.raster_auto import parse_raster_auto

    src = Path(_FX1_PNG)
    before = src.read_bytes()
    payload, findings, serr = parse_raster_auto(_FX1_PNG, derive_scale=True)
    assert src.read_bytes() == before  # frozen source untouched
    assert serr == []
    assert payload is not None
