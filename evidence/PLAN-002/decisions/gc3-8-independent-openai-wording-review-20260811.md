<!-- Archived verbatim by the orchestrator. The reviewer wrote this document; no wording was
altered. Runtime metadata below is from the session rollout, not from the reviewer's
self-description.

  task: GC3-8 contract-amendment wording review (PLAN-002 section 20 gate)
  provider: openai
  requested_model: gpt-5.6-sol
  actual_model_id: gpt-5.6-sol   (no substitution)
  reasoning effort: xhigh
  route: Codex CLI 0.144.6, `codex exec --sandbox read-only --disable hooks`, direct
         read-only filesystem access to the working tree
  subject: evidence/PLAN-002/decisions/gc3-8-amendment-draft-20260810.md
  verdict: APPROVE_WITH_CHANGES

WHY THIS REVIEW EXISTS. Moshe delegated PLAN-002's remaining decisions to the orchestrator on
2026-08-10. He did not delegate approval of the orchestrator's own drafts:
docs/04-מתודיקת-ניהול-סוכנים-ומעקב.md states that the sole author is not the final approver of a
critical artifact, and PLAN-002 section 20 makes this text a gate. The orchestrator is Anthropic,
so the reviewer is OpenAI - opposite provider, as section 17 requires.

WHAT IT CAUGHT, recorded because the orchestrator got these wrong and the record should say so:
three factual errors in the draft (the schema change is not a one-line diff because $id and
schema_version must also change; intake produces the SVG preview for DXF only, not DWG; and the
claim that no other parser change is needed is false, because the current code raises ValueError
for a missing or disallowed inventory entry and the caller converts that to a generic CLI 2
without PARSE_SOURCE_UNSUPPORTED), one governance gap (the enum addition creates contracts bundle
1.2.0 and must not mutate the already-published 1.1.0), and one overstated security claim (the
orchestrator argued the second annotatable kind grants an attacker nothing new; the reviewer
refutes that a forged manifest can now keep multiple arbitrary PNG entries annotatable while
still satisfying the unique-floorplan identity check).
-->

VERDICT: APPROVE_WITH_CHANGES

Runtime provider: OpenAI Codex  
Exact model ID: `gpt-5.6-sol`  
Reasoning effort: `xhigh`

The proposed route is sound, but the draft is not implementation-ready. It contains incorrect claims about current error handling, leaves schema/bundle emission ambiguous, and understates the capability gained through a forged manifest.

## Required replacement wording

### 1. Replace Amendment 1’s definition of selection with

> An annotation selects exactly one source image through its sole `payload.image.source_image_ref`. Selection is exact, code-point-for-code-point string equality, after JSON decoding, with one `payload.inputs[].path` in the validated source manifest. No case folding, slash conversion, Unicode normalization, filesystem alias resolution, path-prefix inference or `derived_from` inference participates in selection.
>
> Source-manifest preflight must first require unique inventory path strings. Duplicate paths are an invalid source contract and fail with CLI 2 and no finalized derived run; they are not an annotation “multiple match.”
>
> The selected entry must have `kind: "floorplan"` and decode as PNG or JPEG, or have `kind: "floorplan_page"` and decode as PNG. Raw PDF, CAD source bytes, CAD previews, `style_reference`, `other`, and all other formats are not annotatable. A missing reference, a disallowed kind, or an incompatible decoded format produces `PARSE_SOURCE_UNSUPPORTED`, CLI 2, and no finalized derived run.
>
> `floorplan_page` is a producer-contract token reserved exclusively for PNG page renders created by the approved intake PDF renderer from the same run’s unique `kind: "floorplan"` PDF input. It must not be assigned to uploaded rasters, style references, DXF/DWG previews, generic derivatives or any other artifact.
>
> The parser treats the validated manifest classification as authoritative; it does not authenticate that classification from the path. `content_hash` is not an authenticity mechanism. An actor able to rewrite a source run and recompute its hashes can misclassify arbitrary PNG inventory entries, and `floorplan_page` increases how many such entries one forged manifest can expose. This is an explicit residual source-run trust-boundary limitation, not a property claimed to be prevented by this amendment.

This definition is sufficiently deterministic for independent implementations. The current phrase “names an entry” is not: implementations could reasonably disagree about path normalization and duplicate-path behavior.

### 2. Replace Amendment 2 with

> Add `schemas/project_manifest/v1/project_manifest-1.1.0.schema.json`. It is structurally identical to 1.0.0 except for these three intentional changes:
>
> 1. `$id` identifies `project_manifest-1.1.0.schema.json`;
> 2. `schema_version` is `const: "1.1.0"`;
> 3. the `kind` enum is `["floorplan", "style_reference", "other", "floorplan_page"]`.
>
> `schemas/project_manifest/v1/project_manifest-1.0.0.schema.json` remains byte-identical, with SHA-256 `b8020d9c79fa009d49c1b7bbaa6a64fd8a7caddfeadfc4080e8a1d3033ca33e6`.
>
> The existing filesystem-discovered schema catalog must expose both exact versions, and its latest-version view must select 1.1.0. There is no separate hard-coded catalog entry to edit.
>
> This contract addition creates contracts bundle `1.2.0`; it must not silently change the already-published meaning of bundle 1.1.0. New intake manifests and new derived parse-run manifests produced after this amendment declare `project_manifest` 1.1.0 and bundle 1.2.0. Existing finalized artifacts retain their declared schema and bundle versions unchanged.
>
> Every valid 1.0.0 project-manifest instance remains valid under the 1.1.0 schema. A manifest using `floorplan_page` is valid only as project-manifest 1.1.0 and does not validate as 1.0.0. Consumers processing an exact 1.0.0 contract remain unchanged; consumers opting into 1.1.0 must handle the appended enum token.

The draft’s “one-line diff” statement is false because `$id` and `schema_version` must also change. More importantly, reusing bundle 1.1.0 would mutate an existing aggregate contract in place.

The amendment must also replace the fixed project-manifest 1.0.0 wording in `docs/plans/PLAN-002-floorplan-parsing.md` section 5 with:

> The new `project/project_manifest.json` is schema `project_manifest` 1.1.0, declares contracts bundle 1.2.0, carries the new parse-run ID and artifact ID, and contains the complete copied inventory with reverified hashes. The source manifest remains byte-unchanged at its originally declared schema and bundle versions.

### 3. Replace Amendment 3 with

> For a PDF floorplan input, each PNG returned by the approved intake PDF renderer is recorded as `kind: "floorplan_page"`. The original PDF remains the unique `kind: "floorplan"` entry. The intake producer must not emit `floorplan_page` for any other artifact.
>
> The DXF SVG preview remains `kind: "other"` and is not annotatable. Current intake produces no DWG SVG preview; any future CAD preview must likewise remain non-annotatable unless separately approved.

The draft incorrectly describes the existing derivative as a “DXF/DWG SVG preview”; `src/pwa/intake.py` currently creates it only for DXF.

### 4. Replace Amendment 4 with

> `_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan", "floorplan_page"}` in `src/pwa/floorplan/annotation_source.py`.
>
> The lookup and format checks must produce `FloorplanError("PARSE_SOURCE_UNSUPPORTED", ...)` for an absent inventory reference, a disallowed inventory kind, or bytes that do not decode to the format allowed for that kind. Hash disagreement continues to produce `PARSE_SOURCE_HASH_MISMATCH`.
>
> Duplicate inventory paths remain an earlier invalid-source-contract failure. No new error-code token is introduced, so `contracts/error_codes.md` is unchanged.

The current draft’s “No other change” claim is incorrect. `src/pwa/floorplan/annotation_source.py:70-76` currently raises `ValueError` for missing or disallowed entries, and `src/pwa/floorplan/builder.py:1090-1109` converts that to a generic CLI-2 operational result without `PARSE_SOURCE_UNSUPPORTED`.

## Replacement acceptance criteria

1. Exact catalog lookup validates project-manifest 1.0.0 and 1.1.0 independently; the latest view selects 1.1.0; duplicate version pairs and duplicate `$id` values remain rejected.
2. Every historical 1.0.0 fixture validates unchanged under its declared version and under 1.1.0. The frozen 1.0.0 schema has the pinned SHA-256 above and rejects `floorplan_page`.
3. New intake and derived manifests declare project-manifest 1.1.0 and bundle 1.2.0. Existing source artifacts remain byte-identical.
4. A two-page PDF intake emits the original PDF as the unique `floorplan`, exactly two PNG `floorplan_page` entries, and no other `floorplan_page` entries. A DXF preview remains `other`.
5. Selecting page 2 proves binding through measurable assertions: the recorded source hash, decoded dimensions, sanitized embedded pixels and overlay source binding correspond to page 2 and differ from page 1. Repeated output is deterministic.
6. Missing inventory references, `style_reference`, `other`, raw PDF, and a `floorplan_page` entry whose bytes are not PNG each produce `PARSE_SOURCE_UNSUPPORTED`, CLI 2, and no finalized derived run.
7. Existing direct PNG and JPEG `floorplan` annotation paths still succeed.
8. Annotation and inventory hash mismatches still produce `PARSE_SOURCE_HASH_MISMATCH`; this amendment must not collapse them into “unsupported.”
9. The complete test suite and contract-version tests pass; `pyproject.toml` and `uv.lock` remain unchanged.

The original “source-aligned overlay” criterion lacks a standalone automated oracle, and “byte-identical to committed state” is self-referential unless pinned to an external digest. The replacements above make both testable.

## Decisions on the four questions

1. **Choose Option A, the new `floorplan_page` kind.** It is clearer than an optional `role`, avoids conflicting classification fields, and is additive when introduced as project-manifest 1.1.0 with the historical schema frozen.

2. **Refute the orchestrator’s literal “no gain” claim.** A forged manifest currently exposes exactly one `floorplan`; the new token permits multiple arbitrary entries to remain annotatable while preserving that unique floorplan identity. F-12 proves that manifest authenticity is already absent, but it does not prove that the new allowlist adds no capability. This is acceptable only when documented as the explicit residual trust boundary above. Option C would be equally forgeable and would not solve it.

3. **Keep the DXF preview excluded.** It is a vector rendering, not the pixel surface identified by an annotation. Current code has no DWG SVG preview; future CAD previews should remain excluded.

4. **The enum widening itself is additive; reusing bundle 1.1.0 would be non-additive version mutation in disguise.** Project-manifest 1.1.0 plus bundle 1.2.0, with all historical files and artifacts preserved, satisfies ADR-0002 and ADR-0005’s forward-only rule.

## Option D and escalation

The orchestrator was right to proceed with the contract-change route. Moshe explicitly selected that route, and delegation did not authorize silently reversing it merely because deferral is cheaper. The draft disclosed Option D’s cost advantage clearly. No additional escalation was required before drafting; selecting D now would require a new decision because it removes a capability PLAN-002 presently promises.

Read-only review only: no repository files were changed and no implementation or test execution was performed.
