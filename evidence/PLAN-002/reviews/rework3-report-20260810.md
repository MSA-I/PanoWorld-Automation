<!-- PLAN-002 NA-3b bounded rework report. Repository-relative paths only. -->

# PLAN-002 NA-3b rework 3 report: GC3-1..GC3-7

## Scope and boundaries

Implemented only GC3-1 through GC3-7 from
`evidence/PLAN-002/reviews/na3b-rework3-dispatch-20260810.md`.
No contract, schema, error-code, dependency, approved-plan, or existing-evidence file was
changed. `pyproject.toml` and `uv.lock` are unchanged. GC3-8, GC3-9, and GC3-10 were left
untouched, including `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}`.

## GC3-1 - destination ancestor containment

Changed `src/pwa/floorplan/runs.py` to validate destination paths lexically from an existing
regular `runs_root`, reject every existing symlink/reparse component, create missing staging
directories one checked component at a time, and revalidate the staging and final chains at
finalization. `src/pwa/floorplan/builder.py` now validates both final and staging destinations
before preflight creates or writes anything.

Proof:

- `tests/integration/test_plan002_parse_run.py::test_destination_staging_junction_is_rejected_before_any_external_write`
- The test failed before the fix because the external junction target contained the parse-run
  directory, then passed after the fix with the target empty.

## GC3-2 - inventory copy root and finalized inventory verification

Changed `copy_source_inventory()` to resolve manifest-declared run-relative paths against the
staging run root, eliminating `project/project/...`. `finalize_run()` now verifies every
declared inventory path and SHA-256 before the rename and opens and verifies all of them again
inside the finalized run after the rename.

Proof:

- `tests/integration/test_plan002_parse_run.py::test_parse_run_finalizes_complete_derived_run`
  opens and hashes every finalized `project_manifest.payload.inputs[]` path.
- `tests/integration/test_plan002_parse_run.py::test_post_finalization_inventory_hash_drift_is_not_reported_complete`
  corrupts a declared file immediately after rename and proves the result is operational CLI 2,
  not complete.

## GC3-3 - one immutable snapshot per input

Manifest, quality-report, and annotation source bytes are read once and retained for staged
exclusive writes. Source inventory files are copied once into staging and checked against their
manifest-declared hashes. Annotation and DXF parsing use only staged paths. Annotation parsing
reuses the document decoded from the retained annotation bytes, so parsing, the staged copy, and
lineage bind the same content. Raster source binding reads one staged byte buffer and derives both
the original-byte SHA-256 and sanitized pixels from that buffer.

Proof:

- `tests/integration/test_plan002_parse_run.py::test_dxf_is_parsed_from_verified_staging_snapshot_after_source_swap`
- `tests/integration/test_plan002_parse_run.py::test_annotation_lineage_uses_the_same_staged_snapshot_that_is_parsed`
- `tests/unit/test_floorplan_builder.py::test_source_binding_hash_and_pixels_come_from_one_raster_read`
- `tests/integration/test_plan002_parse_run.py::test_copied_inventory_hash_drift_before_copy_is_rejected`

Each swap test failed for the expected stale-source/stale-lineage reason before the fix and
passed after parsing and binding were routed through the verified snapshots. Inventory snapshot
hash failure maps to `PARSE_SOURCE_HASH_MISMATCH` and CLI 2 before parsing.

## GC3-4 - source-run finality and identity

`resolve_contained_run()` now accepts only a non-dot direct child directory of `runs_root`.
Preflight requires manifest and quality report `project_id` and `run_id` agreement, requires the
run ID to match the source directory, requires exactly one `kind == "floorplan"` entry, and
requires unique inventory paths. All checks happen before staging creation.

Proof:

- `tests/integration/test_plan002_parse_run.py::test_source_run_under_staging_is_not_accepted_as_finalized`
- `tests/integration/test_plan002_parse_run.py::test_source_manifest_and_quality_project_identity_must_match`
- `tests/integration/test_plan002_parse_run.py::test_source_artifact_run_identity_must_match_source_directory`
- `tests/integration/test_plan002_parse_run.py::test_source_manifest_requires_exactly_one_floorplan_input`
- `tests/integration/test_plan002_parse_run.py::test_source_manifest_requires_unique_inventory_paths`

All five tests failed against the prior behavior and now return CLI 2 with no derived staging or
final run.

## GC3-5 - cumulative DXF entity cap

The worker now carries the already-scanned count into every layout scan. It raises
`ValueError("PARSE_RESOURCE_LIMIT")` immediately when processing the next entity would exceed
`MAX_DXF_ENTITIES`, including paperspace and additional layouts.

Proof:

- `tests/integration/test_plan002_parse_run.py::test_cumulative_paperspace_entity_overflow_is_resource_limit_cli3`

The test uses 11 modelspace entities plus two paperspace entities with a test-local cap of 12.
Before the fix it returned operational CLI 2; after the fix the overflow finalizes a failed run
with `PARSE_RESOURCE_LIMIT` and CLI 3.

## GC3-6 - opaque DXF layout and layer names

Known vocabulary remains literal: layout `Model` and the approved `PWA-*` layer set. Every
unknown layout or layer receives a deterministic encounter-order token such as
`unknown-layout-0001` or `unknown-layer-0001`. Shared maps keep repeated names stable and distinct
names distinct within a run. Only tokens reach source refs and messages, and therefore only
tokens can flow into reports, provenance, or overlay labels.

Proof:

- `tests/integration/test_plan002_parse_run.py::test_unknown_dxf_layout_and_layer_names_are_opaque_in_all_artifacts`
- `tests/unit/test_floorplan_sources.py::test_dxf_worker_records_unmapped_source_entities`

The integration test uses two unknown layouts and two unknown layers, asserts that none of their
names appear in `parse-report.json`, `floorplan_parse.json`, or `overlay.svg`, and asserts four
distinct opaque tokens.

## GC3-7 - no operational filesystem exception escapes `parse_run()`

Preflight now catches `OSError` from source containment, destination checks, file reads, and DXF
stat. Staging creation is inside an operational guard. The staged processing guard now catches a
bounded operational set (`OSError`, input/worker `ValueError`, decode errors) instead of bare
`Exception`; genuine programming errors remain visible. Diagnostic persistence is best-effort,
but a secondary diagnostic-write failure cannot escape or replace the returned CLI-2 diagnostic.

Proof:

- `tests/integration/test_plan002_parse_run.py::test_unreadable_source_input_returns_cli2_result_instead_of_raising`
- `tests/integration/test_plan002_parse_run.py::test_programming_error_is_not_hidden_as_operational_cli2`
- Existing OSError and malformed-worker regression tests remain green.

## Verification

The final full-suite command was run from the repository root with inherited `PYTHONPATH`
cleared exactly as dispatched:

```powershell
$env:PYTHONPATH=''; .\.venv\Scripts\python.exe -m pytest -q
```

The managed sandbox denied both configured system-temp locations, so `TEMP` and `TMP` were set
to the repository-relative `.tmp` scratch directory before the command. This did not change the
pytest arguments or repository code. The initial unmodified baseline was also re-run with an
equivalent repository-local basetemp and produced 316 passed, exit 0.

Final result (verbatim test count and exit code): **330 passed, exit 0**.

The only test warning remains the pre-existing Pillow `Image.getdata` deprecation warning. A
sandbox-only pytest cache warning also reported that `.pytest_cache` was not writable; it did not
affect collection or execution.

Additional checks:

- `git diff --check`: exit 0.
- `pyproject.toml` / `uv.lock` diff: empty.
- Schemas, error codes, and approved PLAN diff: empty.
- Golden canonical-projection hash: **did not move**. It remains
  `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`, and both adapter
  assertions in `tests/golden/test_floorplan_golden.py` passed in the full suite.

## Escalations and deliberately untouched items

No GC3-1..GC3-7 fix required crossing a hard boundary, so there is no escalation from this
rework.

Deliberately left untouched as out of scope:

- GC3-8 PDF-page kind/role contract work.
- GC3-9 historical evidence/path decision and every pre-existing evidence file.
- GC3-10 visual gate and artifact regeneration.
- The existing Pillow deprecation warning.

No commit, add, checkout, stash, reset, or other index/history-changing Git operation was run.

## Follow-up: GC3-11 - untrusted input exception containment

The narrowed staged-processing handler now names both Pillow size-guard failures that can
originate from the staged untrusted raster: `Image.DecompressionBombError` and
`Image.DecompressionBombWarning` (the latter when the process promotes warnings to errors).
Both `AnnotationSource.extract()` and `_source_binding()` open the staged raster inside this
same guarded processing block, so either open returns a `ParseRunResult` with operational
`cli_exit == 2`; neither can escape `parse_run()`.

The required proof-of-concept is
`tests/integration/test_plan002_parse_run.py::test_pillow_decompression_bomb_is_operational_cli2`.
It creates the normal small fixture first, then lowers `Image.MAX_IMAGE_PIXELS`. Against the
pre-follow-up code it failed by leaking `PIL.Image.DecompressionBombError` from
`AnnotationSource.extract()`; after the fix it returns a `ParseRunResult`, reports
`outcome == "operational_failure"`, and has `cli_exit == 2`. The companion
`test_pillow_decompression_bomb_warning_as_error_is_operational_cli2` proves that a promoted
`DecompressionBombWarning` follows the same contract.

Audit of the same untrusted-input paths:

- Pillow 12.3.0's `UnidentifiedImageError` derives from `OSError`, so corrupt or unidentified
  raster files were already covered. Pillow's format-probe `SyntaxError`, `IndexError`,
  `TypeError`, and `struct.error` cases are consumed inside `Image.open()` and fall through to
  `UnidentifiedImageError`; they are therefore not reachable from these call sites as those
  raw exception classes. The public `Image.open()` `TypeError` requires invalid caller-supplied
  `formats`, but these call sites use Pillow's fixed default, so that case would be a
  programming error rather than input handling and remains uncaught.
- `_source_binding()` forces lazy raster decoding while re-encoding. Decoder failures from
  truncated/corrupt pixels are `OSError` (and format/value failures are `ValueError`), both
  already named by the operational handler. Encoder `TypeError`/`KeyError` requires a bad
  program-supplied format or option; the code supplies fixed `PNG`/`JPEG` formats and numeric
  constants, so those classes remain programming errors and propagate.
- Annotation JSON decoding now also handles the input-driven `ValueError` produced by Python's
  integer-string conversion limit and `RecursionError` produced by excessive nesting. A
  decoded top-level value that is not an object is rejected before `validate_artifact()` can
  call `.get()` on it. The three cases are covered by
  `test_annotation_json_input_failures_are_operational_cli2`.
- Manifest and quality-report decoding now handles excessive-nesting `RecursionError`, and
  both documents must be objects before validation or `.get()` access. Manifest and quality
  non-object cases plus recursive manifest JSON are covered by
  `test_source_artifact_json_input_failures_are_operational_cli2`.
- After schema validation, the annotation, manifest, and quality-report shapes used by the
  remaining code are closed, typed schemas. Input-driven missing-member/wrong-type accesses
  are therefore rejected before staged processing. `AnnotationSource.extract()`'s internal
  JSON-read branch is also unreachable from `parse_run()`, which always supplies the retained,
  already decoded document. Consequently `RuntimeError`, `TypeError`, `AttributeError`, and
  other programming failures are not added to an operational catch. The existing
  `test_programming_error_is_not_hidden_as_operational_cli2` remains green.

No bare `except Exception` was introduced. No contract, schema, error code, dependency,
approved-plan file, GC3-8/GC3-9/GC3-10 code, or `_APPROVED_ANNOTATION_IMAGE_KINDS` was changed.
`pyproject.toml` and `uv.lock` remain byte-identical (their Git diff is empty).

Follow-up verification used the dispatched full-suite command from the repository root, with
`TEMP` and `TMP` pointed at the repository-relative `.tmp` scratch directory because the
managed sandbox denies the system temp directory:

```powershell
$env:PYTHONPATH=''; .\.venv\Scripts\python.exe -m pytest -q
```

New full-suite result (verbatim count and exit code): **338 passed, exit 0**. The count was
confirmed by `--collect-only -q` after the successful full run because the repository's own
`addopts = "-q"` combines with the dispatched `-q` and suppresses pytest's final count line.
`git diff --check` also returned exit 0. The golden canonical-projection assertions both passed
in the full suite and remain exactly
`sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`.
