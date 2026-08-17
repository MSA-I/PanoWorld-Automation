# PLAN-003 — Independent Correctness Review (Task t_84f88a08)

- Plan: `PLAN-003-geometry-compiler` (APPROVED, Moshe 2026-08-14, sha256 `a122367b…c3b44`)
- Review task: `t_84f88a08` — "Conduct independent correctness review"
- Reviewer role: independent correctness reviewer (separate from G-t7 code review)
- REVIEWER_MODEL (recorded, not self-inferred): `deepseek/deepseek-v4-pro-0813` via `openrouter`, effort `MAX`
- CROSS_PROVIDER_REVIEW: `false` (D-009 open — same-provider session separation is the interim control; documented in PLAN-003 §18/§19)
- Scope: `src/pwa/geometry/` (11 modules), `tests/unit/test_geometry_*.py`, `tests/integration/test_geometry_run.py`, `contracts/error_codes.md` `GEOM_*` block, golden evidence under `evidence/PLAN-003/geometry-run/`.
- References checked against: frozen `floorplan_parse` 1.1.0 + `scene_geometry` 1.0.0 + `assumptions` 1.0.0 schemas, canonical Layer-A fixture `evidence/PLAN-002/parse/layer-a-1-dxf.json`, PLAN-003 §7/§11, ADR-0007.

## Verdict

**APPROVE** — no BLOCKER, no MAJOR, no MINOR correctness defects found. The
implementation is a faithful, schema-valid realization of the PLAN-003 §7
normative geometry and ADR-0007 vocabulary/lifecycle. All 12 acceptance
criteria are independently verified MET. No unresolved critical issues.

## Independent verification (re-derived, not copied from G-t7)

1. **Full suite green**: re-ran `env -u PYTHONPATH ./.venv/Scripts/python.exe
   -m pytest` → **exit 0**; `--collect-only` reports **420 tests collected**
   (27 geometry + 393 baseline). Matches the G-t7 figure, re-derived fresh.
2. **Geometry subset**: `pytest tests/unit/test_geometry_compiler.py
   tests/unit/test_geometry_topology.py tests/integration/test_geometry_run.py`
   → 27 passed, exit 0.
3. **Schema fidelity (independent):** `scene_geometry` opening items emit
   exactly `{id,type,wall_id,center,width_m,height_m,sill_m}` — no `depth_m` —
   matching the frozen schema's `additionalProperties: false`. `door.depth_m`
   is an in-memory-only invariant (`GeoOpening.depth_m`), correctly never
   leaked into the payload. Verified against `scene_geometry-1.0.0.schema.json`
   (openings block, lines 53–69).
4. **`assumptions` schema binding:** `assumption_entries()` emits
   `{key,value,reason,source,requires_human_ack}` with `source:"default"`
   (valid enum) and `requires_human_ack:false`; payload `{stage:"geometry",
   entries:[…]}` satisfies `assumptions-1.0.0.schema.json` required fields
   `stage` + `entries`. `_artifact()` internally runs `validate_artifact`,
   so any drift would fail the run.
5. **Golden evidence correctness:** `scene_geometry.json` walls carry
   `thickness_m=0.1`/`height_m=2.6`; openings carry correct defaults
   (door 2.10/0.00, window 1.20/0.90); `default_ceiling_height_m=2.6`;
   `up_axis:"z"`, `units:"m"`. `topology-report.json` → `findings:[]`,
   all four checks `true`. `content_hash` values recompute consistently.
6. **Containment / immutability:** re-verified `resolve_contained_relpath`,
   `write_bytes_contained`, `write_json_exclusive` paths reject `..`,
   reparse points, and symlink/junction traversal; source parse is
   byte-copied (`project/source-parse.json`) and never mutated; staging →
   `os.replace` atomic finalize with inventory-hash re-verification.
7. **AC-10/AC-11:** `git diff --stat` shows only `contracts/error_codes.md`
   (+19 lines, purely additive `GEOM_*` block); no `pyproject.toml`/`uv.lock`
   change; no `PARSE_*` mutation.

## Findings

None. (The single G-t7 note R1 — `GEOM_OPENING_AMBIGUOUS_WALL_REF` is reserved
vocabulary with no current detection path — remains a correct, non-blocking
forward-reserve observation and requires no change before the G2 gate.)

## Conclusion

Correctness review passes independently of the G-t7 code review. The G2
Geometry Gate (human — Moshe) remains the sole outstanding gate before merge:
present `evidence/PLAN-003/geometry-run/geometry/overlay-topdown.png` (`.svg`)
plus `topology-report.json` for approval.
