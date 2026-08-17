# PLAN-003 — Planning + Implementation Session Evidence

- TASK_ID: t_c19e7136
- PLAN_ID: PLAN-003-geometry-compiler
- ROLE: Lead Orchestrator / geometry-spatial author
- STATUS: IMPLEMENTED (G-t1..G-t6 complete, 27 geometry tests passing), G-t7 independent review + G2 Geometry Gate pending merge

## Model identity (doc-06 mandatory fields)

```text
REQUESTED_PROVIDER: openrouter
REQUESTED_MODEL: deepseek/deepseek-v4-pro-0813
ACTUAL_MODEL_ID: deepseek/deepseek-v4-pro-0813  (runtime provider; see note below)
EFFORT_NORMALIZED: MAX (author) / EXTRA-MAX (orchestration)
EFFORT_PROVIDER_VALUE: max
THINKING: enabled (spatial/contract reasoning)
MODEL_REASON: spatial representation, units, topology, Blender architecture — C4 geometry compiler
FALLBACK_OCCURRED: no
FALLBACK_PROVIDER: none
FALLBACK_MODEL: none
REVIEWER_MODEL: deepseek/deepseek-v4-pro-0813 (separate isolated session, read-only-first)
CROSS_PROVIDER_REVIEW: false  # D-009 open; same-provider session separation interim policy
```

## Stale-language divergence (recorded, not silently followed)

The kanban card `t_c19e7136` body directs "Opus 5 MAX leads spatial representation …
GPT/Codex handles software contracts". This predates the active DeepSeek/OpenRouter campaign.
The live canonical policy (PROJECT-STATE.yaml `model_policy`, docs/06/08/09/10) mandates
`deepseek/deepseek-v4-pro-0813` via OpenRouter for all roles, MAX effort for spatial/geometry,
with cross-provider review explicitly unavailable (`cross_provider_review_available: false`).
The orchestrator follows the live policy. A real provider/model mismatch still requires Moshe's
approval.

## Artifacts produced this session

- docs/plans/PLAN-003-geometry-compiler.md (APPROVED — Moshe, 2026-08-14, sha256 a122367b…c3b44)
- docs/decisions/ADR-0007-geometry-compiler-vocab-and-run-lifecycle.md (PROPOSED, pending merge)
- contracts/error_codes.md (additive GEOM_* block; PARSE_* untouched)
- evidence/PLAN-003/reviews/independent-plan-review-20260813.md (independent plan review, APPROVE after 3 fixed findings)
- evidence/PLAN-003/geometry-run/** (golden geometry-run artifacts: scene_geometry, assumptions, topology-report, geometry-report, overlay SVG/PNG, source-parse copy)

### New code (src/pwa/geometry/)

- types.py, config.py, findings.py, load.py, compiler.py, topology.py, run_builder.py,
  overlay.py, blender_stub.py, cli.py, __init__.py

### New tests (G-t6)

- tests/unit/test_geometry_compiler.py, tests/unit/test_geometry_topology.py
- tests/integration/test_geometry_run.py
- Total 27 new geometry tests; full suite 420 passed (393 baseline + 27), exit 0.

## Facts verified against source this session (not taken on report)

- Input schema `floorplan_parse` 1.1.0: walls are centreline start/end with OPTIONAL thickness_m,
  no height; openings carry center/width_m/wall_id, no height/sill. (schemas/floorplan_parse/...)
- Output schema `scene_geometry` 1.0.0: up_axis const "z", requires default_ceiling_height_m,
  walls require height_m+thickness_m, openings require height_m+sill_m. (schemas/scene_geometry/...)
- `assumptions` 1.0.0: per-stage entries {key,value,reason,source,requires_human_ack}. (schemas/assumptions/...)
- `contracts/error_codes.md`: PARSE_* table labeled append-only (locked PLAN-000 T8). GEOM_* additive OK.
- Canonical input fixture layer-a-1-dxf.json: 2 rooms, 5 centreline walls, 4 openings. No thickness/height.
- Environment: venv Python 3.11.15; ezdxf 1.4.4; numpy/Pillow/jsonschema locked; Blender 5.1 installed.
- Baseline test suite: 393 passing on main (handoff claim), consistent with observed test files.

## Verification performed this session (orchestrator, source-first)

- `scene_geometry` sample validates against frozen 1.0.0 schema with **0 errors**; content_hash consistent.
- Openings emit exactly the schema-required keys (no depth_m in payload — schema forbids it via
  additionalProperties:false; door depth == wall thickness is enforced compiler-side and tested).
- assumptions.json validates; all 8 default entries present (wall thickness/height, ceiling, door
  height/sill/depth, window height/sill).
- Layer-A fixture produces **0 topology findings** (closed topology holds).
- Door depth_m == host wall thickness (0.10 m) for both doors; sill+height (2.10 m) ≤ wall height (2.60 m).
- Payload deterministic (json sort_keys identical across recompilations).

## Next action

Implementation G-t1..G-t6 is complete. Remaining lifecycle: (1) G-t7 independent read-only-first code
review (separate session) returning APPROVE; (2) bounded rework if findings; (3) G2 Geometry Gate —
present the top-down overlay + topology/dimension report to Moshe for approval; (4) merge + handoff
+ PROJECT-STATE/PROGRESS update in the same merge.
