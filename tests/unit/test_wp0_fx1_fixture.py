from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from PIL import Image

_TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "make_wp0_fx1_fixture.py"
_SPEC = importlib.util.spec_from_file_location("make_wp0_fx1_fixture", _TOOL_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
build_fixture = _MODULE.build_fixture
verify_fixture = _MODULE.verify_fixture


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_build_fixture_emits_independent_truth_and_distributed_scale_anchors(tmp_path):
    package = build_fixture(tmp_path / "fx1")

    assert package == tmp_path / "fx1"
    assert {path.name for path in package.iterdir()} == {
        "fx1-source-geometry.json",
        "fx1.png",
        "fx1-truth.json",
        "fx1-scale-anchors.json",
        "fx1-rights-provenance.json",
        "fx1-manifest.json",
    }

    source = _load(package / "fx1-source-geometry.json")
    truth = _load(package / "fx1-truth.json")
    anchors = _load(package / "fx1-scale-anchors.json")
    manifest = _load(package / "fx1-manifest.json")
    rights = _load(package / "fx1-rights-provenance.json")

    assert source["origin"] == "project_owned_deterministic_synthetic"
    assert rights == {
        "origin": "project_owned_generated",
        "third_party_bytes": 0,
        "third_party_assets": [],
        "network_acquisition": "none",
        "license_statement": "This synthetic fixture is project-created; no repository-wide distribution-license claim is made.",
        "local_only": True,
    }
    assert {wall["kind"] for wall in source["walls"]} == {"segment", "circular_arc"}
    assert any(wall.get("orientation") == "diagonal_3_4_5" for wall in source["walls"])
    assert {opening["type"] for opening in source["openings"]} == {"door", "window", "passage"}
    assert len(source["rooms"]) == 3
    assert len(source["clutter"]) == 9

    assert truth["derived_only_from"] == ["fx1-source-geometry.json"]
    assert truth["recognizer_inputs"] == []
    assert truth["frozen_before_recognition"] is True
    assert truth["source_sha256"] == manifest["files"]["fx1-source-geometry.json"]

    assert len(anchors["anchors"]) >= 2
    directions = [
        (anchor["b_px"][0] - anchor["a_px"][0], anchor["b_px"][1] - anchor["a_px"][1])
        for anchor in anchors["anchors"]
    ]
    assert any(ax * by - ay * bx != 0 for ax, ay in directions for bx, by in directions)
    assert len({anchor["placement_region"] for anchor in anchors["anchors"]}) >= 2
    assert all(anchor["real_length_m"] / anchor["span_px"] == 0.005 for anchor in anchors["anchors"])
    assert anchors["source_sha256"] == manifest["files"]["fx1-source-geometry.json"]
    assert anchors["raster_sha256"] == manifest["files"]["fx1.png"]
    assert anchors["truth_sha256"] == manifest["files"]["fx1-truth.json"]
    assert manifest["dependency_policy"] == "existing local environment only; pinned-environment proof pending; no install performed"

    image = Image.open(package / "fx1.png")
    assert image.mode == "L"
    assert image.size == (2400, 2000)
    assert set(np.asarray(image).ravel()) == {0, 64, 128, 255}
    pixels = np.asarray(image)
    # Passage O-P1 is a real gap in W-PV, not a symbol painted over a solid wall.
    assert pixels[640, 800] == 255
    # Door O-D1 removes the hosted wall at its centre.
    assert pixels[1700, 500] == 255
    assert verify_fixture(package)["valid"] is True


def test_replay_is_byte_deterministic_and_detects_mutation(tmp_path):
    first = build_fixture(tmp_path / "first")
    second = build_fixture(tmp_path / "second")

    first_manifest = _load(first / "fx1-manifest.json")
    second_manifest = _load(second / "fx1-manifest.json")
    assert first_manifest["files"] == second_manifest["files"]
    assert first_manifest["replay_hash"] == second_manifest["replay_hash"]

    raster = second / "fx1.png"
    raster.write_bytes(raster.read_bytes() + b"mutation")
    report = verify_fixture(second)
    assert report["valid"] is False
    assert "fx1.png" in report["mismatches"]


@pytest.mark.parametrize("unsafe_name", ["../outside.json", "/absolute.json"])
def test_verify_rejects_manifest_paths_outside_package(tmp_path, unsafe_name):
    package = build_fixture(tmp_path / "fx1")
    manifest_path = package / "fx1-manifest.json"
    manifest = _load(manifest_path)
    manifest["files"][unsafe_name] = manifest["files"].pop("fx1.png")
    manifest["replay_hash"] = _MODULE._canonical_hash(manifest["files"])
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = verify_fixture(package)

    assert report["valid"] is False
    assert "manifest_file_scope" in report["mismatches"]


def test_verify_requires_exact_payload_set_and_no_unbound_files(tmp_path):
    package = build_fixture(tmp_path / "fx1")
    manifest_path = package / "fx1-manifest.json"
    manifest = _load(manifest_path)
    manifest["files"].pop("fx1-rights-provenance.json")
    manifest["replay_hash"] = _MODULE._canonical_hash(manifest["files"])
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (package / "unbound.txt").write_text("not hash-bound", encoding="utf-8")

    report = verify_fixture(package)

    assert report["valid"] is False
    assert "manifest_file_scope" in report["mismatches"]
    assert "unexpected_files" in report["mismatches"]


def test_evidence_index_binds_every_entry_to_nominated_git_commit():
    repository = _TOOL_PATH.parents[1]
    index = _load(repository / "evidence/PLAN-002RF/WP0-FX1/evidence-index.json")
    commit = index["generated_against_commit"]

    for entry in index["entries"]:
        blob = subprocess.run(
            ["git", "show", f"{commit}:{entry['path']}"],
            cwd=repository,
            capture_output=True,
            check=True,
        ).stdout
        blob_id = subprocess.run(
            ["git", "rev-parse", f"{commit}:{entry['path']}"],
            cwd=repository,
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()

        assert entry["git_blob"] == blob_id
        assert entry["sha256"] == f"sha256:{hashlib.sha256(blob).hexdigest()}"
        assert entry["bytes"] == len(blob)


def test_cli_needs_no_pythonpath(tmp_path):
    package = tmp_path / "cli-fixture"
    built = subprocess.run(
        [sys.executable, str(_TOOL_PATH), "--out", str(package)],
        cwd=_TOOL_PATH.parents[1],
        capture_output=True,
        env={},
    )
    assert built.returncode == 0, built.stderr

    verified = subprocess.run(
        [sys.executable, str(_TOOL_PATH), "--verify", str(package)],
        cwd=_TOOL_PATH.parents[1],
        capture_output=True,
        env={},
    )
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout.decode("utf-8"))["valid"] is True
