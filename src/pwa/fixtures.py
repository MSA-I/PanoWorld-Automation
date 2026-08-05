"""Synthetic "tiny scene" fixture factory (PLAN-000 T7, Layer A).

Generates a minimal but fully valid PanoWorld full-pipeline scene: tiny images,
correct extrinsics in the verified demo convention (camera-to-world, OpenCV
axes, Z-up world, camera height 1.35 m), 16-bit depth with a per-viewpoint
scale, and an insertion-ordered map JSON. Generated procedurally so no binary
fixtures are committed for Layer A.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

DEFAULT_SIZE = (32, 16)  # exact 2:1, even dims (patch alignment)
STYLE_PANO_NAME = "panoImage_2048_test.png"
DEPTH_SCALE = 1000.0  # depth_m = pixel / scale (verified upstream semantics)


def _write_extrinsics(path: Path, t: tuple[float, float, float]) -> None:
    # Camera-to-world, rows; R columns are camera axes in world coordinates:
    # X_cam=(1,0,0), Y_cam=(0,0,-1) (image-down = world-down), Z_cam=(0,1,0).
    # Matches the verified demo convention: R[:,1] == (0,0,-1), t[2] = height.
    rows = [
        (1.0, 0.0, 0.0, t[0]),
        (0.0, 0.0, 1.0, t[1]),
        (0.0, -1.0, 0.0, t[2]),
        (0.0, 0.0, 0.0, 1.0),
    ]
    text = "\n".join(" ".join(f"{v:.10f}" for v in row) for row in rows) + "\n"
    path.write_text(text, encoding="ascii")


def make_tiny_scene(
    dest: Path,
    *,
    with_style: bool = True,
    size: tuple[int, int] = DEFAULT_SIZE,
    n_viewpoints: int = 2,
) -> Path:
    """Create ``<dest>/tiny_scene`` and return its path."""
    scene = Path(dest) / "tiny_scene"
    width, height = size
    viewpoint_ids = [f"{i:04d}" for i in range(n_viewpoints)]

    for i, vp in enumerate(viewpoint_ids):
        vp_dir = scene / "viewpoints" / vp
        vp_dir.mkdir(parents=True)

        Image.new("RGB", size, (200, 200, 200)).save(vp_dir / "place_image.png")

        depth = Image.new("I;16", size)
        # Non-zero everywhere, 1.0..~21.4 m after /scale: plausible indoor range.
        depth.putdata([1000 + 40 * k for k in range(width * height)])
        depth.save(vp_dir / "place_depth.png")

        (vp_dir / "place_depth_scale.txt").write_text(f"{DEPTH_SCALE:.0f}\n", encoding="ascii")
        _write_extrinsics(vp_dir / "extrinsics.txt", (float(i), 0.0, 1.35))

    # Insertion order is load-bearing (start node = first key); never sort_keys.
    map_data = {viewpoint_ids[0]: viewpoint_ids[1:]}
    (scene / "map_panoworld0.json").write_text(
        json.dumps(map_data, indent=0), encoding="ascii"
    )

    if with_style:
        Image.new("RGB", size, (180, 150, 120)).save(
            scene / "viewpoints" / viewpoint_ids[0] / STYLE_PANO_NAME
        )
    return scene
