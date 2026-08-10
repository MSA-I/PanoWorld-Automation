from __future__ import annotations

import pytest

from pwa.floorplan.types import NormOpening, NormRoom, NormWall, NormalizedGeometry, SourceFrame
from pwa.floorplan.validate import validate


def _geometry(
    *,
    walls: tuple[NormWall, ...],
    rooms: tuple[NormRoom, ...],
    openings: tuple[NormOpening, ...] = (),
    dimensions: tuple[tuple[tuple[float, float], tuple[float, float], float], ...] = (),
) -> NormalizedGeometry:
    return NormalizedGeometry(
        units="m",
        walls=walls,
        rooms=rooms,
        openings=openings,
        dimensions_m=dimensions,
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


@pytest.mark.parametrize(
    ("geometry", "expected_codes"),
    [
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (4.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (4.0, 4.0), (0.0, 4.0), (4.0, 0.0)), 1.0, {"source_ref": "r1"}),),
            ),
            {"PARSE_SELF_INTERSECTING_POLYGON"},
            id="f-self-intersect",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (4.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (2.0, 0.0), (4.0, 0.0)), 1.0, {"source_ref": "r1"}),),
            ),
            {"PARSE_SELF_INTERSECTING_POLYGON"},
            id="f-zero-area",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (8.0, 6.0)), 1.0, {"source_ref": "r1"}),),
            ),
            {"PARSE_OPEN_POLYGON"},
            id="f-open-polygon-dup",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (0.0499, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
            ),
            {"PARSE_DEGENERATE_WALL"},
            id="f-degenerate-wall",
        ),
        pytest.param(
            _geometry(
                walls=(
                    NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),
                    NormWall("w2", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w2"}),
                ),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
            ),
            {"PARSE_DUPLICATE_ENTITY"},
            id="f-duplicate-wall",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(
                    NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),
                    NormRoom("r2", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r2"}),
                ),
            ),
            {"PARSE_DUPLICATE_ENTITY"},
            id="f-duplicate-room",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", None, (20.0, 20.0), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            {"PARSE_UNKNOWN_WALL_REF"},
            id="f-unknown-wall-ref",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", "missing-wall", (2.5, 0.0), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            {"PARSE_UNKNOWN_WALL_REF"},
            id="f-unknown-wall-index",
        ),
        pytest.param(
            _geometry(
                walls=(
                    NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),
                    NormWall("w2", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w2"}),
                ),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", None, (2.5, 0.0), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            {"PARSE_AMBIGUOUS_WALL_REF", "PARSE_DUPLICATE_ENTITY"},
            id="f-ambiguous-wall-ref",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", "w1", (2.5, 0.0201), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            {"PARSE_OPENING_OFF_WALL"},
            id="f-opening-off-wall",
        ),
        pytest.param(
            _geometry(
                walls=(
                    NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),
                    NormWall("w2", (8.0, 0.0), (8.0, 6.0), 1.0, {"source_ref": "w2"}),
                ),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", "w2", (2.5, 0.0), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            {"PARSE_OPENING_OFF_WALL"},
            id="f-opening-wrong-ref",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", "w1", (0.4498, 0.0), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            {"PARSE_OPENING_WIDTH_EXCEEDS_WALL"},
            id="f-opening-overhang",
        ),
        pytest.param(
            _geometry(
                walls=(
                    NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),
                    NormWall("w2", (0.0, 6.0), (8.0, 6.0), 1.0, {"source_ref": "w2"}),
                ),
                rooms=(
                    NormRoom("r1", ((0.0, 0.0), (5.0, 0.0), (5.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),
                    NormRoom("r2", ((4.0, 1.0), (9.0, 1.0), (9.0, 5.0), (4.0, 5.0)), 1.0, {"source_ref": "r2"}),
                ),
            ),
            {"PARSE_ROOM_BOUNDARY_UNMATCHED"},
            id="f-room-boundary-cross",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0801, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0801, 0.0), (8.0801, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                dimensions=(((0.0, 0.0), (8.0801, 0.0), 8.0),),
            ),
            {"PARSE_DIMENSION_INCONSISTENT"},
            id="f-dimension-bad",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 0.4999, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
            ),
            {"PARSE_LOW_CONFIDENCE"},
            id="f-low-confidence",
        ),
    ],
)
def test_validate_fixture_codes(geometry: NormalizedGeometry, expected_codes: set[str]):
    assert {finding.code for finding in validate(geometry)} == expected_codes


@pytest.mark.parametrize(
    ("geometry", "expected_codes"),
    [
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (0.05, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
            ),
            set(),
            id="b-wall-exact",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", "w1", (2.5, 0.02), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            set(),
            id="b-offset-exact",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", "w1", (0.45, 0.0), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            set(),
            id="b-span-exact",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                openings=(NormOpening("o1", "door", "w1", (0.4499, 0.0), 0.9, 1.0, {"source_ref": "o1"}),),
            ),
            set(),
            id="b-span-quantum",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.08, 0.0), 1.0, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.08, 0.0), (8.08, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
                dimensions=(((0.0, 0.0), (8.08, 0.0), 8.0),),
            ),
            set(),
            id="b-dimension-exact",
        ),
        pytest.param(
            _geometry(
                walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 0.5, {"source_ref": "w1"}),),
                rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 0.5, {"source_ref": "r1"}),),
            ),
            set(),
            id="b-confidence-half",
        ),
    ],
)
def test_validate_boundary_pass_cases(geometry: NormalizedGeometry, expected_codes: set[str]):
    assert {finding.code for finding in validate(geometry)} == expected_codes
