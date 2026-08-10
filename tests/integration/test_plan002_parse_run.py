from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import warnings
from pathlib import Path

import ezdxf
import pytest
from PIL import Image

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import sha256_file
from pwa.floorplan.builder import ParseRunResult, parse_run
from pwa.floorplan.config import MAX_ANNOTATION_BYTES, MAX_OVERLAY_BYTES, limits_snapshot
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
    # GC-4 (OpenAI cross-provider rework review, 2026-08-10): AnnotationSource
    # now recomputes/verifies content_hash, so fixtures must carry a real one
    # instead of the all-zero placeholder.
    document["content_hash"] = compute_content_hash(document)
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


def _source_run_dxf(root: Path, run_id: str = "RUN-20260809-source-dxf", *, mutate=None) -> Path:
    floorplan = root / "floorplan.dxf"
    style = root / "style.png"
    _write_dxf_fixture(floorplan, mutate=mutate)
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


def _rewrite_artifact(path: Path, mutate) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    document["content_hash"] = compute_content_hash(document)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return document


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
    for item in manifest["payload"]["inputs"]:
        declared_path = result.final_run / item["path"]
        assert declared_path.is_file()
        assert sha256_file(declared_path) == item["sha256"]


def test_post_finalization_inventory_hash_drift_is_not_reported_complete(tmp_path, monkeypatch):
    """GC3-2: the finalized paths are opened and re-hashed after rename."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-post-final-hash")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    real_replace = os.replace

    def replace_then_corrupt(source, destination):
        real_replace(source, destination)
        copied = next((Path(destination) / "project" / "inputs" / "originals").glob("floorplan.*"))
        with copied.open("ab") as stream:
            stream.write(b"post-finalization-drift")

    monkeypatch.setattr("pwa.floorplan.runs.os.replace", replace_then_corrupt)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-post-final-hash",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert result.diagnostic["outcome"] == "operational_failure"
    assert not result.final_run.exists()
    assert result.staging_run.is_dir()


def test_post_finalization_rollback_failure_reports_finalized_directory_left_behind(tmp_path, monkeypatch):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-post-final-rollback")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    real_replace = os.replace
    replace_calls = 0

    def replace_then_corrupt_then_refuse_rollback(source, destination):
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("forced rename-back failure")
        real_replace(source, destination)
        copied = next((Path(destination) / "project" / "inputs" / "originals").glob("floorplan.*"))
        with copied.open("ab") as stream:
            stream.write(b"post-finalization-drift")

    monkeypatch.setattr("pwa.floorplan.runs.os.replace", replace_then_corrupt_then_refuse_rollback)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-post-final-rollback",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert result.diagnostic["outcome"] == "operational_failure"
    assert result.final_run.is_dir()
    assert not result.staging_run.exists()
    assert result.diagnostic["overlay"]["overlay_omitted_reason"] == "finalized_directory_left_behind"


def test_finalization_rejects_overlay_hash_drift(tmp_path, monkeypatch):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-overlay-finalize")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    from pwa.floorplan.runs import finalize_run as real_finalize_run

    def tamper_overlay_then_finalize(staging_run, final_run, manifest):
        (Path(staging_run) / "parse" / "overlay.svg").write_bytes(b"tampered-overlay")
        return real_finalize_run(staging_run, final_run, manifest)

    monkeypatch.setattr("pwa.floorplan.builder.finalize_run", tamper_overlay_then_finalize)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-overlay-finalize",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert result.staging_run.is_dir()


def test_finalization_rejects_envelope_content_hash_drift(tmp_path, monkeypatch):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-envelope-finalize")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    from pwa.floorplan.runs import finalize_run as real_finalize_run

    def tamper_envelope_then_finalize(staging_run, final_run, manifest):
        assumptions_path = Path(staging_run) / "parse" / "assumptions.json"
        assumptions = json.loads(assumptions_path.read_text(encoding="utf-8"))
        assumptions["payload"]["entries"].append({"name": "tampered", "value": "true"})
        assumptions_path.write_text(json.dumps(assumptions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return real_finalize_run(staging_run, final_run, manifest)

    monkeypatch.setattr("pwa.floorplan.builder.finalize_run", tamper_envelope_then_finalize)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-envelope-finalize",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert result.staging_run.is_dir()


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


def test_staged_write_does_not_recreate_missing_parse_parent(tmp_path, monkeypatch):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-missing-parse-parent")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    parse_run_id = "RUN-20260810-parse-missing-parse-parent"
    staging_run = tmp_path / "runs" / ".staging" / parse_run_id
    parse_parent = staging_run / "parse"
    displaced_parent = staging_run / "parse-displaced"
    from pwa.floorplan.overlay import render_overlay as real_render_overlay

    def displace_parse_parent(geometry, source):
        overlay = real_render_overlay(geometry, source)
        parse_parent.rename(displaced_parent)
        return overlay

    monkeypatch.setattr("pwa.floorplan.builder.render_overlay", displace_parse_parent)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id=parse_run_id,
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert result.staging_run.is_dir()
    assert displaced_parent.is_dir()
    assert not parse_parent.exists()


def test_unreadable_source_input_returns_cli2_result_instead_of_raising(tmp_path, monkeypatch):
    """GC3-7: an unreadable inventory input is an operational API result."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-unreadable")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    from pwa.files import copy_immutable as real_copy_immutable

    def unreadable_source(source, destination, **kwargs):
        if Path(source) == copied_floorplan:
            raise PermissionError("input is unreadable")
        return real_copy_immutable(source, destination, **kwargs)

    monkeypatch.setattr("pwa.floorplan.runs.copy_immutable", unreadable_source)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-unreadable",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert result.diagnostic["outcome"] == "operational_failure"
    assert not result.final_run.exists()


def test_pillow_decompression_bomb_is_operational_cli2(tmp_path, monkeypatch):
    """GC3-11: an untrusted oversized raster cannot escape parse_run()."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-decompression-bomb")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1_000_000)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-decompression-bomb",
        annotation=annotation,
    )

    assert isinstance(result, ParseRunResult)
    assert result.cli_exit == 2
    assert result.diagnostic["outcome"] == "operational_failure"
    assert not result.final_run.exists()


def test_pillow_decompression_bomb_warning_as_error_is_operational_cli2(tmp_path, monkeypatch):
    """GC3-11: warnings-as-errors cannot reopen the same Pillow escape."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-decompression-warning")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 2_000_000)

    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id="RUN-20260810-parse-decompression-warning",
            annotation=annotation,
        )

    assert isinstance(result, ParseRunResult)
    assert result.cli_exit == 2
    assert result.diagnostic["outcome"] == "operational_failure"
    assert not result.final_run.exists()


@pytest.mark.parametrize(
    ("invalid_json", "case"),
    [
        ("[]", "non-object"),
        ("[" * 2_000 + "]" * 2_000, "recursive"),
        ('{"value":' + "1" * 5_000 + "}", "integer-limit"),
    ],
    ids=lambda value: value if value in {"non-object", "recursive", "integer-limit"} else None,
)
def test_annotation_json_input_failures_are_operational_cli2(tmp_path, invalid_json, case):
    """GC3-11: decoder/type failures are classified at the input boundary."""
    source_run, copied_floorplan = _source_run(tmp_path, f"RUN-20260810-source-annotation-{case}")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    annotation.write_text(invalid_json, encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id=f"RUN-20260810-parse-annotation-{case}",
        annotation=annotation,
    )

    assert isinstance(result, ParseRunResult)
    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


@pytest.mark.parametrize(
    ("artifact_name", "invalid_json"),
    [
        ("project_manifest.json", "[]"),
        ("input_quality_report.json", "[]"),
        ("project_manifest.json", "[" * 2_000 + "]" * 2_000),
    ],
    ids=("manifest-non-object", "quality-non-object", "manifest-recursive"),
)
def test_source_artifact_json_input_failures_are_operational_cli2(tmp_path, artifact_name, invalid_json):
    """GC3-11: malformed manifest/quality JSON never leaks input exceptions."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-artifact-json")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    (source_run / "project" / artifact_name).write_text(invalid_json, encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-artifact-json",
        annotation=annotation,
    )

    assert isinstance(result, ParseRunResult)
    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_programming_error_is_not_hidden_as_operational_cli2(tmp_path, monkeypatch):
    """GC3-7: genuine programming errors remain distinguishable."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-programming-error")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    def programming_error(*args, **kwargs):
        raise RuntimeError("simulated programming defect")

    monkeypatch.setattr("pwa.floorplan.builder.render_overlay", programming_error)

    with pytest.raises(RuntimeError, match="programming defect"):
        parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id="RUN-20260810-parse-programming-error",
            annotation=annotation,
        )


def test_source_inventory_hash_mismatch_fails_snapshot_before_parsing(tmp_path):
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
    assert result.staging_run.is_dir()
    assert result.diagnostic["terminal_finding"]["code"] == "PARSE_SOURCE_HASH_MISMATCH"


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


def test_cumulative_paperspace_entity_overflow_is_resource_limit_cli3(tmp_path, monkeypatch):
    """GC3-5: the DXF cap includes modelspace and every other layout."""
    floorplan = tmp_path / "paperspace-overflow.dxf"

    def add_paperspace(document):
        paperspace = document.layout("Layout1")
        paperspace.add_line((0, 0), (1, 0))
        paperspace.add_line((0, 1), (1, 1))

    _write_dxf_fixture(floorplan, mutate=add_paperspace)
    style = tmp_path / "style-paperspace-overflow.png"
    _image(style)
    source_run = tmp_path / "runs" / "RUN-20260810-source-paperspace-overflow"
    ingest_project(
        source_run,
        project_id="demo-project",
        run_id=source_run.name,
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="mm",
        m_per_px=None,
    )

    from pwa.floorplan import dxf_worker

    monkeypatch.setattr(dxf_worker, "MAX_DXF_ENTITIES", 12)

    def in_process_extract(_self, path):
        try:
            dxf_worker.extract_dxf(path)
        except ValueError as exc:
            if str(exc) == "PARSE_RESOURCE_LIMIT":
                raise FloorplanError("PARSE_RESOURCE_LIMIT", "PARSE_RESOURCE_LIMIT") from exc
            raise
        raise AssertionError("expected cumulative paperspace overflow")

    monkeypatch.setattr("pwa.floorplan.builder.DxfSource.extract", in_process_extract)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-paperspace-overflow",
        annotation=None,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    assert parse_report["terminal_finding"]["code"] == "PARSE_RESOURCE_LIMIT"
    assert floorplan_parse["errors"][0]["code"] == "PARSE_RESOURCE_LIMIT"


def test_real_dxf_worker_subprocess_maps_cumulative_entity_overflow_to_cli3(tmp_path, monkeypatch):
    """GC3-5: the cumulative cap and parent mapping compose through Popen."""
    worker_override = tmp_path / "worker-override"
    worker_override.mkdir()
    (worker_override / "sitecustomize.py").write_text(
        "import pwa.floorplan.config as _config\n_config.MAX_DXF_ENTITIES = 12\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(worker_override))

    def add_paperspace(document):
        paperspace = document.layout("Layout1")
        paperspace.add_line((0, 0), (1, 0))
        paperspace.add_line((0, 1), (1, 1))

    source_run = _source_run_dxf(
        tmp_path,
        "RUN-20260810-source-real-worker-overflow",
        mutate=add_paperspace,
    )

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-real-worker-overflow",
        annotation=None,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    assert parse_report["terminal_finding"]["code"] == "PARSE_RESOURCE_LIMIT"


def test_unknown_dxf_layout_and_layer_names_are_opaque_in_all_artifacts(tmp_path):
    """GC3-6: client-controlled DXF names never reach runtime artifacts."""
    secret_layers = ("Alice_SecretClient_Layer", "Carol_Confidential_Notes")
    secret_layouts = ("Bob_Private_Project_Layout", "Dave_Restricted_Sheet")
    floorplan = tmp_path / "private-dxf-names.dxf"

    def add_private_names(document):
        for index, layer in enumerate(secret_layers):
            document.modelspace().add_line((0, index), (1000, index), dxfattribs={"layer": layer})
        for index, layout in enumerate(secret_layouts):
            document.layouts.new(layout).add_line((0, index), (1000, index), dxfattribs={"layer": "PWA-WALL"})

    _write_dxf_fixture(floorplan, mutate=add_private_names)
    style = tmp_path / "style-private-dxf-names.png"
    _image(style)
    source_run = tmp_path / "runs" / "RUN-20260810-source-private-dxf-names"
    ingest_project(
        source_run,
        project_id="demo-project",
        run_id=source_run.name,
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="mm",
        m_per_px=None,
    )

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-private-dxf-names",
        annotation=None,
    )

    assert result.cli_exit == 3
    artifact_text = "\n".join(
        (result.final_run / relative).read_text(encoding="utf-8")
        for relative in ("parse/parse-report.json", "parse/floorplan_parse.json", "parse/overlay.svg")
    )
    assert all(name not in artifact_text for name in (*secret_layers, *secret_layouts))
    assert "unknown-layer-0001" in artifact_text
    assert "unknown-layer-0002" in artifact_text
    assert "unknown-layout-0001" in artifact_text
    assert "unknown-layout-0002" in artifact_text


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


def test_source_run_under_staging_is_not_accepted_as_finalized(tmp_path):
    """GC3-4: a source run must be a direct finalized child of runs_root."""
    source_run, _ = _source_run(tmp_path, "RUN-20260810-source-finality")
    staged_source = tmp_path / "runs" / ".staging" / source_run.name
    staged_source.parent.mkdir()
    shutil.copytree(source_run, staged_source)
    copied_floorplan = next((staged_source / "project" / "inputs" / "originals").glob("floorplan.*"))
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=staged_source,
        parse_run_id="RUN-20260810-parse-source-finality",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_source_manifest_and_quality_project_identity_must_match(tmp_path):
    """GC3-4: independently valid source artifacts cannot cross projects."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-project-identity")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    quality_path = source_run / "project" / "input_quality_report.json"
    _rewrite_artifact(quality_path, lambda document: document.update(project_id="other-project"))

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-project-identity",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_source_artifact_run_identity_must_match_source_directory(tmp_path):
    """GC3-4: manifest/quality run_id must also equal the directory name."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-run-identity")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    for name in ("project_manifest.json", "input_quality_report.json"):
        _rewrite_artifact(
            source_run / "project" / name,
            lambda document: document.update(run_id="RUN-20260810-other-source"),
        )

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-run-identity",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_source_manifest_requires_exactly_one_floorplan_input(tmp_path):
    """GC3-4: ambiguous floorplan inventory is rejected before staging."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-floorplan-cardinality")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    manifest_path = source_run / "project" / "project_manifest.json"

    def add_second_floorplan(document):
        style = next(item for item in document["payload"]["inputs"] if item["kind"] == "style_reference")
        style["kind"] = "floorplan"

    _rewrite_artifact(manifest_path, add_second_floorplan)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-floorplan-cardinality",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_source_manifest_requires_unique_inventory_paths(tmp_path):
    """GC3-4: duplicate declared input paths are rejected before staging."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-unique-paths")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    manifest_path = source_run / "project" / "project_manifest.json"

    def duplicate_path(document):
        floorplan = next(item for item in document["payload"]["inputs"] if item["kind"] == "floorplan")
        style = next(item for item in document["payload"]["inputs"] if item["kind"] == "style_reference")
        style["path"] = floorplan["path"]
        style["sha256"] = floorplan["sha256"]

    _rewrite_artifact(manifest_path, duplicate_path)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-unique-paths",
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
    # Recompute content_hash so this test keeps exercising the intended
    # "image not part of the source inventory" rejection rather than the
    # (now separately verified, see GC-4) annotation content_hash check.
    document["content_hash"] = compute_content_hash(document)
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
    # Recompute content_hash so this test keeps exercising the intended
    # dimension-mismatch rejection rather than the (now separately verified,
    # see GC-4) annotation content_hash check.
    document["content_hash"] = compute_content_hash(document)
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


def test_parse_run_id_absolute_path_is_rejected(tmp_path):
    """GC-1 (OpenAI cross-provider rework review, 2026-08-10): an absolute
    --parse-run-id must never be joined into runs_root at all.
    Path.__truediv__ silently discards the left operand when the right one
    is absolute, so `runs_root / parse_run_id` collapsed to the absolute
    value itself -- both final_run and staging_run landed outside
    runs_root, and staging_run.mkdir()/copy_source_inventory() wrote there
    before any containment check ever ran.
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-runid-absolute")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    escape_target = tmp_path / "outside-runs-root-write"
    assert not escape_target.exists()

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id=str(escape_target),
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not escape_target.exists()


def test_parse_run_id_dotdot_traversal_is_rejected(tmp_path):
    """GC-1: a relative parse_run_id containing ".." must not be able to
    walk back out of runs_root either.
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-runid-dotdot")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="../outside-runs-root-write",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not (tmp_path / "outside-runs-root-write").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction coverage")
def test_source_run_junction_alias_resolving_inside_runs_root_is_rejected(tmp_path):
    """GC-2 (OpenAI cross-provider rework review, 2026-08-10): resolve_contained_run()
    used to resolve() the candidate BEFORE walking its lexical ancestor
    chain for reparse points, so a junction whose *resolved* target still
    lands under runs_root was never actually inspected -- only the
    resolved-away "actual" component was checked, never the "alias"
    junction itself. Concretely: runs/alias -> runs/actual (both under
    runs_root, unlike the pre-existing ancestor-reparse regression test
    whose target is deliberately outside runs_root and so is already caught
    by the plain containment check regardless of ordering); a --source-run
    of runs/alias/<run> resolved straight to runs/actual/<run>, so the
    ancestor walk saw "actual", never "alias".
    """
    runs_root = tmp_path / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-junction-alias")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    actual = runs_root / "actual-runs"
    actual.mkdir()
    shutil.move(str(source_run), str(actual / source_run.name))
    alias = runs_root / "alias"
    subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(actual)],
        check=True,
        capture_output=True,
    )
    try:
        assert alias.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        result = parse_run(
            runs_root=runs_root,
            source_run=Path("alias") / source_run.name,
            parse_run_id="RUN-20260809-parse-junction-alias",
            annotation=annotation,
        )

        assert result.cli_exit == 2
        assert not result.final_run.exists()
        assert not result.staging_run.exists()
    finally:
        if alias.exists():
            alias.rmdir()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction coverage")
def test_runs_root_itself_as_a_junction_is_rejected(tmp_path):
    """GC-2: a runs_root that is itself a symlink/junction must be rejected
    before Path.resolve(strict=True) erases it -- the pre-fix code called
    that as its very first step, with no check at all.
    """
    real_root = tmp_path / "runs"
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-root-junction")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    junction_root = tmp_path / "runs-junction"
    subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction_root), str(real_root)],
        check=True,
        capture_output=True,
    )
    try:
        assert junction_root.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        result = parse_run(
            runs_root=junction_root,
            source_run=junction_root / source_run.name,
            parse_run_id="RUN-20260809-parse-root-junction",
            annotation=annotation,
        )

        assert result.cli_exit == 2
        assert not (real_root / "RUN-20260809-parse-root-junction").exists()
        assert not (real_root / ".staging" / "RUN-20260809-parse-root-junction").exists()
    finally:
        if junction_root.exists():
            junction_root.rmdir()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction coverage")
def test_destination_staging_junction_is_rejected_before_any_external_write(tmp_path):
    """GC3-1: a destination junction must be rejected before staging writes.

    The stale annotation content hash makes an unfixed parse fail only after
    copying the source inventory, leaving those copies in the junction target.
    """
    runs_root = tmp_path / "runs"
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-destination-junction")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    annotation_document = json.loads(annotation.read_text(encoding="utf-8"))
    annotation_document["payload"]["walls"][0]["end_px"] = [1750, 1400]
    annotation.write_text(json.dumps(annotation_document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    external_target = tmp_path / "outside-staging-target"
    external_target.mkdir()
    staging_junction = runs_root / ".staging"
    subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(staging_junction), str(external_target)],
        check=True,
        capture_output=True,
    )
    try:
        assert staging_junction.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        result = parse_run(
            runs_root=runs_root,
            source_run=source_run,
            parse_run_id="RUN-20260810-parse-destination-junction",
            annotation=annotation,
        )

        assert result.cli_exit == 2
        assert not result.final_run.exists()
        assert list(external_target.iterdir()) == []
    finally:
        if staging_junction.exists():
            staging_junction.rmdir()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction coverage")
def test_manifest_project_ancestor_junction_is_rejected(tmp_path):
    """GC-3 (OpenAI cross-provider rework review, 2026-08-10): parse_run()
    used to read project_manifest.json/input_quality_report.json directly
    via manifest_path.read_text()/quality_path.read_text() -- their
    "project" ancestor and artifact leaves never passed through
    resolve_contained_relpath(). A source run whose "project" directory is
    a junction is read before anything rejects it.

    The junction's target is deliberately placed *inside* source_run (not
    outside it) -- an external target would already be caught by the
    existing "inventory path escapes source_run" check for an unrelated
    reason (the resolved path fails relative_to(source_run) outright) and
    would not actually exercise this gap. A still-contained target proves
    the "project" ancestor itself is never inspected: unfixed, this must
    let the whole run complete successfully instead of being rejected.
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-manifest-junction")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    real_project = source_run / "project"
    decoy_project = source_run / "decoy-project-real"
    shutil.move(str(real_project), str(decoy_project))
    subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(real_project), str(decoy_project)],
        check=True,
        capture_output=True,
    )
    try:
        assert real_project.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id="RUN-20260809-parse-manifest-junction",
            annotation=annotation,
        )

        assert result.cli_exit == 2
        assert not result.final_run.exists()
        assert not result.staging_run.exists()
    finally:
        if real_project.exists():
            real_project.rmdir()


def test_manifest_with_no_schema_fields_returns_operational_cli2(tmp_path):
    """B (OpenAI cross-provider rework review, 2026-08-10): parse_run() must
    itself classify every reachable failure as CLI 2, not rely on cli.py's
    defense-in-depth catch. validate_artifact() raises ValueError for a
    document with no string schema_id/schema_version -- that call sat
    outside any handler, so a project_manifest.json containing "{}" raised
    out of parse_run() instead of returning ParseRunResult(cli_exit=2).
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-empty-manifest")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    manifest_path = source_run / "project" / "project_manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-empty-manifest",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_missing_annotation_file_returns_operational_cli2(tmp_path):
    """B: Path(annotation).stat() sat outside the main staging try, so
    --annotation pointing at a nonexistent file raised FileNotFoundError
    out of parse_run() instead of returning the documented CLI 2.
    """
    source_run, _copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-missing-annotation")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-missing-annotation",
        annotation=tmp_path / "does-not-exist.json",
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_annotation_read_is_bounded_before_resource_limit_check(tmp_path, monkeypatch):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-bounded-annotation")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    annotation.write_bytes(b"{" + (b"x" * MAX_ANNOTATION_BYTES))
    real_open = Path.open
    read_sizes: list[int] = []

    class BoundedReader:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.stream.close()

        def read(self, size=-1):
            read_sizes.append(size)
            if size != MAX_ANNOTATION_BYTES + 1:
                raise AssertionError("annotation read was not bounded")
            return self.stream.read(size)

    def guarded_open(path, mode="r", *args, **kwargs):
        stream = real_open(path, mode, *args, **kwargs)
        if Path(path) == annotation and mode == "rb":
            return BoundedReader(stream)
        return stream

    monkeypatch.setattr(Path, "open", guarded_open)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-bounded-annotation",
        annotation=annotation,
    )

    assert read_sizes == [MAX_ANNOTATION_BYTES + 1]
    assert result.cli_exit == 2
    assert result.diagnostic["terminal_finding"]["code"] == "PARSE_RESOURCE_LIMIT"


def test_copied_inventory_hash_drift_before_copy_is_rejected(tmp_path, monkeypatch):
    """The one-read snapshot must still match the preflight declaration."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-hash-drift")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    style_reference = next((source_run / "project" / "inputs" / "originals").glob("style_reference.*"))
    from pwa.floorplan.runs import create_contained_directory as real_create_contained_directory

    def create_then_swap(root, relpath):
        created = real_create_contained_directory(root, relpath)
        if Path(relpath) == Path("parse"):
            with style_reference.open("ab") as stream:
                stream.write(b"tampered-after-manifest-snapshot")
        return created

    monkeypatch.setattr("pwa.floorplan.builder.create_contained_directory", create_then_swap)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-hash-drift",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert result.staging_run.is_dir()
    assert result.diagnostic["terminal_finding"]["code"] == "PARSE_SOURCE_HASH_MISMATCH"


def test_dxf_is_parsed_from_verified_staging_snapshot_after_source_swap(tmp_path, monkeypatch):
    """GC3-3: replacing the source DXF after copy cannot change parsing."""
    source_run = _source_run_dxf(tmp_path, "RUN-20260810-source-dxf-snapshot")
    manifest = json.loads((source_run / "project" / "project_manifest.json").read_text(encoding="utf-8"))
    floorplan_entry = next(item for item in manifest["payload"]["inputs"] if item["kind"] == "floorplan")
    source_floorplan = source_run / floorplan_entry["path"]

    from pwa.floorplan.runs import copy_source_inventory as real_copy_source_inventory

    def copy_then_swap(source, staging, source_manifest):
        real_copy_source_inventory(source, staging, source_manifest)
        replacement = ezdxf.new("R2013")
        replacement.header["$INSUNITS"] = 0
        replacement.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
        replacement.saveas(source_floorplan)

    monkeypatch.setattr("pwa.floorplan.builder.copy_source_inventory", copy_then_swap)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-dxf-snapshot",
        annotation=None,
    )

    assert result.cli_exit == 0
    assert result.final_run.is_dir()


def test_annotation_lineage_uses_the_same_staged_snapshot_that_is_parsed(tmp_path, monkeypatch):
    """GC3-3: an annotation swapped after preflight cannot retain stale lineage."""
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260810-source-annotation-snapshot")
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    from pwa.floorplan.runs import copy_source_inventory as real_copy_source_inventory

    def copy_then_swap(source, staging, source_manifest):
        real_copy_source_inventory(source, staging, source_manifest)
        replacement = json.loads(annotation.read_text(encoding="utf-8"))
        replacement["artifact_id"] = "annotation-swapped-002"
        replacement["content_hash"] = compute_content_hash(replacement)
        annotation.write_text(json.dumps(replacement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    monkeypatch.setattr("pwa.floorplan.builder.copy_source_inventory", copy_then_swap)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260810-parse-annotation-snapshot",
        annotation=annotation,
    )

    assert result.cli_exit == 0
    copied_annotation = json.loads((result.final_run / "parse" / "annotation.json").read_text(encoding="utf-8"))
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    assert {
        "artifact_id": copied_annotation["artifact_id"],
        "content_hash": copied_annotation["content_hash"],
    } in floorplan_parse["inputs"]


def test_overlay_write_is_exclusive_and_rejects_preexisting_path(tmp_path, monkeypatch):
    """E (OpenAI cross-provider rework review, 2026-08-10): overlay_path.write_bytes()
    was neither exclusive nor no-follow, unlike every other staged output
    (which uses write_json_exclusive's O_EXCL "x" mode). A pre-planted file
    (or, for a real attacker, a symlink) at the predictable staging overlay
    path was silently followed/truncated. Simulate the race by planting a
    file at the known staging overlay path from inside a wrapped
    render_overlay() -- the real write must now fail closed instead of
    silently overwriting it.
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-overlay-exclusive")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    parse_run_id = "RUN-20260809-parse-overlay-exclusive"
    staging_overlay = tmp_path / "runs" / ".staging" / parse_run_id / "parse" / "overlay.svg"

    from pwa.floorplan.overlay import render_overlay as real_render_overlay

    planted = b"planted-before-parse-run-could-write-here"

    def planted_render_overlay(geometry, source):
        overlay_bytes = real_render_overlay(geometry, source)
        staging_overlay.parent.mkdir(parents=True, exist_ok=True)
        staging_overlay.write_bytes(planted)
        return overlay_bytes

    monkeypatch.setattr("pwa.floorplan.builder.render_overlay", planted_render_overlay)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id=parse_run_id,
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert staging_overlay.read_bytes() == planted


def test_annotation_content_hash_tamper_is_rejected(tmp_path):
    """GC-4 (OpenAI cross-provider rework review, 2026-08-10): AnnotationSource.extract()
    only schema-validated the annotation; it never recomputed content_hash.
    Changing a wall coordinate without updating content_hash must now be
    rejected instead of silently accepted.
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-annotation-tamper")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    document = json.loads(annotation.read_text(encoding="utf-8"))
    document["payload"]["walls"][0]["end_px"] = [1750, 1400]
    annotation.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-annotation-tamper",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()


def test_annotation_lineage_is_bound_into_floorplan_parse_inputs(tmp_path):
    """GC-4: floorplan_parse.inputs[] must record which annotation produced
    it, not just the derived manifest/quality report -- D-013's immutable
    lineage requirement.
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-annotation-lineage")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    annotation_document = json.loads(annotation.read_text(encoding="utf-8"))

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-annotation-lineage",
        annotation=annotation,
    )

    assert result.cli_exit == 0
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    input_ids = {item["artifact_id"] for item in floorplan_parse["inputs"]}
    input_hashes = {item["content_hash"] for item in floorplan_parse["inputs"]}
    assert annotation_document["artifact_id"] in input_ids
    assert annotation_document["content_hash"] in input_hashes


def test_annotation_binding_to_non_floorplan_kind_is_rejected(tmp_path):
    """GC-5 (OpenAI cross-provider rework review, 2026-08-10): AnnotationSource.extract()
    checked inventory membership and hash but never "kind" -- an annotation
    naming the style-reference image (same dimensions, correct hash,
    genuinely present in the source inventory) was accepted and got the
    floorplan's scale applied to it. Section 6 permits only the floorplan
    raster (or an explicitly selected PDF-page derivative).
    """
    from pwa.files import sha256_file

    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-style-binding")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    style_reference = next((source_run / "project" / "inputs" / "originals").glob("style_reference.*"))

    document = json.loads(annotation.read_text(encoding="utf-8"))
    document["payload"]["image"]["source_image_ref"] = style_reference.relative_to(source_run).as_posix()
    document["payload"]["image"]["sha256"] = sha256_file(style_reference)
    document["content_hash"] = compute_content_hash(document)
    annotation.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-style-binding",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()


def test_unsupported_arc_precedence_over_empty_geometry(tmp_path):
    """C (OpenAI cross-provider rework review, 2026-08-10): _prevalidate_raw()
    used to run before raw.errors was folded into the finding set, so its
    cardinality-check exception path discarded raw.errors entirely. A DXF
    whose only wall-like entity is an unsupported ARC on PWA-WALL (so
    raw.walls ends up empty) previously reported only PARSE_EMPTY_GEOMETRY
    (tier 2), losing the higher-precedence PARSE_UNSUPPORTED_FEATURE
    (tier 1) -- violating section 6's disposition table and finding
    precedence.
    """
    floorplan = tmp_path / "arc-only-wall.dxf"
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 4
    modelspace = document.modelspace()
    modelspace.add_arc(center=(3000, 4000), radius=1000, start_angle=0, end_angle=90, dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_lwpolyline(
        [(1000, 2000), (6000, 2000), (6000, 8000), (1000, 8000)],
        dxfattribs={"layer": "PWA-ROOM"},
        close=True,
    )
    document.saveas(floorplan)

    style = tmp_path / "style.png"
    _image(style)
    run_id = "RUN-20260809-source-arc-only-wall"
    run_root = tmp_path / "runs" / run_id
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

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=run_root,
        parse_run_id="RUN-20260809-parse-arc-only-wall",
        annotation=None,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    assert parse_report["terminal_finding"]["code"] == "PARSE_UNSUPPORTED_FEATURE"
    assert floorplan_parse["errors"][0]["code"] == "PARSE_UNSUPPORTED_FEATURE"


def test_dependencies_unchanged():
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "pyproject.toml", "uv.lock"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == ""
