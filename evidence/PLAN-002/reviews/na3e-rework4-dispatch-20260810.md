<!-- NA-3e dispatch brief: fourth bounded PLAN-002 rework, the NA-3d review findings.
     Authored by the orchestrator. Paths are repository-relative per PLAN-002 section 12 -
     no absolute paths, no OS account name. -->

# NA-3e — fourth bounded rework dispatch: the NA-3d findings

You are the PLAN-002 rework implementer. Fix exactly the seven defects below in this
repository, with tests, and write a report. Nothing else.

Read first, in this order:

1. `docs/plans/PLAN-002-floorplan-parsing.md` — the contract you must not break
   (sections 6, 7, 10, 12, the section 14 acceptance criteria, 17, 20).
2. `evidence/PLAN-002/reviews/independent-anthropic-rework3-review-opus-20260810.md` — the
   review that raised these findings. Its finding IDs F-1..F-8 are the IDs used below, and
   each one cites `file:line`. This is the governing review for the round.
3. `evidence/PLAN-002/reviews/orchestrator-verification-na3d-findings-20260810.md` — which
   findings the orchestrator reproduced with an executed proof-of-concept (F-1, F-3, F-7)
   and what the Windows path-aliasing experiment measured.
4. `evidence/PLAN-002/reviews/independent-anthropic-rework3-review-20260810.md` — the
   earlier pass of the same round. It said ACCEPT and is **superseded**; it was denied
   git-diff access. Read it only for its F1/F2 detail, which duplicate F-6 and F-1.

## Why this round exists

The previous round (NA-3b) closed seven gates and was then reviewed by an Anthropic Opus
reviewer with full diff access, which returned **NEEDS_REWORK**. Six gates are genuinely
closed. Two are not: **GC3-2 and GC3-3 are PARTIALLY_CLOSED**, in both cases because the
gate's literal text was satisfied while the invariant it exists to protect was not. F-1 and
F-2 below are those two unclosed halves; they are not new scope, they are the same gates.

Two further findings, F-3 and F-7, are a latent survival of the **GC-1 CRITICAL defect
class** — a path helper that trusts a component `pathlib` will treat as a new anchor —
inside the very helpers GC3-1 created. They are not currently reachable, and they are in
scope anyway; the reasoning is in the review and in the orchestrator's verification.

## Hard boundaries

- **No contract, schema, or error-code change.** `contracts/error_codes.md` is append-only
  and must not need appending: every failure below is either an existing code or an
  operational `cli_exit == 2` result with no code. Schemas under `schemas/` are frozen —
  ADR-0005 permits additive versions only and none is authorised here.
- **No new dependency.** `pyproject.toml` and `uv.lock` byte-identical when you finish.
- **No new key in `limits_snapshot()`.** That dictionary is written into
  `parse/parse-report.json`, so it is contract-visible. If a fix seems to need a new limit
  constant that would surface there, **stop and report** instead of adding it; reuse an
  existing limit or bound the read without publishing a new limit name.
- **Do not touch GC3-8, GC3-9 or GC3-10.** Leave
  `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}` exactly as it is — GC3-8's contract
  amendment is being drafted and reviewed separately and is NOT part of this round. Do not
  rewrite or redact any existing file under `evidence/`.
- **Do not rewrite approved documents in place.** `docs/plans/PLAN-002-floorplan-parsing.md`
  and everything under `evidence/` are append-only records.
- **The golden canonical-projection hash must not move:**
  `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`
  (`tests/golden/test_floorplan_golden.py`). If a change moves it, stop and report rather
  than updating the expected value.
- **`parse_run()` must never raise.** GC3-7 is closed and must stay closed; several fixes
  below touch its failure paths. Every new failure mode returns `cli_exit == 2` with a
  diagnostic, or an existing failed-domain code with `cli_exit == 3`.
- **Section 12 for new evidence:** repository-relative paths only, no OS account name.
- **Baseline to preserve: 338 passed, exit 0** (repository `.venv`, CPython 3.11, inherited
  `PYTHONPATH` cleared). A green suite has coexisted with a live CRITICAL in four
  consecutive rounds of this plan, so a green suite is a floor, not evidence.
- Work test-first where the defect is observable. **Every fix must leave at least one test
  that fails if the fix is reverted**, and you must state in your report which test that is.
- If a fix cannot be made inside these boundaries, **stop and escalate in your report**.
  Do not widen scope and do not silently defer; a quantified deferral was rejected in an
  earlier round of this plan.

## The seven fixes

### F-1 (MAJOR) — a failed finalisation must not leave a published run

`src/pwa/floorplan/runs.py:213-223`. `finalize_run` verifies the inventory, calls
`os.replace(staging_run, final_run)`, then verifies again. When that second verification
raises, the run has already been published: the caller receives `cli_exit == 2` from
`src/pwa/floorplan/builder.py:1069-1076`, while a complete run directory sits in
`runs_root` whose own `parse/parse-report.json` reads `"outcome": "complete"` and
`"cli_exit": 0`, and `builder.py:450` silently skips writing the failure report because
`staging_run` no longer exists.

Confirmed by an executed probe, verbatim: `cli_exit = 2`, `final_run.exists() = True`,
`staging_run.exists() = False`, 15 files in the finalized run, on-disk
`parse-report.outcome = 'complete'`, `parse-report.cli_exit = 0`.

**Required shape** (chosen by the orchestrator so the round is not open-ended): on a
post-rename verification failure, **rename the directory back to staging** with
`os.replace(final_run, staging_run)` and then return the operational failure. That restores
the invariant the neighbouring test
`tests/integration/test_plan002_failure_matrix.py` / `test_plan002_parse_run.py:194`
(`test_operational_failure_retains_staging_and_no_finalized_run`) already asserts for every
other operational failure — staging retained, no finalized run — and it needs no new
artifact name, no new code and no contract change. If the rename-back itself fails, you
still may not raise: return `cli_exit == 2` and make the returned diagnostic say plainly
that a finalized directory was left behind, so the caller is not told a comfortable lie.

Do **not** simply delete the finalized directory: an operational failure keeps its evidence
in this plan.

Test to add: post-rename drift asserts all four of `cli_exit == 2`,
`diagnostic["outcome"] == "operational_failure"`, `not result.final_run.exists()`, and
`result.staging_run.is_dir()`. Note that the existing test at
`tests/integration/test_plan002_parse_run.py:169-191` asserts only the first two — that is
how this defect survived. Strengthen it rather than adding a near-duplicate.

### F-2 (MAJOR) — one immutable snapshot of the annotation raster, not three reads

`src/pwa/floorplan/annotation_source.py:60,64` and `src/pwa/floorplan/builder.py:317`. The
staged raster is read three times: `sha256_file()` (the only integrity-checked read),
`Image.open()` for the dimension check, and `_source_binding`'s own `read_bytes()`, whose
bytes are the ones sanitized into `parse/overlay.svg` and hashed into `source_sha256`. The
hash-verified bytes are therefore neither the dimension-checked bytes nor the embedded
bytes. GC3-3's defect moved from the source run into staging; it was not eliminated.

**Required shape:** mirror the pattern this rework already established for the annotation
JSON. GC3-3's fix added a `document=` parameter so the parsed JSON and the staged JSON come
from one byte snapshot; do the same for the raster with an explicit bytes snapshot — read
the staged raster **once**, hash those bytes, compare to both the annotation's declared
`sha256` and the inventory entry, validate the dimensions from `Image.open(BytesIO(...))`
on those same bytes, and pass the same bytes to `_source_binding` for sanitisation and
embedding. One read, one digest, one set of pixels.

Read the note in the review about the DXF path: `DxfSource` parses in a subprocess that
re-opens the path, so a single snapshot is not achievable there without changing the worker
interface. **That is out of scope here** — record it in your report as a known residue, do
not change the worker's interface in this round.

### F-3 + F-7 (MAJOR latent + MINOR) — two lines in the containment primitives

`src/pwa/floorplan/runs.py:12-17` and `:20-36`.

`_contained_parts` rejects a component equal to `""`, `"."` or `".."` and rejects absolute
paths. It does not reject a component carrying a Windows drive letter, because
`PureWindowsPath("C:sub")` is **not** absolute: its parts are `('C:', 'sub')`. Joining that
onto a root whose drive differs discards the root entirely. Nor does it reject a component
containing `:` at all, which on NTFS names an alternate data stream.

The orchestrator proved both through the real helpers. Verbatim, root `X:/f4lab3`, value
`C:pwa_escape/owned.txt`:

```
validate_contained_destination  -> ACCEPTED, leaf = C:pwa_escape\owned.txt   (under root? False)
resolve_contained_output        -> ACCEPTED
write_bytes_contained           -> WROTE, outside the root
create_contained_directory      -> CREATED a directory outside the root
resolve_contained_relpath       -> ValueError: path escapes containment root   <- read side is safe
```

and for the stream form, against an existing 16-byte `artifact.dxf`: the write succeeded,
the host file's bytes and size were unchanged, `os.listdir` did not show the stream, and
`sha256_file` of the host was unchanged.

The asymmetry is the finding: `resolve_contained_relpath` is the only member of the family
that ends with an independent `resolved.relative_to(root_resolved)` check
(`runs.py:168-177`). The four write-side helpers have the lexical walk and nothing else.

**Required shape, two changes:**
1. In `_contained_parts`, reject any component containing `:`. This closes the
   drive-relative escape and the ADS channel together.
2. Give `validate_contained_destination` the same closing `resolve()` /
   `relative_to(root)` check its read-side sibling already has, so the primitive contains
   even if a future caller passes something the grammar did not anticipate.

Note that the hazard is already documented **in this codebase**, by the previous
implementer, at `src/pwa/floorplan/builder.py:50-54`, and was applied to `parse_run_id` via
`_PARSE_RUN_ID_RE` (which correctly excludes `:`) but not to the shared primitive.

Tests to add: one per mechanism in `tests/integration/test_plan002_failure_matrix.py` — a
drive-relative inventory path and an ADS inventory path, each rejected. Assert on the
rejection, not on an incidental exception type.

### F-4 (MINOR) — staged writes must not re-create their parent with `exist_ok=True`

`src/pwa/floorplan/builder.py:1023` and the identical blocks at `:814-818`, `:848-852`,
`:867-871`, `:1046-1050`, plus `write_json_exclusive` and `copy_immutable` in
`src/pwa/files.py`, all call `path.parent.mkdir(parents=True, exist_ok=True)`. Those
parents were already created and reparse-checked by `create_contained_directory`
(`builder.py:766-768`); re-creating them with `exist_ok=True` succeeds silently against a
junction planted mid-run, and `O_EXCL` on the leaf does nothing about a redirected parent.

**Required shape:** the staged write sites must not create parents. Route them through the
checked helpers, or assert the parent is an existing non-reparse directory before opening
the leaf. `src/pwa/files.py` is shared with PLAN-001 intake — if you change the helper's
behaviour there, keep PLAN-001's call sites working and say so in your report; the safer
route is to stop relying on the implicit `mkdir` from the floorplan side rather than to
change the shared helper's contract.

### F-5 (MINOR) — finalisation must verify the derived artifacts, not only the inputs

`src/pwa/floorplan/runs.py:206-210`. Both inventory verifications iterate only
`manifest["payload"]["inputs"]`. Nothing re-checks `parse/overlay.svg`,
`parse/floorplan_parse.json`, `parse/assumptions.json`, `parse/parse-report.json`,
`parse/annotation.json` or the four `project/*.json` envelopes, and no envelope's
`content_hash` is recomputed at finalisation even though `floorplan_parse.json` carries the
overlay's declared `sha256` (`builder.py:913`).

**Required shape:** extend the finalisation check to cover the derived files that the run
itself declares — at minimum recompute the overlay hash against its declaration in
`floorplan_parse.json`, and re-validate each written envelope's `content_hash` against its
payload using the existing `pwa.contracts` helpers. Use what the artifacts already declare;
do not invent a new manifest of derived hashes, which would be contract surface.

### F-6 (MINOR) — bound the annotation read

`src/pwa/floorplan/builder.py:684,695`. `Path(annotation).read_bytes()` materialises the
whole file, and `MAX_ANNOTATION_BYTES` is only checked afterwards, so the cap bounds what is
processed and never what is read. The reachable failure is `MemoryError`, which is **not**
in the handler tuple at `:1069-1076` and would escape `parse_run()` — breaking GC3-7.

**Required shape:** read at most `MAX_ANNOTATION_BYTES + 1` bytes and treat the overflow as
the existing `PARSE_RESOURCE_LIMIT` case. No new limit key.

### F-8 (MINOR) — check `source_image_ref` for containment before opening it

`src/pwa/floorplan/annotation_source.py:59`. `image_ref` comes from the annotation payload
and is joined onto `source_root` with no containment check of its own; the only guard is the
membership test against `source_inventory`. `builder.py:794-797` does call
`resolve_contained_relpath` on that value — but **after** `extract()` has returned, i.e.
after both `sha256_file` and `Image.open` have opened the unchecked path. Correct today,
backwards, and dependent on a caller two files away. `source_inventory=None` remains a
supported call shape with no gate at all.

**Required shape:** resolve the value through the containment helper inside `extract()`,
before the first open. Keep the caller's check too — defence in depth is not a duplication
worth removing.

## Two test gaps to close in the same round

These are not defects; they are coverage the previous round's disclosures admitted losing.

1. **Overlay XML escaping is now untested.** Disclosure 2 flipped the `f-hostile-label`
   assertion to prove tokenisation, which retired the only test exercising escaping in
   `src/pwa/floorplan/overlay.py`. Escaping is still required — tokenisation covers DXF
   layout and layer names, not every string that can reach the overlay. Add one direct unit
   test on the escaping path so both properties are pinned.
2. **GC3-5 has no end-to-end test through the real worker.** Disclosure 3 admits the
   cumulative entity cap is proven in two halves that no single test spans. Add one test
   that goes through the real `dxf_worker` subprocess and asserts `PARSE_RESOURCE_LIMIT`
   with `cli_exit == 3`.

## What to deliver

1. The code and tests, committed to nothing — **do not commit**. The orchestrator commits.
2. `evidence/PLAN-002/reviews/rework4-report-20260810.md`, containing per fix: the defect,
   the change, the test that fails if the change is reverted, and anything you could not do.
3. The full suite result, and confirmation that `pyproject.toml`, `uv.lock`, `schemas/`,
   `contracts/` and `docs/` are unchanged.
4. Runtime metadata read from your session rollout, not from self-description: CLI version,
   model id, sandbox mode, reasoning effort, session id.

Report honestly. Four review rounds of this plan have each found real defects behind a green
suite, and the round that reported "all closed" most confidently is the one that introduced
a regression. A finding you surface yourself costs the project far less than one the next
reviewer finds.
