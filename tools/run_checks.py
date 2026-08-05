"""Evidence harness (PLAN-000 T10): run the test suite and leave verifiable
evidence under evidence/PLAN-000/test-results/.

Writes: junit.xml, coverage.xml, command.log (exact command + full output +
exit code + timestamp) and summary.md. The directory is wiped first so a stale
pass can never be silently reused (doc 04: fresh tests only).

Usage: uv run python tools/run_checks.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "evidence" / "PLAN-000" / "test-results"


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        f"--junitxml={OUT / 'junit.xml'}",
        "--cov=src/pwa",
        f"--cov-report=xml:{OUT / 'coverage.xml'}",
    ]
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8")

    (OUT / "command.log").write_text(
        f"timestamp: {started}\ncwd: {REPO_ROOT}\ncommand: {' '.join(cmd)}\n"
        f"exit_code: {proc.returncode}\n\n--- stdout ---\n{proc.stdout}\n"
        f"--- stderr ---\n{proc.stderr}\n",
        encoding="utf-8",
    )

    # Summarize junit.xml into a human-readable table.
    lines = ["# PLAN-000 test evidence summary", "", f"- Run at: {started}",
             f"- Command: `{' '.join(cmd[2:])}` (via .venv python)",
             f"- Exit code: **{proc.returncode}**", ""]
    junit = OUT / "junit.xml"
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
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"evidence written to {OUT} (exit {proc.returncode})")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
