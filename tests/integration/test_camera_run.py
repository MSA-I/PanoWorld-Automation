"""Integration tests for the camera run builder + CLI (AC-1..AC-10)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from pwa.camera.run_builder import build_camera_run
from pwa.contracts import compute_content_hash, validate_artifact

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENE_GEOMETRY = REPO_ROOT / "evidence" / "PLAN-003" / "geometry-run" / "geometry" / "scene_geometry.json"


@pytest.fixture
def runs_root(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    (root / "source-geometry.json").write_bytes(SCENE_GEOMETRY.read_bytes())
    return root


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def test_build_run_produces_schema_valid_camera_plan(runs_root):
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-001")
    assert result.cli_exit == 0
    run = result.final_run
    assert run.is_dir()
    plan = json.loads((run / "camera" / "camera_plan.json").read_text(encoding="utf-8"))
    assert plan["schema_id"] == "camera_plan"
    assert plan["schema_version"] == "1.0.0"
    assert plan["status"] == "complete"
    assert validate_artifact(plan) == []
    assert plan["content_hash"] == compute_content_hash(plan)
    payload = plan["payload"]
    assert payload["resolution"] == {"width": 2048, "height": 1024}
    assert payload["camera_height_m"] == 1.35
    assert len(payload["viewpoints"]) == 2
    assert payload["edges"] == [["0000", "0001"]]
    assert payload["start_viewpoint"] == "0000"
    assert payload["max_views_per_lrm_batch"] == 8


def test_run_is_immutable_and_copies_source_geometry(runs_root):
    original_bytes = SCENE_GEOMETRY.read_bytes()
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-002")
    assert result.cli_exit == 0
    copied = (result.final_run / "project" / "source-geometry.json").read_bytes()
    assert copied == original_bytes
    assert (runs_root / "source-geometry.json").read_bytes() == original_bytes


def test_every_viewpoint_emits_valid_extrinsics(runs_root):
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-003")
    assert result.cli_exit == 0
    plan = json.loads((result.final_run / "camera" / "camera_plan.json").read_text(encoding="utf-8"))
    for vp in plan["payload"]["viewpoints"]:
        vp_dir = result.final_run / "camera" / "extrinsics" / f"{vp['id']}.txt"
        assert vp_dir.is_file(), vp["id"]
        text = vp_dir.read_text(encoding="utf-8").strip()
        lines = text.splitlines()
        assert len(lines) == 4
        rows = [[float(x) for x in line.split()] for line in lines]
        assert all(len(row) == 4 for row in rows)
        from pwa.validator.package_validator import check_extrinsics_matrix
        assert check_extrinsics_matrix(rows) == []


def test_deterministic_rerun_byte_identical_payload(runs_root):
    r1 = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-det-1")
    r2 = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-det-2")
    assert r1.cli_exit == 0 and r2.cli_exit == 0
    doc1 = json.loads((r1.final_run / "camera" / "camera_plan.json").read_text(encoding="utf-8"))
    doc2 = json.loads((r2.final_run / "camera" / "camera_plan.json").read_text(encoding="utf-8"))
    assert doc1["payload"] == doc2["payload"]
    assert doc1["content_hash"] != doc2["content_hash"]  # run_id differs
    # reports (no run_id) must be byte-identical
    c1 = (r1.final_run / "camera" / "coverage-report.json").read_bytes()
    c2 = (r2.final_run / "camera" / "coverage-report.json").read_bytes()
    assert c1 == c2
    m1 = (r1.final_run / "camera" / "map.json").read_bytes()
    m2 = (r2.final_run / "camera" / "map.json").read_bytes()
    assert m1 == m2
    o1 = (r1.final_run / "camera" / "overlay-cameras.svg").read_bytes()
    o2 = (r2.final_run / "camera" / "overlay-cameras.svg").read_bytes()
    assert o1 == o2
    e1 = (r1.final_run / "camera" / "extrinsics" / "0000.txt").read_bytes()
    e2 = (r2.final_run / "camera" / "extrinsics" / "0000.txt").read_bytes()
    assert e1 == e2


def test_run_produces_all_artifacts(runs_root):
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-004")
    assert result.cli_exit == 0
    camera_dir = result.final_run / "camera"
    for name in (
        "camera_plan.json",
        "assumptions.json",
        "coverage-report.json",
        "camera-report.json",
        "map.json",
        "overlay-cameras.svg",
    ):
        assert (camera_dir / name).is_file(), name
    assert (result.final_run / "project" / "source-geometry.json").is_file()
    assert (camera_dir / "overlay-cameras.svg").stat().st_size > 0


def test_invalid_cam_run_id_is_rejected(runs_root):
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="../../evil")
    assert result.cli_exit == 2
    assert not result.final_run.exists()


def test_source_hash_mismatch_is_rejected(runs_root):
    source = runs_root / "source-geometry.json"
    doc = json.loads(source.read_text(encoding="utf-8"))
    doc["content_hash"] = "sha256:" + "0" * 64
    source.write_text(json.dumps(doc), encoding="utf-8")
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-005")
    assert result.cli_exit == 2
    assert "source_geometry_hash_mismatch" in result.diagnostic.get("reason", "")


def test_non_scene_geometry_source_is_rejected(runs_root):
    source = runs_root / "source-geometry.json"
    doc = json.loads(source.read_text(encoding="utf-8"))
    doc["schema_id"] = "not_scene_geometry"
    source.write_text(json.dumps(doc), encoding="utf-8")
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-006")
    assert result.cli_exit == 2


def test_assumptions_record_defaults(runs_root):
    result = build_camera_run(runs_root=runs_root, source_geometry=Path("source-geometry.json"), cam_run_id="cam-007")
    assert result.cli_exit == 0
    assumptions = json.loads((result.final_run / "camera" / "assumptions.json").read_text(encoding="utf-8"))
    assert assumptions["schema_id"] == "assumptions"
    assert assumptions["payload"]["stage"] == "camera"
    keys = {e["key"] for e in assumptions["payload"]["entries"]}
    assert "camera.height_m" in keys
    assert "camera.wall_clearance_m" in keys
    assert "camera.opening_clearance_m" in keys
    assert "camera.yaw_rad" in keys
    assert "camera.resolution" in keys
    for entry in assumptions["payload"]["entries"]:
        assert entry["source"] == "default"


def test_no_new_dependency():
    # AC-10: camera package uses only locked deps (numpy, stdlib).
    from pwa.camera import (  # noqa: F401
        build_adjacency,
        build_and_validate,
        build_extrinsics,
        load_scene_geometry,
        render_overlay_svg,
        place_viewpoints,
        coverage_report,
        build_camera_run,
    )