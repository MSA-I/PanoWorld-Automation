"""Generate PLAN-002 Layer A local fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import ezdxf
from PIL import Image

from pwa.contracts import compute_content_hash
from pwa.files import sha256_file


def build(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    image_path = out / "layer-a-1.png"
    Image.new("RGB", (2000, 1800), "white").save(image_path, format="PNG")

    document = ezdxf.new("R2013")
    document.header["$INSUNITS"] = 4
    modelspace = document.modelspace()
    modelspace.add_line((1000, 2000), (9000, 2000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((9000, 2000), (9000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((1000, 8000), (9000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((1000, 2000), (1000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_line((6000, 2000), (6000, 8000), dxfattribs={"layer": "PWA-WALL"})
    modelspace.add_lwpolyline([(1000, 2000), (6000, 2000), (6000, 8000), (1000, 8000)], dxfattribs={"layer": "PWA-ROOM"}, close=True)
    modelspace.add_lwpolyline([(6000, 2000), (9000, 2000), (9000, 8000), (6000, 8000)], dxfattribs={"layer": "PWA-ROOM"}, close=True)
    modelspace.add_line((3050, 2000), (3950, 2000), dxfattribs={"layer": "PWA-DOOR"})
    modelspace.add_line((6000, 4550), (6000, 5450), dxfattribs={"layer": "PWA-DOOR"})
    modelspace.add_line((2400, 8000), (3600, 8000), dxfattribs={"layer": "PWA-WINDOW"})
    modelspace.add_line((9000, 5900), (9000, 7100), dxfattribs={"layer": "PWA-WINDOW"})
    document.saveas(out / "layer-a-1.dxf")

    annotation = {
        "schema_id": "floorplan_annotation",
        "schema_version": "1.0.0",
        "artifact_id": "layer-a-1-annotation",
        "project_id": "fixture-project",
        "run_id": "RUN-PLAN002-FIXTURE",
        "created_at": "2026-08-09T12:00:00Z",
        "producer": {"agent": "fixture-generator", "provider": "local", "model": "deterministic", "effort": "N/A"},
        "inputs": [],
        "content_hash": "sha256:" + "0" * 64,
        "status": "complete",
        "errors": [],
        "payload": {
            "image": {
                "source_image_ref": "layer-a-1.png",
                "sha256": sha256_file(image_path),
                "width_px": 2000,
                "height_px": 1800,
            },
            "scale_m_per_px": 0.005,
            "walls": [
                {"start_px": [200, 1400], "end_px": [1800, 1400]},
                {"start_px": [1800, 1400], "end_px": [1800, 200]},
                {"start_px": [200, 200], "end_px": [1800, 200]},
                {"start_px": [200, 1400], "end_px": [200, 200]},
                {"start_px": [1200, 1400], "end_px": [1200, 200]},
            ],
            "rooms": [
                {"polygon_px": [[200, 1400], [1200, 1400], [1200, 200], [200, 200]]},
                {"polygon_px": [[1200, 1400], [1800, 1400], [1800, 200], [1200, 200]]},
            ],
            "openings": [
                {"type": "door", "wall_index": 0, "center_px": [700, 1400], "width_m": 0.9},
                {"type": "door", "wall_index": 4, "center_px": [1200, 800], "width_m": 0.9},
                {"type": "window", "wall_index": 2, "center_px": [600, 200], "width_m": 1.2},
                {"type": "window", "wall_index": 1, "center_px": [1800, 500], "width_m": 1.2},
            ],
            "declared_dimensions": [
                {"a_px": [200, 1400], "b_px": [1800, 1400], "length_m": 8.0},
                {"a_px": [200, 1400], "b_px": [200, 200], "length_m": 6.0},
            ],
        },
    }
    # GC-4 (OpenAI cross-provider rework review, 2026-08-10): AnnotationSource
    # now recomputes/verifies content_hash, so this generated fixture must
    # carry a real one instead of the all-zero placeholder.
    annotation["content_hash"] = compute_content_hash(annotation)
    (out / "layer-a-1.annotation.json").write_text(json.dumps(annotation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    build(Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
