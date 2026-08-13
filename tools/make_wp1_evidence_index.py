"""Generate the WP1 evidence index bound to the current HEAD commit.

For each WP1 artifact, record its git blob id, byte count and sha256 so the
index is verifiable against Git (mirrors the WP0-FX1 evidence-index.json format).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CONTROLLING_PACKET = "95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7"

REL_PATHS = [
    "evidence/PLAN-002RF/WP1/WORKING-PLAN.md",
    "evidence/PLAN-002RF/WP1/rights-and-role-matrix.md",
    "evidence/PLAN-002RF/WP1/frozen-truth-matcher-canonicalization.md",
    "evidence/PLAN-002RF/WP1/model-provenance.json",
    "evidence/PLAN-002RF/WP1/lock/wp1-evaluator-spec.json",
    "evidence/PLAN-002RF/WP1/lock/wp1-support-taxonomy.json",
    "evidence/PLAN-002RF/WP1/lock/wp1-role-matrix.json",
    "evidence/PLAN-002RF/WP1/lock/wp1-split-manifest.json",
    "evidence/PLAN-002RF/WP1/lock/wp1-manifest.json",
    "src/pwa/evaluator/__init__.py",
    "src/pwa/evaluator/metrics.py",
    "tests/unit/test_wp1_evaluator.py",
    "tools/make_wp1_evaluator_lock.py",
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
        "document": "PLAN-002RF WP1 corpus and evaluator lock evidence index",
        "index_version": "1.0.0",
        "generated_against_commit": commit,
        "controlling_packet_sha256": CONTROLLING_PACKET,
        "entries": entries,
    }
    out = REPO_ROOT / "evidence/PLAN-002RF/WP1/evidence-index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries against {commit} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
