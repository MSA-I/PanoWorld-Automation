# PLAN-002 NA-3e rework 4 implementation report

Date: 2026-08-10

Branch: `panoworld-dev/na-3e-major-fixes`

Status: all seven dispatched fixes and both test-coverage gaps are implemented. No commit was created and Git history was not changed.

## Fix results

### F-1 - failed post-rename verification must not leave a published run

- Defect: a failed verification after `os.replace(staging_run, final_run)` returned operational CLI 2 while leaving a normally named finalized directory on disk.
- Change: `src/pwa/floorplan/runs.py` now renames the directory back to staging before propagating the operational failure. If rename-back itself fails, `parse_run()` still returns CLI 2 and its diagnostic uses `finalized_directory_left_behind` to state the residual condition explicitly.
- Reversion tests:
  - `tests/integration/test_plan002_parse_run.py::test_post_finalization_inventory_hash_drift_is_not_reported_complete`
  - `tests/integration/test_plan002_parse_run.py::test_post_finalization_rollback_failure_reports_finalized_directory_left_behind`

### F-2 - one immutable annotation-raster snapshot

- Defect: hash verification, dimension validation, and overlay embedding reopened the staged raster independently.
- Change: `AnnotationSource.extract_with_image_snapshot()` reads the contained staged raster once, computes one digest from those bytes, compares it independently with both the annotation declaration and source inventory, decodes dimensions from `BytesIO` over the same bytes, and returns that snapshot for `_source_binding()` sanitization and embedding.
- Reversion tests:
  - `tests/unit/test_floorplan_sources.py::test_annotation_source_reads_one_raster_snapshot_for_hash_and_dimensions`
  - `tests/unit/test_floorplan_builder.py::test_source_binding_uses_supplied_verified_raster_snapshot`
- Known residue required by the dispatch: the DXF adapter still invokes a subprocess whose worker reopens the staged DXF path. Achieving one byte snapshot there requires a worker-interface change and was intentionally not attempted in this round.

### F-3 and F-7 - drive-relative and NTFS ADS containment

- Defect: write-side containment accepted colon-bearing components, including Windows drive-relative anchors and alternate data streams, and lacked an independent resolved-root containment proof.
- Change: `_contained_parts()` rejects every component containing `:`. `validate_contained_destination()` now also resolves the candidate and proves `relative_to()` the resolved root after the lexical reparse walk.
- Reversion tests:
  - F-3: `tests/integration/test_plan002_failure_matrix.py::test_drive_relative_inventory_destination_is_rejected`
  - F-3 defense in depth: `tests/integration/test_plan002_failure_matrix.py::test_destination_containment_is_reproved_if_component_grammar_misses_drive_anchor`
  - F-7: `tests/integration/test_plan002_failure_matrix.py::test_ads_inventory_destination_is_rejected`

### F-4 - staged writes must not recreate parents

- Defect: floorplan staged-write sites and shared helpers called `mkdir(parents=True, exist_ok=True)` immediately before opening leaves, allowing a missing or replaced parent to be accepted mid-run.
- Change: shared `copy_immutable()` and `write_json_exclusive()` retain their PLAN-001-compatible default, but accept an opt-in `create_parents=False` mode that requires an existing regular non-reparse parent. PLAN-002 uses that mode for inventory copies and JSON writes. `write_bytes_contained()` has the equivalent checked mode, used for source envelopes, annotation JSON, and overlay bytes. No floorplan staged write recreates its parent.
- Reversion test: `tests/integration/test_plan002_parse_run.py::test_staged_write_does_not_recreate_missing_parse_parent`.
- PLAN-001 compatibility: existing intake and packager call sites retain the original default parent-creation behavior and remained green in the full suite.

### F-5 - finalization verifies derived artifacts

- Defect: finalization rehashed only copied source inventory and did not verify declared overlay bytes or envelope `content_hash` values.
- Change: both pre-rename and post-rename checks now validate all written artifact envelopes, recompute their `content_hash`, parse the non-envelope parse report, and recompute every present overlay declaration against the contained overlay file. The optional annotation envelope is checked when present. No derived-hash manifest or other contract surface was added.
- Reversion tests:
  - `tests/integration/test_plan002_parse_run.py::test_finalization_rejects_overlay_hash_drift`
  - `tests/integration/test_plan002_parse_run.py::test_finalization_rejects_envelope_content_hash_drift`

### F-6 - bounded annotation read

- Defect: `Path.read_bytes()` materialized the full annotation before applying `MAX_ANNOTATION_BYTES`.
- Change: preflight reads at most `MAX_ANNOTATION_BYTES + 1` bytes. The sentinel byte maps overflow to the existing `PARSE_RESOURCE_LIMIT` operational CLI 2 result. No limit or `limits_snapshot()` key was added.
- Reversion test: `tests/integration/test_plan002_parse_run.py::test_annotation_read_is_bounded_before_resource_limit_check`.

### F-8 - contain `source_image_ref` before opening

- Defect: `AnnotationSource.extract()` opened the annotation image before its caller's later containment check; the supported `source_inventory=None` path had no independent gate.
- Change: `AnnotationSource` now resolves `source_image_ref` through `resolve_contained_relpath()` inside the adapter before `read_bytes()`. The caller's later containment check remains as defense in depth.
- Reversion test: `tests/unit/test_floorplan_sources.py::test_annotation_source_rejects_reparse_image_ref_before_open`.

## Test-gap closure

- Overlay XML escaping: added `tests/unit/test_floorplan_overlay.py::test_legend_lines_escape_xml_text_metacharacters`. It checks all XML text metacharacters and parses the generated fragment. The pre-existing direct `test_hostile_label_escaped` also remains green.
- GC3-5 real-worker composition: added `tests/integration/test_plan002_parse_run.py::test_real_dxf_worker_subprocess_maps_cumulative_entity_overflow_to_cli3`. It launches the real `pwa.floorplan.dxf_worker` subprocess with a test-only reduced entity cap, crosses the cap cumulatively between modelspace and paperspace, and asserts `PARSE_RESOURCE_LIMIT` with CLI 3.

## Verification

- Baseline before edits: 338 passed, exit 0.
- Final full suite: `351 passed, 3 warnings in 89.04s`, exit 0, using `.venv/Scripts/python.exe`, CPython 3.11.15, and cleared inherited `PYTHONPATH`.
- Warnings: two existing Pillow `getdata()` deprecations and one pytest cache warning caused by the sandbox's cache-path write restriction. No test failed or was skipped because of them.
- Focused PLAN-002 plus golden run: 151 passed before the final XML test addition, exit 0.
- Golden canonical projection remained `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`; the expected value was not edited.
- `git diff --check`: exit 0.
- `pyproject.toml` SHA-256 remained `f0196ef891c140a6410a4bbcc44aa381dbb38ab0974bdb26a16b26d521c02d5d`.
- `uv.lock` SHA-256 remained `a636f9bca0f4e5f63eb7253386cb5a1248a651d693320f0b5e835975bde0e18a`.
- No diff exists in `pyproject.toml`, `uv.lock`, `schemas/`, `contracts/`, `docs/`, `src/pwa/floorplan/config.py`, or `tests/golden/test_floorplan_golden.py`.
- `limits_snapshot()` is unchanged and has no new key.
- `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}` is unchanged.
- GC3-8, GC3-9, and GC3-10 were not touched.

## Runtime metadata from the session rollout

- CLI version: `0.144.6`
- Model ID: `gpt-5.6-sol`
- Provider configuration: `headroom`
- Sandbox mode: `workspace-write`; network access disabled; approval policy `never`
- Reasoning effort: `xhigh`
- Session ID: `019fed4a-b7a8-7d50-ab8c-bf0397dac943`

## Uncompleted work or escalation

No dispatched fix is incomplete and no boundary escalation is required. The DXF subprocess reopen described under F-2 is the explicitly mandated known residue and remains out of scope.

## Concurrent orchestrator activity observed at handoff

During the implementation session the orchestrator advanced the branch HEAD to `4dcb13f` and updated `PROJECT-STATE.yaml` with NA-3e ownership metadata. Those concurrent changes were preserved and not edited by this implementer. The statement above about commits means this implementer created no commit and performed no Git-history operation.

## GC4-1 follow-up

- Root cause: the defense-in-depth test hard-coded `C:`, so when `tmp_path` was also on `C:`, `pathlib` kept the candidate under the staging root and the resolved containment proof had no escape to reject.
- Change: the test now injects `Q:` unless the staging root is already on `Q:`, in which case it injects `R:`, with an explanatory comment preserving the different-drive requirement. The sibling `C:pwa_escape/owned.txt` test remains unchanged because `_contained_parts()` rejects its colon-bearing component before drive handling.
- Full suite: `351 passed, 3 warnings in 90.84s (0:01:30)`, exit 0, using `.venv/Scripts/python.exe` with inherited `PYTHONPATH` cleared.
- Session ID: `019fed6d-9bce-72c1-9ca5-f47227c1af6c`
