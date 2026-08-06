"""PLAN-001 packager and CLI acceptance tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from pwa.contracts import validate_artifact
from pwa.packager import build_baseline_run, package_tree_hash
from tests.conftest import REPO_ROOT


def _inputs(root: Path) -> tuple[Path, Path]:
    root.mkdir(parents=True, exist_ok=True)
    floorplan = root / "floor.png"
    style = root / "style.png"
    Image.new("RGB", (32, 16), "white").save(floorplan)
    Image.new("RGB", (32, 16), "tan").save(style)
    return floorplan, style


def _build(tmp_path: Path, layer: str, suffix: str) -> Path:
    floorplan, style = _inputs(tmp_path / suffix)
    run, complete = build_baseline_run(
        runs_root=tmp_path / "runs",
        project_id="demo-project",
        run_id=f"RUN-20260806-13{suffix}00-abcd",
        floorplan=floorplan,
        style_reference=style,
        units="m",
        m_per_px=0.01,
        fixture_layer=layer,
    )
    assert complete
    return run


@pytest.mark.parametrize("layer", ["tiny", "golden"])
def test_fixture_packages_validate_and_manifest_is_schema_valid(tmp_path, layer):
    run = _build(tmp_path, layer, "00" if layer == "tiny" else "01")
    report = json.loads((run / "evidence" / "package-validator.json").read_text(encoding="utf-8"))
    manifest = json.loads((run / "artifacts" / "panoworld_manifest.json").read_text(encoding="utf-8"))
    assert report["errors"] == []
    assert validate_artifact(manifest) == []
    map_doc = json.loads(next((run / "package" / "scene").glob("map*.json")).read_text(encoding="utf-8"))
    assert next(iter(map_doc)) == manifest["payload"]["maps"][0]["entries"][0]["key"]


def test_package_hash_is_stable_detects_mutation_and_run_is_exclusive(tmp_path):
    first = _build(tmp_path, "tiny", "02")
    second = _build(tmp_path, "tiny", "03")
    first_manifest = json.loads((first / "artifacts" / "panoworld_manifest.json").read_text(encoding="utf-8"))
    second_manifest = json.loads((second / "artifacts" / "panoworld_manifest.json").read_text(encoding="utf-8"))
    assert first_manifest["payload"]["package_hash"] == second_manifest["payload"]["package_hash"]
    before, _ = package_tree_hash(first / "package" / "scene")
    target = first / "package" / "scene" / "map_panoworld0.json"
    target.write_bytes(target.read_bytes() + b" ")
    after, _ = package_tree_hash(first / "package" / "scene")
    assert before != after

    floorplan, style = _inputs(tmp_path / "duplicate")
    with pytest.raises(FileExistsError):
        build_baseline_run(
            runs_root=tmp_path / "runs",
            project_id="demo-project",
            run_id="RUN-20260806-130300-abcd",
            floorplan=floorplan,
            style_reference=style,
            units="m",
            m_per_px=0.01,
        )


def test_validator_wrapper_needs_no_pythonpath(tmp_path):
    run = _build(tmp_path, "golden", "04")
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "validate_package.py"), str(run / "package" / "scene")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
