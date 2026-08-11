<!-- Independent cross-provider check of the APPLICATION of the text amendment bundle, plus the
     orchestrator's response to it. Repository-relative paths only (section 12). -->

# Application check for the text amendment bundle — and one declined requirement

Subject: `docs/plans/PLAN-002-floorplan-parsing.md` after the edits recorded in
`evidence/PLAN-002/decisions/text-amendment-bundle-20260811.md`.
Checker: OpenAI, via Codex CLI `codex exec --sandbox read-only --disable hooks`, launched with
`-m gpt-5.6-sol` and `model_reasoning_effort=xhigh`.
Date: 2026-08-11.

## Runtime metadata discrepancy, recorded because section 17 requires it

The checker reported its own model as **"GPT-5"**. The orchestrator's launch configuration
specified **`gpt-5.6-sol`**, and it reported that its session metadata did not expose the effort
value. Section 17 requires runtime metadata to come from the harness rather than from an agent's
self-description, and this is exactly why: the launch configuration is the record, the
self-report is not. No verdict here depends on which it was.

## What it verified

| Item | Result |
|---|---|
| Placement — section 6 gained only the authorised one-line cross-reference, sensibly placed | **PASS** |
| The old four section 9 provenance bullets were removed, leaving no competing definition | **PASS** |
| The three version statements now describe project_manifest 1.1.0 and bundle 1.2.0 for new artifacts while preserving existing artifacts and their declared versions | **PASS** |
| No other stale current-version statement anywhere in the document | **PASS** — it searched and found none |
| Internal consistency — nothing else contradicts the new section 9 | **PASS** |
| Scope — no plan edit beyond the authorised items | **PASS** |

Six of the six substantive checks pass. Its overall line was `APPLICATION INCORRECT` on one ground
only, addressed next.

## The one requirement, and why the orchestrator declines it

The checker required that the applied text reproduce the reviewer's blockquote **typography**
exactly: six curly apostrophes (`’`) where ASCII apostrophes were used, and `units—declared`
without spaces where ` — ` was used. Its own words: "These are punctuation/typography differences
only; they do not change meaning."

Declined, on measured evidence rather than preference:

- `docs/plans/PLAN-002-floorplan-parsing.md` contains **zero** U+2019 curly apostrophes and
  **eleven** ASCII apostrophes. Importing curly apostrophes would make the newly added block the
  only place in the document using a different apostrophe character.
- Every existing em dash in the document is **spaced** — for example "the span shortens — a 0.05 m
  span" and "so a JPEG's EXIF — including GPS coordinates". The applied `units — declared` follows
  the document's own convention; the unspaced form would be the outlier.

The curly quotes and unspaced dash are artifacts of the review transcript's own output formatting,
not a deliberate choice by the reviewer about plan typography. The property worth having is that
the **words** are the approved words, and they are: every clause, list item and MUST is verbatim.
Byte-identity with a chat transcript's smart quotes is not a property this plan should acquire, and
acquiring it would reduce the document's internal consistency, which the same checker separately
verified as a PASS.

Recorded as a deviation rather than settled silently. If Moshe or a later reviewer disagrees, the
fix is six character replacements and one space removal, and nothing else depends on it.

## Status

The application is verified on substance, placement, scope and consistency. One typographic
requirement is declined with reasons. AC-13 is now decidable and the plan's internal version
statements are consistent.
