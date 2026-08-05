"""Golden tests (PLAN-000 T9, AC2): the validator must pass on BOTH fixture
layers — synthetic Layer A (with config checks) and the real vendored subset of
PanoWorld scene0000, Layer B (scene-only mode) — proving it is neither overfit
to synthetic data nor broken on real upstream data.
"""
from __future__ import annotations

import json

from pwa.fixtures import STYLE_PANO_NAME
from pwa.validator import PackageValidator

from tests.conftest import GOLDEN_SUBSET, REPO_ROOT

EXPECTED_REPORT = REPO_ROOT / "tests" / "golden" / "expected_report_demo_subset.json"


# --- Layer A: synthetic tiny scene, full config mode -------------------------

def test_layer_a_green_with_config(tiny_scene):
    report = PackageValidator(
        tiny_scene,
        start_image=STYLE_PANO_NAME,
        pano_image_name="panoImage_2048.png",
        max_views=8,
    ).validate()
    assert report.errors == []
    assert report.warnings == []
    assert report.ok()
    assert report.summary["viewpoints_mapped"] == 2


def test_layer_a_missing_start_image(tiny_scene):
    report = PackageValidator(tiny_scene, start_image="panoImage_2048_missing.png").validate()
    assert "START_IMAGE_MISSING" in {f["code"] for f in report.errors}


def test_layer_a_pano_name_collision(tiny_scene):
    report = PackageValidator(
        tiny_scene, start_image=STYLE_PANO_NAME, pano_image_name="place_image.png"
    ).validate()
    assert "PANO_NAME_COLLISION" in {f["code"] for f in report.errors}


def test_layer_a_viewpoint_budget_exceeded(tiny_scene):
    report = PackageValidator(tiny_scene, start_image=STYLE_PANO_NAME, max_views=1).validate()
    assert "VIEWPOINT_BUDGET_EXCEEDED" in {f["code"] for f in report.errors}


# --- Layer B: real vendored subset of scene0000, scene-only mode -------------

def test_layer_b_fixture_present():
    assert GOLDEN_SUBSET.is_dir(), (
        "Golden fixture missing - run: uv run python tools/fetch_golden_fixture.py"
    )
    meta = json.loads((GOLDEN_SUBSET / "fixture-metadata.json").read_text(encoding="utf-8"))
    assert meta["commit_sha"], "fixture must be pinned to an exact upstream commit"


def test_layer_b_demo_subset_validates_green():
    report = PackageValidator(GOLDEN_SUBSET).validate()
    assert report.errors == [], f"real demo subset must validate clean: {report.errors}"
    assert report.ok()
    # Structural expectations, explicit (not just "no exception"):
    assert report.summary["maps"] == 1
    assert report.summary["viewpoints_mapped"] == 4
    for vp in ("0000", "0001", "0008", "0011"):
        d = GOLDEN_SUBSET / "viewpoints" / vp
        for name in ("extrinsics.txt", "place_image.png", "place_depth.png", "place_depth_scale.txt"):
            assert (d / name).is_file(), f"{vp}/{name}"


def test_layer_b_report_snapshot():
    """Golden-master on the validator's own report shape (paths scene-relative,
    so the snapshot is machine-independent)."""
    report_dict = PackageValidator(GOLDEN_SUBSET).validate().to_dict()
    expected = json.loads(EXPECTED_REPORT.read_text(encoding="utf-8"))
    assert report_dict == expected
