# PLAN-003 G-t7 — Independent Code Review (read-only-first)

- Plan: `PLAN-003-geometry-compiler` (APPROVED, Moshe 2026-08-14, sha256 `a122367b…`)
- Reviewer role: independent reviewer, separate session, read-only-first
- Model routing (recorded, not self-inferred): `deepseek/deepseek-v4-pro-0813` via `openrouter`, effort `MAX`
  (per live policy docs/06/08/09/10; card-body "Opus 5 MAX / GPT-Codex" wording predates the DeepSeek
  campaign and is recorded, not followed)
- Cross-provider review: `false` (D-009 open — same-provider session separation is the interim control)
- Scope under review: `src/pwa/geometry/` (G-t1..G-t6 code), `tests/unit/test_geometry_*.py`,
  `tests/integration/test_geometry_run.py`, `contracts/error_codes.md` `GEOM_*` block, golden evidence
  under `evidence/PLAN-003/geometry-run/`.
- References checked against: frozen `floorplan_parse` 1.1.0 + `scene_geometry` 1.0.0 schemas, canonical
  Layer-A fixture `evidence/PLAN-002/parse/layer-a-1-dxf.json`, `HANDOFF-PLAN-002-to-PLAN-003-001`,
  `contracts/error_codes.md`, PLAN-003 §7 normative geometry.

## Verdict

**APPROVE** — bounded rework optional; no BLOCKER/MAJOR. One minor cosmetic finding (R1) noted below.

## What was verified (source-first)

1. **AC-1** — `scene_geometry.json` validates against frozen 1.0.0 schema (0 errors); `content_hash` recomputes
   consistently (`compute_content_hash`). Confirmed by re-reading the golden artifact + schema.
2. **AC-2** — walls carry `thickness_m` 0.10 m / `height_m` 2.60 m; openings carry `height_m`/`sill_m`
   (door 2.10/0.00, window 1.20/0.90); all 8 defaults recorded in `assumptions.json` with reason/source.
3. **AC-3** — Layer-A fixture → `topology-report.json` `findings: []`, all four `checks: true` (closed+simple,
   non-degenerate, on-wall, fit-vertically). No `GEOM_OPEN_*`/self-intersection.
4. **AC-4** — determinism: payload + derived entity IDs byte-identical across reruns (test asserts
   `payload == payload`, reports + overlays byte-equal); only envelope `run_id`/`created_at`/`content_hash` differ.
5. **AC-5** — on-wall placement: door depth == host wall thickness is guaranteed by construction
   (`build_openings` derives `depth_m` from `thickness_by_input`); opening centre within 0.02 m
   (`_wall_projection` distance ≤ `OPENING_OFFSET_M`); `sill+height ≤ wall height` checked
   (`GEOM_OPENING_ABOVE_WALL`).
6. **AC-6** — immutable derived run: source parse byte-copied to `runs/<id>/project/source-parse.json`;
   source never mutated; staging → atomic finalize with inventory hash verification.
7. **AC-7** — fresh `env -u PYTHONPATH ./.venv/Scripts/python.exe -m pytest` → **420 passed, exit 0**
   (27 geometry tests + 393 baseline), re-verified during this review.
8. **AC-8** — top-down SVG + PNG produced, deterministic (byte-identical across reruns).
9. **AC-9** — adversarial fixtures covered: degenerate wall, unknown wall ref (`GEOM_OPENING_UNRESOLVED_WALL`),
   off-wall opening (`GEOM_OPENING_OFF_WALL`), opening above wall (`GEOM_OPENING_ABOVE_WALL`),
   width-exceeds-wall (`GEOM_OPENING_WIDTH_EXCEEDS_WALL`), unclosed room (`GEOM_OPEN_POLYGON`),
   zero-area room (`GEOM_SELF_INTERSECTING_POLYGON`), duplicate id (`GEOM_DUPLICATE_ENTITY`),
   empty geometry (`GEOM_EMPTY_GEOMETRY`).
10. **AC-10 / AC-11** — no `pyproject.toml`/`uv.lock` change; `GEOM_*` is a purely additive block appended
    to `contracts/error_codes.md` (line 69+); no `PARSE_*` mutation; no frozen-schema mutation.
11. **Schema fidelity** — opening payload emits exactly `center,height_m,id,sill_m,type,wall_id,width_m`
    (no `depth_m`), matching the frozen schema's `additionalProperties: false` on openings; door depth==wall
    thickness is enforced compiler-side (in-memory `GeoOpening.depth_m`) and unit-tested, never leaked into the
    forbidden payload field. Correct.
12. **Resource/finiteness guards** — `load.py` bounds entity counts, polygon vertices, coordinate magnitude,
    finiteness, positive width/thickness; all fail-closed with `GEOM_RESOURCE_LIMIT`/`GEOM_EMPTY_GEOMETRY`.
13. **Run-id / path containment** — `geo_run_id` validated against a strict regex; destination paths
    containment-checked; `../../evil` rejected (cli_exit 2).
14. **Blender stub** — default-off (`--export-blender`), best-effort only; missing/failed binary → `False`,
    gate unaffected; repo-owned deterministic script, `--background`, no network, no eval of LLM content (TB-2/5).
15. **Orchestrator-applied fix** (prior run) confirmed in place: `overlay.py render_png` wall stroke width now
    uses `wall.thickness_m * scale` (was hardcoded `0.10 * scale`), matching the SVG renderer.

## Findings

- **R1 (minor, cosmetic, non-blocking).** `GEOM_OPENING_AMBIGUOUS_WALL_REF` is present in the vocabulary
  (`findings.py`) and `contracts/error_codes.md`, but has no detection path — no code can currently raise it.
  In the current data model this is reachable-as-intended: duplicate wall IDs are caught earlier as
  `GEOM_DUPLICATE_ENTITY` (`build_walls` → `_check_unique_ids`), and a genuinely ambiguous wall ref cannot
  arise from verbatim ID carry-through. The entry is defensible as forward-reserve vocabulary for a future
  source contract with non-unique or aliased wall references. Not a correctness gap; no change required before
  the G2 gate. (Optional follow-up: either annotate the entry as reserved, or drop it until a source contract
  can produce ambiguity.)

## Recommendation

Proceed to the **G2 Geometry Gate (human — Moshe)**: present the top-down overlay
(`evidence/PLAN-003/geometry-run/geometry/overlay-topdown.png` + `.svg`) and the topology/dimension report
(`geometry/topology-report.json`) for the Layer-A geometry for approval. Merge is gated on that approval only;
R1 does not block.
