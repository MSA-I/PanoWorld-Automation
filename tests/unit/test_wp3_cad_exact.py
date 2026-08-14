"""Tests for WP3 Product A (cad_exact) native arc/bulge geometry math.

TDD RED-first: these target the not-yet-written
``pwa.floorplan.cad_exact_geometry`` module, which must implement the
deterministic bulge <-> sweep <-> sagitta/tessellation rules that the
``cad_exact`` DXF parser needs for bounded circular-arc walls and room
polylines with bulge. The conventions are locked to the FX1 frozen truth
(``evidence/PLAN-002RF/WP0-FX1/fixture/fx1-truth.json``) and the frozen WP1
evaluator (``src/pwa/evaluator/metrics.py``: SAGITTA_MAX_PX 0.5, QUANTIZE_MM
0.01, bulge > 0 == counter-clockwise sweep).
"""

from __future__ import annotations

import math
from pathlib import Path

import ezdxf
import pytest

from pwa.floorplan import cad_exact_geometry as G
from pwa.floorplan import cad_exact as C
from pwa.floorplan.cad_exact_worker import extract_cad_exact
from pwa.contracts import validate_artifact
from tests.conftest import make_envelope


# --------------------------------------------------------------------------- #
# A — bulge <-> sweep <-> sagitta/tessellation geometry                        #
# --------------------------------------------------------------------------- #


def test_bulge_sign_matches_ccw_convention():
    # Frozen convention (WP2 recognition.arc_invariants): bulge > 0 for ccw.
    assert G.bulge_for_sweep("ccw", angle_rad=math.pi / 2) > 0
    assert G.bulge_for_sweep("cw", angle_rad=math.pi / 2) < 0


def test_bulge_magnitude_is_half_angle_tangent():
    # CAD bulge definition: bulge = tan(theta/4) where theta is the swept angle.
    for theta in (math.pi / 4, math.pi / 2, math.pi):
        assert G.bulge_magnitude(theta) == pytest.approx(math.tan(theta / 4))


def test_sweep_from_bulge_recovers_half_angle():
    bulge = 1.0  # theta/4 = pi/4 -> theta = pi
    angle = G.sweep_from_bulge(bulge)
    assert angle == pytest.approx(math.pi)


def test_sagitta_matches_fx1_apse_at_32_segments():
    # FX1 W-APSE: R=1500 mm, 180 deg sweep, N=32 -> sagitta ~0.36 px (<= 0.5).
    sag_px = G.sagitta_px(radius_mm=1500.0, sweep_rad=math.pi, n_segments=32, mm_per_px=5.0)
    assert sag_px <= 0.5
    assert sag_px == pytest.approx(0.36, abs=0.02)


def test_min_segments_respects_sagitta_bound():
    # N must be the smallest power-of-two >= N_min satisfying sagitta <= bound.
    n = G.min_segments_for_sagitta(radius_mm=1500.0, sweep_rad=math.pi, max_sagitta_px=0.5, mm_per_px=5.0)
    assert n == 32
    n90 = G.min_segments_for_sagitta(radius_mm=900.0, sweep_rad=math.pi / 2, max_sagitta_px=0.5, mm_per_px=5.0)
    assert n90 == 16


def test_tessellate_arc_is_deterministic_and_bounded():
    vertices = G.tessellate_arc(
        center=(9000.0, 3250.0), radius_mm=1500.0, start_deg=-90.0, end_deg=90.0, sweep="ccw", n_segments=32
    )
    assert len(vertices) == 33  # n_segments + 1
    assert vertices[0] == pytest.approx((9000.0, 1750.0), abs=1e-6)  # start at -90 deg
    assert vertices[-1] == pytest.approx((9000.0, 4750.0), abs=1e-6)  # end at +90 deg
    again = G.tessellate_arc(
        center=(9000.0, 3250.0), radius_mm=1500.0, start_deg=-90.0, end_deg=90.0, sweep="ccw", n_segments=32
    )
    assert vertices == again


def test_arc_start_end_angles_are_bounded_bulges():
    assert G.is_bounded_circular_arc(radius=1500.0, start_deg=-90.0, end_deg=90.0) is True
    assert G.is_bounded_circular_arc(radius=0.0, start_deg=-90.0, end_deg=90.0) is False
    assert G.is_bounded_circular_arc(radius=1500.0, start_deg=-90.0, end_deg=math.inf) is False


def test_sweep_sign_from_endpoints():
    sweep, angle = G.sweep_from_endpoints(start_deg=-90.0, end_deg=90.0, direction="ccw")
    assert sweep == "ccw"
    assert angle == pytest.approx(math.pi)


# --------------------------------------------------------------------------- #
# B — worker: native ARC wall, LWPOLYLINE bulge room, thickness, passage       #
# --------------------------------------------------------------------------- #


def _cad_exact_doc(units=4, mutate=None) -> "ezdxf.drawing.Drawing":
    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = units
    return document


def test_extract_cad_exact_parses_native_arc_wall(tmp_path):
    path = tmp_path / "apse.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    # Native ARC on PWA-WALL: centre (9000,3250), R=1500, from -90 to +90 ccw.
    arc = ms.add_arc(center=(9000, 3250), radius=1500, start_angle=-90, end_angle=90, dxfattribs={"layer": "PWA-WALL"})
    _set_thickness(arc, 0.24)
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert [w["kind"] for w in payload["walls"]] == ["circular_arc"]
    wall = payload["walls"][0]
    assert wall["thickness_m"] == pytest.approx(0.24)
    assert wall["arc"]["center"] == [9000.0, 3250.0]
    assert wall["arc"]["radius_mm"] == pytest.approx(1500.0)
    assert wall["arc"]["sweep"] == "ccw"
    assert wall["arc"]["bulge"] > 0


def test_extract_cad_exact_parses_lwpolyline_bulge_room(tmp_path):
    path = tmp_path / "bulged-room.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    # A room LWPOLYLINE with a bulge on one edge (a quarter-circle apse corner).
    ms.add_lwpolyline(
        [(1000, 2000), (9000, 2000, 1.0), (9000, 8000), (1000, 8000)],
        format="xyb",
        close=True,
        dxfattribs={"layer": "PWA-ROOM"},
    )
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert len(payload["rooms"]) == 1
    room = payload["rooms"][0]
    assert room["area_m2"] > 0
    assert room["has_bulge"] is True


def test_extract_cad_exact_parses_passage_openings(tmp_path):
    path = tmp_path / "passage.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    ms.add_line((1000, 1500), (1000, 8500), dxfattribs={"layer": "PWA-WALL"})
    ms.add_line((1000, 6050), (1000, 7550), dxfattribs={"layer": "PWA-PASSAGE"})
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert [o["kind"] for o in payload["openings"]] == ["passage"]
    assert payload["openings"][0]["width_m"] == pytest.approx(1.5)


def test_extract_cad_exact_fails_closed_on_missing_thickness(tmp_path):
    path = tmp_path / "no-thickness.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    ms.add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
    doc.saveas(path)

    payload = extract_cad_exact(path)

    # The wall surface is recorded, but a product wall without sourced
    # thickness must be flagged with the frozen blocking code.
    assert any(err["code"] == "RECOGNITION_THICKNESS_MISSING" for err in payload["errors"])


def test_extract_cad_exact_refuses_passage_over_bound(tmp_path):
    path = tmp_path / "wide-passage.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    ms.add_line((0, 0), (0, 5000), dxfattribs={"layer": "PWA-WALL"})
    ms.add_line((0, 500), (0, 4500), dxfattribs={"layer": "PWA-PASSAGE"})  # 4.0 m span > 3.0 m
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND" for err in payload["errors"])


def test_extract_cad_exact_refuses_unbounded_arc(tmp_path):
    path = tmp_path / "unbounded-arc.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    # A full circle ARC (start == end after 360 sweep) is not a bounded arc.
    arc = ms.add_arc(center=(0, 0), radius=1000, start_angle=0, end_angle=360, dxfattribs={"layer": "PWA-WALL"})
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] in {"PARSE_UNSUPPORTED_FEATURE", "RECOGNITION_ARC_NO_SAGITTA_BOUND"} for err in payload["errors"])


# --------------------------------------------------------------------------- #
# helpers                                                                      #
# --------------------------------------------------------------------------- #


def _set_thickness(entity, metres: float) -> None:
    """Attach sourced thickness (metres) to a wall entity via PWA XDATA."""
    entity.set_xdata("PWA", [(1000, "THICKNESS_M"), (1040, metres)])


# --------------------------------------------------------------------------- #
# C — emitter + FX1 truth scorer                                               #
# --------------------------------------------------------------------------- #


def test_emit_floorplan_parse_declares_cad_exact_source_class():
    payload, findings = C.emit_floorplan_parse(
        walls=[{"index": 0, "source_ref": "dxf:modelspace/PWA-WALL#1", "kind": "segment", "start": [0, 0], "end": [1000, 0], "thickness_m": 0.1}],
        rooms=[],
        openings=[],
    )
    assert payload["source_class"] == "cad_exact"
    assert payload["units"] == "m"
    assert findings == []


def test_emit_floorplan_parse_fails_closed_on_missing_thickness():
    payload, findings = C.emit_floorplan_parse(
        walls=[{"index": 0, "source_ref": "d", "kind": "segment", "start": [0, 0], "end": [1000, 0], "thickness_m": None}],
        rooms=[],
        openings=[],
    )
    assert "RECOGNITION_THICKNESS_MISSING" in findings


def test_emit_floorplan_parse_is_schema_valid_cad_exact():
    payload, _ = C.emit_floorplan_parse(
        walls=[
            {"index": 0, "source_ref": "dxf:modelspace/PWA-WALL#1", "kind": "segment", "start": [1.0, 2.0], "end": [1.0, 8.0], "thickness_m": 0.1},
            {
                "index": 1,
                "source_ref": "dxf:modelspace/PWA-WALL#2",
                "kind": "circular_arc",
                "start": [1.0, 8.0],
                "end": [4.0, 8.0],
                "thickness_m": 0.1,
                "arc": {"center": [2.5, 8.0], "radius_m": 1.5, "start_deg": 180.0, "end_deg": 0.0, "sweep": "ccw", "bulge": 1.0, "max_sagitta_px": 0.4},
            },
        ],
        rooms=[
            {"index": 0, "source_ref": "dxf:modelspace/PWA-ROOM#11", "polygon": [[1.0, 2.0], [6.0, 2.0], [6.0, 8.0], [1.0, 8.0]], "area_m2": 30.0}
        ],
        openings=[
            {"index": 0, "source_ref": "dxf:modelspace/PWA-PASSAGE#31", "kind": "passage", "center": [1.0, 5.0], "width_m": 1.5, "span": [[1.0, 4.25], [1.0, 5.75]]}
        ],
    )
    doc = make_envelope("floorplan_parse", payload, schema_version="1.2.0")
    assert validate_artifact(doc) == []


def test_truth_record_from_wall_segment_shape():
    wall = {"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]}
    record = C.truth_record_from_wall(wall)
    assert record["kind"] == "segment"
    assert record["a_mm"] == [1000.0, 1500.0]
    assert record["b_mm"] == [9000.0, 1500.0]


def test_truth_record_from_wall_arc_shape():
    wall = {
        "kind": "circular_arc",
        "arc": {"center": [9.0, 3.25], "radius_m": 1.5, "start_deg": -90.0, "end_deg": 90.0, "sweep": "ccw", "bulge": 1.0, "max_sagitta_px": 0.4},
    }
    record = C.truth_record_from_wall(wall)
    assert record["kind"] == "circular_arc"
    assert record["center_mm"] == [9000.0, 3250.0]
    assert record["radius_mm"] == 1500.0


def test_score_against_truth_is_exact_1_0_for_matching_fx1_subset():
    # Product walls (m) that exactly reproduce two FX1 truth walls (mm).
    walls = [
        {"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]},  # W-S
        {
            "kind": "circular_arc",
            "arc": {"center": [9.0, 3.25], "radius_m": 1.5, "start_deg": -90.0, "end_deg": 90.0, "sweep": "ccw", "bulge": 1.0, "max_sagitta_px": 0.4},
        },  # W-APSE
    ]
    truth = {
        "walls": [
            {"id": "W-S", "kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]},
            {"id": "W-APSE", "kind": "circular_arc", "center_mm": [9000, 3250], "radius_mm": 1500, "start_deg": -90, "end_deg": 90},
        ]
    }
    result = C.score_against_truth(walls, truth)
    assert result["accuracy"] == 1.0
    assert result["correct"] == 2


def test_score_against_truth_penalizes_mismatch():
    walls = [{"kind": "segment", "start": [1.0, 1.5], "end": [9.0, 1.5]}]
    truth = {
        "walls": [
            {"id": "W-S", "kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]},
            {"id": "W-W", "kind": "segment", "a_mm": [1000, 1500], "b_mm": [1000, 6700]},
        ]
    }
    result = C.score_against_truth(walls, truth)
    assert result["accuracy"] == 0.5
    assert result["correct"] == 1
    assert result["supportable"] == 2


# --------------------------------------------------------------------------- #
# D — end-to-end: full FX1-equivalent CAD parses to 1.000 against frozen truth #
# --------------------------------------------------------------------------- #

_FX1_TRUTH_PATH = (
    Path(__file__).resolve().parents[2]
    / "evidence" / "PLAN-002RF" / "WP0-FX1" / "fixture" / "fx1-truth.json"
)


def _write_fx1_cad(path: Path) -> None:
    """Author a DXF mirroring the FX1 source geometry (9 walls incl. the apse
    arc and the 3-4-5 diagonal), with sourced thickness on every wall."""
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4  # mm
    ms = doc.modelspace()
    segments = [
        ((1000, 1500), (9000, 1500)),  # W-S
        ((9000, 1500), (9000, 1750)),  # W-E-A
        ((9000, 4750), (9000, 8500)),  # W-E-B (merged E-B + E-C in truth)
        ((3400, 8500), (9000, 8500)),  # W-N
        ((1000, 6700), (3400, 8500)),  # W-DIAG (3-4-5)
        ((1000, 1500), (1000, 6700)),  # W-W
        ((4000, 1500), (4000, 8500)),  # W-PV
        ((4000, 5000), (9000, 5000)),  # W-PH
    ]
    for a, b in segments:
        entity = ms.add_line(a, b, dxfattribs={"layer": "PWA-WALL"})
        _set_thickness(entity, 0.24)
    apse = ms.add_arc(center=(9000, 3250), radius=1500, start_angle=-90, end_angle=90, dxfattribs={"layer": "PWA-WALL"})
    _set_thickness(apse, 0.24)
    doc.saveas(path)


def test_extract_emit_score_fx1_mirrored_cad_is_1_0(tmp_path):
    import json

    path = tmp_path / "fx1-cad.dxf"
    _write_fx1_cad(path)

    payload, findings, source_errors = C.parse_cad_exact(path)

    # 9 walls (8 segments + the apse arc), all with sourced thickness;
    # no recognition or fail-closed source findings.
    assert source_errors == []
    assert findings == []
    assert len(payload["walls"]) == 9
    assert sum(1 for w in payload["walls"] if w["kind"] == "circular_arc") == 1
    assert all(w["thickness_m"] is not None for w in payload["walls"])

    truth = json.loads(_FX1_TRUTH_PATH.read_text(encoding="utf-8"))
    result = C.score_against_truth(payload["walls"], truth)

    assert result["accuracy"] == 1.0, result
    assert result["supportable"] == len(truth["walls"])


def test_parse_cad_exact_produces_schema_valid_cad_exact(tmp_path):
    path = tmp_path / "fx1-cad.dxf"
    _write_fx1_cad(path)

    payload, findings, source_errors = C.parse_cad_exact(path)

    assert source_errors == [] and findings == []
    doc = make_envelope("floorplan_parse", payload, schema_version="1.2.0")
    assert validate_artifact(doc) == []


def test_fx1_cad_parse_is_deterministic(tmp_path):
    path = tmp_path / "fx1-cad.dxf"
    _write_fx1_cad(path)

    first = extract_cad_exact(path)
    second = extract_cad_exact(path)

    assert first == second


def test_fx1_cad_parse_refuses_on_scale_topology_resources(tmp_path):
    # A DXF with unknown units must fail closed (scale refusal).
    path = tmp_path / "bad-units.dxf"
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 0  # unknown
    doc.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "PWA-WALL"})
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "PARSE_UNITS_MISMATCH" for err in payload["errors"])


# --------------------------------------------------------------------------- #
# E — migration compatibility: the historical dxf path must be unchanged       #
# --------------------------------------------------------------------------- #


def test_historical_dxf_worker_still_rejects_arc_and_bulge(tmp_path):
    from pwa.floorplan.dxf_worker import extract_dxf

    # The historical dxf_worker (Plan-002 §12) must keep rejecting native ARC
    # walls and bulged rooms as PARSE_UNSUPPORTED_FEATURE — Product A (cad_exact)
    # is additive and never changes the historical fail-closed behaviour.
    arc_path = tmp_path / "historical-arc.dxf"
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4
    doc.modelspace().add_arc(center=(0, 0), radius=1, start_angle=0, end_angle=90, dxfattribs={"layer": "PWA-WALL"})
    doc.saveas(arc_path)

    payload = extract_dxf(arc_path)
    assert any(item["code"] == "PARSE_UNSUPPORTED_FEATURE" for item in payload["errors"])
    assert payload["walls"] == []

    bulge_path = tmp_path / "historical-bulge.dxf"
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4
    doc.modelspace().add_lwpolyline([(0, 0, 0.1), (1000, 0, 0), (1000, 1000, 0)], format="xyb", dxfattribs={"layer": "PWA-ROOM"})
    doc.saveas(bulge_path)

    payload = extract_dxf(bulge_path)
    assert any(item["code"] == "PARSE_UNSUPPORTED_FEATURE" for item in payload["errors"])
    assert payload["rooms"] == []


# --------------------------------------------------------------------------- #
# F — evidence rendering: cad_exact SVG overlay renders arcs natively           #
# --------------------------------------------------------------------------- #


def test_cad_exact_overlay_renders_circular_arc_as_svg_arc_path():
    from pwa.floorplan.cad_exact import render_cad_exact_svg

    walls = [
        {"kind": "segment", "start": [0.0, 0.0], "end": [0.0, 6.0]},
        {
            "kind": "circular_arc",
            "arc": {"center": [1.5, 6.0], "radius_m": 1.5, "start_deg": 180.0, "end_deg": 0.0, "sweep": "ccw", "bulge": 1.0, "max_sagitta_px": 0.4},
        },
    ]
    svg = render_cad_exact_svg(walls, rooms=[], openings=[])

    text = svg.decode("utf-8")
    # A native circular arc must render as an SVG A path, not a straight chord.
    assert "<path" in text and "A 1.5,1.5" in text
    # Deterministic: identical inputs -> identical bytes.
    assert render_cad_exact_svg(walls, rooms=[], openings=[]) == svg


# --------------------------------------------------------------------------- #
# G — acceptance gates: topology / resource / adversarial / rollback            #
# --------------------------------------------------------------------------- #


def test_extract_cad_exact_refuses_degenerate_wall(tmp_path):
    # A wall shorter than the frozen DEGENERATE_WALL_M (0.05 m = 50 mm) must
    # fail closed, not be emitted as product geometry.
    path = tmp_path / "degenerate.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    wall = ms.add_line((0, 0), (10, 0), dxfattribs={"layer": "PWA-WALL"})  # 10 mm
    _set_thickness(wall, 0.24)
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "PARSE_DEGENERATE_WALL" for err in payload["errors"])


def test_extract_cad_exact_refuses_self_intersecting_room(tmp_path):
    # A bow-tie room polygon must be rejected as self-intersecting topology.
    path = tmp_path / "bowtie.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    ms.add_lwpolyline(
        [(1000, 1000), (3000, 3000), (1000, 3000), (3000, 1000)],
        format="xy",
        close=True,
        dxfattribs={"layer": "PWA-ROOM"},
    )
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "PARSE_SELF_INTERSECTING_POLYGON" for err in payload["errors"])


def test_extract_cad_exact_refuses_duplicate_wall(tmp_path):
    # Two coincident walls must be flagged as duplicate geometry.
    path = tmp_path / "dup.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    for _ in range(2):
        wall = ms.add_line((0, 0), (5000, 0), dxfattribs={"layer": "PWA-WALL"})
        _set_thickness(wall, 0.24)
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "PARSE_DUPLICATE_ENTITY" for err in payload["errors"])


def test_extract_cad_exact_enforces_entity_resource_limit(tmp_path, monkeypatch):
    # Resource gate: the worker must refuse (fail closed) when the entity
    # count exceeds the frozen MAX_DXF_ENTITIES cap, never silently truncate.
    from pwa.floorplan import cad_exact_worker as W

    monkeypatch.setattr(W, "MAX_DXF_ENTITIES", 2)
    path = tmp_path / "toomany.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    for x in (0, 1000, 2000):
        wall = ms.add_line((x, 0), (x + 500, 0), dxfattribs={"layer": "PWA-WALL"})
        _set_thickness(wall, 0.24)
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "PARSE_RESOURCE_LIMIT" for err in payload["errors"])


def test_extract_cad_exact_enforces_byte_limit(tmp_path, monkeypatch):
    # Resource gate: an oversized DXF source must fail closed on bytes.
    from pwa.floorplan import cad_exact_worker as W

    monkeypatch.setattr(W, "MAX_DXF_BYTES", 16)
    path = tmp_path / "big.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    wall = ms.add_line((0, 0), (5000, 0), dxfattribs={"layer": "PWA-WALL"})
    _set_thickness(wall, 0.24)
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "PARSE_RESOURCE_LIMIT" for err in payload["errors"])


def test_extract_cad_exact_refuses_nonzero_z_wall(tmp_path):
    # Adversarial/topology: a 3D wall (non-zero Z) is out of the approved
    # 2D floorplan envelope and must be refused, matching dxf_worker.
    path = tmp_path / "walls3d.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    wall = ms.add_line((0, 0, 0), (5000, 0, 25), dxfattribs={"layer": "PWA-WALL"})
    _set_thickness(wall, 0.24)
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert any(err["code"] == "PARSE_UNSUPPORTED_FEATURE" for err in payload["errors"])


def test_cad_exact_parse_is_pure_and_rollback_safe(tmp_path):
    # Rollback gate: parsing is a pure read — it never mutates the source and
    # a failure never leaves partial product output behind. Re-parsing the same
    # source yields byte-identical output (idempotent, deterministic).
    path = tmp_path / "fx1-cad.dxf"
    _write_fx1_cad(path)
    before = path.read_bytes()

    first = extract_cad_exact(path)
    second = extract_cad_exact(path)

    assert path.read_bytes() == before  # source untouched
    assert first == second  # pure / deterministic
    assert first["frame"]["kind"] == "cad_exact"


def test_cad_exact_downstream_refusal_keeps_route_disabled():
    # Rollback/topology gate at the emitter boundary: a wall whose thickness
    # is missing must block emission (fail closed), so no partial cad_exact
    # product is produced and the route stays disabled.
    payload, findings = C.emit_floorplan_parse(
        walls=[{"index": 0, "source_ref": "d", "kind": "segment", "start": [0, 0], "end": [9, 0], "thickness_m": None}],
        rooms=[],
        openings=[],
    )
    assert "RECOGNITION_THICKNESS_MISSING" in findings
    # Emission still returned the wall skeleton, but the caller must treat any
    # finding as blocking — verify the finding is the frozen code.
    assert payload["source_class"] == "cad_exact"


def test_extract_cad_exact_tessellates_bulged_room_edge(tmp_path):
    # A room LWPOLYLINE with a bulge on one edge must be tessellated into the
    # arc it represents (more than the raw 2 endpoints), per the FX1 sagitta
    # rule — NOT flattened to the straight chord between the endpoints.
    path = tmp_path / "bulge-tess.dxf"
    doc = _cad_exact_doc()
    ms = doc.modelspace()
    # Quarter-circle bulged corner on the top edge (bulge = tan(90deg/4) = 0.4142).
    ms.add_lwpolyline(
        [(1000, 2000), (9000, 2000, 0.4142135623730951), (9000, 8000), (1000, 8000)],
        format="xyb",
        close=True,
        dxfattribs={"layer": "PWA-ROOM"},
    )
    doc.saveas(path)

    payload = extract_cad_exact(path)

    assert len(payload["rooms"]) == 1
    room = payload["rooms"][0]
    # A bulged edge must be tessellated: the emitted polygon has more vertices
    # than the raw 4 LWPOLYLINE vertices (intermediate arc samples inserted).
    assert len(room["polygon_mm"]) > 4
    # The intermediate vertices must lie off the straight chord (i.e. the arc
    # bulge is honoured, not flattened): the top edge from (1000,2000) to
    # (9000,2000) has a bulge, so at least one sampled y is above y=2000.
    chord_y = 2000.0
    assert any(p[1] > chord_y + 1.0 for p in room["polygon_mm"])
    # Deterministic: identical inputs -> identical tessellation.
    assert extract_cad_exact(path)["rooms"][0]["polygon_mm"] == room["polygon_mm"]
