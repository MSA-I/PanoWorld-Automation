# PLAN-004 — Planning Session Evidence

- Plan: `PLAN-004-camera-planner` (APPROVED by Moshe 2026-08-18, per kanban `t_9734e83f`)
- ADR: `ADR-0008-camera-planner-vocab-and-run-lifecycle` (approved with PLAN-004)
- Task: `t_9734e83f` — P1-04 camera planning and extrinsics (board `panoworld-dev`)
- Boundary: Part 1 local only. G7/G8, H200/GPU, cloud, remote and spend remain DEFERRED TO PART 2.

## Routing (recorded, not self-inferred)

Per PLAN-004 §17 the card body's "Opus leads / Codex implements / GPT reviews"
language is stale. The live policy is `MODEL-ROUTING-v3-OPENROUTER-DEEPSEEK`
(deepseek/deepseek-v4-pro-0813 via openrouter, no fallback). This task executed
as a single DeepSeek agent under goal_mode; the "independent review" is a
same-provider separate read-only-first pass (cross-provider unavailable, D-009).

```text
ROLE:                  camera/spatial author + implementer (C5)
REQUESTED_PROVIDER:    openrouter
REQUESTED_MODEL:       deepseek/deepseek-v4-pro-0813
ACTUAL_MODEL_ID:       deepseek/deepseek-v4-pro-0813 (runtime; this agent's session)
EFFORT_NORMALIZED:     MAX (spatial/placement/coverage/extrinsics)
EFFORT_PROVIDER_VALUE: max
MODEL_REASON:          camera placement, coverage, collision, extrinsics convention
FALLBACK_OCCURRED:     no
CROSS_PROVIDER_REVIEW: false  # D-009 open; same-provider session separation only

ROLE:                  independent reviewer (separate read-only-first pass)
REQUESTED_MODEL:       deepseek/deepseek-v4-pro-0813
EFFORT_NORMALIZED:     MAX
CROSS_PROVIDER_REVIEW: false
```

## What was built

New `src/pwa/camera/` package (12 modules), mirroring the PLAN-003 `geometry`
package structure and immutable-derived-run discipline:

- `config.py` — normative camera defaults (1.35 m height, 0.35 m wall / 0.20 m
  opening clearance, yaw 0, 2048x1024, batch 8) + resource bounds.
- `types.py` — `Room`, `Wall`, `Opening`, `SceneGeometry`, `Viewpoint`.
- `findings.py` — append-only `CAM_*` vocabulary with `(severity, tier)`.
- `load.py` — scene_geometry 1.0.0 → `SceneGeometry` with bounds/finiteness guards.
- `geometry.py` — pure-stdlib point-in-polygon, centroid, segment/point distance.
- `placement.py` — free-space resolver, deterministic pull-inward, coverage, collision.
- `extrinsics.py` — camera-to-world 4x4 (verified against golden fixture), formatting.
- `adjacency.py` — door-separated-room adjacency graph + map draft.
- `overlay.py` — deterministic top-down coverage SVG (G3 gate).
- `report.py` — coverage + camera run reports.
- `run_builder.py` — immutable camera-run orchestration (byte-copy source, staging,
  atomic finalize, containment checks).
- `cli.py` — `python -m pwa.camera.cli`.

## Key design decision (recorded)

The adjacency warn `CAM_MAP_ADJACENCY_UNRESOLVED` (an exterior door, or a door
that does not connect two covered rooms) is **informational** and does **not**
downgrade the run to `partial`. The G3 gate is coverage + no-collision +
extrinsics (all error tier §11 AC); a normal interior scene has exterior doors,
and treating them as run-dirtying would make every real run "partial". The warn
is still fully reported in `coverage-report.json` findings and the camera report.

Layer-A canonical result: 2 rooms → 2 centroids `(2.5,3.0)` / `(6.5,3.0)`,
1 interior edge `[0000,0001]`, start `0000`, 1 exterior door warn
(`go-9d050af60afc`), all 5 coverage/collision/extrinsics checks `true`.

## Extrinsics convention (verified against golden fixture)

Derived the camera-to-world rotation for yaw θ so that camera-forward maps to
`(sin θ, -cos θ, 0)`, camera-up stays +Z, and `R[:,1]==(0,0,-1)` (OpenCV +Y down).
Re-derived and machine-checked against `tests/golden/panoworld_demo_subset/
viewpoints/0000/extrinsics.txt` (theta ≈ 73.74°): byte-level agreement, and
`check_extrinsics_matrix` returns `[]` for both the golden and the re-built matrix.

## Evidence (AC mapping)

- AC-1..AC-12: see `evidence/PLAN-004/reviews/independent-correctness-review-*.md`.
- Canonical run: `evidence/PLAN-004/camera-run/cam-layer-a-dxf-1/`.
- Tests: `tests/unit/test_camera_planner.py` (unit), `tests/integration/test_camera_run.py`.