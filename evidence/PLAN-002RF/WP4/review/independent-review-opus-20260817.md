# WP4 (t_f2830a3e) — Independent Opus review (2026-08-17)

- Date: 2026-08-17.
- Reviewer model: `claude-opus-5` (requested `opus`; actual confirmed from Claude Code
  transcript `~/.claude/projects/.../51008d1d....jsonl`, `"model":"claude-opus-5"`).
- Method: read-only, via `claude -p --model opus` over the current code
  (`main` HEAD `d15928a`, incl. the U-2 n≥3 scale fix) pasted as data.
- Cross-provider from implementer: openrouter (deepseek) → anthropic (claude-opus-5).
- Verdict: **NEEDS_REWORK**.

The over-segmentation refusal itself is an honest fail-closed outcome
(`over_segmentation_refusal_defensible: true`), but the review found two CRITICAL,
seven MAJOR, four MINOR and one INFO defects, reproduced below verbatim (structured).

## CRITICAL

1. **Fail-closed violation (contract layer)** — `src/pwa/floorplan/raster_auto.py`:
   `parse_raster_auto` empties the payload only for worker findings. `emit_raster_auto_parse`
   returns a fully populated payload together with `recognition_findings` produced by
   `recognition.check_thickness`, `arc_invariants` and `check_passage_span` — all severity
   "error" (RECOGNITION_THICKNESS_MISSING, RECOGNITION_ARC_NO_SAGITTA_BOUND,
   RECOGNITION_ARC_BULGE_SWEEP_MISMATCH, RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND). A wall with
   `thickness_m: None` or an opening whose gap converts > PASSAGE_SPAN_MAX_M yields the
   blocking code AND the geometry. W-17/AT-18 holds only for the worker's error channel,
   not the contract layer.

2. **Resource exhaustion** — `src/pwa/floorplan/raster_auto_worker.py`: post-decode guards
   (RASTER_LOW_CONTRAST, INK_FRACTION_BAND breach) append to `errors` but never short-circuit;
   execution continues into pure-Python connected-components + Hough on up to
   MAX_SOURCE_PIXELS = 100 MP, with no PARSER_TIMEOUT_S enforced on this path.

## MAJOR

3. `_classify_gap_motif` can never return "door" — `_offset_stroke_length` starts at off=1
   from the gap centre (empty by construction) → perp_run == par_run == 0 → every gap with
   ink is "window", else "passage". Door and jamb-tick branches are unreachable.
4. `_derive_rooms` returns `[]` on both branches — the engine can NEVER emit a room; the
   3-room FX1 envelope is structurally unreachable even if walls were perfect.
5. Arc angle conversion wrong in two places (arctan2 branch-cut min/max; `-start_img % 360`
   + hardcoded ccw + unhandled y-flip) — a negative-degree arc can never match frozen truth.
6. `hough_physical_lines` theta-wrap doesn't negate rho for theta≈0/180 — emits two distinct
   lines for one axis-aligned vertical wall (direct over-segmentation contributor).
7. `collinear_runs` + `merge_collinear_segments` join runs across gaps up to 620 px
   unconditionally with no opening-motif verification — manufacture spurious walls.
8. Scale-dependent thresholds frozen in PIXELS (WALL_OPENING_GAP_PX=620, MIN_WALL_LENGTH_PX=10)
   but applied independently of the resolved manifest scale — the merge bound only equals
   PASSAGE_SPAN_MAX_M=3.0 m at 5 mm/px.
9. Confidence/provenance: `confidence` defaults to 1.0 for automatically-recognised entities;
   `emit_raster_auto_parse` hardcodes `scale_m_per_px: None` even though the scale was used.

## MINOR

10. `_estimate_unexplained_ink` is anti-correlated with correctness (more spurious walls →
    more ink "explained") — RASTER_UNEXPLAINED_INK is vacuous in the failure mode it guards.
11. `fit_scale` `median_residual` is actually `max(residuals)` — stricter than AT-15's named
    "median residual", fails closed but the name/docstring are wrong.
12. SVG arc render: large-arc-flag hardcoded 0, sweep-flag wrong under y-negation, no viewBox.
13. `_decode` never closes the Pillow image; `_load_authoritative_anchors` re-reads the whole
    raster for hashing (up to 50 MB held twice); manifest path via `parents[3]` breaks on
    relocation and binds anchors to exactly one raster SHA-256 (structural R0=30 blocker).

## INFO

14. Dead/misleading code: unused `labels` from connected_components (most expensive step fills
    one diagnostic int); `occupied` re-derived inline; `_classify_gap_motif` patch-clipping
    block ends in `pass`; `_arc_wall_opening` unconditionally returns None; `rooms`/`openings`
    reassigned; `main()` indexes argv[0] unchecked and stringifies numpy scalars.

## Tests gap

The tests cannot catch the fail-closed violation they claim to cover
(`test_emit_raster_auto_parse_fails_closed_on_missing_thickness` never asserts empty walls;
`test_extract_raster_auto_recovers_wall_count_with_anchors` uses `walls == [] or ...`;
`test_otsu_tie_break_is_lowest_index` only asserts `f(x) == f(x)`).

## Disposition

This is a substantive, honest independent review (NOT a rubber-stamp). It confirms the
fail-closed refusal is genuine but shows the engine is further from acceptance than the
RUN-REPORT implied: three claimed capabilities (door motif, room derivation, arc-hosted
opening) are unreachable in code, and the contract layer breaks the fail-closed property.
Remediation is a WP-scope engineering task (fix the contract-layer fail-closed + short-circuit
guards first, then the unreachable-capability paths), which the WP4 card's `needs_input` gate
does NOT authorize on its own. Recorded, not acted upon.
