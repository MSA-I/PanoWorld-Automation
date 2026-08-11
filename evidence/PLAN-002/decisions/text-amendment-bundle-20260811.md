<!-- Bundled text-only amendment to PLAN-002, applied 2026-08-11 by the orchestrator under Moshe's
     delegation of 2026-08-10. Every item below carries the exact wording an INDEPENDENT reviewer
     required or approved; none of it is the orchestrator's own unreviewed text. Repository-relative
     paths only (section 12). -->

# Text amendment bundle — three items, all reviewer-supplied

No code changes. Three defects in text that had already passed a gate, bundled because two of the
three reviewers who found them recommended exactly that.

| Item | Origin | Reviewer | Status |
|---|---|---|---|
| **A. AC 2 of the GC3-8 amendment is unsatisfiable as written** | raised by the orchestrator as F-NA6-1 | NA-6b (Anthropic) ruled the orchestrator right and the repair adequate, and added one requirement | applied below |
| **B. Three stale schema/bundle statements in PLAN-002** | raised by NA-6b as F-NA6B-1 | its own finding; it recommended bundling | applied below |
| **C. AC-13's provenance enumeration** | drafted by the orchestrator (NA-7) | NA-7 reviewer (OpenAI) returned APPROVE_WITH_CHANGES with replacement wording and caught three errors in the draft | applied below, in the reviewer's words |

---

## A. Repair to AC 2 of `gc3-8-amendment-rev2-approved-20260811.md`

That file is committed evidence and is **not** edited. This is the correction of record.

AC 2 read:

> Every historical 1.0.0 fixture validates unchanged under its declared version and under 1.1.0.

The second half is unsatisfiable **by construction**: every schema in this system pins its own
`schema_version` as a `const`, so a document declaring `"schema_version": "1.0.0"` fails 1.1.0's
const on its first keyword regardless of payload. Measured on all three committed 1.0.0 manifests
under `runs/`. The NA-6b reviewer confirmed the reasoning and added that the const-pinning is
load-bearing for the security property — it is what stops a `floorplan_page` entry being smuggled
into a 1.0.0-declared manifest — so the clause could not be satisfied by weakening the schema either.

AC 2 is corrected to, incorporating the reviewer's required addition about real artifacts:

> Every historical 1.0.0 fixture **and every committed 1.0.0 run artifact** continues to validate
> unchanged under its declared version, and its payload shape is valid under 1.1.0 when relabelled
> to that version. A document declaring `schema_version: "1.0.0"` is not expected to validate
> against the 1.1.0 schema, whose `schema_version` const forbids it by construction.

`tests/unit/test_contract_versions.py` already proves exactly this, in two distinct steps, so no
test changes.

## B. Three stale schema and bundle statements in PLAN-002

Found by the NA-6b reviewer at `docs/plans/PLAN-002-floorplan-parsing.md:34`, `:90` and `:102`.
Each described the pre-GC3-8 world, in which new artifacts were project_manifest 1.0 and bundle
1.1.0. After NA-6 new artifacts are project_manifest **1.1.0** and bundle **1.2.0**. The historical
statements — that existing artifacts are never rewritten and keep their declared versions — remain
true and are preserved.

Applied as three minimal edits, listed in the commit that carries them.

## C. AC-13 — Required Entity Audit Metadata

The orchestrator's draft is `ac13-provenance-enumeration-draft-20260811.md`; the review that
governs it is `ac13-independent-openai-wording-review-20260811.md`. **The draft was wrong in three
ways and the reviewer's wording replaces it**, recorded because the record should say so:

1. The draft required room provenance to preserve "the same vertex count and order as the emitted
   polygon". `src/pwa/floorplan/normalize.py` deliberately rotates and sometimes reverses room
   vertices, so the clause would have failed the implementation it was written to describe.
2. The draft added a second definition to section 6 while section 9 already carried provenance
   bullets, which would have left two competing requirements.
3. The draft banned synthesised provenance outright, which would also have outlawed the DXF opening
   centre — a deterministic midpoint. The correct line is that a deterministic locator may be
   recorded while a derived annotation span may not be labelled as source-supplied.

Its addendum was also judged correct but failing open: saying `texts` is "out of scope" leaves an
accidental non-empty `texts` unconstrained. The reviewer requires it absent or empty, with a
non-empty array failing AC-13.

Applied: section 9's four provenance bullets are replaced by the reviewer's **Required Entity Audit
Metadata** block, section 6 gains only the one-line cross-reference the reviewer specified, and
AC-13 is replaced by the reviewer's text. All three are quoted verbatim from
`ac13-independent-openai-wording-review-20260811.md`, which states that with this wording it would
mark AC-13 **MET** on the current implementation.

## What this closes and what it does not

- **AC-13 becomes decidable.** It has been CANNOT_VERIFY across three consecutive independent
  reviews for one reason: the plan never enumerated what it required. It does now.
- **GC3-8 is CLOSED** on the NA-6b reviewer's ruling; this bundle removes the plan's internal
  inconsistency that its own implementation exposed.
- It does **not** touch AC-14's byte-determinism clause, which needs a second `ezdxf` version, nor
  the DXF single-snapshot design change, nor NA-4 — which remains Moshe's visual gate.

## Approval path

Every wording here was supplied or explicitly approved by an independent reviewer of a provider
opposite to its author, which is what section 20 and docs/04's "the sole author is not the final
approver" require. The applied result is routed to one further opposite-provider check, recorded
beside this file, so that the *application* is verified and not only the wording.
