# PLAN-004 — Planning Session Evidence

- TASK_ID: t_9734e83f
- PLAN_ID: PLAN-004-camera-planner
- ROLE: Lead Orchestrator / camera-spatial author
- STATUS: PLANNED (PLAN-004 + ADR-0008 drafted; independent plan review dispatched; **blocking on Moshe PLAN approval**)

## Model identity (doc-06 mandatory fields)

```text
REQUESTED_PROVIDER: openrouter
REQUESTED_MODEL: deepseek/deepseek-v4-pro-0813
ACTUAL_MODEL_ID: deepseek/deepseek-v4-pro-0813  (runtime provider; recorded from runtime metadata)
EFFORT_NORMALIZED: MAX (spatial/camera author) / EXTRA (orchestration)
EFFORT_PROVIDER_VALUE: max
THINKING: enabled (spatial/contract reasoning)
MODEL_REASON: camera placement, coverage, collision, extrinsics convention — C5 Camera Planner
FALLBACK_OCCURRED: no
FALLBACK_PROVIDER: none
FALLBACK_MODEL: none
REVIEWER_MODEL: deepseek/deepseek-v4-pro-0813 (separate isolated session, read-only-first)
CROSS_PROVIDER_REVIEW: false  # D-009 open; same-provider session separation interim policy
```

## Stale-language divergence (recorded, not silently followed)

The kanban card `t_9734e83f` body directs "Opus leads spatial design; Codex implements algorithms
and property tests; GPT performs correctness review". This predates the active DeepSeek/OpenRouter
campaign. The live canonical policy (PROJECT-STATE.yaml `model_policy`, docs/06/08/09/10) mandates
`deepseek/deepseek-v4-pro-0813` via OpenRouter for all roles, MAX effort for spatial/camera work,
and cross-provider review explicitly unavailable (`cross_provider_review_available: false`). The
orchestrator follows the live policy and records the divergence here. A real provider/model mismatch
still requires Moshe's approval.

## Artifacts produced this session

- docs/plans/PLAN-004-camera-planner.md (APPROVED-PENDING-MOSHE — drafted under delegated authority)
- docs/decisions/ADR-0008-camera-planner-vocab-and-run-lifecycle.md (PROPOSED, pending merge)
- evidence/PLAN-004/planning-session-evidence.md (this file)
- evidence/PLAN-004/reviews/independent-plan-review-20260817.md (independent plan review — pending)

No code (src/pwa/camera/) or contract mutation yet: implementation is gated on Moshe's PLAN
approval, per the task body and the PLAN-003 precedent (a PLAN is not auto-authorized).

## Facts verified against source this session (not taken on report)

- Output schema `camera_plan` 1.0.0 is **already frozen** (schemas/camera_plan/v1/...-1.0.0.schema.json):
  requires payload `resolution{width,height}`, `viewpoints[{id,position[,yaw_deg,room_id]}]`,
  `edges[[a,b]]`, `start_viewpoint`, `max_views_per_lrm_batch`; optional `camera_height_m` default
  1.35. width/height are `multipleOf 2`, `minimum 2`.
- Input schema `scene_geometry` 1.0.0 is frozen and Z-up (`up_axis` const "z"); rooms carry
  `id`+`polygon[point2]` (+optional name/floor_z/ceiling_z); walls carry `id`,`start`,`end`,
  `height_m`,`thickness_m`; openings carry `id`,`type door|window`,`wall_id`,`center`,`width_m`,
  `height_m`,`sill_m`.
- Golden extrinsics convention (tests/golden/panoworld_demo_subset/viewpoints/0000/extrinsics.txt):
  camera-to-world, Z-up world, OpenCV camera axes; translation `(0.72375, -1.055, 1.35)` → camera
  height **1.35 m**; test_extrinsics_checks.py pins `R[:,1] == (0,0,-1)`.
- `check_extrinsics_matrix` (pwa/validator/package_validator.py) already verifies orthonormality,
  right-handedness, last row `[0,0,0,1]`, Z-up convention, and camera-height outlier — the plan
  makes these the machine gate for every produced extrinsics.
- Canonical input fixture (evidence/PLAN-003/geometry-run/geometry/scene_geometry.json): 2 rooms
  (`gr-0647acdd02a3` 5×6, `gr-f9c1af865cc3` 3×6), 5 walls, 4 openings (2 doors, 2 windows). This is
  the real, hash-bound geometry the planner will consume.
- `contracts/error_codes.md` is append-only: `PARSE_*` (locked PLAN-000 T8) and `GEOM_*` (PLAN-003)
  sections exist; `CAM_*` must be a new additive block only.
- Environment (unchanged from PLAN-003): venv Python 3.11.15; numpy locked; no new dependency needed.

## Next action

1. Independent read-only-first plan review of PLAN-004 + ADR-0008 (separate DeepSeek Pro session,
   dispatched). Apply any APPROVE_WITH_CHANGES findings and re-verify.
2. **Block the card for Moshe's PLAN approval** — PLAN-004 is not auto-authorized; the task body and
   PLAN-003 §14 require explicit approval before the C-t1..C-t7 implementation dispatch.
3. After approval: implement C-t1..C-t6 (TDD, deterministic), C-t7 independent review, G3 Camera
   Gate (coverage overlay + coverage/collision report + sample extrinsics → Moshe), then merge +
   handoff + PROJECT-STATE/PROGRESS update in the same merge.
