<!-- NA-7 draft: enumerate what AC-13 requires provenance to contain. Authored by the
     orchestrator under Moshe's delegation of 2026-08-10. NOT approved: PLAN-002 section 20 makes
     plan text a gate and docs/04 says the sole author is not the final approver, so this goes to
     an independent cross-provider reviewer before it is applied. Repository-relative paths only. -->

# NA-7 — draft amendment: what AC-13 requires provenance to contain

## Why this exists

AC-13 reads, verbatim from `docs/plans/PLAN-002-floorplan-parsing.md:400`:

> AC-13: parse and assumptions validate, hashes recompute, and PLAN-002-required provenance is
> present on every emitted entity.

Three consecutive independent reviews have marked AC-13 **CANNOT_VERIFY**, each for the same
reason, most recently in
`evidence/PLAN-002/reviews/independent-anthropic-rework4-review-20260811.md`: the criterion refers
to "PLAN-002-required provenance" and **PLAN-002 never says what that comprises**. So no reviewer
can decide it and no amount of code can close it. The last reviewer's words: "This is closable by
writing the enumeration into the plan, not by more code."

## The honesty problem with writing this amendment

The enumeration below could be written by reading what the code already emits and calling that the
requirement, which would convert a real open question into a rubber stamp. So it is written the
other way round: from the **property provenance exists to provide**, and then checked against the
implementation. Where the two disagree, that is stated rather than smoothed over.

**The property.** Provenance exists so that a reader holding only the derived run and the source
artifact can answer, for any single emitted entity, three questions without re-running the parser:
which source construct produced this entity, where that construct was in the source's own
coordinates, and how confident the pipeline is in the result. That is what makes the normalisation
transform auditable and what makes a wrong wall traceable to the line that caused it.

## Proposed amendment text

Add to PLAN-002 section 6, and reference it from AC-13:

> **Required provenance.** Every entity emitted in `parse/floorplan_parse.json` — every wall, room
> and opening — carries:
>
> 1. `id`: the stable quantised identity defined in section 7.
> 2. `confidence`: a number in [0, 1].
> 3. `provenance.source_kind`: exactly one of `dxf` or `annotation`.
> 4. `provenance.source_ref`: a reference to the originating source construct, expressed in the
>    tokenised vocabulary section 6 requires — for DXF, layout, layer and entity handle with any
>    client-authored layout or layer name replaced by its opaque token; for an annotation, the
>    array and index in the validated document. A `source_ref` must never contain client free-text.
> 5. The entity's geometry **in the source's own coordinate system and units** — millimetres or the
>    declared DXF unit for `dxf`, pixels for `annotation` — so that the transform recorded in
>    `normalization` can be re-applied and checked by hand:
>    - a wall carries `source_start` and `source_end`;
>    - a room carries `source_polygon`, with the same vertex count and order as the emitted polygon;
>    - an opening carries `source_center`, and additionally `source_span` **if and only if the
>      source expressed the opening as a span**. A DXF opening is drawn as a line and therefore has
>      a span; an annotation opening is declared as a centre plus `width_m` and has none.
>      Synthesising a span for an annotation opening is forbidden: provenance may not contain
>      geometry the source never expressed.
>
> Provenance is descriptive, not authoritative: it records where an entity came from and does not
> authenticate that source. Nothing in provenance may be used as an integrity or authenticity check.

## Check against the implementation

Measured, not assumed — read out of two runs produced on 2026-08-11, one per adapter, from the same
building (`evidence/PLAN-002/visual-gate/harness-summary.json` describes the pair):

| Entity | DXF adapter | Annotation adapter | Matches the requirement |
|---|---|---|---|
| wall | `source_kind`, `source_ref` `dxf:Model/PWA-WALL#37`, `source_start`, `source_end`, `id`, `confidence` 1.0 | same fields, `source_ref` `annotation:walls[8]`, `confidence` 0.9 | yes |
| room | + `source_polygon` (6 vertices, matching the emitted polygon) | same, `source_ref` `annotation:rooms[2]`, `confidence` 0.6 | yes |
| opening | + `source_center`, `source_span` | `source_center` only, **no** `source_span` | yes, under the "if and only if the source expressed a span" clause |

So the implementation already satisfies the enumeration, and the one asymmetry between adapters —
the missing `source_span` on annotation openings — is the reason clause 5 is written as a
conditional rather than a flat requirement. That asymmetry is a fact about the two source formats,
not a defect, and a flat requirement would have forced an implementer to fabricate a span.

## What the reviewer is asked to rule on

1. Is the stated property the right one, or is provenance meant to carry something else this
   enumeration omits — a timestamp, the adapter version, the source artifact's hash?
2. Clause 5's conditional `source_span`: correct, or should the plan instead require a span
   uniformly and have the annotation adapter derive one from `center` and `width_m`? The
   orchestrator's position is that derivation would be fabricated provenance and the conditional is
   right. Rule on it.
3. Is this enumeration a genuine requirement or a description of the implementation dressed as one?
   You have the code and the runs; say so if it is the latter.
4. With this text in the plan, is AC-13 decidable, and on the current implementation would you mark
   it MET?
5. Does anything here conflict with GC3-6's tokenisation rule or with section 12's privacy rule?

## Not in scope

This amendment says nothing about `assumptions.json`, about hash recomputation, or about the
`normalization` block — AC-13's other clauses. Those are already decidable as written: hash
recomputation is enforced at finalisation by `verify_run_derived_artifacts`, which NA-3f confirmed,
and schema validation is enforced by `_artifact`.

---

## Addendum, appended after checking the draft against the schema itself

Appended rather than folded in, because this file is committed evidence. Two gaps in the text above,
found by the orchestrator reading `schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json`
rather than by a reviewer.

### A1 — `texts` exists as an entity array and the enumeration ignored it

AC-13 says "every emitted entity". The payload has a fourth array, `texts`, which the text above
does not mention. Checked:

- `texts` items are typed `required: ["text"]` with properties `text`, `bbox`, `confidence` — and
  **no `provenance` property at all.** A text entity cannot carry provenance under the current
  schema even if something wanted it to.
- The parser never emits `texts`: no source file references it, and both of the 2026-08-11 runs
  omit the key entirely. Part 1 has no OCR, by design (ADR-0004).

So the enumeration is scoped to **walls, rooms and openings**, and that scope should be stated in
the amendment rather than left implicit. Proposed added sentence:

> This enumeration applies to every emitted wall, room and opening. `texts` is out of scope for
> Part 1: the parser emits none, and the schema gives a text item no provenance property. If a later
> part emits text entities, this enumeration must be revisited before AC-13 is claimed for them.

### A2 — the schema makes provenance optional; the plan is what makes it mandatory

For walls, rooms and openings the schema's `required` lists are `id`, geometry and `confidence`.
**`provenance` is not required by the schema.** So a parse artifact with no provenance at all is
schema-valid, and AC-13 is the only thing that forbids it.

That is not a defect to fix in the schema — a permissive optional field is the right shape for an
additive contract, and 1.0.0 had no provenance at all, so requiring it would have broken forward
reading. But it means the amendment must say plainly that the plan, not the schema, is the binding
source for this criterion, and that a reviewer checking AC-13 must check the artifact against the
plan text and not merely run the validator. Proposed added sentence:

> `provenance` is an optional property in the `floorplan_parse` schema, deliberately, so that the
> additive contract can still read artifacts produced before it existed. This criterion is
> therefore binding on the plan and not on the validator: a schema-valid artifact missing provenance
> fails AC-13.

Both additions strengthen the draft rather than change its substance, and the reviewer should judge
the amendment with them included.
