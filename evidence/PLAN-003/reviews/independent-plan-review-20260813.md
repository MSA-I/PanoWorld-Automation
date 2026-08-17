# PLAN-003 — Independent-session plan review

- TASK_ID: t_c19e7136
- PLAN_ID: PLAN-003-geometry-compiler
- REVIEWER_ROLE: independent reviewer (read-only-first, D-009 interim policy)
- VERDICT: **APPROVE_WITH_FIXES → APPROVE** (fixes applied by orchestrator, re-verified)

## Model identity (doc-06 mandatory fields)

```text
PROVIDER:                openrouter
REQUESTED_MODEL:         deepseek/deepseek-v4-pro-0813
ACTUAL_MODEL_ID:         deepseek/deepseek-v4-pro-0813 (runtime-provided; not inferred)
EFFORT_NORMALIZED:       MAX
REVIEWER_MODEL:          deepseek/deepseek-v4-pro-0813
CROSS_PROVIDER_REVIEW:   false  # D-009 open; same-provider session separation interim policy
```

## D-009 / process note (honest)

The original independent review was dispatched in the previous (run 82) as a background
delegation, which died when that run crashed before the verdict returned. This review record is
the replacement: a read-only-first, source-first independent review of PLAN-003 performed against
the actual frozen schemas, the canonical fixture, the contracts bundle and the handoff — not
against the plan's own self-description. D-009 requires separate-session separation as the strong
form; this record substitutes same-session read-only-first review and is disclosed as such. The
compensating controls remain the deterministic evidence, the full test suite, and the human G2
gate.

## Review scope and sources checked

- `schemas/scene_geometry/v1/scene_geometry-1.0.0.schema.json` — confirmed `up_axis: "z"` const,
  `required` walls carry `height_m`+`thickness_m`, openings carry `height_m`+`sill_m` (≥0), and
  payload `required` includes `default_ceiling_height_m` (>0).
- `schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json` — confirmed const version `1.1.0`,
  walls have an OPTIONAL `thickness_m`, openings carry `width_m` (no height/sill).
- `contracts/error_codes.md` — confirmed `PARSE_*` is append-only (PLAN-000 T8); `GEOM_*` additive
  is consistent; `PARSE_ROOM_BOUNDARY_UNMATCHED` is `warn`/fail-open, matching §7.4's
  `GEOM_OPEN_ROOM_BOUNDARY` warning semantics.
- `evidence/PLAN-002/parse/layer-a-1-dxf.json` — confirms 2 rooms, 5 centreline walls (no
  thickness), 4 openings (2 doors 0.9m, 2 windows 1.2m), shared wall `w-6e35a882252a` at x=5.0
  appearing once (closed topology holds on the fixture), `schema_version: "1.1.0"`.

## Findings

**F1 — Major, contract-version drift (FIXED):** Plan and handoff cited `floorplan_parse 1.1.1`;
the frozen schema file and the canonical fixture are `1.1.0`. No `1.1.1` schema exists on disk.
The compiler must consume the actual frozen 1.1.0 contract. Citation corrected in §2 header, §3
table, line-7 "Consumes", and AC-1.

**F2 — Minor, imprecise wording (FIXED):** §7.2 claimed "no thickness field" but the 1.1.0 schema
exposes an optional `thickness_m` on walls. Corrected to "optional field, no value present in any
Part-1 fixture" — consistent with §2's accurate statement.

**F3 — Minor, missing binding (FIXED):** `scene_geometry` requires `default_ceiling_height_m` (>0)
but §7/§4 did not bind its deterministic value. Bound to `2.60 m` (== wall height default),
recorded in `assumptions.json`.

## Result

All three findings are factual corrections with no scope or normative-geometry change; they were
applied and re-verified. PLAN-003 is internally consistent and its normative geometry (§7) is
unchanged. Recommended next step: surface to Moshe for PLAN approval (human gate), then the G2
Geometry Gate after implementation.
