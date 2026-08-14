"""Generate the WP3 evidence index bound to the current HEAD commit.

For each WP3 artifact, record its git blob id, byte count and sha256 so the
index is verifiable against Git (mirrors the WP1/WP2 evidence-index.json format).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CONTROLLING_PACKET = "95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7"

REL_PATHS = [
    "evidence/PLAN-002RF/WP3/WORKING-PLAN.md",
    "evidence/PLAN-002RF/WP3/RUN-REPORT.md",
    "evidence/PLAN-002RF/WP3/model-provenance.json",
    "evidence/PLAN-002RF/WP3/HANDOFF-WP3-to-WP4.md",
    "evidence/PLAN-002RF/WP3/review/independent-review-WP3.md",
    "evidence/PLAN-002RF/WP3/review/omniroute-review-full.txt",
    "evidence/PLAN-002RF/WP3/review/omniroute-headers.txt",
    "evidence/PLAN-002RF/WP3/review/review-brief.txt",
    "evidence/PLAN-002RF/WP3/test-results/wp3-targeted.log",
    "evidence/PLAN-002RF/WP3/test-results/wp3-full-suite.log",
    "src/pwa/floorplan/cad_exact_geometry.py",
    "src/pwa/floorplan/cad_exact_worker.py",
    "src/pwa/floorplan/cad_exact.py",
    "tests/unit/test_wp3_cad_exact.py",
]


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return result.stdout


def main() -> int:
    commit = _git("rev-parse", "HEAD").strip()
    entries = []
    for path in REL_PATHS:
        blob_id = _git("rev-parse", f"{commit}:{path}").strip()
        blob = subprocess.run(
            ["git", "show", f"{commit}:{path}"], cwd=REPO_ROOT, capture_output=True, check=True
        ).stdout
        sha = "sha256:" + hashlib.sha256(blob).hexdigest()
        entries.append({"path": path, "git_blob": blob_id, "sha256": sha, "bytes": len(blob)})
    index = {
        "document": "PLAN-002RF WP3 Product A cad_exact evidence index",
        "index_version": "1.0.0",
        "generated_against_commit": commit,
        "controlling_packet_sha256": CONTROLLING_PACKET,
        "entries": entries,
    }
    out = REPO_ROOT / "evidence/PLAN-002RF/WP3/evidence-index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries against {commit} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
