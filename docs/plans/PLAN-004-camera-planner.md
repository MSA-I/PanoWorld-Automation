# PLAN-004 — Camera Planner

- Plan ID: `PLAN-004-camera-planner`
- Status: **`APPROVED`** — drafted by the orchestrator under Full Part-1 delegated authority; independent read-only-first review returned APPROVE; **Moshe approved PLAN-004 + ADR-0008 on 2026-08-18** (kanban comment). G3 Camera Gate still required before merge.
- Kanban: `t_9734e83f` (`P1-04 camera planning and extrinsics`, board `panoworld-dev`)
- Policy: `MODEL-ROUTING-v3-OPENROUTER-DEEPSEEK` (per docs/06, 08, 09, 10). The card body's "Opus leads / Codex implements / GPT reviews" language is **stale** (see §17).
- Consumes: `scene_geometry` 1.0.0 (PLAN-003 output, frozen) + `HANDOFF-PLAN-003-to-PLAN-004-001`.
- Produces: `camera_plan` 1.0.0 artifacts + deterministic per-viewpoint extrinsics (`extrinsics.txt` camera-to-world 4×4, Z-up world, OpenCV camera axes) + `map JSON` draft + coverage/collision reports + evidence for the G3 Camera Gate.
- Boundary: **Part 1 local only**. G7/G8, H200/GPU, cloud, remote and spending remain **DEFERRED TO PART 2**.

## 1. Goal

Build the deterministic, local, reviewable **C5 Camera Planner**: given one immutable
`scene_geometry` 1.0.0 white model (rooms as 2D polygons, walls as centrelines with
thickness/height, openings with centre/width/height/sill), place a valid set of viewpoints
in free space, prove every target room is covered, prove zero wall/opening collision, emit
a camera-to-world 4×4 extrinsics matrix per viewpoint, and return the adjacency graph
(`edges` + `start_viewpoint`) the Map JSON and downstream rendering (PLAN-005) need.

This is the **G3 Camera Gate** of the pipeline (docs/08: coverage, visibility, no-collision,
extrinsics). It is the last purely-structural stage before any raster output; it must fail
closed rather than silently misplace a camera.

## 2. Current verified state

- PLAN-003 (Geometry Compiler) is `APPROVED` and **merged to main as `b137f3b`** after Moshe's
  G2 Geometry Gate approval. The frozen `scene_geometry` 1.0.0 schema is authoritative.
- Canonical geometry artifact exists and is hash-bound:
  `evidence/PLAN-003/geometry-run/geometry/scene_geometry.json` — `artifact_id
  geo-layer-a-dxf-1:scene_geometry`, `content_hash sha256:d2147f3c…b2971`, 2 rooms
  (`gr-0647acdd02a3` 5×6, `gr-f9c1af865cc3` 3×6), 5 walls, 4 openings (2 doors, 2 windows).
- Output contracts are **already frozen** from PLAN-000/PLAN-001:
  - `schemas/camera_plan/v1/camera_plan-1.0.0.schema.json` — requires `resolution{width,height}`,
    `viewpoints[{id,position[,yaw_deg,room_id]}]`, `edges[[a,b]]`, `start_viewpoint`,
    `max_views_per_lrm_batch`; optional payload `camera_height_m` (default 1.35).
  - Extrinsics convention (verified against the vendored `panoworld_demo_subset` golden fixture):
    **camera-to-world** 4×4, **Z-up world**, **OpenCV camera axes** — `R[:,1] == (0,0,-1)` (camera
    +Y maps to world -Z), `t_z = camera height`. The golden `viewpoints/0000/extrinsics.txt`
    has translation `(0.72375, -1.055, 1.35)`, i.e. a **1.35 m camera height**, matching the
    `camera_height_m` schema default.
  - `pwa.validator.check_extrinsics_matrix` already encodes the invariants the planner must
    satisfy: invertible, orthonormal, right-handed, `R[:,1]≈(0,0,-1)` (Z-up), last row
    `[0,0,0,1]`, camera-height outlier detection.
- Environment (unchanged from PLAN-003): venv Python 3.11.15; `numpy` locked; no new
  dependency is needed — camera placement is pure deterministic numpy/shapely-free polygon math.
- Baselines: PLAN-003 closed at **420 tests passing** (393 + 27 geometry).

## 3. Inputs (stable, from PLAN-003)

| Artifact | Schema | Notes |
|---|---|---|
| `scene_geometry.json` | `scene_geometry` 1.0.0 | rooms (id, polygon[point2], floor_z, ceiling_z), walls (id, start, end, height_m, thickness_m), openings (id, type door|window, wall_id, center, width_m, height_m, sill_m) |
| `assumptions.json` | `assumptions` 1.0.0 | accumulated pipeline assumptions (stage=geometry) |
| contracts `error_codes.md` | — | `PARSE_*` + `GEOM_*` vocabulary append-only |

The planner consumes **one** immutable geometry artifact per run (same single-input discipline
as PLAN-002 → PLAN-003).

## 4. Outputs and binding contracts

One immutable derived **camera run** per compilation:

```text
runs/<cam-run-id>/
  project/source-geometry.json      # byte-copy of the consumed scene_geometry artifact
  camera/camera_plan.json           # camera_plan 1.0.0, Z-up, meters
  camera/assumptions.json           # assumptions 1.0.0 (camera stage entries)
  camera/coverage-report.json       # per-room coverage + collision + adjacency checks
  camera/camera-report.json         # run report with metrics + gate results
  camera/map.json                   # draft Map JSON draft ({start_viewpoint: [neighbors...]})
  camera/extrinsics/                # one extrinsics.txt (4x4, camera-to-world) per viewpoint
  camera/overlay-cameras.svg        # top-down coverage overlay (evidence)
```

- `camera_plan.json` validates against the frozen 1.0.0 schema and carries the standard envelope
  (same `_artifact` discipline as PLAN-003: `schema_id`, `schema_version`, `artifact_id`,
  `project_id`, `run_id`, `created_at`, `producer`, `inputs[]`, `content_hash`, `status`, `errors`).
- Each `extrinsics.txt` is exactly 4 lines of 4 space-separated decimal numbers (matching the
  golden fixture), camera-to-world, and must satisfy `check_extrinsics_matrix` with zero error codes.
- Viewpoint IDs are zero-padded `%04d` (e.g. `0000`, `0001`) to match the golden fixture naming;
  `start_viewpoint` is the first placed viewpoint (deterministic ordering).
- `content_hash` is the canonical deterministic hash over the payload (existing `compute_content_hash`).

## 5. Scope

- New `src/pwa/camera/` package: free-space/placement resolver, coverage scorer, collision
  validator, extrinsics builder (position + yaw → 4×4), coverage-report builder, camera-run
  builder, CLI, and a top-down coverage overlay.
- Append-only `CAM_*` error vocabulary added to `contracts/error_codes.md` (additive; no mutation
  of `PARSE_*`/`GEOM_*`).
- Deterministic default resolution (camera height, clearance, coverage threshold) recorded in
  `assumptions.json` (never silent).
- Unit/property/adversarial tests for: placement in free space, wall/opening collision rejection,
  coverage of every room, adjacency graph correctness, determinant orthonormality of extrinsics,
  byte-identical determinism on rerun.
- Top-down coverage overlay for the G3 visual/camera gate.
- Planning records, independent-session review, and **human G3 Camera Gate / Moshe PLAN approval**
  per the task body.

## 6. Non-goals

- No rendering of `place_image`/`place_depth`/`place_depth_scale`/BlenderProc (PLAN-005).
- No style, source-panorama, packaging or PanoWorld execution.
- No path-planning/trajectory optimisation (the graph edges encode adjacency only; trajectory is
  a render/QA concern downstream).
- No curved walls, multi-storey, or rotated/angled walls (PLAN-002/PLAN-003 boundary upheld).
- No new dependency beyond the locked set (`numpy`, stdlib; **no** `shapely` unless an ADR adds it —
  polygon point-in-polygon and segment distance are implemented with locked numpy/stdlib).
- No mutation of finalized PLAN-003 geometry artifacts or historical evidence.
- No merge or push before independent review + Moshe's approval.

## 7. Camera placement, coverage, collision and extrinsics — the normative section

This is the `MAX`-effort spatial/contract core. Everything is subject to the G3 gate (§11) and is
authored (and independently reviewed) as the critical geometry/contract content.

### 7.1 Units and frame

- Inherit PLAN-003 §7.1: metres, `up_axis = "z"`, XY floor plane, wall height in +z. No coordinate
  transform beyond the straight 2D→3D lift (room polygon XY stays, camera Z = height).
- Camera frame convention (the golden-fixture + validator convention): **camera-to-world 4×4**,
  **Z-up world**, **OpenCV camera axes**. Camera coordinate axes: +X right, +Y down, +Z forward
  (out of the lens). Therefore `R[:,1]` (the world column for camera +Y) `== (0,0,-1)`, and the
  translation column is the camera's world position. This is exactly what
  `check_extrinsics_matrix` verifies; the planner must produce matrices that satisfy it.

### 7.2 Camera height and clearance

- **Camera height default: `1.35 m`** (matches the `camera_height_m` schema default and the golden
  fixture translation `z = 1.35`). Recorded in `assumptions.json`.
- **Wall clearance: `0.35 m`** — a camera may not sit closer than `thickness_m/2 + 0.35 m` to any
  wall centreline, measured in the floor plane. This keeps the lens out of the wall body and gives
  a usable frustum depth. Recorded as an assumption.
- **Opening clearance: `0.20 m`** — a camera may not sit within `0.20 m` of a door/window opening
  centre (floor-plane distance), so viewpoints never block or sit inside an opening. Recorded as
  an assumption.

### 7.3 Candidate placement and free-space resolution

1. **Candidates** — per room, the primary candidate is the room **planar centroid** (area-weighted,
   computed over the room polygon). If that point is valid (see 2), it is used. Corridor/doorway
   candidates and extra viewpoints are **out of scope for Part 1** (PLAN-003 §6 boundary; a single
   centroid viewpoint per room satisfies coverage on the Layer-A fixture).
2. **Free-space validity** — a candidate is valid iff *all* of:
   - it lies strictly inside the room polygon (point-in-polygon with boundary as *inside*, small
     epsilon `1e-6 m`; on-boundary is rejected);
   - its distance to every wall centreline ≥ `thickness_m/2 + 0.35 m` (see §7.2);
   - its distance to every opening centre ≥ `0.20 m`.
   - If the centroid is invalid (e.g. a very thin room or an opening near the middle), the resolver
   pulls the candidate inward along the vector from the nearest violated wall until valid, bounded
   by a maximum distance; if no valid point exists within the bound, the room is reported
   `CAM_UNCOVERED_ROOM` (fail-closed, not silent skip).
3. **Determinism** — candidate selection and any pull-back must be a pure function of the input
   geometry (no randomness); rerunning yields byte-identical output.

### 7.4 Coverage scoring

- **Coverage target: every room is covered by ≥ 1 viewpoint** (Part-1 Layer-A fixture has 2 rooms →
  ≥ 2 viewpoints). The coverage report lists, per room, its assigned viewpoint(s) and the
  point-in-polygon + clearance outcome.
- **Coverage threshold** is an explicit, non-weakened acceptance criterion (§11 AC), and any target
  room with zero valid viewpoints fails the G3 gate via `CAM_UNCOVERED_ROOM`.

### 7.5 Collision validation

- A viewpoint is collision-free iff it satisfies §7.2 wall/opening clearances and §7.3 in-room
  placement. Any violation is a `CAM_*` error/warning in the coverage report (fail-closed for
  errors). The G3 gate requires **zero collision errors and zero uncovered rooms**.

### 7.6 Extrinsics construction

- For a viewpoint at world position `(x, y, 1.35)` with yaw `θ` (rotation about Z), the
  camera-to-world rotation maps the camera-forward (+Z) axis to world `(sin θ, -cos θ, 0)` — the
  horizon in the Z-up frame — and the camera-up is world +Z, subject to the OpenCV +Y-down
  relation `R[:,1] == (0,0,-1)`.
- The **default yaw** is deterministic: for a room centroid viewpoint, yaw is `0` (camera +Z forward
  aligned to world +X plane) unless an explicit per-room override exists (none in Part 1). Recorded
  in `assumptions.json`.
- The resulting 4×4 is written as `extrinsics.txt` (4 lines × 4 columns) and **must pass
  `check_extrinsics_matrix`** with zero error codes. This ties the planner output directly to the
  already-reviewed validator, so extrinsics correctness is machine-checked, not asserted.

### 7.7 Adjacency graph and Map JSON draft

- **Edges** encode room adjacency through shared **doors**: two rooms connected by a door opening
  (the opening `wall_id` belongs to the wall separating them, opening type `door`) produce an
  `edge [roomA_viewpoint, roomB_viewpoint]`.
- **`start_viewpoint`** is the viewpoint of the first room in deterministic order (sorted by room
  id, or the single-room fallback).
- The `map.json` draft follows the golden `map_panoworld0.json` shape: `{ "<start_id>": [<neighbor_ids...>] }`, with viewpoint IDs zero-padded `%04d`.

## 8. Task breakdown and ownership

Ordered by dependency; each task is a bounded dispatch with a single implementer and a separate
reviewer session (the same G-t1..G-t7 shape PLAN-003 used).

| # | Task | Owner role | Model / effort | Outputs |
|---|---|---|---|---|
| C-t1 | Write `CAM_*` error vocabulary (ADR + `contracts/error_codes.md` additive block) | Architect | Pro `MAX` | ADR + error table |
| C-t2 | `src/pwa/camera/types.py` + placement/free-space resolver + coverage scorer | Implementer | Pro `MAX` | code + tests |
| C-t3 | Collision validator + extrinsics builder (position+yaw → 4×4) | Implementer | Pro `MAX` | code + tests |
| C-t4 | Camera-run builder + CLI (immutable derived run, hash binding) | Implementer | Pro `HIGH–EXTRA` | code + tests |
| C-t5 | Coverage overlay render + map JSON draft | Implementer | Pro `HIGH–EXTRA` | code + evidence |
| C-t6 | Adversarial/property/determinism tests + full-suite green | Tester | Pro `HIGH–EXTRA` | tests + report |
| C-t7 | Independent review (read-only-first) + bounded rework | Reviewer | Pro `MAX`, separate session | review report |

After C-t7, the G3 Camera Gate evidence (overlay + coverage/collision report + extrinsics) is
presented to **Moshe** for approval before merge (mirroring G2).

## 9. Determinism and identity

- Pure deterministic Python: same `scene_geometry` → byte-identical `camera_plan.json`, reports,
  `extrinsics/*.txt`, and overlays (verified by a rerun test).
- Viewpoint IDs are deterministic zero-padded ordinals in placement order (stable across reruns of
  the same input), not content hashes, because camera IDs must match the golden `%04d` naming.
- No silent merge/renumber of rooms or viewpoints; a duplicate or colliding camera position is a
  `CAM_DUPLICATE_ENTITY` (fail-closed).

## 10. Acceptance criteria (measurable)

All must be `MET` with evidence before the gate; a `MET` is never asserted without a real artifact
or exit code.

- **AC-1** The planner consumes one `scene_geometry` 1.0.0 artifact and emits `camera_plan` 1.0.0
  that validates against the frozen schema with 0 errors.
- **AC-2** Every viewpoint lies inside its room polygon and satisfies the §7.2 wall/opening
  clearances (no collision); all camera defaults (1.35 m height, 0.35 m / 0.20 m clearances, yaw 0)
  are recorded in `assumptions.json`.
- **AC-3** Coverage: every room has ≥ 1 assigned viewpoint; no `CAM_UNCOVERED_ROOM`.
- **AC-4** Every `extrinsics.txt` is a valid camera-to-world 4×4 that passes
  `check_extrinsics_matrix` with zero error codes (orthonormal, right-handed, Z-up, correct 4th row).
- **AC-5** Determinism: two identical runs produce byte-identical `camera_plan.json`
  (`content_hash` equal), reports, and extrinsics.
- **AC-6** The run is immutable and derived: no write to the consumed geometry artifact; source
  geometry byte-copied under `runs/<cam-run-id>/project/`.
- **AC-7** Full fresh test suite passes (`env -u PYTHONPATH ./.venv/Scripts/python.exe -m pytest`),
  exit 0, on the reviewed commit.
- **AC-8** A top-down coverage overlay (SVG/PNG) is produced for the G3 gate and is deterministic.
- **AC-9** At least one adversarial input (degenerate/thin room, opening near centroid, viewpoint
  on wall) is covered by a failing-closed test with the correct `CAM_*` code.
- **AC-10** No `pyproject.toml`/`uv.lock` change and no new dependency beyond the locked set unless
  a separate ADR is recorded first.
- **AC-11** No change to the `PARSE_*`/`GEOM_*` vocabulary or frozen schemas; `CAM_*` is purely
  additive.
- **AC-12** The **G3 Camera Gate (human)** — the coverage overlay + coverage/collision report +
  sample extrinsics are presented to **Moshe** and approved before merge.

## 11. Tests and evidence expected

- Unit tests per module (placement/free-space, coverage, collision, extrinsics, adjacency).
- Property test over the Layer-A fixture and a re-derived equivalent (adapter equivalence input).
- Adversarial/failure fixtures (at least the AC-9 set).
- Golden `camera_plan` + `extrinsics` with pinned canonical hashes.
- Evidence under `evidence/PLAN-004/`: planning-session record, independent plan review, run
  report, tests, coverage overlay, `assumptions.json`, and the G3 gate record.

## 12. Security, licensing, compatibility, data risks

- Pure Python + numpy; no Blender shell-out in this plan (Blender/render is PLAN-005). No network,
  no eval of LLM content.
- No new license exposure (no new dependency without an ADR).
- No customer-sensitive data; fixture is the synthetic Layer-A geometry.
- Windows path/encoding constraints (non-ASCII project root) already handled by the PLAN-000
  baseline; the camera package adds no new path assumptions.

## 13. Human gates and decisions required from Moshe

1. **PLAN approval** — this plan is `APPROVED-PENDING-MOSHE`: the independent-session review is
   required, but Moshe's approval is still required before any implementation (PLAN-004 is not
   auto-authorized; PLAN-003 set the precedent).
2. **G3 Camera Gate** — the coverage overlay + coverage/collision report + sample extrinsics must be
   presented to Moshe and approved before merge. This is the single gate delegation cannot fully
   substitute for (mirroring GC3-10/NA-4 and G2).
3. **Open decisions carried forward** (see `OPEN-DECISIONS.md`):
   - **D-009** independent review under DeepSeek-only policy — same-provider session separation is
     the interim policy; explicit cross-provider review remains blocked until Moshe decides.
   - **D-006** H200 cloud provider — **DEFERRED TO PART 2**.
4. Retained critical Geometry/Contract gates (fail-closed): any change to §7 normative geometry
   (camera height, clearances, placement, extrinsics convention, coordinate transform) requires a
   revised PLAN + explicit Moshe approval.

## 14. Rollback and cleanup

- Pre-merge: abandon the branch/worktree; finalized PLAN-003 artifacts remain untouched.
- Post-merge: retain `camera_plan` schema (already frozen), `CAM_*` codes, ADRs and evidence as
  append-only; never delete finalized camera runs automatically.
- No force-push, history rewrite, or destructive cleanup.

## 15. Handoff expected to next stage

`HANDOFF-PLAN-004-to-PLAN-005-001` (Render adapter / control assets) delivering `camera_plan.json`
+ per-viewpoint extrinsics as the stable input, with the same consumer-obligations rigor PLAN-002
and PLAN-003 used.

## 16. Definition of Done

Work is `DONE` only when: §10 acceptance criteria are `MET`; a fresh full suite passes (exit 0); at
least one failure path is exercised; an independent-session review returns `APPROVE`; `CAM_*`
vocabulary is updated (additive) and versioned; evidence is hash-bound and openable; the G3 human
camera gate is approved by Moshe; the handoff is written; the orchestrator merges; and
`PROJECT-STATE.yaml` + `PROGRESS.md` are updated in the same merge.

## 17. Model routing (canonical, DeepSeek/OpenRouter)

All roles route to `deepseek/deepseek-v4-pro-0813` through `openrouter` (docs/06, 08, 09, 10);
spatial/camera roles run at `MAX` effort; reporter-only work may use `deepseek/deepseek-v4-flash-0731`.

```text
ROLE:                              camera/spatial author (planning + implementation)
PROVIDER:                          openrouter
REQUESTED_MODEL:                   deepseek/deepseek-v4-pro-0813
ACTUAL_MODEL_ID:                   recorded from runtime metadata (never inferred from self-description)
EFFORT_NORMALIZED:                 MAX (spatial/placement/coverage/extrinsics)
EFFORT_PROVIDER_VALUE:             max
MODEL_REASON:                      camera placement, coverage, collision, extrinsics convention — C5
FALLBACK_PROVIDER:                 none (no silent fallback; block on unavailability)
FALLBACK_MODEL:                    none
CROSS_PROVIDER_REVIEW:             false  # D-009 remains open; same-provider session separation only

ROLE:                              independent reviewer (separate read-only-first session)
PROVIDER:                          openrouter
REQUESTED_MODEL:                   deepseek/deepseek-v4-pro-0813
EFFORT_NORMALIZED:                 MAX
CROSS_PROVIDER_REVIEW:             false
```

> **Stale-language note (recorded, not silently followed).** The Kanban card `t_9734e83f` body says
> "Opus leads spatial design; Codex implements algorithms and property tests; GPT performs
> correctness review". That wording predates the DeepSeek/OpenRouter campaign. The live, authoritative
> model policy (`PROJECT-STATE.yaml` `model_policy`, docs/06/08/09/10) mandates
> `deepseek/deepseek-v4-pro-0813` for all roles, `MAX` effort for spatial/camera work, and
> cross-provider review explicitly unavailable (`cross_provider_review_available: false`). The
> orchestrator follows the live policy and records the divergence here; a real provider/model
> mismatch still requires Moshe's approval.

## 18. Risks and explicit deferrals

- Camera height/clearances/yaw are determinism-serving defaults, not surveyed measurements; they are
  assumptions recorded in `assumptions.json` and surfaced at the G3 gate.
- Curved/angled walls and multi-storey remain unsupported (PLAN-002 boundary).
- Corridor/doorway extra viewpoints and full coverage-optimisation are out of Part-1 scope; a single
  centroid viewpoint per room is the Part-1 placement rule (sufficient for Layer-A).
- Cross-provider review is unavailable until D-009 is decided; same-provider session separation +
  deterministic evidence + the machine-checked extrinsics validator + human G3 gate are the
  compensating controls.
- G7/G8, H200/GPU, cloud, remote and spending remain **DEFERRED TO PART 2**.
