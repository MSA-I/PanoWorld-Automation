from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from pwa.contracts import validate_artifact
from pwa.floorplan.builder import parse_run
from pwa.floorplan.config import MAX_OVERLAY_BYTES, limits_snapshot
from pwa.floorplan.findings import FloorplanError
from pwa.intake import ingest_project
from tests.unit.test_floorplan_sources import _write_dxf_fixture


def _image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (2000, 1800), "white").save(path, format="PNG")


def _annotation_doc(root: Path, image_path: Path) -> Path:
    from pwa.files import sha256_file

    source_root = image_path.parents[3]
    payload = {
        "image": {
            "source_image_ref": image_path.relative_to(source_root).as_posix(),
            "sha256": sha256_file(image_path),
            "width_px": 2000,
            "height_px": 1800,
        },
        "scale_m_per_px": 0.005,
        "walls": [
            {"start_px": [200, 1400], "end_px": [1800, 1400]},
            {"start_px": [1800, 1400], "end_px": [1800, 200]},
            {"start_px": [200, 200], "end_px": [1800, 200]},
            {"start_px": [200, 1400], "end_px": [200, 200]},
            {"start_px": [1200, 1400], "end_px": [1200, 200]},
        ],
        "rooms": [
            {"polygon_px": [[200, 1400], [1200, 1400], [1200, 200], [200, 200]]},
            {"polygon_px": [[1200, 1400], [1800, 1400], [1800, 200], [1200, 200]]},
        ],
        "openings": [
            {"type": "door", "wall_index": 0, "center_px": [700, 1400], "width_m": 0.9},
            {"type": "door", "wall_index": 4, "center_px": [1200, 800], "width_m": 0.9},
            {"type": "window", "wall_index": 2, "center_px": [600, 200], "width_m": 1.2},
            {"type": "window", "wall_index": 1, "center_px": [1800, 500], "width_m": 1.2},
        ],
        "declared_dimensions": [
            {"a_px": [200, 1400], "b_px": [1800, 1400], "length_m": 8.0},
            {"a_px": [200, 1400], "b_px": [200, 200], "length_m": 6.0},
        ],
    }
    document = {
        "schema_id": "floorplan_annotation",
        "schema_version": "1.0.0",
        "artifact_id": "annotation-001",
        "project_id": "demo-project",
        "run_id": "RUN-20260809-source",
        "created_at": "2026-08-09T10:00:00Z",
        "producer": {"agent": "test", "provider": "local", "model": "deterministic", "effort": "N/A"},
        "inputs": [],
        "content_hash": "sha256:" + "0" * 64,
        "status": "complete",
        "errors": [],
        "payload": payload,
    }
    annotation = root / "annotation.json"
    annotation.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return annotation


def _source_run(root: Path, run_id: str = "RUN-20260809-source") -> tuple[Path, Path]:
    floorplan = root / "floor.png"
    style = root / "style.png"
    _image(floorplan)
    _image(style)
    run_root = root / "runs" / run_id
    ingest_project(
        run_root,
        project_id="demo-project",
        run_id=run_id,
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="m",
        m_per_px=0.005,
    )
    copied_floorplan = next((run_root / "project" / "inputs" / "originals").glob("floorplan.*"))
    return run_root, copied_floorplan


def _source_run_dxf(root: Path, run_id: str = "RUN-20260809-source-dxf") -> Path:
    floorplan = root / "floorplan.dxf"
    style = root / "style.png"
    _write_dxf_fixture(floorplan)
    _image(style)
    run_root = root / "runs" / run_id
    ingest_project(
        run_root,
        project_id="demo-project",
        run_id=run_id,
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="mm",
        m_per_px=None,
    )
    return run_root


def test_parse_run_finalizes_complete_derived_run(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path)
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-001",
        annotation=annotation,
    )

    assert result.cli_exit == 0
    assert result.final_run.is_dir()
    manifest = json.loads((result.final_run / "project" / "project_manifest.json").read_text(encoding="utf-8"))
    report = json.loads((result.final_run / "project" / "input_quality_report.json").read_text(encoding="utf-8"))
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    assumptions = json.loads((result.final_run / "parse" / "assumptions.json").read_text(encoding="utf-8"))
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))

    assert validate_artifact(manifest) == []
    assert validate_artifact(report) == []
    assert validate_artifact(floorplan_parse) == []
    assert validate_artifact(assumptions) == []
    assert manifest["payload"]["contracts_bundle_version"] == "1.1.0"
    assert floorplan_parse["schema_version"] == "1.1.0"
    assert floorplan_parse["status"] == "complete"
    assert assumptions["payload"]["stage"] == "parsing"
    assert parse_report["cli_exit"] == 0
    assert parse_report["limits"] == limits_snapshot()
    assert (result.final_run / "parse" / "overlay.svg").is_file()


def test_operational_failure_retains_staging_and_no_finalized_run(tmp_path, monkeypatch):
    source_run, copied_floorplan = _source_run(tmp_path)
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    def boom(*args, **kwargs):
        raise OSError("forced overlay failure")

    monkeypatch.setattr("pwa.floorplan.builder.render_overlay", boom)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-002",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert result.staging_run.is_dir()
    assert (result.staging_run / "parse" / "parse-report.json").is_file()


def test_source_inventory_hash_mismatch_fails_preflight_without_staging(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-hash-mismatch")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    with copied_floorplan.open("ab") as stream:
        stream.write(b"tampered")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-hash-mismatch",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_worker_garbage_is_operational_and_retains_staging(tmp_path, monkeypatch):
    source_run = _source_run_dxf(tmp_path, "RUN-20260809-source-worker-garbage")

    def fake_run_worker(path: Path):
        raise ValueError("worker emitted malformed JSON")

    monkeypatch.setattr("pwa.floorplan.dxf_source._run_worker", fake_run_worker)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-worker-garbage",
        annotation=None,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert result.staging_run.is_dir()
    parse_report = json.loads((result.staging_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    assert parse_report["outcome"] == "operational_failure"
    assert parse_report["overlay"]["overlay_omitted_reason"] == "no_normalized_geometry"
    assert parse_report["limits"] == limits_snapshot()


def test_timeout_after_valid_preflight_finalizes_failed_run(tmp_path, monkeypatch):
    source_run = _source_run_dxf(tmp_path, "RUN-20260809-source-timeout")

    def fake_run_worker(path: Path):
        raise FloorplanError("PARSE_TIMEOUT", "worker timed out")

    monkeypatch.setattr("pwa.floorplan.dxf_source._run_worker", fake_run_worker)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-timeout",
        annotation=None,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    assert not (result.final_run / "parse" / "overlay.svg").exists()
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    assert floorplan_parse["status"] == "failed"
    assert floorplan_parse["errors"][0]["code"] == "PARSE_TIMEOUT"
    assert parse_report["terminal_finding"]["code"] == "PARSE_TIMEOUT"
    assert parse_report["overlay"]["overlay_omitted_reason"] == "no_normalized_geometry"


def test_source_run_traversal_is_rejected_without_staging(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-traversal")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=Path("..") / source_run.name,
        parse_run_id="RUN-20260809-parse-traversal",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_source_run_absolute_dotdot_traversal_is_rejected_without_staging(tmp_path):
    """C-1 (code review, 2026-08-10): an *absolute* --source-run containing
    ".." must not escape runs_root. Path.relative_to() is purely lexical, so
    the guard has to reject/resolve this before it ever reaches the ancestor
    walk. The "outside" run below is fully valid on its own, so on the
    pre-fix code this would proceed past containment and (depending on the
    supplied annotation) attempt to build a derived run from it instead of
    failing closed.
    """
    runs_root = tmp_path / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    outside_root = tmp_path / "secret"
    outside_source_run, outside_floorplan = _source_run(outside_root, "evil-run")
    annotation = _annotation_doc(tmp_path, outside_floorplan)

    escaping_absolute = runs_root / ".." / "secret" / "runs" / "evil-run"
    assert escaping_absolute.resolve() == outside_source_run.resolve()

    result = parse_run(
        runs_root=runs_root,
        source_run=escaping_absolute,
        parse_run_id="RUN-20260809-parse-abs-traversal",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_manifest_inventory_path_traversal_is_rejected(tmp_path):
    """M-1 (code review, 2026-08-10): a manifest-supplied inputs[].path is
    never containment-checked, so a hand-edited manifest declaring a path
    outside the source run (or using ".." to escape staging on the write
    side) would previously be read/copied without any boundary check.
    """
    from pwa.contracts import compute_content_hash
    from pwa.files import sha256_file

    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-inventory-traversal")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    secret = tmp_path / "outside-runs-root" / "secret.png"
    secret.parent.mkdir(parents=True, exist_ok=True)
    _image(secret)

    manifest_path = source_run / "project" / "project_manifest.json"
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    document["payload"]["inputs"].append(
        {"path": str(secret), "sha256": sha256_file(secret), "kind": "other"}
    )
    document["content_hash"] = compute_content_hash(document)
    manifest_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-inventory-traversal",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_annotation_source_image_must_bind_to_source_inventory(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-image-binding")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    rogue_image = tmp_path / "project" / "inputs" / "originals" / "rogue.png"
    _image(rogue_image)

    from pwa.files import sha256_file

    document = json.loads(annotation.read_text(encoding="utf-8"))
    document["payload"]["image"]["source_image_ref"] = rogue_image.relative_to(tmp_path).as_posix()
    document["payload"]["image"]["sha256"] = sha256_file(rogue_image)
    annotation.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-image-binding",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()


def test_annotation_dimension_mismatch_is_rejected(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-dimension-mismatch")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    document = json.loads(annotation.read_text(encoding="utf-8"))
    document["payload"]["image"]["width_px"] = 1999
    annotation.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-dimension-mismatch",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()


def test_existing_final_run_id_is_rejected_before_staging(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-existing-final")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    (tmp_path / "runs" / "RUN-20260809-parse-existing-final").mkdir(parents=True)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-existing-final",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not (tmp_path / "runs" / ".staging" / "RUN-20260809-parse-existing-final").exists()


def test_existing_staging_run_id_is_rejected_before_staging(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-existing-staging")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    (tmp_path / "runs" / ".staging" / "RUN-20260809-parse-existing-staging").mkdir(parents=True)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-existing-staging",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not (tmp_path / "runs" / "RUN-20260809-parse-existing-staging").exists()


def test_overlay_size_limit_finalizes_failed_run_without_overlay(tmp_path, monkeypatch):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-overlay-limit")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    monkeypatch.setattr("pwa.floorplan.builder.render_overlay", lambda *args, **kwargs: b"x" * (MAX_OVERLAY_BYTES + 1))

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-overlay-limit",
        annotation=annotation,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    assert not (result.final_run / "parse" / "overlay.svg").exists()
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    assert floorplan_parse["errors"][0]["code"] == "PARSE_RESOURCE_LIMIT"
    assert parse_report["overlay"]["overlay_omitted_reason"] == "overlay_exceeds_max_bytes"


def test_deterministic_reruns_keep_projection_hash_and_overlay_hash(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-deterministic")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    first = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-deterministic-a",
        annotation=annotation,
    )
    second = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-deterministic-b",
        annotation=annotation,
    )

    first_parse = json.loads((first.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    second_parse = json.loads((second.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    first_report = json.loads((first.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    second_report = json.loads((second.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))

    assert first.cli_exit == 0
    assert second.cli_exit == 0
    assert first_parse["payload"]["overlay"]["sha256"] == second_parse["payload"]["overlay"]["sha256"]
    assert first_report["canonical_projection_sha256"] == second_report["canonical_projection_sha256"]


def test_dependencies_unchanged():
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "pyproject.toml", "uv.lock"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""
