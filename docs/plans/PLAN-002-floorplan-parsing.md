# PLAN-002 — Floorplan Parsing

- Plan ID: `PLAN-002-floorplan-parsing`
- Status: **`PLANNED (revision 2)`** — explicitly approved by Moshe on 2026-08-09; the later AC-20 source-hash and source-quality/scale clarifications were also explicitly approved on Kanban `t_b7ade39e`. Implementation remains bounded by this PLAN and ADR-0004/ADR-0005.
- Revision 2 (2026-08-10) — two §20 retained Geometry/Contract clauses amended, each with Moshe's explicit approval of the changed wording, following the independent OpenAI `gpt-5.6-sol` review of the rework:
  1. §6 DXF table, `PWA-DOOR`/`PWA-WINDOW`: opening width is now the span **projected onto the matched wall direction**, computed after wall resolution succeeds, rather than the raw drawn span length. The reviewer showed the raw length diverges without bound as the span shortens — a 0.05 m span within the 0.02 m endpoint tolerance projects to 0.03 m, a 67% excess — and can flip `PARSE_OPENING_WIDTH_EXCEEDS_WALL` even at 0.9 m. Because `width_m` feeds canonical geometry and stable entity IDs, this is a §20 gate, approved by Moshe on 2026-08-10.
  2. §10 overlay contract: the raster overlay now embeds only decoded pixel data, stripped of EXIF and every other metadata block, while binding the SHA-256 of the **original** source bytes. Previously the source bytes were embedded verbatim, so a JPEG's EXIF — including GPS coordinates and author name — reached `parse/overlay.svg`, which §12 forbids. Approved by Moshe on 2026-08-10.
- Kanban: `t_b7ade39e` (`P1-02 floorplan parsing`, board `panoworld-dev`)
- Policy: `MODEL-ROUTING-v1`
- Consumes: `HANDOFF-PLAN-001-to-PLAN-002-001`, contracts bundle `1.0.0`
- Produces: G1 evidence (`floorplan_parse`, `assumptions`, source-aligned `overlay_svg`)
- Boundary: **Part 1 local only**. G7/G8, H200/GPU, remote and cloud remain **DEFERRED TO PART 2**.

## 1. Goal

Build a deterministic, local, reviewable bridge from a finalized PLAN-001 intake run to a new immutable parse run. Part 1 supports exactly two inputs behind one interface:

1. a deliberately narrow DXF convention; and
2. schema-validated manual annotation for raster inputs.

Both paths must produce schema-valid `floorplan_parse.json`, `assumptions.json`, and a source-aligned SVG overlay. They must agree on a canonical geometry projection, while retaining adapter-specific confidence and provenance.

The plan intentionally proves contracts, validation, traceability and G1 evidence before selecting or modernizing a raster ML parser.

## 2. Scope

- New `src/pwa/floorplan/` package: source protocol, DXF adapter, annotation adapter, normalizer, geometry validator, overlay renderer, parse-run builder and CLI.
- New annotation input schema `floorplan_annotation` 1.0.0.
- Additive `floorplan_parse` 1.1.0 proposal for entity provenance and normalization metadata.
- Version-aware contract lookup so 1.0.0 and 1.1.0 remain independently valid.
- Append-only `PARSE_*` vocabulary.
- Synthetic fixtures, golden artifacts, failure fixtures, tests and evidence.
- A new immutable **derived parse run**; no write to a finalized PLAN-001 run.
- A bounded update to future intake manifests from contracts bundle 1.0.0 to 1.1.0 after D-012 approval, and from 1.1.0 to 1.2.0 after the approved GC3-8 amendment. Existing manifests are never rewritten.
- Planning records, independent cross-provider review and a human approval gate.

## 3. Non-goals

- No OCR, learned raster parser, VLM/LLM runtime, CubiCasa5K, FloorplanToBlender3d, model weights, downloads, clones or network access.
- No DWG entity parsing. DWG remains intake-only until a separately approved conversion strategy exists.
- No Blender, 3D geometry, cameras, rendering, style, packaging, PanoWorld execution, GPU or cloud.
- No new dependency and no changes to `pyproject.toml` or `uv.lock`.
- No curved walls, arcs, splines, blocks, xrefs, images, hatches, multi-layout or multi-storey parsing.
- No automatic snapping, gap closing, duplicate merging, wall-thickness default or inferred room names.
- No mutation of 1.0.0 schema files, finalized runs or historical evidence.
- No merge, push, self-approval or PLAN-003 implementation.

## 4. Accepted decisions and approval boundary

Moshe explicitly approved D-004, D-012, D-013, D-014 and approval-gate items 5–8 on 2026-08-09. ADR-0004 and ADR-0005 are the canonical decision records. The recommendations below are therefore locked decisions for PLAN-002, not unresolved proposals.

### D-004 — Part 1 parser baseline

Options remain CubiCasa5K, heuristic/GPL isolation, VLM-assisted parsing, or a contract-first manual/vector baseline.

**Recommendation:** close D-004 for Part 1 as **Option D: manual annotation + deterministic validator + narrow DXF adapter**. This is an interim contract/fixture baseline, not a claim that DXF or manual annotation is the final scalable parser. Open a later decision for the production raster parser after labeled Layer B evidence exists.

Rationale:

- it releases the parse contract and G1 path without network, weights or new licensing;
- it creates golden geometry against which future adapters can be measured;
- it does not silently select a stale ML stack;
- it preserves D-010: no new dependency is introduced, but the repository-wide commercial license matrix remains open.

### D-012 — Contract evolution and exact-version validation

The current `floorplan_parse` 1.0.0 represents rooms, walls and openings, but it cannot carry per-entity source coordinates/provenance or normalization metadata because entity and payload objects reject additional properties. G1 requires source traceability for each detected component.

**Recommendation:**

1. add `floorplan_parse` 1.1.0 with optional additive fields:
   - entity `provenance` with explicit shapes per entity kind;
   - `payload.normalization`;
   - optional binding to the generated overlay by relative path and SHA-256;
2. require those optional fields in PLAN-002 runtime outputs and tests, while keeping them optional in schema for ADR-0002 additive compatibility;
3. add `floorplan_annotation` 1.0.0;
4. bump the bundle to 1.1.0 for new manifests only;
5. add `load_schema_catalog()` keyed by `(schema_id, schema_version)` and make `validate_artifact()` select the exact declared version;
6. keep `load_all_schemas()` as the compatibility view used by existing code/tests, returning one latest schema per ID; build the reference registry from **all catalog values**, never from the latest-only view;
7. add `floorplan_annotation` valid/invalid examples and update the schema-inventory test from the historical hard-coded 13 to the catalog-derived 14 current artifact IDs.

Version tests must prove:

- historical 1.0.0 artifacts validate against 1.0.0;
- 1.1.0 artifacts validate against 1.1.0;
- a 1.1.0 document is not mislabeled as 1.0.0;
- duplicate `(schema_id, schema_version)` or `$id` is rejected;
- all existing examples remain valid and byte-round-trip unchanged.

Existing finalized project manifests keep whatever bundle they declared. A derived parse run created from one of them writes a new lineage manifest under the new parse run, preserving the original hashes and declaring the current bundle — 1.2.0 after the approved GC3-8 amendment; it never rewrites the source run. Future intake runs declare the current bundle after approval.

### D-013 — Immutable run lifecycle

PLAN-001 finalizes each intake run with `os.replace(staging, final)`. PLAN-002 must not append to it.

**Recommendation:** each parse attempt creates a new derived run:

```text
runs/.staging/<parse-run-id>/
  project/source-manifest.json       # byte-copy of source artifact for audit
  project/source-quality-report.json # byte-copy of source artifact for audit
  project/project_manifest.json      # new project_manifest 1.1.0 artifact, bundle 1.2.0
  project/input_quality_report.json  # new schema 1.0 artifact for parse-run ID
  project/inputs/**                  # full verified source inventory, byte-copied
  parse/annotation.json              # annotation path only
  parse/floorplan_parse.json
  parse/assumptions.json
  parse/overlay.svg
  parse/parse-report.json
runs/<parse-run-id>/                  # atomic finalize only after all writes/checks
```

Rules:

- CLI receives `--source-run runs/<intake-run-id>` and a fresh `--parse-run-id`.
- It resolves the source run under the configured `runs_root`, rejects traversal, symlinks/reparse points in every ancestor from `runs_root` to the file, and verifies copied artifact and floorplan hashes against the source manifest before parsing.
- Parse artifacts use the new parse run ID. Their `inputs[]` bind to source artifact IDs/hashes.
- No hard link or symlink is used. Source artifacts are copied byte-for-byte for audit, and **every item** in the verified source manifest inventory (floorplan, style reference and derivatives, including a selected PDF page) is copied with `copy_immutable` to the same run-relative path under the derived run.
- The new `project/project_manifest.json` is schema `project_manifest` 1.1.0, declares contracts bundle 1.2.0, carries the new parse-run ID and artifact ID, and contains the complete copied inventory with reverified hashes. The source manifest remains byte-unchanged at its originally declared schema and bundle versions.
- The new `project/input_quality_report.json` is schema 1.0.0 with the parse-run/artifact IDs, semantically copied payload/status, recomputed hash, and a top-level input binding to the source quality report. Parsing proceeds only when this derived report is `complete` with no blockers.
- `floorplan_parse` and `assumptions` bind to the **derived** project manifest and quality report; the annotation path additionally binds to the annotation artifact ID/hash. This gives one internally consistent RUN namespace while preserving cross-run lineage through envelope inputs.
- A valid parser outcome (`complete`, `partial`, or `failed`) writes schema-valid diagnostic artifacts and finalizes as an immutable run; only `complete` is G1-eligible. An operational failure before a valid diagnostic set exists leaves `.staging/<parse-run-id>` for diagnosis and never appears as a finalized run. Every retry requires a new parse-run ID.
- Finalization is same-volume `os.replace`. Existing final or staging paths are rejected.
- Crash recovery is explicit: stale staging is reported; never auto-deleted or resumed silently.

### D-014 — G1 partial/confidence policy

The state machine marks G1 as non-human, while requirements also require intervention on low confidence or contradictions.

**Recommendation:** fail closed at the transition boundary:

- a parser may emit a `partial` artifact with findings for diagnosis;
- `partial`, any error-severity finding, or any unresolved `requires_human_ack` prevents `RUN:FLOORPLAN_PARSED`;
- a human corrects the annotation/input and starts a new derived parse run;
- only `complete` outputs with no unresolved acknowledgement satisfy G1.

This preserves the locked state machine and still requires human intervention without inventing an approval record at a non-human gate.

## 5. Input and output contracts

### Inputs

- finalized source run containing schema-valid `project_manifest.json` and `input_quality_report.json`;
- exactly one immutable floorplan listed as `kind=floorplan`;
- source quality must be `complete` with `blockers=[]`; any other source quality state is an invalid preflight contract, returns CLI 2 and creates no finalized derived run;
- a complete, blocker-free source may reach parser diagnostics with missing or contradictory scale: emit `PARSE_SCALE_UNKNOWN`, finalize the schema-valid failed diagnostic set, and return CLI 3;
- annotation path only: `annotation.json` validated before any field is used.

### `floorplan_annotation` 1.0.0

Envelope payload:

- `image`: `source_image_ref`, width/height and `sha256` bound to the immutable raster or selected intake-generated PDF page derivative;
- `scale_m_per_px`;
- `walls[]`: source-space endpoints in pixels;
- `rooms[]`: source-space polygon in pixels;
- `openings[]`: `type`, source wall reference, center in pixels and width in metres;
- `declared_dimensions[]`: two points and measured length.

The file is data only: JSON, no YAML, pickle, eval or executable content.

### Outputs

- `floorplan_parse.json`: schema 1.1.0, canonical metres, complete provenance in PLAN-002 outputs;
- `assumptions.json`: schema 1.0.0, `payload.stage="parsing"`;
- `overlay.svg`: source-aligned G1 evidence;
- `parse-report.json`: raw deterministic finding/metric **evidence**, deliberately not an envelope artifact and not entered in the schema catalog (the same class as PLAN-001's raw package-validator report).

`content_hash` uses `pwa.contracts.compute_content_hash`; JSON writing uses exclusive creation and LF endings.

## 6. Exact adapter semantics

### DXF adapter

Only modelspace, 2D entities, Z/elevation 0 and these mappings are accepted:

| Layer | Entity | Meaning |
|---|---|---|
| `PWA-WALL` | `LINE` | wall centerline; endpoints are geometry |
| `PWA-ROOM` | closed `LWPOLYLINE` | one room polygon; `closed=true`, at least 3 unique vertices, every bulge exactly 0 |
| `PWA-DOOR` | `LINE` | door span; midpoint is center, width is the span projected onto the matched wall direction, computed after wall resolution succeeds; the raw span length is not used |
| `PWA-WINDOW` | `LINE` | window span; midpoint is center, width is the span projected onto the matched wall direction, computed after wall resolution succeeds; the raw span length is not used |

- `$INSUNITS` must map to mm/cm/m and must equal the verified project-manifest units. Unknown or mismatched units fail with `PARSE_UNITS_MISMATCH`; user-supplied intake units never silently override contradictory DXF metadata at parse time.
- Every opening line must be collinear with exactly one wall segment within tolerance. Zero or multiple matches fail.
- Layer matching is case-sensitive exact ASCII. `TEXT`, `MTEXT`, `PWA-DIM`, unknown layers and unsupported entity kinds are reported, not silently interpreted. XREF/IMAGE/OLE paths are never resolved.
- The standard empty paperspace layouts may exist. Any paperspace entity, additional active/non-empty layout, `ARC`, `SPLINE`, `INSERT`, nonzero bulge or nonzero elevation fails with `PARSE_UNSUPPORTED_FEATURE`.
- Finding precedence is deterministic: containment/size/hash/schema first, then units/unsupported source semantics, then normalization, then geometry invariants, then warnings; all findings within a tier sort by `(code, source_ref)`.
- Room names and wall thickness remain absent unless explicitly represented by a future approved contract.

Disposition table:

| Source entity | Code/severity | Continue? |
|---|---|---|
| any entity on an unknown layer | `PARSE_UNMAPPED_SOURCE_ENTITY` / warn | yes; entity ignored after recording |
| `TEXT`/`MTEXT` or wrong entity kind on a known `PWA-*` layer | `PARSE_UNSUPPORTED_FEATURE` / error | finish bounded scan, then fail |
| any entity on reserved `PWA-DIM` | `PARSE_UNSUPPORTED_FEATURE` / error | finish bounded scan, then fail |
| `IMAGE`, XREF, OLE, `INSERT`, `ARC`, `SPLINE`, nonzero bulge/Z | `PARSE_UNSUPPORTED_FEATURE` / error | never resolve external data; finish bounded scan, then fail |

### Annotation adapter

- Pixel coordinates are multiplied by `scale_m_per_px`.
- An annotation selects exactly one source image through its sole `payload.image.source_image_ref`.
  Selection is exact, code-point-for-code-point string equality, after JSON decoding, with one
  `payload.inputs[].path` in the validated source manifest. No case folding, slash conversion,
  Unicode normalization, filesystem alias resolution, path-prefix inference or `derived_from`
  inference participates in selection.

  Source-manifest preflight must first require unique inventory path strings. Duplicate paths are
  an invalid source contract and fail with CLI 2 and no finalized derived run; they are not an
  annotation "multiple match."

  The selected entry must have `kind: "floorplan"` and decode as PNG or JPEG, or have
  `kind: "floorplan_page"` and decode as PNG. Raw PDF, CAD source bytes, CAD previews,
  `style_reference`, `other`, and all other formats are not annotatable. A missing reference, a
  disallowed kind, or an incompatible decoded format produces `PARSE_SOURCE_UNSUPPORTED`, CLI 2,
  and no finalized derived run.

  `floorplan_page` is a producer-contract token reserved exclusively for PNG page renders created
  by the approved intake PDF renderer from the same run's unique `kind: "floorplan"` PDF input. It
  must not be assigned to uploaded rasters, style references, DXF/DWG previews, generic
  derivatives or any other artifact.

  The parser treats the validated manifest classification as authoritative; it does not
  authenticate that classification from the path. `content_hash` is not an authenticity mechanism.
  An actor able to rewrite a source run and recompute its hashes can misclassify arbitrary PNG
  inventory entries, and `floorplan_page` increases how many such entries one forged manifest can
  expose. This is an explicit residual source-run trust-boundary limitation, not a property
  claimed to be prevented by this amendment.
- Width/height are decoded fresh from the verified image bytes (they are not read from manifest `details`) and must match annotation metadata. Scale must match the immutable source manifest.
- Raster coordinates transform from x-right/y-down to x-right/y-up using `metric_y=(height_px-y_px)*scale_m_per_px`; DXF uses native x-right/y-up. The transform and its inverse are recorded in normalization metadata.
- Annotation source references are array indices in the validated document.
- It mirrors the same primitive semantics as DXF so geometry projection can be compared.

### Common interface

```text
FloorplanSource.accepts(path) -> bool
FloorplanSource.extract(path, limits) -> RawGeometry
prevalidate_cardinality(raw) -> finding or pass
normalize(raw, source_manifest) -> NormalizedGeometry
validate(normalized) -> findings
render_overlay(normalized, source_binding) -> bytes
```

`RawGeometry` retains adapter-specific source coordinates/provenance. Immediately after `extract()`, `prevalidate_cardinality()` requires at least one wall and one room and emits `PARSE_EMPTY_GEOMETRY` before any `min()`/normalization operation. No future raster adapter stub is created in Part 1.

All adapters MUST emit the Required Entity Audit Metadata defined in section 9.

## 7. Deterministic normalization

- Convert to metres before identity or validation.
- Reject NaN, infinity, negative widths, non-2D data and values outside documented coordinate bounds.
- Quantize to `1e-4 m` with `Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)`; normalize `-0.0` to `0.0`.
- Translate so minimum wall endpoint x/y is `(0,0)`; record translation and source units. This anchor is deterministic for one complete input but can change when new geometry extends the minimum bounds.
- Walls use lexicographically ordered endpoints.
- Room polygons omit a repeated terminal vertex, must be CCW, and rotate to the lexicographically smallest vertex. Ties use the full rotated tuple, giving a total order.
- Canonical entity order uses complete geometry tuples, never only centroid or an incomplete key.
- Stable IDs are the first 12 hex characters of SHA-256 over canonical identity tuples. Collision/duplicate geometry fails; no suffix or merge.
- IDs are stable across repeated runs and input reordering. Additions that do not change the normalization anchor preserve existing IDs; an addition that moves the minimum bounds may change all IDs and is tested/documented explicitly. A real geometry edit intentionally changes the ID.

### Canonical geometry projection

Cross-path equality compares only normalized geometry fields shared by both adapters:

```text
units, rooms[geometry], walls[geometry], openings[type, wall_id, center, width]
```

It excludes created time, confidence, provenance, source scale and overlay metadata. Separate tests verify those excluded fields per adapter. The acceptance claim is equality of this canonical projection, not whole-payload byte identity.

## 8. Geometry invariants

Named limits/tolerances live in one config module and appear in `parse-report.json`:

- `QUANTUM_M = 1e-4`
- `DEGENERATE_WALL_M = 0.05`
- `OPENING_OFFSET_M = 0.02`
- `DIMENSION_TOL = max(0.02 m, abs(declared_length_m) * 0.01)`
- `MAX_DXF_BYTES = 50 MiB`, `MAX_DXF_ENTITIES = 200_000`, `MAX_ANNOTATION_BYTES = 5 MiB`
- `MAX_WALLS = 20_000`, `MAX_ROOMS = 5_000`, `MAX_OPENINGS = 20_000`, `MAX_POLYGON_VERTICES = 10_000`
- `MAX_COORDINATE_MAGNITUDE_M = 100_000`, `MAX_SOURCE_RASTER_BYTES = 50 MiB`, `MAX_SOURCE_PIXELS = 100_000_000`
- `MAX_OVERLAY_BYTES = 70 MiB`, `MAX_WORKER_STDIO_BYTES = 1 MiB`, `PARSER_TIMEOUT_S = 30`
- `LOW_CONFIDENCE_THRESHOLD = 0.5`; confidence `<0.5` is low, while exactly `0.5` is accepted.

Validation:

1. pre-normalization cardinality requires at least one wall and one room; otherwise `PARSE_EMPTY_GEOMETRY`. Post-normalization validation additionally requires at least one non-degenerate wall and one valid positive-area room;
2. room polygon has >=3 unique points, positive area, CCW and no non-adjacent segment intersection;
3. explicit DXF closure must be present; annotation polygons are closed by contract representation but still pass uniqueness/intersection tests;
4. no degenerate or duplicate wall/entity;
5. opening references exactly one wall;
6. perpendicular distance and projection are in tolerance;
7. the full opening span fits: projected center distance to **both** wall ends is at least `width_m / 2`;
8. declared dimensions match measured distance within tolerance;
9. scale matches source manifest;
10. resource limits are checked before expensive loops.

Room overlap area is not an acceptance invariant in Part 1 because robust arbitrary polygon intersection is not available in the locked dependency set. Obvious boundary intersections are reported as warnings; exact overlap metrics are deferred with a documented upgrade path.

## 9. Confidence, provenance and assumptions

Confidence is deterministic, not model-estimated:

- accepted DXF primitive: `1.0`;
- manually annotated primitive tied to a declared dimension: `0.9`;
- manually annotated primitive derived only from supplied scale: `0.6`.

There are no parser defaults that alter geometry in Part 1. If a future approved default is added, it must create a matching assumption with `requires_human_ack=true`.

**Required Entity Audit Metadata.** In every PLAN-002 Part 1 runtime output, every emitted wall, room and opening MUST carry:

1. `id`: the stable quantised identity defined in section 7.
2. `confidence`: a number in `[0, 1]`, calculated under this section's confidence rules.
3. `provenance.source_kind`: exactly `dxf` or `annotation`.
4. `provenance.source_ref`: a reference resolving to the originating construct in the source artifact bound through the parse artifact's `inputs` and derived manifest:
   - DXF: layout token, layer token and entity handle. The reserved literal `Model` and approved `PWA-*` layer names may appear; every other client-authored layout or layer name MUST be replaced by an opaque token.
   - annotation: the array name and index in the validated annotation document.
   - `source_ref` MUST NOT contain client free-text, a source filename, an absolute/private path or a user name.
5. Source geometry in the source coordinate system and units — declared accepted DXF units (`mm`, `cm` or `m`) for DXF and pixels for annotation:
   - wall: `source_start` and `source_end`, preserving the source endpoints;
   - room: `source_polygon`, preserving the extracted source vertices in source order. It is not required to have the emitted polygon's order. Applying `payload.normalization` and section 7's terminal-vertex, winding and rotation rules MUST reproduce the emitted polygon;
   - opening: `source_center`, using the annotation's declared centre or, for DXF, the deterministic midpoint of the source span. `source_span` MUST be present if and only if the source construct directly supplies span endpoints. DXF openings therefore carry it; annotation openings do not. A span derived from annotation centre, width and wall direction MUST NOT be recorded as `source_span`.

`payload.normalization` MUST be present whenever any wall, room or opening is emitted. It is the single transform applicable to all entity provenance in that payload; no per-entity transform reference is required. Applying it together with the applicable sections 6 and 7 rules to the construct selected by `source_ref` MUST reproduce the emitted geometry.

`payload.texts` MUST be absent or empty in PLAN-002 Part 1. A non-empty `texts` array fails AC-13. If a later part emits text entities, their provenance requirements and schema support MUST be approved before AC-13 is claimed for them.

`provenance` and `normalization` remain optional in the additive `floorplan_parse` schema. They are mandatory in PLAN-002 runtime outputs under this plan. Schema validity alone therefore does not satisfy AC-13: an emitted wall, room or opening missing the metadata above fails AC-13.

Entity provenance is descriptive, not an integrity or authenticity mechanism. Source identity and hashes are established at artifact scope through the envelope inputs, derived manifest inventory and, for annotation, the bound annotation artifact. Private Layer B provenance remains untracked under sections 12 and 13.

Low confidence is aggregated with `any(entity.confidence < 0.5)`. It creates `partial` output and blocks G1 under D-014. Any assumption entry with `requires_human_ack=true` also blocks G1. Because schema 1.0.0 has no resolution field, acknowledgement is represented only by corrected input and a fresh run whose assumptions no longer contain that unresolved entry; an old artifact is never mutated.

## 10. Overlay contract

The primary overlay is mandatory and source-aligned:

- raster annotation: self-contained SVG embeds only the decoded pixel data of the verified source raster as a data URI, stripped of EXIF and all other metadata blocks, and binds the SHA-256 of the **original** source bytes in metadata (never the hash of the sanitized copy, which would break the proof of which input produced the overlay);
- DXF: self-contained SVG renders the accepted source primitives and normalized detections in aligned groups from the same source coordinates;
- no external URL, script, `foreignObject` or arbitrary filesystem reference;
- untrusted labels are XML-escaped;
- layers distinguish source, walls, rooms, doors, windows, IDs, confidence and legend;
- raster SVG uses the source pixel viewBox, embeds the verified raster, and applies the exact recorded y-down↔y-up inverse transform to normalized detections; DXF SVG uses source-coordinate bounds and the inverse normalization translation/units transform;
- deterministic bounds/viewBox, ordering, numeric formatting and LF endings; no timestamp;
- source image size is bounded before base64 embedding.

The Git evidence copy may use the synthetic fixture only. Private Layer B overlays stay untracked; only redacted hashes/counts/metrics may enter Git.

## 11. Error/status/exit policy

Append-only codes:

- errors: `PARSE_SOURCE_UNSUPPORTED`, `PARSE_SCALE_UNKNOWN`, `PARSE_SOURCE_HASH_MISMATCH`, `PARSE_UNITS_MISMATCH`, `PARSE_UNSUPPORTED_FEATURE`, `PARSE_EMPTY_GEOMETRY`, `PARSE_OPEN_POLYGON`, `PARSE_SELF_INTERSECTING_POLYGON`, `PARSE_DEGENERATE_WALL`, `PARSE_DUPLICATE_ENTITY`, `PARSE_UNKNOWN_WALL_REF`, `PARSE_AMBIGUOUS_WALL_REF`, `PARSE_OPENING_OFF_WALL`, `PARSE_OPENING_WIDTH_EXCEEDS_WALL`, `PARSE_DIMENSION_INCONSISTENT`, `PARSE_RESOURCE_LIMIT`, `PARSE_TIMEOUT`;
- warnings: `PARSE_LOW_CONFIDENCE`, `PARSE_UNMAPPED_SOURCE_ENTITY`, `PARSE_ROOM_BOUNDARY_UNMATCHED`.

Decision table:

- no findings: `complete`, CLI 0, eligible for G1;
- warning only: `partial`, CLI 1, not eligible for G1;
- contract/IO/usage before artifact creation: CLI 2;
- any error finding: `failed`, CLI 3, not eligible for G1.

Approved AC-20 preflight semantics (Moshe, 2026-08-09):

- any source manifest, source quality-report, or source inventory hash mismatch discovered before parsing emits the exact `PARSE_SOURCE_HASH_MISMATCH` code, returns CLI 2, and creates no finalized derived run;
- a source quality report that is not `complete` or has any blocker is an invalid source contract, returns CLI 2, and creates no finalized derived run;
- only a schema-valid, complete, blocker-free source that then exposes missing or contradictory scale reaches `PARSE_SCALE_UNKNOWN`, finalizes a schema-valid failed diagnostic set, and returns CLI 3.

No raw stack trace or absolute/private path is emitted to user-facing artifacts.

Outcome/artifact matrix:

| Outcome | Required finalized artifacts | Overlay | CLI |
|---|---|---|---|
| complete | derived manifest + derived quality report + parse + assumptions + parse-report | required | 0 |
| partial (warnings/low confidence, usable geometry) | same diagnostic set | required | 1 |
| failed domain parse (schema-valid source reached parser; geometry may be absent) | derived manifest + derived quality report + `floorplan_parse(status=failed)` + assumptions + parse-report | required only if normalized geometry exists and render stays within cap; otherwise parse-report records `overlay_omitted_reason` | 3 |
| operational/preflight failure (usage, containment, unreadable/invalid source contract, staging create/write/fsync/rename failure, unexpected exception before a schema-valid diagnostic set) | none finalized; bounded staging may remain | not required | 2 |

A “valid diagnostic set” means every **envelope artifact** above is schema-valid and its hash recomputes; the raw non-artifact `parse-report.json` is deterministic JSON with a tested internal shape and names the terminal finding, but is not claimed to be schema-valid. `PARSE_RESOURCE_LIMIT`/`PARSE_TIMEOUT` after validated preflight are failed-domain outcomes and finalize without overlay when rendering is impossible. Failure to serialize/validate that diagnostic set is operational and remains staging/CLI 2.

## 12. Security and resource boundaries

- Parse only a finalized source run below an explicit `runs_root`.
- Resolve containment and reject symlink/reparse points in the full ancestor chain.
- Bind manifest, quality report and floorplan bytes by SHA-256 before parsing.
- Enforce file-size limits before JSON/DXF parsing.
- DXF parser runs in a subprocess with the numeric timeout above; entity limits are post-load protection and are not misrepresented as pre-parse protection. The worker is forbidden to spawn children; the parent uses OS-specific stdlib/process-group termination to kill the worker tree on timeout and captures stdout/stderr through capped temporary files, never unbounded pipes.
- Part 1 has no portable hard RSS/memory limit on Windows. This residual risk is explicit; byte/pixel/count/time/output caps bound normal work, and any hard-memory sandbox is deferred rather than falsely claimed.
- Never resolve XREF/IMAGE/OLE or external hrefs.
- Annotation is schema-validated before use.
- SVG has no executable/external content and escapes all untrusted text.
- No network, secrets, source names, absolute paths, EXIF or user names in artifacts/evidence.
- Final outputs use exclusive writes and atomic staging-to-final rename.

## 13. Fixtures, metrics and licensing

### Layer A — synthetic, tracked

Project-created rectangle-based plan with walls, rooms, two doors and two windows:

- DXF following the exact convention;
- PNG source;
- annotation JSON;
- golden parse, assumptions and source-aligned overlay;
- explicit project-generated provenance notice (not a claim that the repository has a root distribution license).

Failure matrix covers every error code and representative warnings, including boundary cases for quantization, opening span, ambiguous wall match, nonzero bulge/Z, hostile labels, XREF/IMAGE, resource limits and timeout.

### Layer B — private, untracked

Optional real-plan smoke requires Moshe to attest that the file is non-sensitive and that he has the right to use it. Git receives only a redacted evidence record with hashes, counts and metrics; no file name, path, content or overlay.

Layer B without labeled ground truth is a smoke test, not accuracy evidence. Part 1 therefore does **not** claim precision/recall closure for an automatic raster parser. It measures exact geometry agreement only on labeled synthetic Layer A. Production parser accuracy remains a later decision.

### Licensing

No dependency or third-party dataset is added. Existing project-wide commercial licensing risk remains under D-010; the plan does not claim “zero licensing risk.”

## 14. Acceptance criteria

### Contracts and immutability

- AC-1: exact-version schema lookup validates historical 1.0.0 and new 1.1.0 artifacts without collision.
- AC-2: all existing contract examples and PLAN-000/001 tests remain green.
- AC-3: existing finalized source run bytes and hashes are unchanged after success and every failure path.
- AC-4: derived parse run finalizes atomically; existing IDs/paths, stale staging and overwrite attempts fail safely.
- AC-5: crash before finalization leaves only staging; no automatic delete/resume.

### Parsing and invariants

- AC-6: both adapters emit the same canonical geometry projection for Layer A.
- AC-7: adapter-specific confidence, provenance and source scale are correct and intentionally differ where appropriate.
- AC-8: stable IDs survive reruns and input reordering; additions preserve IDs only when the normalization anchor is unchanged. A fixture that extends the minimum bounds proves/documentedly permits the expected ID change; duplicates fail.
- AC-9: every room passes uniqueness, area, winding and self-intersection rules.
- AC-10: every opening references exactly one wall, lies on it and fits by half-width at both ends.
- AC-11: every declared dimension and source scale passes configured tolerance or fails with the exact code.
- AC-12: unsupported DXF semantics fail loudly; unknown layers are reported, never dropped silently.

### G1 evidence

- AC-13: parse and assumptions validate against their exact declared schemas; required artifact and overlay hashes recompute; `payload.normalization` is present whenever geometry is emitted; every emitted wall, room and opening satisfies section 9's Required Entity Audit Metadata; and `payload.texts` is absent or empty.
- AC-14: source-aligned overlay shows source and detections, is deterministic byte-for-byte, XML-valid and contains no active/external content.
- AC-15: hostile labels are escaped; private source data never enters tracked evidence.
- AC-16: warning/partial/unresolved acknowledgement cannot pass G1; corrected input requires a fresh run.

### Security and limits

- AC-17: traversal, ancestor reparse point and source hash mismatch fail before parsing.
- AC-18: over-size input fails pre-parse; timeout/entity/vertex/count limits fail with exact codes.
- AC-19: XREF/IMAGE/OLE never open external paths.

### Quality gates

- AC-20: failure decision table tests exact code, severity, finalized-artifact presence/status and CLI exit code, including all three approved preflight cases above: every pre-parse source hash mismatch is `PARSE_SOURCE_HASH_MISMATCH` + CLI 2 + no finalized derived run; incomplete/blocked source quality is CLI 2 + no finalized derived run; complete/blocker-free but missing or contradictory scale is `PARSE_SCALE_UNKNOWN` + failed diagnostic set + CLI 3.
- AC-21: full pytest suite passes; `git diff --check` passes.
- AC-22: `pyproject.toml` and `uv.lock` dependencies remain unchanged.
- AC-23: no H200/GPU/remote/cloud/network action occurred; G7/G8 remain deferred.

## 15. TDD and evidence plan

Implementation order after approval:

1. red tests for exact-version schemas and immutable derived-run lifecycle;
2. schemas/catalog implementation;
3. synthetic fixtures and annotation validation;
4. normalization and stable IDs;
5. invariant validator;
6. source-aligned overlay;
7. DXF and annotation adapters;
8. CLI/run finalization and failure matrix;
9. full regression, independent code/spatial review and handoff.

Test files:

```text
tests/unit/test_contract_versions.py
tests/unit/test_floorplan_normalize.py
tests/unit/test_floorplan_validate.py
tests/unit/test_floorplan_overlay.py
tests/unit/test_floorplan_sources.py
tests/integration/test_plan002_parse_run.py
tests/integration/test_plan002_failures.py
tests/golden/floorplan/**
tests/golden/test_floorplan_golden.py
```

Evidence:

```text
evidence/PLAN-002/acceptance.md
evidence/PLAN-002/test-results/RUN-<timestamp>/{junit.xml,coverage.xml,command.log,summary.md}
evidence/PLAN-002/parse/layer-a-*.json
evidence/PLAN-002/overlays/layer-a-*.svg
evidence/PLAN-002/determinism/geometry-projection-hashes.json
evidence/PLAN-002/failures/parse-failure-matrix.json
evidence/PLAN-002/real-plan-redacted.json
evidence/PLAN-002/reviews/independent-openai-plan-review-2026-08-09.md
evidence/PLAN-002/reviews/independent-anthropic-code-review-<date>.md
docs/handoffs/HANDOFF-PLAN-002-to-PLAN-003-001.md
```

Verification uses the existing root interpreter from the worktree, with inherited `PYTHONPATH` cleared. No `uv sync` or install is part of this plan.

## 16. Ownership

May create/modify after approval:

```text
src/pwa/contracts.py
src/pwa/intake.py                 # bundle constant only + regression tests
src/pwa/floorplan/**
tools/make_floorplan_fixtures.py
tools/parse_floorplan.py
schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json
schemas/floorplan_annotation/v1/floorplan_annotation-1.0.0.schema.json
schemas/README.md
contracts/error_codes.md          # append-only
contracts/state_machine.yaml       # description-only: overlay_svg is now owned/produced; no gate/state semantic change
docs/OPEN-DECISIONS.md
docs/decisions/ADR-0004-floorplan-parser-baseline.md
docs/decisions/ADR-0005-floorplan-contract-and-run-lifecycle.md
docs/PROGRESS.md
PROJECT-STATE.yaml
docs/handoffs/HANDOFF-PLAN-002-to-PLAN-003-001.md
tests/unit/test_contract_versions.py
tests/unit/test_schemas_roundtrip.py
tests/fixtures/contracts/examples.json
tests/unit/test_floorplan_*.py
tests/integration/test_plan002_*.py
tests/golden/floorplan/**
tests/golden/test_floorplan_golden.py
evidence/PLAN-002/**
```

Read-only: existing 1.0.0 schemas, PLAN-000/001 runtime except the explicit intake bundle constant, package validator and prior evidence. The only allowed state-machine edit is replacing the descriptive `overlay_svg` deferred note with a reference to the PLAN-002 contract; states, gates, transitions and policies remain byte-unchanged.

Forbidden: dependency/lock changes, mutation/removal of historical schemas/error codes/evidence/runs, semantic state-machine changes, network/install, Blender/GPU/cloud, merge/push.

## 17. Staffing and governance

Canonical planning-session record (no silent fallback):

| Role | PROVIDER | REQUESTED_MODEL | ACTUAL_MODEL_ID | EFFORT | FALLBACK | MODEL_REASON | REVIEWER_MODEL | CROSS_PROVIDER_REVIEW |
|---|---|---|---|---|---|---|---|---|
| Plan architect | Anthropic | `claude-opus-5` | `claude-opus-5` | EXTRA; provider value not exposed | no | coordinate normalization, geometry invariants, overlay and parser-boundary design | `gpt-5.6-sol` / xhigh | yes |
| Independent plan reviewer | OpenAI | `gpt-5.6-sol` | `gpt-5.6-sol` | EXTRA / xhigh | no | opposite-provider contract and architecture challenge | Moshe human approval | yes |
| Post-approval spatial brief | Anthropic | `claude-opus-5` | `claude-opus-5` | HIGH / high | no | coordinate transforms, invariants and source-aligned overlay design | OpenAI Codex implementer, then Anthropic code/spatial reviewer | yes |

All provider sessions are bounded to their named planning/review deliverable. Every Claude dispatch must explicitly instruct Claude to invoke `/skills` and use relevant skills before work; absence of that instruction is a dispatch failure, not permission to proceed. Provider/model/effort/runtime metadata must come from runtime metadata rather than model self-description and must be recorded in the run report. Any mismatch or unavailable provider blocks without silent substitution.

### Plan author — spatial architect

```text
PROVIDER: anthropic
MODEL: Opus 5
MODEL_ID_EXACT: claude-opus-5
EFFORT_NORMALIZED: EXTRA
EFFORT_PROVIDER_VALUE: session-inherited (not exposed)
THINKING: extended spatial/contract reasoning
MODEL_REASON: coordinate normalization, geometry invariants, overlay and parser-boundary design
FALLBACK_PROVIDER: none
FALLBACK_MODEL: none
ESCALATE_WHEN: contract mutation, run lifecycle ambiguity, new dependency, network/GPU need
TOKEN_BUDGET: bounded planning session; no implementation
MAX_RUNTIME: bounded planning session
CROSS_PROVIDER_REVIEWER: OpenAI gpt-5.6-sol / EXTRA
```

### Independent plan reviewer

```text
PROVIDER: openai
MODEL: GPT-5.6 Codex
MODEL_ID_EXACT: gpt-5.6-sol
EFFORT_NORMALIZED: EXTRA
EFFORT_PROVIDER_VALUE: xhigh
THINKING: independent contract/architecture review
MODEL_REASON: opposite-provider challenge of Anthropic-authored critical plan
FALLBACK_PROVIDER: none; block if unavailable
FALLBACK_MODEL: none
ESCALATE_WHEN: any CRITICAL/MAJOR finding remains
TOKEN_BUDGET: bounded review only
MAX_RUNTIME: bounded review session
CROSS_PROVIDER_REVIEWER: human Moshe approval
```

### Post-approval implementation

- Implementer: OpenAI approved Codex model / HIGH.
- Code/spatial reviewer: Anthropic Opus 5 / HIGH.
- If the implementer falls back to Anthropic, the reviewer must switch to OpenAI or the gate blocks. No same-provider silent substitution.
- Dispatch briefs must fill all mandatory doc-06 fields, including actual model, thinking, token/runtime budgets and escalation conditions.

## 18. Rollout and rollback

Rollout after approval: record ADRs; write red tests; implement in the order above; run full local checks; perform opposite-provider code/spatial review; fix all CRITICAL/MAJOR findings; produce handoff; stop before merge unless separately authorized.

Rollback distinguishes pre-publication from post-publication:

- before merge/publication: abandon the branch/worktree; finalized historical runs remain untouched;
- after publication: revert runtime activation, but **retain** published schemas, error codes, ADRs and evidence as append-only history; mark superseded versions/adapters deprecated rather than deleting them;
- disable an adapter through the source registry/config, not by rewriting artifacts;
- never delete or mutate finalized source/parse runs automatically.

## 19. Risks and explicit deferrals

- Manual annotation is not scalable; accepted only as the Part 1 contract baseline.
- Real DXF layer conventions vary; the narrow convention will reject many files by design.
- Exact automatic-parser accuracy is not established without labeled real plans.
- DXF libraries parse before entity-count checks; byte cap and subprocess timeout bound that exposure.
- Content-derived IDs are stable across reruns but not across geometry edits; PLAN-003 must consume one immutable parse artifact, not attempt cross-edit identity.
- Wall thickness belongs to PLAN-003 unless explicitly present in a future source contract.
- Robust room-overlap area, OCR, curved geometry and production raster parsing are deferred.
- Repository-wide commercial licensing remains open under D-010.

## 20. Approval record and retained human gates

Moshe explicitly approved the following on Kanban `t_b7ade39e` on 2026-08-09:

1. D-004: interim Option D baseline and later production-raster decision;
2. D-012: 1.1.0 additive contract + exact-version catalog + new bundle behavior;
3. D-013: immutable derived parse-run lifecycle;
4. D-014: partial/ack fail-closed at G1;
5. exact DXF layer/entity convention in section 6;
6. mandatory source-aligned self-contained overlay;
7. Layer B rights/sensitivity rule and no accuracy claim without labels;
8. staffing and opposite-provider review rules.

The approval is converted into ADR-0004 and ADR-0005. Moshe separately selected hash-mismatch Option A and approved the recommended source-quality/scale semantics now stated in sections 5, 11 and AC-20. These clarifications close the only post-approval contract ambiguities and do not expand scope.

Retained human gates are fail-closed:

- any change to the normalized coordinate transform, quantization/identity rules, exact DXF convention, overlay alignment/security contract, G1 eligibility, or source-hash/source-quality/scale outcome semantics is a critical **Geometry/Contract** gate and requires a revised PLAN plus explicit Moshe approval before implementation;
- any Layer B use requires Moshe's rights/non-sensitivity attestation before access, and any Layer B overlay remains private and untracked;
- the first implementation-generated Layer A source-aligned overlay must be presented to Moshe at the later critical **Visual/Geometry evidence** gate before it can be treated as accepted G1 evidence or handed to PLAN-003;
- G7/G8, H200/GPU, cloud, remote execution and spending remain **DEFERRED TO PART 2** and are not approvable through this PLAN.

Precise approval request for any revision: identify the exact PLAN commit/hash and changed contract clauses, then ask Moshe to approve or reject those clauses and the regenerated Layer A overlay; silence or approval of an earlier revision is not approval.
