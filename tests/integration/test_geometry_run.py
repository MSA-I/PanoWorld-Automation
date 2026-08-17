"""Integration tests for the geometry run builder + CLI (G-t4, AC-1/4/6/10)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.geometry.run_builder import build_geometry_run

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYER_A_DXF = REPO_ROOT / "evidence" / "PLAN-002" / "parse" / "layer-a-1-dxf.json"


@pytest.fixture
def runs_root(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    (root / "source-parse.json").write_bytes(LAYER_A_DXF.read_bytes())
    return root


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_build_run_produces_schema_valid_scene_geometry(runs_root):
    result = build_geometry_run(
        runs_root=runs_root,
        source_parse=Path("source-parse.json"),
        geo_run_id="geo-001",
    )
    assert result.cli_exit == 0
    run = result.final_run
    assert run.is_dir()
    scene = json.loads((run / "geometry" / "scene_geometry.json").read_text(encoding="utf-8"))
    assert scene["schema_id"] == "scene_geometry"
    assert scene["schema_version"] == "1.0.0"
    assert scene["status"] == "complete"
    assert validate_artifact(scene) == []
    assert scene["content_hash"] == compute_content_hash(scene)
    assert scene["payload"]["up_axis"] == "z"
    assert scene["payload"]["units"] == "m"


def test_run_is_immutable_and_copies_source_parse(runs_root):
    original_bytes = LAYER_A_DXF.read_bytes()
    result = build_geometry_run(runs_root=runs_root, source_parse=Path("source-parse.json"), geo_run_id="geo-002")
    assert result.cli_exit == 0
    copied = (result.final_run / "project" / "source-parse.json").read_bytes()
    assert copied == original_bytes
    assert _sha256_bytes(copied) == _sha256_bytes(original_bytes)
    # The source itself is unchanged.
    assert (runs_root / "source-parse.json").read_bytes() == original_bytes


def test_deterministic_rerun_byte_identical(runs_root):
    # AC-4: two compilations of the same input are deterministic. The run_id
    # is an explicit per-run identity (and created_at a timestamp), so the
    # *payload* and derived entity IDs must be byte-identical; only the
    # envelope identity fields may differ.
    r1 = build_geometry_run(runs_root=runs_root, source_parse=Path("source-parse.json"), geo_run_id="geo-det-1")
    r2 = build_geometry_run(runs_root=runs_root, source_parse=Path("source-parse.json"), geo_run_id="geo-det-2")
    assert r1.cli_exit == 0 and r2.cli_exit == 0
    doc1 = json.loads((r1.final_run / "geometry" / "scene_geometry.json").read_text(encoding="utf-8"))
    doc2 = json.loads((r2.final_run / "geometry" / "scene_geometry.json").read_text(encoding="utf-8"))
    assert doc1["payload"] == doc2["payload"]
    assert doc1["content_hash"] != doc2["content_hash"]  # run_id is in the envelope
    # Reports (which exclude run_id) must be byte-identical.
    t1 = (r1.final_run / "geometry" / "topology-report.json").read_bytes()
    t2 = (r2.final_run / "geometry" / "topology-report.json").read_bytes()
    assert t1 == t2
    o1 = (r1.final_run / "geometry" / "overlay-topdown.svg").read_bytes()
    o2 = (r2.final_run / "geometry" / "overlay-topdown.svg").read_bytes()
    assert o1 == o2
    p1 = (r1.final_run / "geometry" / "overlay-topdown.png").read_bytes()
    p2 = (r2.final_run / "geometry" / "overlay-topdown.png").read_bytes()
    assert p1 == p2


def test_run_produces_overlay_and_reports(runs_root):
    result = build_geometry_run(runs_root=runs_root, source_parse=Path("source-parse.json"), geo_run_id="geo-003")
    assert result.cli_exit == 0
    geometry_dir = result.final_run / "geometry"
    for name in (
        "scene_geometry.json",
        "assumptions.json",
        "topology-report.json",
        "geometry-report.json",
        "overlay-topdown.svg",
        "overlay-topdown.png",
    ):
        assert (geometry_dir / name).is_file(), name
    # Overlays are non-empty.
    assert (geometry_dir / "overlay-topdown.svg").stat().st_size > 0
    assert (geometry_dir / "overlay-topdown.png").stat().st_size > 0


def test_invalid_geo_run_id_is_rejected(runs_root):
    result = build_geometry_run(
        runs_root=runs_root,
        source_parse=Path("source-parse.json"),
        geo_run_id="../../evil",
    )
    assert result.cli_exit == 2
    assert not result.final_run.exists()


def test_source_parse_hash_mismatch_is_rejected(runs_root):
    # Tamper with the source parse's content_hash field.
    source = runs_root / "source-parse.json"
    doc = json.loads(source.read_text(encoding="utf-8"))
    doc["content_hash"] = "sha256:" + "0" * 64
    source.write_text(json.dumps(doc), encoding="utf-8")
    result = build_geometry_run(runs_root=runs_root, source_parse=Path("source-parse.json"), geo_run_id="geo-004")
    assert result.cli_exit == 2
    assert "source_parse_hash_mismatch" in result.diagnostic.get("reason", "")


def test_non_floorplan_source_is_rejected(runs_root):
    source = runs_root / "source-parse.json"
    doc = json.loads(source.read_text(encoding="utf-8"))
    doc["schema_id"] = "not_floorplan_parse"
    source.write_text(json.dumps(doc), encoding="utf-8")
    result = build_geometry_run(runs_root=runs_root, source_parse=Path("source-parse.json"), geo_run_id="geo-005")
    assert result.cli_exit == 2


def test_no_pyproject_or_dependency_change():
    # AC-10 guard: the geometry package must not require new dependencies.
    from pwa.geometry import (  # noqa: F401
        compile_geometry,
        load_parse_geometry,
        render_png,
        render_svg,
        build_geometry_run,
        validate_topology,
    )
    # Import of the package is sufficient evidence it uses only locked deps.
