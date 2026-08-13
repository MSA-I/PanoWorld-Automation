"""Plan-002RF WP1 evaluator-lock tooling: frozen corpus + evaluator artifacts.

Mirrors make_wp0_fx1_fixture.py conventions: deterministic build, hash-bound
manifest, verify mode. Produces, under a target dir:

  wp1-evaluator-spec.json     frozen matcher/metrics/refusal/rule-of-three spec
  wp1-support-taxonomy.json   predeclared supported motifs + style guide
  wp1-role-matrix.json        roles + forbidden-overlap matrix
  wp1-split-manifest.json     train/dev/blind family splits
  wp1-manifest.json           deterministic replay manifest over the above

This tool locks the corpus/evaluator; it performs no recognition and acquires
nothing from the network.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pwa.files import sha256_file, write_json_exclusive

PAYLOAD_FILENAMES = frozenset({
    "wp1-evaluator-spec.json",
    "wp1-support-taxonomy.json",
    "wp1-role-matrix.json",
    "wp1-split-manifest.json",
})


def _canonical_hash(document: Any) -> str:
    encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _evaluator_spec() -> dict[str, Any]:
    return {
        "document": "wp1-frozen-evaluator-spec",
        "version": "1.0.0",
        "frozen_before_truth_opened": True,
        "recognizer_inputs": [],
        "matcher": {
            "unit": "mm",
            "kind_match_required": True,
            "match_by": "exact_canonical_geometry_key",
            "quantize_grid_mm": 0.01,
            "segments_never_match_arcs": True,
            "id_and_confidence_stripped_from_key": True,
            "no_tolerance_relaxation": True,
        },
        "canonicalization": {
            "quantize_grid_mm": 0.01,
            "key_ordering": "sorted_recursive",
            "id_excluded_from_key": True,
        },
        "metrics": {
            "macro": "unweighted mean of per-plan scores",
            "micro": "aggregate correct over all predictions",
            "per_plan": "correct / supportable (unsupported counted in denominator)",
            "supported_open_span_max_mm": 1500.0,
        },
        "refusal_accounting": {
            "false_negative_refusal_penalised": True,
            "handled_unsupported_refusal_counted_not_promoted": True,
            "refusal_rate_reported_separately": True,
        },
        "rule_of_three": {
            "confidence": 0.95,
            "zero_successes_lower_bound": "3/n",
            "never_reports_100_percent_for_partial_success": True,
        },
        "support_classifier": {
            "unsupported_routes_to_refusal": True,
            "confidence_is_diagnostic_only": True,
            "confidence_never_promotes_output": True,
        },
    }


def _support_taxonomy() -> dict[str, Any]:
    return {
        "document": "wp1-support-taxonomy-style-guide",
        "version": "1.0.0",
        "supported_motifs": [
            {"taxon": "wall_segment", "rule": "straight wall as a segment, any orientation"},
            {"taxon": "wall_circular_arc", "rule": "circular-arc wall with max_sagitta_px <= 0.5"},
            {"taxon": "opening_door", "rule": "door opening, span <= 1500 mm"},
            {"taxon": "opening_window", "rule": "window opening, span <= 1500 mm"},
            {"taxon": "opening_passage", "rule": "passage opening, span <= 3000 mm (frozen upper bound)"},
            {"taxon": "diagonal_3_4_5", "rule": "diagonal wall on the 3-4-5 lattice only"},
        ],
        "out_of_scope": [
            "double_line_hatched_walls",
            "text_annotations",
            "furniture_symbols",
            "stairs",
            "dotted_grid",
            "arbitrary_diagonals",
            "arc_walls_without_stated_sagitta_bound",
        ],
        "blind_split_never_scored_during_development": True,
    }


def _role_matrix() -> dict[str, Any]:
    roles = ["implementer", "labeler_a", "labeler_b", "adjudicator", "qa_delegate", "reviewer", "rights_owner"]
    # forbidden overlap: role_i cannot equal role_j. Rights Owner is a human and
    # may not double as any automated execution role except a pure signing role.
    forbidden = {
        "implementer": ["labeler_a", "labeler_b", "adjudicator", "qa_delegate", "reviewer"],
        "labeler_a": ["labeler_b", "adjudicator", "qa_delegate", "reviewer"],
        "labeler_b": ["adjudicator", "qa_delegate", "reviewer"],
        "adjudicator": ["qa_delegate", "reviewer"],
        "qa_delegate": ["reviewer"],
        "reviewer": [],
        "rights_owner": ["implementer", "labeler_a", "labeler_b", "adjudicator", "qa_delegate", "reviewer"],
    }
    holders = {
        "rights_owner": "Moshe (human)",
        "labeler_a": "deepseek-v4-pro session A (separate run)",
        "labeler_b": "deepseek-v4-pro session B (separate run)",
        "adjudicator": "deepseek-v4-pro session C (separate run)",
        "qa_delegate": "deepseek-v4-pro session D (separate run)",
        "reviewer": "read-only-first independent review session (separate run)",
        "implementer": "deepseek-v4-pro via openrouter (the WP1 producer session)",
    }
    return {
        "document": "wp1-role-matrix",
        "version": "1.0.0",
        "roles": roles,
        "forbidden_overlap": forbidden,
        "holders": holders,
        "overlap_is_fail_closed": True,
        "blind_labeler_rule": "neither labeler sees the other's verdict before recording its own",
        "rights_owner_only_human": True,
    }


def _split_manifest() -> dict[str, Any]:
    # Families are structural templates. FX1 is the initial family; the split
    # manifest declares how the synthetic corpus will be partitioned and what
    # leakage controls apply. No corpus is acquired from the network.
    return {
        "document": "wp1-split-manifest",
        "version": "1.0.0",
        "families": {
            "fx1_hall": {"split": "train", "source": "fx1-source-geometry.json"},
            "fx1_apse": {"split": "dev", "source": "arc topology derived from fx1"},
            "fx1_blind": {"split": "blind", "source": "reserved; truth frozen, never scored during development"},
        },
        "leakage_controls": [
            "family_in_exactly_one_split",
            "content_hash_duplicate_detection_across_corpus",
            "blind_split_truth_not_opened_by_development_tools",
        ],
        "train_families": ["fx1_hall"],
        "dev_families": ["fx1_apse"],
        "blind_families": ["fx1_blind"],
        "network_acquisition": "none",
    }


def build_lock(out: Path) -> Path:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    documents = {
        "wp1-evaluator-spec.json": _evaluator_spec(),
        "wp1-support-taxonomy.json": _support_taxonomy(),
        "wp1-role-matrix.json": _role_matrix(),
        "wp1-split-manifest.json": _split_manifest(),
    }
    for name, document in documents.items():
        write_json_exclusive(out / name, document, create_parents=False)
    files = {path.name: sha256_file(path) for path in sorted(out.iterdir())}
    manifest = {
        "document": "wp1-deterministic-replay-manifest",
        "version": "1.0.0",
        "files": files,
        "replay_hash": _canonical_hash(files),
        "dependency_policy": "existing local environment only; no install performed",
        "recognition_or_scoring_performed": False,
    }
    write_json_exclusive(out / "wp1-manifest.json", manifest, create_parents=False)
    report = verify_lock(out)
    if not report["valid"]:
        raise ValueError(f"generated invalid WP1 lock: {report}")
    return out


def verify_lock(package: Path) -> dict[str, Any]:
    package = Path(package)
    manifest_path = package / "wp1-manifest.json"
    if not manifest_path.is_file():
        return {"valid": False, "mismatches": ["wp1-manifest.json"], "files_verified": 0}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"valid": False, "mismatches": ["manifest_structure"], "files_verified": 0}
    files = manifest.get("files")
    replay_hash = manifest.get("replay_hash")
    if not isinstance(files, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in files.items()):
        return {"valid": False, "mismatches": ["manifest_structure"], "files_verified": 0}
    mismatches = []
    if set(files) != PAYLOAD_FILENAMES or any(Path(name).is_absolute() or Path(name).name != name for name in files):
        mismatches.append("manifest_file_scope")
    actual_names = {p.name for p in package.iterdir() if p.is_file()}
    if actual_names != PAYLOAD_FILENAMES | {"wp1-manifest.json"}:
        mismatches.append("unexpected_files")
    for name, expected in files.items():
        if name not in PAYLOAD_FILENAMES:
            continue
        path = package / name
        if not path.is_file() or sha256_file(path) != expected:
            mismatches.append(name)
    if _canonical_hash(files) != replay_hash:
        mismatches.append("replay_hash")
    return {"valid": not mismatches, "mismatches": sorted(set(mismatches)), "files_verified": len(files)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    if (args.out is None) == (args.verify is None):
        parser.error("provide exactly one of --out or --verify")
    if args.out is not None:
        build_lock(args.out)
        return 0
    report = verify_lock(args.verify)
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
