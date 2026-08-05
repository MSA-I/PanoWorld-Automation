"""Fetch the Layer-B golden fixture: the FULL closure of map_panoworld0.json
from PanoWorld's scene0000 (PLAN-000 T6, per ADR-0003).

- Viewpoints 0000/0001/0008/0011 (the map's complete reference closure —
  plan-reviewer finding C-1), 4 required files each, NO style panoramas.
- The commit SHA is resolved AT RUN TIME from upstream main (the repo has no
  tags/releases) and pinned in fixture-metadata.json together with per-file
  sha256 hashes.
- Sources: api.github.com (SHA resolution) + raw.githubusercontent.com only.
  stdlib urllib; nothing is executed; no model weights are touched.
- Also dumps PIL header info for the fetched images (verifies assumption A2:
  place_depth.png is 16-bit single-channel).

Usage: uv run python tools/fetch_golden_fixture.py [--force]
"""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

REPO = "jjrCN/PanoWorld"
SCENE = "examples/full_pipeline_demo_datas/scene0000"
VIEWPOINTS = ["0000", "0001", "0008", "0011"]
VP_FILES = ["extrinsics.txt", "place_image.png", "place_depth.png", "place_depth_scale.txt"]
DEST = Path(__file__).resolve().parents[1] / "tests" / "golden" / "panoworld_demo_subset"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "panoworld-automation-fixture-fetch"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> int:
    force = "--force" in sys.argv
    if DEST.exists() and not force:
        print(f"fixture already exists at {DEST}; use --force to refetch")
        return 0

    sha = json.loads(_get(f"https://api.github.com/repos/{REPO}/commits/main"))["sha"]
    print(f"pinned upstream commit: {sha}")
    base = f"https://raw.githubusercontent.com/{REPO}/{sha}/{SCENE}"

    rel_paths = ["map_panoworld0.json"] + [
        f"viewpoints/{vp}/{name}" for vp in VIEWPOINTS for name in VP_FILES
    ]

    files_meta: dict[str, dict] = {}
    for rel in rel_paths:
        data = _get(f"{base}/{rel}")
        if not data:
            raise RuntimeError(f"empty download: {rel}")
        target = DEST / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        files_meta[rel] = {
            "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
        print(f"  {rel}  {len(data):>10,} B")

    # Closure sanity: every map key/value must be among the fetched viewpoints.
    map_data = json.loads((DEST / "map_panoworld0.json").read_text(encoding="utf-8"))
    referenced = set(map_data) | {v for vals in map_data.values() for v in vals}
    missing = referenced - set(VIEWPOINTS)
    if missing:
        raise RuntimeError(f"fixture is NOT reference-closed; missing viewpoints: {sorted(missing)}")
    print(f"closure verified: map references {sorted(referenced)} == fetched set")

    # A2 verification: image headers.
    headers = {}
    for vp in VIEWPOINTS:
        for name in ("place_image.png", "place_depth.png"):
            with Image.open(DEST / "viewpoints" / vp / name) as im:
                headers[f"viewpoints/{vp}/{name}"] = {"mode": im.mode, "size": list(im.size)}
    for k, v in headers.items():
        print(f"  header {k}: mode={v['mode']} size={v['size']}")

    meta = {
        "source_repo": f"https://github.com/{REPO}",
        "scene": SCENE,
        "commit_sha": sha,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "license_note": "Upstream repo is Apache-2.0; see tests/golden/NOTICE and LICENSE-panoworld-upstream (ADR-0003).",
        "files": files_meta,
        "image_headers": headers,
    }
    (DEST / "fixture-metadata.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    total = sum(m["bytes"] for m in files_meta.values())
    print(f"done: {len(files_meta)} files, {total:,} bytes -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
