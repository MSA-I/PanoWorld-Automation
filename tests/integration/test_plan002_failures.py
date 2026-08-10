from __future__ import annotations

import json
from pathlib import Path

from pwa.contracts import compute_content_hash
from pwa.floorplan.builder import parse_run
from pwa.intake import ingest_project
from tests.integration.test_plan002_parse_run import _annotation_doc, _image, _source_run


def test_incomplete_source_quality_returns_cli_2_and_no_runs(tmp_path):
    floorplan = tmp_path / "floor.png"
    style = tmp_path / "style.png"
    _image(floorplan)
    _image(style)
    source_run = tmp_path / "runs" / "RUN-20260809-source-partial"
    ingest_project(
        source_run,
        project_id="demo-project",
        run_id="RUN-20260809-source-partial",
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="m",
        m_per_px=None,
    )

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-partial",
        annotation=None,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_annotation_scale_mismatch_finalizes_failed_cli_3_run(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-good")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    document = json.loads(annotation.read_text(encoding="utf-8"))
    document["payload"]["scale_m_per_px"] = 0.006
    # Recompute content_hash so this keeps exercising the intended
    # PARSE_SCALE_UNKNOWN domain rejection rather than the (now separately
    # verified, see GC-4) annotation content_hash check.
    document["content_hash"] = compute_content_hash(document)
    annotation.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-scale-mismatch",
        annotation=annotation,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))

    assert floorplan_parse["status"] == "failed"
    assert floorplan_parse["errors"][0]["code"] == "PARSE_SCALE_UNKNOWN"
    assert parse_report["cli_exit"] == 3
    assert parse_report["terminal_finding"]["code"] == "PARSE_SCALE_UNKNOWN"


def test_source_unsupported_returns_cli_2_without_runs(tmp_path):
    floorplan = tmp_path / "floorplan.dwg"
    style = tmp_path / "style.png"
    floorplan.write_bytes(b"AC1032placeholder")
    _image(style)
    source_run = tmp_path / "runs" / "RUN-20260809-source-dwg"
    ingest_project(
        source_run,
        project_id="demo-project",
        run_id="RUN-20260809-source-dwg",
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="m",
        m_per_px=None,
    )

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-dwg",
        annotation=None,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_missing_source_manifest_returns_cli_2_instead_of_raising(tmp_path):
    """M-3 (code review, 2026-08-10): a --source-run directory that exists
    but is not a completed intake run (missing project_manifest.json) must
    be classified as an "unreadable/invalid source contract" -> CLI 2, no
    finalized run -- not an uncaught FileNotFoundError escaping parse_run().
    """
    source_run = tmp_path / "runs" / "RUN-20260809-source-no-manifest"
    (source_run / "project").mkdir(parents=True)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-no-manifest",
        annotation=None,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_malformed_source_manifest_json_returns_cli_2_instead_of_raising(tmp_path):
    """M-3 (code review, 2026-08-10): malformed JSON in the source manifest
    must not raise json.JSONDecodeError out of parse_run().
    """
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-bad-json")
    manifest_path = source_run / "project" / "project_manifest.json"
    manifest_path.write_text("{not valid json", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-bad-json",
        annotation=None,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()
    assert not result.staging_run.exists()


def test_dxf_source_with_unknown_manifest_units_returns_failed_run_not_uncaught_exception(tmp_path):
    """M-2 (code review, 2026-08-10): "unknown" is a valid project_manifest
    units enum value. When the source is DXF and the manifest declares
    units == "unknown", the DXF/manifest mismatch check raises
    PARSE_UNITS_MISMATCH (a failed-domain code), which used to make
    _failed_scale_artifacts raise a second, uncaught ValueError from inside
    the `except FloorplanError` handler instead of finalizing a failed run.
    """
    from pwa.contracts import compute_content_hash
    from tests.integration.test_plan002_failure_matrix import _source_run_dxf

    source_run = _source_run_dxf(tmp_path, "RUN-20260809-source-units-unknown-manifest")
    manifest_path = source_run / "project" / "project_manifest.json"
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    document["payload"]["units"] = "unknown"
    document["content_hash"] = compute_content_hash(document)
    manifest_path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-units-unknown-manifest",
        annotation=None,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    assert floorplan_parse["status"] == "failed"
    assert floorplan_parse["errors"][0]["code"] == "PARSE_UNITS_MISMATCH"
    assert "normalization" not in floorplan_parse["payload"]
    assert "overlay" not in floorplan_parse["payload"]


def test_empty_annotation_geometry_finalizes_failed_cli_3_run(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-empty")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    document = json.loads(annotation.read_text(encoding="utf-8"))
    document["payload"]["walls"] = []
    document["payload"]["rooms"] = []
    # Recompute content_hash so this keeps exercising the intended
    # PARSE_EMPTY_GEOMETRY domain rejection rather than the (now separately
    # verified, see GC-4) annotation content_hash check.
    document["content_hash"] = compute_content_hash(document)
    annotation.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-empty",
        annotation=annotation,
    )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    floorplan_parse = json.loads((result.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    parse_report = json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    assert floorplan_parse["errors"][0]["code"] == "PARSE_EMPTY_GEOMETRY"
    assert parse_report["terminal_finding"]["code"] == "PARSE_EMPTY_GEOMETRY"
