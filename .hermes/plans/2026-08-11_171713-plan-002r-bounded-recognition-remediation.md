# PLAN-002R — Bounded floorplan-recognition remediation PLAN

- Date: 2026-08-11
- Status: **REVIEW DRAFT — PLANNING ONLY — NOT APPROVED FOR IMPLEMENTATION**
- Kanban synthesis: `t_e50c0bd4`
- Supersedes for review: `.hermes/plans/2026-08-11_165545-floorplan-recognition-remediation.md`
- Preserves: accepted PLAN-002 history, ADR-0004, ADR-0005, immutable historical runs, and exact-version validation
- Hard boundary: local-only Part 1. No H200, GPU, cloud, remote execution, G7, G8, purchase, spend, production activation, merge, push, or PLAN-003 work is authorized by this PLAN.

## 1. Goal and honest target

Remediate the rejected PLAN-002 visual gate without confusing three different products:

1. **Product A — deterministic compliant CAD parsing:** automatic only because the source explicitly carries approved semantics.
2. **Product B0 — human-authored/corrected raster digitization:** no detector or proposal engine; every accepted result is human-verified.
3. **Product B1 — semi-automatic raster proposals:** a future local candidate generator feeding the B0 correction workflow; separately gated and not part of the recommended first increment.
4. **Product C — true automatic raster recognition:** trustworthy canonical geometry from arbitrary raster plans without mandatory correction; deferred.

Recommended Part 1 scope is **A + B0**. B1 is a separately approved stop/go pilot; C is deferred. This recommendation serves compliant CAD deterministically and Moshe's raster inputs honestly while first proving the correction, evidence, and approval containment loop.

The achievable target is exact deterministic parsing for a narrow project-owned CAD convention and highly accurate, explicitly human-verified final geometry for supported raster plans. **Guaranteed 100% automatic accuracy for arbitrary raster plans is not achievable and is explicitly disclaimed.** Rasterization destroys semantic layers; scale can be absent; identical strokes can mean walls, furniture, dimensions, text, hatching, demolition marks, or noise; and opening symbols vary by source. Finite-test success is not a population guarantee.

## 2. Rejection baseline and truth in labelling

Moshe rejected the visual result because it was roughly 50% useful: rotated, angled, and curved walls were omitted; many openings were missing; at least one false opening was shown; wall centrelines were offset from or extended past visible walls; and opaque IDs overlapped until the overlay was hard to judge.

The current raster adapter is not a recognizer. It validates and normalizes a manually authored `floorplan_annotation` and uses the source raster for identity, dimensions, and overlay rendering. The equal CAD/annotation canonical hash proved normalization equivalence for supplied geometry, not pixel recognition. Existing raster evidence remains immutable and auditable but is classified `legacy_manual` and excluded from automatic-recognition claims.

Truth-in-labelling is a blocking invariant:

- Product A entities may be labelled `cad_exact` only when emitted from the approved CAD convention.
- Product B0 entities are labelled `human_confirmed`, `human_edited`, `human_drawn`, or `human_deleted` as applicable.
- Future B1 candidates are labelled `auto_candidate` and are never canonical accepted geometry.
- Any artifact containing human-authored or human-edited geometry is **human-verified**, never “automatic recognition.”
- A candidate ID is provenance only; it never becomes a canonical entity ID by promotion.
- Mislabelled provenance or a recognition claim based on manual annotations is a CRITICAL gate failure.

## 3. Product boundaries

### 3.1 Product A — supported deterministic CAD path

Product A parses a project-owned PWA DXF convention. It does not infer generic architect layer meanings, inspect arbitrary symbols, or repair non-conforming drawings.

Supported source envelope:

- DXF only; 2D modelspace; zero elevation; one floor.
- `$INSUNITS` explicitly mm, cm, or m and equal to verified manifest units.
- Exact case-sensitive approved `PWA-*` layers.
- Bounded bytes, entities, geometry counts, output, and wall time under the existing immutable derived-run boundary.

Supported wall geometry, subject to the contract amendment in section 11:

- `LINE` at any angle.
- Circular `ARC` within approved radius and sweep bounds.
- `LWPOLYLINE` decomposed deterministically into ordered native line segments and circular bulge arcs; parent handle and segment index remain provenance.
- Native arcs remain native canonical geometry. Tessellation is rendering/evaluation-only and cannot change identity.

Unsupported and fail-closed:

- `SPLINE`, ellipse, NURBS, arbitrary non-circular curves, 3D polylines, nonzero elevation.
- blocks/`INSERT`, xrefs, images, OLE, hatches, paperspace entities, multiple active layouts, multiple storeys, or external references.
- generic layer inference, symbol recognition, automatic snapping, gap closure, extension, merging, or guessed thickness.
- wall-edge-only drawings without an approved explicit wall-band representation.

#### Wall, room, and opening semantics

A Product A wall is a declared centreline path. Optional `thickness_m` is accepted only when explicitly encoded by the approved convention. A visible edge must never be interpreted silently as a centreline.

**Selected room model:** Product A requires closed `PWA-ROOM` `LWPOLYLINE` entities with the same defined line/bulge-arc semantics as walls. The parser derives bounded faces independently from the validated wall-path graph after exact junction splitting; openings do not break host-wall topological continuity. Each explicit room must match exactly one bounded face, and each intended bounded face must match exactly one explicit room. Mismatch, duplicate face, self-intersection, unsupported primitive, or ambiguous nesting fails closed. This resolves the prior plan's missing room-source contract; explicit rooms and derived faces are validation counterparts, not competing geometry sources.

Doors and windows are separate types. Each opening must resolve to exactly one host wall; its centre lies on the host within tolerance; its full width fits; and width is measured along the host tangent (projected length for a line, arc length for an arc). Swing, hinge side, and inward/outward direction are present only when explicitly encoded; otherwise they are `unknown`. Duplicate, wrong-type, off-wall, over-wide, ambiguous-host, or topology-breaking openings fail.

Product A performs no topology repair. Non-conforming CAD is rejected rather than “fixed.” Accepted structural confidence is `1.0`, meaning explicit source semantics, not learned probability.

### 3.2 Product B0 — supported human-verified raster path

B0 is a detector-free digitization, correction, and approval product over immutable raster source. It is not semi-automatic recognition and has no proposal-accuracy claim.

Supported source envelope:

- one orthographic 2D floor per PNG/JPEG or approved rendered-PDF page;
- high-contrast printed linework, recommended 150–600 effective DPI;
- no perspective; explicitly corrected skew initially bounded to ±5°;
- straight walls at arbitrary angles and circular arcs;
- at least two independent authoritative scale anchors for approval.

Unsupported or diagnostic-only cases:

- photographs, perspective/isometric views, hand sketches, severe compression/occlusion/damage, multiple floors on one sheet, bespoke/unknown opening symbols, missing or contradictory scale evidence, non-circular curves, or topology that cannot be made unambiguous.

B0 wall geometry is an ordered contiguous path of native line/arc primitives. Three representations remain distinct:

1. paired-edge wall: both visible boundaries are recorded, centreline is derived midway, and estimated thickness plus source-edge provenance are retained;
2. single-line wall: tagged `single_line_assumption` and blocked until a human resolves centre/thickness ambiguity;
3. human-declared wall: operator explicitly confirms centreline and thickness.

Extension beyond observed pixel support is forbidden unless the operator deliberately performs and approves it. Every endpoint change records before/after source coordinates.

**Selected room model:** B0 derives candidate room faces from the corrected wall-path graph; the operator confirms intended bounded faces and exterior/island semantics but does not draw an unrelated duplicate room polygon. Approved annotation serializes the confirmed derived boundaries with provenance. Openings preserve host-wall continuity and determine room/exterior adjacency. Approval requires exact consistency between confirmed faces, serialized rooms, and the derived topology graph.

Permitted repair actions are bounded, previewed, undoable, and explicit: endpoint clustering, tiny-gap closure, collinear merge, T-junction split, arc-line tangent join, and duplicate suppression. No action may create/delete an opening, bridge an opening, alter room count, or move geometry beyond its approved tolerance without direct confirmation.

### 3.3 Product B1 — deferred semi-automatic proposal pilot

B1 may later generate local CPU candidates for walls, arcs, openings, scale, or repairs. It is not included in A+B0 implementation approval. Before any B1 work, Moshe must approve its bounded visual domain, non-canonical proposal format, dataset use, dependency/license envelope, resource budgets, pilot targets, and stop rule.

B1 candidates live only in a versioned diagnostic proposal artifact or non-envelope workspace format. They never appear in canonical `floorplan_parse`; human correction produces a new accepted annotation, and only that annotation can feed a fresh parse. Missing the pilot targets stops B1 for a scope/dependency decision; thresholds are not weakened and hidden test data is not used for tuning.

### 3.4 Product C — deferred automatic raster recognition

Product C means canonical geometry from arbitrary rasters without mandatory human correction. It is outside Part 1. No OCR/model stack, weights, training, corpus download, new compute path, or universal accuracy claim is authorized. Any future C plan must define a bounded domain, out-of-domain refusal, rights-cleared data, calibrated uncertainty, independent held-out evaluation, and a human safety policy.

## 4. B0 correction and approval workflow

Required user flow:

1. open an immutable source-bound review workspace;
2. inspect separate source, geometry, and diff layers with pan/zoom;
3. add/edit/split/merge arbitrary-angle lines and circular arcs;
4. choose paired-edge, single-line, or human-declared centreline semantics and confirm thickness when known;
5. add/delete/retype openings, bind/rebind host, edit width/tangent, and set orientation or leave it `unknown`;
6. add at least two independent scale anchors and inspect residual/disagreement live;
7. resolve gaps, dangling endpoints, self-intersections, duplicates, ambiguous hosts, room faces, and adjacency findings;
8. apply snapping/repair only through previewed, undoable actions;
9. save drafts without creating eligible canonical artifacts;
10. inspect clean overlay, source-only, accepted-geometry-only, diff/error, topology, and audit views;
11. execute one explicit final approval action that creates immutable review evidence;
12. create a subsequent fresh accepted parse run referencing that review evidence; never mutate a finalized run.

All edits are append-only `edit_ops` with at least `confirm`, `edit`, `draw`, `delete`, `retype`, `rebind`, `set_thickness`, `set_scale_anchor`, `confirm_room`, and `apply_repair`. Replay over the exact base hash must reproduce the approved annotation byte-for-byte.

UI requirements include keyboard navigation; IDs/confidence hidden by default and available through hover/selection/audit table; distinct door/window glyphs; layer toggles; no directory listing; and no arbitrary URL/path access.

## 5. Lifecycle and fail-closed decision

The current G1 is machine-labelled and requires `floorplan_parse`, `assumptions`, and overlay evidence; ADR-0005 forbids mutation of finalized parse runs. B0 therefore needs an explicit migration rather than an informal “approval prerequisite.”

**Selected proposed lifecycle, requiring Moshe approval before implementation:**

- UI drafts and any future B1 proposals are non-canonical workspace data and never enter a finalized parse run.
- Explicit B0 human approval finalizes a separate immutable `floorplan_review` run whose artifact binds source, accepted annotation, diagnostic parse, overlay views, metrics, edit-op chain, reviewer identity/authority, and approval hashes.
- A subsequent fresh accepted parse run references the approved review run and revalidates the accepted annotation; no finalized source, diagnostic parse, or review run is mutated.
- Requiring `floorplan_review` for raster eligibility on `INPUT_VALIDATED -> FLOORPLAN_PARSED` is a semantic amendment to G1 and `required_artifacts`, requiring explicit Moshe approval and a versioned state-machine/contract migration.
- Until that amendment is approved and implemented, B0 can produce diagnostic `partial`/`failed` runs only and **cannot satisfy G1**.
- Product A compliant CAD may retain machine G1 eligibility without `floorplan_review`, subject to all deterministic geometry/evidence gates.

Outcome classes preserve ADR-0005/AC-20 exactly:

- invalid or unsafe preflight: CLI 2, no finalized derived run;
- validated source with unsupported domain geometry or contradictory/missing scale: schema-valid `failed`, CLI 3;
- warning-only usable diagnostic geometry: `partial`, CLI 1;
- only fully valid Product A or approved/revalidated B0 output: `complete`, CLI 0 and potentially G1-eligible.

No confidence threshold promotes a candidate or overrides an invariant. Unsupported geometry, ambiguous centreline/thickness, ambiguous opening host, scale conflict, invalid topology, suspected critical false opening, unresolved task, resource breach, timeout, missing approval, or hash mismatch blocks eligibility.

One-anchor raster runs are diagnostic `partial` only and can never be approved. Approval requires two independent anchors meeting both residual gates or a separately approved trusted-scale source contract.

## 6. Dataset and ground truth

Use source-family separation: the underlying plan and all crops, rotations, scans, compressions, PDF renders, DXF exports, annotations, and derived variants stay in one split. Detect leakage by exact source hash, perceptual raster hash, canonical geometry hash, provenance/license ID, and manual collision review.

Minimum corpus proposal:

- optional training pool: 200 source families, declared `not_used` for A/B0;
- development: 60 families;
- deterministic regression: 40 single-defect micro-plans;
- locked acceptance: 100 families — 30 clean raster, 30 degraded raster, 25 conforming CAD, and 15 fail-closed CAD.

The locked set must prove minimum hard-case coverage by per-plan manifest, including horizontal/vertical/angled walls, non-90° rotations, circular raster arcs, segmented curves, interior/exterior thickness ranges, doors, windows, no-opening plans, ambiguous opening decoys, clutter, real licensed/public raster sources from distinct templates, degraded scans, interior/exterior openings, scale contradictions, and every unsupported CAD class. Derivatives cannot inflate source-family counts.

Every locked plan receives two independent labels without parser output visibility; an independent adjudicator resolves wall, opening, room, scale, and uncertainty disagreements. Labels record source and metric geometry, wall centrelines and visible edges, thickness where knowable, semantic endpoints, typed/hosted openings, explicit empty-opening lists, room/exterior topology, scale evidence, uncertainty masks, provenance, rights, and adjudication history.

Public/redistributable data retains source, author, license, retrieval hash, and family ID. Private Layer B data requires Moshe's rights/non-sensitivity attestation; source and overlays remain local/untracked, with only approved redacted hashes/counts/metrics in Git.

Thresholds and corpus version are frozen before the locked test is opened. Parser authors cannot inspect locked labels or test seeds. A threshold/corpus/evaluator change creates a new version and invalidates affected approvals.

## 7. Metrics and proposed acceptance gates

All thresholds below are proposed requirements, not current performance claims. Pixel tolerance is converted to metres using adjudicated scale before comparison. Curves use fixed deterministic sampling or analytical distance as specified by the evaluator. Matching is one-to-one; one prediction cannot satisfy multiple labels.

### 7.1 Geometry matching

Report per-plan macro and global micro precision/recall with 95% confidence intervals, plus entity-wise and length-weighted wall metrics. Report separate CAD, real-raster, degraded, adversarial, axis-aligned, angled, rotated, and arc strata; no aggregate compensates for a failed required slice.

Recommended match tolerances by quality stratum:

| Measure | CAD / clean raster | light degradation | heavy supported degradation |
|---|---:|---:|---:|
| wall symmetric Hausdorff | max(0.02 m, 1 px) | max(0.04 m, 2 px) | max(0.06 m, 3 px) |
| endpoint distance | max(0.03 m, 2 px) | max(0.05 m, 3 px) | max(0.08 m, 4 px) |
| endpoint overrun at junction/free end | max(0.03 m, 2 px) | max(0.05 m, 3 px) | max(0.08 m, 4 px) |

Line matching additionally requires orientation error ≤2° for length ≥0.50 m (≤5° for shorter walls) and ≥90% overlap. Arc/chain matching additionally requires native primitive agreement, deterministic no-double-credit segmentation, radius error ≤2%, and sweep overlap ≥95%. Report p50/p95/max Hausdorff, endpoint distance, angular error, normal centreline offset, and signed endpoint under-run/overrun.

Opening matching requires correct type and matched host, centre distance along host ≤`max(0.05 m, 3 px)`, perpendicular distance ≤`max(0.02 m, 2 px)`, and width error ≤`max(0.05 m, 5%)`.

A critical false positive is an accepted opening that creates false room/exterior adjacency, appears in an explicit no-opening plan, converts damage/furniture/text/dimensions/stairs/decor into an opening, lies outside its host/spans a junction, or changes egress/topological connectivity.

“Zero critical false positives” means zero observed in the locked set and zero in every approved plan. Report the one-sided statistical upper bound; make no population-zero claim.

### 7.2 Product-specific gates

**Product A, conforming CAD:**

- wall precision/recall 1.000/1.000;
- opening precision/recall 1.000/1.000;
- zero critical false positives;
- all explicit rooms match derived bounded faces; valid room topology 100%;
- arbitrary-angle and supported circular-arc fixtures 100%;
- relative scale error ≤0.01%;
- byte-identical canonical output on repeat;
- all 15 unsupported CAD families reject with the approved deterministic finding class and no external resolution.

**Product B0, human-approved final:**

- wall precision/recall ≥0.995/0.995 overall and within each approved hard-geometry slice;
- opening precision/recall ≥0.995/0.990;
- zero observed critical false positives and zero openings on every no-opening plan;
- 100% structurally valid room faces and exact intended room/exterior adjacency per approved plan;
- no unresolved geometry, topology, scale, host, uncertainty, or review findings;
- two-anchor scale median residual ≤1% and anchor disagreement ≤2%;
- deterministic annotation/edit replay and hash-bound approval for every plan;
- median correction time ≤8 minutes for clean exports and ≤20 minutes for supported scans;
- stop B0 if representative correction time is not materially faster than controlled redraw.

These B0 final metrics measure the operator+UI system, not automatic recognition.

**Product B1, if separately approved:** proposal targets are pilot go/no-go targets, never performance promises. Use separate minima for clean, scanned, angled, arc, opening, and out-of-domain-refusal strata. The proposal engine cannot be accepted merely because humans repair it to B0 quality.

### 7.3 Scale and topology

For authoritative scale, report per-plan relative error and p95. Fabricating scale on absent/contradictory evidence is CRITICAL. Rotation, crop, and resampling cannot change recovered physical scale.

Every emitted room must be simple, positive-area, within source bounds, non-duplicated, and consistent with the wall graph. Derive and compare room/exterior adjacency. Any exterior leak, impossible crossing, dangling intended boundary, topology-changing false opening, or explicit/derived room mismatch blocks the plan.

## 8. Evidence and visual gate

Every locked plan has separately rendered and hash-bound evidence:

1. sanitized source alone;
2. adjudicated ground truth over source;
3. accepted geometry alone;
4. source + accepted geometry composite;
5. false-positive/false-negative/matched/tolerance diff;
6. topology and leak/junction view;
7. machine-readable metrics/findings;
8. immutable per-plan approval.

Source and geometry cannot be recoverable only by toggling one composite. Provide deterministic PNG captures at 100%, 200%, and 400% in the pinned browser/rendering environment.

Legibility gates:

- no always-visible entity IDs or confidence text over geometry;
- zero label-label and label-critical-geometry intersections at required zooms;
- text ≥12 CSS px and key legend text ≥14 CSS px at the 100% viewport;
- text contrast ≥4.5:1 and non-text geometry contrast ≥3:1;
- doors/windows distinguishable without color alone;
- prediction/accepted strokes distinguishable from source under color-vision-deficiency simulation;
- no clipping; source remains inspectable; units, scale status, source/evidence hashes, corpus, and runner version appear outside plan geometry;
- deterministic self-contained SVG: no script, external URL, `foreignObject`, active content, timestamp, private label, path, or source metadata.

Moshe or a delegate named by Moshe before test opening reviews all 100 locked plans; sampling is forbidden. Every applicable wall alignment, endpoint, opening, topology, scale, and legibility item must be yes. Human approval never waives a machine failure, and machine thresholds never waive human review. Any changed parser, renderer, source, label, threshold, evaluator, or rendering baseline invalidates affected approval.

## 9. Adversarial and deterministic regression coverage

The 40 micro-plans isolate at least: furniture/dimension/text/stair/decorative opening decoys; damage gaps; no-opening clutter; endpoint-near/over-wide/off-wall/ambiguous/duplicate openings; true opening versus damaged collinear gap; T/four-way/acute/obtuse junctions; one-quantum and half-thickness centreline bias; endpoint overrun/underrun; 7°/37° rotation; circular and segmented curves; variable thickness; isolated walls; self-intersecting/duplicate rooms; courtyard/island; absent/contradictory/occluded scale; unreadable labels; dense IDs; supported CAD; and exact unsupported CAD rejection.

Regression requirements include:

- split/family leakage and corpus-minimum validation;
- exact label/provenance validation;
- endpoint-order-invariant one-to-one matching;
- segmentation-neutral curve matching without double credit;
- opening duplicate/class/host scoring and all critical decoys;
- tolerance behavior immediately below, at, and above boundaries;
- room validity and graph isomorphism;
- exact fail-closed CAD classes;
- byte-identical normalized geometry, metrics, SVG, and pinned PNG output across two clean runs;
- source/annotation/parse/review/evidence hash binding;
- collision, contrast, clipping, and active-content checks;
- aggregation failure on missing plan/slice/approval, any CRITICAL, unresolved MAJOR, or failed threshold;
- approval invalidation after changing any bound input or evaluator component.

## 10. Security, privacy, and resource boundaries

Preserve existing immutable-source preflight, exact-version schema/hash verification, containment checks, reparse/symlink rejection, sanitized errors, exclusive writes, atomic finalization, and no external reference resolution.

Existing limits remain unless an approved revision changes them: DXF/raster source 50 MiB; DXF entities 200,000; annotation JSON 5 MiB; walls/rooms/openings 20,000/5,000/20,000; polygon vertices 10,000; coordinate magnitude 100,000 m; decoded raster 100 MP; overlay 70 MiB; worker stdout/stderr 1 MiB; DXF worker 30 s.

Decisions still requiring approval: maximum raster side 32,768 px; whole local run 60 s; soft observed working-set target 1.5 GiB. Windows has no claimed portable hard RSS sandbox. Decode/geometry work must run in a killable child process with byte/pixel/component/proposal/output/time limits, bounded logs, no child spawning, and no network. Timeout/cancellation verifies process-tree termination and never publishes a final run; no automatic limit relaxation or in-run retry is allowed.

The local review UI must reject every non-loopback peer and every `Host`/`Origin` not equal to its generated loopback origin; use an unguessable per-launch URL secret plus SameSite=Strict/HttpOnly session cookies and CSRF protection; set `Cache-Control: no-store`; authenticate and record reviewer authority; store drafts in a permission-restricted directory under an explicit retention decision; and never expose directory listings or arbitrary paths.

Local-only means no upload, telemetry export, model call, cloud backup, or network retrieval. Strip EXIF/ICC/comments/GPS/author metadata from rendered source while binding original-byte hash. Keep private Layer B source/overlay untracked. Deterministic artifacts exclude timestamp, duration, hostname, process ID, username, and absolute path; nondeterministic operational facts live in a separate bounded local audit log.

Immediate stop/rollback triggers include path escape/external access, worker escape or unverified termination, hash/provenance mismatch, deterministic mismatch, finalized-run mutation, private-data leakage, incorrect G1 eligibility, critical false opening, or resource use above approved pilot limits.

## 11. Existing-contract migration

Historical schemas, manifests, runs, and evidence remain byte-unchanged and independently valid. No document is relabelled or grandfathered into a recognition claim.

Selected proposed additive migration, pending explicit approval:

- new `floorplan_annotation` version for native line/arc paths, source edges, explicit thickness, scale anchors, confirmed room faces, and append-only edit provenance;
- new `floorplan_parse` version for native line/arc wall paths, explicit sourced thickness, room-face provenance, and reference to an approved raster review run; no candidate/proposal fields;
- new exact-versioned `floorplan_review` contract and immutable review-run lineage binding source, accepted annotation, diagnostic parse, overlays, metrics, edit chain, reviewer authority, and approval;
- if B1 is later approved, a separate `floorplan_proposal` diagnostic contract or explicitly non-envelope workspace format; it cannot masquerade as `floorplan_parse` or `floorplan_annotation`;
- append-only error/status vocabulary with every code mapped to ADR-0005 outcome classes;
- a new contracts bundle only for new runs;
- versioned state-machine amendment making `floorplan_review` a raster-only G1 prerequisite while preserving Product A's machine-verifiable path.

Version numbers are intentionally **not locked in this draft** because the exact catalog state and compatibility classification must be reviewed immediately before approval. The migration gate must choose exact versions and prove historical byte round trips, old-version rejection of new fields, new-consumer handling of old/new versions, stable errors, unchanged canonical output for historical fixtures, and no finalized-run mutation.

`scene_geometry` remains downstream. This PLAN cannot invent wall height, opening height/sill, camera, 3D, or PLAN-003 semantics.

## 12. Phased work packages and dependencies

These are planning packages and exit gates, not implementation authorization or prescribed code changes.

### WP0 — Approval and contract lock

Dependencies: this reviewed PLAN and Moshe's decisions in section 14.

Exit: exact A/B0 scope; room model; geometry semantics; lifecycle/state amendment; schema versions; limits; retention; corpus; threshold profile; reviewer authority; budget; and rollback trigger set are approved. No work beyond planning starts before WP0.

### WP1 — Evaluation and corpus design lock

Depends on WP0 product/geometry/rights decisions.

Exit: versioned label guide, source-family manifest, hard-case minima, split custody, deterministic evaluator specification, threshold profile, and private-data policy are independently reviewed before locked labels are exposed.

### WP2 — Additive contract and lifecycle specification

Depends on WP0 and the evaluation truth model from WP1.

Exit: exact annotation/parse/review schemas, state-machine amendment, error/outcome decision table, migration matrix, and historical compatibility evidence are independently accepted.

### WP3 — Product A bounded capability

Depends on WP2 geometry and room contracts.

Exit: conforming CAD and fail-closed CAD corpus gates, determinism, topology, resource, and overlay gates pass. This work package cannot claim arbitrary CAD support.

### WP4 — Product B0 correction/evidence containment

Depends on WP1 labels and WP2 review lifecycle.

Exit: edit replay, scale, room/topology, security, evidence, per-plan approval, final accuracy, and correction-time value gates pass. B0 remains labelled human-verified.

### WP5 — Integrated shadow and rollback rehearsal

Depends on WP3 and WP4.

Exit: local shadow runs only; no canonical publication from drafts; migration, cancellation, incident, disable-to-baseline, and evidence-redaction drills pass; independent cross-provider review has no unresolved CRITICAL/MAJOR.

### WP6 — Named bounded activation decision

Depends on WP5 and fresh Moshe visual approval of all required evidence.

Exit: Moshe may authorize named local runs only. Default activation, B1, C, PLAN-003, or any Part 2 facility requires separate approval.

### Optional WP-B1 — proposal pilot

Depends on proven B0 baseline, separately approved proposal contract/domain/targets, and hidden-set custody. Stop on failed target, correction-time non-improvement, security/resource breach, or scope ambiguity. It does not block A+B0 closure.

## 13. Schedule and cost options

Ranges are planning estimates for one repository-familiar engineer plus review; they are not commitments and exclude waiting for approvals/private data.

- **Option 1 — preserve current line-only baseline:** 5–8 engineer-days / 1–2 calendar weeks / USD 0 incremental infrastructure. Lowest risk, but does not close arcs/thickness or raster usability.
- **Option 2 — recommended A + B0 remediation:** 7–10 calendar weeks, approximately 300–500 engineering/QA hours plus 120–240 labeling/review hours / USD 0 incremental infrastructure. Includes native line/arc contract work, compliant CAD, detector-free correction UI, locked evaluation, and lifecycle migration.
- **Option 3 — A + B0 plus B1 local proposal pilot:** add 3–5 calendar weeks and 15–25 engineer-days plus labeling time after B0 is proven / USD 0 incremental infrastructure. Continuation depends on proposal and correction-time gates.
- **Product C research:** not estimated or authorized in Part 1. Any later estimate requires a separate rights/model/dependency/compute plan; no universal accuracy guarantee follows.

Moshe must choose a scope and labor/calendar cap. If the approved cap cannot support mandatory safety/evidence gates, scope is reduced or blocked; gates are not weakened.

## 14. Decisions requiring Moshe's explicit approval

Unresolved items are intentionally marked **APPROVAL REQUIRED**:

1. **Product scope:** approve recommended A+B0, choose A-only, or authorize a later separate B1 pilot. C remains deferred.
2. **Geometry:** native line/arc paths; centreline versus paired-edge semantics; sourced/confirmed thickness only; unsupported non-circular curves fail closed.
3. **Room model:** Product A explicit `PWA-ROOM` line/bulge polylines must match derived wall faces; B0 confirms faces derived from corrected walls.
4. **Lifecycle:** approve a new immutable `floorplan_review` run and raster-only G1 prerequisite; until then B0 cannot pass G1.
5. **Threshold profile:** approve Product A exact gates and B0 human-approved gates, including zero observed critical false positives and no population-zero claim.
6. **Corpus:** approve 60 development, 100 locked, 40 regression, optional 200 training families; hard-case minima; rights; hidden-set custody; and all-plan review.
7. **Human reviewer:** Moshe reviews all locked plans or names an authorized delegate before test opening.
8. **Resource limits:** approve or replace 32,768 px max side, 60 s whole-run deadline, and 1.5 GiB soft working-set target; acknowledge Windows hard-RSS residual risk.
9. **Cancellation and retention:** operational-only cancellation vocabulary versus additive status/code; stale staging and private-data retention/purge policy.
10. **Contract versions and state migration:** exact schema/bundle versions, error mappings, and G1 wording after pre-approval catalog review.
11. **Budget/schedule:** select Option 1, 2, or a different bounded cap; no hidden commitment is inferred.
12. **Activation and boundary:** named local pilot only; no H200, GPU, cloud, remote execution, G7, G8, spend, or PLAN-003.

Silence, approval of the prior PLAN, or approval of this draft's prose does not authorize implementation. Approval must identify the exact PLAN file/hash and selected clauses/options.

## 15. Moshe finding-to-requirement-to-gate traceability

| Moshe finding | Planned requirement | Acceptance gate |
|---|---|---|
| roughly 50% useful marking | complete hard-case corpus; per-plan macro plus slice metrics; every locked plan reviewed | all required strata pass; no missing plan/slice; explicit approval for all 100 |
| rotated/angled walls omitted | arbitrary-angle native lines; rotated/angled corpus minima and separate metrics | Product A 100% fixtures; B0 ≥0.995 final slice precision/recall; endpoint/angle tolerances pass |
| curved walls/bay omitted or simplified | native circular arcs and bulge-arc polylines; non-circular curves fail closed | Product A 100% supported arc fixtures; B0 approved arc slice passes; unsupported curve rejected, never approximated silently |
| many openings missing | typed, hosted openings; explicit empty lists; opening recall and correction queue | A recall 1.000; B0 recall ≥0.990; no unresolved opening task |
| false-positive opening | candidates never canonical; host/type/topology rules; critical-decoy suite | zero observed critical accepted false positives across locked set and every approved plan; report statistical upper bound |
| centreline offset | edge/centre/thickness representations separated; normal offset measured | stratum Hausdorff/normal-offset thresholds; half-thickness adversary; unresolved ambiguity blocks |
| wall endpoint overrun | extension prohibited unless explicit; signed under/overrun metrics | p95/max and semantic-junction overrun tolerances; boundary fixtures; topology leak blocks |
| overlapping unreadable IDs | IDs hidden by default; clean/source/diff/audit views; collision checks | zero label collisions at 100/200/400%; contrast/size gates; Moshe legibility yes per plan |
| raster path was manual, not recognition | A/B0/B1/C separation and per-entity method labels | manual/human-edited output labelled human-verified; provenance mislabelling is CRITICAL |
| green tests did not prove real accuracy | independent labels, locked source-family test, deterministic scoring plus human gate | machine thresholds and all-plan human approval are conjunctive; no smoke/hash-equivalence accuracy claim |

## 16. Rollout, rollback, and incidents

Default mode remains current baseline only. New modes are explicit, per-run recorded, default-off, and cannot silently fall back or promote drafts.

Rollout gates are approval; contracts; adversarial verification; deterministic shadow; named bounded pilot; and default-eligibility decision. A green unit suite alone is insufficient.

Rollback disables the affected route, stops new runs, terminates active workers with verification, preserves finalized append-only history, quarantines bounded staging locally, reproduces with synthetic/minimized data, re-runs baseline/adversarial/migration/determinism checks, and requires independent review plus the applicable Moshe gate before re-enable. It never deletes or relabels historical runs and never relaxes a gate.

SEV-1 includes path escape, external access, source disclosure, finalized-run mutation, or unkillable worker. SEV-2 includes nondeterminism, contract misrouting, incorrect G1 eligibility, or resource-control bypass. SEV-3 includes bounded malformed-input/performance defects without integrity impact. Incident records use opaque IDs and sanitized facts only.

## 17. Provider, model, skills, and fallback record

Source design/evaluation/operations inputs:

| Role/artifact | Provider | Requested model | Actual model | Effort | Fallback | Claude `/skills` |
|---|---|---|---|---|---|---|
| critical product/geometry memo `t_66d1d834` | Anthropic / Claude Code | `opus` | `claude-opus-5` | high | none observed | yes; `computer-vision-expert` |
| geometry session | Anthropic | `opus` | `claude-opus-5` | high | none observed | yes; session `81405d64-8518-4e5d-b1ec-ac134c9e59d4` |
| evaluation memo `t_5800b432` | OpenAI Codex | active | `gpt-5.6-sol` | runtime default | none | not a Claude session |
| operations memo `t_1d699970` | OpenAI Codex | active | `gpt-5.6-sol` | runtime default | none | not a Claude session |
| this synthesis `t_e50c0bd4` | OpenAI Codex | active | `gpt-5.6-sol` | runtime default | none observed | not a Claude session |

The earlier preliminary PLAN and review are superseded by this synthesis because their unresolved lifecycle, room-source, B0/B1, metric, and UI-security defects are addressed here. A fresh independent cross-provider review is still required downstream; this draft does not self-approve.

Every future Claude design, implementation, or review session must be instructed to invoke `/skills`, record selected skills, requested and actual provider/model, effort, runtime metadata when exposed, fallback provider/model/reason, and reviewer provider/model. A mismatch or unavailable required opposite-provider reviewer blocks the gate; no silent substitution is permitted.

## 18. Final boundary

This PLAN defines what a later approved remediation must prove. It creates no implementation authorization, schema change, fixture, dataset access, dependency change, state-machine edit, production run, activation, merge, push, or PLAN-003 handoff. Product C and all Part 2 facilities remain deferred. The next step is independent review of this exact draft, remediation of any blocking review finding, and then a separate approval packet asking Moshe to select the decisions in section 14.
