# HANDOFF — WP4 (Product B-AUTO) → next WP

- Task: `t_f2830a3e` (WP4 Product B-AUTO clean-raster engine) — BLOCKED closeout.
- Committing HEAD: `560b752` (local only, no push).
- Next WP5 card `t_dfa6f24f` remains a human needs_input gate — WP4 completion
  does NOT authorize WP5.

## What was delivered

A deterministic, CPU-only, no-OCR, no-learned-model `raster_auto` pipeline
(geometry primitives + worker + fail-closed emitter + FX1-truth scorer + SVG),
committed with 25 TDD tests. Full suite 492 passed (excluding the pre-existing
`test_wp0_cpu_feasibility.py` collection error).

## Critical honesty notes for the successor

1. The pixel extraction does NOT converge to the exact FX1 envelope (9 walls /
   6 openings / 3 rooms / 1 arc). It over-segments; the engine correctly
   refuses (`RASTER_OVERSEGMENTED`) and emits an EMPTY payload — fail-closed —
   rather than manufactured geometry.
2. The ≥29/30 clean-emit gate (AT-07) is BLOCKED on the R0=30 corpus (n=1 in
   tree) plus U-2/U-3/U-4/U-5 and AT-21 blind-truth prerequisites.
3. The independent cross-provider review was NOT obtained (felo-chat degenerate
   output; Opus routes silently collapse to felo-chat). Recorded, not fabricated.

## What the successor must NOT do

- Do not fabricate a 29/30 result or an accuracy claim over an absent corpus.
- Do not weaken any threshold to make the fixture "pass".
- Do not treat the over-segmentation refusal as "done" — the actual clean-plan
  extraction (correct wall/opening/room/arc segmentation) is the remaining
  engineering work, bound by the U-2/U-3/U-4/U-5 decisions once unblocked.
- Do not activate any route (WP6 is decision-packet-only).

## Files

- src/pwa/floorplan/raster_auto.py, raster_auto_geometry.py, raster_auto_worker.py
- tests/unit/test_wp4_raster_auto.py
- evidence/PLAN-002RF/WP4/{WORKING-PLAN,RUN-REPORT}.md, model-provenance.md,
  test-results/*.log, review/{review-brief.txt, review-prompt-full.txt,
  omniroute-review-full.txt, omniroute-headers.txt}
