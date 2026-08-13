from __future__ import annotations

import json
from pathlib import Path

from tools.wp0_cpu_feasibility import evaluate_fixture


def test_fixture_without_independent_truth_or_scale_anchors_fails_closed(tmp_path: Path) -> None:
    image = Path("samples/Sample_Floorplan.jpg")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "rights": {
                    "status": "approved",
                    "license": "public-domain",
                    "source_sha256": "917a5753feceb65f8401381894bfb0809bd43194879002d2aa2acb74ee80df08",
                },
                "truth": {"independent": False, "path": None},
                "scale_anchors": [],
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_fixture(image, manifest, replays=2)

    assert result["decision"] == "STOP"
    assert result["accuracy_evaluable"] is False
    assert result["blockers"] == [
        "INDEPENDENT_TRUTH_MISSING",
        "TWO_AUTHORITATIVE_SCALE_ANCHORS_MISSING",
    ]
    assert result["rights"]["status"] == "approved"
    assert result["fixture_disposition"] == "UNSUPPORTED"
    assert result["product_b_feasibility"] == "NOT_EVALUABLE"
    assert result["runtime"]["replays_completed"] == 0


def test_untrusted_manifest_cannot_authorize_corpus_progression(tmp_path: Path) -> None:
    image = Path("samples/Sample_Floorplan.jpg")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "rights": {
                    "status": "pending",
                    "license": "unknown",
                    "source_sha256": "917a5753feceb65f8401381894bfb0809bd43194879002d2aa2acb74ee80df08",
                },
                "truth": {"independent": True, "path": "missing-truth.json"},
                "scale_anchors": [{}, {}],
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_fixture(image, manifest, replays=2)

    assert result["decision"] == "STOP"
    assert result["fixture_disposition"] == "UNSUPPORTED"
    assert result["product_b_feasibility"] == "NOT_EVALUABLE"
    assert result["blockers"] == [
        "RIGHTS_NOT_APPROVED",
        "RIGHTS_LICENSE_NOT_ALLOWED",
        "INDEPENDENT_TRUTH_FILE_MISSING",
        "AUTHORITATIVE_SCALE_ANCHORS_INVALID",
    ]
    assert result["runtime"]["replays_completed"] == 0


def test_fixture_hash_mismatch_fails_before_processing(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "rights": {
                    "status": "approved",
                    "license": "public-domain",
                    "source_sha256": "0" * 64,
                },
                "truth": {"independent": True, "path": "truth.json"},
                "scale_anchors": [{"id": "a"}, {"id": "b"}],
            }
        ),
        encoding="utf-8",
    )

    result = evaluate_fixture(Path("samples/Sample_Floorplan.jpg"), manifest, replays=2)

    assert result["decision"] == "STOP"
    assert result["blockers"] == ["SOURCE_HASH_MISMATCH"]
    assert result["runtime"]["replays_completed"] == 0
