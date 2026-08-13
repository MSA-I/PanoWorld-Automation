# PLAN-002RF approval packet — scope boundaries and measurable acceptance sections

- Date: 2026-08-11
- Kanban task: `t_f5978aca`
- Status: **PROPOSED — PLANNING ONLY; NOT APPROVED FOR IMPLEMENTATION**
- Intended use: drop-in source for the scope and acceptance portions of task `t_301c6952`
- Governing revised plan: `.hermes/plans/2026-08-11-plan-002rf-final-bounded-recognition-remediation.md`
- Governing revised approval packet: `.hermes/plans/2026-08-11-plan-002rf-approval-packet-for-moshe.md`
- Returned decision: Moshe's 2026-08-11 `RETURN WITH CHANGES` requires automatic end-to-end CAD and raster paths, permits human work only for truth/QA/release evaluation, and removes any personal Moshe per-plan review obligation.
- Hard boundary: Local-only Part 1. This document authorizes no implementation, dependency installation, corpus acquisition, network retrieval, compute provisioning, spend, merge/push, activation, PLAN-003, GPU/H200/cloud/remote work, G7, or G8.

## 1. Scope decision proposed for approval

### 1.1 Selected product paths

1. **Product A — `cad_exact`:** deterministic, automatic parsing of an explicit project-owned PWA DXF convention. Product A reads declared semantics; it does not infer arbitrary CAD meaning.
2. **Product B-AUTO — `raster_auto`:** bounded, local CPU-only automatic recognition of one supported raster floorplan or approved rendered PDF page. It automatically recovers scale, native line/circular-arc wall geometry, wall thickness where resolvable, room faces, and typed hosted openings. It emits immutable canonical geometry or fails closed.
3. **Human truth and QA path:** humans create independent evaluation truth, adjudicate truth disagreements, inspect frozen output-versus-truth evidence, and approve/reject an evaluation or release. This path is evidence-only and cannot modify, complete, rescue, tune, or promote product output.

### 1.2 Explicitly rejected or deferred paths

- **B-MANUAL is rejected as a product path:** no marking, tracing, drawing, correction, snapping choice, entity editing, per-plan parameter tuning, or manual rescue occurs between product input and terminal output.
- **Product C is deferred:** no claim or implementation for arbitrary-raster recognition, arbitrary drafting styles, photographs, perspective views, sketches, severe damage, handwriting, unknown symbols, missing/contradictory scale, or non-circular curves.
- Generic CAD layer/symbol inference, inferred room names, inferred opening swing, guessed wall thickness, guessed scale, silent curve approximation, and topology repair that changes semantics are rejected.
- Confidence-based promotion is rejected. Confidence is diagnostic only and cannot waive support, geometry, topology, scale, provenance, security, or evidence gates.
- OCR, learned models, model weights, training, GPU, H200, cloud services, remote inference, network services, and silent dependency additions are not selected.
- No universal, arbitrary-plan, or population-level 100% accuracy promise is selected.

### 1.3 Product execution versus human evidence work

| Activity | Product A/B-AUTO run | Evaluation/QA process |
|---|---:|---:|
| Detect/construct canonical geometry | automatic only | forbidden |
| Mark/draw/edit/correct product geometry | forbidden | forbidden |
| Per-plan tuning or parameter selection | forbidden | forbidden |
| Create independent ground-truth labels | not part of run | required: two labelers per locked plan |
| Adjudicate truth disagreements | not part of run | required: independent adjudicator |
| View frozen output against truth | not part of run | required: pre-named QA delegate on all 100 plans |
| Change output after seeing truth | forbidden | forbidden |
| Approve/reject corpus or release | not part of run | required; records disposition/findings only |
| Personal Moshe review of each plan | not required | not required |

If role separation cannot be staffed, B-AUTO accuracy is **not evaluable** and no B-AUTO accuracy or release claim may be approved. A defect found by QA becomes a new labeled regression and a later separately authorized code/config revision; the original run and review remain immutable.

## 2. Supported/unsupported matrix

| Path/capability | Supported scope | Unsupported or mandatory fail-closed result |
|---|---|---|
| A source envelope | DXF; 2D modelspace; zero elevation; one floor; explicit mm/cm/m units matching the manifest; exact case-sensitive approved `PWA-*` layers | arbitrary layers/symbols; DWG entity parsing; 3D/nonzero Z; paperspace content; multiple layouts/storeys; blocks/`INSERT`; xrefs; images/OLE; hatches; external references |
| A wall primitives | arbitrary-angle `LINE`; bounded circular `ARC`; ordered line/bulge-arc `LWPOLYLINE` paths | SPLINE, ellipse, NURBS, non-circular curves, guessed wall bands, silent tessellation as canonical truth |
| A wall semantics | declared centreline; optional positive `THICKNESS_M` from approved `PWA_METADATA` XDATA; native primitive provenance | interpreting a visible edge as centreline; guessing thickness; hidden offset or extension |
| A junctions | shared source endpoint after canonical `QUANTUM_M = 1e-4 m` quantization | mid-span crossing without shared source vertex; inferred split; snapping, gap closure, extension, or merge |
| A rooms | closed `PWA-ROOM` line/bulge paths on centrelines; exact canonical match to one derived bounded face; `area_basis=centreline` | self-intersection, duplicate/ambiguous/nested mismatch, centreline/clear-face ambiguity, silent clear-area reinterpretation |
| A openings | distinct `door`, `window`, `passage`; unique host; line-on-line or concentric-arc-on-arc; width along host; full span fits | chord-on-arc; leafless passage forced to door; ambiguous/off-host/over-wide/wrong-type/topology-breaking opening; inferred swing/hinge |
| B-AUTO source envelope | exactly one orthographic 2D floor; high-contrast black/white supported linework and fixed symbol guide; PNG/JPEG or approved rendered PDF page; skew within ±5°; at least two machine-readable scale anchors | photos, perspective/isometric, sketches, handwriting, multiple floors, unknown symbols, severe damage/occlusion, missing/contradictory scale, unsupported format/style |
| B-AUTO walls | automatically recovered native straight/circular-arc centrelines; paired-edge thickness or declared single-line convention; arbitrary line angle within envelope | unresolved centreline/thickness; non-circular curve; silent extension; topology-changing repair; any geometry needing human correction |
| B-AUTO rooms | automatically derived simple positive-area bounded faces with intended room/exterior graph | leak, impossible crossing, duplicate/overlap, dangling intended boundary, unresolved room count/face/adjacency |
| B-AUTO openings | automatically classified `door`/`window`/`passage`, unique geometric host, valid centre/width/span and intended adjacency | ambiguous motif/type/host; decorative/text/furniture/scan damage promoted as opening; duplicate or topology-changing false opening |
| Scale | A from explicit matching CAD units; B-AUTO from at least two authoritative anchors | conventional door/wall-size assumption; one unreliable anchor; absent or contradictory anchors; fabricated plausible scale |
| Curves | A and B-AUTO bounded circular arcs represented natively | spline/ellipse/NURBS/non-circular curve; silent segmented approximation as canonical geometry |
| Topology repair | deterministic versioned transforms only within separately approved bounds and only when semantics cannot change | any repair that can create/delete/bridge an opening, change room count/adjacency, or exceed tolerance |
| Authorship/provenance | required product authorship `cad_exact` or `raster_auto`, source class, source binding, and operation/source reference | `annotation` used to disguise machine or human authorship; human-authored product entity; missing/inconsistent authorship |
| Raster manual path | evaluation labels and QA evidence isolated from product output | any manual/semi-automatic product operation, rescue, promotion, or G1 eligibility |
| Downstream 3D | none | `scene_geometry`, Blender, wall height, sill/opening height, camera, render, PLAN-003, G7/G8 |
| Execution location | named Local-only Part 1 work on approved local environment | upload, telemetry, cloud backup, remote model call, GPU/H200, cloud/remote execution, provider spend |

## 3. Achievable accuracy and limitation statement

The only credible exactness claim is: **for inputs that conform exactly to the approved PWA CAD convention, Product A is intended to parse the declared semantics deterministically and exactly under the approved canonicalization and tolerance contract.** This is not a claim about arbitrary CAD.

Product B-AUTO may claim only: **on the predeclared supported raster envelope and exact locked corpus/version, the fully automatic local pipeline met the approved wall, opening, scale, topology, yield, determinism, and evidence gates.** These values are targets until measured; no current B-AUTO accuracy claim exists.

“Zero critical false positives” means zero **observed** across the immutable locked evaluation population and zero on each plan. It is not proof of zero population risk. With zero observed across 60 locked raster families, the required rule-of-three one-sided 95% upper bound is 5.0% per family. Outside the labeled corpus, wording is limited to “automatic checks detected no critical false positive.” Undetected defects remain a named residual risk with an incident and rollback path.

All outputs remain conceptual. They are not architectural/engineering approval, construction documents, permit material, or quantity-survey evidence. Dimensional accuracy depends on authoritative scale and source quality; unsupported or contradictory evidence fails closed.

## 4. Locked acceptance population and anti-gaming rules

### 4.1 Corpus population

The proposed locked test has 100 source families:

- 30 supported clean raster families (`R0`);
- 10 supported light-degradation raster families (`R1`);
- 15 supported heavy-but-human-readable raster families (`R2`);
- 5 unsupported/unreadable raster families (`R3`) expected to fail closed;
- 25 conforming Product A CAD families expected to parse exactly;
- 15 non-conforming CAD families expected to reject with the approved finding class.

The supported B-AUTO denominator is therefore 55 families (`R0+R1+R2`), with clean yield measured over 30 and supported-scan yield over 25 (`R1+R2`). The five `R3` families are refusal tests, not removable from the locked set and not accuracy-scored positives.

The inherited minimum positive-geometry coverage is:

| Feature slice | Minimum plans | Minimum labeled instances |
|---|---:|---:|
| horizontal walls | 25 | 250 walls |
| vertical walls | 25 | 250 walls |
| whole-plan rotation not divisible by 90° | 12 | 120 walls |
| angled walls 10°–80° from axes | 20 | 100 walls |
| circular wall/arc boundaries in raster | 12 | 40 arcs |
| segmented/polyline curved source representation | 10 | 40 chains |
| exterior thickness 0.15–0.45 m | 15 | 100 walls |
| interior thickness 0.06–0.20 m | 15 | 100 walls |
| doors | 35 | 200 openings |
| windows | 35 | 200 openings |
| explicit no-opening plan | 12 | all wall locations are negatives |
| ambiguous opening-like symbols | 20 | 120 negatives |
| mixed scales/wall lengths | 20 | 150 walls |
| clutter/furniture/text/dimensions/hatching | 25 | plan-level tag |
| degraded scan | 30 | plan-level tag |

The 15 fail-closed CAD families retain at least two examples each of `ARC` under the legacy-unsupported convention, nonzero-bulge `LWPOLYLINE`, `SPLINE`, `INSERT`/block, nonzero elevation, non-empty paperspace, ambiguous duplicate wall match, and unsupported entity on a reserved `PWA-*` layer, with at least eight single-defect families. Because PLAN-002RF proposes to make bounded arcs/bulges supported, WP1 must replace the now-obsolete arc/bulge refusal cases with equally explicit out-of-envelope arc/bulge/non-circular-curve cases before corpus lock; the exact replacement mix is unresolved.

Required geometry slices remain declared before test opening: horizontal, vertical, arbitrary-angle, rotated-plan, circular-arc, segmented source representation, exterior/interior thickness, door, window, passage, no-opening, ambiguous opening-like negatives, clutter, mixed wall lengths/scales, and degraded scan. The inherited corpus did not set a `passage` minimum, so that new opening class needs an explicit per-path plan/instance minimum before lock. Corpus minima and family membership must be validated before scoring; insufficient slice count fails the run rather than shrinking the denominator.

### 4.2 Leakage and refusal rules

- Split by source family, including every crop, rotation, rasterization, scan, derivative, PDF page, CAD export, annotation, mirrored/edit variant, generator seed/template, and near duplicate.
- Freeze support labels, test membership, thresholds, matching/evaluator version, and algorithm/config before automatic outputs are generated.
- Freeze automatic outputs before adjudicated truth is opened to developers or QA.
- A rejected supported input receives no true-positive credit. Yield is scored separately so a recognizer cannot inflate accuracy by refusing difficult supported plans.
- An emitted unsupported input is a critical failure; a correct refusal earns refusal credit only.
- Macro scores average plans equally. Micro scores and raw primitive counts are diagnostics and cannot substitute for macro or per-plan floors.
- Aggregate success cannot hide a failing plan or required slice.

## 5. Metric definitions and matching tolerances

### 5.1 Canonical wall matching

Before scoring, truth and prediction undergo the identical frozen canonicalization into maximal tangent-continuous chains split only at semantic junctions defined by the label guide. Matching is deterministic, one-to-one, and no prediction receives credit twice. Opening-host equivalence is geometric—the canonical chain containing the matched centre—not entity-ID equality.

A straight-wall candidate requires:

- orientation error ≤1° for walls ≥0.50 m;
- the relaxed short-wall orientation rule, if selected, only for `[0.20 m, 0.50 m)`; walls below 0.20 m are scored by endpoint/spatial distance only;
- longitudinal overlap ≥95%;
- symmetric source-space Hausdorff distance ≤`max(4 px, 0.025 m)` for raster; pixel terms never apply to CAD;
- endpoint P95 ≤`max(3 px, 0.020 m)` for raster, with signed overrun and underrun reported separately;
- no semantic-junction overrun above the approved tolerance.

A circular-arc candidate additionally requires native primitive-type agreement, radius error ≤2%, sweep overlap ≥95%, and the approved sampled spatial tolerance. Canonical A geometry must match after quantization; evaluation tolerance is not permission to alter Product A source truth.

The revised plan calls for chain-level length-weighted partial credit, but its exact numerator/denominator and partial-overlap formula are not yet frozen. This is **UNRESOLVED U-1** and must be approved before an evaluator or threshold can be locked.

### 5.2 Opening matching and critical false positives

Opening matching is deterministic, one-to-one, and class-sensitive. A true positive requires:

- exact class (`door`, `window`, or `passage`);
- geometrically matched host chain;
- centre error along host ≤`max(4 px, 0.050 m)` for raster;
- perpendicular centre-to-host error within the approved wall spatial tolerance;
- width error ≤`max(0.020 m, 2%)`;
- full span within the host and no semantic-junction crossing.

A duplicate prediction yields at most one true positive; every extra is a false positive. Class confusion is one false positive plus one false negative.

A **critical false positive** is an unmatched or wrongly matched emitted opening that creates a nonexistent room-to-room or room-to-exterior adjacency, appears on a declared no-opening plan, converts clutter/text/dimension/stair/furniture/decorative/scan damage into an opening, lies outside its host, spans a semantic junction, or otherwise changes egress/topological connectivity regardless of confidence.

### 5.3 Scale and topology definitions

- Product A scale error is `abs(emitted_length - source_truth_length) / source_truth_length`, aggregated per plan; every conforming plan must be ≤0.01%.
- B-AUTO requires at least two authoritative machine-readable anchors. The target is median residual ≤1% and anchor disagreement ≤2%.
- The exact residual fit, weighting, and “anchor disagreement” formula are **UNRESOLVED U-2**. They must be frozen before test opening; a plausible scale cannot be accepted under an undefined formula.
- Room topology pass requires every emitted face to be simple, positive-area, nonduplicated, and within the source boundary, plus exact intended room count and exact room/exterior adjacency after matched-room substitution.
- Exterior leak, impossible crossing, unintended overlap, dangling intended boundary, disconnected fragment, false-opening adjacency, or explicit-versus-derived Product A room mismatch is blocking on any emitted plan.

## 6. Measurable acceptance-target table

All rows are conjunctive. “Required evidence” means immutable, hash-bound evidence from the exact candidate/corpus/evaluator/environment versions. Role names marked `TBD` must be filled before lock; a developer or evidence generator cannot self-approve their own gate.

| ID | Metric definition | Threshold | Test population | Pass/fail rule | Required evidence | Accountable approver |
|---|---|---|---|---|---|---|
| AT-01 | Product A conforming-input completion | Canonical output on all conforming cases | 25 conforming CAD families | PASS only if 25/25 emit complete canonical output; any refusal/failure blocks | per-plan result, source/output hashes, findings | independent Contract/Geometry Reviewer (`TBD`) |
| AT-02 | A wall chain precision/recall after canonical matching | 1.000/1.000 per plan and required A slice | 25 conforming CAD families | Any missing/extra/mismatched chain blocks | per-plan match table, chain geometry, slice report | independent Geometry Reviewer (`TBD`) |
| AT-03 | A opening precision/recall with exact class and geometric host | 1.000/1.000 per plan/type | all conforming A plans containing doors/windows/passages plus no-opening negatives | Any FP, FN, wrong class/host, or duplicate blocks | opening match table and topology diff | independent Geometry Reviewer (`TBD`) |
| AT-04 | A scale relative error | ≤0.01% on every plan | 25 conforming CAD families | Any plan above threshold or unit mismatch blocks | source-unit proof and per-plan error | Contract/Geometry Reviewer (`TBD`) |
| AT-05 | A room/face topology | exact explicit/derived face match and 100% intended adjacency | 25 conforming CAD families | Any room mismatch, leak, crossing, dangling boundary, or wrong adjacency blocks | canonical face comparison and graph diff | independent Geometry Reviewer (`TBD`) |
| AT-06 | Unsupported CAD deterministic refusal | correct approved error class; zero canonical acceptance; zero external resolution | 15 fail-closed CAD families | 15/15 must refuse; any accepted unsupported geometry/external read is CRITICAL | terminal code/status/artifact matrix, external-access audit | Contract Reviewer + Security Reviewer (`TBD`) |
| AT-07 | B-AUTO clean supported-set yield | emitted complete canonical output on supported source; refusal receives no accuracy credit | ≥95%; with 30 locked clean families, at least 29 must emit | Fewer than 29 emitted clean plans blocks; emitted plans still must pass all accuracy/topology rows | support labels, emit/refusal ledger, diagnostics by family | Evaluation Owner (`TBD`) + independent QA Lead (`TBD`) |
| AT-08 | B-AUTO supported-scan yield | emitted complete canonical output on predeclared R1/R2 support set | ≥85%; with 25 locked supported scans, at least 22 must emit | Fewer than 22 emitted R1/R2 plans blocks; R3 cannot enter denominator | stratum manifest and emit/refusal ledger | Evaluation Owner + independent QA Lead (`TBD`) |
| AT-09 | B wall chain macro precision/recall | ≥0.995/0.995 macro and in every required slice | emitted supported R0/R1/R2 plans; all predeclared wall slices | Either macro component or any slice component below threshold blocks | per-plan/slice match tables and aggregate recomputation | independent Evaluation Reviewer (`TBD`) |
| AT-10 | B wall per-plan floor | ≥0.980/0.980 | every emitted supported raster plan | Any emitted plan below either floor blocks the corpus | per-plan precision/recall and geometry diff | independent Evaluation Reviewer (`TBD`) |
| AT-11 | B opening macro precision/recall | ≥0.995/0.990 macro | emitted supported R0/R1/R2 plans with explicit empty lists on no-opening plans | Either component below threshold blocks | per-plan/type match tables, macro recomputation | independent Evaluation Reviewer (`TBD`) |
| AT-12 | B opening per-plan floor | ≥0.980/0.980 and exact no-opening behavior | every emitted supported raster plan | Any plan below floor or any predicted opening on a no-opening plan blocks | per-plan opening diff and no-opening ledger | independent Evaluation Reviewer + QA Lead (`TBD`) |
| AT-13 | Critical false positives | zero observed per plan and across the complete locked set | all 100 locked families, including refusals/adversaries | Any critical FP is CRITICAL and blocks; report one-sided 95% bound, including 5.0% for zero/60 raster families | signed critical-FP ledger, topology diffs, bound calculation | independent QA Lead (`TBD`) and Release Approver (`TBD`) |
| AT-14 | Spatial matching tolerances | walls/openings/arcs satisfy §5 thresholds; no matched wall beyond approved maximum | every matched entity on emitted A/B plans; boundary micro-fixtures below/at/above each tolerance | Any out-of-tolerance match accepted as TP or boundary regression blocks | full-precision distance/angle/overlap/error tables and boundary tests | independent Geometry/Evaluation Reviewer (`TBD`) |
| AT-15 | B scale | median anchor residual ≤1%; disagreement ≤2%; unsupported/contradictory cases fail closed | every emitted supported raster with anchors plus scale adversaries | Any emitted plan over limit, invented scale, or incorrect non-refusal blocks | anchor locations/evidence, fit residuals, scale outcome | Geometry Reviewer (`TBD`) |
| AT-16 | B room topology | 100% valid faces and exact intended room/exterior adjacency per emitted plan | every emitted supported raster plan | Any invalid face, room-count mismatch, leak, crossing, dangling boundary, or adjacency mismatch blocks | polygon validator output, room graph, topology diff | independent Geometry Reviewer + QA Lead (`TBD`) |
| AT-17 | Raster unsupported/refusal behavior | no canonical geometry for predeclared unsupported input; stable diagnostic | all 5 R3 plus every unsupported-style/scale regression | Any canonical acceptance or silent approximation is CRITICAL | support classification, terminal outcome, artifact-presence matrix | Evaluation Reviewer (`TBD`) |
| AT-18 | End-to-end automation | no interactive input, marking, correction, per-plan tuning, or truth access; one automatic emit-or-fail-closed outcome | all 100 locked executions and process audit | Any human edit/tuning/manual rescue or output mutation is CRITICAL | stage/event audit, config hash, process trace, immutable output hash | Automation Boundary Reviewer (`TBD`) |
| AT-19 | Deterministic replay | byte-identical A canonical output; byte-identical B outcome/canonical output/diagnostics in pinned environment | two clean runs of every locked family and deterministic micro-fixtures | Any mismatch blocks; cross-environment comparison is normalized-pixel/hash diagnostic only | `environment.json`, two-run hashes, diff report | Reproducibility Reviewer (`TBD`) |
| AT-20 | Corpus validity and leakage | exact population/slice minima; zero cross-split family/near-duplicate leakage; rights complete | entire corpus manifest and all partitions | Missing family/slice/rights record, collision, mutable locked item, or post-lock threshold change blocks before scoring | corpus/split manifest, collision review, rights ledger, hashes | Corpus Rights Owner (`TBD`) + independent Evaluation Reviewer (`TBD`) |
| AT-21 | Human truth independence | two labels without output visibility; independent adjudicator; frozen output first | all 100 locked families | Any role overlap prohibited by the final role matrix, truth leak, or missing adjudication makes B-AUTO non-evaluable | signed role/visibility ledger, raw labels, adjudication records, output-freeze time/hash | Evaluation Governance Approver (`TBD`) |
| AT-22 | Per-plan QA | QA delegate reviews all required frozen output/truth views; no sampling/editing | all 100 locked families | Every applicable checklist item must pass; missing plan/approval or any unresolved CRITICAL/MAJOR blocks | immutable per-plan QA dispositions and lineage heads | pre-named QA Delegate (`TBD`), not necessarily Moshe |
| AT-23 | Evidence completeness/legibility | eight hash-bound views/records, deterministic SVG and 100/200/400% PNG; no collision/clipping/active content; required contrast/CVD | all 100 locked families | Missing/hash-mismatched/unreadable evidence or unresolved MAJOR blocks | source, truth, geometry, composite, diff, topology, metrics/findings, QA lineage; zoom renders; collision/contrast report | QA Lead + Security Reviewer (`TBD`) |
| AT-24 | Security/resource boundary | all approved input/output/time/process/UI/containment controls hold | adversarial matrix plus every locked run | Any path escape, external/network access, source disclosure, unverified worker termination, finalized mutation, or cap bypass blocks and triggers rollback | security test report, resource ledger, kill-tree/finalization evidence | Security Reviewer (`TBD`) |
| AT-25 | Local-only Part 1 boundary | zero pipeline upload/telemetry/model call/cloud backup/network retrieval/GPU/H200/remote/G7/G8/PLAN-003/spend | complete work-package audit | Any prohibited action blocks and requires incident review | environment/network/process/dependency/change audit | Moshe for scope authorization; Security Reviewer for evidence |
| AT-26 | Release aggregation | all AT rows applicable to selected product pass; no CRITICAL or unresolved MAJOR; lineage head current | exact candidate + exact locked corpus/evaluator/environment | Conjunctive pass only; no “partial pass,” averaging waiver, or approval by silence | signed aggregate report referencing every exact artifact/hash | named Release Approver (`TBD`); Moshe approves scope/targets, not every plan |

## 7. Required evidence per locked plan

Each family must have separately rendered and hash-bound:

1. sanitized source-only view with original-byte binding;
2. adjudicated truth over source;
3. accepted automatic geometry alone;
4. source plus accepted automatic geometry;
5. matched/false-positive/false-negative/tolerance diff;
6. topology, leak, and junction view;
7. machine-readable metrics and findings;
8. immutable per-plan QA disposition and current approval lineage head.

Deterministic PNG captures at 100%, 200%, and 400% accompany SVG evidence. The package must also bind source, truth, automatic output, algorithm/config, threshold profile, evaluator, renderer, environment, corpus, and QA record hashes.

Legibility requirements:

- entity IDs/confidence are not always visible over geometry;
- text ≥12 CSS px and legend ≥14 CSS px at 100%; text contrast ≥4.5:1; geometry contrast ≥3:1;
- door/window/passage remain distinguishable without color alone;
- zero glyph-box/glyph-box and glyph-box/critical-geometry collisions;
- accepted strokes retain ≥3:1 contrast under the selected protanopia/deuteranopia/tritanopia simulation;
- no clipping, script, external URL, `foreignObject`, private label/path/username, EXIF/GPS/author/comment metadata, timestamp, or active content.

## 8. Human approval and accountability boundaries

- **Moshe:** approves or rejects the exact product path, support envelope, geometry semantics, threshold profile, resource/security limits, cost/schedule cap, and Local-only Part 1 boundary. He is not required to review each locked plan.
- **Corpus Rights Owner (`TBD`):** attests source rights, provenance, sensitivity, retention, and zero-spend constraints before acquisition/use.
- **Two labelers + adjudicator (`TBD per plan`):** create independent truth without product-output visibility. They do not edit product output.
- **QA Delegate/Lead (`TBD`):** reviews every frozen comparison, records findings/disposition, and cannot modify output or truth.
- **Independent Geometry/Evaluation/Security Reviewers (`TBD`):** approve their evidence domains; implementers and evidence producers cannot self-approve.
- **Release Approver (`TBD`):** accepts only the conjunctive aggregate with a current immutable lineage head.

No role may infer approval from silence, task completion, a model judgment, or a prior artifact hash. A changed source, algorithm/config, renderer/font, label/adjudication, threshold, evaluator, environment baseline, or evidence view invalidates affected approval through a new immutable lineage record and requires fresh scoring/review.

## 9. Local-only Part 1 boundaries

Included only after later separate approvals:

- decision/ADR and feasibility-spike planning;
- rights-approved local corpus/evaluator preparation;
- additive exact-version contract and immutable-lineage planning;
- local Product A implementation/evaluation;
- local CPU-only B-AUTO feasibility, implementation, shadow evaluation, and named pilot planning;
- local deterministic evidence generation, QA, rollback rehearsal, and security testing.

Excluded and unauthorized by this artifact:

- production implementation or activation now;
- installation or dependency/lock change now;
- corpus acquisition or network retrieval now;
- remote execution, upload, telemetry, cloud backup, remote model/API call;
- GPU/H200 provisioning or use, cloud vendor account, purchase, spend, G7, or G8;
- PLAN-003, Blender, `scene_geometry`, wall/opening heights, cameras, rendering, packaging, or PanoWorld execution;
- merge, push, deploy, or default-route change.

The proposed local caps remain approval items: existing 50 MiB source, 200,000 DXF entities, 5 MiB annotation, 20,000/5,000/20,000 walls/rooms/openings, 10,000 vertices, 100,000 m coordinate magnitude, 100 MP raster, 70 MiB overlay, 1 MiB worker output, and 30 s DXF worker; plus proposed 32,768 px maximum side, 60 s whole run, and 1.5 GiB soft observed working-set target. Windows has no claimed portable hard-RSS sandbox.

## 10. Unresolved choices — no commitment may be inferred

| ID | Unresolved choice | Why it blocks measurement/approval | Required decision owner |
|---|---|---|---|
| U-1 | Exact length-weighted chain precision/recall partial-credit formula | AT-09/10 cannot be independently recomputed from prose alone | Moshe approves recommendation; Evaluation Reviewer freezes formula |
| U-2 | Exact two-anchor scale fit, residual weighting, and disagreement formula | AT-15 threshold is numerically stated but metric remains ambiguous | Moshe + Geometry/Evaluation Reviewer |
| U-3 | Exact bounded radius/sweep range and sampling rule for supported circular arcs | “bounded circular arc” and arc spatial matching are not fully executable | Moshe + Geometry Reviewer |
| U-4 | Exact deterministic transform bounds for clustering/gap closure/merge/T-split/tangent join/dedup | B-AUTO may otherwise perform semantic repair under an undefined tolerance | Moshe + Contract/Geometry Reviewer |
| U-5 | Complete fixed B-AUTO symbol/style guide and machine-readable support classifier criteria | Supported-set membership and refusal/yield can otherwise be gamed after results | Moshe + Evaluation Owner |
| U-6 | Named labelers, adjudicator, QA delegate, independent reviewers, release approver, and forbidden role-overlap matrix | Human independence and accountable approval cannot be verified with role placeholders | Moshe/Evaluation Governance Approver |
| U-7 | Corpus sources, licenses, rights owner, private-data/retention policy, and whether zero-spend is feasible | No lawful corpus or honest cost claim exists until fixed | Moshe + Corpus Rights Owner |
| U-8 | Exact Pillow/NumPy CPU feasibility-spike protocol and stop thresholds | B-AUTO accuracy/yield/60 s feasibility is presently unproven | Moshe approves WP0 scope; independent reviewer judges evidence |
| U-9 | Exact schema versions, `authorship`/`source_class`, review-lineage shape, conditional G1 contract, and new topology codes | Current contracts cannot carry all proposed semantics | Moshe through separately reviewed ADR/PLAN; Contract Reviewer |
| U-10 | Whether proposed 32,768 px, 60 s, and 1.5 GiB values are accepted on the target workstation | Values are planning recommendations without benchmark evidence | Moshe + Security/Performance Reviewer |
| U-11 | Exact pinned renderer/font/CVD transform implementation and normalized-pixel hash contract | AT-19/23 determinism and legibility are not executable until fixed | QA/Security/Reproducibility Reviewers |
| U-12 | Final labor/cost cap and consequence if constrained below Option 2B | Scope/yield must shrink; gates and automatic-only boundary may not be weakened | Moshe |
| U-13 | Replacement fail-closed CAD composition after arcs/bulges become supported, plus minimum `passage` coverage for A and B-AUTO | The inherited corpus conflicts with the new Product A envelope and has no passage denominator | Moshe + Corpus/Evaluation/Geometry Reviewers |

Until these are explicitly resolved, they remain choices—not defaults, implementation instructions, or implied approval.

## 11. Scope/acceptance decision form for parent packet

Moshe should approve, reject, or return changes against an exact file hash for each:

1. Product path: A+B-AUTO, with A-only as explicit fallback; B-MANUAL rejected and C deferred.
2. End-to-end automatic execution: zero product marking/drawing/correction/per-plan tuning/manual rescue.
3. Product A geometry: native arbitrary-angle lines, bounded circular arcs, line/bulge paths, centreline rooms, explicit thickness, and door/window/passage.
4. Product B-AUTO support envelope and fail-closed exclusions.
5. Human obligations: two truth labels, independent adjudication, frozen-output QA on all 100, no output edits, no personal Moshe per-plan review.
6. Wall/opening thresholds and the per-plan, slice, macro, spatial, and yield gates in AT-01..AT-12/14.
7. Zero-critical-FP definition, zero-observed rule, 95% bound, and residual-risk wording.
8. Scale formulas/thresholds and fail-closed unknown/contradictory behavior.
9. Exact room/adjacency topology and blocking findings.
10. Corpus population, leakage controls, rights governance, and refusal/yield denominators.
11. Evidence, determinism, legibility, security, and immutable review-lineage requirements.
12. Accountable human roles and separation rules, including every `TBD` appointment before lock.
13. Resource limits, Windows hard-RSS residual, and CPU-only feasibility stop.
14. Cost/schedule cap and rule that constraints reduce scope/yield rather than add manual operation or weaken gates.
15. Local-only Part 1/no-current-implementation boundary, including no H200/GPU/cloud/remote/G7/G8/spend/PLAN-003.
16. Every U-1..U-13 unresolved item, either by explicit resolution or explicit continued block.

# BLOCKED — pending explicit scope, metric-definition, accountable-role, corpus, and acceptance-target decisions; planning only
