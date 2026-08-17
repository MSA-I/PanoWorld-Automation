"""Build the PLAN-002RF WP4 R0 clean-raster corpus (synthetic, project-owned).

Synthesises 32 clean-raster fixtures, each with frozen truth + authoritative
scale anchors, varying in room count, wall count, arc/diagonal presence and
clutter (the U-5 style spread). Deterministic (seeded PRNG) and project-owned:
no third-party bytes, no network, no license claim beyond project-created work.

Authoring convention (identical to FX1):
  - walls: 3 px strokes at value 0;
  - opening motifs: 2 px strokes at value 0 (door leaf perpendicular, window =
    two offset parallel lines, passage = jamb ticks);
  - scale anchors: 2 px strokes at value 64 with diagonal end ticks;
  - clutter: 1 px strokes at value 128;
  - background: 255.
The truth is DERIVED ONLY from the source geometry (frozen before recognition),
never from the raster, so every fixture satisfies the AT-21 independent-truth
discipline for synthetic plans (truth is a pure function of source geometry).
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from pwa.files import sha256_file, write_json_exclusive  # noqa: E402
import make_wp0_fx1_fixture as F1  # reuse render/truth/anchors helpers  # noqa: E402

WIDTH_PX = 2400
HEIGHT_PX = 2000
MM_PER_PX = 5
SCALE_M_PER_PX = 0.005
COUNT = 60
SEED = 20260817


def _rng(i: int) -> random.Random:
    return random.Random(f"{SEED}:{i}")


# Canvas-space offset of every plan so walls never touch the image border and
# the north/east margins exist for the scale anchors (canvas 12000x10000 mm).
OX, OY = 500, 500


def _plan_anchors(W: int, H: int) -> list[dict[str, Any]]:
    """Three non-collinear anchors in the north/east margins (plan-local coords)."""
    return [
        {"id": "A-N", "a_mm": [0, H + 750], "b_mm": [5000, H + 750], "real_length_m": 5.0, "placement_region": "north_margin"},
        {"id": "A-E", "a_mm": [W + 750, 0], "b_mm": [W + 750, 5000], "real_length_m": 5.0, "placement_region": "east_margin"},
        {"id": "A-D", "a_mm": [W + 500, H + 500], "b_mm": [W + 1100, H + 1300], "real_length_m": 1.0, "placement_region": "northeast_margin"},
    ]


def _shift(source: dict[str, Any], dx: int, dy: int) -> dict[str, Any]:
    def pt(p):
        return [p[0] + dx, p[1] + dy]

    for wall in source["walls"]:
        if wall["kind"] == "segment":
            wall["a_mm"] = pt(wall["a_mm"])
            wall["b_mm"] = pt(wall["b_mm"])
        else:
            wall["center_mm"] = pt(wall["center_mm"])
    for opening in source["openings"]:
        if "a_mm" in opening:
            opening["a_mm"] = pt(opening["a_mm"])
            opening["b_mm"] = pt(opening["b_mm"])
    for room in source["rooms"]:
        if "polygon_mm" in room:
            room["polygon_mm"] = [pt(p) for p in room["polygon_mm"]]
    for c in source["clutter"]:
        if "box_mm" in c:
            c["box_mm"] = [c["box_mm"][0] + dx, c["box_mm"][1] + dy, c["box_mm"][2] + dx, c["box_mm"][3] + dy]
        elif "center_mm" in c:
            c["center_mm"] = pt(c["center_mm"])
        elif "a_mm" in c:
            c["a_mm"] = pt(c["a_mm"])
            c["b_mm"] = pt(c["b_mm"])
        elif "origin_mm" in c:
            c["origin_mm"] = pt(c["origin_mm"])
    for anchor in source["anchors"]:
        anchor["a_mm"] = pt(anchor["a_mm"])
        anchor["b_mm"] = pt(anchor["b_mm"])
    return source


# ---------------------------------------------------------------------------
# Plan sources
# ---------------------------------------------------------------------------

def _rect_source(i: int, rng: random.Random) -> dict[str, Any]:
    """A rectangle split into 2-4 rooms by axis-aligned partition walls."""
    W = 8000 + (i % 3) * 1000
    H = 6000 + ((i // 3) % 3) * 1000
    # partition walls at DISTINCT x positions, kept clear of the perimeter
    # openings (north window + south door are centred at W//2), plus one
    # horizontal partition for variety.
    n_part = rng.choice([1, 2, 3])
    cx = W // 2
    candidates = [x for x in [3000, 4000, 5000, 6000, 7000] if abs(x - cx) >= 800]
    if len(candidates) < n_part:
        n_part = max(1, len(candidates))
    xs = rng.sample(candidates, n_part)
    parts = [{"id": f"P-{k + 1}", "x0": x, "y0": 0, "x1": x, "y1": H} for k, x in enumerate(xs)]
    if rng.random() < 0.5:
        y = rng.choice([2500, 3500, 4500])
        parts.append({"id": f"P-{len(parts) + 1}", "x0": 0, "y0": y, "x1": W, "y1": y})

    walls = [
        {"id": "W-S", "kind": "segment", "a_mm": [0, 0], "b_mm": [W, 0]},
        {"id": "W-E", "kind": "segment", "a_mm": [W, 0], "b_mm": [W, H]},
        {"id": "W-N", "kind": "segment", "a_mm": [0, H], "b_mm": [W, H]},
        {"id": "W-W", "kind": "segment", "a_mm": [0, 0], "b_mm": [0, H]},
    ]
    for p in parts:
        walls.append({"id": p["id"], "kind": "segment", "a_mm": [p["x0"], p["y0"]], "b_mm": [p["x1"], p["y1"]]})

    openings = []
    oid = 0
    for p in parts:
        if p["x0"] == p["x1"]:  # vertical partition -> door
            y = 1500
            openings.append({"id": f"O-{oid}", "type": "door", "host_id": p["id"],
                             "a_mm": [p["x0"], y], "b_mm": [p["x0"], y + 900], "width_mm": 900})
            oid += 1
        else:  # horizontal partition -> door
            x = 1500
            openings.append({"id": f"O-{oid}", "type": "door", "host_id": p["id"],
                             "a_mm": [x, p["y0"]], "b_mm": [x + 900, p["y0"]], "width_mm": 900})
            oid += 1
    openings.append({"id": f"O-{oid}", "type": "window", "host_id": "W-N",
                     "a_mm": [W // 2 - 600, H], "b_mm": [W // 2 + 600, H], "width_mm": 1200})
    oid += 1
    openings.append({"id": f"O-{oid}", "type": "door", "host_id": "W-S",
                     "a_mm": [W // 2 - 450, 0], "b_mm": [W // 2 + 450, 0], "width_mm": 900})
    oid += 1

    rooms = _rooms_from_rect(W, H, parts)

    anchors = _plan_anchors(W, H)

    clutter = []
    if i % 3 == 0:
        bx = W // 4 - (W // 4) % 500
        by = H // 3 - (H // 3) % 500
        cx = W // 2 - (W // 2) % 500
        cy = H // 2 - (H // 2) % 500
        clutter = [
            {"id": "C-1", "kind": "rectangle", "box_mm": [bx, by, bx + 1000, by + 800]},
            {"id": "C-2", "kind": "circle", "center_mm": [cx, cy], "radius_mm": 400},
        ]

    return _assemble(W, H, walls, openings, rooms, anchors, clutter, topology=_topology(rooms, openings, walls))


def _rooms_from_rect(W: int, H: int, parts: list[dict]) -> list[dict]:
    # Split the rectangle by the partition walls; produce one polygon per cell
    # of the grid induced by the partitions (simple axis-aligned cells).
    xs = sorted({0, W} | {p["x0"] for p in parts if p["x0"] == p["x1"]})
    ys = sorted({0, H} | {p["y0"] for p in parts if p["y0"] == p["y1"]})
    rooms = []
    rid = 0
    for a in range(len(xs) - 1):
        for b in range(len(ys) - 1):
            x0, x1, y0, y1 = xs[a], xs[a + 1], ys[b], ys[b + 1]
            if x1 - x0 < 1000 or y1 - y0 < 1000:
                continue
            rooms.append({"id": f"R-{rid}", "polygon_mm": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]})
            rid += 1
    return rooms


def _arc_source(i: int, rng: random.Random) -> dict[str, Any]:
    """A rectangle whose east wall is replaced by an apse arc (like FX1)."""
    k = (i - 3) // 4  # arc fixture ordinal 0..14 -> unique (W,H,R)
    W = 6000 + (k % 3) * 1000
    H = 6000 + ((k // 3) % 3) * 1000
    R = 1000 + ((k // 9) % 2) * 500
    walls = [
        {"id": "W-S", "kind": "segment", "a_mm": [0, 0], "b_mm": [W, 0]},
        {"id": "W-E-A", "kind": "segment", "a_mm": [W, 0], "b_mm": [W, H // 2 - R]},
        {"id": "W-APSE", "kind": "circular_arc", "center_mm": [W, H // 2], "radius_mm": R, "start_deg": -90, "end_deg": 90},
        {"id": "W-E-B", "kind": "segment", "a_mm": [W, H // 2 + R], "b_mm": [W, H]},
        {"id": "W-N", "kind": "segment", "a_mm": [0, H], "b_mm": [W, H]},
        {"id": "W-W", "kind": "segment", "a_mm": [0, 0], "b_mm": [0, H]},
        {"id": "W-PV", "kind": "segment", "a_mm": [W // 2, 0], "b_mm": [W // 2, H]},
    ]
    openings = [
        {"id": "O-0", "type": "door", "host_id": "W-S", "a_mm": [W // 2 - 450, 0], "b_mm": [W // 2 + 450, 0], "width_mm": 900},
        {"id": "O-1", "type": "door", "host_id": "W-PV", "a_mm": [W // 2, 1500], "b_mm": [W // 2, 2400], "width_mm": 900},
        {"id": "O-2", "type": "window", "host_id": "W-N", "a_mm": [W // 2 - 600, H], "b_mm": [W // 2 + 600, H], "width_mm": 1200},
        {"id": "O-3", "type": "window", "host_id": "W-APSE", "start_deg": -22.5, "end_deg": 22.5, "width_basis": "arc_length"},
    ]
    rooms = [
        {"id": "R-W", "polygon_mm": [[0, 0], [W // 2, 0], [W // 2, H], [0, H]]},
        {"id": "R-E", "boundary_refs": ["W-S", "W-E-A", "W-APSE", "W-E-B", "W-N", "W-PV"]},
    ]
    anchors = [
        {"id": "A-N", "a_mm": [0, H + 750], "b_mm": [5000, H + 750], "real_length_m": 5.0, "placement_region": "north_margin"},
        {"id": "A-E", "a_mm": [W + R + 1000, 0], "b_mm": [W + R + 1000, 5000], "real_length_m": 5.0, "placement_region": "east_margin"},
        {"id": "A-D", "a_mm": [W + R + 1000, 6000], "b_mm": [W + R + 1600, 6800], "real_length_m": 1.0, "placement_region": "northeast_margin"},
    ]
    return _assemble(W, H, walls, openings, rooms, anchors, [], topology=[{"a": "R-W", "b": "R-E", "opening_ids": ["O-1"]}])


def _diag_source(i: int, rng: random.Random) -> dict[str, Any]:
    """A rectangle with a 3-4-5 diagonal wall in the north-west corner."""
    W, H = {
        4: (8000, 7000), 9: (8500, 7500), 14: (9000, 8000),
        24: (8500, 7000), 29: (9500, 7500), 34: (8000, 7500),
        44: (9000, 7000), 49: (9500, 8000), 54: (8500, 8000),
    }[i]
    walls = [
        {"id": "W-S", "kind": "segment", "a_mm": [0, 0], "b_mm": [W, 0]},
        {"id": "W-E", "kind": "segment", "a_mm": [W, 0], "b_mm": [W, H]},
        {"id": "W-N", "kind": "segment", "a_mm": [2000, H], "b_mm": [W, H]},
        {"id": "W-DIAG", "kind": "segment", "orientation": "diagonal_3_4_5", "a_mm": [0, H - 1500], "b_mm": [2000, H]},
        {"id": "W-W", "kind": "segment", "a_mm": [0, 0], "b_mm": [0, H - 1500]},
        {"id": "W-PV", "kind": "segment", "a_mm": [W // 2, 0], "b_mm": [W // 2, H]},
    ]
    openings = [
        {"id": "O-0", "type": "door", "host_id": "W-S", "a_mm": [W // 2 - 450, 0], "b_mm": [W // 2 + 450, 0], "width_mm": 900},
        {"id": "O-1", "type": "door", "host_id": "W-PV", "a_mm": [W // 2, 2500], "b_mm": [W // 2, 3400], "width_mm": 900},
        {"id": "O-2", "type": "window", "host_id": "W-E", "a_mm": [W, H // 2 - 600], "b_mm": [W, H // 2 + 600], "width_mm": 1200},
        {"id": "O-3", "type": "window", "host_id": "W-DIAG", "a_mm": [600, H - 1050], "b_mm": [1560, H - 330], "width_mm": 1200},
    ]
    rooms = [
        {"id": "R-W", "polygon_mm": [[0, 0], [W // 2, 0], [W // 2, H], [2000, H], [0, H - 1500]]},
        {"id": "R-E", "polygon_mm": [[W // 2, 0], [W, 0], [W, H], [W // 2, H]]},
    ]
    anchors = _plan_anchors(W, H)
    return _assemble(W, H, walls, openings, rooms, anchors, [], topology=[{"a": "R-W", "b": "R-E", "opening_ids": ["O-1"]}])


def _point_in_polygon(px: float, py: float, poly: list[list[int]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _topology(rooms: list[dict], openings: list[dict], walls: list[dict]) -> list[dict]:
    """Adjacency edges: each door connects the room on either side of its host wall."""
    walls_by_id = {w["id"]: w for w in walls}
    edges = []
    for o in openings:
        if o.get("type") != "door" or "a_mm" not in o:
            continue
        host = walls_by_id.get(o["host_id"])
        if not host:
            continue
        mx = (o["a_mm"][0] + o["b_mm"][0]) / 2.0
        my = (o["a_mm"][1] + o["b_mm"][1]) / 2.0
        wx = host["b_mm"][0] - host["a_mm"][0]
        wy = host["b_mm"][1] - host["a_mm"][1]
        L = math.hypot(wx, wy) or 1.0
        nx, ny = -wy / L, wx / L
        sides = []
        for s in (400.0, -400.0):
            px, py = mx + nx * s, my + ny * s
            for r in rooms:
                if "polygon_mm" in r and _point_in_polygon(px, py, r["polygon_mm"]):
                    sides.append(r["id"])
                    break
        if len(sides) == 2 and sides[0] != sides[1]:
            edges.append({"a": sides[0], "b": sides[1], "opening_ids": [o["id"]]})
    return edges


def _assemble(W, H, walls, openings, rooms, anchors, clutter, topology) -> dict[str, Any]:
    return {
        "document": "fxx-source-geometry",
        "version": "1.0.0",
        "origin": "project_owned_deterministic_synthetic",
        "rights": "project-owned; no third-party bytes or assets",
        "coordinate_system": {"units": "mm", "origin": "canvas_bottom_left", "y_axis": "up"},
        "canvas": {"width_px": WIDTH_PX, "height_px": HEIGHT_PX, "mm_per_px": MM_PER_PX},
        "walls": walls,
        "openings": openings,
        "rooms": rooms,
        "topology": topology,
        "clutter": clutter,
        "anchors": anchors,
    }


# ---------------------------------------------------------------------------
# Corpus build
# ---------------------------------------------------------------------------

def _truth(source: dict[str, Any], source_hash: str) -> dict[str, Any]:
    walls = []
    for wall in source["walls"]:
        record = dict(wall)
        if wall["kind"] == "segment":
            record["a_px"] = F1._px(wall["a_mm"])
            record["b_px"] = F1._px(wall["b_mm"])
        else:
            record["tessellation_rule"] = {"segments": 32, "max_sagitta_px": 0.5}
            record["vertices_mm"] = [[round(v, 9) for v in p] for p in F1._arc_points(wall["center_mm"], wall["radius_mm"], wall["start_deg"], wall["end_deg"])]
        walls.append(record)
    return {
        "document": "fxx-frozen-independent-truth",
        "version": "1.0.0",
        "source_sha256": source_hash,
        "derived_only_from": ["fxx-source-geometry.json"],
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
        a_px, b_px = F1._px(anchor["a_mm"]), F1._px(anchor["b_mm"])
        span_px = math.hypot(b_px[0] - a_px[0], b_px[1] - a_px[1])
        records.append({**anchor, "a_px": a_px, "b_px": b_px, "span_px": span_px,
                        "provenance": f"fxx-source-geometry.json#anchors/{anchor['id']}",
                        "derived_m_per_px": anchor["real_length_m"] / span_px})
    return {
        "document": "fxx-authoritative-scale-anchors",
        "version": "1.0.0",
        "source_sha256": source_hash,
        "raster_sha256": raster_hash,
        "truth_sha256": truth_hash,
        "anchors": records,
    }


def _render(source: dict[str, Any]) -> Image.Image:
    # Reuse FX1's renderer, which is keyed on the generic source dict structure.
    return F1._render(source)


def build_one(out: Path, i: int) -> dict[str, Any]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)  # fail fast on a rerun into an existing dir
    rng = _rng(i)
    kind = "arc" if i % 4 == 3 else ("diag" if i % 5 == 4 else "rect")
    if kind == "arc":
        source = _arc_source(i, rng)
    elif kind == "diag":
        source = _diag_source(i, rng)
    else:
        source = _rect_source(i, rng)
    _shift(source, OX, OY)

    source_path = out / "fxx-source-geometry.json"
    write_json_exclusive(source_path, source, create_parents=False)
    source_hash = sha256_file(source_path)

    raster_path = out / "fxx.png"
    _render(source).save(raster_path, format="PNG", optimize=False, compress_level=6)
    raster_hash = sha256_file(raster_path)

    truth = _truth(source, source_hash)
    truth_path = out / "fxx-truth.json"
    write_json_exclusive(truth_path, truth, create_parents=False)
    truth_hash = sha256_file(truth_path)

    anchors_path = out / "fxx-scale-anchors.json"
    write_json_exclusive(anchors_path, _anchors(source, source_hash, raster_hash, truth_hash), create_parents=False)

    rights_path = out / "fxx-rights-provenance.json"
    write_json_exclusive(rights_path, {
        "origin": "project_owned_generated",
        "third_party_bytes": 0,
        "third_party_assets": [],
        "network_acquisition": "none",
        "license_statement": "This synthetic fixture is project-created; no repository-wide distribution-license claim is made.",
        "local_only": True,
    }, create_parents=False)

    files = {p.name: sha256_file(p) for p in sorted(out.iterdir())}
    manifest = {
        "document": "fxx-deterministic-replay-manifest",
        "version": "1.0.0",
        "kind": kind,
        "files": files,
        "replay_hash": F1._canonical_hash(files),
        "dependency_policy": "existing local environment only; no install performed",
        "recognition_or_scoring_performed": False,
    }
    write_json_exclusive(out / "fxx-manifest.json", manifest, create_parents=False)
    # Verification pass: every manifest-bound payload file must hash-match the
    # on-disk bytes (a partial/stale write must fail the build, not ship silently).
    for name, digest in files.items():
        if sha256_file(out / name) != digest:
            raise ValueError(f"corpus fixture {out.name}: hash mismatch on {name}")
    return {"id": f"f{i:02d}", "kind": kind, "walls": len(source["walls"]),
            "rooms": len(source["rooms"]), "openings": len(source["openings"]),
            "clutter": len(source["clutter"])}


def build_corpus(root: Path) -> dict[str, Any]:
    root = Path(root)
    index = []
    for i in range(COUNT):
        d = root / f"f{i:02d}"
        info = build_one(d, i)
        index.append(info)
    summary = {
        "document": "wp4-r0-corpus-index",
        "count": COUNT,
        "seed": SEED,
        "fixtures": index,
        "by_kind": {
            k: len([x for x in index if x["kind"] == k])
            for k in ("rect", "arc", "diag")
        },
    }
    write_json_exclusive(root / "corpus-index.json", summary, create_parents=False)
    return summary


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = build_corpus(args.out)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
