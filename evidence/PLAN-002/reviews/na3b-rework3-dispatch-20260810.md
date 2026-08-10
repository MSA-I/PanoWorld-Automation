<!-- NA-3b dispatch brief: third bounded PLAN-002 rework, gate conditions GC3-1..GC3-7.
     Authored by the orchestrator. Paths in this file are repository-relative per
     PLAN-002 section 12 - no absolute paths, no OS account name. -->

# NA-3b — third bounded rework dispatch: GC3-1..GC3-7

You are the PLAN-002 rework implementer. Fix exactly the seven bounded defects below in
this repository, with tests, and write a report. Nothing else.

Read first, in this order:

1. `docs/plans/PLAN-002-floorplan-parsing.md` — the contract you must not break
   (sections 6, 7, 10, 12, 14 acceptance criteria, 17, 20).
2. `evidence/PLAN-002/reviews/independent-openai-rework2-review-20260810.md` — the review
   that raised these findings (written in Hebrew; the code citations are the point).
3. `evidence/PLAN-002/reviews/orchestrator-verification-na3-20260810.md` — which of them
   were reproduced with a proof-of-concept and which are still only reviewer-asserted.
4. `PROJECT-STATE.yaml`, `current_plan.open_gate_conditions_round3` — the authoritative
   text of GC3-1..GC3-7.

## Hard boundaries

- **No contract, schema, or error-code change.** `contracts/error_codes.md` is append-only
  and must not need appending: every failure below maps to an existing code
  (`PARSE_RESOURCE_LIMIT`, `PARSE_SOURCE_HASH_MISMATCH`, `PARSE_SOURCE_UNSUPPORTED`,
  `PARSE_UNSUPPORTED_FEATURE`) or to an operational `cli_exit == 2` result with no code.
  Schemas under `schemas/` are frozen — ADR-0005 allows additive versions only, and none is
  authorised here.
- **No new dependency.** `pyproject.toml` and `uv.lock` must be byte-identical when you
  finish. Everything below is achievable with the standard library, `ezdxf` and `Pillow`,
  all already locked.
- **Do not touch GC3-8, GC3-9 or GC3-10.** GC3-8 (PDF-page `kind`/role) and GC3-9 (paths
  and OS account name already committed in tracked evidence) are reserved human gates that
  Moshe has routed but whose wording is not yet approved. GC3-10 is a visual gate. In
  particular: leave `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}` exactly as it is,
  and do not rewrite or redact any existing file under `evidence/`.
- **Do not rewrite approved documents in place.** `docs/plans/PLAN-002-floorplan-parsing.md`
  and everything already under `evidence/` are append-only records. A previous session was
  found to have rewritten an approved design brief in place; do not repeat it.
- **The golden canonical-projection hash must not move:**
  `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`
  (`tests/golden/test_floorplan_golden.py`). `canonical_projection()`
  (`src/pwa/floorplan/normalize.py:404-413`) covers units, rooms, walls and openings only —
  provenance and source refs are outside it, so GC3-6 cannot legitimately change this hash.
  If any change you make moves it, stop and report instead of updating the expected value.
- **New evidence must comply with section 12:** no absolute paths, no OS account name in
  anything you write. Repository-relative paths only.
- **Baseline to preserve:** the full suite is green at **316 passed, exit 0** before you
  start (repository `.venv`, CPython 3.11, inherited `PYTHONPATH` cleared). Every one of
  those tests must still pass. Note that a green suite has coexisted with a real defect in
  three consecutive review rounds here, so a green suite is a floor, not evidence.
- Work test-first where the defect is observable: add the failing test, watch it fail for
  the right reason, then fix. Every one of the seven fixes must leave behind at least one
  test that fails if the fix is reverted.
- If a fix cannot be made without crossing one of these boundaries, **stop and escalate in
  your report** rather than widening scope or silently deferring. A deferral with quantified
  reasoning was rejected by the previous review round; do not assume one will be accepted.

## The seven fixes

### GC3-1 — CRITICAL — destination ancestor containment (reproduced)

`src/pwa/floorplan/builder.py:481-513`, `:706-710`; `src/pwa/floorplan/runs.py:62-110`.

`staging_run = runs_root / ".staging" / parse_run_id` is proven contained only by the
lexical `relative_to()` pair, then created with `staging_run.mkdir(parents=True)`. Nothing
ever inspects `.staging` itself for reparse-ness. A junction at `runs/.staging` pointing
outside `runs_root` therefore causes `mkdir()` and `copy_source_inventory()` to write
outside the run boundary; on the failure path the files stay there. The orchestrator
reproduced this: five files, including copies of the caller's floorplan and style images,
written outside `runs_root` and left there at `cli_exit == 2`.

Required: prove containment for the **whole destination ancestor chain** — `runs_root`,
`.staging`, the staging run directory, and every intermediate directory created underneath
it — rejecting any symlink/reparse point at any level, before anything is created or
written. `final_run`'s chain needs the same treatment. `is_link_or_reparse()`
(`src/pwa/files.py:11-16`) already exists and is correct; `resolve_contained_run()` and
`resolve_contained_relpath()` (`src/pwa/floorplan/runs.py`) already do exactly this walk
for the **source** side — the destination side needs the equivalent. Note the wrinkle the
reviewer identified: `resolve_contained_relpath()` skips the reparse check on a root that
does not exist yet, which is precisely the destination case, so a not-yet-existing root
must have its own existing ancestors checked instead of being trusted. Rejection is an
operational failure: return `ParseRunResult(cli_exit=2, ...)`, create nothing.

### GC3-2 — MAJOR — inventory copy root, plus a post-finalization check (reproduced)

`src/pwa/floorplan/runs.py:113-128`; declared paths built at `src/pwa/intake.py:207-211`.

`copy_source_inventory()` resolves destinations under `staging_run / "project"`, but
`item["path"]` already begins with `project/`, so every input lands at
`project/project/...` while the derived manifest keeps declaring `project/...`. A run that
reports `complete` at `cli_exit == 0` is therefore not self-contained: both declared paths
resolve to nothing. Reproduced by running
`tests/integration/test_plan002_parse_run.py::test_parse_run_finalizes_complete_derived_run`
with a retained basetemp and inspecting the finalized run.

Required: resolve inventory destinations against `staging_run`, not `staging_run/"project"`.
Then add a post-finalization verification that opens **every** path declared in the derived
`project_manifest.payload.inputs[]` inside the finalized run and checks its SHA-256 against
the declared `sha256`. A mismatch or a missing file must not finalize silently. Keep the
existing preflight-versus-copy hash reverification at `runs.py:127-128`.

### GC3-3 — MAJOR — one immutable snapshot per input (reviewer-asserted; re-verify)

`src/pwa/floorplan/builder.py:313-331`, `:661-681`, `:708-716`, `:745-756`, `:873-881`;
`src/pwa/floorplan/annotation_source.py:37-47`.

Each input is read more than once:

- the annotation is read and schema-validated at preflight, read again inside
  `AnnotationSource.extract()`, and copied third — while `floorplan_parse.inputs[]` binds
  the artifact ID and hash taken from the **first** read;
- the DXF is stat'd and accepted at preflight, copied into staging, then parsed from the
  **original** source run rather than from the copy;
- for a raster, `_source_binding()` opens the path for pixels and separately calls
  `sha256_file()` on the same path, so the embedded pixels and the bound hash can come from
  different bytes.

A file swapped in between two reads is therefore parsed under a lineage that describes
different bytes, and the run can still finalize `complete`.

Required: read each input exactly once into a verified immutable snapshot, and do
validation, hashing, parsing, copying and sanitisation from those same bytes. The natural
shape here — and what the reviewer asked for — is to copy into staging first (which already
reverifies the hash against the manifest declaration), then parse only the staged copy. For
the raster, derive both the original-bytes hash and the sanitised pixels from one read. Do
not weaken GC-7: the hash bound into the overlay is still the hash of the **original**
verified bytes, never of the sanitised re-encode
(`src/pwa/floorplan/builder.py:325-331`).

### GC3-4 — MAJOR — source-run finality and identity (reviewer-asserted; re-verify)

`src/pwa/floorplan/runs.py:11-59`; `src/pwa/floorplan/builder.py:539-611`.

Four missing preflight checks, all reachable with a schema-valid input:

1. `resolve_contained_run()` accepts any existing directory nested anywhere under
   `runs_root`, including a copy under `runs_root/.staging/...`. Require a **direct child**
   of `runs_root` that is not a staging or otherwise reserved dot-directory — PLAN-002
   requires parsing a finalized source run.
2. The manifest and the quality report are validated independently, so a manifest from
   project A can be paired with a quality report from project B. Require them to agree on
   `project_id` and `run_id`, and require that `run_id` to match the source run directory.
3. `floorplan_entry = next(... if item["kind"] == "floorplan")` silently takes the first of
   several. Require **exactly one** `kind == "floorplan"` inventory entry.
4. Require inventory `path` values to be unique.

Each violation is an operational preflight failure: `cli_exit == 2`, no staging created, no
final run.

### GC3-5 — MAJOR — cumulative DXF entity cap (confirmed by inspection)

`src/pwa/floorplan/dxf_worker.py:143-147`, `:169-182`.

`MAX_DXF_ENTITIES` is checked against `len(modelspace)` only. Every other layout is then
scanned with no cumulative bound, so 200,001 LINEs in paperspace pass the cap and produce
an unsupported/timeout/truncation outcome instead of the declared resource limit.

Required: enforce the cap cumulatively across modelspace and every other layout, stop
exactly at the overflow, and map it to `PARSE_RESOURCE_LIMIT` — which the worker signals as
`raise ValueError("PARSE_RESOURCE_LIMIT")` (`dxf_worker.py:146-147`, surfaced through
`src/pwa/floorplan/dxf_source.py`) and which must reach the caller as `cli_exit == 3` with
that code, matching the existing failure-matrix rows.

### GC3-6 — MAJOR — no free-text DXF layout/layer names in artifacts

`src/pwa/floorplan/dxf_worker.py:37-42`, `:61-81`; reaching overlay labels via
`src/pwa/floorplan/builder.py:359-364` and the parse report via `:918-926`;
`src/pwa/floorplan/overlay.py:57-64`.

`source_ref = f"dxf:{layout.name}/{layer}#{handle}"` and messages such as
`ignored unmapped entity on layer {layer}` carry attacker- or client-controlled free text
into `parse-report.json` and the overlay legend. XML escaping prevents injection but not
disclosure; PLAN-002 section 12 forbids the disclosure.

Required: emit opaque or redacted source refs and messages. The project's own reserved
vocabulary is not private data and may stay literal — `Model` for the layout and the
`_KNOWN_LAYERS` set `{PWA-WALL, PWA-ROOM, PWA-DOOR, PWA-WINDOW, PWA-DIM}`
(`dxf_worker.py:16`). Anything outside that vocabulary must be replaced by a deterministic
opaque token that is stable within a run, reveals nothing about the original string, and
keeps distinct names distinct so findings remain individually attributable. The DXF
`handle` is a document-internal hex id, not free text, and may stay. Remember that
`geometry.*.provenance` values flow into `floorplan_parse.json`, so check every path a
`source_ref` can reach — artifact, report and overlay alike.

### GC3-7 — MINOR — no exception may escape `parse_run()`

`src/pwa/floorplan/builder.py:585-599`, `:683-706`; `src/pwa/floorplan/cli.py:18-31`.

`sha256_file(input_path)`, `source_floorplan.stat()` and `staging_run.mkdir()` can raise
`OSError` (an unreadable-but-present inventory file, an ACL denial, a racing directory
creation) from outside any handler. `cli.main()`'s broad guard hides this from the CLI, but
`parse_run()`'s documented API contract — always a `ParseRunResult`, `cli_exit == 2` for
operational failures — is broken.

Required: every preflight and staging filesystem operation returns a consistent
`cli_exit == 2` diagnostic result instead of raising. Do not paper over it with a bare
`except Exception` around the whole function: keep the diagnostic shape the existing
`_diagnostic()` helper produces, and keep genuine programming errors distinguishable.

## Deliverables

1. The code fixes, in `src/`.
2. Tests, in `tests/`, that fail if any individual fix is reverted. Include at least: a
   junction-based destination-containment test for GC3-1 (the suite already builds real
   Windows junctions — see the existing reparse-point tests for the pattern); a
   post-finalization declared-path/hash assertion for GC3-2; a swap-between-reads test for
   GC3-3; one test per missing check in GC3-4; a cumulative paperspace-overflow test for
   GC3-5 asserting `PARSE_RESOURCE_LIMIT` and `cli_exit == 3`; a test asserting no unknown
   layer or layout name appears anywhere in `parse-report.json`, `floorplan_parse.json` or
   `overlay.svg` for GC3-6; and an unreadable-input test for GC3-7 asserting a returned
   result rather than a raised exception.
3. `evidence/PLAN-002/reviews/rework3-report-20260810.md` — one section per gate condition:
   what you changed, which test proves it, and the exact command output for the full suite
   (test count and exit code). State explicitly whether the golden canonical-projection hash
   moved. List anything you had to escalate, and anything you noticed but deliberately left
   alone as out of scope.
4. Do not commit. Leave the working tree dirty for the orchestrator to inspect, verify
   independently, and commit.

Report honestly. Every claim in your report will be re-verified against the filesystem by
the orchestrator and then attacked by an independent cross-provider reviewer; three previous
rounds each found real defects behind a green suite, and one found an undeclared model
substitution. An accurate "I could not close this" is worth more than an optimistic "closed".
