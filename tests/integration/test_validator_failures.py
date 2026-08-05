"""The 15 failure-injection cases (PLAN-000 T9, AC3) — each mutates one copy of
the Layer-A tiny scene and asserts the specific machine-readable code from
contracts/error_codes.md. Written TDD-first against the stub validator.

Case numbering follows test-architect §3 as amended by plan-reviewer:
case 7 asserts a WARNING (scene0000 legitimately has unmapped spares),
case 12 is redefined for Windows/NTFS (reserved names / trailing dot-space),
case 15 is intra-map duplicate keys only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image

from pwa.validator import PackageValidator, check_filename


def run(scene: Path):
    return PackageValidator(scene).validate()


def error_codes(report) -> set[str]:
    return {f["code"] for f in report.errors}


def warning_codes(report) -> set[str]:
    return {f["code"] for f in report.warnings}


def test_case_01_missing_extrinsics(tiny_scene):
    (tiny_scene / "viewpoints" / "0001" / "extrinsics.txt").unlink()
    assert "MISSING_REQUIRED_FILE" in error_codes(run(tiny_scene))


def test_case_02_matrix_3x4(tiny_scene):
    p = tiny_scene / "viewpoints" / "0000" / "extrinsics.txt"
    lines = p.read_text(encoding="ascii").strip().splitlines()
    p.write_text("\n".join(lines[:3]) + "\n", encoding="ascii")
    assert "INVALID_MATRIX_SHAPE" in error_codes(run(tiny_scene))


def test_case_03_singular_matrix(tiny_scene):
    p = tiny_scene / "viewpoints" / "0000" / "extrinsics.txt"
    p.write_text(
        "0 0 0 0.5\n0 0 0 -1.0\n0 0 0 1.35\n0 0 0 1\n", encoding="ascii"
    )
    assert "MATRIX_NOT_INVERTIBLE" in error_codes(run(tiny_scene))


def test_case_04_unparseable_matrix(tiny_scene):
    p = tiny_scene / "viewpoints" / "0000" / "extrinsics.txt"
    p.write_text("this is ; not, a matrix\n1 2\n", encoding="ascii")
    assert "MATRIX_PARSE_ERROR" in error_codes(run(tiny_scene))


def test_case_05_depth_dimension_mismatch(tiny_scene):
    p = tiny_scene / "viewpoints" / "0000" / "place_depth.png"
    depth = Image.new("I;16", (16, 16))
    depth.putdata([1500] * (16 * 16))
    depth.save(p)
    assert "DEPTH_RGB_DIMENSION_MISMATCH" in error_codes(run(tiny_scene))


def test_case_06_map_references_unknown_viewpoint(tiny_scene):
    p = tiny_scene / "map_panoworld0.json"
    p.write_text(json.dumps({"0000": ["0001", "9999"]}), encoding="ascii")
    assert "MAP_REFERENCES_UNKNOWN_VIEWPOINT" in error_codes(run(tiny_scene))


def test_case_07_unmapped_viewpoint_is_warning_not_error(tiny_scene):
    (tiny_scene / "viewpoints" / "0002").mkdir()
    report = run(tiny_scene)
    assert "VIEWPOINT_NOT_IN_MAP" in warning_codes(report)
    assert report.ok(), "unmapped spare viewpoints must not fail validation (upstream has them)"


def test_case_08_wrong_image_mode(tiny_scene):
    p = tiny_scene / "viewpoints" / "0000" / "place_image.png"
    Image.new("RGBA", (32, 16), (200, 200, 200, 255)).save(p)
    assert "INVALID_IMAGE_MODE" in error_codes(run(tiny_scene))


def test_case_09_zero_depth_scale(tiny_scene):
    (tiny_scene / "viewpoints" / "0000" / "place_depth_scale.txt").write_text("0\n", encoding="ascii")
    assert "INVALID_DEPTH_SCALE" in error_codes(run(tiny_scene))


def test_case_10_nan_depth_scale(tiny_scene):
    (tiny_scene / "viewpoints" / "0000" / "place_depth_scale.txt").write_text("NaN\n", encoding="ascii")
    assert "INVALID_DEPTH_SCALE" in error_codes(run(tiny_scene))


def test_case_11_missing_depth_scale(tiny_scene):
    (tiny_scene / "viewpoints" / "0000" / "place_depth_scale.txt").unlink()
    assert "MISSING_REQUIRED_FILE" in error_codes(run(tiny_scene))


def test_case_12_windows_hostile_filename(tiny_scene):
    """NTFS cannot round-trip trailing-dot names or reserved device names via the
    normal API; try to inject one with the \\\\?\\ prefix, else assert the check
    function directly (reviewer missed-risk 1)."""
    target = tiny_scene / "viewpoints" / "0000" / "badname."
    created = False
    try:
        raw = "\\\\?\\" + str(target)
        with open(raw, "w", encoding="ascii") as fh:
            fh.write("x")
        created = True
    except OSError:
        pass
    if created and any(p.name == "badname." for p in (tiny_scene / "viewpoints" / "0000").iterdir()):
        assert "INVALID_FILENAME" in error_codes(run(tiny_scene))
        os.remove(raw)
    else:
        assert check_filename("badname.") is False
        assert check_filename("NUL") is False


def test_case_13_empty_place_image(tiny_scene):
    (tiny_scene / "viewpoints" / "0000" / "place_image.png").write_bytes(b"")
    assert "EMPTY_FILE" in error_codes(run(tiny_scene))


def test_case_14_malformed_map_json(tiny_scene):
    (tiny_scene / "map_panoworld0.json").write_text('{"0000": ["0001",]', encoding="ascii")
    assert "MAP_JSON_INVALID" in error_codes(run(tiny_scene))


def test_case_15_duplicate_key_within_one_map(tiny_scene):
    (tiny_scene / "map_panoworld0.json").write_text(
        '{"0000": ["0001"], "0000": ["0001"]}', encoding="ascii"
    )
    assert "DUPLICATE_MAP_KEY" in error_codes(run(tiny_scene))


def test_same_key_across_different_maps_is_legitimate(tiny_scene):
    """Upstream scene0000 has key 0000 in two different map files — must NOT error."""
    (tiny_scene / "map_panoworld1.json").write_text(json.dumps({"0000": ["0001"]}), encoding="ascii")
    report = run(tiny_scene)
    assert "DUPLICATE_MAP_KEY" not in error_codes(report)
    assert report.ok()
