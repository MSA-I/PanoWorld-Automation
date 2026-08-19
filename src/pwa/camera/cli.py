"""CLI for PLAN-004 local camera planning."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pwa.camera.run_builder import build_camera_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--source-geometry", required=True)
    parser.add_argument("--cam-run-id", required=True)
    args = parser.parse_args(argv)
    try:
        result = build_camera_run(
            runs_root=Path(args.runs_root),
            source_geometry=Path(args.source_geometry),
            cam_run_id=args.cam_run_id,
        )
        if result.diagnostic and result.diagnostic.get("outcome") == "operational":
            print(json.dumps(result.diagnostic, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    except Exception:
        return 2
    return result.cli_exit


if __name__ == "__main__":
    raise SystemExit(main())