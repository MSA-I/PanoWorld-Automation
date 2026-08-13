# PLAN-002RF WP2 — Additive contracts and lifecycle — working plan

- Task: `t_0fc0a9e4`
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Parent: `t_2f261417` (WP1 corpus/evaluator lock) — DONE, evidence-bound at `75b0c7b`.
- Status: executing under Moshe's full-campaign authorization (2026-08-13).

## 1. Scope statement

WP2 authors the **additive, new-runs-only contracts and lifecycle** that the future
Product A (`cad_exact`) and Product B-AUTO (`raster_auto`) recognizers (WP3/WP4) will
emit, without changing any historical byte and without activating any route.

This is the contract-design/review work named by ADR-0006 decision 10 ("exact
schema/catalog/bundle/code shapes remain blocked pending contract design/review")
and U-9 ("no schema/catalog/bundle/error version is chosen"). WP2 chooses them.

Deliverables:

1. **Exact schema/catalog/bundle/error versions** — a single source of truth for the
   contracts bundle version, a frozen schema catalog that already keys by
   `(schema_id, schema_version)`, and a version-gate that explains old-consumer
   rejection predictably.
2. **`cad_exact` / `raster_auto` authorship** — the `source_class` vocabulary and the
   producer/author model that distinguishes human-authored annotation/DXF-parse from
   recognizer output. Product authorship is limited to `cad_exact` and `raster_auto`
   (ADR-0006 decision 2); human-created truth is never product output.
3. **Native lines/arcs/bulges + thickness/area semantics** — the additive geometry
   envelope for straight segments and bounded circular arcs (bulge), sourced wall
   thickness, and room area (centreline basis), per ADR-0006 decision 4.
4. **`passage`** — the third opening type alongside `door`/`window`, matching WP1's
   frozen support taxonomy and the FX1 spatial design.
5. **Immutable recognition provenance** — a `floorplan_review` artifact carrying the
   recognizer's read-only provenance and lineage.
6. **`floorplan_review` lineage + current-head invalidation** — a review chain whose
   `current_head` is invalidated when any reviewed artifact changes.
7. **Append-only blocking topology codes** — `RECOGNITION_*` / `REVIEW_*` vocabulary
   in `contracts/error_codes.md`, append-only, no severity mutation.
8. **Historical byte preservation + predictable old-consumer rejection** — 1.0.0 and
   1.1.0 schemas, manifests, examples, and finalized runs remain byte-identical; a
   doc carrying the new additive fields is predictably rejected by an older
   `additionalProperties:false` consumer, with a machine-readable reason.

Hard boundary (unchanged): local-only; no H200/GPU/cloud/remote, no spend, no G7/G8,
no Product C, no PLAN-003, no route activation, no dependency install, no push.

## 2. Model & provider provenance (recorded, not inferred)

- Active runtime (this session): `deepseek/deepseek-v4-pro-0813` via `openrouter`
  (`profiles/panoworld/config.yaml → model.default/provider`). `fallback_providers: []`.
- OmniRoute gateway `Local (127.0.0.1:20128)` probes live (`GET /v1/models` → 200,
  exposes `auto/best-*`, `auto/pro-*`). It is reachable but is NOT the active routing
  for THIS session. No OmniRoute/Anthropic model substitution is claimed here.
- Implementer = `deepseek/deepseek-v4-pro-0813` via `openrouter`.
- Independent review follows D-009 interim policy (2026-08-13): a SEPARATE qualified
  reviewer session via OmniRoute; if no second provider is provable, record
  `SAME-PROVIDER EXCEPTION` and keep the review read-only and deterministic. WP2
  contains no NEW spatial/geometry design beyond freezing the already-approved
  FX1/opus spatial truth (WP0) and WP1 evaluator/support taxonomy into contract
  shapes — no novel geometry reasoning is produced, so no Anthropic-Opus spatial
  review gate is newly triggered.

## 3. Design (what changes, what stays byte-identical)

### 3.1 Versions

- `CONTRACTS_BUNDLE_VERSION`: `1.2.0` → `1.3.0`. Single source of truth moved to
  `src/pwa/contracts.py`; `src/pwa/intake.py` re-exports it (no behavior change for
  existing manifests — finalized historical manifests keep their recorded `1.2.0`).
- New schema files (additive only):
  - `schemas/floorplan_parse/v1/floorplan_parse-1.2.0.schema.json`
  - `schemas/floorplan_review/v1/floorplan_review-1.0.0.schema.json`

### 3.2 `floorplan_parse` 1.2.0 additions (each optional/additional, additive)

- `payload.source_class`: enum `["cad_exact","raster_auto","annotation","dxf"]`;
  records the producing pipeline class. `annotation`/`dxf` = existing PLAN-002 path;
  `cad_exact`/`raster_auto` = future Product A/B. Human-authored truth is never
  emitted with a product `source_class`.
- `payload.walls[]`: optional additive `kind` (`segment`|`circular_arc`) with an
  optional `arc` sub-object (`center`, `radius_m`, `start_deg`, `end_deg`, `bulge`,
  `sweep`) and an additive `thickness_m` (sourced, `>0`). Existing `start`/`end`
  segment walls remain valid and default to `kind:segment`.
- `payload.openings[]`: `type` enum extended with `passage`; additive optional
  `source_span` already exists via provenance. `passage` span bound ≤ 3.0 m is a
  validation-level (not schema-level) frozen bound (WP1 taxonomy).
- `payload.rooms[]`: additive optional `area_m2` (`>0`, centreline-basis shoelace).
- All additive fields are OPTIONAL so 1.1.0 documents remain valid under 1.2.0, and
  the 1.0.0/1.1.0 schemas are never edited (byte-identical, hash-pinned by tests).

### 3.3 `floorplan_review` 1.0.0 (new)

- Immutable, append-only review-chain artifact: `review_id`, `reviewed_artifact`
  (artifact_id + content_hash + provenance), `verdict` (`APPROVE`|`APPROVE_WITH_FIXES`|
  `NEEDS_REWORK`|`BLOCKED`), `findings[]` (stable IDs + severity), `reviewer`
  (agent/provider/model/effort, cross-provider flag), `lineage` (parent review_id +
  current_head), and `invalidated_by` (a new head) — current-head invalidation
  semantics: a review is superseded, never edited.

### 3.4 Append-only topology/recognition error codes

Add to `contracts/error_codes.md` (append-only, no existing-row edit):
- `RECOGNITION_SOURCE_CLASS_INVALID` (error)
- `RECOGNITION_UNSUPPORTED_TAXON` (error)
- `RECOGNITION_ARC_NO_SAGITTA_BOUND` (error)
- `RECOGNITION_ARC_BULGE_SWEEP_MISMATCH` (error)
- `RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND` (error)
- `RECOGNITION_THICKNESS_MISSING` (error, sourced thickness required for product output)
- `REVIEW_LINEAGE_CYCLE` (error — review chain self-reference fails closed)
- `REVIEW_CURRENT_HEAD_STALE` (error — review head no longer current)
- `SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER` (error — old-consumer rejection, explained)
All are errors (fail-closed); none warn. Meanings are fixed; changing them needs an ADR.

### 3.5 Old-consumer rejection (predictable + explained)

A `pwa.contracts.contract_rejection_reason(doc, consumer_schema_version)` helper
returns a machine-readable reason when a doc declared against a newer schema would be
rejected by an older consumer (unknown schema_version → `SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER`;
unknown additive field on an `additionalProperties:false` entity → the same code with
the field/JSON-path). Purely diagnostic; it never mutates the doc.

## 4. Implementation plan (TDD)

All code changes follow RED→GREEN. New files:

- `schemas/floorplan_parse/v1/floorplan_parse-1.2.0.schema.json`
- `schemas/floorplan_review/v1/floorplan_review-1.0.0.schema.json`
- `src/pwa/contracts.py` additions: `CONTRACTS_BUNDLE_VERSION`, `contract_rejection_reason`.
- `src/pwa/floorplan/recognition.py` (new): frozen `source_class` vocabulary, arc/bulge
  invariant checks, passage-span bound, current-head invalidation helpers — pure, no I/O.
- `tests/unit/test_wp2_contracts.py` (new) — RED then GREEN over migration, round-trip,
  negative version/catalog, lineage, rejection, byte-identity, determinism.

No dependency is installed. No existing `schemas/` / `contracts/` file is edited except
the append-only rows appended to `contracts/error_codes.md`.

## 5. Acceptance (from task body)

- migration / round-trip / negative / lineage / concurrency / security / determinism
  tests pass (RED→GREEN per contract change).
- historical byte-identity proven (1.0.0/1.1.0 schema + example hashes pinned).
- independent read-only review (per D-009 interim policy) returns APPROVE or
  APPROVE_WITH_FIXES with all fixes closed.
- routes default-off; no activation.

## 6. Evidence & handoff

- `evidence/PLAN-002RF/WP2/` — run report, targeted + full-suite logs, an
  evidence index bound to the exact checkpoint, and `HANDOFF-WP2-to-WP3.md`.
- Git checkpoint on `main` (local commits only; no push).
