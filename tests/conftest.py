"""Shared fixtures/helpers for the PLAN-000 test suite."""
from __future__ import annotations

from pathlib import Path

import pytest

from pwa.fixtures import make_tiny_scene

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_SUBSET = REPO_ROOT / "tests" / "golden" / "panoworld_demo_subset"


def make_envelope(schema_id: str, payload: dict, **overrides) -> dict:
    """A valid envelope document wrapping the given payload."""
    doc = {
        "schema_id": schema_id,
        "schema_version": "1.0.0",
        "artifact_id": f"{schema_id}-example-001",
        "project_id": "demo-project",
        "run_id": None,
        "created_at": "2026-08-05T12:00:00Z",
        "producer": {
            "agent": "test-agent",
            "provider": "anthropic",
            "model": "test-model",
            "effort": "N/A",
        },
        "inputs": [],
        "content_hash": "sha256:" + "0" * 64,
        "status": "complete",
        "errors": [],
        "payload": payload,
    }
    doc.update(overrides)
    return doc


@pytest.fixture
def tiny_scene(tmp_path):
    """A fully valid Layer-A scene (2 viewpoints, style pano on the start node)."""
    return make_tiny_scene(tmp_path)
