"""Tests for PLAN-004 camera planner: geometry, load, placement, extrinsics,
adjacency (C-t2/C-t3)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from pwa.camera.adjacency import build_adjacency
from pwa.camera.extrinsics import build_extrinsics, validate_extrinsics
from pwa.camera.findings import CameraError
from pwa.camera.geometry import centroid, point_in_polygon
from pwa.camera.load import load_scene_geometry
from pwa.camera.placement import free_space_violations, place_viewpoints
from pwa.camera.types import Opening, Room, SceneGeometry, Viewpoint, Wall
from pwa.validator.package_validator import check_extrinsics_matrix

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENE_GEOMETRY = REPO_ROOT / "evidence" / "PLAN-003" / "geometry-run" / "geometry" / "scene_geometry.json"


def _layer_a_payload() -> dict:
    return json.loads(SCENE_GEOMETRY.read_text(encoding="utf-8"))["payload"]


def _layer_a_geometry() -> SceneGeometry:
    return load_scene_geometry(_layer_a_payload())


# --- geometry helpers ---


def test_centroid_of_axis_aligned_room():
    polygon = ((0.0, 0.0), (5.0, 0.0), (5.0, 6.0), (0.0, 6.0))
    assert centroid(polygon) == pytest.approx((2.5, 3.0))


def test_point_in_polygon_inside_and_outside():
    polygon = ((0.0, 0.0), (5.0, 0.0), (5.0, 6.0), (0.0, 6.0))
    assert point_in_polygon((2.5, 3.0), polygon)
    assert not point_in_polygon((6.0, 3.0), polygon)


def test_point_on_boundary_is_rejected():
    polygon = ((0.0, 0.0), (5.0, 0.0), (5.0, 6.0), (0.0, 6.0))
    # exactly on an edge
    assert not point_in_polygon((2.5, 0.0), polygon)


# --- load ---


def test_loads_layer_a_geometry():
    geometry = _layer_a_geometry()
    assert len(geometry.rooms) == 2
    assert len(geometry.walls) == 5
    assert len(geometry.openings) == 4


def test_load_empty_geometry_fails_closed():
    with pytest.raises(CameraError) as exc:
        load_scene_geometry({"rooms": [], "walls": [], "openings": []})
    assert exc.value.finding.code == "CAM_EMPTY_GEOMETRY"


def test_load_rejects_nonfinite_coordinates():
    payload = _layer_a_payload()
    payload["rooms"][0]["polygon"][0] = [float("nan"), 0.0]
    with pytest.raises(CameraError) as exc:
        load_scene_geometry(payload)
    assert exc.value.finding.code == "CAM_RESOURCE_LIMIT"


# --- placement / free space / coverage ---


def test_places_one_viewpoint_per_room():
    geometry = _layer_a_geometry()
    viewpoints, findings = place_viewpoints(geometry)
    assert len(viewpoints) == 2
    assert not findings
    by_room = {vp.room_id: vp for vp in viewpoints}
    assert set(by_room) == {"gr-0647acdd02a3", "gr-f9c1af865cc3"}
    # zero-padded ordinal ids in deterministic room order
    assert [vp.id for vp in viewpoints] == ["0000", "0001"]


def test_viewpoints_are_free_space_valid():
    geometry = _layer_a_geometry()
    viewpoints, _ = place_viewpoints(geometry)
    for vp in viewpoints:
        room = next(r for r in geometry.rooms if r.id == vp.room_id)
        assert free_space_violations(vp.position, room, geometry) == []


def test_centroid_candidate_invalid_gets_pulled_inward():
    # A thin room whose centroid collides with an opening: the resolver pulls
    # inward. Build a room with an opening centre at the centroid.
    geometry = SceneGeometry(
        rooms=(Room(id="r1", polygon=((0.0, 0.0), (4.0, 0.0), (4.0, 4.0), (0.0, 4.0))),),
        walls=(),
        openings=(Opening(id="o1", type="door", wall_id="w0", center=(2.0, 2.0)),),
    )
    viewpoints, findings = place_viewpoints(geometry)
    # No walls, so the only constraint is the opening clearance (0.20 m).
    assert len(viewpoints) == 1
    assert not findings
    assert abs(viewpoints[0].position[0] - 2.0) > 0.05 or abs(viewpoints[0].position[1] - 2.0) > 0.05


def test_room_fully_colliding_reports_uncovered():
    # A room so thin that no non-colliding point exists within pull-back bound:
    # opening centred at centroid with clearance 0.20 in a 0.10-wide room.
    geometry = SceneGeometry(
        rooms=(Room(id="r1", polygon=((0.0, 0.0), (0.10, 0.0), (0.10, 4.0), (0.0, 4.0))),),
        walls=(),
        openings=(Opening(id="o1", type="door", wall_id="w0", center=(0.05, 2.0)),),
    )
    viewpoints, findings = place_viewpoints(geometry)
    assert len(viewpoints) == 0
    assert any(f.code == "CAM_UNCOVERED_ROOM" for f in findings)


def test_duplicate_positions_fail_closed():
    geometry = _layer_a_geometry()
    # Force two viewpoints onto the same spot by making both rooms identical.
    payload = _layer_a_payload()
    payload["rooms"][1]["polygon"] = payload["rooms"][0]["polygon"]
    geometry2 = load_scene_geometry(payload)
    viewpoints, findings = place_viewpoints(geometry2)
    assert any(f.code == "CAM_DUPLICATE_ENTITY" for f in findings)


def test_viewpoint_outside_room_detected():
    geometry = _layer_a_geometry()
    room = geometry.rooms[0]
    violations = free_space_violations((10.0, 10.0), room, geometry)
    assert any(f.code == "CAM_VIEWPOINT_OUTSIDE_ROOM" for f in violations)


def test_viewpoint_collides_wall_detected():
    geometry = _layer_a_geometry()
    room = geometry.rooms[0]
    # Room 1's bottom wall runs (0,0)-(5,0); a point at (2.5, 0.05) is well
    # within the wall clearance (thickness 0.1 -> clearance 0.4 m).
    violations = free_space_violations((2.5, 0.05), room, geometry)
    assert any(f.code == "CAM_VIEWPOINT_COLLIDES_WALL" for f in violations)


def test_viewpoint_collides_opening_detected():
    geometry = _layer_a_geometry()
    room = geometry.rooms[0]
    # Door at (2.5, 0.0): point at (2.55, 0.1) is within 0.20 m.
    violations = free_space_violations((2.5, 0.05), room, geometry)
    assert any(f.code == "CAM_VIEWPOINT_COLLIDES_OPENING" for f in violations)


# --- extrinsics ---


def _vp(x=0.0, y=0.0, yaw_rad=0.0, height=1.35) -> Viewpoint:
    return Viewpoint(id="0000", position=(x, y), yaw_rad=yaw_rad, room_id="r1", camera_height_m=height)


def test_extrinsics_at_yaw_zero_is_valid():
    matrix = build_extrinsics(_vp())
    assert check_extrinsics_matrix(matrix) == []


def test_extrinsics_matches_golden_fixture():
    golden = np.array([
        [-0.2799965701, -0.0000000000, 0.9600010004, 0.7237534000],
        [-0.9600010004, -0.0000000000, -0.2799965701, -1.0550000000],
        [0.0000000000, -1.0000000000, -0.0000000000, 1.3500000000],
        [0.0000000000, 0.0000000000, 0.0000000000, 1.0000000000],
    ])
    theta = math.atan2(0.96, 0.28)
    vp = _vp(x=0.7237534000, y=-1.0550000000, yaw_rad=theta, height=1.35)
    matrix = build_extrinsics(vp)
    assert np.allclose(matrix, golden, atol=1e-6)


def test_extrinsics_translation_is_camera_position():
    vp = _vp(x=2.5, y=3.0, height=1.35)
    matrix = build_extrinsics(vp)
    assert matrix[0, 3] == 2.5
    assert matrix[1, 3] == 3.0
    assert matrix[2, 3] == 1.35


def test_extrinsics_right_handed_and_orthonormal_for_various_yaws():
    for yaw in (0.0, 0.5, 1.0, math.pi / 2, math.pi):
        matrix = build_extrinsics(_vp(yaw_rad=yaw))
        assert check_extrinsics_matrix(matrix) == []
        r = matrix[:3, :3]
        assert np.allclose(r.T @ r, np.eye(3), atol=1e-4)
        assert np.linalg.det(r) > 0


def test_validate_extrinsics_empty_for_valid_viewpoint():
    assert validate_extrinsics(_vp()) == []


# --- adjacency ---


def test_adjacency_connects_rooms_via_interior_door():
    geometry = _layer_a_geometry()
    viewpoints, _ = place_viewpoints(geometry)
    edges, start, findings = build_adjacency(geometry, viewpoints)
    # Layer A: one interior door (wall gw-f2d519b0b541) connects the two rooms.
    assert start == "0000"
    assert ["0000", "0001"] in edges
    # The exterior bottom door produces a warn, not an edge.
    assert any(f.code == "CAM_MAP_ADJACENCY_UNRESOLVED" for f in findings)


def test_adjacency_window_never_produces_edge():
    geometry = _layer_a_geometry()
    viewpoints, _ = place_viewpoints(geometry)
    edges, _, findings = build_adjacency(geometry, viewpoints)
    # No window should ever create an edge (only doors do).
    window_wall_ids = {o.wall_id for o in geometry.openings if o.type == "window"}
    for edge in edges:
        assert not any(w in window_wall_ids for w in edge)