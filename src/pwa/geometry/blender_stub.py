"""Headless-Blender export stub (PLAN-003 §8, default-off).

Best-effort evidence only: writes an optional `.glb` white model by shelling
out to the pinned local Blender 5.1 binary in `--background` mode running a
repo-owned deterministic script. This path is default-off and never affects
the geometry gate — a missing or failing Blender run is recorded as a deferral
(geometry-report `export.blender_completed` stays false), never a failure.

The Blender script is repo-owned, deterministic and network-free (TB-2, TB-5):
no eval of LLM-generated content, no imports beyond bpy, factory settings.
Full Blender/rendering integration is PLAN-005 scope; in PLAN-003 this exists
only to produce visual evidence and is itself reviewed in PLAN-005.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

_PINNED_BLENDER_CANDIDATES = (
    r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
)

_GLB_EXPORT_SCRIPT = r"""
import bpy
import json
import os
import math

spec_path = os.environ["PWA_GEOMETRY_SPEC"]
out_path = os.environ["PWA_GEOMETRY_OUT"]
with open(spec_path, "r", encoding="utf-8") as fh:
    spec = json.load(fh)

bpy.ops.wm.read_factory_settings(use_empty=True)

def add_wall(start, end, thickness, height):
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = "wall"
    cx, cy = (sx + ex) / 2, (sy + ey) / 2
    obj.location = (cx, cy, height / 2)
    obj.scale = (thickness / 2, length / 2, height / 2)
    angle = math.atan2(dy, dx)
    obj.rotation_euler = (0, 0, angle - math.pi / 2)

for wall in spec["payload"]["walls"]:
    add_wall(
        [wall["start"][0], wall["start"][1]],
        [wall["end"][0], wall["end"][1]],
        wall["thickness_m"],
        wall["height_m"],
    )

bpy.ops.export_scene.gltf(filepath=out_path, export_apply=True)
"""


def _blender_binary() -> Path | None:
    for candidate in _PINNED_BLENDER_CANDIDATES:
        if Path(candidate).exists():
            return Path(candidate)
    found = shutil.which("blender")
    return Path(found) if found else None


def blend_completed(staging_run: Path, compiled) -> bool:
    """Attempt a headless `.glb` export. Returns True only on actual success.

    ``compiled`` is accepted for API symmetry but unused — the script reads the
    already-written `scene_geometry.json` envelope from disk.

    A missing binary, subprocess failure, or any exception returns False; the
    caller records the deferral and continues (geometry gate unaffected).
    """
    del compiled  # unused; the Blender script reads scene_geometry.json
    binary = _blender_binary()
    if binary is None:
        return False
    geometry_dir = staging_run / "geometry"
    spec_path = geometry_dir / "scene_geometry.json"
    out_path = geometry_dir / "scene_geometry.glb"
    try:
        subprocess.run(
            [
                str(binary),
                "--background",
                "--python-expr",
                _GLB_EXPORT_SCRIPT,
            ],
            check=True,
            capture_output=True,
            timeout=120,
            env={
                **__import__("os").environ,
                "PWA_GEOMETRY_SPEC": str(spec_path),
                "PWA_GEOMETRY_OUT": str(out_path),
            },
        )
    except Exception:
        return False
    return out_path.exists() and out_path.stat().st_size > 0
