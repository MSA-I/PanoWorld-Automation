# ADR-0007 — Geometry-compiler GEOM_* vocabulary and scene_geometry run lifecycle

- Status: PROPOSED (PLAN-003, pending Moshe G2 Geometry Gate + merge)
- Date: 2026-08-14
- Controlling plan: `docs/plans/PLAN-003-geometry-compiler.md` (Moshe-approved 2026-08-14, sha256 a122367ba14d2c48f09c48e94adb0448b114375c6dfc187410541237224c3b44)
- Scope: Part 1 local only. G7/G8, H200/GPU, cloud, remote and spend remain DEFERRED TO PART 2.

## Context

PLAN-003 compiles one immutable `floorplan_parse` 1.1.0 artifact into a
schema-valid `scene_geometry` 1.0.0 white model. It needs its own append-only
error vocabulary (the parser's `PARSE_*` codes are PLAN-002-owned and frozen)
and an immutable derived-run lifecycle distinct from the parser's `parse/`
layout.

## Decision

1. Add an additive `GEOM_*` error/severity vocabulary (append-only; no
   mutation of any `PARSE_*` code or severity). Codes:
   - `GEOM_SOURCE_HASH_MISMATCH` (error, tier 0) — consumed parse artifact
     content_hash does not match its canonical hash.
   - `GEOM_RESOURCE_LIMIT` (error, tier 0) — a configured count/byte/coordinate
     bound was exceeded, or a field was non-finite/malformed.
   - `GEOM_EMPTY_GEOMETRY` (error, tier 2) — parse payload lacks at least one
     wall and one room.
   - `GEOM_DUPLICATE_ENTITY` (error, tier 2) — derived geometry IDs collided
     within one run (fail-closed, no silent merge/renumber).
   - `GEOM_OPEN_POLYGON` (error, tier 3) — room polygon not closed.
   - `GEOM_SELF_INTERSECTING_POLYGON` (error, tier 3) — room polygon zero-area
     or self-crossing.
   - `GEOM_DEGENERATE_WALL` (error, tier 3) — wall shorter than 0.05 m.
   - `GEOM_OPENING_UNRESOLVED_WALL` (error, tier 3) — opening references no wall.
   - `GEOM_OPENING_AMBIGUOUS_WALL_REF` (error, tier 3) — reserved; opening
     resolves to more than one wall candidate (fail-closed).
   - `GEOM_OPENING_OFF_WALL` (error, tier 3) — opening centre > 0.02 m from
     host wall.
   - `GEOM_OPENING_WIDTH_EXCEEDS_WALL` (error, tier 3) — opening span does not
     fit the host wall.
   - `GEOM_OPENING_ABOVE_WALL` (error, tier 3) — `sill_m + height_m` exceeds
     host wall height.
   - `GEOM_OPEN_ROOM_BOUNDARY` (warn, tier 4) — wall endpoint not on a room
     vertex, or room edge with no supporting wall (fail-open, reported).
2. `scene_geometry` 1.0.0 remains the frozen output schema (already Z-up). The
   compiler fills the required `default_ceiling_height_m` (2.60 m == wall
   height default), wall `height_m`/`thickness_m`, and opening
   `height_m`/`sill_m`; door depth equals host wall thickness by construction.
3. One immutable derived geometry run per compilation:
   `runs/<geo-run-id>/{project/source-parse.json, geometry/{scene_geometry.json,
   assumptions.json, topology-report.json, geometry-report.json,
   overlay-topdown.svg, overlay-topdown.png}}`. The source parse is byte-copied,
   never mutated; staging→final is atomic (os.replace); destinations are
   containment-checked.
4. Defaults (wall thickness 0.10 m, wall height 2.60 m, door 2.10/0.00 m,
   window 1.20/0.90 m) are recorded in `assumptions.json` (source=default),
   never silently applied.
5. Headless-Blender `.glb` export is default-off and best-effort; a missing or
   failing Blender run is a deferral, never a gate failure (PLAN-003 §8).

## Consequences

- Append-only: `PARSE_*` untouched; `GEOM_*` is purely additive; `scene_geometry`
  1.0.0 consumed as-is (no schema change in this ADR).
- Geometry runs consume storage per run (byte-copied source + overlays); new
  runs require new geo-run IDs.
- Any change to the normative §7 geometry defaults or topology rules is a
  critical Geometry-gate change requiring a revised plan and Moshe approval.

## Evidence

`docs/plans/PLAN-003-geometry-compiler.md` §§5, 7, 15, 17; Moshe PLAN-003
approval 2026-08-14.
