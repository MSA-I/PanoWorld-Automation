# WP4 synthesis corpus — independent Opus review (2026-08-17)

Reviewer: Claude Code CLI `claude -p --model opus` (actual model `claude-opus-5`,
verified from transcript). Read-only; NOT via OmniRoute (Moshe direction).

Scope: `tools/make_wp4_corpus.py`, the arc-opening fix in
`tools/make_wp0_fx1_fixture.py`, and `tests/unit/test_wp4_corpus.py`.

## Verdict: NEEDS_REWORK

## Findings (verbatim severities)

CRITICAL:
1. 13 of 32 fixtures were byte-identical duplicates (`_arc_source`/`_diag_source`
   ignored `i`/`rng`), so the effective corpus was 21 distinct plans, not 32.
2. The door motif was drawn always "up", valid only for horizontal hosts; on
   vertical walls the leaf collinearly refilled the opening gap, so every fixture
   had a raster contradicting its own truth.

MAJOR:
3. diag window O-3 width_mm=1200 vs actual 1250 mm span (hand-authored constant).
4. diag room truth geometrically wrong (outside triangle + overlapping R-W).
5. rect partitions ran straight through the perimeter openings.
6. `topology: []` everywhere — a false assertion that no rooms connect.
7. arc-hosted window drawn as a single polyline on the wall centreline
   (indistinguishable from the 3px wall).
8. test could not detect any of the above (tautological assertions).

MINOR / INFO: sealed unreachable rooms; no validation pass in `build_one`;
`exist_ok=True` (partial dir on rerun); FX1 hash-neutrality unproven;
`_rooms_from_rect` silent cell-drop; clutter not checked against walls; PNG bytes
environment-bound; dead imports (`hashlib`, `PIL`, inner `import math`).

## Remediation (commits 8de0e72, f3edf40)

- CRITICAL 1: arc/diag sources vary by fixture ordinal -> 32/32 distinct.
- CRITICAL 2: door leaf drawn PERPENDICULAR to host wall; proven hash-neutral for
  the frozen FX1 raster (committed sha256 == rebuilt sha256).
- MAJOR 3/4: diag window width + rooms corrected.
- MAJOR 5: rect partitions kept >=800mm from opening centres.
- MAJOR 6: topology computed from door adjacency (rect) / explicit (arc, diag).
- MAJOR 7: arc window now two concentric glazing arcs; FX1 re-frozen.
- MINOR: `build_one` exist_ok=False + per-fixture hash verification; dead imports removed.
- Strengthened `test_wp4_corpus`: uniqueness, openings-on-host-wall, width==span,
  anchors on-grid/in-canvas/non-collinear, project-ownership.
