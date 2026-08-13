# PLAN-002RF WP1 — Frozen hidden truth, matcher & canonicalization

- Task: `t_2f261417`
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`

This document records the *freeze* of hidden truth and the evaluator's core
semantics. It is a provenance/contract record, not a recognizer implementation.

## 1. Hidden truth freeze

- Frozen truth source: `evidence/PLAN-002RF/WP0-FX1/fixture/fx1-truth.json`
  (`sha256:f4f9c1de5d781c85c66179c00d0c6178a800d4a2c918dd5e09c4e30a5f3dcb9a`,
  git blob `ba969d7759458b962cb8bca63f5202942e150232`).
- Truth is derived **only** from `fx1-source-geometry.json`; `recognizer_inputs=[]`;
  `frozen_before_recognition: true`. It is bound by hash to source, raster and
  anchors (see `fx1-scale-anchors.json`).
- No truth is ever derived from recognizer output. WP1 does not open new truth:
  it locks the existing frozen truth into the evaluator contract.

## 2. Canonicalization & matcher (frozen)

Implemented in `src/pwa/evaluator/metrics.py` (byte-level pinned by
`tests/unit/test_wp1_evaluator.py`):

- **Canonical key** = sha256 of the JSON-canonical form (sorted keys, `:`/`,`
  separators, no ASCII escaping) with non-geometry fields (`id`, `confidence`,
  `width_mm`) stripped. Order- and id-independent; two equal geometries collide.
- **Matcher** = same `kind` AND byte-identical canonical key. Exact-by-key: no
  tolerance relaxation. Segments never match arcs; confidence never drives
  matching; record ids never drive matching.

## 3. Metrics (frozen)

- `macro` = unweighted mean of per-plan scores.
- `micro` = aggregate correct / all predictions.
- `per_plan` = correct / supportable; unsupported-taxon predictions are counted in
  the denominator (not dropped).
- Refusal accounting: a refusal on a supported input is a *false negative*
  (penalised); a refusal on an unsupported taxon is *handled* (counted, never
  promoted). Refusal rate is always reported separately.

## 4. Rule-of-three (frozen)

`rule_of_three(k, n, confidence=0.95)`:
- `k=0` → lower bound `3/n` (never reports a nonzero success lower bound from zero
  observations).
- `k=n` → lower bound strictly below 1.0 (Wilson lower bound for k=n).
- `0<k<n` → Wilson score interval lower bound.
- Rejects invalid inputs (`n<=0`, `k` outside `[0,n]`).

## 5. Support classifier / style guide (frozen)

See `lock/wp1-support-taxonomy.json`. Supported motifs (predeclared): wall segment,
circular-arc wall (`max_sagitta_px<=0.5`), door/window/passage openings,
`diagonal_3_4_5`. Out of scope (→ refusal): double-line hatched walls, text,
furniture, stairs, dotted grid, arbitrary diagonals, arcs without a stated sagitta
bound. The support classifier is predeclared BEFORE truth is opened; anything
outside it is `unsupported`.

The in-code form is `metrics.support_taxon_supported`, and the frozen machine
spec is `lock/wp1-evaluator-spec.json`.

## 6. Family splits & leakage (U-4/U-5/U-13)

`lock/wp1-split-manifest.json` declares disjoint families across three splits:

- `train`: `fx1_hall` (the FX1 source family)
- `dev`: `fx1_apse` (arc-topology variant)
- `blind`: `fx1_blind` (reserved; truth frozen, never scored during development)

Leakage controls (all enforced/pinned):
1. a family maps to exactly one split;
2. content-hash duplicate detection across the whole corpus (no near-duplicate
   family straddling splits);
3. the blind split's truth is never opened by development-time scorers.

## 7. Evaluator evidence binding

The frozen artifacts are hash-bound by `lock/wp1-manifest.json` (replay hash
`sha256:3ba9f37eaf5e9079c14edb56d7f12f135ef249108f2f7c9437bc034970d658fb`) and by
`evidence-index.json` (each artifact bound to a git blob + sha256 + byte count).

## 8. Boundary reaffirmation

No recognizer ran; `recognition_or_scoring_performed: false`. No corpus acquired.
No schema/contract/route changed. `recognition_runtime` / `peak_working_set` /
`accuracy` remain NOT_EVALUABLE until WP3/WP4 bind a recognizer to this frozen
evaluator.
