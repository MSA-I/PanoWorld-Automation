# PLAN-002 visual-remediation evaluation and evidence specification

- Status: **PROPOSED — planning only; thresholds require Moshe approval before implementation**
- Date: 2026-08-11
- Scope: replacement acceptance protocol for the rejected PLAN-002 visual gate
- This document creates no fixtures, runs no parser or model, and implements no tests.

## 1. Decision and boundaries

The former NA-4/NA-5 gate proved that the two adapters could emit aligned geometry, but it was not accuracy evidence: the sample had no independent ground truth, omitted known geometry, simplified its angled bay, and produced an overlay whose opaque labels obscured the plan. A successful parse and a plausible-looking composite are therefore insufficient.

The replacement gate has four independent parts:

1. a provenance-controlled, leakage-resistant labeled evaluation corpus;
2. deterministic machine scoring against geometry and topology ground truth;
3. source-versus-overlay evidence that permits inspection without trusting the composite;
4. explicit, per-plan human approval by Moshe (or a named human delegate approved by Moshe).

All four must pass. Machine thresholds never waive human review, and human approval never waives a critical machine failure.

This specification evaluates remediation of wall/opening extraction and visual evidence. It does not silently expand the current PLAN-002 contract. In particular, the current accepted DXF adapter supports `LINE` walls, zero-bulge closed `LWPOLYLINE` rooms and `LINE` doors/windows only; `ARC`, nonzero bulge, spline, block and wall thickness are currently unsupported and must fail closed. Curves and wall thickness are nevertheless represented in the corpus as (a) raster challenges, (b) explicit current-contract rejection cases, and (c) a separately scored future-capability slice only after a later approved contract authorizes them.

## 2. Corpus structure and separation

### 2.1 Units of separation

The split unit is a **source family**, not an exported file. A family contains the same underlying plan and every derivative: rasterization, crop, rotation, rescale, scan, compression, noise, color treatment, PDF render, DXF export, annotation and mirrored/edited variant. All members of a family belong to exactly one split.

Near-duplicate protection is mandatory before locking a split:

- exact SHA-256 on source bytes;
- normalized perceptual-image hash for rasters;
- canonical geometry hash after stripping identifiers and rigid translation;
- provenance/license identifier comparison;
- manual review of every cross-split collision candidate.

No plan, traced redraw, apartment variant, page from the same multi-page document, or synthetic seed/template may cross splits. Augmentation parameters and random seeds are recorded. Test seeds are inaccessible to parser authors until evaluation.

### 2.2 Minimum acceptance corpus

| Partition | Minimum source families | Purpose | Mutable? |
|---|---:|---|---|
| Training pool | 200 | Optional future learned parser only; never acceptance evidence | yes, versioned |
| Development | 60 | Algorithm tuning, label-guideline calibration, threshold dry runs | yes, versioned |
| Deterministic regression fixtures | 40 micro-plans | One defect or boundary condition per fixture | append-only after review |
| Locked acceptance test | 100 | Final machine and human gate | no; changes create a new corpus version |

The training pool may be empty for deterministic/manual systems; it must still be declared as `not_used`. Development and test ground truth must never be used to fit model weights. Thresholds in this document are frozen before the locked test is opened.

### 2.3 Locked test composition

The 100 locked source families comprise:

- 30 clean raster plans (born-digital PNG/JPEG/PDF-page render);
- 30 degraded raster plans (scans or controlled degradations of test-only clean masters);
- 25 supported DXF/CAD plans conforming exactly to the current adapter contract;
- 15 DXF/CAD fail-closed plans containing unsupported or ambiguous semantics.

Required geometric coverage across the 85 positively scored families:

| Feature | Minimum plans | Minimum labeled instances |
|---|---:|---:|
| horizontal walls | 25 | 250 |
| vertical walls | 25 | 250 |
| rotated whole plans (not multiples of 90°) | 12 | 120 |
| angled walls (10°–80° from axes) | 20 | 100 |
| curved walls or arc boundaries in raster | 12 | 40 |
| polyline/segmented curved approximation | 10 | 40 chains |
| exterior wall thickness 0.15–0.45 m | 15 | 100 walls |
| interior wall thickness 0.06–0.20 m | 15 | 100 walls |
| doors | 35 | 200 |
| windows | 35 | 200 |
| plan with no openings | 12 | n/a; all wall locations are negatives |
| ambiguous opening-like symbols | 20 | 120 negatives |
| at least two room scales / mixed wall lengths | 20 | 150 walls |
| clutter/furniture/text/dimensions/hatching | 25 | n/a |
| degraded scan | 30 | n/a |

A plan may satisfy multiple rows. The manifest must prove these minima; aggregate counts without per-plan IDs are not sufficient.

The 15 fail-closed CAD families must include at least two examples each of `ARC`, nonzero-bulge `LWPOLYLINE`, `SPLINE`, `INSERT`/block, nonzero Z/elevation, active/non-empty paperspace, ambiguous duplicate wall match, and unsupported entity on a reserved `PWA-*` layer. Some families may contain more than one condition, but at least eight families must isolate a single condition so the expected terminal finding is unambiguous. External references are represented by inert, non-resolving fixture tokens only and must never be opened.

### 2.4 Quality strata

Each raster receives exactly one primary stratum and any number of secondary tags.

- `R0-clean`: sharp born-digital source, no visible compression damage.
- `R1-light`: mild antialiasing/compression, ≤1° skew, or 150–300 dpi scan.
- `R2-heavy`: blur, bleed-through, folds, stains, broken ink, perspective correction residue, 5–15° rotation, or 75–150 dpi effective resolution; still human-readable.
- `R3-unreadable`: independent annotators cannot reliably recover the required geometry or scale. This is a fail-closed quality fixture, not an accuracy-scored positive.

The 30 degraded test families contain at least 10 `R1`, 15 `R2`, and 5 `R3`. Controlled degradation keeps the clean test-only master and transform recipe in the same family; real scans use the original scan as source and may not claim exact clean-master provenance.

### 2.5 Adversarial regression matrix

This matrix explicitly targets false openings, broken topology, centreline offset/overrun and unreadable labels rather than treating them as incidental aggregate errors.

The 40 micro-plans contain at least the following independently named cases:

1. furniture edge parallel to a wall;
2. dimension-line gap resembling a door;
3. text stroke crossing a wall;
4. stair tread touching a partition;
5. double line / wall-thickness band mistaken for two centrelines;
6. window symbol without a wall break;
7. door swing arc without a leaf gap;
8. decorative arc touching a wall;
9. erased/noisy patch resembling an opening;
10. wall intersection resembling an opening;
11. no-opening plan with dense clutter;
12. opening near a wall endpoint;
13. opening wider than its wall segment;
14. opening offset from wall centreline;
15. opening equidistant from two walls;
16. duplicate opening prediction;
17. two collinear walls separated by a true opening;
18. collinear wall fragments separated by damage, not an opening;
19. T-junction and four-way junction continuity;
20. one-pixel/one-quantum centreline offset;
21. systematic half-thickness centreline bias;
22. wall endpoint overrun into the next room;
23. wall endpoint underrun that breaks a room;
24. acute-angle wall junction;
25. obtuse-angle wall junction;
26. rotated plan at 7°;
27. rotated plan at 37°;
28. circular/curved exterior raster wall;
29. segmented polyline curve;
30. variable wall thickness on one plan;
31. isolated wall not bounding a room;
32. self-intersecting predicted room boundary;
33. duplicated room polygon;
34. interior island/courtyard;
35. absent or contradictory scale;
36. scale bar partially occluded;
37. unreadable label region beneath overlay annotation;
38. dense entity IDs causing label collisions;
39. supported DXF line/polyline case;
40. unsupported DXF arc/bulge case with exact fail-closed finding.

These fixtures are deterministic unit/regression evidence, not a substitute for the locked representative test.

## 3. Ground-truth model and annotation rules

### 3.1 Required files per source family

The planned dataset package for each family must eventually contain:

- immutable source bytes and SHA-256 (or a rights-safe private reference where source redistribution is forbidden);
- source metadata: format, dimensions, units, quality stratum, feature tags, provenance and license/rights status;
- geometry labels in source coordinates and metric coordinates when scale is known;
- scale label with value, evidence type, anchor locations and uncertainty;
- an adjudication record and annotator identities/roles (pseudonymous IDs are allowed);
- deterministic rendering/scoring configuration version;
- split and family ID.

No absolute path, OS username, client filename, private text or unredacted private source enters tracked evidence.

### 3.2 Geometry labels

**Walls.** Label the geometric centreline of the visible wall body, not either ink edge. A straight wall is one directed-agnostic segment between semantic junctions. A polyline is split at junctions or curvature discontinuities and additionally carries a `chain_id`. A curve is stored as its native arc parameters when provenance supports them and as a densely sampled reference curve for scoring. Wall thickness is separately labeled at representative cross-sections; it does not move the centreline.

**Endpoints.** End a wall at its semantic junction with another wall or at its true free end. Do not extend through a crossing. Openings do not split the ground-truth wall centreline; they are intervals attached to that wall. Occluded but unambiguous continuation may be labeled `inferred` and is scored in a separate slice. Ambiguous continuation is masked, not guessed.

**Openings.** A door/window label requires positive source evidence under the labeling guide. Record class, centre projected on its host wall, width along the wall, host-wall ID, visible/evidential status and criticality. A swing arc alone is not a door. A symbol near but not attached to a wall is not an opening. Plans with no openings receive an explicit `openings: []`; absence may not be inferred from a missing file.

**Rooms/topology.** Label closed navigable room faces against wall centrelines, with stable room IDs. Separately derive the expected planar room graph: room nodes, exterior node, and opening-mediated adjacency edges. Curved boundaries use the same sampled tolerance as walls. Uncertain/unreadable regions are masks and cannot be used to hide an entire difficult plan.

**Scale.** Ground truth must come from, in descending order: native CAD units; explicit dimension lines; a scale bar; verified project metadata; multiple documented physical anchors. Conventional door or wall-size assumptions alone are not authoritative test ground truth. Record relative uncertainty. If no anchor reaches the required certainty, label `scale_unknown`; a correct system must fail closed rather than fabricate scale.

### 3.3 Label independence and adjudication

Every locked-test plan is labeled independently by two trained annotators using the same written guide. They may not see parser output. An adjudicator resolves every disagreement above any of these triggers:

- wall endpoint difference > `max(0.02 m, 1 source pixel × true scale)`;
- wall/curve symmetric Hausdorff difference > the same tolerance;
- opening class/host disagreement, centre difference >0.02 m, or width difference >2%;
- any room-count, room-boundary or adjacency disagreement;
- scale difference >0.5%;
- any disagreement over an uncertainty mask.

The final ground truth records both raw annotations, the adjudicated result, reason codes and the adjudicator. A person who authored the parser or its predictions cannot adjudicate the locked test.

### 3.4 Provenance classes

Each family uses one of:

- `native-cad`: geometry derived directly from owned/licensed vector source and independently visually checked;
- `project-synthetic`: generated from a versioned seed and exact generator parameters;
- `dual-human-raster`: two independent human labels plus adjudication;
- `survey-verified`: dimensions tied to a trusted survey/as-built record;
- `private-rights-attested`: source retained outside Git, with Moshe's rights/non-sensitivity attestation and redacted evidence only.

Public-domain or redistributable sources must retain source URL, author, license text/version and retrieval hash. “Found online” is not acceptable provenance. A plan without adequate rights or provenance is excluded, not merely tagged.

## 4. Deterministic scoring protocol

All metrics are computed twice: in metric space where trusted scale exists and in source-pixel/source-unit space. Coordinates are evaluated before PLAN-002's translation normalization, using the recorded inverse transform. Scores use full precision; `QUANTUM_M = 0.0001` is serialization precision, not an accuracy allowance.

### 4.1 Wall matching

Predicted and true wall entities are one-to-one matched per plan using deterministic maximum-cardinality, minimum-cost bipartite matching. Endpoint order is ignored. A straight-wall candidate match requires:

- orientation error ≤2° for length ≥0.50 m and ≤5° for shorter walls;
- symmetric Hausdorff distance ≤ `T_wall`;
- both orientation-invariant endpoint distances ≤ `T_endpoint` after optimal endpoint pairing;
- overlap along the ground-truth tangent ≥90% of the shorter segment;
- no endpoint overrun beyond `T_overrun` at either semantic junction.

Curves/chains are sampled at spacing ≤`min(0.01 m, 0.5 source pixel × true scale)` and matched by symmetric Hausdorff plus length overlap; no prediction receives credit twice through segmentation.

Recommended tolerances:

| Measure | CAD / R0 | R1 | R2 |
|---|---:|---:|---:|
| `T_wall` symmetric Hausdorff | max(0.02 m, 1 px) | max(0.04 m, 2 px) | max(0.06 m, 3 px) |
| `T_endpoint` | max(0.03 m, 2 px) | max(0.05 m, 3 px) | max(0.08 m, 4 px) |
| `T_overrun` at junction/free end | max(0.03 m, 2 px) | max(0.05 m, 3 px) | max(0.08 m, 4 px) |

`px` means the stated pixel count multiplied by trusted metres-per-pixel. For scale-unknown plans, only source-pixel scoring applies and no metric-space pass is claimed.

Report micro and macro precision/recall/F1, per-plan values, p50/p95/max endpoint distance, p50/p95/max symmetric Hausdorff distance, angular error, centreline normal offset, and endpoint overrun/underrun. Macro values average plans equally; a large plan cannot hide a failed small plan.

### 4.2 Opening matching and critical false positives

Opening matching is one-to-one and class-sensitive. A candidate must have the same class and matched host wall, centre distance along the wall ≤`max(0.05 m, 3 px)`, perpendicular distance ≤`max(0.02 m, 2 px)`, and width error ≤`max(0.05 m, 5%)`.

A **critical false positive** is any predicted opening that is unmatched and either:

- creates a room-to-room or room-to-exterior adjacency absent from ground truth;
- occurs in an explicit no-opening plan;
- converts scan damage, furniture, text, a dimension mark, stair tread or decorative symbol into an opening;
- lies outside the host wall or spans a semantic junction;
- changes egress/topological connectivity, regardless of confidence.

Duplicate predictions for one true opening count as one true positive plus false positives for all extras. Class confusion counts as one false positive and one false negative.

### 4.3 Room and topology scoring

For every positively scored plan:

- every emitted room polygon must be simple, positive-area and within the source boundary;
- no duplicate room, unintended overlap, dangling boundary or impossible crossing is allowed;
- room instance match requires polygon IoU ≥0.95 for CAD/R0, ≥0.92 for R1 and ≥0.88 for R2 after tolerance buffering solely for evaluation;
- the room/exterior adjacency graph derived from walls and openings must be isomorphic to ground truth after matched-room ID substitution;
- connected components, room count, exterior leakage and opening-mediated edges are reported separately.

The current PLAN-002 artifact does not emit an adjacency graph; the evaluator derives one without changing the contract. Derived topology is evidence only.

### 4.4 Scale scoring

For plans with authoritative scale:

`relative_scale_error = abs(predicted - true) / true`.

Report per-plan error and p95. A contradictory or absent scale must produce the approved fail-closed scale outcome; supplying a plausible conventional scale is a critical error. Rotation, crop and raster resampling may not change recovered physical scale.

## 5. Recommended acceptance thresholds

These are the recommended strict thresholds for Moshe to approve. Section 5.2 offers one bounded fallback option; no threshold may be selected after viewing locked-test results.

### 5.1 Option A — recommended release gate

All conditions are conjunctive:

**Walls**

- supported DXF/CAD: micro precision ≥0.995, recall ≥0.995, macro F1 ≥0.990;
- R0 clean raster: micro precision ≥0.980, recall ≥0.980, macro F1 ≥0.970;
- R1/R2 degraded raster combined: micro precision ≥0.950, recall ≥0.930, macro F1 ≥0.920;
- angled-wall slice precision and recall each ≥0.950;
- rotated-plan slice precision and recall each ≥0.950;
- curve/polyline raster slice precision ≥0.940 and recall ≥0.900;
- p95 endpoint and symmetric Hausdorff distances are within the stratum tolerances; no single matched wall exceeds 2× its stratum tolerance unless the region was adjudicated uncertain before evaluation.

**Openings**

- all scored plans: micro precision ≥0.995 and recall ≥0.970;
- degraded raster: precision ≥0.990 and recall ≥0.940;
- door and window recall each ≥0.950 overall;
- **zero critical false positives over the entire locked test**;
- every no-opening plan has exactly zero predicted openings;
- p95 centre and width errors satisfy section 4.2.

**Scale and topology**

- CAD/R0 relative scale error: p95 ≤1.0%, maximum ≤2.0%;
- R1/R2 with authoritative scale: p95 ≤2.0%, maximum ≤3.0%;
- 100% exact fail-closed behavior for scale-unknown/contradictory cases;
- 100% structurally valid emitted room polygons;
- exact room count on ≥98% of scored plans and on every CAD/R0 plan;
- exact derived room/exterior adjacency graph on ≥98% of scored plans;
- zero exterior leaks or disconnected fragments caused by endpoint offset/overrun on CAD/R0; at most one non-critical topology miss across all R1/R2 plans, and never on a safety/egress-critical opening.

**Contract rejection**

- all 15 unsupported CAD families reject deterministically with the expected approved finding class;
- no unsupported geometry is silently approximated, dropped, or accepted;
- no external reference is resolved.

### 5.2 Option B — limited pilot only

If Moshe rejects Option A as premature, the only pre-approved alternative to consider is a non-production pilot gate:

- R0 walls precision/recall ≥0.970; R1/R2 ≥0.920/0.900;
- openings precision ≥0.990, recall ≥0.930 overall and ≥0.900 degraded;
- scale p95 limits unchanged;
- topology exact on ≥95% of scored plans;
- **zero critical false positives, 100% CAD fail-closed behavior, overlay rules and per-plan human approval remain unchanged**.

Option B may authorize only a labeled pilot with explicit warnings. It cannot support G1/production acceptance and must create a remediation backlog for every failed Option A slice.

## 6. Overlay legibility and visual approval

### 6.1 Required evidence views per plan

The evaluator must preserve distinct evidence, all bound to the immutable source and prediction hashes:

1. `source` — original source rendered alone (sanitized rendering for tracked raster evidence, original-byte SHA-256 retained separately);
2. `ground-truth` — source plus adjudicated labels;
3. `prediction` — detections alone on a neutral background;
4. `composite` — source plus predictions;
5. `diff` — false positives, false negatives, matched geometry and tolerance bands in distinct colors;
6. `topology` — derived room graph and any broken/leaking junctions;
7. machine-readable per-plan metrics and finding list.

The source and prediction views must not be recoverable only by hiding elements in the composite; each is rendered and hashed separately. SVG source groups may remain toggleable, but the evidence package also contains deterministic browser-rendered PNG captures at 100%, 200% and 400% zoom so review does not depend on one SVG viewer.

### 6.2 Legibility rules

- Entity IDs are hidden by default. Selection/callout or a separate indexed legend exposes them without drawing every ID over the plan.
- Default composite shows wall/opening classes and confidence through unobtrusive styling, not per-entity text.
- Text rendered for review is at least 12 CSS px at the 100% evidence viewport; key legend text is at least 14 CSS px.
- Text/background contrast is ≥4.5:1; non-text geometry contrast is ≥3:1.
- No label may cover an opening marker, junction, detected endpoint, scale anchor, or another label.
- Automated collision checks must report zero label-label intersections and zero label-critical-geometry intersections at all three required zooms.
- Prediction strokes remain distinguishable from source wall strokes in color and dash/style, including a color-vision-deficiency simulation.
- Doors and windows are distinguishable without relying on color alone.
- The source remains inspectable: overlay fill opacity may not obscure wall edges, openings, dimensions used for scale, or ambiguous symbols.
- A legend maps every color/style; units, scale status, quality stratum, corpus/runner version and source/prediction hashes are visible outside the plan area.
- Cropping/viewBox must include all source pixels and every detection; no primitive may be clipped.
- No active/external content, timestamps, private labels, absolute paths or source metadata leakage is allowed.

Automated legibility checks are necessary but not sufficient. If Moshe cannot comfortably trace a wall or identify why an opening was accepted/rejected at 100% and 200%, the plan fails even when collision counts are zero.

### 6.3 Mandatory per-plan human approval

Moshe, or a named delegate explicitly approved by Moshe before test opening, reviews all 100 locked plans. Sampling is forbidden. The approval form records for each plan:

- source readable enough to judge (`yes/no`);
- wall centreline alignment acceptable (`yes/no`);
- endpoints/junctions acceptable (`yes/no`);
- doors/windows correctly located and classified (`yes/no`);
- no false opening affecting topology (`yes/no`);
- room/topology overlay acceptable (`yes/no`);
- scale evidence and displayed units acceptable (`yes/no/not-applicable`);
- overlay legible at 100% and 200% (`yes/no`);
- comments and marked coordinates for every `no`;
- decision, reviewer identity, UTC timestamp, evidence-package hash and signature/approval-record hash.

Every applicable item must be `yes`. Approval cannot be inferred from silence, board completion, a model's assessment or delegated artifact generation. A changed parser, renderer, source, label, threshold, evaluator or browser-rendering baseline invalidates affected approvals and requires a fresh run and fresh human review.

## 7. Severity and fail-closed aggregation

### 7.1 Severity

- `CRITICAL`: fabricated/critical false opening; wrong room/exterior connectivity; invented scale; unsupported CAD accepted or external reference resolved; source/prediction mismatch; evidence tampering/hash failure; private-data leakage; missing human approval.
- `MAJOR`: missed true opening; wall error that breaks topology; centreline bias/endpoint overrun above 2× tolerance; invalid room polygon; scale outside maximum tolerance; unreadable or materially obscuring overlay; required slice below threshold.
- `MINOR`: non-topological geometry error within 2× tolerance; local styling/legend defect that does not prevent judgement; isolated non-critical label collision.
- `INFO`: observation with no acceptance impact.

### 7.2 Aggregation

A candidate passes only when:

1. corpus manifest, labels, provenance and evaluator versions validate and all hashes recompute;
2. deterministic reruns produce byte-identical normalized predictions, metrics and SVG/PNG evidence on the pinned environment;
3. every critical invariant has zero failures;
4. all global, stratum and feature-slice thresholds pass — no averaging across slices to compensate;
5. no plan has a `CRITICAL` finding or unresolved `MAJOR` finding;
6. every plan has an explicit human `approved` record;
7. the aggregate report is signed/hashed and references exactly the reviewed per-plan evidence.

The run fails closed on missing artifacts, missing labels, unknown split membership, source/ground-truth/prediction hash mismatch, evaluator exception, nondeterminism, insufficient required slice count, unavailable evidence rendering, missing approval, threshold ambiguity, or any post-lock corpus/threshold change. A failed run may not be relabeled `partial pass`; corrections require a new immutable run ID.

## 8. Evidence package and deterministic regressions

### 8.1 Planned immutable evidence tree

```text
evidence/PLAN-002/visual-remediation/<run-id>/
  run-manifest.json
  corpus-manifest.json
  threshold-profile.json
  environment.json
  aggregate-metrics.json
  aggregate-report.md
  determinism.json
  approvals.json
  plans/<opaque-plan-id>/
    source-render.png
    ground-truth.svg
    prediction.svg
    composite.svg
    diff.svg
    topology.svg
    rendered-100.png
    rendered-200.png
    rendered-400.png
    metrics.json
    findings.json
    approval.json
```

Private plans use opaque IDs and rights-safe redacted renders only when the approved rights policy permits them; otherwise their evidence remains outside Git and the tracked record contains hashes, counts, metrics and approval only.

`environment.json` records repository commit, dirty-state flag, OS, Python, dependency lock hash, evaluator/rendering-browser versions, locale, fonts, device scale factor, provider/model/fallback metadata for any model-assisted step, and random seeds. Paths and usernames are redacted.

### 8.2 Deterministic regression requirements

The future implementation plan must create tests that prove, without network access:

- split/family leakage detection and manifest count minima;
- exact label-schema and provenance validation;
- endpoint-order-invariant one-to-one wall matching;
- segmentation-neutral curve/polyline matching without double credit;
- opening duplicate/class/host-wall scoring;
- every critical false-positive adversary in section 2.5;
- centreline offset and overrun boundary behavior immediately below, at and above each tolerance;
- scale error and `scale_unknown` fail-closed behavior;
- room polygon validity and graph-isomorphism scoring;
- unsupported DXF exact rejection classes;
- byte-identical metrics and overlays across two clean runs;
- source/prediction/evidence hash binding;
- label-collision, contrast, clipping and active-content checks;
- aggregation cannot pass with a missing plan, missing slice, missing approval, `CRITICAL`, unresolved `MAJOR`, or failed sub-threshold;
- changing any source, label, prediction, threshold, evaluator or rendered view invalidates the approval/evidence hash.

Golden screenshots must be pinned to a rendering environment. Pixel comparison uses exact identity for deterministic same-environment reruns; cross-environment review uses perceptual comparison only as a diagnostic and cannot replace the pinned golden.

## 9. Governance and threshold approval

Before implementation or fixture creation, Moshe must explicitly record:

- `threshold_profile = Option A` (recommended) or `Option B` (pilot only);
- whether any private plans may participate and under what evidence-retention rule;
- the named human delegate, if Moshe will not personally review every plan;
- authorization of any future curve/thickness output contract; absent that approval, such CAD inputs remain fail-closed cases;
- corpus version and the point at which the locked test becomes inaccessible to implementers.

The approval must occur before locked-test evaluation. Results cannot be used to negotiate a lower threshold.

## 10. Agent/session metadata

This specification was authored in the Hermes Kanban worker session for task `t_5800b432`.

- provider: `openai-codex`
- actual model: `gpt-5.6-sol`
- fallback: none used; no silent provider/model substitution
- Claude session: none used
- `/skills` rule: any later Claude authoring or review session must be instructed to invoke `/skills` before work and must record requested provider/model, actual provider/model, effort, fallback provider/model and whether fallback occurred.

No model, parser or production fixture was run for this planning artifact.
