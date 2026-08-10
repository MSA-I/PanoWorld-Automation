from __future__ import annotations

import io

from PIL import Image

from pwa.floorplan.overlay import render_overlay
from pwa.floorplan.types import NormOpening, NormRoom, NormWall, NormalizedGeometry, SourceFrame


def _geometry() -> NormalizedGeometry:
    return NormalizedGeometry(
        units="m",
        walls=(
            NormWall("w-b38b11821642", (0.0, 0.0), (0.0, 6.0), 1.0, {"source_ref": "wall<script>"}),
            NormWall("w-8829e7c2d2cc", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "south"}),
        ),
        rooms=(
            NormRoom("r-ab354c288e8a", ((0.0, 0.0), (5.0, 0.0), (5.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "room"}),
        ),
        openings=(
            NormOpening("o-9585ee57fe3e", "door", "w-8829e7c2d2cc", (2.5, 0.0), 0.9, 1.0, {"source_ref": "door"}),
        ),
        dimensions_m=(),
        normalization={
            "quantum_m": 0.0001,
            "source_units": "px",
            "source_unit_scale_m": 0.005,
            "translation_m": [1.0, 2.0],
            "y_axis": "flipped_from_raster",
            "source_height_px": 1800,
            "scale_m_per_px": 0.005,
        },
        frame=SourceFrame(kind="raster", unit_scale_m=0.005, y_down=True, height_px=1800, source_units="px"),
    )


def _png_bytes() -> bytes:
    image = Image.new("RGB", (2000, 1800), "white")
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def test_raster_overlay_is_deterministic_and_self_contained():
    geometry = _geometry()
    source = {
        "kind": "raster",
        "source_sha256": "sha256:" + "a" * 64,
        "image_bytes": _png_bytes(),
        "width_px": 2000,
        "height_px": 1800,
    }

    first = render_overlay(geometry, source)
    second = render_overlay(geometry, source)
    text = first.decode("utf-8")

    assert first == second
    assert 'viewBox="0 0 2000 1800"' in text
    assert 'href="data:image/png;base64,' in text
    assert '200,1400' in text
    assert '700,1400' in text
    assert "<script" not in text
    assert "xlink:" not in text
    assert "<!DOCTYPE" not in text


def test_dxf_overlay_uses_margin_and_inverted_source_coordinates():
    geometry = NormalizedGeometry(
        units="m",
        walls=(
            NormWall("w-b38b11821642", (0.0, 0.0), (0.0, 6.0), 1.0, {"source_ref": "west"}),
            NormWall("w-0df3b64861a5", (0.0, 6.0), (8.0, 6.0), 1.0, {"source_ref": "north"}),
        ),
        rooms=(),
        openings=(NormOpening("o-13a46a7d32db", "window", "w-0df3b64861a5", (2.0, 6.0), 1.2, 1.0, {"source_ref": "n1"}),),
        dimensions_m=(),
        normalization={
            "quantum_m": 0.0001,
            "source_units": "mm",
            "source_unit_scale_m": 0.001,
            "translation_m": [1.0, 2.0],
            "y_axis": "up",
            "source_height_px": None,
            "scale_m_per_px": None,
        },
        frame=SourceFrame(kind="dxf", unit_scale_m=0.001, y_down=False, height_px=None, source_units="mm"),
    )
    source = {
        "kind": "dxf",
        "source_sha256": "sha256:" + "b" * 64,
        "primitives": [
            {"type": "line", "start": [1000, 2000], "end": [1000, 8000]},
            {"type": "line", "start": [1000, 8000], "end": [9000, 8000]},
        ],
    }

    text = render_overlay(geometry, source).decode("utf-8")
    assert 'viewBox="0 0 8800 6800"' in text
    assert '400,6400' in text
    assert '2400,400' in text
    assert '"adapter":"dxf"' in text


def test_raster_overlay_uses_media_type_from_source():
    """m-4/M-5 (code+spatial review, 2026-08-10): overlay.py used to
    hardcode data:image/png regardless of the actual source format. The
    media type must come from the verified source bytes (via
    source["media_type"], as builder.py's _source_binding now derives it
    from the decoded PIL format), not be assumed.
    """
    geometry = _geometry()
    source = {
        "kind": "raster",
        "source_sha256": "sha256:" + "d" * 64,
        "image_bytes": _png_bytes(),
        "media_type": "image/jpeg",
        "width_px": 2000,
        "height_px": 1800,
    }

    text = render_overlay(geometry, source).decode("utf-8")

    assert 'href="data:image/jpeg;base64,' in text
    assert "data:image/png" not in text


def test_dxf_overlay_renders_rooms_and_doors_not_empty_placeholders():
    """M-4/M-11 (spatial+code review, 2026-08-10): the DXF renderer's
    #rooms and #doors groups used to be unconditional empty placeholders --
    4 of 11 Layer-A detections (2 rooms, 2 doors) never appeared in the
    overlay a human reviews at the §20 visual-evidence gate.
    """
    geometry = NormalizedGeometry(
        units="m",
        walls=(
            NormWall("w-a", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "s"}),
            NormWall("w-b", (0.0, 0.0), (0.0, 6.0), 1.0, {"source_ref": "n"}),
        ),
        rooms=(NormRoom("r-a", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "room"}),),
        openings=(NormOpening("o-a", "door", "w-a", (2.5, 0.0), 0.9, 1.0, {"source_ref": "door"}),),
        dimensions_m=(),
        normalization={
            "quantum_m": 0.0001,
            "source_units": "mm",
            "source_unit_scale_m": 0.001,
            "translation_m": [1.0, 2.0],
            "y_axis": "up",
            "source_height_px": None,
            "scale_m_per_px": None,
        },
        frame=SourceFrame(kind="dxf", unit_scale_m=0.001, y_down=False, height_px=None, source_units="mm"),
    )
    source = {
        "kind": "dxf",
        "source_sha256": "sha256:" + "e" * 64,
        "primitives": [
            {"type": "line", "start": [1000, 2000], "end": [9000, 2000]},
            {"type": "line", "start": [1000, 2000], "end": [1000, 8000]},
        ],
    }

    text = render_overlay(geometry, source).decode("utf-8")

    rooms_group = text[text.index('<g id="rooms">') : text.index('<g id="doors">')]
    doors_group = text[text.index('<g id="doors">') : text.index('<g id="windows">')]
    assert "<polygon" in rooms_group
    assert "<circle" in doors_group


def test_dxf_overlay_source_layer_is_independent_of_detections():
    """M-4 (spatial review, 2026-08-10): the DXF "source" layer used to be
    re-projected from the normalized walls' own provenance, so source and
    detections were coincident by construction and could never disagree --
    AC-14's alignment claim was unfalsifiable. Feeding a source primitive
    that genuinely differs from the normalized wall must produce visibly
    different coordinates in #source vs #walls.
    """
    geometry = NormalizedGeometry(
        units="m",
        walls=(NormWall("w-a", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "s"}),),
        rooms=(),
        openings=(),
        dimensions_m=(),
        normalization={
            "quantum_m": 0.0001,
            "source_units": "mm",
            "source_unit_scale_m": 0.001,
            "translation_m": [1.0, 2.0],
            "y_axis": "up",
            "source_height_px": None,
            "scale_m_per_px": None,
        },
        frame=SourceFrame(kind="dxf", unit_scale_m=0.001, y_down=False, height_px=None, source_units="mm"),
    )
    # Deliberately disagrees with the normalized wall (1000,2000)-(9000,2000).
    source = {
        "kind": "dxf",
        "source_sha256": "sha256:" + "f" * 64,
        "primitives": [{"type": "line", "start": [1000, 2000], "end": [5000, 2000]}],
    }

    text = render_overlay(geometry, source).decode("utf-8")

    source_group = text[text.index('<g id="source">') : text.index('<g id="walls">')]
    walls_group = text[text.index('<g id="walls">') : text.index('<g id="rooms">')]
    # The normalized wall inverse-transforms to (1000,2000)-(9000,2000)mm,
    # the source primitive is only (1000,2000)-(5000,2000)mm: same viewBox
    # (sized from the source primitives), but genuinely different spans.
    assert '<polyline points="200,200 4200,200"' in source_group  # short source primitive
    assert '<polyline points="200,200 8200,200"' in walls_group  # full normalized wall, disagrees


def test_overlay_ids_and_confidence_are_populated():
    """m-9 (spatial review, 2026-08-10): #ids/#confidence used to be
    unconditional empty placeholder groups in both renderers.
    """
    geometry = _geometry()
    source = {
        "kind": "raster",
        "source_sha256": "sha256:" + "a" * 64,
        "image_bytes": _png_bytes(),
        "media_type": "image/png",
        "width_px": 2000,
        "height_px": 1800,
    }

    text = render_overlay(geometry, source).decode("utf-8")

    ids_group = text[text.index('<g id="ids">') : text.index('<g id="confidence">')]
    confidence_group = text[text.index('<g id="confidence">') :]
    assert "w-b38b11821642" in ids_group
    assert "o-9585ee57fe3e" in ids_group
    assert "<text" in confidence_group


def test_hostile_label_escaped():
    geometry = _geometry()
    source = {
        "kind": "dxf",
        "source_sha256": "sha256:" + "c" * 64,
        "primitives": [
            {"type": "line", "start": [1000, 2000], "end": [1000, 8000]},
            {"type": "line", "start": [1000, 8000], "end": [9000, 8000]},
        ],
        "labels": ["dxf:Model/NOTES<script>alert(1)</script>#2F"],
    }

    text = render_overlay(geometry, source).decode("utf-8")

    assert "<script" not in text.lower()
    assert "&lt;script&gt;" in text
    assert "xlink:" not in text
    assert "<!DOCTYPE" not in text
