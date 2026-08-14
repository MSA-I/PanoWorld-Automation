# HANDOFF — WP3 to WP4 (PLAN-002RF)

- HANDOFF_ID: `HANDOFF-PLAN-002RF-WP3-to-WP4`
- Producer: `t_aa5fb2fb` (WP3 — Product A: cad_exact), panoworld profile, implementer
  `deepseek/deepseek-v4-pro-0813` via `openrouter`
- Consumer: `t_f2830a3e` (WP4) — NOT authorized; remains a human `needs_input` gate.
  WP3 closure does NOT authorize WP4. Moshe must explicitly approve continuation.
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Checkpoint: evidence-bound index against this exact HEAD (see `evidence-index.json`).

## What is delivered (Product A — cad_exact)

The first recognizer in the WP0–WP6 chain: an exact, deterministic, local-only CAD/DXF
parser emitting `floorplan_parse` 1.2.0 (`source_class: cad_exact`), scored against the
FX1 frozen truth via the frozen WP1 evaluator (exact-by-key canonical matching).

New modules (all additive; no historical byte changed):

- `src/pwa/floorplan/cad_exact_geometry.py` — pure arc/bulge/sagitta math: bulge↔sweep↔
  sagitta, deterministic arc tessellation (SAGITTA_MAX_PX 0.5, QUANTIZE_MM 0.01,
  bulge>0 == ccw).
- `src/pwa/floorplan/cad_exact_worker.py` — DXF extraction: native LINE walls (arbitrary
  angle), bounded ARC walls (`circular_arc` + arc sub-object), LWPOLYLINE rooms WITH bulge
  (tessellated per FX1 sagitta), sourced thickness (PWA XDATA), door/window/passage
  openings (passage ≤ 3.0 m), and fail-closed scale/topology/resource/security refusals.
- `src/pwa/floorplan/cad_exact.py` — emitter (m→quantized mm, `source_class: cad_exact`),
  FX1 truth scorer, deterministic SVG evidence renderer (native arc `A`-paths).

Capabilities implemented (scope from task body):
1. Native arbitrary-angle LINE walls.
2. Bounded circular arcs / bulges (native ARC + LWPOLYLINE bulge).
3. Exact quantized junctions / rooms / opening hosts.
4. Sourced thickness metadata (fail-closed `RECOGNITION_THICKNESS_MISSING` when absent).
5. Door / window / passage discrimination (passage span ≤ 3.0 m).
6. Fail-closed scale / topology / resource / security refusals (frozen finding codes
   + frozen `RECOGNITION_*` blocking codes).
7. Evidence rendering (SVG overlay with native arc paths).
8. Migration compatibility (historical dxf/annotation path byte-identical;
   `contract_rejection_reason` for old-consumer rejection).

## Verification (fresh, authorized commands, local-only)

- `tests/unit/test_wp3_cad_exact.py` → 36/36 pass (TDD RED→GREEN).
- Full suite (excluding pre-existing `test_wp0_cpu_feasibility.py` collection error)
  → 467 passed, 2 pre-existing warnings, exit 0.
- Independent cross-provider read-only review → `felo/felo-chat` via OmniRoute `auto`
  (identity proven from HTTP headers `x-omniroute-provider: felo`,
  `x-omniroute-model: felo-chat`) → APPROVE_WITH_FIXES; 1 CRITICAL + 1 MAJOR (same root
  cause: bulged LWPOLYLINE room edges) fixed under TDD and test-locked.

## Acceptance gates (task body) — all pass

- accuracy 1.000/1.000 against FX1 frozen truth (`test_extract_emit_score_fx1_mirrored_cad_is_1_0`).
- topology (degenerate/duplicate/self-intersecting/open/full-circle fail closed).
- determinism (parse + SVG byte-determinism).
- adversarial (non-zero-Z, SPLINE/INSERT/IMAGE/OLE2FRAME, unknown units, over-bound passage).
- resource (`MAX_DXF_BYTES` + `MAX_DXF_ENTITIES`).
- rollback (pure/idempotent parse, source immutable, route default-off).
- migration (historical `dxf_worker` still rejects ARC/bulge).

## Consumer obligations / gates for WP4

- WP4 must NOT begin on this handoff alone. `t_f2830a3e` remains a human `needs_input`
  gate until Moshe explicitly approves continuation.
- WP4 consumes this recognizer's `floorplan_parse` 1.2.0 output and the frozen WP1
  evaluator / FX1 truth; it must bind against these exact contracts and preserve the
  cross-provider review provenance (`floorplan_review` 1.0.0, immutable lineage).
- Routes remain default-off; neither WP3 nor WP4 activates any route.

## Remaining explicit limits (carried forward, unchanged)

- No route activated (default-off).
- No H200/GPU/cloud/remote execution, no spend, no G7/G8, no Product C, no PLAN-003.
- No dependency installed (ezdxf/pillow/numpy already in pyproject).
- No push/merge-to-remote (local commits only).
- Anthropic-Opus spatial review route unreachable this run; pre-approved fallback applied
  (felo-chat cross-provider review + deterministic corroboration); thresholds never weakened.
  See `model-provenance.json`.
- Pinned-environment proof remains pending (unchanged from WP0/WP1/WP2).
