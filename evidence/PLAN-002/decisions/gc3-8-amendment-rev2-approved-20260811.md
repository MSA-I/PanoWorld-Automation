<!-- GC3-8 amendment, revision 2. Supersedes gc3-8-amendment-draft-20260810.md, which stays in
     place unedited because evidence here is append-only. This revision adopts every change the
     independent OpenAI reviewer required in
     gc3-8-independent-openai-wording-review-20260811.md, whose verdict was
     APPROVE_WITH_CHANGES. Paths are repository-relative per section 12. -->

# GC3-8 — amendment revision 2: annotating a selected intake-generated PDF page

## Status

`VERIFIED` as text: drafted by the orchestrator under Moshe's delegation of 2026-08-10 and
approved by an independent cross-provider reviewer, with every required change applied below.
**Not implemented.** Implementation is a separate bounded round.

Provenance chain, so no one has to reconstruct it:

| Step | Artifact |
|---|---|
| Moshe chose the route (contract change, not provenance allowlist) | `PROJECT-STATE.yaml`, `current_plan.open_gate_conditions_round3`, GC3-8 |
| Orchestrator drafted the wording | `evidence/PLAN-002/decisions/gc3-8-amendment-draft-20260810.md` |
| Independent OpenAI review, `APPROVE_WITH_CHANGES` | `evidence/PLAN-002/decisions/gc3-8-independent-openai-wording-review-20260811.md` |
| This revision applies the required changes | this file |

## What revision 1 got wrong

Recorded plainly, because the point of the gate is that it caught these:

1. "One-line schema diff" was false. `$id` and `schema_version` must change too.
2. The amendment creates **contracts bundle 1.2.0**. Revision 1 said nothing about bundle
   versioning, and reusing 1.1.0 would mutate an already-published aggregate contract.
3. "No other parser change" was false. `src/pwa/floorplan/annotation_source.py:70-76` currently
   raises `ValueError` for a missing or disallowed inventory entry, and
   `src/pwa/floorplan/builder.py:1090-1109` converts that into a generic CLI 2 with no
   `PARSE_SOURCE_UNSUPPORTED` code. Restoring the capability requires fixing that
   classification.
4. "DXF/DWG SVG preview" was wrong: `src/pwa/intake.py` creates the SVG preview for DXF only.
5. The security argument was overstated. Revision 1 argued the second annotatable kind grants a
   forged-manifest attacker nothing new. The reviewer refuted it: today a forged manifest exposes
   exactly one annotatable `floorplan`; with `floorplan_page` it can keep **multiple** arbitrary
   PNG entries annotatable while still satisfying the unique-floorplan identity check. That is a
   real if modest capability increase, acceptable only because it is documented as a residual
   trust boundary in the amendment text itself.

Option A (a new `kind` token) is confirmed as the right shape, and the reviewer explicitly agreed
that following Moshe's recorded route rather than silently switching to the cheaper Option D was
correct: "delegation did not authorize silently reversing it merely because deferral is cheaper."

## Amendment 1 — PLAN-002 section 6, "Annotation adapter"

Replace the second bullet (currently line 203) with the reviewer's approved text:

> An annotation selects exactly one source image through its sole `payload.image.source_image_ref`.
> Selection is exact, code-point-for-code-point string equality, after JSON decoding, with one
> `payload.inputs[].path` in the validated source manifest. No case folding, slash conversion,
> Unicode normalization, filesystem alias resolution, path-prefix inference or `derived_from`
> inference participates in selection.
>
> Source-manifest preflight must first require unique inventory path strings. Duplicate paths are
> an invalid source contract and fail with CLI 2 and no finalized derived run; they are not an
> annotation "multiple match."
>
> The selected entry must have `kind: "floorplan"` and decode as PNG or JPEG, or have
> `kind: "floorplan_page"` and decode as PNG. Raw PDF, CAD source bytes, CAD previews,
> `style_reference`, `other`, and all other formats are not annotatable. A missing reference, a
> disallowed kind, or an incompatible decoded format produces `PARSE_SOURCE_UNSUPPORTED`, CLI 2,
> and no finalized derived run.
>
> `floorplan_page` is a producer-contract token reserved exclusively for PNG page renders created
> by the approved intake PDF renderer from the same run's unique `kind: "floorplan"` PDF input. It
> must not be assigned to uploaded rasters, style references, DXF/DWG previews, generic
> derivatives or any other artifact.
>
> The parser treats the validated manifest classification as authoritative; it does not
> authenticate that classification from the path. `content_hash` is not an authenticity mechanism.
> An actor able to rewrite a source run and recompute its hashes can misclassify arbitrary PNG
> inventory entries, and `floorplan_page` increases how many such entries one forged manifest can
> expose. This is an explicit residual source-run trust-boundary limitation, not a property
> claimed to be prevented by this amendment.

Unchanged and not to be widened by an implementer: the manifest must still contain exactly one
`kind: "floorplan"` entry (`src/pwa/floorplan/builder.py:622`); `style_reference` never becomes
annotatable; width, height and hash are still decoded fresh from the verified bytes.

## Amendment 2 — schema and bundle

> Add `schemas/project_manifest/v1/project_manifest-1.1.0.schema.json`. It is structurally
> identical to 1.0.0 except for these three intentional changes:
>
> 1. `$id` identifies `project_manifest-1.1.0.schema.json`;
> 2. `schema_version` is `const: "1.1.0"`;
> 3. the `kind` enum is `["floorplan", "style_reference", "other", "floorplan_page"]`.
>
> `schemas/project_manifest/v1/project_manifest-1.0.0.schema.json` remains byte-identical, with
> SHA-256 `b8020d9c79fa009d49c1b7bbaa6a64fd8a7caddfeadfc4080e8a1d3033ca33e6`.
>
> The existing filesystem-discovered schema catalog must expose both exact versions, and its
> latest-version view must select 1.1.0. There is no separate hard-coded catalog entry to edit.
>
> This contract addition creates contracts bundle `1.2.0`; it must not silently change the
> already-published meaning of bundle 1.1.0. New intake manifests and new derived parse-run
> manifests produced after this amendment declare `project_manifest` 1.1.0 and bundle 1.2.0.
> Existing finalized artifacts retain their declared schema and bundle versions unchanged.
>
> Every valid 1.0.0 project-manifest instance remains valid under the 1.1.0 schema. A manifest
> using `floorplan_page` is valid only as project-manifest 1.1.0 and does not validate as 1.0.0.
> Consumers processing an exact 1.0.0 contract remain unchanged; consumers opting into 1.1.0 must
> handle the appended enum token.

And in PLAN-002 section 5, replace the fixed project-manifest 1.0.0 wording with:

> The new `project/project_manifest.json` is schema `project_manifest` 1.1.0, declares contracts
> bundle 1.2.0, carries the new parse-run ID and artifact ID, and contains the complete copied
> inventory with reverified hashes. The source manifest remains byte-unchanged at its originally
> declared schema and bundle versions.

**Orchestrator check:** the pinned digest was verified against the file rather than taken on
trust. `Get-FileHash -Algorithm SHA256` on
`schemas/project_manifest/v1/project_manifest-1.0.0.schema.json` returns
`b8020d9c79fa009d49c1b7bbaa6a64fd8a7caddfeadfc4080e8a1d3033ca33e6`, which matches. An amendment
that pins a wrong digest would be worse than one that pins none.

## Amendment 3 — intake

> For a PDF floorplan input, each PNG returned by the approved intake PDF renderer is recorded as
> `kind: "floorplan_page"`. The original PDF remains the unique `kind: "floorplan"` entry. The
> intake producer must not emit `floorplan_page` for any other artifact.
>
> The DXF SVG preview remains `kind: "other"` and is not annotatable. Current intake produces no
> DWG SVG preview; any future CAD preview must likewise remain non-annotatable unless separately
> approved.

## Amendment 4 — parser

> `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan", "floorplan_page"}` in
> `src/pwa/floorplan/annotation_source.py`.
>
> The lookup and format checks must produce `FloorplanError("PARSE_SOURCE_UNSUPPORTED", ...)` for
> an absent inventory reference, a disallowed inventory kind, or bytes that do not decode to the
> format allowed for that kind. Hash disagreement continues to produce
> `PARSE_SOURCE_HASH_MISMATCH`.
>
> Duplicate inventory paths remain an earlier invalid-source-contract failure. No new error-code
> token is introduced, so `contracts/error_codes.md` is unchanged.

## Acceptance criteria (the reviewer's replacements, adopted in full)

1. Exact catalog lookup validates project-manifest 1.0.0 and 1.1.0 independently; the latest view
   selects 1.1.0; duplicate version pairs and duplicate `$id` values remain rejected.
2. Every historical 1.0.0 fixture validates unchanged under its declared version and under 1.1.0.
   The frozen 1.0.0 schema has the pinned SHA-256 above and rejects `floorplan_page`.
3. New intake and derived manifests declare project-manifest 1.1.0 and bundle 1.2.0. Existing
   source artifacts remain byte-identical.
4. A two-page PDF intake emits the original PDF as the unique `floorplan`, exactly two PNG
   `floorplan_page` entries, and no other `floorplan_page` entries. A DXF preview remains `other`.
5. Selecting page 2 proves binding through measurable assertions: the recorded source hash,
   decoded dimensions, sanitized embedded pixels and overlay source binding correspond to page 2
   and differ from page 1. Repeated output is deterministic.
6. Missing inventory references, `style_reference`, `other`, raw PDF, and a `floorplan_page` entry
   whose bytes are not PNG each produce `PARSE_SOURCE_UNSUPPORTED`, CLI 2, and no finalized
   derived run.
7. Existing direct PNG and JPEG `floorplan` annotation paths still succeed.
8. Annotation and inventory hash mismatches still produce `PARSE_SOURCE_HASH_MISMATCH`; this
   amendment must not collapse them into "unsupported."
9. The complete test suite and contract-version tests pass; `pyproject.toml` and `uv.lock` remain
   unchanged.

## Scope note for whoever schedules the implementation

This is no longer the small change revision 1 implied. It touches `schemas/`, the contracts
bundle version, `src/pwa/intake.py`, `src/pwa/floorplan/annotation_source.py`, the error
classification in `src/pwa/floorplan/builder.py`, PLAN-002 sections 5 and 6, and the contract
version tests. It is a bounded round of its own and must not be bolted onto a code-fix round.

Nothing else remaining in Part 1 depends on it: `samples/Sample_Floorplan.jpg` is a JPEG and the
NA-4/NA-5 runs bind to `kind: "floorplan"` directly. So this round can be scheduled after the
Part 1 gates close without blocking them — but PLAN-002 section 6 promises the capability today,
so leaving it unimplemented means the plan text and the code still disagree.
