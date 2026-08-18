"""PLAN-004 extrinsics construction (§7.6).

Camera-to-world 4x4, Z-up world, OpenCV camera axes. Camera coordinate axes:
+X right, +Y down, +Z forward (out of the lens), so R[:,1] == (0,0,-1). The
translation column is the camera's world position (x, y, camera_height_m).

For yaw theta (rotation about world Z), the camera-to-world rotation is

    R = [ -cos(theta)   0    sin(theta) ]
        [ -sin(theta)   0   -cos(theta) ]
        [  0           -1      0        ]

so that camera-forward (+Z) maps to world (sin(theta), -cos(theta), 0) — the
horizon in the Z-up frame — camera-up stays world +Z, and the OpenCV +Y-down
relation R[:,1] == (0,0,-1) holds. This matches the vendored golden fixture
(viewpoints/0000/extrinsics.txt) exactly and is right-handed.

The produced matrix must pass pwa.validator.check_extrinsics_matrix with zero
error codes (machine-checked, not asserted).
"""

from __future__ import annotations

import math

import numpy as np

from pwa.camera.findings import CameraError
from pwa.camera.types import Viewpoint


def build_extrinsics(viewpoint: Viewpoint) -> np.ndarray:
    """Camera-to-world 4x4 extrinsics for a viewpoint (pure, deterministic)."""
    theta = float(viewpoint.yaw_rad)
    c = math.cos(theta)
    s = math.sin(theta)

    r = np.array(
        [
            [-c, 0.0, s],
            [-s, 0.0, -c],
            [0.0, -1.0, 0.0],
        ],
        dtype=float,
    )

    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = r
    matrix[0, 3] = float(viewpoint.position[0])
    matrix[1, 3] = float(viewpoint.position[1])
    matrix[2, 3] = float(viewpoint.camera_height_m)
    return matrix


def format_extrinsics(matrix: np.ndarray) -> str:
    """Format a 4x4 extrinsics matrix as the golden-fixture extrinsics.txt text
    (4 lines of 4 space-separated decimals, trailing newline)."""
    lines = []
    for row in range(4):
        lines.append(" ".join(f"{float(matrix[row, col]):.10f}" for col in range(4)))
    return "\n".join(lines) + "\n"


def validate_extrinsics(viewpoint: Viewpoint) -> list[str]:
    """Return the error codes from check_extrinsics_matrix for a viewpoint's
    matrix (empty == valid). The camera height range is checked by the caller
    (CAM_CAMERA_HEIGHT_OUT_OF_RANGE) before this runs."""
    from pwa.validator.package_validator import check_extrinsics_matrix

    matrix = build_extrinsics(viewpoint)
    return list(check_extrinsics_matrix(matrix))


def build_and_validate(viewpoint: Viewpoint) -> np.ndarray:
    """Build extrinsics and raise CAM_EXTRINSICS_INVALID if invalid."""
    codes = validate_extrinsics(viewpoint)
    if codes:
        raise CameraError("CAM_EXTRINSICS_INVALID", f"extrinsics failed validation: {codes}", source_ref=viewpoint.id)
    return build_extrinsics(viewpoint)