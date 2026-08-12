from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
import tracemalloc
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter, __version__ as pillow_version

SOFT_MEMORY_LIMIT_BYTES = 1_610_612_736  # 1.5 GiB
RUNTIME_LIMIT_SECONDS = 60.0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _deterministic_probe(image_path: Path) -> dict[str, Any]:
    with Image.open(image_path) as image:
        grayscale = image.convert("L")
        width, height = grayscale.size
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        pixels = np.asarray(grayscale, dtype=np.uint8)
        edge_pixels = np.asarray(edges, dtype=np.uint8)
        # Diagnostic-only morphology-free measurements. They intentionally make
        # no geometry/accuracy claim without independent truth.
        payload = {
            "width_px": width,
            "height_px": height,
            "dark_pixels_lt_64": int(np.count_nonzero(pixels < 64)),
            "dark_pixels_lt_128": int(np.count_nonzero(pixels < 128)),
            "edge_pixels_gt_64": int(np.count_nonzero(edge_pixels > 64)),
            "grayscale_sha256": hashlib.sha256(pixels.tobytes()).hexdigest(),
            "edge_sha256": hashlib.sha256(edge_pixels.tobytes()).hexdigest(),
        }
    payload["canonical_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def evaluate_fixture(image_path: Path, manifest_path: Path, replays: int = 2) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_hash = _sha256(image_path)
    expected_hash = manifest.get("rights", {}).get("source_sha256")
    base = {
        "source": {"sha256": actual_hash, "path_recorded": False},
        "rights": manifest.get("rights", {}),
        "accuracy_evaluable": False,
        "yield_evaluable": False,
        "runtime": {"limit_seconds": RUNTIME_LIMIT_SECONDS, "replays_completed": 0},
        "memory": {"soft_limit_bytes": SOFT_MEMORY_LIMIT_BYTES},
        "environment": {
            "python": platform.python_version(),
            "pillow": pillow_version,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
    }
    if expected_hash != actual_hash:
        return {**base, "decision": "STOP", "blockers": ["SOURCE_HASH_MISMATCH"]}

    blockers: list[str] = []
    truth = manifest.get("truth", {})
    if not truth.get("independent") or not truth.get("path"):
        blockers.append("INDEPENDENT_TRUTH_MISSING")
    if len(manifest.get("scale_anchors", [])) < 2:
        blockers.append("TWO_AUTHORITATIVE_SCALE_ANCHORS_MISSING")

    durations: list[float] = []
    probes: list[dict[str, Any]] = []
    tracemalloc.start()
    for _ in range(replays):
        started = time.perf_counter()
        probes.append(_deterministic_probe(image_path))
        durations.append(time.perf_counter() - started)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    identical = all(probe == probes[0] for probe in probes[1:])
    if not identical:
        blockers.append("NONDETERMINISTIC_DIAGNOSTIC_OUTPUT")
    if max(durations) >= RUNTIME_LIMIT_SECONDS:
        blockers.append("RUNTIME_LIMIT_EXCEEDED")
    if peak >= SOFT_MEMORY_LIMIT_BYTES:
        blockers.append("SOFT_MEMORY_LIMIT_EXCEEDED")

    return {
        **base,
        "decision": "STOP" if blockers else "GO_TO_LOCKED_CORPUS_ONLY",
        "blockers": blockers,
        "runtime": {
            "limit_seconds": RUNTIME_LIMIT_SECONDS,
            "replays_completed": replays,
            "seconds": durations,
            "median_seconds": statistics.median(durations),
            "max_seconds": max(durations),
        },
        "memory": {"soft_limit_bytes": SOFT_MEMORY_LIMIT_BYTES, "peak_tracemalloc_bytes": peak},
        "determinism": {
            "replays": replays,
            "identical": identical,
            "canonical_sha256": [probe["canonical_sha256"] for probe in probes],
        },
        "diagnostic_probe": probes[0],
        "accuracy_note": "Not scored: no independent truth and/or two authoritative scale anchors.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--replays", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate_fixture(args.image, args.manifest, args.replays)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["decision"] != "STOP" else 3


if __name__ == "__main__":
    raise SystemExit(main())
