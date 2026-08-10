from __future__ import annotations

from pwa.floorplan.types import NormOpening, NormRoom, NormWall, NormalizedGeometry, SourceFrame
from pwa.floorplan.validate import seg_intersects_non_adjacent, seg_proper_cross, validate


def _geometry(
    *,
    walls: tuple[NormWall, ...],
    rooms: tuple[NormRoom, ...],
    openings: tuple[NormOpening, ...],
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


def test_clean_geometry_has_no_findings():
    geometry = _geometry(
        walls=(
            NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),
            NormWall("w2", (0.0, 0.0), (0.0, 6.0), 1.0, {"source_ref": "w2"}),
            NormWall("w3", (0.0, 6.0), (8.0, 6.0), 1.0, {"source_ref": "w3"}),
            NormWall("w4", (8.0, 0.0), (8.0, 6.0), 1.0, {"source_ref": "w4"}),
        ),
        rooms=(
            NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),
        ),
        openings=(
            NormOpening(
                "o1",
                "door",
                "w1",
                (2.5, 0.0),
                0.9,
                1.0,
                {"source_ref": "o1"},
            ),
        ),
        dimensions=((((0.0, 0.0), (8.0, 0.0), 8.0)),),
    )

    assert validate(geometry) == []


def test_polygon_crossing_and_zero_area_are_exact_codes():
    bowtie = _geometry(
        walls=(NormWall("w1", (0.0, 0.0), (4.0, 0.0), 1.0, {"source_ref": "w1"}),),
        rooms=(NormRoom("r1", ((0.0, 0.0), (4.0, 4.0), (0.0, 4.0), (4.0, 0.0)), 1.0, {"source_ref": "r1"}),),
        openings=(),
    )
    zero_area = _geometry(
        walls=(NormWall("w1", (0.0, 0.0), (4.0, 0.0), 1.0, {"source_ref": "w1"}),),
        rooms=(NormRoom("r1", ((0.0, 0.0), (2.0, 0.0), (4.0, 0.0)), 1.0, {"source_ref": "r1"}),),
        openings=(),
    )

    assert {finding.code for finding in validate(bowtie)} == {"PARSE_SELF_INTERSECTING_POLYGON"}
    assert {finding.code for finding in validate(zero_area)} == {"PARSE_SELF_INTERSECTING_POLYGON"}


def test_opening_binding_dimension_and_room_crossing_matrix():
    crossed = _geometry(
        walls=(
            NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),
            NormWall("w2", (0.0, 6.0), (8.0, 6.0), 1.0, {"source_ref": "w2"}),
        ),
        rooms=(
            NormRoom("r1", ((0.0, 0.0), (5.0, 0.0), (5.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),
            NormRoom("r2", ((4.0, 1.0), (9.0, 1.0), (9.0, 5.0), (4.0, 5.0)), 1.0, {"source_ref": "r2"}),
        ),
        openings=(
            NormOpening("o1", "door", "w1", (2.5, 0.0201), 0.9, 1.0, {"source_ref": "o1"}),
            NormOpening("o2", "door", "w1", (0.4498, 0.0), 0.9, 1.0, {"source_ref": "o2"}),
            NormOpening("o3", "door", "missing", (20.0, 20.0), 0.9, 1.0, {"source_ref": "o3"}),
        ),
        dimensions=((((0.0, 0.0), (8.0801, 0.0), 8.0)),),
    )

    codes = {finding.code for finding in validate(crossed)}
    assert "PARSE_ROOM_BOUNDARY_UNMATCHED" in codes
    assert "PARSE_OPENING_OFF_WALL" in codes
    assert "PARSE_OPENING_WIDTH_EXCEEDS_WALL" in codes
    assert "PARSE_UNKNOWN_WALL_REF" in codes
    assert "PARSE_DIMENSION_INCONSISTENT" in codes


def test_boundary_values_pass_exactly():
    geometry = _geometry(
        walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
        rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
        openings=(
            NormOpening("o1", "door", "w1", (2.5, 0.02), 0.9, 1.0, {"source_ref": "o1"}),
            NormOpening("o2", "door", "w1", (0.4499, 0.0), 0.9, 1.0, {"source_ref": "o2"}),
        ),
        dimensions=((((0.0, 0.0), (8.08, 0.0), 8.0)),),
    )

    assert validate(geometry) == []


def test_degenerate_duplicate_and_open_polygon_codes():
    geometry = _geometry(
        walls=(
            NormWall("w1", (0.0, 0.0), (0.0499, 0.0), 1.0, {"source_ref": "w1"}),
            NormWall("w2", (0.0, 0.0), (0.0499, 0.0), 1.0, {"source_ref": "w2"}),
        ),
        rooms=(
            NormRoom("r1", ((0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (3.0, 3.0)), 1.0, {"source_ref": "r1"}),
        ),
        openings=(),
    )

    codes = {finding.code for finding in validate(geometry)}
    assert "PARSE_DEGENERATE_WALL" in codes
    assert "PARSE_DUPLICATE_ENTITY" in codes
    assert "PARSE_OPEN_POLYGON" in codes


def test_ambiguous_wall_ref_and_low_confidence_boundary():
    geometry = _geometry(
        walls=(
            NormWall("w1", (0.0, 0.0), (4.0, 0.0), 0.4999, {"source_ref": "w1"}),
            NormWall("w2", (0.0, 0.0), (4.0, 0.0), 0.5, {"source_ref": "w2"}),
        ),
        rooms=(
            NormRoom("r1", ((0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0)), 0.5, {"source_ref": "r1"}),
        ),
        openings=(
            NormOpening("o1", "door", None, (2.0, 0.0), 0.9, 1.0, {"source_ref": "o1"}),
        ),
    )

    codes = [finding.code for finding in validate(geometry)]
    assert "PARSE_AMBIGUOUS_WALL_REF" in codes
    assert codes.count("PARSE_LOW_CONFIDENCE") == 1


def test_seg_intersects_non_adjacent_detects_collinear_overlap_and_both_side_touches():
    """M-3 (spatial review, 2026-08-10): seg_proper_cross folded zero into
    the "not greater than zero" branch, so a collinear overlap and a
    one-sided vertex-on-edge touch (from the "right") were never detected.
    §8.2 requires "no non-adjacent segment intersection", not merely "no
    proper crossing". seg_intersects_non_adjacent is the full predicate used
    by _validate_room for that invariant.
    """
    # Collinear overlap: [(0,0)-(6,0)] vs [(1,0)-(4,0)] overlap on x in [1,4].
    assert seg_intersects_non_adjacent((0, 0), (6, 0), (1, 0), (4, 0)) is True
    # Collinear but only touching at a single shared point: not an overlap.
    assert seg_intersects_non_adjacent((0, 0), (4, 0), (4, 0), (8, 0)) is False
    # Collinear but disjoint (no shared point at all).
    assert seg_intersects_non_adjacent((0, 0), (2, 0), (4, 0), (6, 0)) is False
    # T-touch: q1 lands exactly on p1-p2, approaching from the "left" (q2 above).
    assert seg_intersects_non_adjacent((0, 0), (10, 0), (5, 0), (5, 5)) is True
    # T-touch: same touch point, approaching from the "right" (q2 below) --
    # this is the side seg_proper_cross's `>0` fold used to miss.
    assert seg_intersects_non_adjacent((0, 0), (10, 0), (5, 0), (5, -5)) is True
    # A proper crossing must still be detected (regression guard).
    assert seg_intersects_non_adjacent((0, 0), (4, 4), (0, 4), (4, 0)) is True
    # Genuinely disjoint, non-collinear segments must not be flagged.
    assert seg_intersects_non_adjacent((0, 0), (1, 0), (5, 5), (6, 6)) is False


def test_seg_proper_cross_is_unaffected_by_the_stricter_predicate():
    """_room_pair_warning (cross-room boundary warning) deliberately keeps
    using the original seg_proper_cross, not seg_intersects_non_adjacent:
    two different rooms sharing a wall produce an exactly-coincident
    collinear edge pair, which is the normal adjacent-rooms case and must
    not warn. Only a genuine proper crossing should.
    """
    assert seg_proper_cross((0, 0), (6, 0), (1, 0), (4, 0)) is False
    assert seg_proper_cross((0, 0), (4, 4), (0, 4), (4, 0)) is True


def test_validate_detects_room_self_intersection_via_collinear_overlap():
    """M-3 (spatial review, 2026-08-10) at the validate() level: a room
    polygon with a non-adjacent collinear-overlapping edge pair -- and a
    vertex of one edge lying strictly inside another -- is not simple, but
    used to pass with zero findings."""
    geometry = _geometry(
        walls=(NormWall("w1", (0.0, 0.0), (6.0, 0.0), 1.0, {"source_ref": "w1"}),),
        rooms=(
            NormRoom(
                "r1",
                ((0.0, 0.0), (6.0, 0.0), (6.0, 2.0), (3.0, 2.0), (3.0, 5.0), (4.5, 5.0), (4.5, 2.0), (0.0, 2.0)),
                1.0,
                {"source_ref": "r1"},
            ),
        ),
        openings=(),
    )

    codes = {finding.code for finding in validate(geometry)}
    assert "PARSE_SELF_INTERSECTING_POLYGON" in codes


def test_validate_rejects_duplicate_opening_geometry():
    """C-1 (spatial review, 2026-08-10): validate() checked duplicate
    geometry for walls and rooms but not openings. Two coincident openings
    collided on `id` with zero findings, status complete, CLI 0,
    G1-eligible. §7 requires duplicate geometry to fail (no suffix/merge).
    """
    geometry = _geometry(
        walls=(NormWall("w1", (0.0, 0.0), (8.0, 0.0), 1.0, {"source_ref": "w1"}),),
        rooms=(NormRoom("r1", ((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), 1.0, {"source_ref": "r1"}),),
        openings=(
            NormOpening("o1", "door", "w1", (2.5, 0.0), 0.9, 1.0, {"source_ref": "o1"}),
            NormOpening("o1", "door", "w1", (2.5, 0.0), 0.9, 1.0, {"source_ref": "o1-dup"}),
        ),
    )

    codes = [finding.code for finding in validate(geometry)]
    assert codes.count("PARSE_DUPLICATE_ENTITY") == 1


def test_validate_rejects_opening_whose_span_is_not_collinear_with_the_matched_wall():
    """M-2 (spatial review, 2026-08-10): opening<->wall matching used to
    test only the opening's centre point. A door line drawn perpendicular
    to a wall (only its centre landing on the wall) used to bind at
    confidence 1.0 with zero findings. §6 requires the opening *line* to be
    collinear with exactly one wall within tolerance; zero/multiple matches
    must fail.
    """
    geometry = _geometry(
        walls=(NormWall("w1", (0.0, 0.0), (5.0, 0.0), 1.0, {"source_ref": "w1"}),),
        rooms=(NormRoom("r1", ((0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (0.0, 4.0)), 1.0, {"source_ref": "r1"}),),
        openings=(
            NormOpening(
                "o1",
                "door",
                "w1",
                (2.5, 0.0),
                0.9,
                1.0,
                {"source_ref": "o1", "source_kind": "dxf"},
                span_m=((2.5, -0.45), (2.5, 0.45)),
            ),
        ),
    )

    codes = {finding.code for finding in validate(geometry)}
    assert "PARSE_OPENING_OFF_WALL" in codes
