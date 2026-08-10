from __future__ import annotations

import pytest

from pwa.floorplan.normalize import normalize
from pwa.floorplan.types import RawGeometry, RawRoom, RawWall, SourceFrame


@pytest.mark.parametrize(
    ("source", "assertion"),
    [
        pytest.param(
            RawGeometry(
                frame=SourceFrame(kind="dxf", unit_scale_m=1.0, y_down=False, height_px=None, source_units="m"),
                walls=(RawWall(0, "dxf:modelspace/PWA-WALL#01", (0.00005, 0.0), (0.00015, 1.0)),),
                rooms=(RawRoom(0, "dxf:modelspace/PWA-ROOM#11", ((0.00005, 0.0), (1.00015, 0.0), (1.00015, 1.0))),),
                openings=(),
                dimensions=(),
                scanned_entities=2,
                unmapped=(),
            ),
            lambda geometry: (
                geometry.walls[0].start[0] == 0.0 and geometry.walls[0].end[0] == 0.0002
            ),
            id="b-quantize-half-even",
        ),
        pytest.param(
            RawGeometry(
                frame=SourceFrame(kind="raster", unit_scale_m=0.005, y_down=True, height_px=100, source_units="px"),
                walls=(RawWall(0, "annotation:walls[0]", (9.998, 90.002), (10.0, 10.0)),),
                rooms=(RawRoom(0, "annotation:rooms[0]", ((9.998, 90.002), (30.0, 90.002), (30.0, 10.0), (10.0, 10.0))),),
                openings=(),
                dimensions=(),
                scanned_entities=2,
                unmapped=(),
            ),
            lambda geometry: geometry.walls[0].start == (0.0, 0.0) and geometry.rooms[0].polygon[0] == (0.0, 0.0),
            id="b-negative-zero",
        ),
    ],
)
def test_normalize_boundary_cases(source: RawGeometry, assertion):
    assert assertion(normalize(source))
