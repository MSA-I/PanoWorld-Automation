<!-- Archived verbatim by the orchestrator. No changes to the reviewer's text.

  task: NA-7, independent cross-provider review of the AC-13 provenance enumeration draft
  provider: openai
  requested_model: gpt-5.6-sol
  actual_model_id: gpt-5.6-sol per the launch configuration; the reviewer reports that its own
         session metadata did not expose the model id or effort to it, and it declined to invent
         them. The orchestrator's launch used -m gpt-5.6-sol with model_reasoning_effort=xhigh.
  route: Codex CLI 0.144.6, `codex exec --sandbox read-only --disable hooks`
  subject: evidence/PLAN-002/decisions/ac13-provenance-enumeration-draft-20260811.md
  verdict: APPROVE_WITH_CHANGES

WHY THIS REVIEW EXISTS. AC-13 has been CANNOT_VERIFY across three independent reviews because
PLAN-002 never enumerated what provenance it requires. The orchestrator drafted the enumeration
under Moshe's delegation of 2026-08-10; the delegation moved the decision, not the approval, so an
opposite-provider reviewer rules on the text.

WHAT IT CAUGHT IN THE ORCHESTRATOR'S DRAFT, recorded because the draft was wrong and the record
should say so:
  * a factual error - the draft required room provenance to preserve "the same vertex count and
    order as the emitted polygon", but src/pwa/floorplan/normalize.py deliberately rotates and
    sometimes reverses room vertices, so the clause would have failed the implementation it was
    written to describe;
  * a structural error - the draft added a second definition to section 6 while section 9 already
    carries provenance bullets, which would have left two competing requirements. The reviewer
    requires the definition to live in section 9 with a cross-reference from section 6;
  * an over-broad rationale - the draft's blanket ban on synthesised provenance would also have
    outlawed the DXF opening centre, which is a deterministic midpoint. The correct distinction is
    that a deterministic locator may be recorded while a derived annotation span may not be
    labelled as source-supplied;
  * an addendum that failed open - the draft said `texts` was out of scope, which leaves an
    accidental non-empty `texts` unconstrained. The reviewer requires it absent or empty, with a
    non-empty array failing AC-13.

With its replacement wording it would mark AC-13 MET on the current implementation, which would
close a criterion that three reviews could not decide.
-->

VERDICT: APPROVE_WITH_CHANGES

Runtime provider: OpenAI  
Exact model id: not exposed in this session metadata  
Reasoning effort: not exposed in this session metadata

## Required replacement wording

Do not add a second, potentially conflicting definition to section 6. Add only this cross-reference there:

> All adapters MUST emit the Required Entity Audit Metadata defined in section 9.

Replace section 9’s existing provenance bullets with:

> **Required Entity Audit Metadata.** In every PLAN-002 Part 1 runtime output, every emitted wall, room and opening MUST carry:
>
> 1. `id`: the stable quantised identity defined in section 7.
> 2. `confidence`: a number in `[0, 1]`, calculated under this section’s confidence rules.
> 3. `provenance.source_kind`: exactly `dxf` or `annotation`.
> 4. `provenance.source_ref`: a reference resolving to the originating construct in the source artifact bound through the parse artifact’s `inputs` and derived manifest:
>    - DXF: layout token, layer token and entity handle. The reserved literal `Model` and approved `PWA-*` layer names may appear; every other client-authored layout or layer name MUST be replaced by an opaque token.
>    - annotation: the array name and index in the validated annotation document.
>    - `source_ref` MUST NOT contain client free-text, a source filename, an absolute/private path or a user name.
> 5. Source geometry in the source coordinate system and units—declared accepted DXF units (`mm`, `cm` or `m`) for DXF and pixels for annotation:
>    - wall: `source_start` and `source_end`, preserving the source endpoints;
>    - room: `source_polygon`, preserving the extracted source vertices in source order. It is not required to have the emitted polygon’s order. Applying `payload.normalization` and section 7’s terminal-vertex, winding and rotation rules MUST reproduce the emitted polygon;
>    - opening: `source_center`, using the annotation’s declared centre or, for DXF, the deterministic midpoint of the source span. `source_span` MUST be present if and only if the source construct directly supplies span endpoints. DXF openings therefore carry it; annotation openings do not. A span derived from annotation centre, width and wall direction MUST NOT be recorded as `source_span`.
>
> `payload.normalization` MUST be present whenever any wall, room or opening is emitted. It is the single transform applicable to all entity provenance in that payload; no per-entity transform reference is required. Applying it together with the applicable sections 6 and 7 rules to the construct selected by `source_ref` MUST reproduce the emitted geometry.
>
> `payload.texts` MUST be absent or empty in PLAN-002 Part 1. A non-empty `texts` array fails AC-13. If a later part emits text entities, their provenance requirements and schema support MUST be approved before AC-13 is claimed for them.
>
> `provenance` and `normalization` remain optional in the additive `floorplan_parse` schema. They are mandatory in PLAN-002 runtime outputs under this plan. Schema validity alone therefore does not satisfy AC-13: an emitted wall, room or opening missing the metadata above fails AC-13.
>
> Entity provenance is descriptive, not an integrity or authenticity mechanism. Source identity and hashes are established at artifact scope through the envelope inputs, derived manifest inventory and, for annotation, the bound annotation artifact. Private Layer B provenance remains untracked under sections 12 and 13.

Replace AC-13 with:

> AC-13: parse and assumptions validate against their exact declared schemas; required artifact and overlay hashes recompute; `payload.normalization` is present whenever geometry is emitted; every emitted wall, room and opening satisfies section 9’s Required Entity Audit Metadata; and `payload.texts` is absent or empty.

## Rulings

1. **The property is correct.** Provenance should let a reviewer locate the originating construct and reproduce the source-to-normalised mapping without rerunning the parser. Timestamp, adapter version and source hash do not belong on every entity.

2. **The conditional `source_span` is correct.** Annotation span endpoints would be reconstructed geometry, not source span provenance. They may be derived during an audit, but must not be stored under `source_span`.

3. **This is fundamentally a genuine requirement, not merely implementation dressed as one.** It follows from D-012’s source-traceability requirement and applies coherently across both adapters. However, the “same vertex count and order as the emitted polygon” sentence is fixture-shaped and incorrect: `src/pwa/floorplan/normalize.py:75-82` and `:255-265` deliberately rotate and sometimes reverse room vertices.

4. **The draft’s absolute anti-synthesis rationale is too broad.** DXF provides a span, while `src/pwa/floorplan/dxf_worker.py:158-167` derives its centre. The correct distinction is that a deterministic locator such as the midpoint may be recorded, but a derived annotation span must not be mislabelled as source-supplied span geometry.

5. **Both addendum findings are factually correct, but they are not sufficient as written.**
   - A1 must fail closed: merely saying the parser currently emits no texts leaves accidental non-empty `texts` outside the enumeration.
   - A2 correctly states that the plan, not schema validation alone, makes provenance mandatory. The schema confirms this at `schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json:131-220`.

6. **No per-entity timestamp, adapter version, source hash or transform identifier is required.**
   - Timestamp and producer are envelope-level data.
   - Source identity and hashes are run/artifact-level lineage.
   - One `payload.normalization` block applies to the whole payload.
   - An adapter/build version would improve exact reproducibility, but it is not needed to audit an entity back to its source. If required later, it belongs in producer/run metadata.

7. **There is no conflict with GC3-6 or section 12.** The proposed structural/tokenised references strengthen GC3-6. Coordinates are necessary runtime geometry, but private Layer B provenance must remain outside tracked evidence.

## AC-13 decision

As drafted, I would **not** mark the implementation MET: the literal room-order clause conflicts with section 7 and the implementation, and adding the block to section 6 without replacing section 9 leaves competing opening requirements.

With the replacement wording above, AC-13 is decidable, and I would mark the current implementation **MET** based on the inspected implementation and retained evidence:

- `src/pwa/floorplan/normalize.py:238-267` emits wall and room provenance;
- `src/pwa/floorplan/normalize.py:327-345` emits opening provenance with conditional span;
- `src/pwa/floorplan/builder.py:934-987` serialises it on every emitted wall, room and opening;
- the builder emits no `texts`;
- the previous independent review found the plan enumeration to be the remaining AC-13 blocker after validation and hash recomputation were enforced.

No files were modified and no Git operation was performed.
