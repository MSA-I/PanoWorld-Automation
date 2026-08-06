"""Build one immutable PLAN-001 intake + fixture-package run."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pwa.packager import build_baseline_run  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--floorplan", required=True, type=Path)
    parser.add_argument("--style-reference", required=True, type=Path)
    parser.add_argument("--goal", choices=["conceptual", "precise"], default="conceptual")
    parser.add_argument("--units", choices=["m", "cm", "mm", "unknown"], default="unknown")
    parser.add_argument("--m-per-px", type=float)
    parser.add_argument("--fixture-layer", choices=["tiny", "golden"], default="tiny")
    parser.add_argument("--run-id")
    parser.add_argument("--runs-root", type=Path, default=REPO_ROOT / "runs")
    args = parser.parse_args(argv)
    try:
        run, complete = build_baseline_run(
            runs_root=args.runs_root,
            project_id=args.project_id,
            floorplan=args.floorplan,
            style_reference=args.style_reference,
            goal=args.goal,
            units=args.units,
            m_per_px=args.m_per_px,
            fixture_layer=args.fixture_layer,
            run_id=args.run_id,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(run)
    if not complete:
        print("input blocked: scale or units unknown", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
