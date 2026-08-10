<!-- Orchestrator independent verification of the NA-3 cross-provider review.
     Reviews are never accepted on report in this project; the two most
     consequential findings were reproduced before the review was recorded as
     authoritative. Paths below are redacted per PLAN-002 section 12. -->

# NA-3 — orchestrator verification of the OpenAI round-3 review, 2026-08-10

Reviewed artifact: `evidence/PLAN-002/reviews/independent-openai-rework2-review-20260810.md`
(verdict `NEEDS_REWORK`; 1 CRITICAL, 6 MAJOR, 1 MINOR, 2 INFO, plus 3 checklist items
downgraded from CLOSED to PARTIALLY_CLOSED).

## Baseline re-established first

- Full suite in the worktree, inherited `PYTHONPATH` cleared, repository `.venv` CPython 3.11:
  **316 passed, 0 failures, 0 errors, 0 skipped, exit 0.**
- One deprecation warning only (`PIL.Image.getdata`, already recorded as a non-urgent
  follow-up under GC-7 in `PROJECT-STATE.yaml`).

The suite was green while both reproduced defects below were live. That is the third
consecutive round in which a fully green suite coexisted with a real defect, and it is the
reason acceptance in this plan rests on adversarial review rather than on test count.

## Route change from the NA-3 plan, and why

`next_actions.NA-3` specified re-packaging the implementation and sending it to
`gpt-5.6-sol` through the OmniRoute local gateway as a chat request. That route was not
used. The Codex CLI — recorded as unavailable on 2026-08-10 and the stated reason for the
Sonnet 5 implementer fallback — is in fact installed (`codex-cli 0.144.6`), authenticated,
and configured for `gpt-5.6-sol` at `xhigh`. The review therefore ran as
`codex exec --sandbox read-only --disable hooks` **inside the worktree**, giving the
reviewer direct read-only access to every file.

This removes the specific defect NA-3 existed to correct. Round 2 returned `CANNOT_VERIFY`
for code findings M-8 and M-9 and could not assess `src/pwa/files.py`, purely because the
orchestrator's hand-assembled package omitted three files. With filesystem access there is
no package and no omission: **M-8 and M-9 both reached a verdict (CLOSED) this round, and
`files.py` was assessed.** It also cost nothing in independence — the reviewer is still a
different provider from the rework author, and it was sandboxed read-only so it could not
alter what it judged.

Model identity was taken from the Codex session rollout
(`turn_context.model = "gpt-5.6-sol"`, `effort = "xhigh"`), not from the reviewer's
self-report, following the `plan-002-implementer` silent-substitution precedent. Hooks were
disabled so no persona hook could bias the reviewer's disposition.

## Finding 1 — C-NA3-1 (CRITICAL): REPRODUCED

Claim: a junction at `runs_root/.staging` lets `parse_run()` create directories and copy
source inventory outside `runs_root`, because `.staging` is never checked for reparse-ness
and the containment proof is the lexical `relative_to()` pair on `final_run`/`staging_run`.

A proof-of-concept was written and executed against the real `parse_run()`. It builds a
valid source run with `ingest_project()`, makes `runs/.staging` a junction
(`mklink /J`) to a directory outside `runs_root`, and calls `parse_run()` with a
well-formed `parse_run_id` that passes the GC-1 grammar.

Result, case A (annotation rejected after staging — stale `content_hash`):

```
cli_exit               = 2
staging_run (reported) = <runs_root>\.staging\RUN-POC-001
final_run exists       = False
files written OUTSIDE runs_root: 5
    RUN-POC-001/parse/parse-report.json
    RUN-POC-001/project/project/inputs/originals/floorplan.png
    RUN-POC-001/project/project/inputs/originals/style_reference.png
    RUN-POC-001/project/source-manifest.json
    RUN-POC-001/project/source-quality-report.json
```

Result, case B (otherwise-valid run): `cli_exit = 0`, and **no residue** outside
`runs_root` — because `finalize_run()`'s `os.replace()` moves the staging directory back
in. The write still happened outside during the run; only the evidence of it is moved
away afterwards.

**Confirmed.** Copies of the caller's real source inputs are written to an
attacker-chosen location outside the configured run boundary, and on the failure path they
stay there. GC-1 closed the *run-id* half of the destination problem; the *ancestor* half
was never closed. AC-17 is not met.

## Finding 2 — M-NA3-1 (MAJOR): REPRODUCED

Claim: `copy_source_inventory()` resolves inventory destinations against
`staging_run / "project"` while `item["path"]` already carries the `project/` prefix, so
every copied input lands one level too deep and the derived manifest points at a path that
does not exist.

Verified two ways.

By reading: `src/pwa/intake.py:207-211` builds `inputs[].path` as
`floor_copy.relative_to(run_root)`, and `floor_copy` is
`run_root/"project"/"inputs"/"originals"/...` (`intake.py:162-164`), so the declared path
starts with `project/`. `src/pwa/floorplan/runs.py:114-117` then joins that same value
under `staging_run/"project"`. The source side (`runs.py:116`) resolves against
`source_run` and is correct; only the destination side is doubled.

By execution: `tests/integration/test_plan002_parse_run.py::test_parse_run_finalizes_complete_derived_run`
was run with a retained `--basetemp`, and the finalized run inspected.

```
<final_run>/project/project/inputs/originals/floorplan.png        <- actually on disk
<final_run>/project/project/inputs/originals/style_reference.png  <- actually on disk

project_manifest.payload.inputs[0].path = project/inputs/originals/floorplan.png        -> exists=False
project_manifest.payload.inputs[1].path = project/inputs/originals/style_reference.png  -> exists=False
```

**Confirmed.** A run that reports `complete` with `cli_exit == 0` and passes schema
validation is not self-contained: both declared inventory paths resolve to nothing. Every
prior round — two Anthropic reviews and one OpenAI review — missed this, because none of
them could look at a finalized run on disk. AC-13 is not met.

## Finding 3 — M-NA3-5 (MAJOR): CONFIRMED BY INSPECTION

`src/pwa/floorplan/dxf_worker.py:143-147` enforces `MAX_DXF_ENTITIES` against
`len(modelspace)` only. The loop at `:169-182` then scans every other layout and merely
accumulates `scanned_entities`; no cumulative bound is applied before or during that scan.
The reviewer's paperspace-overflow scenario follows directly from the code. Not executed —
inspection was decisive.

## Finding 4 — M-NA3-4 (MAJOR, second half): CONFIRMED

The claim that absolute paths and the OS user name are *already present in tracked
evidence* holds and is broader than the two files the reviewer cited: a scan of
`evidence/**` finds **53 occurrences across 29 files**, most of them legacy PLAN-000 and
PLAN-001 `coverage.xml` and `command.log` artifacts, plus three PLAN-002 review/report
files. This is a live PLAN-002 section 12 violation in the repository as it stands, and it
predates PLAN-002. The first half of the finding (free-text DXF layer/layout names reaching
overlays and parse reports) was not separately reproduced.

## Not verified

Everything else in the review is recorded as reviewer-asserted and **not** independently
confirmed by the orchestrator: M-NA3-2 (snapshot/lineage races), M-NA3-3 (PDF-page
capability), M-NA3-6 (source-run finality, cross-project manifest/quality pairing, multiple
`kind=floorplan`), N-NA3-1, I-NA3-1, I-NA3-2, the three downgrades to PARTIALLY_CLOSED
(GC-4, GC-5, GC-7, B, E, `copy_immutable`/`is_link_or_reparse`), and the per-AC verdict
table. They carry the reviewer's file:line citations and should be re-verified as part of
whichever rework dispatch takes them on, not treated as established here.

Two of the review's own conclusions were checked and **held**: GC-6 is genuinely closed —
the projection is computed after wall resolution against the matched wall's unit direction
(`normalize.py:156-183`, `:298-313`), with the degenerate case failing closed at `:314` —
and the GC-1 run-id grammar itself (`builder.py:53-57`, `:445`) does reject every separator,
anchor and drive form before a path is built.
