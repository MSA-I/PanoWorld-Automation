# PLAN-002RF WP3 — RUN REPORT

- Task: `t_aa5fb2fb` (WP3 — Product A: cad_exact)
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Parent: `t_0fc0a9e4` (WP2) — DONE, evidence-bound.
- Governing policy: `docs/08` + `docs/10` + Moshe full-campaign authorization (2026-08-13).
- Implementer model: `deepseek/deepseek-v4-pro-0813` via `openrouter` (no fallback).
- Independent reviewer: `felo/felo-chat` via OmniRoute (cross-provider; identity from HTTP headers).
- Prior attempt: run 86 timed out (90/90 iterations) after authoring the initial code; run 87
  (this run) completed the missing acceptance gates + evidence + review + checkpoint.

## What was done

Product A (`cad_exact`) — the exact, deterministic, local-only CAD/DXF recognizer — emits
`floorplan_parse` 1.2.0 (`source_class: cad_exact`) against the frozen WP2 contracts, scored
against the FX1 frozen truth via the frozen WP1 evaluator (exact-by-key canonical matching).

New modules (all additive; no historical byte changed):
1. `src/pwa/floorplan/cad_exact_geometry.py` — pure arc/bulge/sagitta math (bulge↔sweep↔
   sagitta/tessellation), frozen to FX1 + WP1 evaluator (SAGITTA_MAX_PX 0.5, QUANTIZE_MM 0.01,
   bulge>0 == ccw).
2. `src/pwa/floorplan/cad_exact_worker.py` — in-process DXF extraction: native LINE walls
   (arbitrary angle), bounded ARC walls (`circular_arc` + arc sub-object), LWPOLYLINE rooms
   WITH bulge (tessellated per sagitta), sourced thickness (PWA XDATA), door/window/passage
   openings (passage ≤ 3.0 m), and fail-closed scale/topology/resource/security refusals.
3. `src/pwa/floorplan/cad_exact.py` — emitter (m→quantized mm, `source_class: cad_exact`,
   arc sub-object, thickness, opening host resolution), FX1 truth scorer, deterministic SVG
   evidence renderer (native arc `A`-paths).

## Acceptance gates (task body)

- **accuracy 1.000/1.000** — `test_extract_emit_score_fx1_mirrored_cad_is_1_0`: a DXF
  mirroring the 9 FX1 truth walls (8 segments + apse arc) scores 1.000 exactly.
- **topology** — degenerate wall, duplicate wall, self-intersecting room, open polygon,
  full-circle arc all fail closed.
- **determinism** — `test_fx1_cad_parse_is_deterministic` + SVG byte-determinism.
- **adversarial** — non-zero-Z walls/openings, SPLINE/INSERT/IMAGE/OLE2FRAME, unknown units,
  over-bound passage all refused.
- **resource** — `MAX_DXF_BYTES` + `MAX_DXF_ENTITIES` enforced in the worker (fail closed).
- **rollback** — parse is pure/idempotent; source never mutated; route stays default-off.
- **migration** — historical `dxf_worker` still rejects ARC/bulge (`test_historical_dxf_worker_still_rejects_arc_and_bulge`).

## TDD evidence

36 targeted tests in `tests/unit/test_wp3_cad_exact.py` (sections A–G), RED→GREEN:
- A: bulge/sweep/sagitta geometry; B: worker parse (arc wall, bulge room, passage, missing
  thickness, over-bound passage, unbounded arc); C: emitter + FX1 scorer;
  D: FX1 1.000 end-to-end + schema validity + determinism + scale/topology/resource refusal;
  E: migration; F: SVG evidence rendering; G: topology/resource/adversarial/rollback gates
  + bulged-edge tessellation.

## Findings closed (independent cross-provider review)

- CRITICAL-1 (felo-chat): bulged LWPOLYLINE room edges were not tessellated. Fixed via
  `_tessellate_polyline` (ezdxf bulge→arc + frozen `G.tessellate_arc`), TDD-locked.
- MAJOR-1 (same root cause): self-intersection + area on wrong geometry. Fixed by the same change.
- 6 additional LLM "MAJOR" findings were brief-artifacts (reviewer saw an abbreviated summary,
  not the code) and are documented + dismissed line-by-line in
  `review/independent-review-WP3.md`.

## Commands run (authorized, local-only)

```
uv run python -m pytest tests/unit/test_wp3_cad_exact.py -v        # RED then GREEN (27 -> 36)
uv run python -m pytest tests/ --ignore=tests/unit/test_wp0_cpu_feasibility.py   # full suite -> 467 passed
```

## Test results

- Targeted (WP3): **36 passed** — `test-results/wp3-targeted.log`
- Full suite: **467 passed, 2 warnings** (pre-existing Pillow deprecation) — `test-results/wp3-full-suite.log`
- `test_wp0_cpu_feasibility.py` excluded via `--ignore` (pre-existing collection error:
  `tools/__init__.py` missing; OUTSIDE WP3 scope, unchanged from WP1/WP2).

## Known limits / non-goals

- Routes remain default-off; WP3 activates NO route.
- No H200/GPU/cloud/remote execution, no spend, no G7/G8, no Product C, no PLAN-003.
- No dependency installed (ezdxf/pillow/numpy already in pyproject).
- No push/merge-to-remote (local commits only).
- Anthropic-Opus spatial review route unreachable this run; pre-approved fallback applied
  (felo-chat cross-provider review + deterministic corroboration). See `model-provenance.json`.
- Pinned-environment proof remains pending (unchanged from WP0/WP1/WP2).

## Verification checklist

- [x] accuracy 1.000/1.000 against FX1 frozen truth (exact-by-key)
- [x] topology gates (degenerate/duplicate/self-intersect/open/full-circle)
- [x] determinism (parse + SVG byte-identical)
- [x] adversarial refusals (nonzero-Z, security entities, unknown units, over-bound passage)
- [x] resource caps (bytes + entities)
- [x] rollback (pure/idempotent; source immutable; route default-off)
- [x] migration compatibility (historical dxf path unchanged)
- [x] independent cross-provider read-only review (APPROVE_WITH_FIXES, all fixes closed)
- [x] routes default-off; no activation

## Next dependency

WP3 closure does NOT authorize WP4 (`t_f2830a3e`). That card remains a human `needs_input`
gate until Moshe explicitly approves continuation.
