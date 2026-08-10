# PLAN-002 NA-3g rework 5 report

Dispatch: `evidence/PLAN-002/reviews/na3g-rework5-dispatch-20260811.md`.

This round implements only the three dispatched residues. No commit or Git-history operation was
performed by this implementer.

## Fix 1 - residual finalization state and retained staging report

### Defect

The rollback double-fault used `overlay.overlay_omitted_reason` to report that a finalized directory
was left behind, even though that field describes only overlay omission. The CLI then discarded the
returned diagnostic. Separately, a successful rollback restored a staging
`parse/parse-report.json` whose `outcome` still said `complete`.

### Change

- `src/pwa/floorplan/builder.py` now records the double-fault as the distinct top-level diagnostic
  field `residual_state: "finalized_directory_left_behind"`. The overlay omission field returns to
  its existing overlay-only vocabulary.
- `src/pwa/floorplan/cli.py` writes that residual diagnostic as deterministic JSON to stderr before
  returning exit 2, so the operator-visible surface no longer discards it.
- After a successful rename-back, `_staged_operational_result()` explicitly replaces the invalid
  happy-path `parse/parse-report.json` with the operational-failure report. The replacement is
  prepared through the exclusively-created transient sibling
  `parse/parse-report.operational-failure.tmp` and atomically renamed over the invalid report. This
  preserves exclusive creation for the new bytes while preventing a retained staging directory
  from claiming success. The sibling is not a second persisted artifact on the successful path; if
  the atomic replacement itself fails, it remains as failure evidence and `parse_run()` still
  returns rather than raising.

### Reversion tests

- `tests/integration/test_plan002_parse_run.py::test_post_finalization_inventory_hash_drift_is_not_reported_complete`
  fails if the rolled-back staging report again remains `complete`.
- `tests/integration/test_plan002_parse_run.py::test_post_finalization_rollback_failure_reports_finalized_directory_left_behind`
  fails if the residual state is put back into `overlay_omitted_reason` or escapes `parse_run()`.
- `tests/integration/test_plan002_cli.py::test_main_surfaces_finalized_directory_left_behind_diagnostic`
  fails if the CLI discards the residual diagnostic again.

### Design-record amendment not applied

`evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md:585` is append-only and was not
edited. The routed amendment should say that `overlay_omitted_reason` remains limited to
`no_normalized_geometry`, `overlay_exceeds_max_bytes`, and `source_raster_exceeds_limits`; residual
filesystem state is instead recorded at the top level as
`residual_state: "finalized_directory_left_behind"` and is emitted by the CLI on exit 2. It should
also record that, after a successful finalization rollback, the retained staging parse report is
replaced explicitly with the operational-failure report because the pre-rollback `complete` claim
is no longer true.

## Fix 2 - bounded source-raster snapshot

### Defect

`src/pwa/floorplan/annotation_source.py` materialized the entire staged raster with `read_bytes()`
before `MAX_SOURCE_RASTER_BYTES` was enforced downstream.

### Change

The adapter now performs one `open("rb")` read of at most `MAX_SOURCE_RASTER_BYTES + 1`. An overflow
raises the existing `PARSE_RESOURCE_LIMIT` finding with no new error code or limit key. For an
accepted raster, that same single byte snapshot supplies the digest comparisons, Pillow dimension
decode, returned image snapshot, and downstream overlay embedding.

### Reversion tests

- `tests/unit/test_floorplan_sources.py::test_annotation_source_reads_one_raster_snapshot_for_hash_and_dimensions`
  fails if the read becomes unbounded or if more than one raster snapshot is taken.
- `tests/unit/test_floorplan_sources.py::test_annotation_source_maps_raster_read_overflow_to_resource_limit`
  fails if overflow no longer maps to `PARSE_RESOURCE_LIMIT`.
- `tests/integration/test_plan002_parse_run.py::test_source_raster_read_overflow_maps_to_resource_limit_without_raising`
  fails if the overflow escapes `parse_run()` or is not classified as `PARSE_RESOURCE_LIMIT`.

## Fix 3 - shared component grammar on the read side

### Defect

`resolve_contained_relpath()` duplicated a narrower component check instead of using
`_contained_parts()`, so read-side and write-side legal-component grammar could diverge.

### Change

`src/pwa/floorplan/runs.py` now obtains the read-side components from `_contained_parts()` and then
retains the existing lexical ancestor walk, reparse checks, and independent
`resolve()` / `relative_to()` containment proof.

### Reversion tests

- `tests/integration/test_plan002_failure_matrix.py::test_read_side_rejects_ads_component_via_shared_component_grammar`
  fails if the read side stops applying the shared colon rejection.
- `tests/integration/test_plan002_failure_matrix.py::test_read_side_component_grammar_accepts_every_parser_resolved_path`
  fails if the read side stops routing through `_contained_parts()` or if the grammar over-rejects
  any actual parser path. It covers every derived-manifest inventory path plus
  `project/project_manifest.json`, `project/input_quality_report.json`,
  `parse/annotation.json`, and `parse/overlay.svg`.

The test uses no injected drive letter and therefore has no outcome dependency on the volume used
for `tmp_path`. The pre-existing different-drive defense-in-depth test continues to derive its
foreign drive from the runtime root drive.

## Verification

All executable verification used the repository `.venv` with inherited `PYTHONPATH` removed.
Because the default pytest temp/cache location was inaccessible in this sandbox, the successful
runs used repository-ignored `.tmp/pytest-na3g-*` basetemp directories and disabled pytest's cache
provider. Sandbox policy rejected the final recursive cleanup command, so the seven ignored
session basetemp directories remain under `.tmp/`; no tracked file is present there.

- Per-fix targeted tests: exit 0.
- All changed test modules together: exit 0.
- Golden suite: 9 passed, exit 0.
- Full handoff suite after the concurrent HEAD switch: 356 passed, exit 0, in 86.31 seconds; two
  pre-existing Pillow `getdata()` deprecation warnings. Collection independently confirmed 356
  test nodes. The dispatched baseline was 351; this round adds five tests.
- Golden canonical projection hash remained
  `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`.
- `git diff --check`: exit 0.

## Boundary verification

- `pyproject.toml` remained byte-identical across the round:
  `sha256:f0196ef891c140a6410a4bbcc44aa381dbb38ab0974bdb26a16b26d521c02d5d`.
- `uv.lock` remained byte-identical across the round:
  `sha256:a636f9bca0f4e5f63eb7253386cb5a1248a651d693320f0b5e835975bde0e18a`.
- `contracts/error_codes.md` remained unchanged:
  `sha256:4e19219949dfe249e0c5d2d0ca399679ab82d88de9a9f438784d187962e8fbca`.
- `docs/plans/PLAN-002-floorplan-parsing.md` remained unchanged:
  `sha256:b744bb7fdb1865e020c21a9b9d926c0aedf7e1956cb0bed2edd08f5e85085384`.
- No schema changed, no error-code token was added, `src/pwa/floorplan/config.py` is unchanged, and
  `limits_snapshot()` gained no key.
- `_APPROVED_ANNOTATION_IMAGE_KINDS` remains exactly `{"floorplan"}`.
- GC3-8, GC3-9, and GC3-10 were not touched.
- The plan document and existing evidence records were not edited. This report is the only new
  evidence file from the implementation session.
- No dependency was added and no commit, checkout, reset, merge, rebase, stage, or push operation
  was performed by this implementer.

## Runtime metadata from the session rollout

- CLI version: `0.144.6`
- Model ID: `gpt-5.6-sol`
- Provider configuration: `headroom`
- Reasoning effort: `xhigh`
- Originator/source: `codex_exec` / `exec`
- Sandbox mode: `workspace-write`; network access restricted; approval policy `never`
- Session ID: `019fed8c-8842-77e1-a247-7b58478d4322`
- Session-start branch and HEAD: `panoworld-dev/na-3g-residues` at `1946815b4f0bde31471a4a0bda94cb82155bba9e`

## Concurrent orchestrator activity at handoff

During final boundary verification, the shared checkout was externally advanced and switched to
`main` at `2c4f161522d62d35533e36eb16d7e54cd7a39533` by the accepted NA-3e/NA-3f merge. The eight NA-3g
source/test files remained as unstaged working-tree changes on top of that HEAD. This implementer
did not initiate or reverse the branch/HEAD change; the orchestrator remains responsible for
placing and committing the NA-3g working tree on the intended branch.

## Uncompleted work

No dispatched code fix or executable verification is incomplete. The append-only design-record
amendment described under Fix 1 was intentionally not applied and is routed to the orchestrator as
required by the dispatch.
