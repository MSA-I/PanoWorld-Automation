from __future__ import annotations

import hashlib
import json

from pwa.floorplan.annotation_source import AnnotationSource
from pwa.floorplan.dxf_source import DxfSource
from pwa.floorplan.normalize import canonical_projection, normalize
from tests.unit.test_floorplan_sources import _write_annotation_fixture, _write_dxf_fixture


def _projection_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def test_canonical_projection_matches_across_adapters(tmp_path):
    annotation_path, _ = _write_annotation_fixture(tmp_path)
    dxf_path = tmp_path / "layer-a-1.dxf"
    _write_dxf_fixture(dxf_path)

    annotation = normalize(AnnotationSource().extract(annotation_path))
    dxf = normalize(DxfSource().extract(dxf_path))

    assert canonical_projection(annotation) == canonical_projection(dxf)
    assert _projection_hash(canonical_projection(annotation)) == "sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e"
    assert _projection_hash(canonical_projection(dxf)) == "sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e"


def test_adapter_specific_fields(tmp_path):
    annotation_path, _ = _write_annotation_fixture(tmp_path)
    dxf_path = tmp_path / "layer-a-1.dxf"
    _write_dxf_fixture(dxf_path)

    annotation = normalize(AnnotationSource().extract(annotation_path))
    dxf = normalize(DxfSource().extract(dxf_path))

    assert annotation.normalization["source_units"] == "px"
    assert annotation.normalization["y_axis"] == "flipped_from_raster"
    assert annotation.normalization["scale_m_per_px"] == 0.005
    assert dxf.normalization["source_units"] == "mm"
    assert dxf.normalization["y_axis"] == "up"
    assert dxf.normalization["scale_m_per_px"] is None

    assert all(wall.confidence == 1.0 for wall in dxf.walls)
    assert all(room.confidence == 1.0 for room in dxf.rooms)
    assert all(opening.confidence == 1.0 for opening in dxf.openings)

    assert [wall.confidence for wall in annotation.walls] == [0.9, 0.9, 0.6, 0.6, 0.6]
    assert [room.confidence for room in annotation.rooms] == [0.9, 0.6]
    assert [opening.confidence for opening in annotation.openings] == [0.6, 0.9, 0.6, 0.6]
