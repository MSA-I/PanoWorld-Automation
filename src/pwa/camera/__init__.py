"""Deterministic plan004-camera-planner package."""

from __future__ import annotations

from pwa.camera.adjacency import build_adjacency
from pwa.camera.extrinsics import build_and_validate, build_extrinsics
from pwa.camera.load import load_scene_geometry
from pwa.camera.overlay import render_overlay_svg
from pwa.camera.placement import place_viewpoints
from pwa.camera.report import coverage_report
from pwa.camera.run_builder import build_camera_run

__all__ = [
    "build_adjacency",
    "build_and_validate",
    "build_extrinsics",
    "load_scene_geometry",
    "render_overlay_svg",
    "place_viewpoints",
    "coverage_report",
    "build_camera_run",
]