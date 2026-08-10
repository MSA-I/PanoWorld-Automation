# Orchestrator verification of NA-3e (PLAN-002, fourth bounded rework)

Subject: branch `panoworld-dev/na-3e-major-fixes`, cut from `main` at `c1cbc45`.
Implementer report: `evidence/PLAN-002/reviews/rework4-report-20260810.md`.
Dispatch brief: `evidence/PLAN-002/reviews/na3e-rework4-dispatch-20260810.md`.
Governing review: `evidence/PLAN-002/reviews/independent-anthropic-rework3-review-opus-20260810.md`.
Date: 2026-08-10. Author: orchestrator (Anthropic `claude-opus-5[1m]`, EXTRA).

The implementer's report was not accepted as evidence. Everything below was executed or read by
the orchestrator. Paths are repository-relative per section 12; scratch material lives outside
the repository and is referred to as `<scratch>/...`.

## 1. The three proofs-of-concept that demonstrated the defects, re-run against the fixes

The same scripts that proved F-1, F-3 and F-7 before the rework were re-run with the opposite
expectation. `<scratch>/verify_na3e.py`, with the containment root on a drive letter distinct
from the escape target (a `subst` of the scratch directory), so a surviving escape would land
inside the sandbox:

```
[PASS] F-3 _contained_parts('C:x')           rejected: path must be a contained relative path
[PASS] F-3 validate_contained_destination    rejected
[PASS] F-3 resolve_contained_output          rejected
[PASS] F-3 create_contained_directory        rejected
[PASS] F-3 write_bytes_contained             rejected
[PASS] F-7 _contained_parts('a.dxf:evil')    rejected
[PASS] F-7 resolve_contained_output          rejected
[PASS] F-7 write_bytes_contained             rejected
[PASS] no file written outside the root      landing dir contains []
[PASS] no ADS attached to the host artifact  stream absent
[PASS] host artifact bytes unchanged         b'ORIGINAL-PAYLOAD'
[PASS] legit 'project/source-manifest.json'  ACCEPTED
[PASS] legit 'a/b/c.json'                    ACCEPTED
[PASS] legit single 'x.json'                 ACCEPTED
[PASS] still rejects '..'                    rejected
[PASS] still rejects absolute                rejected
[PASS] still rejects empty                   rejected
17/17 checks passed
```

The last six lines matter as much as the first eight: a containment fix that also rejects
`project/source-manifest.json` would be a worse defect than the one it closes, and it does not.

F-1's probe (`<scratch>/test_f1_probe.py`, which reuses the repository test's own fixtures from
outside the tree so nothing in the repository is modified) now reports:

```
cli_exit             = 2
diagnostic.outcome   = operational_failure
final_run.exists()   = False      <- was True before the fix
staging_run.exists() = True       <- was False before the fix
```

That is the invariant `test_operational_failure_retains_staging_and_no_finalized_run` asserts
for every other operational failure, and F-1 was the one path that violated it.

## 2. Boundaries, checked independently

| Boundary | Command | Result |
|---|---|---|
| dependencies, schemas, contracts, plan docs | `git diff --stat main -- pyproject.toml uv.lock schemas contracts docs/plans docs/decisions` | empty |
| limits and golden expectation | `git diff --stat main -- src/pwa/floorplan/config.py tests/golden` | empty |
| `limits_snapshot()` | diff of `config.py` | 0 lines changed, so no new key |
| GC3-8 not touched | grep | `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}` unchanged at `src/pwa/floorplan/annotation_source.py:25` |
| whitespace | `git diff --check` | exit 0 |
| evidence rewritten | the only new file under `evidence/` is the implementer's own report | append-only respected |

## 3. What I found that the implementer's report does not say

### V-1 (blocking, dispatched back as GC4-1) — one new test is environment-dependent and fails here

`tests/integration/test_plan002_failure_matrix.py::test_destination_containment_is_reproved_if_component_grammar_misses_drive_anchor`
fails on the machine of record. The suite here was **350 passed, 1 failed**, against the report's
claim of 351 passed.

The fix is not at fault; the test is. It monkeypatches `_contained_parts` to return
`("C:", "pwa_escape", "owned.txt")` so the second containment layer can be exercised, but
`pathlib` discards the left-hand path **only when the injected drive differs from the root's
drive**. pytest's `tmp_path` is on `C:` here, so there is no escape for the second layer to
reject. Measured directly, with a root on `C:`:

```
injected 'C:'  -> ACCEPTED, leaf still under the root
injected 'Q:'  -> rejected: "path escapes containment root"
```

So the test passes or fails depending on which volume pytest puts its temp directory on, which
is a property of the machine and not of the code. Dispatched back to the same implementer rather
than patched by the orchestrator, keeping section 17's provider separation intact — the same
discipline used for GC3-11 in the previous round. Its sibling at line 100 is
environment-independent, because `_contained_parts` now rejects any component containing `:`
before any drive logic runs.

### V-2 (observation for the reviewer) — the raster read is still unbounded, and F-2 moved it earlier

`MAX_SOURCE_RASTER_BYTES` (50 MiB) is enforced at `src/pwa/floorplan/overlay.py:110`, inside
overlay rendering. F-2's snapshot reads the whole staged raster with `read_bytes()` at
`src/pwa/floorplan/annotation_source.py`, before that cap is ever consulted. Before the rework
the adapter streamed the file in 1 MiB chunks through `sha256_file` and let Pillow open it
lazily; the first full materialisation happened later, in `_source_binding`.

This is **not a new defect** — the unbounded `read_bytes()` already existed one step downstream,
inside the same `try` — but F-2 moved it earlier, and the reasoning that produced F-6's fix (read
at most the cap plus one byte, so the limit bounds the read it names) was applied to the
annotation JSON and not to the raster. `MemoryError` remains outside the handler tuple. Intake
caps its own inputs at 250 MiB, so the exposure needs a source run written by something other
than intake, which is the threat model GC3-1 already accepts.

### V-3 (observation for the reviewer) — the rollback-failure signal travels in an overlay field

When rollback after a failed post-rename verification itself fails, the residual state is
reported by setting `overlay_omitted_reason` to `"finalized_directory_left_behind"`. That field
exists to say why an overlay was omitted. Using it to report a filesystem rollback failure is a
semantic overload, and a consumer reading it would be misled about what kind of thing went
wrong. The dispatch forbade new contract surface, so this may be the least-bad option inside the
boundaries — but the reviewer should say whether the boundary is the thing that should give.

### V-4 (residue, not a defect) — staging keeps a report that says `complete`

After a successful rollback, `staging_run` exists again with the full happy-path artifact set,
including a `parse/parse-report.json` that reads `"outcome": "complete"`. `builder.py`'s
`_staged_operational_result` skips writing its failure report because one already exists at that
path. The published invariant holds — there is no finalized run, and the returned diagnostic is
accurate — but a human inspecting the retained staging directory sees a report claiming success
for a run that failed. Recorded rather than fixed, because fixing it means either overwriting an
exclusively-created artifact or adding a new one, and both deserve a reviewer's opinion first.

## 4. Read-through of the change set

The four production files were read as a diff, not sampled:

- `runs.py` — `":" in part` added to the component grammar; `validate_contained_destination`
  gains the closing `resolve()` / `relative_to()` proof its read-side sibling already had, with
  `strict=True` on the root, which is safe because the function already requires the root to be
  an existing directory. `finalize_run` verifies derived artifacts on both sides of the rename
  and rolls back on failure, raising `FinalizedRunLeftBehindError(OSError)` only when the
  rollback itself fails — and because it derives from `OSError` the existing handler tuple
  catches it, so `parse_run()` still cannot raise.
- `annotation_source.py` — one `read_bytes()`, one digest computed from those bytes, that digest
  compared independently against both the annotation declaration and the inventory entry
  (strictly stronger than the old declaration-to-declaration comparison), dimensions decoded
  from `BytesIO` over the same bytes, and the bytes returned for embedding. `source_image_ref`
  is resolved through `resolve_contained_relpath` inside the adapter, before the first open.
- `files.py` — `create_parents` is opt-in, so PLAN-001 intake keeps its existing behaviour and
  only the floorplan call sites take the checked mode. That is what the brief asked for.
- `builder.py` — every staged write goes through the checked mode; the annotation read is
  bounded to `MAX_ANNOTATION_BYTES + 1`, and the overflow lands on the existing
  `PARSE_RESOURCE_LIMIT` branch unchanged.

Six of the seven derived-envelope checks in `verify_run_derived_artifacts` are required paths
that every finalisation path writes, including the failed-scale paths, and the overlay
declaration check skips a declaration with no `path` key — which is exactly the shape a
failed-scale run produces (`{"overlay_omitted_reason": ...}`). The suite result corroborates
that reading.

## 5. Status

F-1, F-2, F-3, F-4, F-5, F-6, F-7 and F-8 are implemented, and the three that had executable
proofs-of-concept are proven closed by re-running them. V-1 must be green before this round can
be called anything other than `REWORK`. V-2, V-3 and V-4 are handed to the NA-3f reviewer as
open questions rather than resolved by the orchestrator, because the orchestrator wrote the
brief that constrained the answers.
