"""Tests for PLAN-003 topology + dimension validation (G-t3, AC-9)."""

from __future__ import annotations

import json
from pathlib import Path

from pwa.geometry.compiler import compile_geometry
from pwa.geometry.load import load_parse_geometry
from pwa.geometry.topology import validate_topology
from pwa.geometry.types import CompiledGeometry, GeoOpening, GeoRoom, GeoWall

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYER_A_DXF = REPO_ROOT / "evidence" / "PLAN-002" / "parse" / "layer-a-1-dxf.json"


def _layer_a_payload() -> dict:
    return json.loads(LAYER_A_DXF.read_text(encoding="utf-8"))["payload"]


def _compiled(payload: dict) -> CompiledGeometry:
    return compile_geometry(load_parse_geometry(payload))


def test_layer_a_has_no_topology_findings():
    findings = validate_topology(_compiled(_layer_a_payload()))
    assert findings == []


def _codes(findings) -> set:
    return {f.code for f in findings}


def test_degenerate_wall_fails_closed():
    payload = _layer_a_payload()
    payload["walls"][0]["start"] = [0.0, 0.0]
    payload["walls"][0]["end"] = [0.01, 0.0]  # 1 cm wall, below 0.05 m threshold
    findings = validate_topology(_compiled(payload))
    assert "GEOM_DEGENERATE_WALL" in _codes(findings)


def test_unknown_wall_ref_fails_closed():
    payload = _layer_a_payload()
    payload["openings"][0]["wall_id"] = "w-does-not-exist"
    findings = validate_topology(_compiled(payload))
    assert "GEOM_OPENING_UNRESOLVED_WALL" in _codes(findings)


def test_opening_off_wall_fails_closed():
    payload = _layer_a_payload()
    # Move the first window's centre off its host wall (w-0df3b64861a5 is the
    # top wall y=6.0; shift the window to y=4.0 which is far off-wall).
    payload["openings"][0]["center"] = [2.0, 3.0]
    findings = validate_topology(_compiled(payload))
    assert "GEOM_OPENING_OFF_WALL" in _codes(findings)


def test_opening_above_wall_fails_closed():
    # A window with sill+height above the 2.60 m wall: craft a window with a
    # sill that would push it over. Use a custom compiled geometry directly.
    wall = GeoWall(id="gw-x", start=(0.0, 0.0), end=(8.0, 0.0), height_m=2.6, thickness_m=0.1)
    opening = GeoOpening(
        id="go-x", type="window", wall_id="gw-x", center=(4.0, 0.0),
        width_m=1.2, height_m=1.2, sill_m=2.5, depth_m=0.1,
    )
    compiled = CompiledGeometry(
        units="m", up_axis="z", default_ceiling_height_m=2.6,
        rooms=(GeoRoom(id="gr-x", polygon=((0.0, 0.0), (8.0, 0.0), (8.0, 6.0), (0.0, 6.0)), floor_z=0.0, ceiling_z=2.6),),
        walls=(wall,), openings=(opening,),
    )
    findings = validate_topology(compiled)
    assert "GEOM_OPENING_ABOVE_WALL" in _codes(findings)


def test_opening_width_exceeds_wall_fails_closed():
    payload = _layer_a_payload()
    # Give a door an absurd width that cannot fit its wall.
    for opening in payload["openings"]:
        if opening["type"] == "door":
            opening["width_m"] = 50.0
    findings = validate_topology(_compiled(payload))
    assert "GEOM_OPENING_WIDTH_EXCEEDS_WALL" in _codes(findings)


def test_unclosed_room_fails_closed():
    payload = _layer_a_payload()
    # Collapse a room to fewer than 3 distinct vertices.
    payload["rooms"][0]["polygon"] = [[0.0, 0.0], [5.0, 0.0], [0.0, 0.0]]
    findings = validate_topology(_compiled(payload))
    assert "GEOM_OPEN_POLYGON" in _codes(findings)


def test_zero_area_room_fails_closed():
    payload = _layer_a_payload()
    # A collinear "room" with non-zero vertex count but zero area.
    payload["rooms"][0]["polygon"] = [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]]
    findings = validate_topology(_compiled(payload))
    assert "GEOM_SELF_INTERSECTING_POLYGON" in _codes(findings)
