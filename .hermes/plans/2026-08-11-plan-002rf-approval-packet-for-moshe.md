# PLAN-002RF approval packet for Moshe

- Date: 2026-08-11
- Decision state: **BLOCKED — revised after RETURN WITH CHANGES; explicit approval/rejection required**
- Exact plan: `.hermes/plans/2026-08-11-plan-002rf-final-bounded-recognition-remediation.md`
- Revised plan SHA-256: `de506463fedfe5b233215b15914d009502e3dfbb85ab3dc683b1f61f5ab9ea10`
- Returned baseline plan SHA-256: `64d176220a68593d7e5ee5070df5fe8e81ca6dadc5184155cd6f3bb0c5a6554a`
- Reviewed predecessor SHA-256: `1c466214c1231cbc790cf534984eadf8762ec30022f21a6a69b64a69d9992562`
- Independent review: `.hermes/reviews/independent-anthropic-plan-002r-review-20260811.md`
- Independent-review verdict on predecessor: **NOT READY — 15 blocking, 8 major, 1 minor**
- This packet incorporates/disposes all F-1..F-24 findings; it does not self-approve.

## 1. Executive summary

The revised recommended bounded path is **A + B-AUTO**:

- A: exact deterministic parsing of a narrow, project-owned PWA CAD convention.
- B-AUTO: automatic local CPU-only recognition of a narrow raster envelope, from source to canonical walls/rooms/scale/openings, with no marking, drawing, correction, or per-plan tuning during product execution. Every run emits machine-generated geometry or fails closed.

The proposal explicitly rejects manual/semi-automatic raster operation, defers Product C arbitrary-raster recognition, and rejects generic CAD inference, silent topology repair, automatic promotion by confidence, and any promise of universal 100% automatic accuracy. Humans provide truth labels, adjudication, QA, and release acceptance only; they cannot alter the automatic output under test. Moshe has no personal review obligation.

Approval means only: Moshe accepts the exact product scope, geometry contract, human obligations, quantitative gates, local resource/security envelope, cost range, and migration direction so later work may be separately planned and tracked. It does **not** authorize implementation, production code edits, dependency installation, corpus retrieval, compute provisioning, merge/push, activation, PLAN-003, GPU/H200/cloud, G7/G8, or spend.

## 2. Selected and rejected scope

| Area | Proposed selection | Explicitly not selected |
|---|---|---|
| Product | A + B-AUTO | manual/semi-automatic product flow; C; arbitrary CAD/raster automation |
| CAD geometry | arbitrary-angle lines, bounded circular arcs, line/bulge paths, centreline rooms, door/window/passage | SPLINE/ellipse/NURBS, 3D, blocks/xrefs, inferred symbols, silent repair |
| Raster geometry | automatically recovered native line/arc centrelines and thickness; automatically derived faces; typed uniquely hosted openings | unknown symbols, non-circular curves, unresolvable scale/topology, any output needing human correction |
| Truth label | product output `cad_exact` or `raster_auto`; human labels isolated to evaluation | manual annotations in product output; candidates in canonical geometry |
| Lifecycle | immutable review run plus immutable supersession/invalidation lineage | mutating finalized approvals or informal G1 exceptions |
| Deployment | named Local-only Part 1 pilot after separate later gates | remote/cloud/GPU/H200/G7/G8/PLAN-003/default activation |

## 3. Achievable accuracy statement

Exact A behavior is credible only inside the approved CAD convention. B-AUTO may target high automatic accuracy only on the declared raster envelope. These are acceptance goals, not a current claim; no release claim exists until the locked gates pass. Zero-critical-false-positive means zero **observed** in the locked corpus, not zero population risk. With zero observed across 60 raster families, the required rule-of-three one-sided 95% upper bound is 5.0% per family. Outside the corpus, wording is limited to “automatic checks detected no critical false positive.” Human QA supports evaluation/release and is not a per-run product dependency.

## 4. Supported/unsupported matrix

| Path | Supported | Unsupported/fail-closed |
|---|---|---|
| A input | 2D single-floor DXF, zero elevation, explicit units, exact PWA layers | arbitrary layers/symbols, 3D, paperspace, block/xref/image/OLE/hatch/multiple-layout content |
| A wall/room | line/arc paths; room centreline polylines exactly matching quantized derived faces | non-circular curves, midpoint crossings without shared source endpoint, ambiguous centreline/area basis |
| A openings | distinct door/window/passage; line-on-line or concentric-arc-on-arc; unique host | chord-on-arc, omitted passage semantics, ambiguous/off-host/over-wide/topology-breaking |
| B-AUTO source | one orthographic floor; high-contrast fixed line/symbol guide; ±5° skew; two machine-readable scale anchors | photos, perspective, sketches, severe damage/occlusion, handwriting, multiple floors, contradictory/missing scale |
| B-AUTO output | machine-generated lines/arcs, thickness, rooms, typed uniquely hosted openings, deterministic recognition replay | unresolved ambiguity, unsupported style/symbol, non-circular curves, silent semantic repair, any manual rescue |
| B-MANUAL/C | no product support in this approval | marking/correction/tuning during execution; arbitrary-raster claims; OCR/models/training/weights |

## 5. Proposed acceptance-target table

| Target | A | B-AUTO |
|---|---:|---:|
| wall chain precision/recall | 1.000/1.000 per plan/slice | macro and each required slice ≥0.995/0.995; each plan ≥0.980/0.980 |
| opening precision/recall | 1.000/1.000 | macro ≥0.995/0.990; each plan ≥0.980/0.980 |
| critical false positives | zero observed | zero observed per plan and locked set; statistical upper bound reported |
| topology | 100%; exact explicit/derived match | 100% faces and intended adjacency per plan |
| scale | ≤0.01% relative error | two-anchor median residual ≤1%; disagreement ≤2% |
| determinism | byte-identical canonical output | byte-identical outcome, canonical output, and diagnostics in pinned environment |
| unresolved findings | none | none |
| automation | no interactive step | 100% emit-or-fail-closed; zero marking/drawing/correction/per-plan tuning |
| supported-set yield | n/a | ≥95% emit on clean and ≥85% on supported scans, reported by stratum; rejected inputs earn no accuracy credit |

Matching is canonical chain-level after identical label/prediction normalization. Raw primitive counts are diagnostics. Opening-host match is geometric, never entity-ID based. Proposed tolerances restore the geometry memo: line orientation ≤1°, overlap ≥95%, opening width error ≤`max(0.020 m, 2%)`. Pixel tolerances apply only to raster at adjudicated resolution. Aggregate scores cannot hide one failing plan.

## 6. Human-QA obligations and product separation

- Every locked plan gets two independent labels plus independent adjudication.
- Automatic outputs are frozen before adjudicated truth is opened.
- A pre-named QA delegate reviews all 100 frozen output/truth comparisons; no sampling. Moshe personally is not required to review them.
- QA records pass/fail and findings only. It may not mark, draw, correct, tune, complete, or promote a run by altering its geometry.
- A defect becomes a new labeled regression and a later separately approved code/config revision; the original run stays immutable.
- Machine and QA release gates are conjunctive; neither waives the other. Product execution itself has no human step.
- If label/adjudication separation cannot be staffed, B-AUTO accuracy is non-evaluable and cannot be approved.
- Any changed source, algorithm/config, renderer, label, threshold, evaluator, or rendering baseline creates immutable invalidation/supersession and requires affected re-review.

## 7. Evidence requirements

Each locked plan requires separately hash-bound source-only, truth-overlay, geometry-only, composite, FP/FN/tolerance diff, topology view, metrics/findings, and immutable approval/lineage artifacts. PNG captures are required at 100%, 200%, and 400%, alongside deterministic SVG.

Recommended tooling stays inside the locked dependency set: direct Pillow/NumPy rendering; fixed NumPy thresholding, connected components, line/arc voting, paired-edge analysis, bounded symbol templates, topology search/face derivation, and CVD transforms. No OCR, learned model, browser, or network service is selected. A separately authorized WP0 spike must prove CPU-only feasibility against the hardest clean-raster stratum; failure stops for a revised dependency/model/license/compute decision. No silent dependency or manual fallback.

Evidence also includes `environment.json`, bundled-font hash, sRGB conversion, stripped nondeterministic PNG metadata, normalized-pixel hashes, active-content rejection, measurable glyph/geometry collision checks, and ≥3:1 CVD geometry contrast under protanopia/deuteranopia/tritanopia simulation.

## 8. Phased schedule/cost options

| Choice | Scope | Estimate | Consequence |
|---|---|---|---|
| 1 | Preserve line-only baseline | 1–2 weeks; 5–8 engineer-days | does not solve arc/thickness/raster rejection |
| 2A | A only | 4–7 weeks; 180–300 engineering/QA h; 40–80 corpus/review h | safest automatic claim; raster need remains unmet |
| 2B recommended | A + B-AUTO | 16–26 weeks; 700–1,200 engineering/QA h; 260–520 labeling/corpus/adjudication h; 20–50 delegated QA h | bounded CAD plus bounded automatic raster; high technical risk; staged stop/go |
| 3 later | broaden B-AUTO styles | unestimated; new corpus/gates required | separate approval; no manual fallback |
| C | arbitrary raster research | unestimated and unauthorized | separate rights/model/compute plan |

The locked set alone needs 200 independent labels, or 100–200 hours at 30–60 minutes each, before adjudication/development/regression/QA work. The larger engineering range reflects automatic scale, line/arc, symbol, host, and topology recovery without operator correction. Re-review after invalidation is unbudgeted contingency requiring a fresh cap. USD 0 incremental infrastructure is conditional on the CPU-only no-new-dependency path and zero-cost rights-cleared corpus; it is not an unconditional promise. A lower cap reduces support/yield instead of adding manual operation or weakening gates.

Phases are WP0 decision/ADR/CPU-feasibility-spike plan; WP1 corpus/evaluator lock; WP2 additive contracts/lifecycle; WP3 A; WP4 B-AUTO clean-raster engine; WP5 supported-scan hardening/local shadow/rollback; WP6 named activation decision. Each phase stops rather than routing to manual correction. This packet starts none of them.

## 9. Risks and residuals

| Risk | Control / decision impact |
|---|---|
| finite data cannot prove population zero | exact 95% bound and residual-risk wording; incident path |
| evaluator leakage/self-scoring | family splits, hidden labels, output freeze before adjudication, independent QA |
| geometry ambiguity | narrow support matrix, exact semantics, fail closed |
| false opening changes connectivity | typed hosted opening gates; zero observed critical FP; topology checks; human review |
| approval becomes stale | immutable lineage-head invalidation/supersession |
| local UI attack/path escape | loopback+Host/Origin, per-launch secret, strict cookie/CSRF, no-store, containment tests |
| Windows lacks portable hard RSS cap | killable child, soft 1.5 GiB target, bounded inputs/time/output, verified termination |
| deterministic renderer variance | pinned font/environment, metadata stripping, normalized pixel hashes |
| CPU-only automatic approach infeasible | stop and return for explicit dependency/model/license/compute/hour approval; no manual fallback |
| rights/privacy failure | out-of-band acquisition gate, named rights owner, private Layer B local/untracked |
| labor overrun | select cap; reduce scope rather than weaken gates; re-review requires fresh decision |

## 10. Security/resource constraints

Local-only means no pipeline upload, telemetry, model call, cloud backup, or network retrieval. UI is loopback-only with exact Host/Origin, unguessable launch URL, SameSite=Strict/HttpOnly cookies, CSRF, no-store, authenticated authority, permission-restricted drafts, and no path/listing exposure.

Existing limits remain: 50 MiB source, 200,000 DXF entities, 5 MiB annotation, 20,000/5,000/20,000 walls/rooms/openings, 10,000 vertices, 100,000 m coordinate magnitude, 100 MP raster, 70 MiB overlay, 1 MiB worker output, 30 s DXF worker. Proposed new limits are 32,768 px side, 60 s whole run, and 1.5 GiB soft working set. No child spawn, network, auto-relaxation, or in-run retry.

Required security evidence covers non-loopback/Host/Origin rejection, CSRF replay, cookie/cache headers, traversal/symlink/reparse escape, listings/authentication, process-tree termination, and kill-during-finalization atomicity.

## 11. Migration, rollback, and activation impact

The migration is additive and new-runs-only: product authorship restricted to `cad_exact`/`raster_auto`, human labels isolated in evaluation contracts, `source_class`, native line/arc and room-area semantics, `passage`, recognition diagnostics, exact-version `floorplan_review`, immutable lineage, conditional G1 artifacts, and new blocking topology codes. Historical artifacts remain byte-unchanged. ADR-0006 must record ADR-0004 supersession; every decision becomes a numbered `D-0xx` before implementation.

Default stays on the current baseline. New routes are default-off and named per run. Rollback disables the route, blocks new runs, verifies worker termination, preserves finalized history, quarantines bounded staging, reruns baseline/adversarial/migration/determinism checks, and requires independent review plus Moshe's gate before re-enable. `scene_geometry`, PLAN-003, wall height, sill/opening height, camera, and 3D semantics are unaffected and unauthorized.

## 12. Reviewer findings and dispositions

All independent findings are incorporated:

- F-1..F-4: ADR supersession, machine authorship carrier, immutable invalidation lineage, conditional G1/source class.
- F-5..F-7: segmentation-neutral metrics, per-plan floors, output freeze plus independent label/adjudication/QA roles.
- F-8..F-10: CPU-only automatic recognition/evidence option with feasibility stop, lawful out-of-band corpus acquisition, exact Product A geometry/thickness/area semantics.
- F-11..F-15: passage type, exact statistical statement, realistic labor/review budget, restored provider dissent/session, append-only topology codes.
- F-16: exact hashes recorded; Git commit anchor remains required before implementation/release because this planning card does not commit.
- F-17..F-20: append-only recognition provenance/immutable reruns, environment fingerprint, measurable legibility/CVD, containment/cancellation adversaries.
- F-21..F-24: restored tighter tolerances, B-AUTO diagnostic confidence rule, external legacy index, corrected scale/sRGB wording.

Moshe's RETURN WITH CHANGES supersedes the reviewer's B0/manual-product recommendation: manual marking/correction is removed from execution and human work is QA/evaluation only. Other reviewer dispositions remain: add `passage`; use XDATA `PWA_METADATA/THICKNESS_M`; attempt a bounded CPU-only Pillow/NumPy path with a feasibility stop; treat A+B-AUTO as recommended while preserving A-only as an explicit fallback decision.

### 12.1 Disposition of Moshe's 2026-08-11 RETURN WITH CHANGES

| Returned item | Disposition in this revision |
|---|---|
| 1 — returned artifact/hash is a baseline, not final approval | preserved as the returned-baseline hash; this packet identifies a new exact revised-plan hash |
| 2 — both CAD and raster must be automatic end to end | replaced B0 with A+B-AUTO; defined fixed emit-or-fail-closed stages and explicitly rejected product marking/drawing/correction/tuning |
| 3–4 — geometry and CAD semantics approved | retained unchanged: lines/bounded arcs, centreline rooms, quantized junctions, XDATA thickness, door/window/passage |
| 5 — no personal Moshe review; human work is QA only | removed Moshe/operator roles; retained independent truth labels/adjudication and pre-named delegated QA over frozen outputs, with no output editing |
| 6–14 — targets approved subject to automatic path | retained and adapted; added automation and emit-yield gates, automatic replay, CPU-only feasibility stop, revised cost/schedule, and unchanged Local-only boundary |
| 15 — return with changes | remains BLOCKED until Moshe approves or rejects this revised exact scope, hash, and targets |

## 13. Complete provider/model/fallback metadata

| Work | Provider | Requested / actual | Effort/runtime | Fallback | Skills/session |
|---|---|---|---|---|---|
| early geometry synthesis | Anthropic via Claude Code | opus / claude-opus-5 | high requested; runtime unavailable | none observed | `e89cd83c-215a-430e-a058-664d64724fae`; skill metadata unavailable |
| critical geometry memo | Anthropic via Claude Code | opus / claude-opus-5 | high; runtime unavailable | none observed | computer-vision-expert; `81405d64-8518-4e5d-b1ec-ac134c9e59d4` |
| evaluation memo | OpenAI Codex | active/default / gpt-5.6-sol | not exposed | none observed | no Claude skills |
| operations memo | OpenAI Codex | active/default / gpt-5.6-sol | not exposed | none observed | no Claude skills |
| PLAN-002R synthesis | OpenAI Codex | active/default / gpt-5.6-sol | not exposed | none observed | no Claude skills |
| independent review | Anthropic via Claude Code | opus / claude-opus-5 | plan mode; 833.342 s wall; 798.428 s API; 26 turns; effort field unavailable | none observed | computer-vision-expert, advanced-evaluation, threat-modeling-expert; `53971edf-2b1e-48b8-86a9-3f81040a5dbb` |
| final packet | OpenAI Codex | active/default / gpt-5.6-sol | not exposed | none observed at authoring | Hermes kanban-worker; no Claude session |
| automatic-only revision after Moshe decision | OpenAI Codex | active/default / gpt-5.6-sol | not exposed | none observed at revision | Hermes kanban-worker + plan; Kanban run 35; no Claude session |

The early A-only dissent and later Anthropic A+B0 recommendation remain historical context. Moshe's RETURN WITH CHANGES replaces the recommended product path with A+B-AUTO; A-only remains selectable. Unknown metadata is marked unavailable rather than guessed.

## 14. Concise decision form — Moshe must answer every line

Respond with **APPROVE** or **REJECT/CHANGE** for each item; no blank is treated as approval.

1. **Exact artifact:** APPROVE / REJECT the revised plan and hash stated at the top of this packet.
2. **Product path:** APPROVE recommended **A+B-AUTO** / CHANGE to **A-only** / REJECT. Manual/semi-automatic operation and C remain excluded.
3. **Geometry coverage:** APPROVE native arbitrary-angle lines + bounded circular arcs + line/bulge paths; non-circular curves fail closed.
4. **CAD semantics:** APPROVE centreline rooms, quantized shared-endpoint junctions, exact room/face match, XDATA `PWA_METADATA/THICKNESS_M`, and distinct door/window/passage.
5. **Automation/Human-QA:** APPROVE zero marking/drawing/correction/per-plan tuning in product runs; two truth labels + adjudicator; frozen-output QA by a pre-named delegate on all 100 plans; no personal Moshe review; QA records findings but cannot edit output.
6. **Wall/opening thresholds:** APPROVE A 1.000/1.000; B-AUTO macro/slice wall ≥0.995/0.995 and opening ≥0.995/0.990; each emitted plan wall/opening ≥0.980/0.980; ≤1° line angle, ≥95% overlap, width error ≤`max(0.020 m,2%)`; supported-set emit yield ≥95% clean/≥85% scans.
7. **Zero-critical-FP rule:** APPROVE zero observed per plan/locked set, 95% `3/n` bound, and explicit residual risk outside corpus; no population-zero claim.
8. **Spatial/scale tolerances:** APPROVE A scale ≤0.01%; B-AUTO two-anchor median residual ≤1% and disagreement ≤2%; unsupported/contradictory scale fails closed.
9. **Topology:** APPROVE 100% valid room faces/intended adjacency per plan; exterior leak, impossible crossing, dangling intended boundary, false-opening topology change, or room mismatch blocks.
10. **Contracts/lifecycle:** APPROVE required authorship/source_class, immutable review lineage, raster-conditional G1 artifact, new topology codes, ADR-0006, and additive new-runs-only migration.
11. **Evidence/tooling:** APPROVE eight per-plan artifacts, 3 zooms, measurable legibility/CVD, and a CPU-only Pillow/NumPy automatic path with a WP0 feasibility stop; no OCR/model/network/manual fallback.
12. **Resources/security:** APPROVE existing caps plus 32,768 px, 60 s, 1.5 GiB soft target; acknowledge Windows hard-RSS residual; Local-only controls.
13. **Cost/schedule:** APPROVE Option 2B range (16–26 weeks; 700–1,200 engineering/QA h; 260–520 labeling/corpus/adjudication h; 20–50 delegated QA h) / CHANGE cap or support/yield.
14. **Part 1 boundary:** APPROVE named Local-only work only; no implementation under this packet, no H200/GPU/cloud/remote/G7/G8/spend/PLAN-003, and every later work package separately tracked and approved.
15. **Final decision:** APPROVE REVISED AUTOMATIC-ONLY SCOPE AND TARGETS / REJECT / RETURN WITH CHANGES: `________________`.

# BLOCKED — awaiting Moshe's explicit approval or rejection of the revised automatic-only scope and adapted targets
