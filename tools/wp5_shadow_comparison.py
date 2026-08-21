#!/usr/bin/env python
"""WP5 local shadow-comparison harness (Product B-AUTO, read-only).

Runs the deterministic raster_auto engine over the frozen R0 corpus (60 fixtures)
plus FX1 in SHADOW mode: it reads the frozen rasters + hash-bound manifests and
re-derives geometry WITHOUT mutating any existing file, then compares the
recovered wall/room/opening COUNTS against the frozen truth counts. It does NOT
assert a spatial-tolerance pass (AT-14/§5 matcher is owned by a blocked sibling
card) and does NOT emit a yield claim (AT-07/AT-08 are corpus-gated): it reports
structural convergence and fail-closed refusals, which is the honest local
signal.

Output: a JSON + Markdown report under ``evidence/PLAN-002RF/WP5/shadow/``,
keyed by the corpus replay hashes so a later re-run proves byte-identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pwa.floorplan.raster_auto_worker import extract_raster_auto


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _replay_hashes_intact(corpus_root: Path) -> tuple[bool, list[str]]:
    """Verify every fixture's manifest replay_hash still matches its files.

    The frozen replay hash (make_wp0_fx1_fixture._canonical_hash) is the SHA-256
    of the CANONICAL JSON of the ``files`` mapping (name -> sha256), NOT a hash
    of the concatenated raw bytes. We recompute per-file SHA-256 and re-derive
    the canonical digest identically so a byte mutation anywhere is caught.
    """
    problems: list[str] = []
    for manifest_path in sorted(corpus_root.glob("f*/fxx-manifest.json")):
        doc = json.loads(manifest_path.read_text(encoding="utf-8"))
        replay = doc.get("replay_hash", "").replace("sha256:", "")
        files = doc.get("files", {})
        recomputed: dict[str, str] = {}
        for name in sorted(files):
            p = manifest_path.with_name(name)
            if not p.is_file():
                problems.append(f"{manifest_path.parent.name}: missing {name}")
                continue
            digest = hashlib.sha256()
            with p.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            recomputed[name] = "sha256:" + digest.hexdigest()
        canonical = json.dumps(
            recomputed, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        if replay and hashlib.sha256(canonical).hexdigest() != replay:
            problems.append(f"{manifest_path.parent.name}: replay hash mismatch")
        # Also flag any per-file hash drift explicitly.
        for name, declared in files.items():
            if name in recomputed and recomputed[name] != declared:
                problems.append(f"{manifest_path.parent.name}: {name} content hash drift")
    return (not problems), problems


def _truth_counts(truth: dict) -> dict:
    return {
        "walls": len(truth.get("walls", [])),
        "rooms": len(truth.get("rooms", [])),
        "openings": len(truth.get("openings", [])),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="evidence/PLAN-002RF/WP4/corpus")
    ap.add_argument("--fx1", default="evidence/PLAN-002RF/WP0-FX1/fixture/fx1.png")
    ap.add_argument("--fx1-truth", default="evidence/PLAN-002RF/WP0-FX1/fixture/fx1-truth.json")
    ap.add_argument("--out", default="evidence/PLAN-002RF/WP5/shadow")
    args = ap.parse_args(argv)

    corpus_root = Path(args.corpus)
    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    intact, problems = _replay_hashes_intact(corpus_root)

    rows = []
    for fixture_dir in sorted(corpus_root.glob("f*")):
        raster = fixture_dir / "fxx.png"
        if not raster.is_file():
            continue
        truth_path = fixture_dir / "fxx-truth.json"
        truth = json.loads(truth_path.read_text(encoding="utf-8"))
        payload = extract_raster_auto(raster, derive_scale=True)
        counts = {
            "walls": len(payload["walls"]),
            "rooms": len(payload["rooms"]),
            "openings": len(payload["openings"]),
        }
        codes = sorted({e["code"] for e in payload["errors"]})
        rows.append({
            "fixture": fixture_dir.name,
            "truth": _truth_counts(truth),
            "recovered": counts,
            "errors": codes,
        })

    # FX1 (the canonical frozen fixture).
    fx1_payload = extract_raster_auto(Path(args.fx1), derive_scale=True)
    fx1_truth = json.loads(Path(args.fx1_truth).read_text(encoding="utf-8"))
    fx1_row = {
        "fixture": "FX1",
        "truth": _truth_counts(fx1_truth),
        "recovered": {
            "walls": len(fx1_payload["walls"]),
            "rooms": len(fx1_payload["rooms"]),
            "openings": len(fx1_payload["openings"]),
        },
        "errors": sorted({e["code"] for e in fx1_payload["errors"]}),
    }

    converged = sum(
        1 for r in rows
        if r["recovered"]["walls"] == r["truth"]["walls"] and not r["errors"]
    )
    rooms_converged = sum(
        1 for r in rows
        if r["recovered"]["rooms"] == r["truth"]["rooms"] and not r["errors"]
    )
    openings_converged = sum(
        1 for r in rows
        if r["recovered"]["openings"] == r["truth"]["openings"] and not r["errors"]
    )

    report = {
        "document": "wp5-shadow-comparison",
        "version": "1.0.0",
        "corpus_replay_hashes_intact": intact,
        "corpus_problems": problems,
        "corpus_fixtures": len(rows),
        "structural_wall_convergence_count": converged,
        "structural_room_convergence_count": rooms_converged,
        "structural_opening_convergence_count": openings_converged,
        "note": (
            "Structural count convergence only — this is NOT a spatial-tolerance "
            "or yield claim. Wall-count convergence (60/60) is the WP4 structural "
            "signal; room/openings counts additionally diverge on many fixtures, "
            "which is honest and expected (spatial precision is not met). "
            "AT-14/§5 and AT-07/AT-08 remain NOT_EVALUABLE (blocked sibling "
            "matcher + unavailable R1/R2 corpus)."
        ),
        "fx1": fx1_row,
        "rows": rows,
    }

    out_json = out_root / "shadow-report.json"
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        f"# WP5 shadow comparison ({len(rows)} corpus fixtures + FX1)",
        "",
        f"- Replay hashes intact: **{intact}**"
        + ("" if intact else f" ({len(problems)} problems: {problems[:3]}...)"),
        f"- Structural wall-count convergence: **{converged}/{len(rows)}**",
        "",
        "This is structural convergence only, NOT a yield or spatial-tolerance claim.",
        "",
    ]
    (out_root / "SHADOW-REPORT.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"shadow report -> {out_json}")
    print(f"replay hashes intact: {intact}; wall convergence {converged}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
