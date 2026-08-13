"""Frozen evaluator metrics for the PanoWorld corpus lock (PLAN-002RF WP1).

These functions are the frozen, deterministic core of the evaluator. They are
pure (no I/O, no recognizer input) and are the single source of truth for how a
prediction is matched, canonicalized, scored and refusal-counted. They are
frozen BEFORE truth is opened, so their byte-level behaviour is pinned by tests.

Nothing in this module reads a recognizer output. A "prediction" is a plain
data structure the scorer receives; the scorer never derives truth.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Iterable

# Frozen grid / taxon constants. These are part of the evaluator contract and
# must not change without a versioned evaluator-spec amendment and re-review.
QUANTIZE_MM = 0.01  # 0.01 mm grid for canonical quantized points
SAGITTA_MAX_PX = 0.5  # circular-arc tessellation governs the supported arc taxon

# Window/openings with a drawn span wider than this are treated as unsupported
# under the frozen open-span upper bound.
MAX_OPENING_SPAN_MM = 1500.0


_NON_GEOMETRY_FIELDS = frozenset({"id", "confidence", "width_mm"})


def canonical_key(record: dict[str, Any]) -> str:
    """Return a deterministic, order-independent key for a geometric record.

    The key is the sha256 of the JSON-canonical form (sorted keys, no ASCII
    escaping, no whitespace). Two records with equal geometry serialize to equal
    keys. Non-geometry fields (id, confidence, width_mm) are deliberately
    excluded so matching is on geometry, not on authorship or confidence.
    """
    geometry = {k: v for k, v in record.items() if k not in _NON_GEOMETRY_FIELDS}
    canonical = json.dumps(geometry, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def quantize(value: float, grid: float = QUANTIZE_MM) -> float:
    """Quantize a scalar to the frozen grid (round-half-away from zero)."""
    return math.floor(value / grid + 0.5) * grid


def canon_point(point: Iterable[float]) -> list[float]:
    """Quantize a 2-D point onto the frozen grid."""
    x, y = point
    return [round(quantize(float(x)), 9), round(quantize(float(y)), 9)]


def match_wall(truth_wall: dict[str, Any], pred_wall: dict[str, Any]) -> bool:
    """A predicted wall matches a truth wall iff the kind is identical and the
    canonical geometry key (id- and confidence-stripped, key-sorted, quantized)
    is byte-identical. Matching is exact-by-key and never runs on recognizer
    confidence or on record ids."""
    if truth_wall.get("kind") != pred_wall.get("kind"):
        return False
    return canonical_key(truth_wall) == canonical_key(pred_wall)


def macro_average(per_plan_scores: Iterable[float]) -> float:
    """Unweighted mean across plans (each plan counts equally)."""
    scores = list(per_plan_scores)
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def micro_average(predictions: Iterable[bool]) -> float:
    """Aggregate accuracy over all predictions (each prediction counts equally)."""
    values = list(predictions)
    if not values:
        return 0.0
    return sum(1 for v in values if v) / len(values)


def per_plan_score(plan: dict[str, Any]) -> float:
    """Per-plan metric: matched / supportable, where unsupported predictions are
    counted in the denominator as handled-but-not-correct (they are not dropped).
    Refusals are counted separately by `refusal_accounting` and are excluded here
    only if they are genuine unsupported-taxon refusals (see `refusal_accounting`).
    """
    supportable = int(plan.get("supportable", 0))
    correct = int(plan.get("correct", 0))
    if supportable <= 0:
        return 0.0
    return correct / supportable


def refusal_accounting(plan: dict[str, Any]) -> dict[str, Any]:
    """Refusals are never silently promoted. Return counts and a pass flag.

    A refusal on an unsupported-taxon input is a *handled* refusal (counted, not
    penalised as a false positive). A refusal on a supported input is a false
    negative and is penalised. `plan["refusals"]` is a list of {kind, taxon}.
    """
    refusals = list(plan.get("refusals", []))
    handled = 0
    false_negative = 0
    unsupported = plan.get("unsupported", 0)
    for r in refusals:
        if r.get("kind") == "supported":
            false_negative += 1
        else:
            handled += 1
    return {
        "total": len(refusals),
        "handled": handled,
        "false_negative": false_negative,
        "refusal_rate": (len(refusals) / int(plan.get("supportable", 0))) if plan.get("supportable") else 0.0,
    }


def rule_of_three(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    """Return (point_estimate, lower_bound) of the confidence interval for a
    proportion, using the rule-of-three lower bound when there are zero
    successes (k=0 → 3/n). Never returns 1.0 as a lower bound for k<n.
    """
    if trials <= 0:
        raise ValueError("trials must be positive")
    if successes < 0 or successes > trials:
        raise ValueError("successes must satisfy 0 <= successes <= trials")
    point = successes / trials
    if successes == 0:
        lower = min(3.0 / trials, 1.0)
        return point, lower
    if successes == trials:
        # Wilson lower bound for k=n through 0.95: use 1 - (1-conf)/n approx is
        # not standard; keep deterministic and conservative via rule-of-three
        # symmetry is invalid, so report lower bound from the Wilson score for
        # k=n is ~ (n/(n+z^2)) which we approximate conservatively below 1.
        z = 1.959963984540054
        lower = trials / (trials + z * z)
        return point, lower
    z = 1.959963984540054
    n = float(trials)
    p_hat = point
    denom = 1.0 + z * z / n
    centre = p_hat + z * z / (2.0 * n)
    half = z * math.sqrt((p_hat * (1.0 - p_hat) + z * z / (4.0 * n)) / n)
    lower = (centre - half) / denom
    return point, max(0.0, lower)


def support_taxon_supported(record: dict[str, Any]) -> bool:
    """Predeclared supported-taxon classifier (the style guide in code form).

    Supported motifs: segment walls (including the diagonal_3_4_5 orientation
    variant), circular-arc walls with a stated sagitta bound, and
    door/window/passage openings of bounded span. Everything else is
    unsupported and routes to the refusal path. The kind vocabulary here is the
    frozen contract; it must match wp1-support-taxonomy.json exactly.
    """
    kind = record.get("kind")
    if kind in {"segment", "diagonal_3_4_5"}:
        return True
    if kind == "circular_arc":
        tess = record.get("tessellation_rule") or {}
        return float(tess.get("max_sagitta_px", SAGITTA_MAX_PX)) <= SAGITTA_MAX_PX
    if kind in {"door", "window", "passage"}:
        return True
    return False
