from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from pwa.contracts import load_all_schemas, load_schema_catalog, validate_artifact
from tests.conftest import REPO_ROOT, make_envelope


def _floorplan_parse_v1_1_payload() -> dict:
    return {
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
        "overlay": {
            "path": "parse/overlay.svg",
            "sha256": "sha256:" + "f" * 64,
        },
        "rooms": [
            {
                "id": "r-ab354c288e8a",
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
                "id": "w-b38b11821642",
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
        "openings": [
            {
                "id": "o-13a46a7d32db",
                "type": "window",
                "wall_id": "w-b38b11821642",
                "center": [0, 3],
                "width_m": 1.2,
                "confidence": 1.0,
                "provenance": {
                    "source_kind": "dxf",
                    "source_ref": "dxf:modelspace/PWA-WINDOW#21",
                    "source_center": [1000, 5000],
                    "source_span": [[1000, 4400], [1000, 5600]],
                },
            }
        ],
    }


def test_schema_catalog_tracks_exact_versions_and_latest_view():
    catalog = load_schema_catalog()
    assert ("project_manifest", "1.0.0") in catalog
    assert ("project_manifest", "1.1.0") in catalog
    assert ("floorplan_parse", "1.0.0") in catalog
    assert ("floorplan_parse", "1.1.0") in catalog
    assert ("floorplan_annotation", "1.0.0") in catalog

    latest = load_all_schemas()
    assert latest["project_manifest"]["allOf"][1]["properties"]["schema_version"]["const"] == "1.1.0"
    assert latest["floorplan_parse"]["allOf"][1]["properties"]["schema_version"]["const"] == "1.2.0"
    assert "floorplan_annotation" in latest
    assert "floorplan_review" in latest


def test_project_manifest_1_0_fixture_is_compatible_with_1_1_and_frozen_schema_rejects_new_kind():
    schema_1_0_path = REPO_ROOT / "schemas" / "project_manifest" / "v1" / "project_manifest-1.0.0.schema.json"
    schema_1_1_path = REPO_ROOT / "schemas" / "project_manifest" / "v1" / "project_manifest-1.1.0.schema.json"
    assert hashlib.sha256(schema_1_0_path.read_bytes()).hexdigest() == (
        "b8020d9c79fa009d49c1b7bbaa6a64fd8a7caddfeadfc4080e8a1d3033ca33e6"
    )
    schema_1_0 = json.loads(schema_1_0_path.read_text(encoding="utf-8"))
    schema_1_1 = json.loads(schema_1_1_path.read_text(encoding="utf-8"))
    schema_1_1["$id"] = schema_1_0["$id"]
    schema_1_1["allOf"][1]["properties"]["schema_version"]["const"] = "1.0.0"
    schema_1_1["allOf"][1]["properties"]["payload"]["properties"]["inputs"]["items"]["properties"]["kind"][
        "enum"
    ].remove("floorplan_page")
    assert schema_1_1 == schema_1_0

    examples = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "contracts" / "examples.json").read_text(encoding="utf-8")
    )
    historical = make_envelope("project_manifest", copy.deepcopy(examples["project_manifest"]["valid"]))
    assert validate_artifact(historical) == []

    compatible_1_1 = copy.deepcopy(historical)
    compatible_1_1["schema_version"] = "1.1.0"
    assert validate_artifact(compatible_1_1) == []

    floorplan_page = copy.deepcopy(compatible_1_1)
    floorplan_page["payload"]["inputs"].append(
        {
            "path": "project/inputs/derivatives/pdf/page-0001.png",
            "sha256": "sha256:" + "f" * 64,
            "kind": "floorplan_page",
        }
    )
    assert validate_artifact(floorplan_page) == []
    floorplan_page["schema_version"] = "1.0.0"
    assert validate_artifact(floorplan_page)


def test_validate_artifact_uses_declared_exact_version():
    examples = json.loads(
        (REPO_ROOT / "tests" / "fixtures" / "contracts" / "examples.json").read_text(encoding="utf-8")
    )
    v1_doc = make_envelope("floorplan_parse", examples["floorplan_parse"]["valid"])
    assert validate_artifact(v1_doc) == []

    v1_1_doc = make_envelope(
        "floorplan_parse",
        _floorplan_parse_v1_1_payload(),
        schema_version="1.1.0",
    )
    assert validate_artifact(v1_1_doc) == []

    mislabeled = dict(v1_1_doc, schema_version="1.0.0")
    assert validate_artifact(mislabeled)


@pytest.mark.parametrize(
    ("filename", "mutator"),
    [
        (
            "floorplan_parse-1.1.0-copy.schema.json",
            lambda schema: schema,
        ),
        (
            "floorplan_parse-1.1.1.schema.json",
            lambda schema: {**schema, "$id": schema["$id"].replace("1.1.1", "1.1.0")},
        ),
    ],
)
def test_schema_catalog_rejects_filename_version_mismatches(tmp_path: Path, filename: str, mutator) -> None:
    """These two fixtures trip the earlier filename-consistency guards
    (filename does not end with a semantic version / schema version does
    not match filename), not the D-012 duplicate-(id,version)/duplicate-$id
    branches -- see test_schema_catalog_rejects_duplicate_version_pair and
    test_schema_catalog_rejects_duplicate_schema_id below for those.
    """
    schemas_src = REPO_ROOT / "schemas"
    schemas_tmp = tmp_path / "schemas"
    shutil.copytree(schemas_src, schemas_tmp)

    source_path = schemas_tmp / "floorplan_parse" / "v1" / "floorplan_parse-1.1.0.schema.json"
    duplicate_path = source_path.with_name(filename)
    duplicate_path.write_text(
        json.dumps(mutator(json.loads(source_path.read_text(encoding="utf-8"))), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_schema_catalog(schemas_tmp)


def test_schema_catalog_rejects_duplicate_version_pair(tmp_path: Path) -> None:
    """M-8 (code review, 2026-08-10): D-012 requires "duplicate
    (schema_id, schema_version) ... is rejected". Neither fixture above
    reaches that branch (both trip earlier, unrelated filename guards). A
    second directory carrying the exact same (schema_id, schema_version) --
    a legal filename, correct internal consts, wrong directory major --
    must hit the real duplicate-pair branch.
    """
    schemas_src = REPO_ROOT / "schemas"
    schemas_tmp = tmp_path / "schemas"
    shutil.copytree(schemas_src, schemas_tmp)

    source_path = schemas_tmp / "floorplan_parse" / "v1" / "floorplan_parse-1.1.0.schema.json"
    duplicate_dir = schemas_tmp / "floorplan_parse" / "v2"
    duplicate_dir.mkdir()
    (duplicate_dir / "floorplan_parse-1.1.0.schema.json").write_text(
        source_path.read_text(encoding="utf-8"), encoding="utf-8"
    )

    with pytest.raises(ValueError, match=r"Duplicate schema version pair"):
        load_schema_catalog(schemas_tmp)


def test_schema_catalog_rejects_duplicate_schema_id(tmp_path: Path) -> None:
    """M-8 (code review, 2026-08-10): D-012 also requires "duplicate ...
    $id is rejected". Construct a schema with a genuinely different
    (schema_id, schema_version) key (so the duplicate-pair branch above does
    NOT fire first) but a $id copied unchanged from the existing 1.1.0
    schema, to reach the real duplicate-$id branch.
    """
    schemas_src = REPO_ROOT / "schemas"
    schemas_tmp = tmp_path / "schemas"
    shutil.copytree(schemas_src, schemas_tmp)

    source_path = schemas_tmp / "floorplan_parse" / "v1" / "floorplan_parse-1.1.0.schema.json"
    schema = json.loads(source_path.read_text(encoding="utf-8"))
    schema["allOf"][1]["properties"]["schema_version"]["const"] = "1.1.2"
    # $id intentionally left unchanged -- it still points at the 1.1.0 URL.
    duplicate_path = source_path.with_name("floorplan_parse-1.1.2.schema.json")
    duplicate_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"Duplicate schema \$id"):
        load_schema_catalog(schemas_tmp)
