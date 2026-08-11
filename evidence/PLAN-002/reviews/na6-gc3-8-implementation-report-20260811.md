# PLAN-002 NA-6 GC3-8 implementation report

Dispatch: `evidence/PLAN-002/reviews/na6-gc3-8-dispatch-20260811.md`.

Approved specification:
`evidence/PLAN-002/decisions/gc3-8-amendment-rev2-approved-20260811.md`.
The superseded revision 1 was not implemented. No commit or Git-history operation was performed by
this implementer.

## Amendment 1 - PLAN-002 section 6 annotation adapter contract

### Change

The second annotation-adapter bullet in `docs/plans/PLAN-002-floorplan-parsing.md` was replaced by
the approved blockquoted wording. It now records exact code-point selection, earlier duplicate-path
preflight, the two permitted kind/format arms, the exclusive producer meaning of
`floorplan_page`, and the residual source-run trust boundary. No other section-6 clause changed.

This amendment is exercised by AC 5, AC 6 and AC 8. The already-present
`tests/integration/test_plan002_parse_run.py::test_source_manifest_requires_unique_inventory_paths`
continues to prove that duplicate paths fail before annotation matching.

### Reversion tests

- `tests/unit/test_plan002_contract_text.py::test_plan002_contains_approved_gc3_8_blockquoted_replacements`
  fails if either approved plan replacement is removed or textually changed.
- `tests/integration/test_plan002_gc3_8.py::test_selected_pdf_page_two_binds_hash_dimensions_pixels_and_overlay_deterministically`
  fails if exact selected-page binding is lost.
- `tests/integration/test_plan002_gc3_8.py::test_disallowed_annotation_inventory_or_format_is_classified_unsupported`
  fails if the selected-entry kind/format rules are widened or misclassified.

## Amendment 2 - project-manifest schema and contracts bundle

### Change

- Added `schemas/project_manifest/v1/project_manifest-1.1.0.schema.json`, structurally identical to
  1.0.0 except for its `$id`, `schema_version` const and appended `floorplan_page` kind.
- Left the filesystem-discovered catalog unchanged; it now exposes exact 1.0.0 and 1.1.0 entries
  and selects 1.1.0 as latest without a hard-coded catalog entry.
- New intake project manifests and both successful and failed derived parse-run project manifests
  declare schema 1.1.0 and contracts bundle 1.2.0.
- Source manifests are copied byte-for-byte and are not rewritten or relabeled.
- Replaced the named fixed project-manifest wording in
  `docs/plans/PLAN-002-floorplan-parsing.md` with the approved blockquote. No other plan clause was
  changed for this amendment.

This satisfies AC 1, AC 2, AC 3 and the contract portion of AC 9.

### Reversion tests

- `tests/unit/test_contract_versions.py::test_schema_catalog_tracks_exact_versions_and_latest_view`
  covers both exact versions and latest selection; the existing duplicate-pair and duplicate-`$id`
  catalog tests remain green.
- `tests/unit/test_contract_versions.py::test_project_manifest_1_0_fixture_is_compatible_with_1_1_and_frozen_schema_rejects_new_kind`
  proves the exact three-change structural delta, historical-fixture compatibility, the pinned
  1.0.0 digest and 1.0.0 rejection of `floorplan_page`.
- `tests/integration/test_plan001_intake.py::test_all_floorplan_formats_keep_original_and_emit_valid_contracts`
  fails if new intake version declarations regress.
- `tests/integration/test_plan002_parse_run.py::test_parse_run_finalizes_complete_derived_run`
  fails if derived declarations regress or if the source manifest ceases to be byte-identical.
- `tests/unit/test_plan002_contract_text.py::test_plan002_contains_approved_gc3_8_blockquoted_replacements`
  pins the approved plan wording.

## Amendment 3 - intake producer tagging

### Change

`src/pwa/intake.py` now records every approved PDF page render as
`kind: "floorplan_page"`. The original PDF remains the single `floorplan`; the DXF SVG preview
remains `other`; DWG still produces no preview. No other producer emits `floorplan_page`.

This satisfies AC 3 and AC 4.

### Reversion tests

- `tests/integration/test_plan001_intake.py::test_two_page_pdf_emits_only_two_floorplan_page_pngs`
  proves one PDF floorplan plus exactly two ordered PNG page entries and no additional page entry.
- `tests/integration/test_plan001_intake.py::test_all_floorplan_formats_keep_original_and_emit_valid_contracts`
  proves the DXF preview remains `other`, DWG emits no preview, and PDF/intake versions are current.

## Amendment 4 - parser allowlist and error classification

### Change

- `_APPROVED_ANNOTATION_IMAGE_KINDS` in `src/pwa/floorplan/annotation_source.py` is now exactly
  `{"floorplan", "floorplan_page"}`.
- `floorplan` permits decoded PNG/JPEG; `floorplan_page` permits decoded PNG only. The accepted
  bounded byte snapshot is fully decoded before dimensions are accepted.
- Missing inventory references, disallowed kinds and incompatible/undecodable bytes now raise
  `FloorplanError("PARSE_SOURCE_UNSUPPORTED", ...)`, which `parse_run()` converts to CLI 2 with no
  finalized run. These paths do not escape `parse_run()`.
- Annotation-content, annotation-image and inventory hash disagreements retain
  `PARSE_SOURCE_HASH_MISMATCH`; duplicate inventory paths remain the earlier invalid-contract path.

This satisfies AC 5, AC 6, AC 7 and AC 8.

### Reversion tests

- `tests/integration/test_plan002_gc3_8.py::test_selected_pdf_page_two_binds_hash_dimensions_pixels_and_overlay_deterministically`
  proves page 2 hash, decoded size, sanitized embedded pixels and overlay metadata all bind to page
  2, all differ measurably from page 1, and repeated overlays are byte-identical.
- `tests/integration/test_plan002_gc3_8.py::test_disallowed_annotation_inventory_or_format_is_classified_unsupported`
  covers a missing reference, `style_reference`, `other`, raw PDF and JPEG bytes labeled
  `floorplan_page`; every case returns the named code, CLI 2 and no final run.
- `tests/integration/test_plan002_gc3_8.py::test_direct_floorplan_png_and_jpeg_annotation_paths_still_succeed`
  preserves both existing direct-raster arms.
- `tests/integration/test_plan002_gc3_8.py::test_annotation_image_hash_mismatch_remains_hash_mismatch`
  and the existing
  `tests/integration/test_plan002_parse_run.py::test_source_inventory_hash_mismatch_fails_snapshot_before_parsing`
  preserve the distinct hash-mismatch classification.

## R-1 - stderr OSError retains exit 2

The residual-state stderr write in `src/pwa/floorplan/cli.py` now runs inside the existing
`try/except Exception: return 2`. An `OSError` while reporting
`finalized_directory_left_behind` therefore cannot escape `main()` or change the documented exit
from 2 to 1.

Reversion test:
`tests/integration/test_plan002_cli.py::test_main_returns_2_when_residual_diagnostic_stderr_write_raises_oserror`
patches `sys.stderr` with an object whose `write()` raises `OSError`; it does not patch `print`.

## Acceptance-criteria matrix

| AC | Evidence |
|---|---|
| 1 | Exact 1.0.0/1.1.0 catalog tests, latest 1.1.0, existing duplicate pair and duplicate `$id` rejection tests |
| 2 | Pinned frozen-schema digest, historical fixture valid under both versions, 1.0.0 rejects `floorplan_page`, structural three-delta assertion |
| 3 | Intake and derived schema 1.1.0/bundle 1.2.0 assertions; source-manifest byte equality before and after parse |
| 4 | Two-page intake test and all-format DXF/DWG regression test |
| 5 | Page-2 test compares page hashes, sizes, embedded pixels, normalization, overlay metadata and repeated output |
| 6 | Five-case unsupported matrix asserts code, CLI 2 and absent final run |
| 7 | Direct PNG and JPEG parameterized success test |
| 8 | Annotation-image and inventory hash mismatch tests assert the unchanged mismatch code |
| 9 | Full suite, contract modules, golden suite, protected-file digests and dependency diff checks below |

No new test derives or injects a drive/volume assumption; all test paths remain under the supplied
`tmp_path` and have the same outcome regardless of its volume.

## Verification

All executable verification used the repository `.venv` with inherited `PYTHONPATH` removed and
pytest's cache provider disabled. Repository-ignored `.tmp/pytest-na6-*` basetemp directories were
used.

- Initial focused run: 32 passed and one fixture-setup failure because its forged derivative parent
  directory had not been created. The setup was corrected without changing product behavior.
- Repeated focused contract/acceptance run: 33 passed, exit 0.
- Complete `tests/integration/test_plan002_parse_run.py`: 56 passed, exit 0.
- Affected contract/intake/CLI/GC3-8/failure-matrix/floorplan-golden run: 96 passed, exit 0.
- Final plan-text plus schema-contract run: 8 passed, exit 0.
- Final complete suite: **369 passed, exit 0, 94.0 seconds**. This is the 356-test baseline plus 13
  new contract/acceptance tests. The only output was two pre-existing Pillow `getdata()`
  deprecation warnings from `tests/unit/test_floorplan_builder.py`.
- Independent collection count: 369 nodes.
- Final golden suite: 9 passed, exit 0.
- Golden canonical projection hash remained
  `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`.
- `git diff --check`: exit 0 before this report.

## Boundary verification

- Frozen `schemas/project_manifest/v1/project_manifest-1.0.0.schema.json` remained byte-identical:
  `sha256:b8020d9c79fa009d49c1b7bbaa6a64fd8a7caddfeadfc4080e8a1d3033ca33e6`.
- New `schemas/project_manifest/v1/project_manifest-1.1.0.schema.json`:
  `sha256:c5ec58cfc11306630cbb71e6c54f097fee6bad841400b181e695b67553a52ff0`.
- `contracts/error_codes.md` remained byte-identical; no token was added:
  `sha256:4e19219949dfe249e0c5d2d0ca399679ab82d88de9a9f438784d187962e8fbca`.
- `pyproject.toml` remained byte-identical:
  `sha256:f0196ef891c140a6410a4bbcc44aa381dbb38ab0974bdb26a16b26d521c02d5d`.
- `uv.lock` remained byte-identical:
  `sha256:a636f9bca0f4e5f63eb7253386cb5a1248a651d693320f0b5e835975bde0e18a`.
- `src/pwa/floorplan/config.py` remained unchanged:
  `sha256:bfb5c5e4eada292a03c26d979ba8be8682e7b0433fac66e61272d9a4ddbe62d2`;
  `limits_snapshot()` gained no key.
- `docs/plans/PLAN-002-floorplan-parsing.md` changed only at the two clauses named by the approved
  amendment. Its resulting digest is
  `sha256:a5f00fd8214407a543b81a6ffcfaacc750d8f1b5c641a602eea975d83bf088ec`.
- GC3-9 and GC3-10 were not touched by this implementation. No dependency, state-machine or
  unrelated schema file changed.
- Final `git diff --check` after report creation: exit 0.
- Existing evidence files were not edited. This report is the implementer's only new evidence
  file.
- No commit, checkout, reset, merge, rebase, stage or push operation was performed by this
  implementer.

## Runtime metadata from the session rollout

- CLI version: `0.144.6`
- Model ID: `gpt-5.6-sol`
- Provider configuration: `headroom`
- Reasoning effort: `xhigh`
- Originator/source: `codex_exec` / `exec`
- Python: `3.11.15` from the repository `.venv`
- Sandbox mode: `workspace-write`; network disabled; approval policy `never`
- Session ID: `019ff067-d3e9-75f1-9efb-f487f85a9331`
- Session-start branch and HEAD: `panoworld-dev/na-6-gc3-8` at
  `e8e0e7ecddcfd1f14018dfc52121cdad42ca649f`

## Concurrent orchestrator activity at handoff

During final verification, the shared checkout was externally advanced on the same branch from the
session-start HEAD to `761a6abadbc9ba4d102e7c41e3a5a2e2124852a7` by commit
`PLAN-002 NA-7: two gaps in my own AC-13 draft, found against the schema`. That commit adds only
`evidence/PLAN-002/decisions/ac13-provenance-enumeration-draft-20260811.md`; it does not overlap the
NA-6 implementation files or affect executable verification. The NA-6 changes remain unstaged in
the working tree. This implementer did not initiate or reverse the HEAD change.

## Uncompleted work

No dispatched amendment, acceptance criterion, R-1 fix or executable verification is incomplete.
Commit and merge remain the orchestrator's responsibility.
