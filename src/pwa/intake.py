"""Immutable local intake baseline for PLAN-001."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import ezdxf
import pypdfium2 as pdfium
from ezdxf import recover
from ezdxf.addons.drawing import Frontend, RenderContext, layout, svg
from PIL import Image

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import copy_immutable, sha256_file, write_json_exclusive

FLOORPLAN_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg"}
STYLE_SUFFIXES = {".png", ".jpg", ".jpeg"}
MAX_PDF_PAGES = 20
MAX_PREVIEW_DIMENSION = 4096
MAX_IMAGE_PIXELS = 100_000_000
MAX_INPUT_BYTES = 250 * 1024 * 1024
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
_DWG_HEADER_RE = re.compile(rb"^AC10\d{2}")
_DXF_UNITS = {4: "mm", 5: "cm", 6: "m"}


def _artifact(
    schema_id: str,
    payload: dict,
    *,
    project_id: str,
    run_id: str,
    status: str = "complete",
    errors: list[dict] | None = None,
) -> dict:
    document = {
        "schema_id": schema_id,
        "schema_version": "1.0.0",
        "artifact_id": f"{run_id}:{schema_id}",
        "project_id": project_id,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "producer": {
            "agent": "plan001-intake",
            "provider": "local",
            "model": "deterministic-python",
            "effort": "N/A",
        },
        "inputs": [],
        "content_hash": "sha256:" + "0" * 64,
        "status": status,
        "errors": errors or [],
        "payload": payload,
    }
    document["content_hash"] = compute_content_hash(document)
    schema_errors = validate_artifact(document)
    if schema_errors:
        raise ValueError(f"generated {schema_id} failed schema: {schema_errors[0].message}")
    return document


def _image_metadata(path: Path, expected_suffix: str) -> dict:
    expected = "JPEG" if expected_suffix in {".jpg", ".jpeg"} else "PNG"
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        if image.format != expected:
            raise ValueError(f"file extension does not match image format {image.format}")
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ValueError("image exceeds the 100-megapixel intake limit")
        return {"format": image.format, "width": image.width, "height": image.height, "mode": image.mode}


def _render_pdf(path: Path, derivatives: Path) -> tuple[dict, list[Path]]:
    with path.open("rb") as stream:
        signature = stream.read(5)
    if signature != b"%PDF-":
        raise ValueError("file extension does not match PDF signature")
    document = pdfium.PdfDocument(str(path))
    try:
        page_count = len(document)
        if not 1 <= page_count <= MAX_PDF_PAGES:
            raise ValueError(f"PDF page count must be 1..{MAX_PDF_PAGES}")
        outputs: list[Path] = []
        derivatives.mkdir(parents=True, exist_ok=True)
        for index in range(page_count):
            page = document[index]
            width, height = page.get_size()
            scale = min(2.0, MAX_PREVIEW_DIMENSION / max(width, height))
            bitmap = page.render(scale=scale)
            try:
                output = derivatives / f"page-{index + 1:04d}.png"
                bitmap.to_pil().convert("RGB").save(output, format="PNG")
                outputs.append(output)
            finally:
                bitmap.close()
                page.close()
        return {"format": "PDF", "pages": page_count}, outputs
    finally:
        document.close()


def _read_dxf(path: Path, preview: Path) -> tuple[dict, str | None]:
    try:
        document, auditor = recover.readfile(path)
    except (OSError, ezdxf.DXFError) as exc:
        raise ValueError(f"invalid DXF: {type(exc).__name__}") from exc
    if auditor.has_errors:
        raise ValueError(f"DXF audit reported {len(auditor.errors)} error(s)")
    backend = svg.SVGBackend()
    Frontend(RenderContext(document), backend).draw_layout(document.modelspace())
    preview.parent.mkdir(parents=True, exist_ok=True)
    with preview.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(backend.get_string(layout.Page(0, 0)))
    units = _DXF_UNITS.get(int(document.header.get("$INSUNITS", 0)))
    return {
        "format": "DXF",
        "version": document.dxfversion,
        "layers": len(document.layers),
        "entities": len(document.modelspace()),
    }, units


def _read_dwg(path: Path) -> dict:
    with path.open("rb") as stream:
        header = stream.read(6)
    if not _DWG_HEADER_RE.fullmatch(header):
        raise ValueError("file extension does not match a supported DWG header")
    return {"format": "DWG", "version": header.decode("ascii"), "bytes": path.stat().st_size}


def ingest_project(
    run_root: Path,
    *,
    project_id: str,
    run_id: str,
    floorplan: Path,
    style_reference: Path,
    goal: str,
    units: str,
    m_per_px: float | None,
) -> tuple[dict, dict]:
    if not _ID_RE.fullmatch(project_id):
        raise ValueError("project_id must be lowercase ASCII letters/digits/hyphens")
    if goal not in {"conceptual", "precise"} or units not in {"m", "cm", "mm", "unknown"}:
        raise ValueError("invalid goal or units")
    if m_per_px is not None and m_per_px <= 0:
        raise ValueError("m_per_px must be positive")

    floorplan = Path(floorplan)
    style_reference = Path(style_reference)
    for source in (floorplan, style_reference):
        if not source.is_file() or source.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError("input must be a regular file no larger than 250 MiB")
    floor_suffix = floorplan.suffix.lower()
    style_suffix = style_reference.suffix.lower()
    if floor_suffix not in FLOORPLAN_SUFFIXES or style_suffix not in STYLE_SUFFIXES:
        raise ValueError("unsupported floorplan or style-reference extension")

    originals = run_root / "project" / "inputs" / "originals"
    floor_copy = originals / f"floorplan{floor_suffix}"
    style_copy = originals / f"style_reference{style_suffix}"
    floor_hash = copy_immutable(floorplan, floor_copy)
    style_hash = copy_immutable(style_reference, style_copy)

    checks: list[dict] = []
    derivative_entries: list[dict] = []
    inferred_units: str | None = None
    if floor_suffix in {".png", ".jpg", ".jpeg"}:
        metadata = _image_metadata(floor_copy, floor_suffix)
    elif floor_suffix == ".pdf":
        metadata, outputs = _render_pdf(
            floor_copy, run_root / "project" / "inputs" / "derivatives" / "pdf"
        )
        derivative_entries = [
            {"path": p.relative_to(run_root).as_posix(), "sha256": sha256_file(p), "kind": "other"}
            for p in outputs
        ]
    elif floor_suffix == ".dxf":
        preview = run_root / "project" / "inputs" / "derivatives" / "dxf" / "preview.svg"
        metadata, inferred_units = _read_dxf(floor_copy, preview)
        derivative_entries = [
            {"path": preview.relative_to(run_root).as_posix(), "sha256": sha256_file(preview), "kind": "other"}
        ]
    else:
        metadata = _read_dwg(floor_copy)

    style_metadata = _image_metadata(style_copy, style_suffix)
    if units == "unknown" and inferred_units:
        units = inferred_units
    scale_known = (m_per_px is not None) if floor_suffix in {".png", ".jpg", ".jpeg", ".pdf"} else units != "unknown"
    blockers = [] if scale_known else ["INPUT_SCALE_UNKNOWN"]
    checks.extend(
        [
            {"check": "floorplan_readability", "result": "pass", "details": str(metadata)},
            {"check": "style_reference_readability", "result": "pass", "details": str(style_metadata)},
            {
                "check": "scale_and_units",
                "result": "pass" if scale_known else "fail",
                "details": "known" if scale_known else "scale or CAD units were not supplied/detected",
            },
        ]
    )

    inputs = [
        {"path": floor_copy.relative_to(run_root).as_posix(), "sha256": floor_hash, "kind": "floorplan"},
        {"path": style_copy.relative_to(run_root).as_posix(), "sha256": style_hash, "kind": "style_reference"},
        *derivative_entries,
    ]
    manifest = _artifact(
        "project_manifest",
        {
            "goal": goal,
            "units": units,
            "scale": {"known": scale_known, "m_per_px": m_per_px},
            "inputs": inputs,
            "contracts_bundle_version": "1.0.0",
        },
        project_id=project_id,
        run_id=run_id,
    )
    report_errors = [] if scale_known else [
        {"code": "INPUT_SCALE_UNKNOWN", "message": "scale or CAD units are required before packaging"}
    ]
    report = _artifact(
        "input_quality_report",
        {"scale_known": scale_known, "checks": checks, "blockers": blockers},
        project_id=project_id,
        run_id=run_id,
        status="complete" if scale_known else "partial",
        errors=report_errors,
    )
    write_json_exclusive(run_root / "project" / "project_manifest.json", manifest)
    write_json_exclusive(run_root / "project" / "input_quality_report.json", report)
    return manifest, report
