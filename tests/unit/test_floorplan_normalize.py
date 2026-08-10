from __future__ import annotations

import pytest

from pwa.floorplan.findings import FloorplanError
from pwa.floorplan.normalize import canonical_projection, normalize
from pwa.floorplan.types import RawGeometry, RawOpening, RawRoom, RawWall, SourceFrame


def _frame() -> SourceFrame:
    return SourceFrame(
        kind="dxf",
        unit_scale_m=0.001,
        y_down=False,
        height_px=None,
        source_units="mm",
    )


def _layer_a_1() -> RawGeometry:
    return RawGeometry(
        frame=_frame(),
        walls=(
            RawWall(0, "dxf:modelspace/PWA-WALL#01", (1000, 2000), (9000, 2000)),
            RawWall(1, "dxf:modelspace/PWA-WALL#02", (9000, 2000), (9000, 8000)),
            RawWall(2, "dxf:modelspace/PWA-WALL#03", (1000, 8000), (9000, 8000)),
            RawWall(3, "dxf:modelspace/PWA-WALL#04", (1000, 2000), (1000, 8000)),
            RawWall(4, "dxf:modelspace/PWA-WALL#05", (6000, 2000), (6000, 8000)),
        ),
        rooms=(
            RawRoom(0, "dxf:modelspace/PWA-ROOM#11", ((1000, 2000), (6000, 2000), (6000, 8000), (1000, 8000))),
            RawRoom(1, "dxf:modelspace/PWA-ROOM#12", ((6000, 2000), (9000, 2000), (9000, 8000), (6000, 8000))),
        ),
        openings=(
            RawOpening(
                0,
                "dxf:modelspace/PWA-WINDOW#21",
                "window",
                (3000, 8000),
                1.2,
                ((2400, 8000), (3600, 8000)),
                None,
            ),
            RawOpening(
                1,
                "dxf:modelspace/PWA-DOOR#22",
                "door",
                (3500, 2000),
                0.9,
                ((3050, 2000), (3950, 2000)),
                None,
            ),
            RawOpening(
                2,
                "dxf:modelspace/PWA-DOOR#23",
                "door",
                (6000, 5000),
                0.9,
                ((6000, 4550), (6000, 5450)),
                None,
            ),
            RawOpening(
                3,
                "dxf:modelspace/PWA-WINDOW#24",
                "window",
                (9000, 6500),
                1.2,
                ((9000, 5900), (9000, 7100)),
                None,
            ),
        ),
        dimensions=(),
        scanned_entities=11,
        unmapped=(),
    )


def test_layer_a_1_normalization_matches_approved_ids_and_projection():
    geometry = normalize(_layer_a_1())

    assert [wall.id for wall in geometry.walls] == [
        "w-b38b11821642",
        "w-8829e7c2d2cc",
        "w-0df3b64861a5",
        "w-6e35a882252a",
        "w-5e931339aa8f",
    ]
    assert [room.id for room in geometry.rooms] == [
        "r-ab354c288e8a",
        "r-bea085b2f952",
    ]
    assert [opening.id for opening in geometry.openings] == [
        "o-13a46a7d32db",
        "o-9585ee57fe3e",
        "o-3a101c4fd203",
        "o-378d46ae40f1",
    ]
    assert geometry.normalization == {
        "quantum_m": 0.0001,
        "source_units": "mm",
        "source_unit_scale_m": 0.001,
        "translation_m": [1.0, 2.0],
        "y_axis": "up",
        "source_height_px": None,
        "scale_m_per_px": None,
    }
    assert canonical_projection(geometry) == {
        "units": "m",
        "rooms": [
            [[0.0, 0.0], [5.0, 0.0], [5.0, 6.0], [0.0, 6.0]],
            [[5.0, 0.0], [8.0, 0.0], [8.0, 6.0], [5.0, 6.0]],
        ],
        "walls": [
            [[0.0, 0.0], [0.0, 6.0]],
            [[0.0, 0.0], [8.0, 0.0]],
            [[0.0, 6.0], [8.0, 6.0]],
            [[5.0, 0.0], [5.0, 6.0]],
            [[8.0, 0.0], [8.0, 6.0]],
        ],
        "openings": [
            ["window", "w-0df3b64861a5", [2.0, 6.0], 1.2],
            ["door", "w-8829e7c2d2cc", [2.5, 0.0], 0.9],
            ["door", "w-6e35a882252a", [5.0, 3.0], 0.9],
            ["window", "w-5e931339aa8f", [8.0, 4.5], 1.2],
        ],
    }


def test_reordered_input_keeps_same_ids_and_projection():
    source = _layer_a_1()
    shuffled = RawGeometry(
        frame=source.frame,
        walls=tuple(reversed(source.walls)),
        rooms=tuple(reversed(source.rooms)),
        openings=(source.openings[2], source.openings[0], source.openings[3], source.openings[1]),
        dimensions=source.dimensions,
        scanned_entities=source.scanned_entities,
        unmapped=source.unmapped,
    )

    original = normalize(source)
    reordered = normalize(shuffled)

    assert canonical_projection(reordered) == canonical_projection(original)
    assert [wall.id for wall in reordered.walls] == [wall.id for wall in original.walls]
    assert [room.id for room in reordered.rooms] == [room.id for room in original.rooms]
    assert [opening.id for opening in reordered.openings] == [opening.id for opening in original.openings]


def test_anchor_moves_only_with_wall_minimum_and_reuses_prior_geometry_ids():
    source = _layer_a_1()
    moved = RawGeometry(
        frame=source.frame,
        walls=source.walls + (RawWall(5, "dxf:modelspace/PWA-WALL#06", (0, 2000), (0, 8000)),),
        rooms=source.rooms,
        openings=source.openings,
        dimensions=source.dimensions,
        scanned_entities=source.scanned_entities + 1,
        unmapped=source.unmapped,
    )

    geometry = normalize(moved)

    assert geometry.normalization["translation_m"] == [0.0, 2.0]
    assert geometry.walls[0].id == "w-b38b11821642"
    assert geometry.walls[4].id == "w-ff541ff1603d"
    assert geometry.walls[5].id == "w-ac11489133c8"
    assert geometry.openings[2].id == "o-da9fe0362785"


def test_negative_zero_is_emitted_as_zero():
    source = RawGeometry(
        frame=SourceFrame(kind="raster", unit_scale_m=0.005, y_down=True, height_px=100, source_units="px"),
        walls=(RawWall(0, "annotation:walls[0]", (10, 90), (10, 10)),),
        rooms=(RawRoom(0, "annotation:rooms[0]", ((10, 90), (30, 90), (30, 10), (10, 10))),),
        openings=(),
        dimensions=(),
        scanned_entities=2,
        unmapped=(),
    )

    geometry = normalize(source)
    assert geometry.walls[0].start == (0.0, 0.0)
    assert geometry.rooms[0].polygon[0] == (0.0, 0.0)


def test_half_even_quantization_hits_approved_boundaries():
    source = RawGeometry(
        frame=SourceFrame(kind="dxf", unit_scale_m=1.0, y_down=False, height_px=None, source_units="m"),
        walls=(RawWall(0, "dxf:modelspace/PWA-WALL#01", (0.00005, 0.0), (0.00015, 1.0)),),
        rooms=(RawRoom(0, "dxf:modelspace/PWA-ROOM#11", ((0.00005, 0.0), (1.00015, 0.0), (1.00015, 1.0))),),
        openings=(),
        dimensions=(),
        scanned_entities=2,
        unmapped=(),
    )

    geometry = normalize(source)

    assert geometry.walls[0].start[0] == 0.0
    assert geometry.walls[0].end[0] == 0.0002


def test_dxf_opening_span_stores_normalized_span_m():
    """A DXF opening's span is normalized and threaded through as
    NormOpening.span_m so validate() can re-check §6 collinearity without
    re-deriving metric coordinates from raw provenance."""
    source = _layer_a_1()

    geometry = normalize(source)

    door = geometry.openings[1]  # PWA-DOOR#22, span (3050,2000)-(3950,2000) mm
    assert door.type == "door"
    # translation_m == [1.0, 2.0] for this fixture: 3.05 - 1.0 = 2.05, 3.95 - 1.0 = 2.95
    assert door.span_m == ((2.05, 0.0), (2.95, 0.0))


def test_resolve_wall_id_rejects_span_not_collinear_with_the_only_nearby_wall():
    """M-2 (spatial review, 2026-08-10): a door whose centre lands on a wall
    but whose span is perpendicular to it must not silently resolve -- the
    opening becomes PENDING (deferred to validate()'s re-check, which must
    also reject it) instead of binding at confidence 1.0.
    """
    source = RawGeometry(
        frame=_frame(),
        walls=(RawWall(0, "dxf:modelspace/PWA-WALL#01", (0, 0), (5000, 0)),),
        rooms=(RawRoom(0, "dxf:modelspace/PWA-ROOM#11", ((0, 0), (5000, 0), (5000, 4000), (0, 4000))),),
        openings=(
            RawOpening(0, "dxf:modelspace/PWA-DOOR#01", "door", (2500, 0), 0.9, ((2500, -450), (2500, 450)), None),
        ),
        dimensions=(),
        scanned_entities=6,
        unmapped=(),
    )

    geometry = normalize(source)

    assert geometry.openings[0].wall_id == "__dxf_probe__"


def test_resolve_wall_id_multi_match_raises_ambiguous_not_unknown():
    """m-7 (spatial review, 2026-08-10): _resolve_wall_id folded the
    zero-match and multi-match cases into a single PARSE_UNKNOWN_WALL_REF.
    §6/§11 require PARSE_AMBIGUOUS_WALL_REF for the multi-match case.
    """
    from pwa.floorplan.normalize import _resolve_wall_id
    from pwa.floorplan.types import NormWall

    walls = (
        NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),
        NormWall("w2", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w2"}),
    )

    with pytest.raises(FloorplanError) as exc:
        _resolve_wall_id(walls, (2.5, 0.0))
    assert exc.value.finding.code == "PARSE_AMBIGUOUS_WALL_REF"

    with pytest.raises(FloorplanError) as exc:
        _resolve_wall_id(walls, (20.0, 20.0))
    assert exc.value.finding.code == "PARSE_UNKNOWN_WALL_REF"


def test_normalize_rejects_coordinates_exceeding_bounds_only_after_translation():
    """m-8 (spatial review, 2026-08-10): MAX_COORDINATE_MAGNITUDE_M was only
    checked pre-translation. Geometry whose individual endpoints are each
    within bounds can still land far outside the bound once translated
    relative to the anchor (e.g. x in [-99000, 99000] -> translated span up
    to 198000).
    """
    from pwa.floorplan.config import MAX_COORDINATE_MAGNITUDE_M

    assert 99_000 <= MAX_COORDINATE_MAGNITUDE_M
    source = RawGeometry(
        frame=SourceFrame(kind="dxf", unit_scale_m=1.0, y_down=False, height_px=None, source_units="m"),
        walls=(
            RawWall(0, "dxf:modelspace/PWA-WALL#01", (-99_000, 0), (99_000, 0)),
            RawWall(1, "dxf:modelspace/PWA-WALL#02", (-99_000, 0), (-99_000, 10)),
        ),
        rooms=(RawRoom(0, "dxf:modelspace/PWA-ROOM#11", ((-99_000, 0), (99_000, 0), (99_000, 10), (-99_000, 10))),),
        openings=(),
        dimensions=(),
        scanned_entities=3,
        unmapped=(),
    )

    with pytest.raises(FloorplanError) as exc:
        normalize(source)
    assert exc.value.finding.code == "PARSE_RESOURCE_LIMIT"
