"""Tests for PLAN-003 geometry load + compiler (G-t2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pwa.geometry.compiler import (
    assumption_entries,
    compile_geometry,
    derive_opening_id,
    derive_room_id,
    derive_wall_id,
)
from pwa.geometry.config import (
    DEFAULT_CEILING_HEIGHT_M,
    DOOR_HEIGHT_M,
    DOOR_SILL_M,
    WALL_HEIGHT_M,
    WALL_THICKNESS_M,
    WINDOW_HEIGHT_M,
    WINDOW_SILL_M,
)
from pwa.geometry.findings import GeometryError
from pwa.geometry.load import load_parse_geometry

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYER_A_DXF = REPO_ROOT / "evidence" / "PLAN-002" / "parse" / "layer-a-1-dxf.json"


def _layer_a_payload() -> dict:
    return json.loads(LAYER_A_DXF.read_text(encoding="utf-8"))["payload"]


def test_loads_layer_a_geometry():
    geometry = load_parse_geometry(_layer_a_payload())
    assert len(geometry.walls) == 5
    assert len(geometry.rooms) == 2
    assert len(geometry.openings) == 4
    assert geometry.units == "m"


def test_compiled_walls_carry_thickness_and_height():
    compiled = compile_geometry(load_parse_geometry(_layer_a_payload()))
    for wall in compiled.walls:
        assert wall.thickness_m == WALL_THICKNESS_M
        assert wall.height_m == WALL_HEIGHT_M


def test_compiled_openings_carry_height_and_sill():
    compiled = compile_geometry(load_parse_geometry(_layer_a_payload()))
    doors = [o for o in compiled.openings if o.type == "door"]
    windows = [o for o in compiled.openings if o.type == "window"]
    assert doors
    assert windows
    for door in doors:
        assert door.height_m == DOOR_HEIGHT_M
        assert door.sill_m == DOOR_SILL_M
        # AC-5: door depth == host wall thickness
        host = next(w for w in compiled.walls if w.id == door.wall_id)
        assert door.depth_m == host.thickness_m
    for window in windows:
        assert window.height_m == WINDOW_HEIGHT_M
        assert window.sill_m == WINDOW_SILL_M


def test_opening_wall_refs_are_remapped_to_derived_ids():
    compiled = compile_geometry(load_parse_geometry(_layer_a_payload()))
    wall_ids = {w.id for w in compiled.walls}
    for opening in compiled.openings:
        assert opening.wall_id in wall_ids


def test_default_ceiling_height_is_bound():
    compiled = compile_geometry(load_parse_geometry(_layer_a_payload()))
    assert compiled.default_ceiling_height_m == DEFAULT_CEILING_HEIGHT_M == WALL_HEIGHT_M


def test_compiled_rooms_have_floor_and_ceiling_zero_up():
    compiled = compile_geometry(load_parse_geometry(_layer_a_payload()))
    for room in compiled.rooms:
        assert room.floor_z == 0.0
        assert room.ceiling_z == DEFAULT_CEILING_HEIGHT_M


def test_derived_ids_are_stable_and_distinct():
    assert derive_wall_id("w-a") == derive_wall_id("w-a")
    assert derive_wall_id("w-a") != derive_wall_id("w-b")
    assert derive_wall_id("w-a") != derive_room_id("w-a")
    assert derive_opening_id("o-a") != derive_opening_id("o-b")


def test_per_wall_thickness_override():
    payload = _layer_a_payload()
    payload["walls"] = [{**w, "thickness_m": 0.20} for w in payload["walls"]]
    compiled = compile_geometry(load_parse_geometry(payload))
    for wall in compiled.walls:
        assert wall.thickness_m == 0.20


def test_assumption_entries_record_defaults():
    geometry = load_parse_geometry(_layer_a_payload())
    entries = assumption_entries(geometry)
    keys = {e["key"] for e in entries}
    assert "wall.thickness_m" in keys
    assert "wall.height_m" in keys
    assert "default_ceiling_height_m" in keys
    assert "door.height_m" in keys
    assert "window.sill_m" in keys
    for entry in entries:
        assert entry["source"] == "default"
        assert entry["value"]
        assert entry["reason"]


def test_duplicate_wall_id_fails_closed():
    payload = _layer_a_payload()
    # Force two walls to collide (same id) -> derived collision via same input id
    payload["walls"][1]["id"] = payload["walls"][0]["id"]
    with pytest.raises(GeometryError) as exc:
        compile_geometry(load_parse_geometry(payload))
    assert exc.value.finding.code == "GEOM_DUPLICATE_ENTITY"


def test_empty_geometry_fails_closed():
    with pytest.raises(GeometryError) as exc:
        load_parse_geometry({"walls": [], "rooms": [], "openings": []})
    assert exc.value.finding.code == "GEOM_EMPTY_GEOMETRY"
