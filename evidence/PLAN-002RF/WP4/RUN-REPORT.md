# RUN REPORT — PLAN-002RF WP4 (t_f2830a3e) — Product B-AUTO clean-raster engine

- Committing HEAD: `d66f0ad` + `bb58efd` (local only, no push).
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`.
- Session: continued from Moshe continuation approval 2026-08-18 (finish O-W2/O-W3 + close AT-07).

## What was delivered (this continuation)

The engine now converges — the earlier over-segmentation refusal is resolved.

1. **Wall recovery converges** (prior REWORK, commits 7d8f3aa… a56c555): FX1 recovers
   exactly 9 walls (8 segments + 1 circular arc) with correct orientation; the full
   60-fixture corpus converges 60/60 (wall count == truth, zero `RASTER_OVERSEGMENTED`).
2. **Openings 6/6** (FX1): 2 doors + 1 passage + 3 windows, including the arc-hosted
   window (W-APSE) and the diagonal-staircase window (W-DIAG). Type from motif
   (leaf at jamb / glazing offset / bare gap).
3. **Rooms 3/3** (FX1): planar half-edge face walk (T-junction split + snap TOL=10),
   now emitted in mm truth space with `polygon`/`area_m2`/`index` (previously the
   contract layer silently dropped every room on the room channel).
4. **O-W2 arc-window render fix** (this continuation): the inner glazing offset is
   authored in pixels (8 px = 40 mm on the 5 mm/px grid), fixing the render/detect
   unit mismatch that made the arc-hosted window unreachable. FX1 + 16 arc corpus
   fixtures re-frozen (raster hash + hash-bound manifests updated; truth geometry hash
   unchanged).
5. **O-W3 staircase-window width** now emits (previously fail-closed); width precision
   remains imperfect (~0.365 m vs authored 1.2 m) — documented, open.
6. **Per-plan scale anchors**: corpus fixtures read their own sibling
   `fxx-scale-anchors.json` (hash-bound), no longer the hardcoded FX1 manifest.
7. **Segment-direction normalization** (TDD RED→GREEN): `truth_record_from_wall` now
   emits segments in canonical (lexicographically-smaller endpoint first) order, so a
   correctly-recovered wall is no longer scored as a miss when the pixel detector names
   endpoints in scan order. FX1 self-score improved 0/9 → 3/9 (the three axis-aligned
   long walls W-S/W-PV/W-PH now match byte-exactly).

## Test results

- Targeted WP4 (`test_wp4_raster_auto.py`): 36 passed.
- Corpus (`test_wp4_corpus.py`): 5 passed.
- Full suite (excluding pre-existing `test_wp0_cpu_feasibility.py` collection error):
  564 passed, 2 warnings.
- Determinism: parse + emit + SVG byte-deterministic (replay tested).

## Honest assessment of spatial precision (packet §5 / AT-14)

Wall counts, kinds, openings and rooms are correct. Exact-by-key endpoint precision is
NOT yet met for all walls:

- 3/8 segments recover byte-exactly (W-S, W-PV, W-PH).
- 5/8 segments have endpoint error 25–50 mm (W-W 45, W-N 50, W-E-B 30, W-E-A 25,
  W-DIAG 27): the detector stops short at / overruns a junction or opening instead of
  landing on the exact truth endpoint.
- The arc recovers with radius error 0.035% and sweep 179.99° (well inside §5's
  radius ≤2% / sweep ≥95%), but the angle parametrization differs modulo 360 and the
  centre is ~5.4 mm off (pixel quantization), so it does not byte-match truth.

Packet §5 (line 77) defines a tolerance matcher — raster endpoint P95 ≤ `max(3 px,
0.020 m)`, radius error ≤2%, sweep overlap ≥95%. Several segment endpoints (25–50 mm)
exceed the 20 mm endpoint bound. The frozen `match_wall` in `src/pwa/evaluator/metrics.py`
is exact-by-key (deliberately; see `test_match_requires_same_kind_then_exact_quantized_geometry`)
and is NOT the §5 spatial matcher. The §5/AT-14 tolerance matcher is owned by the
Evaluation/Geometry Reviewer (TBD in the packet) and is not yet implemented. Until it
is, the recognizer's own exact-by-key self-scorer reports 3/9, not a full spatial pass.

## Acceptance status

- Met (engine behavior): determinism, fail-closed negative/adversarial refusals,
  resource caps, two-anchor scale validation from hash-bound manifests, emitter
  invariants, FX1 structural convergence (9 walls / 6 openings / 3 rooms), 60/60 corpus
  wall-count convergence.
- Not met / honest blockers (unchanged by this continuation):
  - AT-07 (≥29/30 clean emits): the R0 corpus is the 60-fixture synthetic set; wall
    count converges 60/60, but "every emitted plan still meets all gates" (incl. §5
    spatial precision) is not yet proven at the 20 mm endpoint bound.
  - AT-14 (§5 tolerance matcher) — matcher not implemented (owner TBD); 5/8 segments
    exceed the 20 mm endpoint tolerance.
  - Independent cross-provider Opus-level review is a prerequisite before closure and
    has not been (re)obtained this continuation.

## Hard boundaries honored

No dependency install; no network/model call in the engine; no H200/GPU/cloud/remote;
no spend; no G7/G8/Product C/PLAN-003; no route activation (default-off); no
push/merge-to-remote (local commits only); no manual rescue or per-plan tuning; no
fabricated truth or weakened thresholds.
