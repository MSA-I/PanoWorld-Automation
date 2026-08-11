<!-- NA-6 dispatch brief: implement the APPROVED GC3-8 contract amendment. Authored by the
     orchestrator. Repository-relative paths only (PLAN-002 section 12). -->

# NA-6 — implement the approved GC3-8 amendment

You are the PLAN-002 implementer. This is a **contract round**, unlike the five code-fix rounds
before it: you will change `schemas/`, the contracts bundle version, `src/pwa/intake.py`, the
annotation adapter, an error classification, and PLAN-002 sections 5 and 6. That is authorised —
and only because the exact text is already approved. **Implement that text; do not redesign it.**

## The approved text is your specification

    evidence/PLAN-002/decisions/gc3-8-amendment-rev2-approved-20260811.md

Read it in full before touching anything. It contains four numbered amendments and nine acceptance
criteria, all approved. Its provenance:

- Moshe chose the route (contract change, not a provenance-based allowlist) on 2026-08-10 and
  delegated the wording to the orchestrator.
- The orchestrator drafted it (`gc3-8-amendment-draft-20260810.md`, revision 1).
- An independent OpenAI reviewer returned APPROVE_WITH_CHANGES and supplied replacement wording
  (`gc3-8-independent-openai-wording-review-20260811.md`). It caught three factual errors and a
  bundle-versioning gap in revision 1.
- Revision 2 applies every required change. **Revision 2 is the specification. Revision 1 is
  superseded and must not be implemented.**

Where revision 2 quotes text in a blockquote, that is the wording to put in the plan, verbatim.

## What the amendment closes

PLAN-002 section 6 permits annotating one explicitly selected intake-generated PDF page. The code
cannot reach it: intake tags every rendered page `kind: "other"`, the annotation allowlist admits
only `kind: "floorplan"`, and for a PDF source that entry is the PDF itself — which section 6 says
the parser never decodes. Closed at both ends.

## The five pieces, in the order they should be built

1. **Schema.** Add `schemas/project_manifest/v1/project_manifest-1.1.0.schema.json`, structurally
   identical to 1.0.0 except `$id`, `schema_version` const, and the `kind` enum gaining
   `floorplan_page` as an appended value. Leave 1.0.0 **byte-identical** — its SHA-256 is pinned in
   the amendment and was verified by the orchestrator against the file, so if your build changes it
   you have broken something.
2. **Bundle.** The addition creates contracts bundle **1.2.0**. It must not mutate the published
   1.1.0. New intake manifests and new derived parse-run manifests declare project_manifest 1.1.0
   and bundle 1.2.0; existing finalized artifacts keep their declared versions. The catalog is
   filesystem-discovered, so both exact versions must be exposed and the latest-version view must
   select 1.1.0.
3. **Intake.** PDF page renders become `kind: "floorplan_page"`; the PDF stays the unique
   `kind: "floorplan"`. The DXF SVG preview stays `kind: "other"`. Note the amendment's correction:
   intake creates that preview for DXF only, not DWG.
4. **Parser.** The allowlist becomes `{"floorplan", "floorplan_page"}`, **and** the error
   classification is fixed: a missing inventory reference, a disallowed kind, or bytes that do not
   decode to the format allowed for that kind must produce
   `FloorplanError("PARSE_SOURCE_UNSUPPORTED", ...)`. Today `src/pwa/floorplan/annotation_source.py`
   raises a bare `ValueError` for those cases and the caller turns it into a generic CLI 2 with no
   code — that is the third factual error the reviewer caught, and fixing it is part of this round.
   Hash disagreement must keep producing `PARSE_SOURCE_HASH_MISMATCH`; do not collapse the two.
   Duplicate inventory paths are an earlier invalid-source-contract failure, CLI 2, no finalized
   run — not an annotation "multiple match".
5. **Plan text.** Apply the amendment's blockquoted replacements to PLAN-002 sections 5 and 6.
   This is the **one** round in which editing `docs/plans/PLAN-002-floorplan-parsing.md` is
   authorised, and only for the clauses the amendment names. Do not touch any other clause.

## Boundaries

- **`contracts/error_codes.md` is unchanged.** No new error-code token; `PARSE_SOURCE_UNSUPPORTED`
  already exists.
- **No new dependency.** `pyproject.toml` and `uv.lock` byte-identical.
- **`limits_snapshot()` gains no key.**
- **Do not touch anything under `evidence/`** — append-only. Your report is the one new file.
- **Do not touch GC3-9 or GC3-10.**
- `parse_run()` must never raise.
- The golden canonical projection hash must not move:
  `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`.
- Baseline to preserve: **356 passed, exit 0**, repository `.venv`, cleared `PYTHONPATH`.
- Do not commit. The orchestrator commits.
- Do not write a test whose outcome depends on which volume `pytest` puts `tmp_path` on. That
  mistake cost a follow-up round already.

## The nine acceptance criteria are the test plan

They are in the amendment and they are not negotiable. Two deserve emphasis because they are the
ones a careless implementation breaks:

- **AC 2:** every historical 1.0.0 fixture must still validate under its declared version, and the
  frozen 1.0.0 schema must still **reject** `floorplan_page`.
- **AC 5:** selecting page 2 of a two-page PDF must be proven by measurable assertions — the
  recorded source hash, the decoded dimensions, the sanitized embedded pixels and the overlay
  source binding all correspond to page 2 and **differ from page 1**. A test that only checks the
  run succeeded does not prove selection.

## One extra fix folded in, on the reviewer's own recommendation: R-1

The NA-3h review of the previous round returned ACCEPT with exactly one must-fix follow-up, and said
"fold it into NA-6". Doing that:

**R-1 — `src/pwa/floorplan/cli.py`.** The stderr write that reports `residual_state` sits **outside**
the `try/except Exception: return 2` that wraps `parse_run`. So a `BrokenPipeError`, a closed stderr
or a full disk turns the documented **exit 2** into an uncaught exception and **exit 1** — on exactly
the path whose purpose is to report that a finalized run directory was left behind. An in-process
caller of `main()` receives an exception where the contract promises an `int`.

Fix: move the write inside the existing `try`, or wrap it in its own `except OSError: pass`. Two
lines. Add a test that proves an `OSError` on the stderr write still yields exit 2 — patching
`sys.stderr` with an object whose `write` raises is enough; do not simulate it by patching `print`.

Note the reviewer disproved a neighbouring hypothesis so you do not need to chase it:
`ensure_ascii=False` on a legacy-codepage stderr cannot raise `UnicodeEncodeError`, because CPython
initialises `sys.stderr` with the `backslashreplace` handler. R-1 is an `OSError` finding only.

## Deliverable

`evidence/PLAN-002/reviews/na6-gc3-8-implementation-report-20260811.md` with, per amendment: what
changed, which acceptance criteria it satisfies, and the test that fails if it is reverted. Plus
R-1's fix and its test, the full suite result, the boundary confirmations with digests, and your
runtime metadata from the session rollout.

If any part of the approved text turns out to be unimplementable as written, **stop and say so**
rather than improvising an alternative — the text went through a gate and a deviation needs the same
gate, not an implementer's judgement.
