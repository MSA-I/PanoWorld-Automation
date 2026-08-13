# HANDOFF — WP2 to WP3 (PLAN-002RF)

- HANDOFF_ID: `HANDOFF-PLAN-002RF-WP2-to-WP3`
- Producer: `t_0fc0a9e4` (panoworld profile), implementer `deepseek/deepseek-v4-pro-0813` via `openrouter`
- Consumer: `t_aa5fb2fb` (WP3) — NOT yet authorized; human `needs_input` gate
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Checkpoint: `6201705` (evidence-bound index against this exact HEAD; see below)

## What is locked (frozen, hash-bound)

- Contracts bundle version `1.3.0` (single source of truth: `src/pwa/contracts.py`).
- `floorplan_parse` 1.2.0 schema (additive): `source_class` enum (`cad_exact`/`raster_auto`/`annotation`/`dxf`);
  wall `kind` (`segment`|`circular_arc`) + `arc` sub-object; sourced `thickness_m`; room `area_m2`;
  opening `type` + `passage`. All additive fields OPTIONAL → historical 1.0.0/1.1.0 docs remain valid.
- `floorplan_review` 1.0.0 schema (new): immutable review-chain artifact.
- Frozen recognition vocabulary + invariants (`src/pwa/floorplan/recognition.py`, pure/no I/O):
  `SOURCE_CLASSES`, `PRODUCT_SOURCE_CLASSES`, `arc_invariants`, `check_thickness`,
  `check_passage_span` (3.0 m), `polygon_area_m2`, `ReviewHead` lineage + `supersede`.
- Append-only blocking codes (`contracts/error_codes.md`): `RECOGNITION_*` / `REVIEW_*` /
  `SCHEMA_VERSION_*`, all `error`, append-only.
- `pwa.contracts.contract_rejection_reason` — machine-readable old-consumer rejection.
- Historical 1.0.0/1.1.0 schemas byte-pinned (SHA-256 in tests).

## Verification (fresh, authorized commands)

- `tests/unit/test_wp2_contracts.py` → 38/38 pass.
- Full suite (excluding pre-existing `test_wp0_cpu_feasibility.py` collection error) → 431 passed, 2 warnings, exit 0.
- Independent cross-provider read-only review → `felo/felo-chat` via OmniRoute `auto/best-coding`
  returned APPROVE (5× INFO); a deterministic read-only corroboration found 1 MINOR
  (arc example bulge-sign vs frozen ccw convention), now fixed and locked by a test.

## Consumer obligations / gates for WP3

- WP3 must NOT begin on this handoff alone. `t_aa5fb2fb` is a human `needs_input` gate;
  Moshe must explicitly approve WP3 before it becomes runnable.
- WP3 (first recognizer) emits against THESE frozen contracts, using the frozen WP1
  evaluator (`src/pwa/evaluator/metrics.py`) and the FX1 frozen truth. It must bind
  recognizer output to `source_class` = `cad_exact` or `raster_auto` (product authors only).
- Products must satisfy the recognition invariants (arc sagitta bound, bulge/sweep
  convention, sourced thickness, passage span ≤ 3.0 m) — fail-closed on violation.
- Review provenance must be recorded as `floorplan_review` 1.0.0 with immutable lineage.
- Routes remain default-off; WP3 activates NO route.

## Remaining explicit limits (carried forward, unchanged)

- No recognizer ran; accuracy/yield/runtime/peak remain NOT_EVALUABLE (unchanged).
- Pinned-environment proof pending. No merge-to-remote/push performed (local commits only).
- No H200/GPU/cloud/remote execution, no spend, no G7/G8, no Product C, no PLAN-003.
- Cross-provider review used the only live OmniRoute route (felo-chat); Anthropic/Opus
  direct routes and DDG proxy were unavailable this run (see `model-provenance.json`).
