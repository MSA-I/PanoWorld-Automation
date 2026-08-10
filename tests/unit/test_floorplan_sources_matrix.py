from __future__ import annotations

import builtins
from pathlib import Path

import ezdxf
import pytest

from pwa.floorplan.dxf_source import DxfSource
from pwa.floorplan.dxf_worker import extract_dxf
from tests.unit.test_floorplan_sources import _write_dxf_fixture


def _raw_codes(raw) -> set[str]:
    return {finding.code for finding in raw.errors}


@pytest.mark.parametrize(
    ("fixture", "mutate"),
    [
        pytest.param(
            "f-unsupported-arc",
            lambda document: document.modelspace().add_arc(
                center=(0, 0), radius=1, start_angle=0, end_angle=90, dxfattribs={"layer": "PWA-WALL"}
            ),
            id="f-unsupported-arc",
        ),
        pytest.param(
            "f-unsupported-bulge",
            lambda document: document.modelspace().add_lwpolyline(
                [(0, 0, 0.1), (1000, 0, 0), (1000, 1000, 0)],
                format="xyb",
                dxfattribs={"layer": "PWA-ROOM"},
            ),
            id="f-unsupported-bulge",
        ),
        pytest.param(
            "f-unsupported-z",
            lambda document: document.modelspace().add_line((0, 0, 1.0), (1000, 0, 1.0), dxfattribs={"layer": "PWA-WALL"}),
            id="f-unsupported-z",
        ),
        pytest.param(
            "f-unsupported-insert",
            lambda document: (
                document.blocks.new("PWA_BLOCK").add_line((0, 0), (1000, 0)),
                document.modelspace().add_blockref("PWA_BLOCK", (0, 0), dxfattribs={"layer": "PWA-WALL"}),
            ),
            id="f-unsupported-insert",
        ),
        pytest.param(
            "f-unsupported-text",
            lambda document: document.modelspace().add_mtext("room", dxfattribs={"layer": "PWA-ROOM"}),
            id="f-unsupported-text",
        ),
        pytest.param(
            "f-unsupported-dim",
            lambda document: document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-DIM"}),
            id="f-unsupported-dim",
        ),
        pytest.param(
            "f-unsupported-paperspace",
            lambda document: document.layout("Layout1").add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"}),
            id="f-unsupported-paperspace",
        ),
        pytest.param(
            "f-unsupported-layout",
            lambda document: document.layouts.new("ExtraLayout").add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"}),
            id="f-unsupported-layout",
        ),
        pytest.param(
            "f-unmapped-layer",
            lambda document: document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "NOTES"}),
            id="f-unmapped-layer",
        ),
        pytest.param(
            "f-hostile-label",
            lambda document: document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "NOTES_HOSTILE_LABEL_1234567890"}),
            id="f-hostile-label",
        ),
    ],
)
def test_dxf_source_fixture_matrix(tmp_path, fixture: str, mutate):
    dxf_path = tmp_path / f"{fixture}.dxf"
    _write_dxf_fixture(dxf_path, mutate=mutate)
    if fixture == "f-hostile-label":
        text = dxf_path.read_text(encoding="utf-8")
        text = text.replace("NOTES_HOSTILE_LABEL_1234567890", "NOTES<script>alert(1)</script>")
        dxf_path.write_text(text, encoding="utf-8")

    raw = DxfSource().extract(dxf_path)

    if fixture in {"f-unmapped-layer", "f-hostile-label"}:
        assert {finding.code for finding in raw.unmapped} == {"PARSE_UNMAPPED_SOURCE_ENTITY"}
    else:
        assert _raw_codes(raw) == {"PARSE_UNSUPPORTED_FEATURE"}


def test_dxf_source_fixture_matrix_f_units_unknown(tmp_path):
    dxf_path = tmp_path / "f-units-unknown.dxf"
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 0
    document.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
    document.modelspace().add_lwpolyline([(0, 0), (1000, 0), (1000, 1000)], dxfattribs={"layer": "PWA-ROOM"}, close=True)
    document.saveas(dxf_path)

    with pytest.raises(Exception):
        DxfSource().extract(dxf_path)


def test_external_refs_never_opened(tmp_path, monkeypatch):
    dxf_path = tmp_path / "f-unsupported-xref.dxf"

    def mutate(document):
        image_def = document.add_image_def(filename="C:/should-not-open.png", size_in_pixel=(100, 100), name="IMG_DEF")
        document.modelspace().add_image(image_def, insert=(0, 0), size_in_units=(100, 100), rotation=0, dxfattribs={"layer": "PWA-WALL"})

    _write_dxf_fixture(dxf_path, mutate=mutate)
    opened: list[str] = []
    real_open = builtins.open

    def tracking_open(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", tracking_open)
    payload = extract_dxf(dxf_path)

    assert payload["errors"][0]["code"] == "PARSE_UNSUPPORTED_FEATURE"
    assert all("should-not-open.png" not in path for path in opened)


def test_external_refs_never_opened_on_unknown_layer(tmp_path, monkeypatch):
    """M-7 (code review, 2026-08-10): the §6 disposition table requires
    IMAGE/XREF/OLE/INSERT/ARC/SPLINE to fail loudly "regardless of layer".
    The layer-known check used to run first, so an IMAGE placed on an
    unknown layer (e.g. "0", the common real-world default layer)
    downgraded to PARSE_UNMAPPED_SOURCE_ENTITY/warn instead of erroring --
    the one case test_external_refs_never_opened above does not cover,
    since it places the IMAGE on the known PWA-WALL layer.
    """
    dxf_path = tmp_path / "f-unsupported-xref-unknown-layer.dxf"

    def mutate(document):
        image_def = document.add_image_def(filename="C:/should-not-open.png", size_in_pixel=(100, 100), name="IMG_DEF")
        document.modelspace().add_image(image_def, insert=(0, 0), size_in_units=(100, 100), rotation=0, dxfattribs={"layer": "0"})

    _write_dxf_fixture(dxf_path, mutate=mutate)
    opened: list[str] = []
    real_open = builtins.open

    def tracking_open(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", tracking_open)
    payload = extract_dxf(dxf_path)

    assert payload["errors"], "IMAGE on an unknown layer must be a hard error, not merely unmapped"
    assert payload["errors"][0]["code"] == "PARSE_UNSUPPORTED_FEATURE"
    assert all("should-not-open.png" not in path for path in opened)
