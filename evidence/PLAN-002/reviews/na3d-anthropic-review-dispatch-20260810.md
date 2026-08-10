# NA-3d dispatch brief — fourth independent cross-provider review of PLAN-002

- Task: `NA-3d` (`next_actions` in `PROJECT-STATE.yaml`)
- Reviewer provider: **Anthropic** (required — see "Why Anthropic" below)
- Subject: branch `panoworld-dev/na-3b-gc3-fixes`, commit `6eaef17`
- Access: real read-only filesystem access to the repository. Nothing is packaged for you;
  read whatever you judge relevant.
- Output: a single review document, written to stdout, captured verbatim by the orchestrator
  into `evidence/PLAN-002/reviews/independent-anthropic-rework3-review-20260810.md`.
- Language: **English.** The NA-3 reviewer answered in Hebrew and that was recorded as a
  deviation; do not repeat it.

## Why Anthropic

PLAN-002 section 17, row 3, states the sequence literally: "OpenAI Codex implementer, then
Anthropic code/spatial reviewer". The third bounded rework (NA-3b) was implemented by OpenAI
`gpt-5.6-sol` at xhigh through the Codex CLI. Reviewing OpenAI's code with OpenAI would
destroy the opposite-provider property this gate exists for. The `next_actions.NA-3d` entry
previously said "same route as NA-3 (Codex CLI)"; that wording was written when the
implementer was assumed to be Anthropic and has been corrected in `PROJECT-STATE.yaml`.

## Required first step (section 17)

Invoke `/skills` and use the skills relevant to this review before you start. Section 17 makes
the absence of this instruction a dispatch failure; ignoring the instruction is equally a
failure.

## What is under review

The seven bounded fixes GC3-1..GC3-7 from the NA-3 review, plus GC3-11, a regression the
rework itself introduced and then closed. Full text of all eleven gate conditions is in
`PROJECT-STATE.yaml` under `current_plan.open_gate_conditions_round3`.

Read these three, in this order:

1. `evidence/PLAN-002/reviews/na3b-rework3-dispatch-20260810.md` — what the implementer was told to do.
2. `evidence/PLAN-002/reviews/rework3-report-20260810.md` — what the implementer says it did.
3. `evidence/PLAN-002/reviews/orchestrator-verification-na3b-20260810.md` — what the orchestrator independently proved.

Then read the code. The changed files are:

- `src/pwa/floorplan/runs.py` (containment helpers, inventory copy root, `verify_run_inventory`, `finalize_run` signature)
- `src/pwa/floorplan/builder.py` (single-snapshot reads, guarded directory creation, identity checks, the `parse_run()` exception handler)
- `src/pwa/floorplan/dxf_worker.py` (cumulative entity cap, opaque layout/layer tokens)
- `src/pwa/floorplan/annotation_source.py` (`extract(..., document=...)`)
- `tests/integration/test_plan002_parse_run.py`, `tests/integration/test_plan002_failure_matrix.py`,
  `tests/unit/test_floorplan_builder.py`, `tests/unit/test_floorplan_sources.py`

`git show --stat 6eaef17` and `git diff 11ef553 6eaef17 -- <path>` give you the exact diff.

## Your mandate

1. **Do not trust either report.** Both the implementer's report and the orchestrator's
   verification are evidence to be challenged, not findings to be adopted. If a claim in
   either document does not survive contact with the code, say so — that is the most valuable
   thing you can produce here.
2. **Per gate, state CLOSED / PARTIALLY_CLOSED / NOT_CLOSED** for GC3-1..GC3-7 and GC3-11,
   with the file:line you based it on.
3. **Concentrate on GC3-3 and GC3-4.** These two have no orchestrator proof-of-concept behind
   them — they rest on code reading plus implementer tests that fail if the fix is reverted.
   GC3-3 is "one immutable snapshot per untrusted input" (the TOCTOU between reading for
   parsing, for copying and for hashing). GC3-4 is source-run finality and cross-artifact
   identity. Assume they are the weakest links and try to break them.
4. **Hunt for new defects the rework introduced.** This is not hypothetical: narrowing the
   GC3-7 handler from `except Exception` to a named list let `PIL.Image.DecompressionBombError`
   — which derives from `Exception`, not `OSError` — escape `parse_run()` at both raster open
   sites. The orchestrator found that (GC3-11) and it was fixed. The same class of mistake may
   exist elsewhere in this diff. Places worth attacking: the `parse_run()` handler's current
   exception tuple against everything Pillow, `json`, `ezdxf` and the subprocess layer can
   raise; the new `create_contained_directory` / `resolve_contained_output` /
   `write_bytes_contained` helpers against Windows path semantics, reparse points, case
   folding, trailing dots/spaces, ADS (`file:stream`) and long paths; `verify_run_inventory`
   against what it does *not* check; the `finalize_run` signature change and every caller.
5. **Judge the four disclosures** recorded in
   `PROJECT-STATE.yaml → current_plan.round3_bounded_fix_resolution.disclosures_for_the_reviewer`.
   The first is the one that matters: the pre-staging inventory hash check was **removed** and
   its test replaced. The orchestrator judges that required by GC3-3 rather than optional,
   because the removed check was a second read of the same file. Decide independently whether
   that is a correction or a weakening — a test rewritten to match new behaviour can be either,
   and this call is explicitly yours.
6. **Re-assess the acceptance criteria** the NA-3 review marked NOT MET (AC-4, AC-13, AC-14,
   AC-15, AC-17, AC-18, AC-20) and AC-23 (WEAK). The orchestrator deliberately changed no AC
   verdict. AC text is in `docs/plans/PLAN-002-floorplan-parsing.md`.
7. **List what you could not verify and why.** "CANNOT_VERIFY" is an acceptable and useful
   answer; a confident guess is not.

## Boundaries

- **Read-only. Change nothing.** No edits, no new files, no `git add`, no commit, no merge, no
  push, no test-suite mutation. If you want something run, name the command and the expected
  output in your review and the orchestrator will run it.
- Section 12 privacy: **repository-relative paths only** in your review. No absolute paths, no
  OS account name.
- Do not re-open GC3-8, GC3-9 or GC3-10 as code findings. GC3-8 and GC3-9 were decided by
  Moshe on 2026-08-10 (GC3-8 takes the contract-change route and awaits his section 20 wording
  approval; GC3-9 accepts the already-committed evidence paths without rewriting history), and
  GC3-10 is a human visual gate. You may note if a NA-3b change makes one of them worse.
- Record your **runtime** provider/model/effort metadata as reported by the harness, not from
  self-description, and state it at the top of your review. Section 17 forbids silent
  substitution.

## Baseline facts you may verify but should not assume

- Suite: 338 passed, exit 0. Baseline before this rework was 316.
- Golden canonical-projection hash: `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`, unchanged.
- `pyproject.toml` and `uv.lock` are byte-identical to `main`; `schemas/`, `contracts/` and
  `docs/` are untouched by this commit.
- A green suite has coexisted with live CRITICAL defects in three consecutive review rounds of
  this plan. Test count is not evidence of correctness here.

## Verdict format

Open with `VERDICT: ACCEPT` or `VERDICT: NEEDS_REWORK`, then a findings table
(ID, severity CRITICAL/MAJOR/MINOR/INFO, file:line, one-line claim), then one section per
finding with a concrete failure scenario — inputs and state in, wrong behaviour out. Then the
per-gate table, the disclosure judgments, the AC re-assessment, and the CANNOT_VERIFY list.

This review does not decide merge. Merge requires Moshe's separate authorisation, and G1
additionally requires the human visual gate GC3-10 / NA-4.
