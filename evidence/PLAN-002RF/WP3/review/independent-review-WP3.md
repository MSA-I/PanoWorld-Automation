# PLAN-002RF WP3 — Independent cross-provider read-only review

- Reviewer: `felo/felo-chat` via OmniRoute `auto` route (HTTP 200)
- Identity (authoritative, from HTTP response headers):
  - `x-omniroute-provider: felo`
  - `x-omniroute-model: felo-chat`
  - `x-omniroute-decision: strategy=single; provider=felo`
- Cross-provider: **YES** — `felo` != implementer `openrouter` (deepseek/deepseek-v4-pro-0813).
- Requested route (spatial/geometry gate): Anthropic Opus-level review was requested
  first. All Opus/Anthropic routes on OmniRoute were unreachable this run:
  - `oc/claude-opus-5`, `opencode/claude-opus-5`, `auto/claude-opus` → HTTP 000 (timeout)
  - `oc/claude-opus-4-8`, `opencode/claude-fable-5` → HTTP 401 (missing API key)
  - `tllm/CLAUDE_4_6_OPUS` → HTTP 403 (egress blocked)
  - Applied the Moshe authorized technical fallback (2026-08-13): record requested vs
    actual provider/model + reason + impact, preserve independent read-only review,
    never weaken thresholds. See `model-provenance.json`.

## Verdict

**APPROVE_WITH_FIXES** — 1 CRITICAL + 1 MAJOR (same root cause) + MINOR/INFO artifacts.

## Findings (evidence-backed)

### CRITICAL-1 — bulged LWPOLYLINE room edges not tessellated (REAL, FIXED)
- File: `src/pwa/floorplan/cad_exact_worker.py` (room branch)
- The worker read `has_bulge` but copied raw LWPOLYLINE vertex coordinates 1:1,
  ignoring the bulge. This violated WORKING-PLAN §3.1 (bulged edges tessellated per
  the FX1 sagitta rule) and produced geometrically wrong room polygons/areas.
- **Fix (TDD):** added `_tessellate_polyline` using `ezdxf.math.bulge_center` /
  `bulge_radius` + frozen `G.tessellate_arc`/`G.min_segments_for_sagitta`, and wired
  it into the room branch. Locked by `test_extract_cad_exact_tessellates_bulged_room_edge`
  (RED→GREEN: asserts >4 vertices and arc samples off the chord).

### MAJOR-1 — same root cause (REAL, FIXED)
- Self-intersection check and area_m2 operated on the un-tessellated polygon. Both
  now operate on the tessellated polygon.

### Findings classified as brief-artifacts (NOT real defects)
The first review pass was over an abbreviated brief (4.3 KB), and the reviewer
mis-derived several "MAJOR" findings that are not present in the real code. They
were re-verified line-by-line against the source and dismissed:
- "sweep_from_endpoints multiplies by 60" — actual code uses `% 360.0` (no `*60`).
- "worker does not convert mm→m before emitting" — `_wall_to_metres`/`_room_to_metres`/
  `_opening_to_metres` multiply by `unit_scale_m` (0.001 mm).
- "passage span compared in wrong units" — `width_m = hypot(...) * scale`.
- "degenerate wall not unit-converted" — `length_mm < DEGENERATE_WALL_M * 1000.0`.
- "ARC wall thickness not checked" — it is (same branch as segment).
- "full-circle arc not rejected" — `delta >= 360.0` rejects it.
These are documented here for transparency; they did not change any code.

## Deterministic read-only corroboration (self-review, same-session)

A deterministic line-by-line review (independent of the LLM reviewer, no model call)
additionally identified and closed the following acceptance gaps that the task body
required but the inherited implementation lacked — all fixed under TDD:
- resource gate: added `MAX_DXF_BYTES` / `MAX_DXF_ENTITIES` enforcement in the worker.
- topology gate: degenerate wall (`PARSE_DEGENERATE_WALL`), duplicate wall
  (`PARSE_DUPLICATE_ENTITY`), self-intersecting room (`PARSE_SELF_INTERSECTING_POLYGON`),
  non-zero-Z wall/openings (`PARSE_UNSUPPORTED_FEATURE`).
- adversarial gate: non-zero-Z refusal test.
- rollback gate: pure/idempotent/deterministic parse + source immutability test.

## Review record location

- `omniroute-review-src.txt` — raw felo response over the full source (geometry + worker).
- `omniroute-headers.txt` — response headers proving provider/model identity.
- `review-brief.txt` / `review-prompt-src.txt` / `review-prompt-full.txt` — inputs.
