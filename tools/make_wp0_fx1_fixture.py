"""Build and verify the PLAN-002RF WP0-FX1 local-only synthetic fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pwa.files import sha256_file, write_json_exclusive

WIDTH_PX = 2400
HEIGHT_PX = 2000
MM_PER_PX = 5
SCALE_M_PER_PX = 0.005
PAYLOAD_FILENAMES = frozenset({
    "fx1-rights-provenance.json",
    "fx1-scale-anchors.json",
    "fx1-source-geometry.json",
    "fx1-truth.json",
    "fx1.png",
})


def _canonical_hash(document: Any) -> str:
    encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _px(point_mm: list[int]) -> list[int]:
    x_mm, y_mm = point_mm
    if x_mm % MM_PER_PX or y_mm % MM_PER_PX:
        raise ValueError(f"authored coordinate is not on the {MM_PER_PX} mm grid: {point_mm}")
    return [x_mm // MM_PER_PX, HEIGHT_PX - y_mm // MM_PER_PX]


def _source() -> dict[str, Any]:
    return {
        "document": "fx1-source-geometry",
        "version": "1.0.0",
        "origin": "project_owned_deterministic_synthetic",
        "rights": "project-owned; no third-party bytes or assets",
        "coordinate_system": {"units": "mm", "origin": "canvas_bottom_left", "y_axis": "up"},
        "canvas": {"width_px": WIDTH_PX, "height_px": HEIGHT_PX, "mm_per_px": MM_PER_PX},
        "walls": [
            {"id": "W-S", "kind": "segment", "a_mm": [1000, 1500], "b_mm": [9000, 1500]},
            {"id": "W-E-A", "kind": "segment", "a_mm": [9000, 1500], "b_mm": [9000, 1750]},
            {"id": "W-APSE", "kind": "circular_arc", "center_mm": [9000, 3250], "radius_mm": 1500, "start_deg": -90, "end_deg": 90},
            {"id": "W-E-B", "kind": "segment", "a_mm": [9000, 4750], "b_mm": [9000, 8500]},
            {"id": "W-N", "kind": "segment", "a_mm": [3400, 8500], "b_mm": [9000, 8500]},
            {"id": "W-DIAG", "kind": "segment", "orientation": "diagonal_3_4_5", "a_mm": [1000, 6700], "b_mm": [3400, 8500]},
            {"id": "W-W", "kind": "segment", "a_mm": [1000, 1500], "b_mm": [1000, 6700]},
            {"id": "W-PV", "kind": "segment", "a_mm": [4000, 1500], "b_mm": [4000, 8500]},
            {"id": "W-PH", "kind": "segment", "a_mm": [4000, 5000], "b_mm": [9000, 5000]},
        ],
        "openings": [
            {"id": "O-D1", "type": "door", "host_id": "W-S", "a_mm": [2050, 1500], "b_mm": [2950, 1500], "width_mm": 900},
            {"id": "O-D2", "type": "door", "host_id": "W-PH", "a_mm": [6550, 5000], "b_mm": [7450, 5000], "width_mm": 900},
            {"id": "O-P1", "type": "passage", "host_id": "W-PV", "a_mm": [4000, 6050], "b_mm": [4000, 7550], "width_mm": 1500},
            {"id": "O-W1", "type": "window", "host_id": "W-N", "a_mm": [5400, 8500], "b_mm": [6600, 8500], "width_mm": 1200},
            {"id": "O-W2", "type": "window", "host_id": "W-APSE", "start_deg": -22.5, "end_deg": 22.5, "width_basis": "arc_length"},
            {"id": "O-W3", "type": "window", "host_id": "W-DIAG", "a_mm": [1720, 7240], "b_mm": [2680, 7960], "width_mm": 1200},
        ],
        "rooms": [
            {"id": "R-HALL", "polygon_mm": [[1000, 1500], [4000, 1500], [4000, 8500], [3400, 8500], [1000, 6700]]},
            {"id": "R-NE", "polygon_mm": [[4000, 5000], [9000, 5000], [9000, 8500], [4000, 8500]]},
            {"id": "R-SE", "boundary_refs": ["W-S", "W-E-A", "W-APSE", "W-E-B", "W-PH", "W-PV"]},
        ],
        "topology": [
            {"a": "R-HALL", "b": "R-NE", "opening_ids": ["O-P1"]},
            {"a": "R-NE", "b": "R-SE", "opening_ids": ["O-D2"]},
            {"a": "R-HALL", "b": "R-SE", "opening_ids": [], "sealed_adjacency": True},
        ],
        "clutter": [
            {"id": "C-1", "kind": "rectangle", "box_mm": [1300, 2600, 2300, 3400]},
            {"id": "C-2", "kind": "rectangle", "box_mm": [4600, 5600, 6200, 6800]},
            {"id": "C-3", "kind": "circle", "center_mm": [7600, 7000], "radius_mm": 600},
            {"id": "C-4", "kind": "line", "a_mm": [4400, 2200], "b_mm": [8400, 2200]},
            {"id": "C-5", "kind": "line", "a_mm": [1400, 5000], "b_mm": [3600, 5000]},
            {"id": "C-6", "kind": "tick_run", "origin_mm": [1300, 4000], "count": 5, "pitch_mm": 300, "length_mm": 800},
            {"id": "C-7", "kind": "tick_run", "origin_mm": [4600, 3400], "count": 5, "pitch_mm": 300, "length_mm": 600},
            {"id": "C-8", "kind": "rectangle", "box_mm": [7000, 3600, 8600, 4400]},
            {"id": "C-9", "kind": "circle", "center_mm": [6000, 2800], "radius_mm": 400},
        ],
        "anchors": [
            {"id": "A-S", "a_mm": [1500, 750], "b_mm": [6500, 750], "real_length_m": 5.0, "placement_region": "south_margin"},
            {"id": "A-W", "a_mm": [500, 2000], "b_mm": [500, 8000], "real_length_m": 6.0, "placement_region": "west_margin"},
            {"id": "A-D", "a_mm": [10500, 5500], "b_mm": [11700, 7100], "real_length_m": 2.0, "placement_region": "east_margin"},
        ],
    }


def _arc_points(center_mm: list[int], radius_mm: int, start_deg: float, end_deg: float, steps: int = 32) -> list[list[float]]:
    cx, cy = center_mm
    return [[cx + radius_mm * math.cos(math.radians(start_deg + (end_deg - start_deg) * index / steps)), cy + radius_mm * math.sin(math.radians(start_deg + (end_deg - start_deg) * index / steps))] for index in range(steps + 1)]


def _float_px(point_mm: list[float]) -> tuple[float, float]:
    return point_mm[0] / MM_PER_PX, HEIGHT_PX - point_mm[1] / MM_PER_PX


def _render(source: dict[str, Any]) -> Image.Image:
    image = Image.new("L", (WIDTH_PX, HEIGHT_PX), 255)
    draw = ImageDraw.Draw(image)
    for item in source["clutter"]:
        if item["kind"] == "rectangle":
            x1, y1, x2, y2 = item["box_mm"]
            draw.rectangle([_px([x1, y2]), _px([x2, y1])], outline=128, width=1)
        elif item["kind"] == "circle":
            cx, cy = item["center_mm"]
            r = item["radius_mm"]
            draw.ellipse([_px([cx - r, cy + r]), _px([cx + r, cy - r])], outline=128, width=1)
        elif item["kind"] == "line":
            draw.line([_px(item["a_mm"]), _px(item["b_mm"])], fill=128, width=1)
        else:
            ox, oy = item["origin_mm"]
            for index in range(item["count"]):
                x = ox + index * item["pitch_mm"]
                draw.line([_px([x, oy]), _px([x, oy + item["length_mm"]])], fill=128, width=1)
    for anchor in source["anchors"]:
        a, b = _px(anchor["a_mm"]), _px(anchor["b_mm"])
        draw.line([a, b], fill=64, width=2)
        for x, y in (a, b):
            draw.line([(x - 10, y - 10), (x + 10, y + 10)], fill=64, width=2)
    openings_by_host = {wall["id"]: [] for wall in source["walls"]}
    for opening in source["openings"]:
        openings_by_host[opening["host_id"]].append(opening)
    for wall in source["walls"]:
        if wall["kind"] == "segment":
            ax, ay = wall["a_mm"]
            bx, by = wall["b_mm"]
            dx, dy = bx - ax, by - ay
            denominator = dx * dx + dy * dy
            cuts = []
            for opening in openings_by_host[wall["id"]]:
                ta = ((opening["a_mm"][0] - ax) * dx + (opening["a_mm"][1] - ay) * dy) / denominator
                tb = ((opening["b_mm"][0] - ax) * dx + (opening["b_mm"][1] - ay) * dy) / denominator
                cuts.append(tuple(sorted((ta, tb))))
            cursor = 0.0
            for start, end in sorted(cuts):
                if start > cursor:
                    draw.line([
                        _float_px([ax + cursor * dx, ay + cursor * dy]),
                        _float_px([ax + start * dx, ay + start * dy]),
                    ], fill=0, width=3)
                cursor = max(cursor, end)
            if cursor < 1.0:
                draw.line([
                    _float_px([ax + cursor * dx, ay + cursor * dy]),
                    _float_px([bx, by]),
                ], fill=0, width=3)
        else:
            arc_openings = openings_by_host[wall["id"]]
            opening = arc_openings[0] if arc_openings else None
            spans = [(wall["start_deg"], wall["end_deg"])] if opening is None else [
                (wall["start_deg"], opening["start_deg"]),
                (opening["end_deg"], wall["end_deg"]),
            ]
            for start_deg, end_deg in spans:
                steps = max(2, round((end_deg - start_deg) / 5.625))
                points = _arc_points(wall["center_mm"], wall["radius_mm"], start_deg, end_deg, steps)
                draw.line([_float_px(point) for point in points], fill=0, width=3)
    walls_by_id = {wall["id"]: wall for wall in source["walls"]}
    for opening in source["openings"]:
        if "a_mm" not in opening:
            host = walls_by_id[opening["host_id"]]
            points = _arc_points(host["center_mm"], host["radius_mm"], opening["start_deg"], opening["end_deg"], 8)
            draw.line([_float_px(point) for point in points], fill=0, width=2)
            continue
        a, b = _px(opening["a_mm"]), _px(opening["b_mm"])
        if opening["type"] == "window":
            draw.line([a, b], fill=0, width=2)
            draw.line([(a[0] + 4, a[1] + 4), (b[0] + 4, b[1] + 4)], fill=0, width=2)
        elif opening["type"] == "door":
            dx = b[0] - a[0]
            dy = b[1] - a[1]
            length = math.hypot(dx, dy) or 1.0
            # Leaf drawn PERPENDICULAR to the host wall (image space, y-down),
            # not always "up": a vertical wall's leaf must be horizontal, else it
            # collinearly refills the opening gap and the raster contradicts truth.
            draw.line([a, (a[0] + dy / length * 180.0, a[1] - dx / length * 180.0)], fill=0, width=2)
        else:
            for x, y in (a, b):
                draw.line([(x - 10, y), (x + 10, y)], fill=0, width=2)
    return image


def _truth(source: dict[str, Any], source_hash: str) -> dict[str, Any]:
    walls = []
    for wall in source["walls"]:
        record = dict(wall)
        if wall["kind"] == "segment":
            record["a_px"] = _px(wall["a_mm"])
            record["b_px"] = _px(wall["b_mm"])
        else:
            record["tessellation_rule"] = {"segments": 32, "max_sagitta_px": 0.5}
            record["vertices_mm"] = [[round(value, 9) for value in point] for point in _arc_points(wall["center_mm"], wall["radius_mm"], wall["start_deg"], wall["end_deg"])]
        walls.append(record)
    return {
        "document": "fx1-frozen-independent-truth",
        "version": "1.0.0",
        "source_sha256": source_hash,
        "derived_only_from": ["fx1-source-geometry.json"],
        "recognizer_inputs": [],
        "frozen_before_recognition": True,
        "scale_m_per_px": SCALE_M_PER_PX,
        "walls": walls,
        "rooms": source["rooms"],
        "openings": source["openings"],
        "topology": source["topology"],
        "clutter": source["clutter"],
    }


def _anchors(source: dict[str, Any], source_hash: str, raster_hash: str, truth_hash: str) -> dict[str, Any]:
    records = []
    for anchor in source["anchors"]:
        a_px, b_px = _px(anchor["a_mm"]), _px(anchor["b_mm"])
        span_px = math.hypot(b_px[0] - a_px[0], b_px[1] - a_px[1])
        records.append({**anchor, "a_px": a_px, "b_px": b_px, "span_px": span_px, "provenance": f"fx1-source-geometry.json#anchors/{anchor['id']}", "derived_m_per_px": anchor["real_length_m"] / span_px})
    return {
        "document": "fx1-authoritative-scale-anchors",
        "version": "1.0.0",
        "source_sha256": source_hash,
        "raster_sha256": raster_hash,
        "truth_sha256": truth_hash,
        "anchors": records,
    }


def build_fixture(out: Path) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    source = _source()
    source_path = out / "fx1-source-geometry.json"
    write_json_exclusive(source_path, source, create_parents=False)
    source_hash = sha256_file(source_path)

    raster_path = out / "fx1.png"
    _render(source).save(raster_path, format="PNG", optimize=False, compress_level=6)
    raster_hash = sha256_file(raster_path)

    truth = _truth(source, source_hash)
    truth_path = out / "fx1-truth.json"
    write_json_exclusive(truth_path, truth, create_parents=False)
    truth_hash = sha256_file(truth_path)

    anchors_path = out / "fx1-scale-anchors.json"
    write_json_exclusive(anchors_path, _anchors(source, source_hash, raster_hash, truth_hash), create_parents=False)

    rights_path = out / "fx1-rights-provenance.json"
    write_json_exclusive(rights_path, {
        "origin": "project_owned_generated",
        "third_party_bytes": 0,
        "third_party_assets": [],
        "network_acquisition": "none",
        "license_statement": "This synthetic fixture is project-created; no repository-wide distribution-license claim is made.",
        "local_only": True,
    }, create_parents=False)

    files = {path.name: sha256_file(path) for path in sorted(out.iterdir())}
    manifest = {
        "document": "fx1-deterministic-replay-manifest",
        "version": "1.0.0",
        "files": files,
        "replay_hash": _canonical_hash(files),
        "dependency_policy": "existing local environment only; pinned-environment proof pending; no install performed",
        "recognition_or_scoring_performed": False,
    }
    write_json_exclusive(out / "fx1-manifest.json", manifest, create_parents=False)
    report = verify_fixture(out)
    if not report["valid"]:
        raise ValueError(f"generated invalid fixture: {report}")
    return out


def verify_fixture(package: Path) -> dict[str, Any]:
    package = Path(package)
    manifest_path = package / "fx1-manifest.json"
    if not manifest_path.is_file():
        return {"valid": False, "mismatches": ["fx1-manifest.json"], "files_verified": 0}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"valid": False, "mismatches": ["manifest_structure"], "files_verified": 0}
    files = manifest.get("files")
    replay_hash = manifest.get("replay_hash")
    if not isinstance(files, dict) or not all(isinstance(name, str) and isinstance(digest, str) for name, digest in files.items()):
        return {"valid": False, "mismatches": ["manifest_structure"], "files_verified": 0}
    mismatches = []
    if set(files) != PAYLOAD_FILENAMES or any(Path(name).is_absolute() or Path(name).name != name for name in files):
        mismatches.append("manifest_file_scope")
    actual_names = {path.name for path in package.iterdir() if path.is_file()}
    if actual_names != PAYLOAD_FILENAMES | {"fx1-manifest.json"}:
        mismatches.append("unexpected_files")
    for name, expected in files.items():
        if name not in PAYLOAD_FILENAMES:
            continue
        path = package / name
        if not path.is_file() or sha256_file(path) != expected:
            mismatches.append(name)
    if _canonical_hash(files) != replay_hash:
        mismatches.append("replay_hash")
    return {"valid": not mismatches, "mismatches": sorted(set(mismatches)), "files_verified": len(files)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    if (args.out is None) == (args.verify is None):
        parser.error("provide exactly one of --out or --verify")
    if args.out is not None:
        build_fixture(args.out)
        return 0
    report = verify_fixture(args.verify)
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
