<!-- Second bounded rework closing the OpenAI (gpt-5.6-sol) cross-provider
     rework review's NEEDS_REWORK findings.
     PROVIDER: anthropic | MODEL_ID_EXACT: claude-sonnet-5 | EFFORT: HIGH
     MODEL_REASON: OpenAI Codex CLI unavailable; documented MODEL-ROUTING-v1
     fallback (OpenAI Codex -> Sonnet 5 HIGH). Approved by Moshe 2026-08-10. -->

# PLAN-002 second rework report — 2026-08-10

## Skills loaded (mandatory first step, PLAN-002 §17)

`python-patterns`, `test-driven-development`, `security-audit`, `file-path-traversal`,
`python-testing-patterns`, `debugging-strategies`.

## Scope

Closed every finding in `evidence/PLAN-002/reviews/independent-openai-rework-review-20260810.md`'s
"Required gate conditions before approval" list (GC-1..GC-5) plus the five further confirmed
majors (A..E). GC-6 (opening width projection) and the JPEG-EXIF overlay question were explicitly
out of scope per the dispatch brief and were **not touched**.

## Disposition table

| Finding | Status | Proving test |
|---|---|---|
| **GC-1** — `parse_run_id` permits writes outside `runs_root` | FIXED | `test_parse_run_id_absolute_path_is_rejected`, `test_parse_run_id_dotdot_traversal_is_rejected` |
| **GC-2** — `resolve()` erases reparse points before they are checked | FIXED (in both `resolve_contained_run` and `resolve_contained_relpath` — see note) | `test_source_run_junction_alias_resolving_inside_runs_root_is_rejected`, `test_runs_root_itself_as_a_junction_is_rejected` |
| **GC-3** — manifest/quality-report paths read without containment | FIXED | `test_manifest_project_ancestor_junction_is_rejected` |
| **GC-4** — annotation integrity/lineage not verified or recorded | FIXED | `test_annotation_content_hash_tamper_is_rejected`, `test_annotation_lineage_is_bound_into_floorplan_parse_inputs` |
| **GC-5** — annotation may bind to a style image instead of the floorplan | FIXED (bounded to `kind == "floorplan"` — see note) | `test_annotation_binding_to_non_floorplan_kind_is_rejected` |
| **A** — copied inventory not rehashed after copying | FIXED | `test_copied_inventory_hash_drift_before_copy_is_rejected` |
| **B** — more preflight inputs raise out of `parse_run()` | FIXED | `test_manifest_with_no_schema_fields_returns_operational_cli2`, `test_missing_annotation_file_returns_operational_cli2` |
| **C** — unsupported DXF semantics hidden by cardinality failure | FIXED | `test_unsupported_arc_precedence_over_empty_geometry` |
| **D** — DXF overlay unusable for metre-unit DXFs / clips disagreeing detections | FIXED | `test_dxf_overlay_opening_radius_scales_with_metre_units`, `test_dxf_overlay_bounds_include_detected_geometry_outside_source_primitives`, updated `test_dxf_overlay_source_layer_is_independent_of_detections` |
| **E** — overlay written non-exclusively, can follow a symlink | FIXED | `test_overlay_write_is_exclusive_and_rejects_preexisting_path` |
| GC-6 (opening width projection) | OUT OF SCOPE — untouched, reserved for Moshe | — |
| JPEG EXIF in overlay | OUT OF SCOPE — untouched, reserved for Moshe | — |

No escalation was required. Every fix stayed inside `src/pwa/floorplan/**` +
`tools/make_floorplan_fixtures.py` + `tests/**` (PLAN-002 §16); none required a contract/schema
change, a new dependency, or network access.

## Per-finding detail

### GC-1 — `parse_run_id` path traversal (`builder.py`)

Added `_is_valid_parse_run_id()`: a closed allowlist grammar (`^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`)
checked as the very first thing `parse_run()` does, before any path is constructed from the value.
No separator, drive letter, UNC prefix, or leading `.`/`..` can pass. Also added an independent
`final_run.relative_to(runs_root)` / `staging_run.relative_to(runs_root)` containment check
immediately after (defense in depth per the review's explicit "independently prove" wording,
though unreachable given the grammar). All existing `parse_run_id` values in the test suite
(`RUN-YYYYMMDD-...`, `f"RUN-{fixture}-parse"`) are plain alnum/hyphen and pass unchanged.

### GC-2 — reparse points resolved away before inspection (`runs.py`)

Both `resolve_contained_run()` **and** `resolve_contained_relpath()` had the identical defect: each
called `.resolve()` on the full candidate before walking its ancestors, so the ancestor walk only
ever inspected the *already-substituted* resolved path components, never the original (possibly
reparse-point) lexical ones. `resolve_contained_relpath()` is not incidental — it is the exact
containment helper GC-3 routes the manifest/quality reads through, so fixing only
`resolve_contained_run` would have left GC-3's remedy hollow. Both functions were reworked to walk
the *lexical* (never-resolved) ancestor chain from the root down, checking `is_link_or_reparse()`
at each step before any substitution can occur, then independently re-confirm containment via
`resolve()` afterward as defense in depth. `resolve_contained_run()` also now rejects a `runs_root`
that is itself a reparse point (checked before `resolve(strict=True)` erases it).

The pre-existing `test_operational_fixture_matrix_f_ancestor_reparse` (Windows junction test) does
not actually exercise this ordering bug — its junction target is deliberately outside `runs_root`,
so the plain "resolved path escapes root" check already rejects it for an unrelated reason
regardless of ordering. The two new tests place the junction target *inside* `runs_root`
(`runs/alias -> runs/actual-runs/...`), which is the case the review describes and which the
pre-fix code silently accepted.

### GC-3 — manifest/quality-report read without containment (`builder.py`)

`manifest_path`/`quality_path` now go through `resolve_contained_relpath(source_run, "project/...")`
before `read_text()`, wrapped in `except (ValueError, OSError, json.JSONDecodeError)`. The proving
test places a junction at `source_run/"project"` pointing at byte-identical content still inside
`source_run` (an external target would be caught by an unrelated existing check for the wrong
reason — see the test's docstring); unfixed, the whole run finalized successfully (`cli_exit == 0`)
instead of being rejected.

### GC-4 — annotation integrity/lineage (`annotation_source.py`, `builder.py`)

`AnnotationSource.extract()` now recomputes and verifies `content_hash` via
`pwa.contracts.compute_content_hash` immediately after schema validation, raising
`PARSE_SOURCE_HASH_MISMATCH` (same code/treatment as every other source-integrity check) on
mismatch. `parse_run()` now binds `{artifact_id, content_hash}` from the annotation document into
every `floorplan_parse.inputs[]` it builds (`_annotation_input()` helper, threaded through
`_failed_scale_artifacts()` and the main success path).

Per the review's own note, existing tests constructed annotations with an all-zero content hash;
all such fixtures were updated to compute a real one:
- `tests/unit/test_floorplan_sources.py::_write_annotation_fixture`
- `tests/integration/test_plan002_parse_run.py::_annotation_doc`
- `tests/integration/test_plan002_failure_matrix.py::_rewrite_annotation` (now recomputes the hash
  after mutating the payload, mirroring `_rewrite_envelope`, which already did this for the
  manifest/quality envelopes)
- `tools/make_floorplan_fixtures.py` (the canonical Layer-A evidence-fixture generator carried the
  same placeholder)
- Four individual tests that mutate an annotation document inline
  (`test_annotation_source_image_must_bind_to_source_inventory`,
  `test_annotation_dimension_mismatch_is_rejected`,
  `test_annotation_scale_mismatch_finalizes_failed_cli_3_run`,
  `test_empty_annotation_geometry_finalizes_failed_cli_3_run`) now recompute `content_hash` after
  their mutation so they keep exercising their originally-intended rejection path (image binding /
  dimension mismatch / scale mismatch / empty geometry) rather than being pre-empted by the new,
  higher-precedence hash check. None of these changes weaken any assertion — they restore each
  test's original intent now that a prerequisite (a *valid* hash) is enforced earlier in the
  pipeline.

### GC-5 — annotation may bind to a non-floorplan image (`annotation_source.py`)

Added `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}` and a check against
`source_inventory[image_ref]["kind"]`. **Bounded design note:** PLAN-002 §6 also permits "one
explicitly selected intake-generated PDF page ... already listed in the source manifest," but
`src/pwa/intake.py`'s current inventory vocabulary tags PDF-page derivatives (and the DXF preview)
with the same generic `kind: "other"` as any other non-floorplan/non-style artifact — there is no
distinct kind to safelist for PDF pages without a manifest/contract change, which is out of this
bounded rework's scope. The fix is therefore conservative: it closes the reported vulnerability
(binding to `style_reference`) and rejects every non-`"floorplan"` kind, including `"other"`. No
existing test binds an annotation to a PDF-page derivative, so nothing regresses; this is flagged
here for Moshe's awareness rather than escalated, since it does not change any existing contract or
remove any previously-working capability.

### A — copied inventory not rehashed after copying (`runs.py`)

`copy_source_inventory()` now compares `copy_immutable()`'s returned hash (computed from the bytes
actually copied) against the manifest-declared `item["sha256"]` (captured at preflight), raising
`ValueError` on mismatch. Previously `copy_immutable()`'s own hash check only proved
"destination == what was just read from source," not "destination == what preflight verified."
The proving test simulates the TOCTOU gap by making `builder.sha256_file` return the stale
(pre-tamper) hash for one file during preflight while the real bytes on disk are already tampered —
exactly what an intervening external write would look like from `parse_run()`'s point of view.

### B — preflight inputs still raise out of `parse_run()` (`builder.py`)

- `validate_artifact(source_manifest) or validate_artifact(source_quality)` is now wrapped in
  `try/except (ValueError, KeyError)`, classifying the result as CLI 2 instead of propagating.
- `Path(annotation).stat()` is now wrapped in `try/except OSError`.
- `validate_artifact(annotation_document)` (a few lines below) got the same
  `except (ValueError, KeyError)` treatment for consistency, since it is the identical failure mode.

### C — unsupported DXF semantics hidden by cardinality failure (`builder.py`)

`_prevalidate_raw()` still raises only on an *actual* cardinality problem (unchanged trigger
conditions — healthy geometry with unrelated `raw.errors` entries still falls through to the normal
`normalize()`/`validate()`/`sort_findings()` path, exactly as before). When it does raise, it now
picks the highest-precedence (lowest-tier) finding from the combination of `raw.errors` and the
cardinality problem(s) via `sort_findings()`, instead of always raising `PARSE_EMPTY_GEOMETRY`/
`PARSE_RESOURCE_LIMIT` and discarding `raw.errors`.

*(Caught during implementation: my first draft of this fix always raised whenever `raw.errors` was
non-empty, which would have broken the existing "healthy geometry + unrelated unsupported entity"
test — `test_operational_fixture_matrix[f-annotation-schema]`-style and
`test_failed_domain_fixture_matrix[f-unsupported-arc]` fixtures rely on *not* short-circuiting here.
Corrected before it ever reached the "green" test run.)*

### D — DXF overlay unusable for metre-unit DXFs (`overlay.py`, `config.py`)

Added `OVERLAY_OPENING_RADIUS_FRACTION = 0.01` and `OVERLAY_FONT_SIZE_FRACTION = 0.02` (both in
`limits_snapshot()`). `_dxf_svg()` now scales the opening-marker radius and id/confidence label
font-size to a fraction of `max(width, height)` instead of a fixed `r="20"`/SVG-default text size.
Bounds now also include every normalized wall/room/opening point (inverse-transformed back into
source-unit space), not just the source primitives, so a detection that disagrees with the source
enough to fall outside the old narrow bounds is no longer clipped/invisible. `_raster_svg()` is
untouched (its pixel viewBox was never the problem; verified via `git diff --stat` showing zero
raster-path changes and all raster overlay tests passing unmodified).

The existing `test_dxf_overlay_source_layer_is_independent_of_detections` deliberately built a case
where the normalized wall fell *outside* the source-primitive-only viewBox — its own comment said
"same viewBox (sized from the source primitives)" as if that were correct, when it was actually
demonstrating the exact clipping bug this fix closes. I updated its comment and expected
coordinates to reflect the new (correct) wider viewBox that contains both source and detection,
and added an explicit assertion that the disagreeing wall endpoint is now inside the viewBox. This
is a legitimate correction, not a weakening: the test's original purpose (source vs. detection must
show genuinely different coordinates) still holds and is still asserted.

The tracked Layer-A evidence fixture's DXF overlay changed as a direct, expected result:
`evidence/PLAN-002/overlays/layer-a-1-dxf.svg`, `evidence/PLAN-002/parse/layer-a-1-dxf.json`,
`evidence/PLAN-002/determinism/geometry-projection-hashes.json`, and
`evidence/PLAN-002/implementation/plan002-evidence-meta.json` were regenerated (see Evidence
section). `canonical_projection_sha256` is unchanged, confirming the fix touches rendering only,
never geometry.

### E — overlay written non-exclusively, can follow a symlink (`builder.py`)

`overlay_path.write_bytes(overlay_bytes)` replaced with `overlay_path.open("xb")` (the same
exclusive-create discipline `write_json_exclusive` already uses for every other staged artifact).
`pwa/files.py` is PLAN-000/001 runtime and outside PLAN-002 §16 ownership, so the write was
implemented inline in `builder.py` rather than by adding a shared `write_bytes_exclusive()` helper
there.

Implementing this surfaced a real, previously-unreachable ordering bug: `parse-report.json` was
written *before* the overlay in the success path, so if the (now-fallible) overlay write failed,
the generic `except Exception:` handler's own `write_json_exclusive(.../parse-report.json, ...)`
call would raise a *second*, uncaught `FileExistsError` (the file already existed from the earlier
successful write), escaping `parse_run()` entirely instead of returning a clean `cli_exit=2`. Fixed
by moving the overlay write to happen *first*, before any of the envelope JSON writes, so a failure
there leaves nothing on disk yet and the exception handler's assumptions hold. Caught by the
`test_overlay_write_is_exclusive_and_rejects_preexisting_path` test itself failing with an
unhandled exception before the reorder, and passing cleanly after.

## Test counts

- Baseline: 291 tests, 0 failures/errors, exit 0.
- Final: **306 tests, 0 failures, 0 errors, 0 skipped, exit 0** (15 new tests: 13 in
  `tests/integration/test_plan002_parse_run.py`, 2 in `tests/unit/test_floorplan_overlay.py`; three
  of the thirteen are Windows-junction tests gated `skipif(os.name != "nt")` and confirmed to
  actually execute — not skip — on this machine).
- Every new test was confirmed to fail for the stated reason against the pre-fix code before the
  corresponding fix was implemented (TDD red/green, verified via targeted `pytest` runs at each
  step, not just the final full-suite pass).

## Verification performed

- `git diff --check`: clean (exit 0).
- `git diff -- pyproject.toml uv.lock`: empty (AC-22, no dependency changes).
- `git status --short`: only the intended files touched (see below); no stray/junk files created.
  `PROJECT-STATE.yaml` shows as modified but that change predates this session (the orchestrator's
  prior update) and was not touched by this rework.
- DXF-path overlay determinism re-verified end-to-end (not just via the existing raster-path
  determinism test): two independent `parse_run()` calls against the same Layer-A DXF fixture
  produce byte-identical `overlay.svg` (sha256 `a181228d...` both times).
- No network, install, dependency, GPU/cloud, merge, or push action occurred at any point.
- No PLAN clause, schema, or `contracts/error_codes.md` entry was changed.

## Files touched (all within PLAN-002 §16 ownership)

```
src/pwa/floorplan/annotation_source.py
src/pwa/floorplan/builder.py
src/pwa/floorplan/config.py
src/pwa/floorplan/overlay.py
src/pwa/floorplan/runs.py
tools/make_floorplan_fixtures.py
tests/integration/test_plan002_failure_matrix.py
tests/integration/test_plan002_failures.py
tests/integration/test_plan002_parse_run.py
tests/unit/test_floorplan_overlay.py
tests/unit/test_floorplan_sources.py
evidence/PLAN-002/overlays/layer-a-1-dxf.svg
evidence/PLAN-002/parse/layer-a-1-dxf.json
evidence/PLAN-002/determinism/geometry-projection-hashes.json
evidence/PLAN-002/implementation/plan002-evidence-meta.json
```

## Escalations

None. Every finding was closeable as a bounded code fix within the existing contract, schema, and
dependency set, as the review itself anticipated for GC-1 through GC-5 and A through E.
