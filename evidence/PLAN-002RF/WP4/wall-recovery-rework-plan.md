# WP4 wall-recovery REWORK plan (diagnosis, 2026-08-17)

Status: the raster_auto engine recovers **72 walls** on the FX1 fixture instead of
**9** (8 straight segments + 1 apse arc), so it refuses with
`RASTER_OVERSEGMENTED`. This is the remaining TECHNICAL blocker for WP4 acceptance
(the governance blockers — corpus ratification, U-3/U-4/U-5, AT-21 — are separate).

## Measured breakdown (FX1, 2400x2000 @ 5mm/px, 1px wall skeleton)

- ~15 near-axis wall fragments (should be 4 vertical + 3 horizontal): the same
  wall is emitted from multiple near-duplicate Hough theta bins.
- ~7 x 600px fragments of the **3-4-5 diagonal** (should be 1 wall): the diagonal
  is rasterized as a STAIRCASE (binary, no anti-aliasing); Hough votes on the
  staircase's axis-aligned steps, not the 36.87-degree line.
- ~7 chord fragments of the **apse arc** (should be 1 `circular_arc`): the arc is
  detected as near-axis tangent chords, then `_paint_segment_coverage` (8px) covers
  its own residue, so `_recover_arc_walls` returns `[]`.
- ~28 short fragments (< 200px): staircase steps + arc chords promoted to walls.

## Three sub-problems (each substantial, multi-hour)

1. **Arc-first detection.** Detect the circular arc from the 1px skeleton BEFORE
   segment-wall extraction, remove its pixels, then run Hough on the straight
   remainder. The arc is the only curved feature; a deterministic RANSAC circle
   fit with a fixed seed + radius sanity bound (arc radius ~100-500px) is the
   cleanest path. This also fixes the W-E-A/W-E-B merge-across-the-arc (the merge
   threshold `WALL_OPENING_GAP_PX`=620px > the ~600px apse gap).

   **Measured blocker (2026-08-18):** the 3x3 `wall_centerlines` erosion FRAGMENTS
   the arc. The arc is rendered as a 32-chord polyline (Pillow `draw.line` width=3);
   the erosion collapses it from ~1862 px (structural, 3px) to ~348 px across 52
   tiny connected components (largest ~55 px). A RANSAC+guard prototype recovered
   the FX1 arc correctly (center 1795/1350, r=303) but the fragmentation defeats
   the contiguity/density guards, and no threshold tune made it robust. Two fix
   paths: (a) render the arc as a TRUE arc (`ImageDraw.arc` or a dense polyline,
   not 32 chords) so the erosion leaves a clean 1px arc — cascades to re-freeze FX1
   + rebuild the corpus; (b) detect the arc from the STRUCTURAL mask (pre-erosion,
   clean 3px arc) and remove it before erosion. Path (b) is preferred (no fixture
   churn).

2. **Diagonal via staircase, not Hough.** A 3-4-5 diagonal staircase must be
   recovered by fitting a line to the staircase's pixel cloud (RANSAC/least
   squares at the known 3-4-5 orientation 36.87deg / complement 53.13deg), or by
   suppressing the staircase's axis-aligned step peaks (near-axis lines whose
   runs are staircase-length-1) before collinear-run extraction.

3. **Merge only across recognised openings (U-4).** `merge_collinear_segments`
   must join two collinear runs ONLY when the gap between them contains a
   recognised opening motif (door leaf / window glazing / passage jamb ticks),
   not unconditionally up to `WALL_OPENING_GAP_PX`.

   **Resolved (2026-08-18):** the merge-across-the-arc failure is fixed by the
   arc-first change (the arc is removed from the mask before Hough, so its
   600px chord gap never reaches the merge) plus lowering `WALL_OPENING_GAP_PX`
   to 350px (below the min arc chord 400px, above the max opening 300px). The
   full "motif check" (which would need passage jamb ticks, presently rendered
   as a bare gap) is deferred as a future refinement for the 3.0m-passage ==
   3.0m-arc-gap case, absent from the current corpus.

## Constraints

Deterministic; no OCR; no new deps beyond scipy; constants derived from stroke
geometry and documented (NOT tuned against the fixture — AT-18). TDD: keep
`tests/unit/test_wp4_raster_auto.py` green and add a convergence test.

## Note on parallel agents

`delegate_task` fan-out fails in this environment ("API call failed after 3
retries: Connection error"), so this work cannot be parallelized via subagents
today; it is sequential.
