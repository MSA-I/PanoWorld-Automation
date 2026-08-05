"""Regenerate tests/golden/expected_report_demo_subset.json — the golden-master
snapshot of the validator's report on the vendored demo subset (PLAN-000 T9).
Run only when the validator's report shape intentionally changes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # package=false: no install

from pwa.validator import PackageValidator  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN = REPO_ROOT / "tests" / "golden" / "panoworld_demo_subset"
OUT = REPO_ROOT / "tests" / "golden" / "expected_report_demo_subset.json"

if __name__ == "__main__":
    report = PackageValidator(GOLDEN).validate().to_dict()
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
