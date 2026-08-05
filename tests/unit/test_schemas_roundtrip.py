"""Contract tests for the 13 artifact schemas + envelope (PLAN-000 T5/T9, AC4)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pwa.contracts import load_all_schemas, validate_artifact
from tests.conftest import REPO_ROOT, make_envelope

EXAMPLES = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "contracts" / "examples.json").read_text(encoding="utf-8")
)
ARTIFACT_IDS = sorted(EXAMPLES)


def test_all_13_artifact_schemas_present():
    schemas = load_all_schemas()
    assert sorted(set(schemas) - {"envelope"}) == ARTIFACT_IDS
    assert len(ARTIFACT_IDS) == 13


def test_every_schema_file_is_valid_draft_2020_12():
    for schema_id, schema in load_all_schemas().items():
        Draft202012Validator.check_schema(schema)
        assert schema["$id"].endswith(".schema.json"), schema_id


@pytest.mark.parametrize("schema_id", ARTIFACT_IDS)
def test_valid_example_passes(schema_id):
    doc = make_envelope(schema_id, EXAMPLES[schema_id]["valid"])
    assert validate_artifact(doc) == []


@pytest.mark.parametrize("schema_id", ARTIFACT_IDS)
def test_invalid_example_fails(schema_id):
    doc = make_envelope(schema_id, EXAMPLES[schema_id]["invalid"])
    errors = validate_artifact(doc)
    assert errors, f"invalid {schema_id} example unexpectedly passed validation"


@pytest.mark.parametrize("schema_id", ARTIFACT_IDS)
def test_roundtrip_preserves_validity_and_content(schema_id):
    doc = make_envelope(schema_id, EXAMPLES[schema_id]["valid"])
    restored = json.loads(json.dumps(doc))
    assert restored == doc  # semantic equality survives serialization
    assert validate_artifact(restored) == []


def test_envelope_rejects_bad_status():
    doc = make_envelope("qa_report", EXAMPLES["qa_report"]["valid"], status="done")
    assert validate_artifact(doc)


def test_envelope_partial_requires_errors():
    doc = make_envelope("qa_report", EXAMPLES["qa_report"]["valid"], status="partial", errors=[])
    assert validate_artifact(doc), "status=partial with empty errors must be rejected"


def test_envelope_rejects_bad_hash_format():
    doc = make_envelope("qa_report", EXAMPLES["qa_report"]["valid"], content_hash="md5:abc")
    assert validate_artifact(doc)


def test_map_ordering_representation_is_an_array():
    """panoworld_manifest maps.entries must be an ARRAY (order-preserving) — a
    plain JSON object would silently lose the load-bearing start-node order."""
    payload = json.loads(json.dumps(EXAMPLES["panoworld_manifest"]["valid"]))
    payload["maps"][0]["entries"] = {"0000": ["0001"]}  # object instead of array
    doc = make_envelope("panoworld_manifest", payload)
    assert validate_artifact(doc)
