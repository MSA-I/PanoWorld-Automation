"""Unit tests for the matrix and filename checks (PLAN-000 T8/T9, TDD-first).

Codes per contracts/error_codes.md. The reference matrix uses the verified demo
convention: camera-to-world, OpenCV camera axes, Z-up world (R[:,1] == (0,0,-1)).
"""
from __future__ import annotations

import numpy as np
import pytest

from pwa.validator import check_extrinsics_matrix, check_filename

STANDARD = np.array([
    [1.0, 0.0, 0.0, 0.5],
    [0.0, 0.0, 1.0, -1.0],
    [0.0, -1.0, 0.0, 1.35],
    [0.0, 0.0, 0.0, 1.0],
])


def test_standard_matrix_is_clean():
    assert check_extrinsics_matrix(STANDARD) == []


def test_wrong_shape():
    assert "INVALID_MATRIX_SHAPE" in check_extrinsics_matrix(STANDARD[:3, :])


def test_singular_matrix():
    m = STANDARD.copy()
    m[:3, :3] = 0.0
    assert "MATRIX_NOT_INVERTIBLE" in check_extrinsics_matrix(m)


def test_bad_last_row():
    m = STANDARD.copy()
    m[3] = [0.0, 0.0, 0.1, 1.0]
    assert "MATRIX_LAST_ROW_INVALID" in check_extrinsics_matrix(m)


def test_non_orthonormal_rotation():
    m = STANDARD.copy()
    m[:3, :3] *= 2.0  # scaled rotation: invertible but not orthonormal
    assert "MATRIX_NOT_ORTHONORMAL" in check_extrinsics_matrix(m)


def test_reflection_not_right_handed():
    m = STANDARD.copy()
    m[:3, 0] *= -1.0  # mirror X: orthonormal, det = -1
    assert "MATRIX_NOT_RIGHT_HANDED" in check_extrinsics_matrix(m)


def test_y_up_world_warns_nonstandard_convention():
    # Identity rotation: camera Y-down maps to world Y — NOT the demo's Z-up.
    m = np.eye(4)
    m[2, 3] = 1.35
    codes = check_extrinsics_matrix(m)
    assert "NONSTANDARD_WORLD_CONVENTION" in codes
    # Still a perfectly valid rigid transform — no hard errors expected.
    assert not {"MATRIX_NOT_ORTHONORMAL", "MATRIX_NOT_INVERTIBLE"} & set(codes)


def test_camera_height_outlier_warn():
    m = STANDARD.copy()
    m[2, 3] = 12.0  # 12 m high camera in the Z-up convention
    assert "CAMERA_HEIGHT_OUTLIER" in check_extrinsics_matrix(m)


@pytest.mark.parametrize("bad", ["NUL", "con", "COM1.txt", "aux.png", "name.", "name "])
def test_windows_hostile_filenames_rejected(bad):
    assert check_filename(bad) is False


@pytest.mark.parametrize("good", ["place_image.png", "extrinsics.txt", "0000", "map_panoworld0.json"])
def test_normal_filenames_accepted(good):
    assert check_filename(good) is True
