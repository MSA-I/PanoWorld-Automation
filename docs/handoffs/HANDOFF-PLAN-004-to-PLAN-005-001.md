# HANDOFF

- Handoff ID: `HANDOFF-PLAN-004-to-PLAN-005-001`
- Producer: PLAN-004 Camera Planner (C5)
- Producer status: `APPROVED (PLAN + ADR)` — pending G3 Camera Gate before merge
- Consumer: PLAN-005 Render adapter / control assets (Part 1, local; NOT auto-authorized by this handoff)
- Date: 2026-08-18
- Contract version: `camera_plan` 1.0.0 (frozen since PLAN-000/PLAN-001), `scene_geometry` 1.0.0 (consumed as-is)
- Model policy: MODEL-ROUTING-v3-OPENROUTER-DEEPSEEK

## What was delivered

PLAN-004 built the deterministic, local, reviewable C5 Camera Planner: given one
immutable `scene_geometry` 1.0.0 white model, it places one viewpoint per room
(area-weighted centroid, pulled inward when invalid), proves every target room
is covered, proves zero wall/opening collision, emits a camera-to-world 4x4
extrinsics per viewpoint, and returns the adjacency graph (edges + start
viewpoint) the Map JSON and downstream rendering (PLAN-005) need.

## What is stable

- `src/pwa/camera/` package (12 modules): placement/free-space resolver, coverage
  scorer, collision validator, extrinsics builder, adjacency graph, coverage
  overlay, camera-run builder, CLI (`python -m pwa.camera.cli`).
- `camera_plan` 1.0.0 output schema (consumed as-is; already frozen).
- Append-only `CAM_*` error vocabulary (`contracts/error_codes.md`); `PARSE_*`
  and `GEOM_*` untouched.
- Extrinsics convention: **camera-to-world 4x4, Z-up world, OpenCV camera axes**
  (`R[:,1]==(0,0,-1)`), camera height 1.35 m. Machine-checked against the golden
  fixture and `check_extrinsics_matrix`.
- Immutable derived run semantics: source geometry byte-copied, never mutated;
  staging → atomic finalize; containment checks on read and write.

## Artifacts

| Path | Schema/version | Description |
|---|---|---|
| `evidence/PLAN-004/camera-run/cam-layer-a-dxf-1/camera/camera_plan.json` | `camera_plan` 1.0.0 | Canonical camera plan (2 rooms → 2 viewpoints, 1 edge) |
| `.../camera/extrinsics/*.txt` | — | Per-viewpoint camera-to-world 4x4 |
| `.../camera/coverage-report.json` | — | Coverage + collision + adjacency checks |
| `.../camera/camera-report.json` | — | Run report (metrics + gate results) |
| `.../camera/map.json` | — | Draft map JSON `{start: [neighbors...]}` |
| `.../camera/assumptions.json` | `assumptions` 1.0.0 | Camera defaults (height/clearances/yaw/resolution/batch) |
| `.../camera/overlay-cameras.svg` | — | G3 gate coverage overlay |
| `docs/plans/PLAN-004-camera-planner.md` | — | Approved plan |
| `docs/decisions/ADR-0008-camera-planner-vocab-and-run-lifecycle.md` | — | CAM_* vocabulary + run lifecycle ADR |

## How to validate

```bash
# Full suite (554 passed):
env -u PYTHONPATH ./.venv/Scripts/python.exe -m pytest

# Reproduce the canonical run:
PYTHONPATH=src ./.venv/Scripts/python.exe -m pwa.camera.cli \
  --runs-root evidence/PLAN-004/camera-run \
  --source-geometry source-geometry.json \
  --cam-run-id cam-layer-a-dxf-1
```

## Test evidence

- Fresh closeout run 2026-08-18: **554 passed** (523 baseline + 31 camera),
  0 failures, exit 0.
- Camera subset: `test_camera_planner.py` + `test_camera_run.py` → 31 passed.

## Known limitations (honest, accepted — not defects)

- **Single centroid viewpoint per room.** Corridor/doorway extra viewpoints and
  full coverage-optimisation are out of Part-1 scope.
- **Default yaw 0.** No per-room orientation; recorded in assumptions.
- **Camera defaults are determinism-serving, not surveyed.** Height/clearances
  are assumptions surfaced at the G3 gate.
- **Straight / axis-aligned walls only** (PLAN-002 boundary upheld).
- **Exterior doors** yield `CAM_MAP_ADJACENCY_UNRESOLVED` (warn, fail-open) —
  informational, does not affect coverage/collision/extrinsics gate.

## Consumer obligations (PLAN-005)

- Consume ONE immutable `camera_plan` + per-viewpoint `extrinsics/*.txt` per run.
- Respect extrinsics convention: camera-to-world, Z-up, OpenCV axes, 1.35 m height.
- Do not modify the `camera_plan` schema or `CAM_*` vocabulary without a new
  approved PLAN and additive-only versioning analysis (ADR-0008).
- PLAN-005 rendering is **NOT auto-authorized** by this handoff: it requires its
  own PLAN and Moshe's approval.

## Open blockers

The **G3 Camera Gate (human — Moshe)** is outstanding: present the coverage
overlay + coverage/collision report + sample extrinsics for approval before merge.
G7/G8 and H200/GPU/cloud/remote remain **DEFERRED TO PART 2**.

## Approval

- Producer status: `APPROVED (PLAN + ADR)` — pending G3 Camera Gate.
- Independent review: APPROVE (same-provider separate pass; cross-provider unavailable per D-009).
- Orchestrator status: 554-passing suite, git diff additive-only, boundaries held.