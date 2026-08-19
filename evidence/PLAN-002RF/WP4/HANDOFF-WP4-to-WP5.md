# HANDOFF — WP4 (Product B-AUTO) → next WP

- Task: `t_f2830a3e` (WP4 Product B-AUTO clean-raster engine) — BLOCKED closeout.
- Committing HEAD: `d66f0ad` (engine + re-freeze) + `bb58efd` (docs) + direction-fix
  commit (local only, no push).
- Next WP5 card `t_dfa6f24f` remains a human needs_input gate — WP4 completion does
  NOT authorize WP5.

## What was delivered

A deterministic, CPU-only, no-OCR, no-learned-model `raster_auto` pipeline. The engine
now CONVERGES (the earlier over-segmentation refusal is resolved):

- FX1 → 9 walls (8 segments + 1 arc) / 6 openings (2 doors + passage + 3 windows incl.
  arc-hosted + staircase) / 3 rooms, deterministic, zero errors.
- 60-fixture synthetic corpus → 60/60 wall-count convergence, zero fail-closed codes,
  openings pred ≥ truth on every fixture.
- Rooms emitted in mm truth space (`polygon`/`area_m2`/`index`); per-plan scale anchors;
  arc-band ink attribution; O-W2 arc-window px-offset render fix (+ FX1/corpus re-freeze);
  segment-direction normalization in the self-scorer.
- 36 WP4 tests + full suite 564 passed (excluding pre-existing
  `test_wp0_cpu_feasibility.py` collection error).

## Critical honesty notes for the successor

1. **Structural convergence is met, spatial precision is not (packet §5 / AT-14).**
   3/8 segments match truth byte-exactly (W-S/W-PV/W-PH); the other 5 have endpoint
   error 25–50 mm, which exceeds the §5 endpoint-P95 bound of `max(3 px, 20 mm)`. The
   arc is within §5 radius (0.035%) and sweep (179.99°) tolerances but does not
   byte-match (angle modulo-360 + ~5.4 mm centre quantization). Exact-by-key
   `match_wall` (frozen, `src/pwa/evaluator/metrics.py`) is NOT the §5 spatial matcher
   and can never score raster reconstruction fully. The §5/AT-14 tolerance matcher is
   owned by the Evaluation/Geometry Reviewer (TBD) and has not been implemented.
2. **AT-07 (≥29/30 clean emits):** the wall-count layer converges 60/60, but "every
   emitted plan still meets all gates" is not proven while endpoints exceed the 20 mm
   bound. The recognizer's exact-by-key self-scorer reports 3/9 on FX1 (up from 0/9).
3. **O-W3 staircase-window width** is imprecise (~0.365 m vs authored 1.2 m) — emits
   but does not meet width tolerance. Documented, open.
4. **Independent cross-provider Opus-level review** remains a prerequisite before any
   B-AUTO acceptance claim; not re-obtained this continuation.

## What the successor must NOT do

- Do not fabricate a ≥29/30 clean-emit claim: yield at wall count is not the same as
  "every emitted plan meets all gates" under the §5 spatial tolerances.
- Do not weaken any threshold, invent a tolerance matcher as part of this WP, or claim
  the exact-by-key self-scorer is the acceptance scorer.
- Do not treat `match_wall` exact-by-key pass/fail as the spatial gate — it is a frozen
  sanity matcher, not §5/AT-14.
- Do not activate any route (WP6 is decision-packet-only).

## Files

- src/pwa/floorplan/raster_auto.py, raster_auto_geometry.py, raster_auto_worker.py
- tests/unit/test_wp4_raster_auto.py, tests/unit/test_wp4_corpus.py
- tools/make_wp0_fx1_fixture.py, tools/make_wp4_corpus.py
- evidence/PLAN-002RF/WP4/{WORKING-PLAN,RUN-REPORT,wall-recovery-rework-plan}.md,
  decision-record-u3-u4-u5-at21-20260818.md, model-provenance.md, review/,
  corpus/, test-results/
