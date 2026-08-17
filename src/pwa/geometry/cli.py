"""CLI for PLAN-003 local geometry compilation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pwa.geometry.run_builder import build_geometry_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--source-parse", required=True)
    parser.add_argument("--geo-run-id", required=True)
    parser.add_argument("--export-blender", action="store_true", default=False)
    args = parser.parse_args(argv)
    try:
        result = build_geometry_run(
            runs_root=Path(args.runs_root),
            source_parse=Path(args.source_parse),
            geo_run_id=args.geo_run_id,
            export_blender=args.export_blender,
        )
        if result.diagnostic and result.diagnostic.get("outcome") == "operational":
            print(json.dumps(result.diagnostic, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    except Exception:
        return 2
    return result.cli_exit


if __name__ == "__main__":
    raise SystemExit(main())
