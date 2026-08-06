"""Evidence harness: run the test suite and leave append-only evidence.

Writes: junit.xml, coverage.xml, command.log (exact command + full output +
exit code + timestamp) and summary.md. Every invocation writes a unique
subdirectory so neither stale results nor previous evidence can be erased.

Usage: uv run python tools/run_checks.py --plan-id PLAN-001
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-id", default="PLAN-000")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"PLAN-\d{3}", args.plan_id):
        parser.error("--plan-id must match PLAN-###")
    started_dt = datetime.now(timezone.utc)
    evidence_run_id = started_dt.strftime("RUN-%Y%m%d-%H%M%S-%f")
    out = REPO_ROOT / "evidence" / args.plan_id / "test-results" / evidence_run_id
    out.mkdir(parents=True)

    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        f"--junitxml={out / 'junit.xml'}",
        "--cov=src/pwa",
        f"--cov-report=xml:{out / 'coverage.xml'}",
    ]
    started = started_dt.isoformat(timespec="seconds")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8")

    (out / "command.log").write_text(
        f"timestamp: {started}\ncwd: {REPO_ROOT}\ncommand: {' '.join(cmd)}\n"
        f"exit_code: {proc.returncode}\n\n--- stdout ---\n{proc.stdout}\n"
        f"--- stderr ---\n{proc.stderr}\n",
        encoding="utf-8",
    )

    # Summarize junit.xml into a human-readable table.
    lines = [f"# {args.plan_id} test evidence summary", "", f"- Run at: {started}",
             f"- Command: `{' '.join(cmd[2:])}` (via .venv python)",
             f"- Exit code: **{proc.returncode}**", ""]
    junit = out / "junit.xml"
    if junit.exists():
        suite = ET.parse(junit).getroot().find("testsuite")
        if suite is not None:
            lines += [
                f"- Tests: {suite.get('tests')} | Failures: {suite.get('failures')} | "
                f"Errors: {suite.get('errors')} | Skipped: {suite.get('skipped')} | "
                f"Time: {suite.get('time')}s", "",
                "| Test | Result |", "|---|---|",
            ]
            for case in suite.iter("testcase"):
                name = f"{case.get('classname')}.{case.get('name')}"
                if case.find("failure") is not None:
                    result = "FAIL"
                elif case.find("error") is not None:
                    result = "ERROR"
                elif case.find("skipped") is not None:
                    result = "SKIP"
                else:
                    result = "PASS"
                lines.append(f"| `{name}` | {result} |")
    lines.append("")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"evidence written to {out} (exit {proc.returncode})")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
