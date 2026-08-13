# Design memo — supported floorplan products and geometry contracts

Date: 2026-08-11
Kanban: `t_66d1d834`
Status: planning only; no implementation authorization

## 1. Decision summary

Proceed locally in Part 1 with a bounded combination:

1. **Product A — narrow deterministic PWA DXF/CAD parsing** as the only automatic, G1-eligible route.
2. **Product B₀ — manual raster correction and hash-bound approval UI** over the existing annotation route, explicitly labelled **human-verified**, with no automatic proposal engine in the first increment.
3. **Product C — true automatic raster recognition** remains deferred.

Product B₀ is narrower than the previously proposed full A+B scope. It fixes the defects that caused rejection—omissions, false openings, centreline offsets/overruns, missing thickness/curve semantics and unreadable IDs—before adding another uncertain component. A later, separately approved Product B proposal engine may be evaluated against B₀’s approved annotations and correction-time baseline.

This recommendation differs from both extremes: A-only does not serve Moshe’s actual raster input, while full A+B commits to a detector, dataset and tuning effort before the mandatory human containment loop is proven.

## 2. Routing record

Critical spatial/geometry design was performed in an Anthropic Claude Code session that invoked `/skills` and loaded `computer-vision-expert` before analysis.

| Field | Recorded value |
|---|---|
| Provider | Anthropic / Claude Code |
| Requested model | `opus` |
| Actual runtime model | `claude-opus-5` / Opus 5 |
| Effort | `high` requested and shown in the TUI |
| Fallback | none observed; no provider/model substitution |
| Session | `81405d64-8518-4e5d-b1ec-ac134c9e59d4` |
| Boundary | read-only planning; no network, GPU, H200, cloud, remote work or PLAN-003 |

Related completed Opus synthesis already present in the planning packet: session `e89cd83c-215a-430e-a058-664d64724fae`, actual `claude-opus-5`, high effort requested, no fallback.

## 3. Rejected PLAN-002 result: constraints this design must close

The rejected G1 visual result was roughly half useful. It omitted rotated/angled walls, the angled bay, curved geometry and many openings; showed at least one false-positive opening; drew centrelines offset from or extending past source walls; and rendered opaque IDs on top of one another until the evidence became unreadable.

The existing raster route is not a recognizer. It consumes manually authored `floorplan_annotation` coordinates and uses the raster only to verify identity, dimensions and format and to render the overlay. It does not detect walls, arcs, rooms or openings from pixels. Green PLAN-002 tests proved contract handling, immutability, validation and determinism; they did not prove automatic recognition accuracy. Existing raster evidence must therefore remain auditable but be labelled `legacy_manual` and excluded from automatic-accuracy claims.

The equal CAD/annotation canonical geometry hash is useful evidence that two adapters normalize the same supplied geometry consistently. It is not recognition evidence because both routes received the same manually measured geometry.

Truth-in-labelling is a blocking invariant:

- Product A entities may be labelled `cad_exact` only when they come from the approved CAD convention.
- Product B entities are labelled `human_confirmed`, `human_edited`, `human_drawn` or `human_deleted` as applicable.
- Future proposal entities may be labelled `auto_candidate`, but candidates are never accepted geometry.
- Any artifact containing human-authored or edited geometry is **human-verified**, never “automatic recognition.”

## 4. Product A — narrow deterministic DXF/CAD

### Product definition

Product A parses an explicit project-owned drawing convention. It reads semantics the drafter made unambiguous; it does not infer arbitrary CAD layer meanings or recognize drafting symbols.

### Supported inputs

- DXF only.
- 2D modelspace, zero elevation.
- `$INSUNITS` explicitly declared as mm, cm or m and equal to verified manifest units.
- Exact, case-sensitive approved `PWA-*` layers.
- Bounded file/entity counts and parser timeout under the existing immutable derived-run boundary.

### Supported geometry

- `LINE` wall primitives at any angle. Horizontal, vertical, rotated and angled walls have identical semantics.
- Circular `ARC` wall primitives within declared radius/sweep bounds.
- `LWPOLYLINE` wall paths decomposed deterministically into ordered native line segments and circular bulge arcs, with parent handle and segment-index provenance.
- Closed room polylines made from supported native primitives.
- Native arcs remain native in canonical geometry. Tessellation is rendering-only and never changes arc identity.

### Unsupported geometry and inputs

- `SPLINE`, ellipse, NURBS and arbitrary non-circular curves.
- 3D polylines, nonzero elevation, blocks/`INSERT`, xrefs, images, OLE, hatches, paperspace entities, multiple active layouts and multiple storeys.
- Generic architect layer naming or semantic inference.
- CAD containing only ambiguous wall edges rather than declared centrelines or an approved wall-band entity.

All unsupported cases fail closed and are never approximated silently.

### Centreline, edges and thickness

The Product A wall truth is a declared centreline. Optional `thickness_m` is accepted only when explicitly carried by the approved convention. A drawn wall edge must never be silently interpreted as a centreline, because doing so creates a systematic half-thickness offset and corrupts clear-room dimensions.

If a future convention represents wall bands, it must do so unambiguously and preserve both source edges, derived centreline and thickness provenance. That is a separate approved contract extension.

### Intersections and topology

- Wall endpoints and junctions come from source geometry exactly.
- Rooms require at least three unique vertices, positive area, deterministic winding and no non-adjacent self-intersection.
- Duplicate/degenerate entities fail.
- Product A performs no topology repair: no snapping, gap closure, extension, merge or inferred split. A non-conforming file is rejected instead of “fixed.”

### Openings, type and orientation

- Door/window type comes from the approved source layer/entity contract, never from symbol recognition.
- Every opening resolves to exactly one host wall; zero or multiple hosts fail.
- Centre must lie on the host within tolerance and the full opening must fit.
- Width is measured along the host tangent. For straight walls this is projected span; for arc hosts it is arc length.
- Swing, hinge side and inward/outward direction are present only when explicitly encoded. Otherwise they are `unknown`, not inferred.
- Duplicate, wrong-type, off-wall, over-wide or topology-breaking openings fail.

### Scale, confidence and failure policy

- `$INSUNITS` must match manifest units; mismatch fails with the exact contract code.
- Target scale error after quantization: no more than 0.01%.
- Accepted primitives have structural confidence `1.0`; this records explicit source semantics, not a learned probability.
- Any unsupported entity, unit conflict, ambiguous host, invalid topology, duplicate, resource cap or timeout prevents `complete` and prevents G1.

### Honest Product A claim

For compliant PWA CAD, exact deterministic parsing is credible. Product A does not claim to parse arbitrary CAD and does not solve JPEG/raster input.

## 5. Product B₀ — manual raster correction and approval

### Product definition

Product B₀ is a human-in-the-loop digitizer with no automatic detector in its first increment. It turns the existing raw annotation contract into a reviewable product: native line/arc geometry, explicit centreline/thickness semantics, append-only edit operations, topology diagnostics, clean evidence and immutable per-plan approval.

### Supported inputs

- One 2D orthographic floor per image.
- PNG/JPEG or an approved rendered PDF page.
- High-contrast printed linework; recommended 150–600 effective DPI.
- No perspective; skew corrected explicitly, initially bounded to ±5°.
- At least two independent scale anchors for normal scale acceptance.
- Straight walls at arbitrary angles and circular arcs.

### Unsupported or mandatory-manual cases

- Photographs, perspective/isometric views and hand sketches.
- Severe compression, occlusion or scan damage.
- Multiple floors on one sheet.
- Bespoke/unknown opening symbols.
- Missing or contradictory scale evidence.
- Non-circular curves.
- Topology that cannot be made unambiguous.

Unsupported input produces diagnostic `partial` or `failed` output and cannot become G1 eligible. It is never guessed into completeness.

### Geometry contract

A wall is an ordered contiguous path of native primitives:

- line: start/end;
- arc: start/end/centre/radius/sweep/direction;
- optional explicit thickness;
- source representation and provenance;
- no canonical tessellation loss.

Arbitrary line angles are fully supported by editing. Circular arcs are placed or corrected by three points or centre/radius/sweep. Non-circular curves are refused rather than disguised as a polyline approximation.

### Centreline, wall edges and thickness

Three representations remain distinct:

1. **Paired-edge wall:** both visible boundaries are recorded; the centreline is derived midway; estimated thickness and source-edge provenance are retained.
2. **Single-line wall:** tagged `single_line_assumption`; centre/thickness ambiguity blocks auto-approval until a human resolves it.
3. **Human-declared wall:** the operator explicitly confirms the centreline and thickness.

Room areas must state their basis—centreline, clear internal face or another explicit convention. No consumer may silently treat centreline area as clear area.

Extension beyond observed pixel support is forbidden unless a human explicitly performs and approves it. Every endpoint repair stores before/after coordinates. This directly prevents silent centreline overrun.

### Intersections and topology repair

Permitted repair suggestions are bounded and reversible:

- endpoint clustering;
- tiny-gap closure;
- collinear merge;
- T-junction split;
- arc-line tangent join;
- duplicate suppression.

Each repair has a deterministic tolerance, preview, undo and provenance record. No repair may create/delete an opening, bridge an opening, change room count or move geometry beyond tolerance without explicit confirmation. Approval requires no self-intersection, duplicate entity, dangling room boundary, ambiguous host or unresolved topology finding.

### Openings, orientation and type

- Door, window and untyped passage are separate types.
- A future machine proposal is only a candidate, visibly distinct and never serialized as accepted geometry.
- Acceptance requires correct type, unique host, centre-on-host tolerance, tangent-consistent span and width fit.
- Swing/hinge/direction is set by the human or remains `unknown`.
- Suspected false openings are blocking findings.
- Zero critical false-positive openings is an absolute final-output gate. A critical false positive is an accepted opening in solid wall, on the wrong host or of a wrong type that creates a false passage/exterior breach.

### Scale

- Normal acceptance requires at least two independent declared dimensions.
- Median fitted scale residual must be at most 1%; anchor disagreement at most 2%.
- One anchor yields `partial` and requires explicit acknowledgement.
- No reliable anchor or contradiction over 2% fails with `PARSE_SCALE_UNKNOWN`.

### Confidence

Confidence is advisory only. It may order the review queue; it never overrides an invariant or promotes geometry. In B₀, method/provenance is more important than probability because all final entities are human-verified.

## 6. Product B₀ correction UI

Required workflow:

1. Open an immutable source-bound review session.
2. Inspect source, geometry and diff layers with pan/zoom.
3. Add/edit/split/merge arbitrary-angle line and circular-arc walls.
4. Select centreline or paired-edge representation and set/confirm thickness.
5. Add/delete/retype openings; bind/rebind host; edit width and tangent; set or leave orientation unknown.
6. Add at least two scale anchors and view residual/disagreement live.
7. Resolve topology diagnostics: gaps, dangling endpoints, self-intersections, duplicates and ambiguous hosts.
8. Use snap only through previewed, undoable actions.
9. Resolve the confidence/task queue.
10. Save drafts without creating an eligible artifact.
11. Review a clean overlay and diff/error view.
12. Execute one explicit final approval action that writes an immutable hash-bound review record.

UI requirements:

- full keyboard navigation;
- append-only undoable `edit_ops`;
- deterministic replay over the exact base/proposal hash;
- IDs and confidence hidden by default and shown only on hover/selection or in an audit side table;
- distinct door/window glyphs;
- source, edges, centrelines, arcs, openings, rooms, repairs and uncertainty toggles;
- loopback-only binding to `127.0.0.1`, restrictive CSP and CSRF token;
- no arbitrary URL/path access and no serving outside the selected immutable run.

Edit operation vocabulary includes at least: `confirm`, `edit`, `draw`, `delete`, `retype`, `rebind`, `set_thickness`, `set_scale_anchor`, and `apply_repair`. Replaying the operations must reproduce approved geometry byte-for-byte.

## 7. Approval state model

| State | Meaning | G1 eligible |
|---|---|---:|
| `proposed` | Future candidates exist; nothing accepted. Absent in B₀. | no |
| `in_review` | Draft edits exist or review queue is non-empty. | no |
| `blocked` | Unsupported input, scale conflict, ambiguous host, topology error, resource/timeout event or suspected critical false opening. | no |
| `awaiting_approval` | All invariants pass, queue is empty and evidence is generated. | no |
| `approved` | Immutable approval record binds source, annotation, parse, overlay, metrics and edit-op chain hashes. | yes, subject to all geometry gates |
| `superseded` | A later immutable run replaced this review result. | no |

There is no confidence-based fast path from candidate to approved. Every raster result passes through explicit human action. Approval is per plan; aggregate metrics cannot waive a per-plan failure.

G1 can remain machine-verifiable by requiring the human review artifact as a machine-checkable prerequisite. Changing G1 itself into a human gate is a separate state-machine decision and is not implied by this memo.

## 8. Product C — true automatic raster recognition

Product C means arbitrary raster plans become trustworthy geometry with no human correction. It is deferred from Part 1.

Arbitrary raster plans cannot be guaranteed at 100% automatic accuracy:

- identical strokes can mean walls, furniture, dimensions, grids, hatching, demolition layers, text or noise;
- rasterization destroys CAD layers and entity semantics;
- scale can be absent and therefore unrecoverable;
- door/window symbols vary by office, region and era;
- occlusion, skew and compression can erase geometric evidence;
- a learned parser still yields distribution-bounded error rates, not a universal guarantee.

Classical local CPU vision can offer useful candidates on a declared bounded domain, but it cannot remove semantic ambiguity. Learned recognition additionally requires a rights-cleared labeled corpus, grouped held-out evaluation, model/dependency/licensing decisions and human review. No OCR stack, model weights, dataset download, training, GPU, H200 or cloud belongs in Part 1.

Any future Product C work must publish its supported domain, measure out-of-domain refusal and fail closed outside the domain. It may never market held-out corpus performance as a guarantee on arbitrary plans.

## 9. Credible bounded targets

These are proposed gates, not current performance claims.

### Product A compliant CAD

- Wall precision/recall: 1.000/1.000.
- Opening precision/recall: 1.000/1.000.
- Critical opening false positives: 0.
- Valid room topology: 100%.
- Arbitrary-angle and supported circular-arc fixture coverage: 100%.
- Scale error: at most 0.01%.
- Repeat output: byte-identical.

### Product B₀ human-approved final

- Wall precision/recall: at least 0.995/0.995.
- Opening precision/recall: at least 0.995/0.99.
- Critical opening false positives: 0 absolute.
- Valid room topology and represented intended rooms: 100% per approved plan.
- No unresolved geometry/topology/scale findings.
- Hash-bound approval and deterministic replay for every plan.
- Median correction time: at most 8 minutes for clean exports and 20 minutes for supported scans.
- Stop Product B if correction is not materially faster than redrawing on a representative sample.

These final metrics primarily measure operator+UI effectiveness, not recognition.

### Future Product B proposal engine

Use tiered targets, not a single aggregate:

| Domain | Wall precision/recall | Arc recall | Opening precision/recall |
|---|---:|---:|---:|
| R1 clean vector-rendered exports, 200–600 DPI | ≥0.95/≥0.90 | ≥0.85 | ≥0.98/0.50–0.75 |
| R2 clean printed/scanned high-contrast plans | ≥0.90/≥0.75 | ≥0.70 | ≥0.98/0.40–0.65 |
| R3 everything else | out-of-domain refusal, ≥0.95 correct-refusal rate | n/a | n/a |

Opening recall is intentionally lower while precision is very high: a missed opening costs a human correction, while an invented opening creates unsafe downstream topology. Candidate-only false positives are allowed; accepted false positives are not.

Wall results must be both entity-wise and length-weighted and separately reported for axis-aligned, angled (>2°) and circular-arc buckets. Aggregate performance may not hide a failed geometry class.

### Matching rules

- One-to-one assignment; one prediction cannot satisfy multiple labels.
- Line wall: primitive type match, angle error ≤1°, longitudinal overlap ≥95%, symmetric source-space Hausdorff distance ≤`max(4 px, 0.025 m)`.
- Endpoint P95 ≤`max(3 px, 0.020 m)`; signed under-run and overrun reported separately.
- Arc wall: radius error ≤2% and sweep overlap ≥95% in addition to spatial tolerance.
- Opening: correct type and host, centre error ≤`max(4 px, 0.050 m)`, width error ≤`max(0.020 m, 2%)`.
- Aggregate metrics never waive a per-plan blocker.

## 10. Overlay evidence contract

The rejected ID clutter is fixed structurally:

- zero always-visible entity IDs or confidence labels over geometry;
- zero label bounding-box collisions in the default clean view;
- IDs remain addressable through hover/selection and a separate audit index;
- distinct door/window shapes and colors;
- clean source-vs-geometry view, diff/error view and audit view;
- toggles for source, wall edges, centrelines, arcs, openings, rooms, repairs and uncertainty;
- visible text at least 11 px and contrast at least 4.5:1 at 100%; moved callouts have leader lines;
- deterministic self-contained SVG with no script, external URL or `foreignObject`;
- correction UI remains a separate loopback-only application, not embedded active content.

## 11. Fail-closed contract

No raster result is `complete` unless all are true:

- source belongs to the supported envelope;
- scale is valid;
- topology is valid;
- no error finding remains;
- no unresolved review task or low-confidence item remains;
- zero critical false-positive openings;
- every correction task is resolved;
- immutable approval record and all bound hashes verify.

Any unsupported curve, ambiguous centreline/thickness, ambiguous opening host, scale conflict, topology-changing repair, out-of-domain raster, resource cap or timeout blocks approval. Confidence cannot override an invariant. Failure produces diagnostic `partial`/`failed` artifacts where safe and never advances to PLAN-003.

## 12. Final boundary

This memo authorizes no implementation, schema change, dependency change, merge, push or PLAN-003 work. Product C, GPU/H200/cloud, G7 and G8 remain deferred to Part 2. Historical PLAN-002 artifacts remain immutable and auditable but are not grandfathered into a recognition claim.

The next human scope decision is whether to approve A+B₀ as recommended, choose A-only, or authorize the larger A+B proposal-engine and dataset scope. No choice is inferred by this memo.
