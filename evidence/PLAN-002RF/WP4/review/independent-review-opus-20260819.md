# WP4 (t_f2830a3e) — Independent Opus review (2026-08-19)

- Date: 2026-08-19.
- Reviewer model: `claude-opus-5` (requested `--model opus`; actual confirmed from
  Claude Code transcript `~/.claude/projects/D-...PanoWorld-Automation/e7e2bbcb….jsonl`,
  45× `"model":"claude-opus-5"`).
- Method: read-only, `claude -p --model opus` over the converged engine
  (`raster_auto.py` + `raster_auto_worker.py`, 1552-line review input pasted as data).
- Cross-provider from implementer: openrouter (deepseek-v4-pro-0813) → anthropic (claude-opus-5).
- Scope: post-REWORK converged state (walls 9/9, openings 6/6, rooms 3/3, 60/60 corpus),
  incl. the uncommitted segment-direction normalization.
- Verdict: **NEEDS_REWORK**.

The reviewer CONFIRMED the two items this WP most needed a fresh review to validate:
- Fail-closed holds at the emitter/contract layer (the 2026-08-17 CRITICAL #1 is confirmed fixed).
- Short-circuit ordering (low-contrast / clutter guards precede connected-components/Hough/RANSAC)
  and determinism are both sound (the 2026-08-17 CRITICAL #2 is confirmed fixed).

The reviewer then found NEW substantive defects (see full JSON in the review artifact):

## Security / resource (3)
1. **Resource amplification within declared caps** — low-contrast/clutter guards bound ink
   *fraction* only, never absolute work; a 10000×10000 ~5%-ink PNG passes the band yet still
   drives ~35M-ink-pixel pure-Python Hough + fixed-iteration RANSAC + ~1.6 GB `mgrid` grids.
   Needs an absolute ink-pixel/work cap firing `PARSE_RESOURCE_LIMIT` in the short-circuit block.
2. **Absolute path leak** — `_decode` "source file not found" finding uses `source_ref=str(path)`
   (absolute), every other finding uses `path.name`. Findings serialize into evidence with a
   public remote. Use `path.name` consistently.
3. **Uncapped manifest read** — `_load_authoritative_anchors` reads the sibling `*-scale-anchors.json`
   with uncapped `read_text()` before any size check (the raster gets MAX_SOURCE_RASTER_BYTES,
   the manifest gets nothing). No traversal (path derived via `with_name`), SHA-256 binding correct.

## Logic errors (10)
4. **Schema violation (HIGH)** — `openings[].wall_id` emits the worker's INTEGER index, but the
   1.2.0 schema requires a non-empty STRING and walls are `w-%04d`. Every real emit with openings
   (FX1 emits 6) is schema-invalid AND the reference matches no wall id. Invisible to the suite
   because the schema-validity test passes `openings=[]`. Fix: emit `f"w-{wall_id:04d}"` + add a
   schema test with a non-empty openings list.
5. **Worker-channel fail-closed gap** — `extract_raster_auto` returns full walls/rooms/openings
   alongside late blocking findings (SCALE_ANCHORS_INSUFFICIENT, PARSE_DIMENSION_INCONSISTENT,
   RASTER_OVERSEGMENTED, RASTER_UNEXPLAINED_INK); only early decode/contrast/clutter returns are
   empty. `main()` json-dumps that dict verbatim, so the worker CLI emits geometry next to a
   blocking finding. Only `parse_raster_auto` enforces W-17/AT-18.
6. **Span guard covers only `passage`** — door/window widths emitted unchecked although the frozen
   bound (MAX_OPENING_SPAN_MM=1500) bounds every opening; O-W3 (0.365 m vs 1.2 m authored) passes
   silently. Check every opening span.
7. **Arc angles never satisfy the truth convention** — `_finalize_units` emits `start_deg/end_deg`
   always in `(-360, 0]` while fx1-truth W-APSE is `-90/+90`; exact-by-key fails regardless of fit.
   Normalize into `(-180, 180]`.
8. **Arc bulge/sweep invariant vacuous** — `sweep='ccw'` hardcoded + bulge derived from the same
   line, so `recognition.arc_invariants`' sign check compares self-produced values. Derive sweep
   from detected traversal direction.
9. **Window detection coupled to the fixture renderer, not geometry** — `_glazing_at` tests the
   single hardcoded offset `(x+4, y+4)` (the authoring offset); a window offset to the opposite
   side is undetectable. Same class: arc radius 150–450 px, RANSAC spread 60 px, cnt ≥300/≥75,
   leaf run 100/190 px, glazing r−8 are all fixture-coupled constants. Contradicts the
   "none tuned against truth (AT-18/AT-21)" claim.
10. **Two/three-anchor scale validation cannot fail** — `_load_authoritative_anchors` reads BOTH
    `real_length_m` and `span_px` out of the manifest (which also ships `derived_m_per_px`), so
    `fit_scale`'s median-residual/disagreement compare author-declared numbers against themselves
    → 0 by construction; AT-15 gates unreachable. The anchor pixel span must be *measured* from
    the anchor ink (anchors drawn at value 64, already excluded from structural mask).
11. **Scorer matches against a reduced truth projection** — `_truth_mm_record` strips orientation,
    tessellation_rule and vertices_mm before hashing; canonical_key excludes only {id, confidence,
    width_mm}. The "frozen WP1 exact-by-key matcher" is applied to a recognizer-authored reduced
    shape. Projection belongs in the evaluator; both sides must project identically.
12. **a/b canonicalization symmetric gap** — normalization applied only to predictions; truth
    passed through untouched. Sound for the current data (all 8 fx1 + f37 authored smaller-endpoint
    first, verified) but asymmetric; canonicalize in `_truth_mm_record` too.
13. **Scale provenance dropped** — payload always sets `scale_m_per_px: None`; `parse_raster_auto`
    computes `mm_per_px` then hands it to three converters that ignore it.

## Suggestions (non-blocking)
Short-circuit + determinism confirmed sound; `_paint_segment_coverage` dead code; SVG has no
viewBox/width/height and negates y (renders blank) + large-arc-flag hardcoded 0; out-of-image
centreline → phantom gap; `score_against_truth` greedy first-fit not maximum matching;
`_decode` third-element return annotation wrong; leftover `.tmp_arccheck.py` (deleted after review).

## Disposition

Recorded, not yet acted upon. Findings are concrete in-scope WP4 engineering defects (fail-closed
worker channel, schema wall_id, span guard, arc angle/sweep, scale provenance) plus a resource-cap
hardening and several fixture-coupled tuning constants that contradict the AT-18/AT-21 anti-gaming
claim. Remediation is WP-scope work under Moshe's 2026-08-18 continuation approval.
