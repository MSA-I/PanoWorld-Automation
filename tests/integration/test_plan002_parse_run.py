from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import ezdxf
import pytest
from PIL import Image

from pwa.contracts import compute_content_hash, validate_artifact
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


def test_copied_inventory_hash_drift_before_copy_is_rejected(tmp_path, monkeypatch):
    """A (OpenAI cross-provider rework review, 2026-08-10): preflight hashes
    the source, then copy_source_inventory() copies -- but no destination
    hash was reverified against the manifest-declared value before the
    derived manifest finalized. Simulate a file that changes on disk
    between the preflight hash check and the copy: bypass only the
    preflight comparison (by making builder.sha256_file lie for this one
    file) while the real bytes on disk are already tampered -- exactly what
    an intervening external write would look like from parse_run()'s point
    of view.
    """
    from pwa.files import sha256_file as real_sha256_file

    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-source-hash-drift")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    style_reference = next((source_run / "project" / "inputs" / "originals").glob("style_reference.*"))
    manifest = json.loads((source_run / "project" / "project_manifest.json").read_text(encoding="utf-8"))
    style_entry = next(item for item in manifest["payload"]["inputs"] if item["kind"] == "style_reference")
    original_hash = style_entry["sha256"]

    with style_reference.open("ab") as stream:
        stream.write(b"tampered-after-preflight-hash-check")

    def fake_sha256_file(path):
        if Path(path) == style_reference:
            return original_hash
        return real_sha256_file(path)

    monkeypatch.setattr("pwa.floorplan.builder.sha256_file", fake_sha256_file)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260809-parse-hash-drift",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert not result.final_run.exists()


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
