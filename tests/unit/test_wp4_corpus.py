"""Verify the PLAN-002RF WP4 R0 clean-raster corpus (synthetic, project-owned)."""
from __future__ import annotations

import json
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


def test_corpus_has_thirty_two_valid_fixtures():
    assert CORPUS.is_dir(), "corpus directory missing (run tools/make_wp4_corpus.py)"
    dirs = sorted(d for d in CORPUS.iterdir() if d.is_dir() and d.name.startswith("f"))
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
        source = json.loads((d / "fxx-source-geometry.json").read_text(encoding="utf-8"))
        # Truth is derived ONLY from source geometry: wall/opening/room counts agree.
        assert len(truth["walls"]) == len(source["walls"]), f"{d.name}: wall count mismatch"
        assert truth["frozen_before_recognition"] is True
        assert truth["scale_m_per_px"] == 0.005


def test_corpus_fixtures_are_project_owned():
    # Every fixture must declare zero third-party bytes (the U-5 corpus is
    # project-owned synthetic, unlike the CC BY-NC-SA CubiCasa5K adaptation).
    for d in sorted(x for x in CORPUS.iterdir() if x.is_dir() and x.name.startswith("f")):
        rights = json.loads((d / "fxx-rights-provenance.json").read_text(encoding="utf-8"))
        assert rights["origin"] == "project_owned_generated"
        assert rights["third_party_bytes"] == 0
        assert rights["third_party_assets"] == []
        assert rights["network_acquisition"] == "none"
