"""CLI for PLAN-002 local floorplan parsing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pwa.floorplan.builder import parse_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", required=True)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--parse-run-id", required=True)
    parser.add_argument("--annotation")
    args = parser.parse_args(argv)
    try:
        result = parse_run(
            runs_root=Path(args.runs_root),
            source_run=Path(args.source_run),
            parse_run_id=args.parse_run_id,
            annotation=Path(args.annotation) if args.annotation else None,
        )
        if result.diagnostic and result.diagnostic.get("residual_state") == "finalized_directory_left_behind":
            print(json.dumps(result.diagnostic, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    except Exception:
        # Defense in depth: parse_run() is expected to convert every reachable
        # failure into a CLI-2 ParseRunResult itself (see builder.py's
        # top-level except clauses). This guard exists only so a genuinely
        # unforeseen exception still surfaces as the documented operational
        # exit code instead of a raw traceback / stack trace to the user.
        return 2
    return result.cli_exit


if __name__ == "__main__":
    raise SystemExit(main())
