from __future__ import annotations

import base64
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

from pwa.contracts import compute_content_hash
from pwa.files import sha256_file
from pwa.floorplan.builder import parse_run
from pwa.intake import ingest_project
from tests.integration.test_plan002_parse_run import _annotation_doc, _image, _source_run


_SVG_NS = "{http://www.w3.org/2000/svg}"


def _two_page_pdf_source(root: Path, run_id: str) -> tuple[Path, list[dict]]:
    floorplan = root / f"{run_id}.pdf"
    first_page = Image.new("RGB", (1000, 800), (220, 20, 20))
    second_page = Image.new("RGB", (1000, 900), (20, 20, 220))
    first_page.save(floorplan, format="PDF", save_all=True, append_images=[second_page], resolution=72)
    style = root / f"{run_id}-style.png"
    _image(style)
    source_run = root / "runs" / run_id
    manifest, _ = ingest_project(
        source_run,
        project_id="demo-project",
        run_id=run_id,
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="m",
        m_per_px=0.005,
    )
    pages = [item for item in manifest["payload"]["inputs"] if item["kind"] == "floorplan_page"]
    assert len(pages) == 2
    return source_run, pages


def _rewrite_document(path: Path, document: dict) -> None:
    document["content_hash"] = compute_content_hash(document)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _overlay_binding(overlay: bytes) -> tuple[ET.Element, dict, bytes]:
    root = ET.fromstring(overlay)
    metadata_node = root.find(f"{_SVG_NS}metadata")
    image_node = root.find(f".//{_SVG_NS}image")
    assert metadata_node is not None and metadata_node.text is not None
    assert image_node is not None
    href = image_node.attrib["href"]
    assert href.startswith("data:image/png;base64,")
    return root, json.loads(metadata_node.text), base64.b64decode(href.split(",", 1)[1])


def test_selected_pdf_page_two_binds_hash_dimensions_pixels_and_overlay_deterministically(tmp_path):
    source_run, page_entries = _two_page_pdf_source(tmp_path, "RUN-20260811-source-pdf-page-two")
    page_one = source_run / page_entries[0]["path"]
    page_two = source_run / page_entries[1]["path"]
    annotation = _annotation_doc(tmp_path, page_two, source_root=source_run)
    annotation_document = json.loads(annotation.read_text(encoding="utf-8"))

    first = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260811-parse-pdf-page-two-a",
        annotation=annotation,
    )
    second = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260811-parse-pdf-page-two-b",
        annotation=annotation,
    )

    assert first.cli_exit == second.cli_exit == 0
    overlay_one = (first.final_run / "parse" / "overlay.svg").read_bytes()
    overlay_two = (second.final_run / "parse" / "overlay.svg").read_bytes()
    assert overlay_one == overlay_two

    root, metadata, embedded_bytes = _overlay_binding(overlay_one)
    with Image.open(page_one) as decoded_page_one, Image.open(page_two) as decoded_page_two:
        page_one_size = decoded_page_one.size
        page_two_size = decoded_page_two.size
        center = (page_two_size[0] // 2, page_two_size[1] // 2)
        page_one_pixel = decoded_page_one.getpixel((page_one_size[0] // 2, page_one_size[1] // 2))
        page_two_pixel = decoded_page_two.getpixel(center)
    with Image.open(io.BytesIO(embedded_bytes)) as embedded:
        embedded.load()
        assert embedded.size == page_two_size
        assert embedded.getpixel(center) == page_two_pixel
        assert embedded.getpixel(center) != page_one_pixel

    page_one_hash = sha256_file(page_one)
    page_two_hash = sha256_file(page_two)
    assert page_one_hash != page_two_hash
    assert annotation_document["payload"]["image"]["sha256"] == page_two_hash
    assert annotation_document["payload"]["image"]["sha256"] != page_one_hash
    assert metadata["source_sha256"] == page_two_hash
    assert metadata["source_sha256"] != page_one_hash
    assert page_one_size != page_two_size
    assert (int(root.attrib["width"]), int(root.attrib["height"])) == page_two_size
    assert (int(root.attrib["width"]), int(root.attrib["height"])) != page_one_size

    floorplan_parse = json.loads((first.final_run / "parse" / "floorplan_parse.json").read_text(encoding="utf-8"))
    first_report = json.loads((first.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    second_report = json.loads((second.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))
    assert floorplan_parse["payload"]["normalization"]["source_height_px"] == page_two_size[1]
    assert floorplan_parse["payload"]["normalization"]["source_height_px"] != page_one_size[1]
    assert first_report["overlay"] == second_report["overlay"]
    assert first_report["canonical_projection_sha256"] == second_report["canonical_projection_sha256"]


@pytest.mark.parametrize(
    "case",
    ["missing", "style_reference", "other", "raw_pdf", "non_png_floorplan_page"],
)
def test_disallowed_annotation_inventory_or_format_is_classified_unsupported(tmp_path, case):
    if case == "raw_pdf":
        source_run, page_entries = _two_page_pdf_source(tmp_path, f"RUN-20260811-source-{case}")
        selected_image = source_run / page_entries[1]["path"]
        annotation = _annotation_doc(tmp_path, selected_image, source_root=source_run)
    else:
        source_run, selected_image = _source_run(tmp_path, f"RUN-20260811-source-{case}")
        annotation = _annotation_doc(tmp_path, selected_image)

    manifest_path = source_run / "project" / "project_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    annotation_document = json.loads(annotation.read_text(encoding="utf-8"))

    if case == "missing":
        annotation_document["payload"]["image"].update(
            {
                "source_image_ref": "project/inputs/derivatives/missing.png",
                "sha256": "sha256:" + "0" * 64,
            }
        )
    elif case in {"style_reference", "other"}:
        style_entry = next(item for item in manifest["payload"]["inputs"] if item["kind"] == "style_reference")
        if case == "other":
            style_entry["kind"] = "other"
            _rewrite_document(manifest_path, manifest)
        annotation_document["payload"]["image"].update(
            {
                "source_image_ref": style_entry["path"],
                "sha256": style_entry["sha256"],
            }
        )
    elif case == "raw_pdf":
        floorplan_entry = next(item for item in manifest["payload"]["inputs"] if item["kind"] == "floorplan")
        annotation_document["payload"]["image"].update(
            {
                "source_image_ref": floorplan_entry["path"],
                "sha256": floorplan_entry["sha256"],
            }
        )
    else:
        forged_page = source_run / "project" / "inputs" / "derivatives" / "forged-page.jpg"
        forged_page.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (2000, 1800), (10, 120, 200)).save(forged_page, format="JPEG")
        forged_entry = {
            "path": forged_page.relative_to(source_run).as_posix(),
            "sha256": sha256_file(forged_page),
            "kind": "floorplan_page",
        }
        manifest["payload"]["inputs"].append(forged_entry)
        _rewrite_document(manifest_path, manifest)
        annotation_document["payload"]["image"].update(
            {
                "source_image_ref": forged_entry["path"],
                "sha256": forged_entry["sha256"],
            }
        )

    _rewrite_document(annotation, annotation_document)
    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id=f"RUN-20260811-parse-{case}",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert result.diagnostic["terminal_finding"]["code"] == "PARSE_SOURCE_UNSUPPORTED"
    assert not result.final_run.exists()


@pytest.mark.parametrize(
    ("image_format", "suffix", "media_type"),
    [("PNG", ".png", "image/png"), ("JPEG", ".jpg", "image/jpeg")],
)
def test_direct_floorplan_png_and_jpeg_annotation_paths_still_succeed(tmp_path, image_format, suffix, media_type):
    floorplan = tmp_path / f"floorplan{suffix}"
    Image.new("RGB", (2000, 1800), (245, 245, 245)).save(floorplan, format=image_format)
    style = tmp_path / "style.png"
    _image(style)
    run_id = f"RUN-20260811-source-{image_format.lower()}"
    source_run = tmp_path / "runs" / run_id
    manifest, _ = ingest_project(
        source_run,
        project_id="demo-project",
        run_id=run_id,
        floorplan=floorplan,
        style_reference=style,
        goal="precise",
        units="m",
        m_per_px=0.005,
    )
    floorplan_entry = next(item for item in manifest["payload"]["inputs"] if item["kind"] == "floorplan")
    copied_floorplan = source_run / floorplan_entry["path"]
    annotation = _annotation_doc(tmp_path, copied_floorplan)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id=f"RUN-20260811-parse-{image_format.lower()}",
        annotation=annotation,
    )

    assert result.cli_exit == 0
    overlay = (result.final_run / "parse" / "overlay.svg").read_text(encoding="utf-8")
    assert f"data:{media_type};base64," in overlay


def test_annotation_image_hash_mismatch_remains_hash_mismatch(tmp_path):
    source_run, copied_floorplan = _source_run(tmp_path, "RUN-20260811-source-annotation-hash")
    annotation = _annotation_doc(tmp_path, copied_floorplan)
    annotation_document = json.loads(annotation.read_text(encoding="utf-8"))
    annotation_document["payload"]["image"]["sha256"] = "sha256:" + "0" * 64
    _rewrite_document(annotation, annotation_document)

    result = parse_run(
        runs_root=tmp_path / "runs",
        source_run=source_run,
        parse_run_id="RUN-20260811-parse-annotation-hash",
        annotation=annotation,
    )

    assert result.cli_exit == 2
    assert result.diagnostic["terminal_finding"]["code"] == "PARSE_SOURCE_HASH_MISMATCH"
    assert not result.final_run.exists()
