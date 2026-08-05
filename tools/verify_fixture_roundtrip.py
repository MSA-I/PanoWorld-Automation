"""AC7 verification: prove the golden fixture survives a git round-trip
byte-identically (delete working copies, re-checkout from the index, re-hash
against fixture-metadata.json). Catches any CRLF/filter corruption."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "golden" / "panoworld_demo_subset"

if __name__ == "__main__":
    meta = json.loads((FIXTURE / "fixture-metadata.json").read_text(encoding="utf-8"))
    shutil.rmtree(FIXTURE)
    subprocess.run(
        ["git", "checkout", "--", "tests/golden/panoworld_demo_subset"],
        cwd=REPO_ROOT, check=True,
    )
    bad = []
    for rel, info in meta["files"].items():
        actual = "sha256:" + hashlib.sha256((FIXTURE / rel).read_bytes()).hexdigest()
        if actual != info["sha256"]:
            bad.append(rel)
    if bad:
        print(f"ROUNDTRIP FAILED for {len(bad)} files: {bad}")
        sys.exit(1)
    print(f"ROUNDTRIP OK: all {len(meta['files'])} fixture files byte-identical after git checkout")
