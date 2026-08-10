# PLAN-002 AC traceability

- Verification run: `RUN-PLAN002-REWORK-20260810` (bounded rework pass closing the 2026-08-10 independent
  code/security/contracts and spatial/geometry review findings; supersedes `RUN-20260809-173417-586650`).
- Status: all AC-1..AC-23 evidenced for Part 1 implementation scope.
- Remaining downstream gates only: human visual/geometry approval and pending cross-provider review.
- M-9 correction (code review, 2026-08-10): AC-5 previously cited a test name
  (`test_staging_left_on_operational_failure`) that does not exist in the suite; corrected below to the
  real test. AC-3 previously had zero assertions anywhere; the new dedicated test is cited below.

| AC | Status | Tests / Execution | Evidence |
|---|---|---|---|
| AC-1 | evidenced | `tests/unit/test_contract_versions.py` (incl. `test_schema_catalog_rejects_duplicate_version_pair`, `test_schema_catalog_rejects_duplicate_schema_id`, added 2026-08-10 to actually reach the D-012 duplicate branches) | `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/junit.xml` |
| AC-2 | evidenced | `tests/unit/test_schemas_roundtrip.py` in full suite | `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/summary.md` |
| AC-3 | evidenced | `tests/integration/test_plan002_failure_matrix.py::test_source_run_bytes_and_hashes_unchanged_across_outcomes` (added 2026-08-10; parametrized success/warning/failed_domain/operational) | `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/junit.xml` |
| AC-4 | evidenced | `f-existing-final`, `f-existing-staging` executable rows | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-5 | evidenced | `tests/integration/test_plan002_parse_run.py::test_operational_failure_retains_staging_and_no_finalized_run`, `f-worker-garbage` | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-6 | evidenced | `tests/golden/test_floorplan_golden.py::test_canonical_projection_matches_across_adapters` | `evidence/PLAN-002/determinism/geometry-projection-hashes.json` |
| AC-7 | evidenced | `tests/golden/test_floorplan_golden.py::test_adapter_specific_fields` | `evidence/PLAN-002/parse/layer-a-1-raster.json`, `evidence/PLAN-002/parse/layer-a-1-dxf.json` |
| AC-8 | evidenced | `tests/unit/test_floorplan_normalize.py`, `tests/unit/test_floorplan_normalize_matrix.py`, `tests/unit/test_floorplan_validate.py::test_validate_rejects_duplicate_opening_geometry` (C-1 spatial, added 2026-08-10), `f-duplicate-opening` row | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-9 | evidenced | `tests/unit/test_floorplan_validate.py` (incl. `test_seg_intersects_non_adjacent_detects_collinear_overlap_and_both_side_touches`, `test_validate_detects_room_self_intersection_via_collinear_overlap`, M-3 spatial, added 2026-08-10), `tests/unit/test_floorplan_validate_matrix.py` | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-10 | evidenced | `resolve_opening_wall`/`_resolve_wall_id` unit coverage (incl. collinearity tests, M-2 spatial, added 2026-08-10) + `f-unknown-wall-ref`, `f-ambiguous-wall-ref`, `f-opening-*`, `f-opening-not-collinear` rows | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-11 | evidenced | `f-dimension-bad`, `f-scale-*`, `b-dimension-exact` executable tests | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-12 | evidenced | `tests/unit/test_floorplan_sources.py`, `tests/unit/test_floorplan_sources_matrix.py` (incl. `test_external_refs_never_opened_on_unknown_layer`, M-7, added 2026-08-10) | `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/junit.xml` |
| AC-13 | evidenced | `tests/integration/test_plan002_parse_run.py` | `evidence/PLAN-002/parse/layer-a-1-raster.json`, `evidence/PLAN-002/parse/layer-a-1-dxf.json` |
| AC-14 | evidenced | `tests/unit/test_floorplan_overlay.py` (incl. `test_dxf_overlay_renders_rooms_and_doors_not_empty_placeholders`, `test_dxf_overlay_source_layer_is_independent_of_detections`, M-4 spatial, added 2026-08-10) + repeat-run overlay hashes | `evidence/PLAN-002/overlays/`, `evidence/PLAN-002/determinism/geometry-projection-hashes.json` |
| AC-15 | evidenced | `tests/unit/test_floorplan_overlay.py::test_hostile_label_escaped`; M-10 (code review 2026-08-10): absolute paths/user name redacted from `acceptance.md`, `implementation/runtime-metadata.json`, `implementation/codex-followup-prompt.md`, `implementation/plan002-evidence-meta.json`; raw 8.3 MB session-transcript dumps (not a required PLAN-002 evidence artifact) removed | `evidence/PLAN-002/failures/parse-failure-matrix.json`, `evidence/PLAN-002/real-plan-redacted.json` |
| AC-16 | evidenced | `f-unmapped-layer`, `f-low-confidence` executable rows | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-17 | evidenced | `f-traversal`, `f-ancestor-reparse`, `f-hash-*` executable rows + `tests/integration/test_plan002_parse_run.py::test_source_run_absolute_dotdot_traversal_is_rejected_without_staging` (C-1 code, added 2026-08-10), `::test_manifest_inventory_path_traversal_is_rejected` (M-1 code, added 2026-08-10) | `evidence/PLAN-002/failures/parse-failure-matrix.json`, `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/junit.xml` |
| AC-18 | evidenced | `f-annotation-oversize`, `f-dxf-oversize`, `f-limit-*`, `f-timeout` executable rows + `tests/unit/test_floorplan_sources.py::test_worker_output_channel_is_not_truncated_at_the_stdio_log_cap` (M-6, added 2026-08-10) | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-19 | evidenced | `tests/unit/test_floorplan_sources_matrix.py::test_external_refs_never_opened`, `::test_external_refs_never_opened_on_unknown_layer` | `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/junit.xml` |
| AC-20 | evidenced | one executable row per §13 fixture (65 rows after the 2026-08-10 rework, up from 63) + `tests/integration/test_plan002_failures.py::test_missing_source_manifest_returns_cli_2_instead_of_raising`, `::test_malformed_source_manifest_json_returns_cli_2_instead_of_raising`, `::test_dxf_source_with_unknown_manifest_units_returns_failed_run_not_uncaught_exception` (M-2/M-3 code, added 2026-08-10) | `evidence/PLAN-002/failures/parse-failure-matrix.json` |
| AC-21 | evidenced | fresh focused suite + fresh full suite + `git diff --check` | `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/command.log`, `evidence/PLAN-002/implementation/git-verification.json` |
| AC-22 | evidenced | `git diff -- pyproject.toml uv.lock` empty | `evidence/PLAN-002/implementation/git-verification.json` |
| AC-23 | evidenced | acceptance boundary statement preserved | `evidence/PLAN-002/acceptance.md` |
