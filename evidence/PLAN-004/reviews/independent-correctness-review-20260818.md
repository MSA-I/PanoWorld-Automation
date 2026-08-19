# PLAN-004 — Independent Correctness Review (read-only-first)

- Plan: `PLAN-004-camera-planner` (APPROVED, Moshe 2026-08-18)
- ADR: `ADR-0008-camera-planner-vocab-and-run-lifecycle` (PROPOSED→approved with PLAN-004)
- Reviewer role: independent correctness reviewer (same-provider separate pass; cross-provider unavailable per D-009)
- REVIEWER_MODEL (recorded, not self-inferred): `deepseek/deepseek-v4-pro-0813` via `openrouter`, effort `MAX`
- CROSS_PROVIDER_REVIEW: `false` (same-provider session separation + deterministic evidence + machine-checked extrinsics validator + human G3 gate are the compensating controls)
- Scope: `src/pwa/camera/` (12 modules), `tests/unit/test_camera_planner.py`, `tests/integration/test_camera_run.py`, `contracts/error_codes.md` `CAM_*` block, canonical run `evidence/PLAN-004/camera-run/cam-layer-a-dxf-1/`.
- References checked against: frozen `scene_geometry` 1.0.0 + `camera_plan` 1.0.0 + `assumptions` 1.0.0 schemas, canonical `evidence/PLAN-003/geometry-run/geometry/scene_geometry.json`, PLAN-004 §7/§10/§11, ADR-0008, golden `tests/golden/panoworld_demo_subset/viewpoints/0000/extrinsics.txt`.

## Verdict

**APPROVE** — no BLOCKER, no MAJOR, no MINOR correctness defects found. The
implementation faithfully realizes PLAN-004 §7 normative camera placement and
ADR-0008 vocabulary/lifecycle. All 12 acceptance criteria are independently
verified MET. The G3 Camera Gate (human — Moshe) is the sole outstanding gate
before merge.

## Independent verification (re-derived, not author-asserted)

1. **Full suite green (AC-7):** re-ran `env -u PYTHONPATH ./.venv/Scripts/python.exe
   -m pytest` → **554 passed, exit 0** (523 baseline + 31 camera). Re-derived fresh.
2. **Camera subset:** `pytest tests/unit/test_camera_planner.py
   tests/integration/test_camera_run.py` → **31 passed, exit 0**.
3. **AC-1 schema fidelity:** produced `camera_plan.json` validates with
   `validate_artifact` → `[]`; `content_hash == compute_content_hash` (True);
   `status == "complete"`. `assumptions.json` validates → `[]`.
4. **AC-4 extrinsics:** every `extrinsics/*.txt` parsed and run through
   `check_extrinsics_matrix` → `[]` (zero error codes) for both `0000`/`0001`.
   Independently confirmed the yaw-θ convention matches the golden fixture byte-for-byte.
5. **AC-2 free-space:** both viewpoints are the area-weighted centroids
   `(2.5,3.0)` / `(6.5,3.0)`, each inside its room, ≥0.4 m wall clearance and
   ≥0.2 m opening clearance. Defaults (1.35 / 0.35 / 0.20 / yaw 0) all present
   in `assumptions.json` with `source:"default"`.
6. **AC-3 coverage:** `coverage-report.json` → 2 rooms, 2 viewpoints, 1 edge,
   0 uncovered; `every_room_covered == true`, `no_collision_errors == true`.
7. **AC-5 determinism:** two identical runs produce byte-identical payloads,
   coverage report, map.json, overlay SVG, and `extrinsics/0000.txt`
   (asserted in `test_deterministic_rerun_byte_identical_payload`).
8. **AC-6 immutability:** source geometry byte-copied to `project/source-geometry.json`
   (diff-verified identical to the consumed artifact); the consumed file is unchanged.
9. **AC-8 overlay:** `overlay-cameras.svg` is non-empty, deterministic, and
   places both cameras (red circles) at their room centroids.
10. **AC-9 adversarial:** `test_room_fully_colliding_reports_uncovered` (thin room
    + opening at centroid) and `test_duplicate_positions_fail_closed` exercise
    failing-closed paths with the correct `CAM_UNCOVERED_ROOM` / `CAM_DUPLICATE_ENTITY` codes.
11. **AC-10:** `git diff --stat -- pyproject.toml uv.lock` → empty (no dependency change).
12. **AC-11:** `contracts/error_codes.md` diff is purely additive (+21 lines,
    `CAM_*` block); zero `-` lines; `PARSE_*`/`GEOM_*` untouched; no frozen schema change.

## Findings

None. One forward note (non-blocking): `CAM_MAP_ADJACENCY_UNRESOLVED` is a
tier-4 warn for exterior doors (e.g. the Layer-A entrance door
`go-9d050af60afc`). This is correct fail-open behavior and does not affect the
coverage/collision/extrinsics gate; recorded in the planning-session evidence.

## Conclusion

Correctness review passes. The **G3 Camera Gate (human — Moshe)** remains the
sole outstanding gate before merge: present
`evidence/PLAN-004/camera-run/cam-layer-a-dxf-1/camera/overlay-cameras.svg`
plus `coverage-report.json` (and a sample `extrinsics/*.txt`) for approval.