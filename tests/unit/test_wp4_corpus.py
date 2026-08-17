"""Verify the PLAN-002RF WP4 R0 clean-raster corpus (synthetic, project-owned)."""
from __future__ import annotations

import json
import math
from pathlib import Path

from pwa.files import sha256_file

CORPUS = Path(__file__).resolve().parents[2] / "evidence" / "PLAN-002RF" / "WP4" / "corpus"
EXPECTED_FILES = {
    "fxx.png",
    "fxx-source-geometry.json",
    "fxx-truth.json",
    "fxx-scale-anchors.json",
    "fxx-rights-provenance.json",
    "fxx-manifest.json",
}
CANVAS = (12000.0, 10000.0)  # mm


def _fixtures():
    return sorted(d for d in CORPUS.iterdir() if d.is_dir() and d.name.startswith("f"))


def _source(d: Path) -> dict:
    return json.loads((d / "fxx-source-geometry.json").read_text(encoding="utf-8"))


def test_corpus_has_thirty_two_valid_fixtures():
    assert CORPUS.is_dir(), "corpus directory missing (run tools/make_wp4_corpus.py)"
    dirs = _fixtures()
    assert len(dirs) == 32, f"expected 32 fixtures, found {len(dirs)}"

    index = json.loads((CORPUS / "corpus-index.json").read_text(encoding="utf-8"))
    assert index["count"] == 32
    # U-5 style spread: at least one of each kind (rect / arc / diagonal).
    assert index["by_kind"]["rect"] >= 1
    assert index["by_kind"]["arc"] >= 1
    assert index["by_kind"]["diag"] >= 1

    for d in dirs:
        names = {p.name for p in d.iterdir() if p.is_file()}
        assert names == EXPECTED_FILES, f"{d.name}: unexpected files {names ^ EXPECTED_FILES}"
        manifest = json.loads((d / "fxx-manifest.json").read_text(encoding="utf-8"))
        for name, digest in manifest["files"].items():
            assert sha256_file(d / name) == digest, f"{d.name}/{name}: hash mismatch"
        truth = json.loads((d / "fxx-truth.json").read_text(encoding="utf-8"))
        source = _source(d)
        assert len(truth["walls"]) == len(source["walls"]), f"{d.name}: wall count mismatch"
        assert truth["frozen_before_recognition"] is True
        assert truth["scale_m_per_px"] == 0.005


def test_corpus_fixtures_are_unique():
    # Every fixture must be a DISTINCT plan — a duplicated fixture would inflate
    # any per-fixture acceptance score (review CRITICAL: 13/32 were duplicates).
    hashes = {sha256_file(d / "fxx-source-geometry.json") for d in _fixtures()}
    assert len(hashes) == 32, f"only {len(hashes)} distinct source geometries (duplicates present)"


def test_corpus_openings_lie_on_their_host_wall():
    for d in _fixtures():
        source = _source(d)
        walls = {w["id"]: w for w in source["walls"]}
        for o in source["openings"]:
            if "a_mm" not in o:
                continue  # arc-hosted opening (angular span, not endpoints)
            host = walls[o["host_id"]]
            ax, ay = host["a_mm"]
            bx, by = host["b_mm"]
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy) or 1.0
            # both endpoints must lie on the host wall line (cross product ~ 0)
            for (px, py) in (o["a_mm"], o["b_mm"]):
                cross = abs((px - ax) * dy - (py - ay) * dx)
                assert cross <= 0.5 * L, f"{d.name}/{o['id']}: off its host wall"
            # width_mm must equal the endpoint span (not a hand-authored constant)
            span = math.hypot(o["b_mm"][0] - o["a_mm"][0], o["b_mm"][1] - o["a_mm"][1])
            assert abs(span - o["width_mm"]) < 1.0, f"{d.name}/{o['id']}: width_mm {o['width_mm']} != span {span:.1f}"


def test_corpus_anchors_are_on_grid_in_canvas_and_non_collinear():
    for d in _fixtures():
        source = _source(d)
        anchors = source["anchors"]
        assert len(anchors) == 3, f"{d.name}: expected 3 anchors"
        directions = []
        for a in anchors:
            for (x, y) in (a["a_mm"], a["b_mm"]):
                assert x % 5 == 0 and y % 5 == 0, f"{d.name}/{a['id']}: off 5 mm grid"
                assert 0 <= x <= CANVAS[0] and 0 <= y <= CANVAS[1], f"{d.name}/{a['id']}: outside canvas"
            dx = a["b_mm"][0] - a["a_mm"][0]
            dy = a["b_mm"][1] - a["a_mm"][1]
            L = math.hypot(dx, dy)
            assert L > 0, f"{d.name}/{a['id']}: zero-length anchor"
            directions.append((dx / L, dy / L))
        # non-collinear: not all three anchors share one direction (up to sign)
        ux, uy = directions[0]
        non_collinear = any(abs(vx * uy - vy * ux) > 0.1 for (vx, vy) in directions[1:])
        assert non_collinear, f"{d.name}: anchors are collinear"


def test_corpus_fixtures_are_project_owned():
    for d in _fixtures():
        rights = json.loads((d / "fxx-rights-provenance.json").read_text(encoding="utf-8"))
        assert rights["origin"] == "project_owned_generated"
        assert rights["third_party_bytes"] == 0
        assert rights["third_party_assets"] == []
        assert rights["network_acquisition"] == "none"
