# RUN REPORT — PLAN-002RF WP4 (t_f2830a3e) — Product B-AUTO clean-raster engine

- Committing HEAD: `560b752` (local only, no push).
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7` (verified this session).

## What was implemented (deterministic, CPU-only, no-OCR, no-learned-model)

A new additive Product-B pipeline `raster_auto` (source_class already frozen by
WP2). New modules:

- `src/pwa/floorplan/raster_auto_geometry.py` — pure primitives: global Otsu
  (+ separability gate + frozen tie-break), 8-connected union-find components,
  2-parameter Hough + physical-line clustering, Kasa algebraic circle fit +
  RMS residual, two-anchor scale fit (median residual + disagreement), stroke
  thickness recovery, collinear run extraction + opening-gap merge, clutter /
  unexplained-ink / pixel-budget guards.
- `src/pwa/floorplan/raster_auto_worker.py` — worker boundary: header-first
  decode with pre-allocation guards, structural binarization (value 0 only),
  threshold/components, wall (segment + arc) recovery, opening motif
  classification, two-anchor scale validation, fail-closed refusals, mm
  conversion, FX1-truth scorer + SVG overlay.
- `src/pwa/floorplan/raster_auto.py` — emitter (`emit_raster_auto_parse`) into
  `floorplan_parse` 1.2.0 (`source_class: raster_auto`) + fail-closed
  `parse_raster_auto` + FX1-truth scorer + SVG renderer.
- `tests/unit/test_wp4_raster_auto.py` — 25 tests (RED→GREEN TDD).

## Test results

- Targeted WP4: 25 passed.
- Full suite (excluding pre-existing `test_wp0_cpu_feasibility.py` collection
  error, same exclusion as WP3): 492 passed, 2 warnings.
- Determinism: parse + emit + SVG are byte-deterministic (replay tested).

## Honest state of the recognition extraction

The pixel-recognition extraction does NOT yet converge to the exact FX1 frozen
envelope (9 walls = 8 segments + 1 semicircular arc; 6 openings; 3 rooms). The
Hough physical-line clustering over-segments the structure (~70 collinear
fragments vs 9) because opening motifs (door leaves, window glazing, jamb
ticks) and clutter strokes are partially conflated with wall centrelines, and
the diagonal (3-4-5) wall's Hough peaks bleed into nearby angular bins.

Correctly, the engine DETECTS this (`RASTER_OVERSEGMENTED`) and — via
`parse_raster_auto` — emits an EMPTY payload (0 walls / 0 rooms / 0 openings)
rather than a manufactured partial plan. This is the required fail-closed
behavior (W-17 / AT-18): the engine never emits geometry alongside a blocking
finding.

## Acceptance that IS implementable and verified this WP

- determinism (parse + emit + SVG);
- fail-closed negative/adversarial refusals (low-contrast, clutter-over-band,
  unexplained-ink, over-segmentation, unsupported-format, missing anchors,
  oversized pixels);
- resource caps (MAX_SOURCE_RASTER_BYTES / MAX_SOURCE_PIXELS, header-only decode);
- scale validation from the hash-bound manifest (median residual ≤1%,
  disagreement ≤2%);
- emitter invariants (thickness present, passage span bound, arc sagitta bound);
- FX1-truth scorer (exact-by-key via the frozen WP1 evaluator).

## Acceptance that is NOT verifiable this WP (→ BLOCKED, not fabricated)

- ≥29/30 clean emits (AT-07): R0=30 corpus absent (n=1 fixture in the tree).
- wall/opening P/R ≥0.995/0.980 (AT-09..AT-12): no adjudicated labeler truth.
- zero critical FP with exact 3/n bound over 100 families (AT-13): corpus absent.
- two-anchor scale fit / disagreement formula (U-2 BLOCKED).
- arc radius/sweep/sampling bounds (U-3 BLOCKED).
- clustering/gap/merge bounds (U-4 BLOCKED).
- fixed B symbol/style guide (U-5 BLOCKED).
- independent truth via two blind labelers + adjudicator (AT-21): absent.
- exact clean-plan extraction (8 segments + arc + openings + rooms) to frozen-truth accuracy.

## Independent cross-provider review — NOT OBTAINED (blocked)

The Anthropic-Opus spatial review gate is triggered (new raster-vision
geometry). Opus-level routes probed via OmniRoute (`auto/claude-opus`,
`aug/opus*`, `tllm/CLAUDE_4_6_OPUS`) all silently resolve to `felo/felo-chat`
behind the scenes; `felo-chat` is currently returning degenerate output (1–2
completion tokens: "```", "."). No substantive cross-provider review could be
produced. This is recorded, not fabricated; a real independent read-only review
remains a prerequisite before any B-AUTO acceptance claim. Requested/actual
provider+model and the fallback impact are recorded in
`model-provenance.md`.

## Hard boundaries honored

No dependency install; no network/model call in the engine; no H200/GPU/cloud/
remote; no spend; no G7/G8/Product C/PLAN-003; no route activation (default-off);
no push/merge-to-remote (local commits only); no manual rescue or per-plan tuning.
