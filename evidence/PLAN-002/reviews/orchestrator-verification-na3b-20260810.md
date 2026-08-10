<!-- Orchestrator independent verification of the NA-3b third bounded rework (GC3-1..GC3-7).
     Nothing here is taken from the implementer's report. Every claim below was produced by
     running the real code. Paths are repository-relative per PLAN-002 section 12. -->

# NA-3b — orchestrator verification of the third rework, 2026-08-10

Reviewed work: the uncommitted-then-committed changes on branch
`panoworld-dev/na-3b-gc3-fixes`, implemented by OpenAI `gpt-5.6-sol` (xhigh) through the
Codex CLI with direct workspace-write filesystem access, against the dispatch brief
`evidence/PLAN-002/reviews/na3b-rework3-dispatch-20260810.md`. The implementer's own report
is `evidence/PLAN-002/reviews/rework3-report-20260810.md`.

**Verdict of this verification: GC3-1..GC3-7 are closed, and one regression that this rework
itself introduced (recorded as GC3-11) was found by the orchestrator, dispatched back to the
same implementer as a bounded follow-up, and is also closed.** This is not an acceptance of
PLAN-002. The independent cross-provider review (NA-3d) has not run.

## Method

The point of this exercise is that a green suite has coexisted with a live defect in three
consecutive review rounds. So nothing was accepted on report:

1. A **pre-fix source tree** was reconstructed by copying `src/pwa` and restoring the four
   changed modules from `HEAD` (the pre-rework commit), alongside copies of `schemas/` and
   `contracts/` so `REPO_ROOT` resolution still worked.
2. Orchestrator-authored proofs-of-concept were run against **both** trees with the
   repository `.venv` (CPython 3.11) and the inherited `PYTHONPATH` cleared. A fix counts as
   closed only when the same PoC reproduces the defect before and fails to reproduce it
   after.
3. The implementer's 15 new tests were additionally run against the pre-fix tree to check
   they are not vacuous.

## Baseline and boundaries

| check | result |
|---|---|
| baseline suite on `main` before the rework | 316 passed, exit 0 |
| suite after the rework | 330 passed, exit 0 |
| suite after the GC3-11 follow-up | **338 passed, exit 0** |
| `git diff --check` | exit 0 |
| `pyproject.toml`, `uv.lock` diff | empty |
| `schemas/`, `contracts/`, `docs/`, `.gitattributes`, `.gitignore` diff | empty |
| pre-existing files under `evidence/` | untouched; two new files only |
| golden canonical-projection hash | unchanged, `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`, 9 golden tests pass |
| absolute paths / OS account name in the new evidence files | 0 occurrences |
| `_APPROVED_ANNOTATION_IMAGE_KINDS` (GC3-8 territory) | unchanged |

Three zero-byte junk files were created in the repository root during this round by broken
shell quoting — `1` and `CLI` by the follow-up run, and `-,+` by an orchestrator verification
command — and all three were deleted before committing. `git status` was confirmed clean of
them. Recorded because the same failure mode has produced committed junk in this repository
before, so the check belongs in the record rather than in someone's memory.

## GC3-1 — CRITICAL — destination ancestor containment: CLOSED

PoC: build a real source run with `ingest_project()`, make `runs/.staging` a junction
(`mklink /J`) to a directory outside `runs_root`, then call the real `parse_run()`. Two
cases, matching the NA-3 reproduction: an annotation with a stale `content_hash` (fails after
the inventory copy, so residue is retained) and an otherwise-valid run.

```
pre-fix, failure path : cli_exit 2, and 5 files written OUTSIDE runs_root and left there
    RUN-POC-A-001/parse/parse-report.json
    RUN-POC-A-001/project/project/inputs/originals/floorplan.png
    RUN-POC-A-001/project/project/inputs/originals/style_reference.png
    RUN-POC-A-001/project/source-manifest.json
    RUN-POC-A-001/project/source-quality-report.json

after   , failure path : cli_exit 2, 0 files outside runs_root, no final run
after   , valid path   : cli_exit 2, 0 files outside runs_root, nothing created
```

The escape is closed at the point the review demanded: the whole destination chain is walked
component by component and every existing component is rejected if it is a link or reparse
point, before anything is created (`src/pwa/floorplan/runs.py`,
`validate_contained_destination()` / `create_contained_directory()`; called from
`src/pwa/floorplan/builder.py` before preflight writes anything).

## GC3-2 — MAJOR — inventory copy root and post-finalization verification: CLOSED

PoC: finalize a real complete DXF run, then open every path declared in the finalized
`project_manifest.payload.inputs[]` and re-hash it.

```
pre-fix : cli_exit 0, run reports complete, and all three declared paths DO NOT EXIST
          (files are physically at project/project/inputs/...)
after   : cli_exit 0, all three declared paths exist with matching SHA-256
          project/inputs/originals/floorplan.dxf
          project/inputs/originals/style_reference.png
          project/inputs/derivatives/dxf/preview.svg
```

`finalize_run()` now verifies the declared inventory before the rename and again inside the
finalized run afterwards.

## GC3-3 — MAJOR — one immutable snapshot per input: CLOSED (by inspection + tests)

Not separately reproduced by the orchestrator; a TOCTOU race needs an interleaving harness,
and the implementer's three tests for it all fail against the pre-fix tree. Verified by
reading the code that the shape is right: the manifest, quality report and annotation bytes
are each read exactly once and reused for validation, staging and lineage; the annotation
document decoded from those bytes is passed into `AnnotationSource.extract()` instead of
being re-read; the DXF and the raster are parsed from the **staged** copy whose hash was
verified against the manifest declaration during the copy; and `_source_binding()` derives
both the original-byte SHA-256 and the sanitised pixels from a single `read_bytes()` buffer.
GC-7's property is preserved — the bound hash is still the hash of the original bytes, not of
the sanitised re-encode.

**Disclosure the implementer's report does not make explicitly.** The pre-staging inventory
hash check (`sha256_file(input_path)` in the preflight loop) was **removed**, and
`tests/.../test_source_inventory_hash_mismatch_fails_preflight_without_staging` was replaced
by `..._fails_snapshot_before_parsing`. A source-inventory hash mismatch is still `cli_exit 2`
with no final run, and the hash is still verified before any parsing, so the section 20
semantics Moshe approved ("all pre-parse source hash mismatches are CLI 2 / no final run")
still hold — but staging is now created and partially populated before the mismatch is
detected, where previously nothing was created. The orchestrator's assessment is that this is
required rather than optional: the removed check was a second read of the same file, which is
exactly the TOCTOU that GC3-3 exists to eliminate. It is flagged here because a test rewritten
to match new behaviour can be either a correction or a weakening, and that judgement belongs
to the independent reviewer, not to the implementer or the orchestrator.

## GC3-4 — MAJOR — source-run finality and identity: CLOSED (by tests + inspection)

`resolve_contained_run()` now requires a direct, non-dot child of `runs_root`, and preflight
requires manifest/quality `project_id` and `run_id` agreement, the run id to match the source
directory name, exactly one `kind == "floorplan"` entry, and unique inventory paths. All five
of the implementer's tests for these fail against the pre-fix tree.

## GC3-5 — MAJOR — cumulative DXF entity cap: CLOSED

PoC at the worker's own subprocess entry point (`dxf_worker.main`), not through the
monkeypatched `DxfSource` the implementer's test uses: 10 modelspace entities plus 40
paperspace entities against a cap of 20.

```
pre-fix : worker exits 0, scanned_entities 50, 40 findings, fatal_error_code = null
after   : fatal_error_code = "PARSE_RESOURCE_LIMIT"
```

`src/pwa/floorplan/dxf_source.py` maps any worker `fatal_error_code` to a `FloorplanError`
with that code, and `PARSE_RESOURCE_LIMIT` is a failed-domain code, so the outcome is CLI 3
with that terminal finding. Note for the reviewer: the implementer's own test asserts the
CLI-3 end of that chain but reaches it with an in-process `DxfSource.extract` substitute, so
the cumulative trigger and the subprocess mapping are proven separately rather than in one
end-to-end run.

## GC3-6 — MAJOR — opaque DXF layout/layer names: CLOSED

PoC: a DXF carrying an unknown layer named `Alice-SecretClient-Layer` and an extra layout
named `Confidential-Sheet-1`, parsed to a finalized run, then all three artifacts scanned for
those strings.

```
pre-fix : layer name present in parse-report.json, floorplan_parse.json AND overlay.svg;
          layout name present in parse-report.json
          source refs: dxf:Confidential-Sheet-1/Alice-SecretClient-Layer#3C
after   : 0 occurrences of either name in any of the three artifacts
          source refs: dxf:unknown-layout-0001/unknown-layer-0001#3C
```

The project's own reserved vocabulary (`Model`, `PWA-*`) stays literal, which is correct — it
is not private data — and unknown names get deterministic encounter-order tokens that keep
distinct names distinct.

**Second disclosure.** The `f-hostile-label` row of the failure matrix previously asserted
that `&lt;script&gt;` appears in the overlay, proving XML escaping. It now asserts the
opposite plus the presence of an opaque token, because the hostile name no longer reaches the
overlay at all. That is a stronger privacy property but it retires the one test that
exercised the escaping path; escaping itself is untouched in `src/pwa/floorplan/overlay.py`.

## GC3-7 — MINOR — no exception escapes `parse_run()`: CLOSED, but see GC3-11

PoC without any monkeypatching: leave `runs/.staging` occupied by a **regular file**, so
creating the staging directory cannot succeed.

```
pre-fix : FileExistsError [WinError 183] ESCAPES parse_run()
after   : cli_exit 2, outcome "operational", no final run
```

The other two call sites named by the reviewer are settled by inspection: the preflight
`sha256_file()` call is gone entirely (see GC3-3 above) and `source_floorplan.stat()` is now
wrapped. Note that the implementer's own two GC3-7 tests both pass against the pre-fix tree —
`test_unreadable_source_input_returns_cli2_result_instead_of_raising` passes because the old
bare `except Exception` also caught it, and
`test_post_finalization_inventory_hash_drift_is_not_reported_complete` passes for an unrelated
reason (its own patched `os.replace` raises `StopIteration` on the pre-fix layout). Both fixes
are real, but the evidence for them is this section's PoC and the diff, not those two tests.

## GC3-11 — NEW, orchestrator-found regression introduced by this rework: CLOSED

`except Exception` was narrowed to
`except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError)`. Pillow's
`Image.DecompressionBombError` derives directly from `Exception`, so it stopped being caught.
It is raised by `Image.open()` above roughly 178 Mpixels — and both raster opens
(`AnnotationSource.extract()` and `_source_binding()`) run before `render_overlay()`'s
`MAX_SOURCE_PIXELS` check, so the guard that was supposed to catch an oversized raster cannot
be reached first. PoC: real `parse_run()` with an annotation source and `Image.MAX_IMAGE_PIXELS`
lowered so a small fixture reproduces the production condition.

```
before the rework      : cli_exit 2, outcome "operational_failure", nothing raised
after the rework       : DecompressionBombError ESCAPES parse_run()
after the follow-up fix: cli_exit 2, outcome "operational_failure", nothing raised
```

This is the same API-contract break GC3-7 exists to prevent, reintroduced through a different
exception class, so it was dispatched back to the same implementer as a bounded follow-up
rather than fixed by the orchestrator (the implementer must remain OpenAI under PLAN-002
section 17). The follow-up names both Pillow size-guard classes, adds input-driven
`RecursionError` and integer-string-conversion `ValueError` handling for JSON decoding,
requires decoded top-level documents to be objects, and adds four parametrised regression
tests (8 cases). `test_programming_error_is_not_hidden_as_operational_cli2` still passes, so
`RuntimeError`/`TypeError`/`AttributeError` still propagate as intended.

## Non-vacuity of the implementer's tests

Of the 15 tests added in the first round, **13 fail against the pre-fix tree** and 2 pass (both
named above under GC3-7). The 8 follow-up cases were verified through the orchestrator's own
before/after PoC rather than by replaying them against an intermediate tree.

## What this verification does NOT establish

- No G1 claim. PLAN-002 is not accepted.
- GC3-8 (PDF-page kind/role contract wording), GC3-9 (already-committed evidence paths) and
  GC3-10 (visual/geometry gate) are untouched and remain Moshe's.
- The independent cross-provider review of this rework has not run. Because the implementer is
  OpenAI, PLAN-002 section 17 makes the NA-3d reviewer **Anthropic** — the opposite of the
  route recorded in `next_actions.NA-3d`, which was written when the expected implementer was
  Anthropic.
- Race conditions (GC3-3) and the identity checks (GC3-4) rest on code reading plus the
  implementer's tests, not on orchestrator proofs-of-concept.
