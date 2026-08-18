# ADR-0008 — Camera-planner CAM_* vocabulary and camera_plan run lifecycle

- Status: **APPROVED** (Moshe 2026-08-18, with PLAN-004) — pending G3 Camera Gate + merge
- Date: 2026-08-17
- Controlling plan: `docs/plans/PLAN-004-camera-planner.md`
- Scope: Part 1 local only. G7/G8, H200/GPU, cloud, remote and spend remain DEFERRED TO PART 2.

## Context

PLAN-004 (C5 Camera Planner) consumes one immutable `scene_geometry` 1.0.0 white model and emits a
schema-valid `camera_plan` 1.0.0 plus per-viewpoint camera-to-world extrinsics
(`extrinsics.txt`, Z-up world, OpenCV camera axes). It needs its own append-only error vocabulary
(the parser's `PARSE_*` and the compiler's `GEOM_*` are owned by earlier plans and frozen) and an
immutable derived-run lifecycle distinct from the parse and geometry layouts.

## Decision

1. Add an additive `CAM_*` error/severity vocabulary (append-only; no mutation of any `PARSE_*` or
   `GEOM_*` code or severity). Codes:

   - `CAM_SOURCE_HASH_MISMATCH` (error, tier 0) — consumed geometry artifact content_hash does not
     match its canonical hash.
   - `CAM_RESOURCE_LIMIT` (error, tier 0) — a configured count/byte/coordinate bound was exceeded,
     or a field was non-finite/malformed.
   - `CAM_EMPTY_GEOMETRY` (error, tier 2) — geometry payload lacks at least one room (and, for
     coverage scoring, at least one usable room polygon).
   - `CAM_DUPLICATE_ENTITY` (error, tier 2) — viewpoint IDs or positions collided within one run
     (fail-closed, no silent merge/renumber).
   - `CAM_UNCOVERED_ROOM` (error, tier 3) — a target room has zero valid viewpoint placements after
     free-space resolution (fail-closed; the room is not silently skipped).
   - `CAM_VIEWPOINT_OUTSIDE_ROOM` (error, tier 3) — a viewpoint lies outside or on the boundary of
     its room polygon.
   - `CAM_VIEWPOINT_COLLIDES_WALL` (error, tier 3) — a viewpoint is closer than the wall clearance
     (`thickness_m/2 + 0.35 m`) to a wall centreline.
   - `CAM_VIEWPOINT_COLLIDES_OPENING` (error, tier 3) — a viewpoint is closer than `0.20 m` to a
     door/window opening centre.
   - `CAM_EXTRINSICS_INVALID` (error, tier 3) — a produced 4×4 fails `check_extrinsics_matrix` (not
     orthonormal, not right-handed, wrong last row, or non-Z-up convention).
   - `CAM_CAMERA_HEIGHT_OUT_OF_RANGE` (error, tier 3) — camera height is non-finite or outside
     `[0.5, 3.0]` m.
   - `CAM_MAP_ADJACENCY_UNRESOLVED` (warn, tier 4) — a door opening does not resolve to two
     distinct covered rooms, so no adjacency edge is emitted (fail-open, reported).

2. `camera_plan` 1.0.0 remains the frozen output schema (already Z-up). The planner fills the
   required `resolution`, `viewpoints`, `edges`, `start_viewpoint`, `max_views_per_lrm_batch`, and
   the optional `camera_height_m` (default 1.35 m). Resolution default `2048 × 1024` (width == 2 ×
   height), recorded in `assumptions.json`; `max_views_per_lrm_batch` default `8` (mirrors verified
   PanoWorld `viewpoint_max_view`).

3. One immutable derived camera run per compilation:
   `runs/<cam-run-id>/{project/source-geometry.json, camera/{camera_plan.json, assumptions.json,
   coverage-report.json, camera-report.json, map.json, extrinsics/<viewpoint-id>.txt,
   overlay-cameras.svg}}`. The source geometry is byte-copied, never mutated; staging→final is
   atomic (`os.replace`); destinations are containment-checked.

4. Defaults (camera height 1.35 m, wall clearance 0.35 m, opening clearance 0.20 m, yaw 0,
   resolution 2048×1024, batch 8) are recorded in `assumptions.json` (source=default), never
   silently applied.

5. Extrinsics are **camera-to-world**, **Z-up world**, **OpenCV camera axes** (`R[:,1] == (0,0,-1)`)
   and must pass `pwa.validator.check_extrinsics_matrix` with zero error codes — machine-checked,
   not asserted.

## Consequences

- Append-only: `PARSE_*` and `GEOM_*` untouched; `CAM_*` is purely additive; `camera_plan` 1.0.0
  consumed as-is (no schema change in this ADR).
- Camera runs consume storage per run (byte-copied source + overlays + extrinsics); new runs
  require new cam-run IDs.
- Any change to the normative §7 placement/coverage/extrinsics defaults or conventions is a critical
  Camera-gate change requiring a revised plan and Moshe approval.

## Evidence

`docs/plans/PLAN-004-camera-planner.md` §§5, 7, 14, 16; PLAN-003 §7 precedent;
`schemas/camera_plan/v1/camera_plan-1.0.0.schema.json`; `pwa/validator/package_validator.py`
`check_extrinsics_matrix`.
