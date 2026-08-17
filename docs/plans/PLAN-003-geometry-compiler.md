# PLAN-003 — Geometry Compiler

- Plan ID: `PLAN-003-geometry-compiler`
- Status: **`APPROVED`** — Moshe approved 2026-08-14 (comment on t_c19e7136, bound to sha256 a122367ba14d2c48f09c48e94adb0448b114375c6dfc187410541237224c3b44). Implementation of G-t1..G-t7 authorized in Part-1 local scope; G2 Geometry Gate before merge.
- Kanban: `t_c19e7136` (`P1-03 geometry compiler`, board `panoworld-dev`)
- Policy: `MODEL-ROUTING-v3-OPENROUTER-DEEPSEEK` (per docs/06, 08, 09, 10). Historical `MODEL-ROUTING-v1` cross-provider records remain dated history and are not rewritten.
- Consumes: `HANDOFF-PLAN-002-to-PLAN-003-001`, contracts bundle `1.2.0`, `floorplan_parse` 1.1.0 artifacts.
- Produces: `scene_geometry` 1.0.0 artifacts (Z-up white model) + top-down overlay + evidence for the G2 Geometry Gate (human approval).
- Boundary: **Part 1 local only**. G7/G8, H200/GPU, cloud, remote and spending remain **DEFERRED TO PART 2**.

## 1. Goal

Build the deterministic, local, reviewable compiler that turns one immutable `floorplan_parse`
artifact (rooms as 2D polygons, walls as 2D centrelines, openings as centre + width + wall ref)
into a schema-valid `scene_geometry` white model: walls with thickness/height, rooms, and openings
with height/sill, in a Z-up metric frame, ready for the Camera Planner (PLAN-004) and
headless-Blender export (PLAN-005 rendering). This is C4 in `ARCHITECTURE.md`, and it is the G2
Geometry Gate of the pipeline.

The compiler resolves exactly the facts PLAN-002 deliberately left open:

- **Wall thickness** — PLAN-002 delivered centrelines only (no thickness field). PLAN-003 owns it
  (`HANDOFF` DR-001: interior walls 0.10 m; door depth = host wall thickness).
- **Wall/opening height** — not present in the 2D parse; PLAN-003 assigns deterministic defaults.
- **Closed topology** — room polygons must share walls/vertices consistently; openings must sit on
  their declared wall within the approved tolerance.

The plan intentionally proves topology, dimensions, determinism and G2 evidence from the frozen
Layer-A fixture before touching any camera or render work.

## 2. Current verified state

- PLAN-002 is `ACCEPTED (G1 claimed)`, approved by Moshe 2026-08-13. Its parser output is handed to
  PLAN-003 via `docs/handoffs/HANDOFF-PLAN-002-to-PLAN-003-001.md`.
- Canonical parse artifacts exist and are hash-bound:
  - `evidence/PLAN-002/parse/layer-a-1-dxf.json` (DXF adapter) — 2 rooms, 5 walls, 4 openings.
  - `evidence/PLAN-002/parse/layer-a-1-raster.json` (annotation adapter) — identical canonical
    projection hash (`e5041ddc…`), proving adapter equivalence.
- Input schema `floorplan_parse` is frozen at **`1.1.0`** (`schemas/floorplan_parse/v1/…-1.1.0.schema.json`,
  `content` const `1.1.0`; the canonical Layer-A fixture `layer-a-1-dxf.json` carries `schema_version: "1.1.0"`).
  NB: the `HANDOFF` header cites "floorplan_parse 1.1.1" — that citation predates the frozen 1.1.0 schema
  file and is recorded here as a version-citation drift; the compiler consumes the actual frozen **1.1.0**
  schema. Output schema `scene_geometry` 1.0.0 is frozen (`schemas/scene_geometry/v1/…-1.0.0.schema.json`),
  already Z-up (`up_axis: "z"`), and requires walls with `height_m`/`thickness_m` and openings with
  `height_m`/`sill_m`.
- Environment verified 2026-08-13: venv Python 3.11.15, `ezdxf==1.4.4`, `pypdfium2`, Pillow locked;
  **Blender 5.1 installed** at `C:\Program Files\Blender Foundation\Blender 5.1\blender.exe`
  (embedded Python 3.13). The local machine does **not** run PanoWorld inference.
- Baseline test suite: 393 passing on `main` (PYTHONPATH-unset run), 2026-08-13.

## 3. Inputs (stable, from PLAN-002)

| Artifact | Schema | Hash (canonical) | Notes |
|---|---|---|---|
| `layer-a-1-dxf.json` | `floorplan_parse` 1.1.0 | see PLAN-002 acceptance | DXF adapter output |
| `layer-a-1-raster.json` | `floorplan_parse` 1.1.0 | same canonical projection | annotation adapter output |
| `overlay.svg` | — | `a181228d…` | source-aligned 2D overlay (reference) |
| contracts `error_codes.md` | — | append-only | `PARSE_*` vocabulary frozen |

The compiler consumes **one** immutable parse artifact per compilation (no cross-edit identity).

## 4. Outputs and binding contracts

One immutable derived **geometry run** per compilation:

```text
runs/<geo-run-id>/
  project/source-parse.json               # byte-copy of the consumed floorplan_parse artifact
  geometry/scene_geometry.json            # scene_geometry 1.0.0, Z-up, meters
  geometry/assumptions.json               # assumptions 1.0.0 (defaults applied, decisions)
  geometry/overlay-topdown.png            # top-down white-model render (evidence)
  geometry/geometry-report.json           # run report with metrics + gate results
  geometry/topology-report.json           # closed-topology + dimension checks
```

- `scene_geometry.json` must validate against the frozen 1.0.0 schema and carry the standard
  envelope (`schema_id`, `schema_version`, `artifact_id`, `project_id`, `run_id`,
  `created_at`, `producer`, `inputs[]`, `content_hash`, `status`, `errors`).
- Walls gain deterministic `thickness_m` and `height_m`; openings gain `height_m` and `sill_m`.
- `content_hash` is the canonical deterministic hash over the payload (existing `compute_content_hash`).

## 5. Scope

- New `src/pwa/geometry/` package: 2D→3D compiler, wall builder, opening builder, room classifier,
  topology validator, dimension validator, geometry-run builder, CLI, and a headless-Blender export
  stub (writes `.glb`) gated behind a flag that **defaults off** until Blender integration is
  separately reviewed in PLAN-005.
- Deterministic default resolution with explicit `assumptions.json` records (not silent defaults).
- Append-only `GEOM_*` error vocabulary added to `contracts/error_codes.md` (additive; no
  mutation of the `PARSE_*` table).
- Unit/property/adversarial tests: topology closure, dimension consistency, determinism
  (byte-identical rerun), opening-on-wall placement, degenerate inputs.
- Top-down SVG/PNG overlay for the visual/geometry gate.
- Planning records, independent-session review, and **human G2 Geometry Gate** before merge.

## 6. Non-goals

- No camera planning, covering, collision-avoidance or extrinsics (PLAN-004).
- No rendering of place_image/depth/scale or BlenderProc integration (PLAN-005).
- No style, source-panorama, packaging or PanoWorld execution.
- No curved walls, arcs, splines, multi-storey, or rotated/angled walls (PLAN-002 boundary upheld).
- No new CLI dependency beyond what PLAN-002 already locked (`ezdxf`, `pypdfium2`, Pillow, `numpy`
  if already present — verified against `uv.lock` before use; no new `pyproject.toml`/`uv.lock`
  change without an ADR).
- No OCR, learned geometry inference, model weights, downloads or network access.
- No automatic snapping/merging of walls beyond the closed-topology rules below (fail-closed on
  ambiguity, never silent repair).
- No mutation of finalized PLAN-002 parse artifacts or historical evidence.
- No merge or push before independent review + Moshe's G2 approval.

## 7. Spatial representation, units and topology (the normative geometry)

This is the `MAX`-effort spatial core. Everything below is subject to the closed-topology and
dimension invariants in §11 and is authored (and independently reviewed) as the critical
geometry/contract content.

### 7.1 Units and frame

- Units: **meters** (`units: "m"`), matching the parse output. Rounding quantum `0.0001 m` (0.1 mm).
- Frame: `up_axis: "z"` (fixed by the scene_geometry schema; matches upstream PanoWorld Z-up,
  verified in PLAN-000 panoworld-compat #2). XY is the floor plane; Z is height.
- The 2D parse coordinates become `(x, y, 0)` floor coords; wall height extends in `+z`.
- No coordinate transform is applied beyond the straight 2D→3D lift — the parse already normalizes
  to meters and a consistent frame. Any transform change is a critical Geometry gate.

### 7.2 Walls — thickness and height

- PLAN-002 walls are **centrelines** (`start`, `end` in 2D). PLAN-003 derives a solid wall body of
  thickness `thickness_m` centred on that line, extruded to `height_m`.
- **Thickness default (DR-001): `0.10 m` interior walls.** Applied uniformly unless a future source
  contract carries a per-wall thickness (the frozen `floorplan_parse` 1.1.0 schema exposes an *optional*
  `thickness_m` on walls, but no field value is present in any Part-1 fixture). Recorded in
  `assumptions.json`.
- **Door depth = host wall thickness** (`HANDOFF` DR-001): a door opening's depth equals the
  thickness of the wall it is placed on.
- **Height default: `2.60 m`** for full-height walls. The required payload field
  `default_ceiling_height_m` is bound to the same **`2.60 m`** (deterministic, recorded in
  `assumptions.json`). Windows and doors are *not* full height (see §7.3); they carve the wall body
  they sit on.
- Wall body geometry in the `scene_geometry` payload is the **centreline + thickness + height**
  representation the schema requires (`start`, `end`, `height_m`, `thickness_m`); the solid quad /
  box derivation (corners offset by `thickness_m/2` normal to the centreline) is computed and
  checked for topology but the payload stays in the schema's own wall vocabulary.

### 7.3 Openings — door and window placement

An opening resolve requires, in order and fail-closed:

1. **wall reference resolution** — `wall_id` must name exactly one wall (a missing ref →
   `GEOM_OPENING_UNRESOLVED_WALL`; an ambiguous ref → fail-closed, no silent pick).
2. **on-wall placement** — the opening centre must lie on the host wall segment within
   `0.02 m` (the PLAN-002 endpoint tolerance), and its span must fit within the wall length under
   the approved projected-width slack (the width projected onto the wall direction; degenerate or
   negative projection fails closed, no new error invented — reuse of `PARSE_RESOURCE_LIMIT` is
   forbidden; use the `GEOM_*` vocabulary).
3. **vertical placement** — deterministic defaults, recorded in `assumptions.json`:
   - door: `height_m = 2.10 m`, `sill_m = 0.00 m`;
   - window: `height_m = 1.20 m`, `sill_m = 0.90 m`.
4. **fit** — `sill_m + height_m` must not exceed the host wall height (else
   `GEOM_OPENING_ABOVE_WALL`).

### 7.4 Rooms and closed topology

- Rooms are the parse `polygon` arrays. The compiler must verify, not assume, closed topology:
  - every room polygon is closed (first == last after the existing canonical closing rules) and
    simple (no self-intersection, non-zero area) — reuse of PLAN-002 invariants where the
    vocabulary still applies, otherwise a new `GEOM_*` code;
  - walls are shared consistently: a wall shared by two rooms appears once in the wall list and its
    endpoints coincide with vertices of both room polygons (within `0.02 m`);
  - the union of walls closes every room boundary (a room edge with no supporting wall and not
    matched to an adjacent room is a `GEOM_OPEN_ROOM_BOUNDARY` warning, matching PLAN-002's
    fail-open `PARSE_ROOM_BOUNDARY_UNMATCHED` semantics — the geometry gate still runs but reports
    it, so no silent acceptance).

## 8. Blender architecture

- The geometry compiler is **pure, deterministic Python + JSON** — it never requires Blender to
  produce `scene_geometry.json` or the topology/dimension reports.
- A separate, flag-gated `--export-blend` / `--export-glb` path shells out to the pinned local
  Blender 5.1 headless binary (`blender --background --python tools/export_scene_geometry.py`) to
  write an optional `.glb` white model for human visual review and as forward evidence for
  PLAN-005. **This path is default-off** and is itself reviewed in PLAN-005 before it becomes part
  of any accepted gate; in PLAN-003 it is exercised only to produce visual evidence, and its output
  is identical in intent (coordinates) to the JSON.
- Blender scripts are repo-owned, deterministic, and run with `--background` + factory settings;
  no eval of LLM-generated content, no network in the export path (TB-2, TB-5).
- If the headless Blender run is unavailable or fails, the geometry gate does **not** fail — the
  JSON + top-down SVG/PNG (generated by the deterministic compiler itself, without Blender) remain
  the authoritative G2 evidence, and the Blender export is recorded as a deferral.

## 9. Determinism and identity

- The compiler is deterministic: same input artifact → byte-identical `scene_geometry.json` and
  reports (verified by a rerun test).
- Entity IDs in the output are derived from the stable input IDs (e.g. `w-…` → geometry wall id
  derived by the same content-hash rule PLAN-002 uses for stable content-derived IDs). IDs are
  stable across reruns of the same input, not across geometry edits — matching the `HANDOFF`
  consumer obligation (consume ONE immutable parse artifact; no cross-edit identity).
- No wall/room silently merged or renumbered to resolve a collision; a collision is
  `GEOM_DUPLICATE_ENTITY` (fail-closed), mirroring `PARSE_DUPLICATE_ENTITY`.

## 10. Task breakdown and ownership

Ordered by dependency; each task is a bounded dispatch with a single implementer and a separate
reviewer session.

| # | Task | Owner role | Model / effort | Outputs |
|---|---|---|---|---|
| G-t1 | Write `GEOM_*` error vocabulary (ADRs + `contracts/error_codes.md` additive block) | Architect | Pro `MAX` | ADR + error table |
| G-t2 | `src/pwa/geometry/types.py` + wall/opening/room builder (thickness, height, defaults) | Implementer | Pro `HIGH–EXTRA` | code + tests |
| G-t3 | Topology + dimension validator (closure, sharing, on-wall fit) | Implementer | Pro `HIGH–EXTRA` | code + tests |
| G-t4 | Geometry-run builder + CLI (immutable derived run, hash binding) | Implementer | Pro `HIGH–EXTRA` | code + tests |
| G-t5 | Top-down overlay render + Blender export stub (default-off) | Implementer | Pro `HIGH–EXTRA` | code + evidence |
| G-t6 | Adversarial/property/determinism tests + full-suite green | Tester | Pro `HIGH–EXTRA` | tests + report |
| G-t7 | Independent review (read-only-first) + bounded rework | Reviewer | Pro `MAX`, separate session | review report |

## 11. Acceptance criteria (measurable)

All must be `MET` with evidence before the gate; a `MET` is never asserted without a real artifact
or exit code.

- **AC-1** The compiler consumes one `floorplan_parse` 1.1.0 artifact and emits
  `scene_geometry` 1.0.0 that validates against the frozen schema with 0 errors.
- **AC-2** Every wall carries `thickness_m` (0.10 m default) and `height_m` (2.60 m default);
  every opening carries `height_m`/`sill_m` per §7.3, all recorded in `assumptions.json`.
- **AC-3** Closed topology: no `GEOM_OPEN_*` / self-intersection on the Layer-A fixture; any
  deviation surfaces as an explicit warning/error, never silent.
- **AC-4** Determinism: two identical runs produce byte-identical `scene_geometry.json`
  (`content_hash` equal) and reports.
- **AC-5** On-wall opening placement holds: door depth == wall thickness; opening centre within
  0.02 m of the host wall; `sill_m + height_m ≤ wall height_m` for every opening.
- **AC-6** The run is immutable and derived: no write to the consumed parse artifact; source parse
  byte-copied under `runs/<geo-run-id>/project/`.
- **AC-7** Full fresh test suite passes (`env -u PYTHONPATH ./.venv/Scripts/python.exe -m pytest`),
  exit 0, on the reviewed commit.
- **AC-8** A top-down overlay (SVG or PNG) is produced for the visual/geometry gate and is
  deterministic across reruns.
- **AC-9** At least one adversarial input (degenerate wall, unknown/ambiguous wall ref, opening
  above wall, unclosed room) is covered by a failing-closed test with the correct `GEOM_*` code.
- **AC-10** No `pyproject.toml`/`uv.lock` change and no new dependency beyond the already-locked set
  unless a separate ADR is recorded first.
- **AC-11** No change to the `PARSE_*` vocabulary or to any frozen PLAN-002 schema; `GEOM_*` is
  purely additive.
- **AC-12** The **G2 Geometry Gate (human)** — the top-down overlay and the topology/dimension
  report for the Layer-A geometry are presented to **Moshe** and approved before merge.

## 12. Tests and evidence expected

- Unit tests per module (wall/opening builder, topology, dimension, determinism).
- Property test over the Layer-A fixture and a re-derived equivalent (adapter equivalence input).
- Adversarial/failure fixtures (at least the AC-9 set).
- Golden `scene_geometry` artifact with a pinned canonical hash (mirroring PLAN-002's pinned
  projection hashes).
- Evidence under `evidence/PLAN-003/`: run report, review report, tests, overlays,
  `assumptions.json`, and the gate record.

## 13. Security, licensing, compatibility, data risks

- Blender export is repo-owned deterministic script, `--background`, no network, no eval of
  LLM content (TB-2). Default-off in PLAN-003.
- No new license exposure: no new dependency without an ADR; Blender itself is a local tool, not a
  linked library (TB-5).
- No customer-sensitive data; fixture is the synthetic Layer-A geometry.
- Windows path/encoding constraints (non-ASCII project root, `package=false`) already handled by
  the PLAN-000 baseline; the compiler adds no new path assumptions.

## 14. Human gates and decisions required from Moshe

1. **PLAN approval** — this plan is `APPROVED-PENDING-MOSHE`: the independent-session review
   returned APPROVE (three findings, all factual, applied and re-verified), but Moshe's approval is
   still required before any implementation, per `HANDOFF` (PLAN-003 is not auto-authorized) and the
   task body ("approved PLAN before code").
2. **G2 Geometry Gate** — the top-down overlay + topology/dimension report must be presented to
   Moshe and approved before merge. This is the single gate delegation cannot fully substitute for
   (mirroring GC3-10/NA-4 in PLAN-002).
3. **Open decisions carried forward** (see `OPEN-DECISIONS.md`):
   - **D-009** independent review under DeepSeek-only policy — same-provider session separation is
     the interim policy; explicit cross-provider review remains blocked until Moshe decides.
   - **D-006** H200 cloud provider — **DEFERRED TO PART 2**, not touched here.
4. Retained critical Geometry/Contract gates (fail-closed): any change to §7 normative geometry
   (thickness/height defaults, opening placement, topology rules, coordinate transform) requires a
   revised PLAN + explicit Moshe approval.

## 15. Rollback and cleanup

- Pre-merge: abandon the branch/worktree; finalized PLAN-002 artifacts remain untouched.
- Post-merge: retain `scene_geometry` schema, `GEOM_*` codes, ADRs and evidence as append-only;
  never delete finalized geometry runs automatically.
- Disable the Blender export by flag/config, not by deleting code.
- No force-push, history rewrite, or destructive cleanup.

## 16. Handoff expected to next stage

`HANDOFF-PLAN-003-to-PLAN-004-001` (Camera Planner) delivering the `scene_geometry` white model as
the stable input, with the same consumer-obligations rigor PLAN-002 used.

## 17. Definition of Done

Work is `DONE` only when: §11 acceptance criteria are `MET`; a fresh full suite passes (exit 0); at
least one failure path is exercised; an independent-session review returns `APPROVE`;
`scene_geometry` schema and `GEOM_*` vocabulary are updated (additive) and versioned; evidence is
hash-bound and openable; the G2 human geometry gate is approved by Moshe; the handoff is written;
the orchestrator merges; and `PROJECT-STATE.yaml` + `PROGRESS.md` are updated in the same merge.

## 18. Model routing (canonical, DeepSeek/OpenRouter)

All roles route to `deepseek/deepseek-v4-pro-0813` through `openrouter` (docs/06, 08, 09, 10);
reporter-only work may use `deepseek/deepseek-v4-flash-0731`. Geometry/spatial roles run at
`MAX` effort.

```text
ROLE:                              geometric/spatial author
PROVIDER:                          openrouter
REQUESTED_MODEL:                   deepseek/deepseek-v4-pro-0813
ACTUAL_MODEL_ID:                   recorded from runtime metadata (never inferred from self-description)
EFFORT_NORMALIZED:                 MAX
EFFORT_PROVIDER_VALUE:             max
MODEL_REASON:                      spatial representation, units, topology, Blender architecture
FALLBACK_PROVIDER:                 none (no silent fallback; block on unavailability)
FALLBACK_MODEL:                    none
CROSS_PROVIDER_REVIEW:             false  # D-009 remains open; same-provider session separation only

ROLE:                              independent reviewer (separate read-only-first session)
PROVIDER:                          openrouter
REQUESTED_MODEL:                   deepseek/deepseek-v4-pro-0813
EFFORT_NORMALIZED:                 MAX
CROSS_PROVIDER_REVIEW:             false
```

> **Stale-language note (recorded, not silently followed).** The Kanban card `t_c19e7136` body
> says "Opus 5 MAX leads spatial representation … GPT/Codex handles implementation". That wording
> predates the DeepSeek/OpenRouter campaign. The live, authoritative model policy (docs/06/08/09/10
> and `PROJECT-STATE.yaml` `model_policy`) mandates `deepseek/deepseek-v4-pro-0813` for all roles,
> with effort `MAX` for spatial/geometry, and cross-provider review explicitly unavailable
> (`cross_provider_review_available: false`). The orchestrator follows the live policy and records
> the divergence here; a real provider/model mismatch still requires Moshe's approval.

## 19. Risks and explicit deferrals

- Thickness/height defaults are determinism-serving conveniences, not surveyed measurements; they
  are assumptions recorded in `assumptions.json` and surfaced at the G2 gate.
- Curved/angled walls remain unsupported (PLAN-002 boundary).
- Headless Blender export is best-effort evidence in PLAN-003, not a gate dependency; full
  Blender/rendering integration is PLAN-005.
- Cross-provider review is unavailable until D-009 is decided; same-provider session separation +
  deterministic evidence + human G2 gate are the compensating controls.
- G7/G8, H200/GPU, cloud, remote and spending remain **DEFERRED TO PART 2**.
