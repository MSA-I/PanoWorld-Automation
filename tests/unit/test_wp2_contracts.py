"""WP2 (PLAN-002RF) — additive contracts and lifecycle.

Red→Green over the additive new-runs-only contract surface that the future
`cad_exact` / `raster_auto` recognizers (WP3/WP4) will emit, without touching
any historical byte.

Sections:
  S1  bundle + catalog exact-versioning
  S2  additive `floorplan_parse` 1.2.0 round-trip (source_class, arc/bulge,
      passage, thickness, area) and 1.0/1.1 remain byte-valid
  S3  recognition source_class authorship vocabulary
  S4  arc/bulge + thickness/area invariants
  S5  passage span bound
  S6  floorplan_review lineage + current-head invalidation
  S7  append-only topology/recognition error vocabulary
  S8  old-consumer rejection (predictable + explained)
"""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from pathlib import Path

import pytest

from pwa import contracts
from pwa.contracts import (
    CONTRACTS_BUNDLE_VERSION,
    contract_rejection_reason,
    load_all_schemas,
    load_schema_catalog,
    validate_artifact,
)
from pwa.floorplan import recognition
from tests.conftest import REPO_ROOT, make_envelope

# --------------------------------------------------------------------------- #
# S1 — bundle + catalog exact-versioning                                     #
# --------------------------------------------------------------------------- #


def _bundle_doc(payload: dict, schema_version: str = "1.2.0") -> dict:
    return make_envelope("floorplan_parse", payload, schema_version=schema_version)


def test_wp2_bundle_version_is_1_3_0():
    assert CONTRACTS_BUNDLE_VERSION == "1.3.0"


def test_wp2_catalog_tracks_new_additive_versions():
    catalog = load_schema_catalog()
    assert ("floorplan_parse", "1.2.0") in catalog
    assert ("floorplan_review", "1.0.0") in catalog
    # Historical versions remain present and independently valid.
    assert ("floorplan_parse", "1.0.0") in catalog
    assert ("floorplan_parse", "1.1.0") in catalog

    latest = load_all_schemas()
    assert latest["floorplan_parse"]["allOf"][1]["properties"]["schema_version"]["const"] == "1.2.0"


# --------------------------------------------------------------------------- #
# S2 — additive 1.2.0 round-trip                                              #
# --------------------------------------------------------------------------- #


def _floorplan_parse_1_2_full_payload() -> dict:
    return {
        "units": "m",
        "scale_m_per_px": 0.005,
        "source_class": "cad_exact",
        "rooms": [
            {
                "id": "r-aprojectowned001",
                "polygon": [[0, 0], [5, 0], [5, 6], [0, 6]],
                "confidence": 1.0,
                "area_m2": 30.0,
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": "dxf:modelspace/PWA-ROOM#11",
                    "source_polygon": [[1000, 2000], [6000, 2000], [6000, 8000], [1000, 8000]],
                },
            }
        ],
        "walls": [
            {
                "id": "w-seg001",
                "start": [0, 0],
                "end": [0, 6],
                "kind": "segment",
                "thickness_m": 0.1,
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": "dxf:modelspace/PWA-WALL#01",
                    "source_start": [1000, 2000],
                    "source_end": [1000, 8000],
                },
            },
            {
                "id": "w-arc001",
                "start": [0, 6],
                "end": [3, 6],
                "kind": "circular_arc",
                "thickness_m": 0.1,
                "confidence": 1.0,
                "arc": {
                    "center": [1.5, 6],
                    "radius_m": 1.5,
                    "start_deg": 180.0,
                    "end_deg": 0.0,
                    "sweep": "ccw",
                    "bulge": -1.0,
                    "max_sagitta_px": 0.4,
                },
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": "dxf:modelspace/PWA-WALL#02",
                    "source_start": [1000, 8000],
                    "source_end": [4000, 8000],
                },
            },
        ],
        "openings": [
            {
                "id": "o-passage001",
                "type": "passage",
                "wall_id": "w-seg001",
                "center": [0, 3],
                "width_m": 1.5,
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": "dxf:modelspace/PWA-PASSAGE#31",
                    "source_center": [1000, 5000],
                    "source_span": [[1000, 4250], [1000, 5750]],
                },
            }
        ],
    }


def test_wp2_floorplan_parse_1_2_full_payload_round_trips():
    doc = _bundle_doc(_floorplan_parse_1_2_full_payload())
    assert validate_artifact(doc) == []


def test_wp2_floorplan_parse_1_1_payload_remains_valid_under_1_2():
    # A 1.1.0-shaped payload (no source_class/kind/arc/thickness/area/passage)
    # must remain valid when declared against 1.2.0 — additive fields optional.
    payload = {
        "units": "m",
        "scale_m_per_px": None,
        "normalization": {
            "quantum_m": 0.0001,
            "source_units": "mm",
            "source_unit_scale_m": 0.001,
            "translation_m": [1.0, 2.0],
            "y_axis": "up",
            "source_height_px": None,
            "scale_m_per_px": None,
        },
        "rooms": [
            {
                "id": "r-a",
                "polygon": [[0, 0], [5, 0], [5, 6], [0, 6]],
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": "dxf:modelspace/PWA-ROOM#11",
                    "source_polygon": [[1000, 2000], [6000, 2000], [6000, 8000], [1000, 8000]],
                },
            }
        ],
        "walls": [
            {
                "id": "w-b",
                "start": [0, 0],
                "end": [0, 6],
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": "dxf:modelspace/PWA-WALL#01",
                    "source_start": [1000, 2000],
                    "source_end": [1000, 8000],
                },
            }
        ],
        "openings": [],
    }
    doc = _bundle_doc(payload)
    assert validate_artifact(doc) == []


def test_wp2_passage_is_rejected_by_1_1_consumer_but_not_1_2():
    payload = _floorplan_parse_1_2_full_payload()
    doc_1_2 = _bundle_doc(payload)
    assert validate_artifact(doc_1_2) == []

    # A 1.1.0 consumer (schema_version still 1.1.0) must reject the passage
    # opening type — predictable old-consumer rejection.
    doc_1_1 = _bundle_doc(payload, schema_version="1.1.0")
    assert validate_artifact(doc_1_1)  # non-empty -> rejected


# --------------------------------------------------------------------------- #
# S3 — source_class authorship vocabulary                                     #
# --------------------------------------------------------------------------- #

VALID_SOURCE_CLASSES = {"cad_exact", "raster_auto", "annotation", "dxf"}


def test_wp2_source_class_vocabulary_is_frozen():
    assert set(recognition.SOURCE_CLASSES) == VALID_SOURCE_CLASSES
    # Product authorship is limited to these two; human-authored classes are not product.
    assert set(recognition.PRODUCT_SOURCE_CLASSES) == {"cad_exact", "raster_auto"}


@pytest.mark.parametrize("cls", ["cad_exact", "raster_auto", "annotation", "dxf"])
def test_wp2_valid_source_classes_accepted(cls):
    assert recognition.is_valid_source_class(cls) is True


@pytest.mark.parametrize("cls", ["", "CAD_EXACT", "human", "ocr", "manual", None])
def test_wp2_invalid_source_classes_rejected(cls):
    assert recognition.is_valid_source_class(cls) is False


def test_wp2_human_truth_is_never_product_output():
    # annotation/dxf are not product classes; only cad_exact/raster_auto are.
    assert recognition.is_product_author("annotation") is False
    assert recognition.is_product_author("dxf") is False
    assert recognition.is_product_author("cad_exact") is True
    assert recognition.is_product_author("raster_auto") is True


# --------------------------------------------------------------------------- #
# S4 — arc/bulge + thickness/area invariants                                   #
# --------------------------------------------------------------------------- #


def test_wp2_arc_without_sagitta_bound_is_rejected():
    # bulge sign matches the ccw sweep, so ONLY the missing sagitta bound fires.
    arc = {"center": [1.5, 6], "radius_m": 1.5, "start_deg": 180.0, "end_deg": 0.0, "sweep": "ccw", "bulge": 1.0}
    assert recognition.arc_invariants(arc) == ["RECOGNITION_ARC_NO_SAGITTA_BOUND"]


def test_wp2_arc_bulge_sweep_mismatch_is_rejected():
    arc = {
        "center": [1.5, 6],
        "radius_m": 1.5,
        "start_deg": 180.0,
        "end_deg": 0.0,
        "sweep": "ccw",
        "bulge": -1.0,
        "max_sagitta_px": 0.4,
    }
    # bulge sign contradicts declared sweep (ccw sweep over a left-turning bulge).
    assert recognition.arc_invariants(arc) == ["RECOGNITION_ARC_BULGE_SWEEP_MISMATCH"]


def test_wp2_valid_arc_has_no_findings():
    # A CCW arc with positive bulge (left-hand bulge) is internally consistent.
    arc = {
        "center": [1.5, 6],
        "radius_m": 1.5,
        "start_deg": 180.0,
        "end_deg": 0.0,
        "sweep": "ccw",
        "bulge": 1.0,
        "max_sagitta_px": 0.4,
    }
    assert recognition.arc_invariants(arc) == []


def test_wp2_product_output_requires_thickness():
    assert recognition.check_thickness(None) == ["RECOGNITION_THICKNESS_MISSING"]
    assert recognition.check_thickness(0.0) == ["RECOGNITION_THICKNESS_MISSING"]
    assert recognition.check_thickness(0.1) == []


def test_wp2_room_area_is_centreline_shoelace_and_deterministic():
    # Independent shoelace over a known rectangle: 5x6 = 30.0 m^2.
    area = recognition.polygon_area_m2([[0, 0], [5, 0], [5, 6], [0, 6]])
    assert area == pytest.approx(30.0)
    # Deterministic over many runs (no global mutable state).
    results = [recognition.polygon_area_m2([[0, 0], [5, 0], [5, 6], [0, 6]]) for _ in range(50)]
    assert all(r == pytest.approx(30.0) for r in results)


# --------------------------------------------------------------------------- #
# S5 — passage span bound                                                     #
# --------------------------------------------------------------------------- #


def test_wp2_passage_span_bound():
    assert recognition.PASSAGE_SPAN_MAX_M == 3.0
    assert recognition.check_passage_span(1.5) == []
    assert recognition.check_passage_span(3.0) == []
    assert recognition.check_passage_span(3.001) == ["RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND"]


# --------------------------------------------------------------------------- #
# S6 — floorplan_review lineage + current-head invalidation                    #
# --------------------------------------------------------------------------- #


def _review_doc(**overrides) -> dict:
    doc = make_envelope(
        "floorplan_review",
        {
            "reviewed_artifact": {
                "artifact_id": "fp-001",
                "schema_id": "floorplan_parse",
                "schema_version": "1.2.0",
                "content_hash": "sha256:" + "a" * 64,
            },
            "verdict": "APPROVE",
            "findings": [],
            "reviewer": {
                "agent": "wp2-independent-reviewer",
                "provider": "omniroute",
                "model": "auto/best-reasoning",
                "effort": "HIGH",
                "cross_provider": True,
            },
            "lineage": {"parent_review_id": None, "current_head": True},
        },
        schema_version="1.0.0",
    )
    doc.update(overrides)
    return doc


def test_wp2_floorplan_review_round_trips():
    assert validate_artifact(_review_doc()) == []


def test_wp2_review_verdict_vocabulary_is_frozen():
    assert set(recognition.REVIEW_VERDICTS) == {"APPROVE", "APPROVE_WITH_FIXES", "NEEDS_REWORK", "BLOCKED"}


def test_wp2_review_lineage_cycle_fails_closed():
    head = recognition.append_review(None, "rev-a")
    head = recognition.append_review(head, "rev-b", parent_review_id="rev-a")
    assert head.chain_ids == ("rev-a", "rev-b")
    # id reuse is a cycle/append violation -> fail closed.
    with pytest.raises(ValueError):
        recognition.append_review(head, "rev-a")
    # a parent not in the chain is a cycle -> fail closed.
    with pytest.raises(ValueError):
        recognition.append_review(head, "rev-c", parent_review_id="rev-zzz")


def test_wp2_current_head_invalidation():
    head = recognition.append_review(None, "rev-a")
    assert head.current_head_id == "rev-a"
    # Supersede: a new head replaces the old; the OLD head object is unchanged
    # and its current_head_id is no longer the live head.
    stale = head
    new_head = recognition.supersede(stale, "rev-b")
    assert new_head.current_head_id == "rev-b"
    assert stale.current_head_id == "rev-a"  # immutable, never mutated in place
    assert stale != new_head


def test_wp2_review_is_immutable_on_reappend():
    head = recognition.append_review(None, "rev-a")
    # A second append with the same review id is rejected (append-only: id reuse forbidden).
    with pytest.raises(ValueError):
        recognition.append_review(head, "rev-a")


# --------------------------------------------------------------------------- #
# S7 — append-only topology/recognition error vocabulary                       #
# --------------------------------------------------------------------------- #


def test_wp2_error_code_vocabulary_contains_new_codes_append_only():
    text = (REPO_ROOT / "contracts" / "error_codes.md").read_text(encoding="utf-8")
    for code in recognition.BLOCKING_CODES:
        assert f"`{code}`" in text


def test_wp2_new_error_codes_are_all_error_severity():
    for code in recognition.BLOCKING_CODES:
        assert recognition.code_severity(code) == "error"


# --------------------------------------------------------------------------- #
# S8 — old-consumer rejection (predictable + explained)                        #
# --------------------------------------------------------------------------- #


def test_wp2_contract_rejection_reason_unknown_version():
    reason = contract_rejection_reason({"schema_id": "floorplan_parse", "schema_version": "9.9.9"}, "1.1.0")
    assert reason is not None
    assert reason["code"] == "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER"
    assert "9.9.9" in reason["detail"]


def test_wp2_contract_rejection_reason_new_field():
    # A 1.2.0 doc carrying the additive `source_class` field, consumed by a 1.1.0
    # consumer (additionalProperties:false) — rejection must be explained.
    doc = _bundle_doc(_floorplan_parse_1_2_full_payload())
    reason = contract_rejection_reason(doc, "1.1.0")
    assert reason is not None
    assert reason["code"] == "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER"
    assert "1.2.0" in reason["detail"]


def test_wp2_contract_rejection_reason_none_when_consumer_supports():
    doc = _bundle_doc(_floorplan_parse_1_2_full_payload())
    assert contract_rejection_reason(doc, "1.2.0") is None


def test_wp2_contract_rejection_is_deterministic_and_side_effect_free():
    doc = _bundle_doc(_floorplan_parse_1_2_full_payload())
    before = copy.deepcopy(doc)
    r1 = contract_rejection_reason(doc, "1.1.0")
    r2 = contract_rejection_reason(doc, "1.1.0")
    assert r1 == r2
    assert doc == before  # never mutates the input document


# --------------------------------------------------------------------------- #
# S9 — historical byte-identity                                                #
# --------------------------------------------------------------------------- #


def test_wp2_historical_schema_bytes_are_identical():
    # The 1.0.0 / 1.1.0 schemas and the 1.0.0 envelope must not be modified by WP2.
    # Exact SHA-256 pins prove byte-identity against the pre-WP2 committed bytes.
    pins = {
        "schemas/floorplan_parse/v1/floorplan_parse-1.0.0.schema.json": "fb2cc70f89bdbdd5608b4720bba2d4e58ab08872903588eeb89ecaaceb719274",
        "schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json": "0be18d5a106815d4c7cc7ca1010100a4dba54c088959dfdb21654e8b48adb746",
        "schemas/floorplan_annotation/v1/floorplan_annotation-1.0.0.schema.json": "99f19cd8a14e1c7ce59a784de2b105263d617eb17fd5f72b59f828bf04f1fa31",
        "schemas/envelope/v1/envelope-1.0.0.schema.json": "7eb6ca6b7f83632b35a4c87acdab3ea18deb564cf960a6503bf3919d978fec99",
    }
    for rel, expected_sha in pins.items():
        path = REPO_ROOT / rel
        assert path.exists(), rel
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected_sha, rel
        json.loads(raw.decode("utf-8"))


def test_wp2_historical_floorplan_parse_1_0_and_1_1_examples_still_validate():
    examples = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "contracts" / "examples.json").read_text(encoding="utf-8")
    )
    historical = make_envelope("floorplan_parse", examples["floorplan_parse"]["valid"])
    assert validate_artifact(historical) == []


# --------------------------------------------------------------------------- #
# S10 — concurrency                                                           #
# --------------------------------------------------------------------------- #


def test_wp2_contract_rejection_reason_is_thread_safe():
    doc = _bundle_doc(_floorplan_parse_1_2_full_payload())
    results = []
    lock = threading.Lock()

    def worker():
        r = contract_rejection_reason(doc, "1.1.0")
        with lock:
            results.append(r["code"])

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all(code == "SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER" for code in results)
