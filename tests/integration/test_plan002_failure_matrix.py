from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from pwa.contracts import compute_content_hash
from pwa.floorplan.builder import parse_run
from pwa.floorplan.config import MAX_ANNOTATION_BYTES
from pwa.floorplan.findings import FloorplanError
from pwa.floorplan.runs import validate_contained_destination
from pwa.intake import ingest_project
from tests.integration.test_plan002_parse_run import _annotation_doc, _image, _source_run
from tests.unit.test_floorplan_sources import _write_dxf_fixture


def _source_run_dxf(root: Path, run_id: str, *, manifest_units: str = "mm", mutate=None) -> Path:
    floorplan = root / f"{run_id}.dxf"
    style = root / f"{run_id}-style.png"
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
        units=manifest_units,
        m_per_px=None,
    )
    return run_root


def _write_json(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifacts_present(run_root: Path) -> bool:
    return all(
        (run_root / relative).exists()
        for relative in (
            "project/project_manifest.json",
            "project/input_quality_report.json",
            "parse/floorplan_parse.json",
            "parse/assumptions.json",
            "parse/parse-report.json",
        )
    )


def _rewrite_envelope(path: Path, mutate) -> None:
    document = _read_json(path)
    mutate(document)
    document["content_hash"] = compute_content_hash(document)
    _write_json(path, document)


def _rewrite_annotation(annotation: Path, mutate) -> None:
    document = _read_json(annotation)
    mutate(document["payload"])
    # GC-4 (OpenAI cross-provider rework review, 2026-08-10): AnnotationSource
    # now recomputes/verifies content_hash. These fixtures intentionally
    # mutate the annotation *payload* to reach a specific domain finding
    # (e.g. PARSE_SCALE_UNKNOWN) -- they are not testing tampering -- so the
    # hash must be recomputed to match, exactly like _rewrite_envelope()
    # already does for the manifest/quality envelopes above.
    document["content_hash"] = compute_content_hash(document)
    _write_json(annotation, document)


def _finalized_docs(result):
    floorplan_parse = _read_json(result.final_run / "parse" / "floorplan_parse.json")
    parse_report = _read_json(result.final_run / "parse" / "parse-report.json")
    overlay_path = result.final_run / "parse" / "overlay.svg"
    return floorplan_parse, parse_report, overlay_path


def _destination_is_rejected(root: Path, inventory_path: str) -> bool:
    try:
        validate_contained_destination(root, inventory_path)
    except (OSError, ValueError):
        return True
    return False


def test_drive_relative_inventory_destination_is_rejected(tmp_path):
    staging_root = tmp_path / "staging"
    staging_root.mkdir()

    assert _destination_is_rejected(staging_root, "C:pwa_escape/owned.txt")


def test_ads_inventory_destination_is_rejected(tmp_path):
    staging_root = tmp_path / "staging"
    staging_root.mkdir()

    assert _destination_is_rejected(staging_root, "artifact.dxf:payload")


def test_destination_containment_is_reproved_if_component_grammar_misses_drive_anchor(tmp_path, monkeypatch):
    staging_root = tmp_path / "staging"
    staging_root.mkdir()
    # The injected drive must differ from the temp root's drive or pathlib keeps it under the root.
    injected_drive = "Q:" if staging_root.drive.casefold() != "q:" else "R:"
    monkeypatch.setattr(
        "pwa.floorplan.runs._contained_parts",
        lambda relpath: (injected_drive, "pwa_escape", "owned.txt"),
    )

    assert _destination_is_rejected(staging_root, "inventory-path")


@pytest.mark.parametrize(
    "fixture",
    [
        "f-traversal",
        "f-existing-final",
        "f-existing-staging",
        "f-hash-manifest",
        "f-hash-quality",
        "f-hash-inventory",
        "f-quality-partial",
        "f-quality-blockers",
        "f-source-unsupported",
        "f-annotation-schema",
        "f-annotation-oversize",
        "f-dxf-oversize",
        "f-worker-garbage",
    ],
    ids=lambda fixture: fixture,
)
def test_operational_fixture_matrix(tmp_path, monkeypatch, fixture: str):
    expected_code = None
    source_run, copied_floorplan = _source_run(tmp_path, f"RUN-20260809-{fixture}-source")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    parse_run_id = f"RUN-20260809-{fixture}-parse"

    if fixture == "f-traversal":
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=Path("..") / source_run.name,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-existing-final":
        (tmp_path / "runs" / parse_run_id).mkdir(parents=True)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
        assert not _artifacts_present(tmp_path / "runs" / parse_run_id)
    elif fixture == "f-existing-staging":
        (tmp_path / "runs" / ".staging" / parse_run_id).mkdir(parents=True)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-hash-manifest":
        manifest_path = source_run / "project" / "project_manifest.json"
        document = _read_json(manifest_path)
        document["payload"]["goal"] = "conceptual"
        _write_json(manifest_path, document)
        expected_code = "PARSE_SOURCE_HASH_MISMATCH"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-hash-quality":
        quality_path = source_run / "project" / "input_quality_report.json"
        document = _read_json(quality_path)
        document["payload"]["checks"][0]["details"] = "tampered"
        _write_json(quality_path, document)
        expected_code = "PARSE_SOURCE_HASH_MISMATCH"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-hash-inventory":
        with copied_floorplan.open("ab") as stream:
            stream.write(b"tampered")
        expected_code = "PARSE_SOURCE_HASH_MISMATCH"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-quality-partial":
        quality_path = source_run / "project" / "input_quality_report.json"
        document = _read_json(quality_path)
        document["status"] = "partial"
        document["content_hash"] = compute_content_hash(document)
        _write_json(quality_path, document)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-quality-blockers":
        quality_path = source_run / "project" / "input_quality_report.json"
        document = _read_json(quality_path)
        document["payload"]["blockers"] = ["x"]
        document["content_hash"] = compute_content_hash(document)
        _write_json(quality_path, document)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-source-unsupported":
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
        expected_code = "PARSE_SOURCE_UNSUPPORTED"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=None,
        )
    elif fixture == "f-annotation-schema":
        document = _read_json(annotation)
        document["payload"].pop("walls")
        _write_json(annotation, document)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-annotation-oversize":
        annotation.write_bytes(b"{" + (b"x" * (MAX_ANNOTATION_BYTES + 1)))
        expected_code = "PARSE_RESOURCE_LIMIT"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=parse_run_id,
            annotation=annotation,
        )
    elif fixture == "f-dxf-oversize":
        dxf_run = _source_run_dxf(tmp_path, "RUN-20260809-source-dxf-oversize")
        monkeypatch.setattr("pwa.floorplan.builder.MAX_DXF_BYTES", 1)
        monkeypatch.setattr("pwa.floorplan.dxf_source.MAX_DXF_BYTES", 1)
        expected_code = "PARSE_RESOURCE_LIMIT"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=dxf_run,
            parse_run_id=parse_run_id,
            annotation=None,
        )
    elif fixture == "f-worker-garbage":
        dxf_run = _source_run_dxf(tmp_path, "RUN-20260809-source-worker-garbage")

        def fake_run_worker(path: Path):
            raise ValueError("worker emitted malformed JSON")

        monkeypatch.setattr("pwa.floorplan.dxf_source._run_worker", fake_run_worker)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=dxf_run,
            parse_run_id=parse_run_id,
            annotation=None,
        )
    else:
        raise AssertionError(f"Unhandled fixture: {fixture}")

    assert result.cli_exit == 2
    assert not _artifacts_present(result.final_run)
    diagnostic = result.diagnostic
    assert diagnostic is not None
    assert diagnostic["cli_exit"] == 2
    assert diagnostic["overlay"] == {"overlay_omitted_reason": "no_normalized_geometry"}
    if fixture in {"f-worker-garbage", "f-hash-inventory"}:
        assert result.staging_run.is_dir()
        assert not result.final_run.exists()
        assert (result.staging_run / "parse" / "parse-report.json").is_file()
    elif fixture == "f-existing-staging":
        assert result.staging_run.is_dir()
    else:
        assert not result.staging_run.exists()
    if expected_code is None:
        assert diagnostic["terminal_finding"] is None
    else:
        assert diagnostic["terminal_finding"]["code"] == expected_code


@pytest.mark.skipif(os.name != "nt", reason="Windows junction coverage")
def test_operational_fixture_matrix_f_ancestor_reparse(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260809-ancestor-reparse-source")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    target = tmp_path / "runs-real"
    target.mkdir()
    nested = target / source_run.name
    nested.mkdir()
    junction = tmp_path / "runs" / "linked"
    try:
        subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(target)],
            check=True,
            capture_output=True,
        )
        assert junction.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=Path("linked") / source_run.name,
            parse_run_id="RUN-20260809-f-ancestor-reparse-parse",
            annotation=annotation,
        )
        assert result.cli_exit == 2
        assert not result.staging_run.exists()
        assert result.diagnostic["terminal_finding"] is None
    finally:
        if junction.exists():
            junction.rmdir()


@pytest.mark.parametrize(
    "fixture",
    [
        "f-scale-unknown",
        "f-scale-contradictory",
        "f-units-mismatch",
        "f-units-unknown",
        "f-unsupported-arc",
        "f-unsupported-bulge",
        "f-unsupported-z",
        "f-unsupported-insert",
        "f-unsupported-xref",
        "f-unsupported-paperspace",
        "f-unsupported-layout",
        "f-unsupported-text",
        "f-unsupported-dim",
        "f-empty-walls",
        "f-empty-rooms",
        "f-empty-after-norm",
        "f-open-polygon",
        "f-open-polygon-dup",
        "f-self-intersect",
        "f-zero-area",
        "f-degenerate-wall",
        "f-duplicate-wall",
        "f-duplicate-room",
        "f-duplicate-opening",
        "f-opening-not-collinear",
        "f-unknown-wall-ref",
        "f-unknown-wall-index",
        "f-ambiguous-wall-ref",
        "f-opening-off-wall",
        "f-opening-wrong-ref",
        "f-opening-overhang",
        "f-dimension-bad",
        "f-limit-walls",
        "f-limit-vertices",
        "f-limit-coordinate",
        "f-limit-entities",
        "f-timeout",
        "f-overlay-too-big",
    ],
    ids=lambda fixture: fixture,
)
def test_failed_domain_fixture_matrix(tmp_path, monkeypatch, fixture: str):
    expected_code = ""
    expected_overlay = "present"
    expected_extra_codes: set[str] = set()

    if fixture in {
        "f-scale-unknown",
        "f-scale-contradictory",
        "f-empty-walls",
        "f-empty-rooms",
        "f-empty-after-norm",
        "f-open-polygon-dup",
        "f-self-intersect",
        "f-zero-area",
        "f-degenerate-wall",
        "f-duplicate-wall",
        "f-duplicate-room",
        "f-duplicate-opening",
        "f-unknown-wall-index",
        "f-opening-off-wall",
        "f-opening-wrong-ref",
        "f-opening-overhang",
        "f-dimension-bad",
        "f-limit-walls",
        "f-limit-vertices",
        "f-limit-coordinate",
        "f-overlay-too-big",
    }:
        source_run, copied_floorplan = _source_run(tmp_path, f"RUN-20260809-{fixture}-source")
        annotation = _annotation_doc(tmp_path, copied_floorplan)
        if fixture == "f-scale-unknown":
            _rewrite_envelope(
                source_run / "project" / "project_manifest.json",
                lambda document: document["payload"].update({"scale": {"known": False}}),
            )
            _rewrite_envelope(
                source_run / "project" / "input_quality_report.json",
                lambda document: document.update({"status": "complete"})
                or document["payload"].update({"blockers": [], "scale_known": False}),
            )
            expected_code = "PARSE_SCALE_UNKNOWN"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-scale-contradictory":
            _rewrite_annotation(annotation, lambda payload: payload.__setitem__("scale_m_per_px", 0.004))
            expected_code = "PARSE_SCALE_UNKNOWN"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-empty-walls":
            _rewrite_annotation(annotation, lambda payload: payload.__setitem__("walls", []))
            expected_code = "PARSE_EMPTY_GEOMETRY"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-empty-rooms":
            _rewrite_annotation(annotation, lambda payload: payload.__setitem__("rooms", []))
            expected_code = "PARSE_EMPTY_GEOMETRY"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-empty-after-norm":
            def mutate(payload):
                payload["walls"] = [{"start_px": [200, 1400], "end_px": [202, 1400]}]
                payload["rooms"] = [{"polygon_px": [[200, 1400], [400, 1400], [600, 1400]]}]
                payload["openings"] = []
                payload["declared_dimensions"] = []

            _rewrite_annotation(annotation, mutate)
            expected_code = "PARSE_EMPTY_GEOMETRY"
            expected_extra_codes = {"PARSE_DEGENERATE_WALL"}
        elif fixture == "f-open-polygon-dup":
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__("rooms", [{"polygon_px": [[200, 1400], [1200, 1400], [1200, 1400], [200, 200]]}]),
            )
            expected_code = "PARSE_OPEN_POLYGON"
        elif fixture == "f-self-intersect":
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__("rooms", [{"polygon_px": [[200, 1400], [1200, 200], [1200, 1400], [200, 200]]}]),
            )
            expected_code = "PARSE_SELF_INTERSECTING_POLYGON"
        elif fixture == "f-zero-area":
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__("rooms", [{"polygon_px": [[200, 1400], [400, 1400], [600, 1400]]}]),
            )
            expected_code = "PARSE_SELF_INTERSECTING_POLYGON"
        elif fixture == "f-degenerate-wall":
            _rewrite_annotation(annotation, lambda payload: payload.__setitem__("walls", [{"start_px": [200, 1400], "end_px": [209.98, 1400]}]))
            expected_code = "PARSE_DEGENERATE_WALL"
        elif fixture == "f-duplicate-wall":
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__(
                    "walls",
                    [
                        {"start_px": [200, 1400], "end_px": [1800, 1400]},
                        {"start_px": [200, 1400], "end_px": [1800, 1400]},
                    ],
                ),
            )
            expected_code = "PARSE_DUPLICATE_ENTITY"
        elif fixture == "f-duplicate-room":
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__(
                    "rooms",
                    [
                        {"polygon_px": [[200, 1400], [1200, 1400], [1200, 200], [200, 200]]},
                        {"polygon_px": [[200, 1400], [1200, 1400], [1200, 200], [200, 200]]},
                    ],
                ),
            )
            expected_code = "PARSE_DUPLICATE_ENTITY"
        elif fixture == "f-duplicate-opening":
            # C-1 (spatial review, 2026-08-10): validate() only checked
            # duplicate geometry for walls and rooms -- two coincident
            # openings collided on `id` with zero findings, status
            # complete, CLI 0, G1-eligible. §7 requires duplicate geometry
            # to fail (no suffix, no merge). Keep walls/rooms as the base
            # fixture's valid 5/2 so no other finding masks this one.
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__(
                    "openings",
                    [
                        {"type": "door", "wall_index": 0, "center_px": [700, 1400], "width_m": 0.9},
                        {"type": "door", "wall_index": 0, "center_px": [700, 1400], "width_m": 0.9},
                    ],
                ),
            )
            expected_code = "PARSE_DUPLICATE_ENTITY"
        elif fixture == "f-unknown-wall-index":
            _rewrite_annotation(annotation, lambda payload: payload["openings"][0].__setitem__("wall_index", 99))
            expected_code = "PARSE_UNKNOWN_WALL_REF"
        elif fixture == "f-opening-off-wall":
            _rewrite_annotation(annotation, lambda payload: payload["openings"][0].__setitem__("center_px", [700, 1395.98]))
            expected_code = "PARSE_OPENING_OFF_WALL"
        elif fixture == "f-opening-wrong-ref":
            _rewrite_annotation(annotation, lambda payload: payload["openings"][0].__setitem__("wall_index", 1))
            expected_code = "PARSE_OPENING_OFF_WALL"
        elif fixture == "f-opening-overhang":
            _rewrite_annotation(annotation, lambda payload: payload["openings"][0].__setitem__("center_px", [289.96, 1400]))
            expected_code = "PARSE_OPENING_WIDTH_EXCEEDS_WALL"
        elif fixture == "f-dimension-bad":
            def mutate_dimension(payload):
                payload["walls"][0]["end_px"] = [1816.02, 1400]
                payload["rooms"][1]["polygon_px"] = [[1200, 1400], [1816.02, 1400], [1816.02, 200], [1200, 200]]
                payload["openings"][3]["center_px"] = [1816.02, 500]
                payload["declared_dimensions"][0]["b_px"] = [1816.02, 1400]

            _rewrite_annotation(annotation, mutate_dimension)
            expected_code = "PARSE_DIMENSION_INCONSISTENT"
        elif fixture == "f-limit-walls":
            monkeypatch.setattr("pwa.floorplan.builder.MAX_WALLS", 1)
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__(
                    "walls",
                    [
                        {"start_px": [200, 1400], "end_px": [1800, 1400]},
                        {"start_px": [200, 200], "end_px": [1800, 200]},
                    ],
                ),
            )
            expected_code = "PARSE_RESOURCE_LIMIT"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-limit-vertices":
            monkeypatch.setattr("pwa.floorplan.builder.MAX_POLYGON_VERTICES", 3)
            _rewrite_annotation(
                annotation,
                lambda payload: payload.__setitem__("rooms", [{"polygon_px": [[200, 1400], [1200, 1400], [1200, 200], [200, 200]]}]),
            )
            expected_code = "PARSE_RESOURCE_LIMIT"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-limit-coordinate":
            _rewrite_annotation(annotation, lambda payload: payload["walls"][0].__setitem__("end_px", [20_000_001, 1400]))
            expected_code = "PARSE_RESOURCE_LIMIT"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-overlay-too-big":
            monkeypatch.setattr("pwa.floorplan.builder.render_overlay", lambda *args, **kwargs: b"x" * (70 * 1024 * 1024 + 1))
            expected_code = "PARSE_RESOURCE_LIMIT"
            expected_overlay = "overlay_exceeds_max_bytes"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-20260809-{fixture}-parse",
            annotation=annotation,
        )
    else:
        def mutate(document):
            modelspace = document.modelspace()
            if fixture == "f-units-unknown":
                document.header["$INSUNITS"] = 0
            elif fixture == "f-unsupported-arc":
                modelspace.add_arc(center=(0, 0), radius=1, start_angle=0, end_angle=90, dxfattribs={"layer": "PWA-WALL"})
            elif fixture == "f-unsupported-bulge":
                modelspace.add_lwpolyline([(0, 0, 0.1), (1000, 0, 0), (1000, 1000, 0)], format="xyb", dxfattribs={"layer": "PWA-ROOM"})
            elif fixture == "f-unsupported-z":
                modelspace.add_line((0, 0, 1.0), (1000, 0, 1.0), dxfattribs={"layer": "PWA-WALL"})
            elif fixture == "f-unsupported-insert":
                document.blocks.new("PWA_BLOCK").add_line((0, 0), (1000, 0))
                modelspace.add_blockref("PWA_BLOCK", (0, 0), dxfattribs={"layer": "PWA-WALL"})
            elif fixture == "f-unsupported-xref":
                image_def = document.add_image_def(filename="C:/should-not-open.png", size_in_pixel=(100, 100), name="IMG_DEF")
                modelspace.add_image(image_def, insert=(0, 0), size_in_units=(100, 100), rotation=0, dxfattribs={"layer": "PWA-WALL"})
            elif fixture == "f-unsupported-paperspace":
                document.layout("Layout1").add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
            elif fixture == "f-unsupported-layout":
                document.layouts.new("ExtraLayout").add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
            elif fixture == "f-unsupported-text":
                modelspace.add_mtext("room", dxfattribs={"layer": "PWA-ROOM"})
            elif fixture == "f-unsupported-dim":
                modelspace.add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-DIM"})
            elif fixture == "f-open-polygon":
                modelspace.add_lwpolyline([(0, 0), (1000, 0), (1000, 1000), (0, 1000)], dxfattribs={"layer": "PWA-ROOM"}, close=False)
            elif fixture == "f-unknown-wall-ref":
                modelspace.add_line((20_000, 20_000), (20_900, 20_000), dxfattribs={"layer": "PWA-DOOR"})
            elif fixture == "f-opening-not-collinear":
                # M-2 (spatial review, 2026-08-10): opening<->wall matching
                # used to test only the opening's centre point. This door's
                # centre (3500, 2000) sits exactly on wall1's line, but its
                # span is perpendicular to the wall (endpoints 50mm off the
                # wall line on either side, exceeding OPENING_OFFSET_M).
                # §6 requires the opening *line* to be collinear with the
                # wall; zero/multiple matches must fail.
                for entity in list(modelspace.query("LINE[layer=='PWA-DOOR']")):
                    modelspace.delete_entity(entity)
                modelspace.add_line((3500, 1950), (3500, 2050), dxfattribs={"layer": "PWA-DOOR"})
            elif fixture == "f-ambiguous-wall-ref":
                for entity in list(modelspace.query("LINE[layer=='PWA-WALL']")):
                    modelspace.delete_entity(entity)
                for entity in list(modelspace.query("LWPOLYLINE[layer=='PWA-ROOM']")):
                    modelspace.delete_entity(entity)
                for entity in list(modelspace.query("LINE[layer=='PWA-DOOR']")):
                    modelspace.delete_entity(entity)
                for entity in list(modelspace.query("LINE[layer=='PWA-WINDOW']")):
                    modelspace.delete_entity(entity)
                modelspace.add_line((1000, 2000), (5000, 2000), dxfattribs={"layer": "PWA-WALL"})
                modelspace.add_line((3000, 2000), (7000, 2000), dxfattribs={"layer": "PWA-WALL"})
                modelspace.add_line((1000, 2000), (1000, 8000), dxfattribs={"layer": "PWA-WALL"})
                modelspace.add_line((7000, 2000), (7000, 8000), dxfattribs={"layer": "PWA-WALL"})
                modelspace.add_line((1000, 8000), (7000, 8000), dxfattribs={"layer": "PWA-WALL"})
                modelspace.add_lwpolyline([(1000, 2000), (7000, 2000), (7000, 8000), (1000, 8000)], dxfattribs={"layer": "PWA-ROOM"}, close=True)
                modelspace.add_line((2550, 2000), (3450, 2000), dxfattribs={"layer": "PWA-DOOR"})

        manifest_units = "m" if fixture == "f-units-mismatch" else "mm"
        source_run = _source_run_dxf(tmp_path, f"RUN-20260809-{fixture}-source", manifest_units=manifest_units, mutate=mutate)
        if fixture == "f-units-mismatch":
            expected_code = "PARSE_UNITS_MISMATCH"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-units-unknown":
            expected_code = "PARSE_UNITS_MISMATCH"
            expected_overlay = "no_normalized_geometry"
        elif fixture.startswith("f-unsupported-"):
            expected_code = "PARSE_UNSUPPORTED_FEATURE"
        elif fixture == "f-open-polygon":
            expected_code = "PARSE_OPEN_POLYGON"
        elif fixture == "f-unknown-wall-ref":
            expected_code = "PARSE_UNKNOWN_WALL_REF"
        elif fixture == "f-opening-not-collinear":
            expected_code = "PARSE_UNKNOWN_WALL_REF"
        elif fixture == "f-ambiguous-wall-ref":
            expected_code = "PARSE_AMBIGUOUS_WALL_REF"
        elif fixture == "f-limit-entities":
            monkeypatch.setattr(
                "pwa.floorplan.dxf_source._run_worker",
                lambda path: (_ for _ in ()).throw(FloorplanError("PARSE_RESOURCE_LIMIT", "DXF entities exceed configured limit")),
            )
            expected_code = "PARSE_RESOURCE_LIMIT"
            expected_overlay = "no_normalized_geometry"
        elif fixture == "f-timeout":
            monkeypatch.setattr("pwa.floorplan.dxf_source._run_worker", lambda path: (_ for _ in ()).throw(FloorplanError("PARSE_TIMEOUT", "worker timed out")))
            expected_code = "PARSE_TIMEOUT"
            expected_overlay = "no_normalized_geometry"
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-20260809-{fixture}-parse",
            annotation=None,
        )

    assert result.cli_exit == 3
    assert result.final_run.is_dir()
    floorplan_parse, parse_report, overlay_path = _finalized_docs(result)
    assert floorplan_parse["status"] == "failed"
    assert parse_report["cli_exit"] == 3
    assert parse_report["terminal_finding"]["code"] == expected_code
    assert floorplan_parse["errors"][0]["code"] == expected_code
    assert _artifacts_present(result.final_run)
    if expected_overlay == "present":
        assert overlay_path.is_file()
        assert parse_report["overlay"]["path"] == "parse/overlay.svg"
    else:
        assert not overlay_path.exists()
        assert parse_report["overlay"]["overlay_omitted_reason"] == expected_overlay
        # M-4 (code review, 2026-08-10): a failed-domain run must never claim
        # a false overlay binding for a file that was never written -- omit
        # payload.overlay entirely instead of a path + all-zero sha256.
        assert "overlay" not in floorplan_parse["payload"]
    for code in expected_extra_codes:
        assert code in {item["code"] for item in floorplan_parse["errors"]}


@pytest.mark.parametrize(
    "fixture",
    ["f-unmapped-layer", "f-room-boundary-cross", "f-hostile-label"],
    ids=lambda fixture: fixture,
)
def test_warning_fixture_matrix(tmp_path, fixture: str):
    if fixture == "f-room-boundary-cross":
        source_run, copied_floorplan = _source_run(tmp_path, f"RUN-20260809-{fixture}-source")
        annotation = _annotation_doc(tmp_path, copied_floorplan)
        _rewrite_annotation(
            annotation,
            lambda payload: payload["rooms"].append({"polygon_px": [[1000, 1200], [2000, 1200], [2000, 400], [1000, 400]]}),
        )
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-20260809-{fixture}-parse",
            annotation=annotation,
        )
        expected_code = "PARSE_ROOM_BOUNDARY_UNMATCHED"
    else:
        def mutate(document):
            layer = "NOTES" if fixture == "f-unmapped-layer" else "NOTES_HOSTILE_LABEL_1234567890"
            document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": layer})

        source_run = _source_run_dxf(tmp_path, f"RUN-20260809-{fixture}-source", mutate=mutate)
        if fixture == "f-hostile-label":
            dxf_path = next((source_run / "project" / "inputs" / "originals").glob("floorplan.*"))
            text = dxf_path.read_text(encoding="utf-8")
            dxf_path.write_text(text.replace("NOTES_HOSTILE_LABEL_1234567890", "NOTES<script>alert(1)</script>"), encoding="utf-8")
            def refresh_manifest(document):
                for item in document["payload"]["inputs"]:
                    if item["kind"] == "floorplan":
                        from pwa.files import sha256_file
                        item["sha256"] = sha256_file(dxf_path)
            _rewrite_envelope(source_run / "project" / "project_manifest.json", refresh_manifest)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-20260809-{fixture}-parse",
            annotation=None,
        )
        expected_code = "PARSE_UNMAPPED_SOURCE_ENTITY"

    assert result.cli_exit == 1
    assert result.final_run.is_dir()
    floorplan_parse, parse_report, overlay_path = _finalized_docs(result)
    assert floorplan_parse["status"] == "partial"
    assert parse_report["cli_exit"] == 1
    assert overlay_path.is_file()
    assert parse_report["terminal_finding"]["code"] == expected_code
    if fixture == "f-hostile-label":
        overlay_text = overlay_path.read_text(encoding="utf-8")
        assert "<script" not in overlay_text.lower()
        assert "&lt;script&gt;" not in overlay_text
        assert "unknown-layer-0001" in overlay_text


def _hash_tree(root: Path) -> dict[str, str]:
    from pwa.files import sha256_file

    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.mark.parametrize("outcome", ["success", "warning", "failed_domain", "operational"], ids=lambda o: o)
def test_source_run_bytes_and_hashes_unchanged_across_outcomes(tmp_path, outcome: str):
    """AC-3 / M-9 (code review, 2026-08-10): "existing finalized source run
    bytes and hashes are unchanged after success and every failure path".
    No test anywhere asserted this before -- a future change to
    copy_source_inventory/copy_immutable (e.g. switching to shutil.move, or
    adding a "repair" step) could mutate the finalized source run and the
    suite would stay green. Snapshot {relpath: sha256} for the whole source
    run tree immediately before parse_run() and re-assert it unchanged
    after, across one representative row of each outcome category.
    """
    if outcome == "success":
        source_run, copied_floorplan = _source_run(tmp_path, f"RUN-ac3-{outcome}-source")
        annotation = _annotation_doc(tmp_path, copied_floorplan)
        before = _hash_tree(source_run)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-ac3-{outcome}-parse",
            annotation=annotation,
        )
        assert result.cli_exit == 0
    elif outcome == "warning":
        def mutate(document):
            document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "NOTES"})

        source_run = _source_run_dxf(tmp_path, f"RUN-ac3-{outcome}-source", mutate=mutate)
        before = _hash_tree(source_run)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-ac3-{outcome}-parse",
            annotation=None,
        )
        assert result.cli_exit == 1
    elif outcome == "failed_domain":
        source_run, copied_floorplan = _source_run(tmp_path, f"RUN-ac3-{outcome}-source")
        annotation = _annotation_doc(tmp_path, copied_floorplan)
        _rewrite_annotation(annotation, lambda payload: payload.__setitem__("walls", []))
        before = _hash_tree(source_run)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-ac3-{outcome}-parse",
            annotation=annotation,
        )
        assert result.cli_exit == 3
    else:  # operational: pre-existing tamper simulates a corrupted source run
        source_run, copied_floorplan = _source_run(tmp_path, f"RUN-ac3-{outcome}-source")
        annotation = _annotation_doc(tmp_path, copied_floorplan)
        with copied_floorplan.open("ab") as stream:
            stream.write(b"tampered")
        before = _hash_tree(source_run)
        result = parse_run(
            runs_root=tmp_path / "runs",
            source_run=source_run,
            parse_run_id=f"RUN-ac3-{outcome}-parse",
            annotation=annotation,
        )
        assert result.cli_exit == 2

    after = _hash_tree(source_run)
    assert after == before
