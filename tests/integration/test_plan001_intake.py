"""PLAN-001 intake acceptance tests."""
from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import ezdxf
import pytest
from PIL import Image

from pwa.contracts import compute_content_hash, validate_artifact
from pwa.files import is_link_or_reparse, sha256_file
from pwa.intake import _image_metadata, ingest_project
from pwa.packager import build_baseline_run


def _image(path: Path, fmt: str | None = None) -> bytes:
    Image.new("RGB", (32, 16), (120, 140, 160)).save(path, format=fmt)
    return path.read_bytes()


def _floorplan(path: Path, kind: str) -> None:
    if kind == "png":
        _image(path, "PNG")
    elif kind == "jpg":
        _image(path, "JPEG")
    elif kind == "pdf":
        _image(path, "PDF")
    elif kind == "dxf":
        document = ezdxf.new("R2013")
        document.header["$INSUNITS"] = 6
        document.modelspace().add_line((0, 0), (4, 3))
        document.saveas(path)
    elif kind == "dwg":
        path.write_bytes(b"AC1032" + bytes(128))


@pytest.mark.parametrize("kind", ["png", "jpg", "pdf", "dxf", "dwg"])
def test_all_floorplan_formats_keep_original_and_emit_valid_contracts(tmp_path, kind):
    floorplan = tmp_path / f"private-name.{kind}"
    style = tmp_path / "private-style.png"
    _floorplan(floorplan, kind)
    _image(style, "PNG")
    original = floorplan.read_bytes()
    run_root = tmp_path / "stage"
    _, report = ingest_project(
        run_root,
        project_id="demo-project",
        run_id="RUN-20260806-120000-abcd",
        floorplan=floorplan,
        style_reference=style,
        goal="conceptual",
        units="m" if kind == "dwg" else "unknown",
        m_per_px=0.01 if kind in {"png", "jpg", "pdf"} else None,
    )
    manifest = json.loads((run_root / "project" / "project_manifest.json").read_text(encoding="utf-8"))
    assert validate_artifact(manifest) == []
    assert validate_artifact(report) == []
    assert manifest["content_hash"] == compute_content_hash(manifest)
    assert report["content_hash"] == compute_content_hash(report)
    copied = next((run_root / "project" / "inputs" / "originals").glob("floorplan.*"))
    assert copied.read_bytes() == original
    for item in manifest["payload"]["inputs"]:
        assert item["sha256"] == sha256_file(run_root / Path(item["path"]))
    assert "private-name" not in json.dumps(manifest)
    if kind == "pdf":
        assert list((run_root / "project" / "inputs" / "derivatives" / "pdf").glob("*.png"))
    if kind == "dxf":
        assert (run_root / "project" / "inputs" / "derivatives" / "dxf" / "preview.svg").is_file()
    if kind == "dwg":
        assert not (run_root / "project" / "inputs" / "derivatives" / "dwg").exists()


def test_unknown_scale_finalizes_blocked_run_without_package(tmp_path):
    floorplan = tmp_path / "floor.png"
    style = tmp_path / "style.png"
    _image(floorplan, "PNG")
    _image(style, "PNG")
    run, complete = build_baseline_run(
        runs_root=tmp_path / "runs",
        project_id="demo-project",
        run_id="RUN-20260806-120001-abcd",
        floorplan=floorplan,
        style_reference=style,
    )
    report = json.loads((run / "project" / "input_quality_report.json").read_text(encoding="utf-8"))
    assert not complete
    assert report["status"] == "partial"
    assert report["payload"]["blockers"] == ["INPUT_SCALE_UNKNOWN"]
    assert not (run / "package").exists()


def test_format_mismatch_and_links_are_rejected(tmp_path, monkeypatch):
    fake_jpg = tmp_path / "floor.jpg"
    style = tmp_path / "style.png"
    _image(fake_jpg, "PNG")
    _image(style, "PNG")
    with pytest.raises(ValueError, match="does not match"):
        ingest_project(
            tmp_path / "mismatch",
            project_id="demo-project",
            run_id="RUN-20260806-120002-abcd",
            floorplan=fake_jpg,
            style_reference=style,
            goal="conceptual",
            units="m",
            m_per_px=0.01,
        )

    link = tmp_path / "linked.png"
    try:
        os.symlink(style, link)
    except OSError:
        link = style
        monkeypatch.setattr("pwa.files.is_link_or_reparse", lambda path: path == style)
    with pytest.raises(ValueError, match="link or reparse"):
        ingest_project(
            tmp_path / "linked",
            project_id="demo-project",
            run_id="RUN-20260806-120003-abcd",
            floorplan=fake_jpg,
            style_reference=link,
            goal="conceptual",
            units="m",
            m_per_px=0.01,
        )


@pytest.mark.skipif(os.name != "nt", reason="Windows junction coverage")
def test_windows_junction_exercises_reparse_attribute_detection(tmp_path):
    target = tmp_path / "target"
    junction = tmp_path / "junction"
    target.mkdir()
    try:
        subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(target)],
            check=True,
            capture_output=True,
        )
        assert not junction.is_symlink()
        assert junction.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        assert is_link_or_reparse(junction)
    finally:
        if junction.exists():
            junction.rmdir()


def test_over_limit_image_is_rejected_before_verify(tmp_path, monkeypatch):
    image_path = tmp_path / "oversized.png"
    _image(image_path, "PNG")
    with Image.open(image_path) as image:
        image_type = type(image)
    verify_calls = 0

    def track_verify(_image):
        nonlocal verify_calls
        verify_calls += 1

    monkeypatch.setattr("pwa.intake.MAX_IMAGE_PIXELS", 1)
    monkeypatch.setattr(image_type, "verify", track_verify)

    with pytest.raises(ValueError, match="100-megapixel intake limit"):
        _image_metadata(image_path, ".png")
    assert verify_calls == 0
