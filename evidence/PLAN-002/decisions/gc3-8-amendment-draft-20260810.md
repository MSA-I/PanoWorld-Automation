<!-- GC3-8 amendment draft. Authored by the orchestrator under the authority Moshe delegated
     on 2026-08-10. NOT approved and NOT implemented: PLAN-002 section 20 and docs/04's rule
     that the sole author is not the final approver of a critical artifact both require an
     independent cross-provider review of this text before any code changes. Paths are
     repository-relative per section 12. -->

# GC3-8 — draft amendment: annotating a selected intake-generated PDF page

## Status

`REVIEW` — drafted 2026-08-10, awaiting independent cross-provider approval. Implementation
is a separate bounded round and must not start from this document alone.

## The defect this closes

PLAN-002 section 6 permits annotating one explicitly selected intake-generated PDF page.
The code cannot reach that capability:

- `src/pwa/intake.py:174-179` renders each PDF page to
  `project/inputs/derivatives/pdf/page-NNNN.png` and tags every one `kind: "other"`.
- The GC-5 fix set `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}`, so an annotation may
  only bind to the single `kind: "floorplan"` entry.
- For a PDF source that entry is the **PDF file itself** (`src/pwa/intake.py:208`), and
  section 6 line 203 states plainly that "Raw PDF is not embedded or decoded by the parser".

So the permitted path is closed at both ends: the page PNGs are not annotatable, and the
only annotatable entry is undecodable. Moshe decided on 2026-08-10 that the route is a
**contract change** rather than a provenance-based allowlist. This draft fills in the
wording that decision deliberately left open.

## Decision, and why

**Chosen: a new inventory `kind` token, `floorplan_page`.**

| Option | What it does | Verdict |
|---|---|---|
| **A. new `kind` token `floorplan_page`** (chosen) | Intake tags rendered PDF pages `floorplan_page`; the parser's allowlist becomes `{"floorplan", "floorplan_page"}` | One classification axis, and the token says exactly what the thing is |
| B. provenance-based allowlist (path prefix or `derived_from`) | Parser infers annotatability from where intake put the file | **Rejected by Moshe on 2026-08-10.** Also makes a directory layout into a security-relevant contract |
| C. keep `kind: "other"`, add an optional `role: "floorplan_page"` | Additive optional property instead of a widened enum | Technically the gentlest schema change, but it leaves two fields answering the same question and the next reader has to learn which one wins. Recorded as the fallback if the reviewer rejects the enum widening |
| D. amend section 6 to defer PDF-page annotation out of Part 1 | Deletes the contradiction instead of the gap | **Cheapest option and NOT chosen**, because it reverses Moshe's recorded route. Flagged for him explicitly below, since nothing remaining in Part 1 needs this capability |

Honest note for Moshe, since this is the kind of thing delegation should not bury: option D
is materially cheaper than A. `samples/Sample_Floorplan.jpg` is a JPEG, so NA-5 and every
other remaining Part 1 step work without this capability, and A costs an additive schema
version, a catalog entry, an intake change, a parser change and fixture updates. A is chosen
only because you already decided the route was a contract change. If you would rather defer
the capability, say so and D is a two-line amendment.

## Amendment 1 — PLAN-002 section 6, "Annotation adapter"

Replace the second bullet (currently line 203) with:

> - Annotation `source_image_ref` and hash must bind to one inventory entry of the verified
>   source manifest whose `kind` is `floorplan` (an immutable PNG or JPEG floorplan input) or
>   `floorplan_page` (an intake-generated PDF page render). Raw PDF is neither embedded nor
>   decoded by the parser: a PDF source is annotated only through a `floorplan_page`
>   derivative. **"Explicitly selected" is an act of the annotation document, not of the
>   manifest**: the manifest may declare many `floorplan_page` entries, and the annotation's
>   single `source_image_ref` is the selection. The reference must resolve to exactly one
>   inventory entry with an annotatable `kind`; zero matches, more than one match, or a match
>   whose `kind` is neither of the two is `PARSE_SOURCE_UNSUPPORTED` with `cli_exit == 2`.

Unchanged by this amendment, and stated here so no implementer widens them by accident:

- The manifest must still contain **exactly one** `kind: "floorplan"` entry
  (`src/pwa/floorplan/builder.py:622`). A PDF source keeps the PDF itself as that entry, so
  adding `floorplan_page` entries does not disturb GC3-4's identity checks.
- `style_reference` is not annotatable and does not become annotatable.
- Width, height and hash are still decoded fresh from the verified bytes, not read from
  manifest `details` (section 6, line 204).

## Amendment 2 — schema

Additive minor version per ADR-0002 and ADR-0005:
`schemas/project_manifest/v1/project_manifest-1.1.0.schema.json`, identical to 1.0.0 except
that `payload.inputs.items.properties.kind.enum` becomes
`["floorplan", "style_reference", "other", "floorplan_page"]`. The new value is appended so
the diff is one line. Register the exact version in the catalog ADR-0005 requires; do not
edit `project_manifest-1.0.0.schema.json`, which is frozen.

Compatibility, stated rather than assumed: every existing 1.0.0 manifest validates unchanged
under 1.1.0. A 1.1.0 manifest that uses the new token does **not** validate under 1.0.0,
which is the normal direction for an additive minor bump. A consumer that switches
exhaustively on `kind` must gain the new arm — inside this repository that is the annotation
allowlist and the intake writer, both changed below.

## Amendment 3 — intake

`src/pwa/intake.py:178`: PDF page renders under `project/inputs/derivatives/pdf/` are tagged
`kind: "floorplan_page"`. The DXF/DWG SVG preview at `:185` stays `kind: "other"` — it is a
preview, not an annotatable floorplan surface, and widening it would hand the annotation
adapter a vector preview it cannot bind pixels to.

## Amendment 4 — parser

`_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan", "floorplan_page"}`. No other change: the
"exactly one match" rule of Amendment 1 is already the behaviour of the existing lookup, and
its failure path already produces `PARSE_SOURCE_UNSUPPORTED` with `cli_exit == 2`, so no new
error code is needed and `contracts/error_codes.md` is not appended.

## Acceptance criteria added by this amendment

1. An annotation whose `source_image_ref` names a `floorplan_page` entry parses successfully
   and produces a source-aligned overlay from that page's pixels.
2. An annotation naming a `style_reference` or an `other` entry fails with
   `PARSE_SOURCE_UNSUPPORTED` and `cli_exit == 2` — the GC-5 property must not regress.
3. An annotation naming a path absent from the inventory fails the same way.
4. A two-page PDF intake produces two `floorplan_page` entries, and annotating page 2
   binds to page 2's bytes and hash, not page 1's.
5. Every pre-existing manifest fixture still validates, and the 1.0.0 schema file is
   byte-identical to its committed state.

## What the reviewer is asked to rule on

1. Is widening the `kind` enum the right shape, or is option C's optional `role` field
   preferable given ADR-0005's additive-only rule? Rule on it; do not just note the tension.
2. Does "selection is an act of the annotation, not the manifest" leave a hole? Specifically:
   can an attacker who forges a source manifest gain anything from a second annotatable kind
   that they did not already have by tagging any file `kind: "floorplan"`? The orchestrator's
   position is no — finding F-12 of the NA-3d review establishes that `content_hash` is
   keyless, so manifest forgery is already available and the allowlist is a least-privilege
   control rather than an authenticity boundary. Confirm or refute.
3. Does Amendment 3 leave the DXF/DWG SVG preview correctly excluded?
4. Is anything here a non-additive change in disguise?
