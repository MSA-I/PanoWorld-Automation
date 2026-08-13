# PLAN-002RF — final remediation PLAN and approval packet

- Date: 2026-08-11
- Assembly task: `t_68bd94ab`; approval task: `t_301c6952`
- Decision state: **PLANNING ONLY — NO APPROVAL IS IMPLIED**
- Exact decision artifact: this file; its SHA-256 must be recorded with Moshe's response after finalization.
- Governing sources: [S1] `.hermes/plans/2026-08-11-plan-002rf-final-bounded-recognition-remediation.md`; [S2] `.hermes/plans/2026-08-11-plan-002rf-approval-packet-for-moshe.md`; [S3] `.hermes/plans/2026-08-11-t_f5978aca-scope-and-acceptance-sections.md`; [S4] `.hermes/plans/2026-08-11-plan-002rf-delivery-options-constraints-impacts-metadata.md`; [S5] `.hermes/plans/2026-08-11_215950-plan-002rf-independent-review-findings-register.md`; [S6] `.hermes/reviews/independent-anthropic-plan-002r-review-20260811.md`.
- Source hashes: S1 `de506463fedfe5b233215b15914d009502e3dfbb85ab3dc683b1f61f5ab9ea10`; S2 `8e7de8da2341985f8ab3e4a1005f965efae3f15083058dfd2fc2bfb5028fddf3`; S3 `c6a8bbf52678621ac3b60fa9e027601afa3b962724a94c6afaab646c16bf703a`; S4 `10a147e11d7e7afb14d89eb32714307173c2e7e2b2b71c5b375ce938ca69b6b9`; S5 `2111b724dee98877f2cf66cf0622693969fbb7f1d516dad2d2470f96da8595c6`; S6 `a6e00121da07316e148fb63e44044c9677361e82e59c88f166fb76e9ab126e48`.
- Review-target warning: S6 reviewed predecessor PLAN SHA-256 `1c466214c1231cbc790cf534984eadf8762ec30022f21a6a69b64a69d9992562`, not S1 or this materially revised A+B-AUTO packet. All 24 findings remain open pending named evidence and fresh independent review. [S5 §§1,4–6]
- Hard boundary: **Local-only Part 1**. This packet authorizes no implementation, production-code/contract/state edit, dependency installation, corpus acquisition, network retrieval, compute provisioning, spend, merge/push, activation, H200/GPU/cloud/remote execution, G7/G8, or PLAN-003 work.

## 1. Executive summary

The recommended product scope is **Option 2B: Product A + Product B-AUTO**. Product A automatically and deterministically parses an explicit project-owned PWA CAD convention. Product B-AUTO automatically processes only a narrow approved raster envelope on a named local CPU environment. A product run either emits immutable machine-generated canonical geometry after every invariant passes or fails closed. [S3 §§1–3; S4 §§1–3]

Manual or semi-automatic product operation is rejected. Humans are required only for rights approval, two independent truth labels, independent adjudication, frozen-output QA, release acceptance, and incidents; they cannot mark, draw, correct, tune, complete, rescue, or promote product output. Moshe need not review each plan personally. [S3 §§1.3,8]

The only achievable exactness claim is for conforming Product A inputs under the approved contract. B-AUTO values below are unproven acceptance targets for the exact locked corpus/version, not a current accuracy claim or a population guarantee. CPU-only Pillow/NumPy feasibility is unknown until a separately authorized WP0 spike. [S3 §3; S4 §§5.3,12]

Approval of this exact packet authorizes only the creation and consideration of later, separately tracked work packages inside the approved scope. It does **not** authorize implementation, production-code edits, merges, compute provisioning, spend, activation, or PLAN-003.

## 2. Product scope: selected, rejected, and deferred

### 2.1 Selected if explicitly approved

1. **Product A — `cad_exact`:** automatic deterministic parsing of declared PWA DXF semantics; no arbitrary-CAD inference.
2. **Product B-AUTO — `raster_auto`:** local CPU-only automatic recognition of supported PNG/JPEG or approved rendered-PDF-page inputs into scale, native line/circular-arc walls, sourced/resolvable thickness, room faces, and typed hosted openings; emit or fail closed.
3. **Human evidence path:** rights/provenance review, independent truth labels, adjudication, frozen-output QA, release disposition, and incident/rollback decisions only.
4. **Default-off migration:** additive exact versions for new runs only; historical bytes remain unchanged; B-AUTO remains shadow-only until every gate and a later activation approval pass. [S1 §§3–6; S3 §§1,8–9]

### 2.2 Explicitly rejected

- B-MANUAL or any product marking, tracing, drawing, snapping choice, correction, entity editing, per-plan tuning, or manual rescue.
- Generic CAD layer/symbol inference; guessed scale/thickness/room names/opening swing; silent curve approximation; topology repair that can change semantics.
- Confidence-based promotion or waiver of support, geometry, topology, provenance, scale, security, or evidence gates.
- OCR, learned models, weights, training, GPU, H200, cloud/remote inference, network services, silent dependency additions, or provider fallback.
- A universal, arbitrary-plan, population-level, or “100% automatic accuracy” promise. [S3 §1.2]

### 2.3 Deferred and not authorized

- Product C/arbitrary-raster recognition; arbitrary drafting styles; photographs/perspective/sketches/handwriting/severe damage; unknown symbols; non-circular curves; missing/contradictory scale.
- Broader B-AUTO style coverage, 3D/`scene_geometry`, wall/opening heights, camera/Blender/rendering, G7/G8, and PLAN-003.
- Product A-only is an explicit **planning fallback decision**, not an in-run fallback and not equivalent fulfillment of raster automation. Switching to A-only requires Moshe's explicit scope decision. [S4 §2]

## 3. Supported/unsupported matrix

| Path/capability | Supported | Unsupported / mandatory fail-closed |
|---|---|---|
| A source | DXF; one 2D modelspace floor; zero elevation; explicit mm/cm/m units matching manifest; exact case-sensitive approved `PWA-*` layers | DWG parsing; arbitrary layers/symbols; 3D; paperspace; multiple layouts/storeys; blocks/`INSERT`; xrefs; images/OLE; hatches; external references |
| A walls | arbitrary-angle `LINE`; bounded circular `ARC`; ordered line/bulge-arc `LWPOLYLINE`; declared centreline; optional positive `PWA_METADATA/THICKNESS_M` | SPLINE/ellipse/NURBS/non-circular curves; guessed thickness/bands; silent tessellation, snapping, extension, or merge |
| A junctions/rooms | shared source endpoints after `QUANTUM_M=1e-4 m`; closed centreline `PWA-ROOM` path exactly matching one derived face; `area_basis=centreline` | mid-span crossing without a shared vertex; inferred split; self-intersection; duplicate/ambiguous/nested face mismatch; silent clear-area interpretation |
| A openings | distinct `door`, `window`, `passage`; unique host; line-on-line or concentric-arc-on-arc; width along host; full span fits | chord-on-arc; forced door for leafless passage; ambiguous/off-host/over-wide/wrong-type/topology-breaking opening; inferred swing/hinge |
| B source | one orthographic 2D floor; high-contrast supported linework/fixed symbol guide; PNG/JPEG or approved rendered PDF page; skew ±5°; at least two machine-readable scale anchors | photos, perspective/isometric, sketches, handwriting, multiple floors, severe damage/occlusion, unknown symbols, unsupported style/format, missing/contradictory scale |
| B walls/rooms | automatic native straight/circular-arc centrelines; paired-edge thickness or declared single-line convention; simple positive bounded faces and intended room/exterior graph | unresolved centreline/thickness; non-circular curve; leak/crossing/overlap/dangling boundary; topology-changing repair; geometry needing human correction |
| B openings | automatic `door`/`window`/`passage`; unique geometric host; valid centre/width/span and intended adjacency | ambiguous motif/type/host; clutter/text/furniture/damage promoted as opening; duplicate, off-host, or topology-changing false opening |
| Scale | A explicit units; B at least two authoritative anchors | conventional-size assumptions; one unreliable anchor; fabricated plausible scale; absent/contradictory anchors |
| Provenance | product authorship `cad_exact` or `raster_auto`, source class/binding, source/operation reference | missing/inconsistent authorship; human-authored product entity; candidates in canonical output |
| Execution | named local Windows CPU environment; loopback-only UI | upload, telemetry, cloud backup, model call, network retrieval, GPU/H200, cloud/remote execution, spend, G7/G8/PLAN-003 |

Source: [S3 §2]. Exact arc ranges, transform bounds, and symbol guide remain decisions U-3–U-5 rather than implied defaults.

## 4. Achievable accuracy and residual-risk statement

- Product A may claim deterministic exact parsing only for inputs conforming exactly to the approved PWA CAD convention and exact canonicalization/contract. This is not an arbitrary-CAD claim.
- Product B-AUTO may claim only that the exact automatic local pipeline/version met the approved wall, opening, scale, topology, yield, determinism, refusal, security, and evidence gates on the predeclared supported envelope and exact locked corpus. No such claim exists today.
- “Zero critical false positives” means zero **observed** per plan and across the immutable locked evaluation population. It does not prove zero population risk. When zero is observed, report the exact one-sided 95% rule-of-three upper bound `3/n` by frozen stratum; zero across 60 raster families yields 5.0% per family. Outside labeled data, wording is limited to “automatic checks detected no critical false positive.”
- Outputs remain conceptual—not engineering/architectural approval, construction documents, permit material, or quantity-survey evidence. Unsupported or contradictory evidence fails closed. [S3 §3]

## 5. Locked population, metric definitions, and anti-gaming rules

Locked acceptance contains 100 source families: R0 30 supported clean raster; R1 10 supported light-degradation raster; R2 15 supported heavy-but-human-readable raster; R3 5 unsupported/unreadable raster expected to fail closed; 25 conforming Product A CAD; 15 non-conforming CAD expected to reject. B supported denominator is 55 (R0+R1+R2); supported-scan denominator is 25 (R1+R2); all raster families total 60 for the stated bound. [S3 §4.1]

Before lock, U-13 must replace obsolete CAD arc/bulge refusal cases with explicit out-of-envelope cases and set minimum `passage` coverage for A and B. Required geometry slices and corpus minima must be validated before scoring; missing coverage fails rather than shrinking a denominator.

Truth and predictions undergo the same frozen canonicalization into maximal tangent-continuous chains split only at semantic junctions. Matching is deterministic and one-to-one; opening-host equivalence is geometric. Macro averages plans equally; micro and primitive counts are diagnostic. Rejected supported inputs earn no true-positive credit and yield is scored separately. Source-family derivatives stay in one split. Support labels, membership, thresholds, evaluator, algorithm/config, and outputs freeze before truth is opened. [S3 §§4.2,5]

Proposed wall match requires orientation ≤1° for walls ≥0.50 m; an approved bounded relaxed rule only in `[0.20,0.50) m`; endpoint/spatial scoring below 0.20 m; overlap ≥95%; raster Hausdorff ≤`max(4 px,0.025 m)`; raster endpoint P95 ≤`max(3 px,0.020 m)`; and no overrun above an approved junction tolerance. Arc matching also requires native primitive agreement, radius error ≤2%, sweep overlap ≥95%, and approved sampled tolerance. Pixel terms never apply to CAD.

Proposed opening match requires exact class, geometric host, raster centre error along host ≤`max(4 px,0.050 m)`, approved perpendicular tolerance, width error ≤`max(0.020 m,2%)`, full host span, and no semantic-junction crossing. U-1 (partial-credit formula), U-2 (scale fit), U-3 (arc bounds), and U-4 (transform bounds) remain unresolved.

## 6. Acceptance-target table — all rows are conjunctive

| ID | Metric / threshold | Population and pass/fail | Required evidence / accountable approval |
|---|---|---|---|
| AT-01 | A completion: canonical output on all conforming cases | 25/25 conforming CAD emit; any failure blocks | per-plan source/output hashes/findings; independent Contract/Geometry Reviewer TBD |
| AT-02 | A wall chain P/R 1.000/1.000 per plan and required slice | any missing/extra/mismatched chain blocks | full match/slice tables; Geometry Reviewer TBD |
| AT-03 | A opening P/R 1.000/1.000, exact class/host | all typed-opening and no-opening A cases; any FP/FN/class/host/duplicate blocks | opening/topology diff; Geometry Reviewer TBD |
| AT-04 | A scale relative error ≤0.01% each plan | any excess/unit mismatch blocks | unit proof and full-precision errors; Contract/Geometry Reviewer TBD |
| AT-05 | A exact room/face and 100% intended adjacency | any mismatch/leak/crossing/dangling/wrong adjacency blocks | canonical face/graph diff; Geometry Reviewer TBD |
| AT-06 | Unsupported CAD: correct refusal, zero canonical acceptance/external resolution | 15/15 reject; any acceptance/external read is CRITICAL | terminal/artifact/access matrix; Contract + Security Reviewers TBD |
| AT-07 | B clean emit yield ≥95% | R0=30; at least 29 emit; every emitted plan still meets all gates | support/emit ledger; Evaluation Owner + QA Lead TBD |
| AT-08 | B supported-scan emit yield ≥85% | R1+R2=25; at least 22 emit; R3 excluded | stratum ledger; Evaluation Owner + QA Lead TBD |
| AT-09 | B wall macro and every required slice P/R ≥0.995/0.995 | any component/slice below blocks | per-plan/slice tables and recomputation; Evaluation Reviewer TBD |
| AT-10 | B wall per-plan P/R ≥0.980/0.980 | every emitted supported raster; one failure blocks corpus | geometry diffs; Evaluation Reviewer TBD |
| AT-11 | B opening macro P/R ≥0.995/0.990 | emitted supported set incl. explicit empty no-opening lists; either below blocks | per-plan/type tables; Evaluation Reviewer TBD |
| AT-12 | B opening per-plan P/R ≥0.980/0.980 and exact no-opening behavior | one plan below or any opening on no-opening plan blocks | opening diff/ledger; Evaluation Reviewer + QA Lead TBD |
| AT-13 | zero observed critical FP per plan and locked set; report exact 95% bound | all 100 families/refusals/adversaries; any critical FP is CRITICAL | signed ledger/topology/bound; QA Lead + Release Approver TBD |
| AT-14 | every wall/opening/arc match obeys approved §5 tolerances | every matched entity plus below/at/above boundary fixtures; any false TP blocks | full-precision tables/tests; Geometry/Evaluation Reviewer TBD |
| AT-15 | B scale median anchor residual ≤1%, disagreement ≤2% | every emitted B plan and scale adversaries; invented/incorrect non-refusal blocks | anchor/fit evidence; Geometry Reviewer TBD; exact U-2 formula required |
| AT-16 | B topology: 100% valid faces and exact intended adjacency per plan | any invalid face/count/leak/crossing/dangling/adjacency mismatch blocks | validators/graph diff; Geometry Reviewer + QA Lead TBD |
| AT-17 | unsupported raster deterministic refusal | all R3 and style/scale regressions; canonical acceptance/silent approximation is CRITICAL | support/outcome/artifact matrix; Evaluation Reviewer TBD |
| AT-18 | automatic-only execution | all 100 runs: no interaction/edit/tuning/truth access; emit or fail closed | event/config/process/output audit; Automation Reviewer TBD |
| AT-19 | deterministic replay | two clean runs each: A canonical bytes; B outcome/output/diagnostics bytes in pinned environment | `environment.json`, hashes/diff; Reproducibility Reviewer TBD |
| AT-20 | corpus validity/leakage/rights complete | all manifests/splits; any missing right/slice, collision, mutation, or post-lock threshold change blocks | manifests/collision/rights ledgers; Rights Owner + Evaluation Reviewer TBD |
| AT-21 | independent truth | two blind labels, independent adjudicator, output frozen first; prohibited overlap/leak makes B non-evaluable | role/visibility ledger, labels/adjudication/freeze hashes; Governance Approver TBD |
| AT-22 | frozen-output QA on all 100; no sampling/editing | missing plan/disposition or unresolved CRITICAL/MAJOR blocks | immutable per-plan QA/lineage; pre-named QA Delegate TBD |
| AT-23 | eight complete/legible hash-bound records, SVG + 100/200/400% PNG, contrast/CVD/collision pass | all 100; missing/hash mismatch/unreadable evidence or unresolved MAJOR blocks | evidence index and reports; QA Lead + Security Reviewer TBD |
| AT-24 | security/resource controls hold | adversarial matrix + all runs; path/network/disclosure/termination/finalization/cap failure blocks and triggers rollback | security/resource/kill evidence; Security Reviewer TBD |
| AT-25 | Local-only Part 1: zero upload/telemetry/model/cloud/network/GPU/H200/remote/G7/G8/PLAN-003/spend | complete work-package audit; any breach blocks/incident | environment/network/process/dependency/change audit; Moshe + Security Reviewer |
| AT-26 | conjunctive release aggregation; current lineage; no CRITICAL/unresolved MAJOR | exact candidate/corpus/evaluator/environment; no partial/average waiver | signed index of every artifact/hash; Release Approver TBD |

Source and detailed definitions: [S3 §§4–6]. A developer or evidence generator cannot self-approve their own gate.

## 7. Evidence and accountability requirements

Each family requires eight separately hash-bound records: sanitized source; adjudicated truth; automatic accepted geometry; source+geometry; matched FP/FN/tolerance diff; topology/leak/junction view; machine metrics/findings; immutable QA disposition/current lineage head. Deterministic SVG and PNG at 100%/200%/400%, environment fingerprint, exact source/truth/output/algorithm/config/threshold/evaluator/renderer/corpus/QA hashes, font hash, metadata stripping, normalized-pixel hash, collision checks, and CVD results are required. [S3 §§7–8; S4 §11]

Legibility requires text ≥12 CSS px, legend ≥14 CSS px, text contrast ≥4.5:1, geometry contrast ≥3:1, no always-visible IDs/confidence over geometry, zero glyph-box collisions with glyphs or critical geometry, no clipping/active/external SVG content, and ≥3:1 accepted-stroke contrast under declared protanopia/deuteranopia/tritanopia severity-1.0 simulation.

Roles: Moshe decides scope/targets/caps but need not review each plan; a named Rights Owner approves provenance/privacy; two blind labelers and an independent adjudicator create truth; a pre-named QA delegate reviews all frozen comparisons without editing output; independent Contract/Geometry/Evaluation/Security/Reproducibility reviewers approve their domains; a named Release Approver accepts only AT-26. U-6 must prohibit QA from also serving as labeler/adjudicator and prohibit implementer/evidence-producer self-approval; until names and overlap rules are fixed, evaluation/release remains blocked. This resolves the ambiguity identified in F-7 by selecting strict separation, subject to Moshe's explicit approval.

## 8. Phased cost and schedule options

| Option | Scope | Planning estimate | Consequence |
|---|---|---|---|
| 1 | preserve current line-only baseline | 1–2 weeks; 5–8 engineer-days | lowest change risk; arcs/thickness/raster need remains unmet |
| 2A | Product A only | 4–7 weeks; 180–300 engineering/QA h; 40–80 corpus/review h | safest automatic claim; raster need unmet |
| **2B recommended** | A + B-AUTO | **16–26 weeks; 700–1,200 engineering/QA h; 260–520 corpus/labeling/adjudication h; 20–50 delegated QA h** | bounded CAD+raster direction; highest feasibility/evaluation risk |
| 3 later | broader B-AUTO styles | unestimated | new corpus, targets, rights, security/resources, and approval; no manual fallback |
| C | arbitrary-raster research | unestimated/unauthorized | new provider/model/data/license/compute/security packet |

| Phase | Range | Required output / stop-go gate |
|---|---:|---|
| WP0 decisions/ADR/feasibility design | 60–100 h; 2–3 weeks | exact approved hash/decisions, ADR-0006, dependency/license inventory, target workstation, hardest-clean-raster protocol; stop if route to targets within 60 s/soft 1.5 GiB is implausible |
| WP1 corpus/evaluator lock | 80–140 engineering h + 260–520 corpus h; 3–5 weeks | rights, split/leakage, two labels/adjudication, hidden truth, matcher/statistics approved; otherwise B non-evaluable |
| WP2 additive contracts/lifecycle | 80–140 h; 2–3 weeks | exact versions, provenance, source class, native geometry, passage, lineage/G1/codes; historical compatibility passes |
| WP3 Product A | 120–200 h; 3–4 weeks | all A, migration, determinism, adversarial, and resource gates pass; otherwise route disabled |
| WP4 B clean raster | 180–300 h; 4–6 weeks | ≥29/30 clean emits and every accuracy/topology/scale/determinism/FP gate; otherwise stop/re-scope |
| WP5 supported scans/shadow/rollback | 140–240 h; 3–5 weeks | ≥22/25 scan emits, security/resource/rollback and 20–50 h QA pass; no unresolved critical/major finding |
| WP6 activation decision | 40–80 h; ~1 week | exact local scope/evidence/incident owners/fresh review; separate Moshe activation approval or remain off |

Estimates exclude approval/private-data waiting, staffing contention, procurement, re-review after invalidation, and future scope expansion. Incremental infrastructure USD 0 is conditional—not a commitment—on the current workstation, locked dependencies, and rights-cleared zero-cost corpus proving sufficient. A lower cap must narrow support/yield/phase coverage; it cannot add manual operation or weaken gates. [S4 §§1–4,12]

## 9. Risks, security, and resource constraints

| Risk | Control / decision consequence |
|---|---|
| finite corpus cannot prove population zero | exact per-stratum 95% bound, narrow claim, incident/rollback path |
| CPU-only B-AUTO infeasible | WP0 stop and return with explicit dependency/model/license/compute/hour options; no silent install/manual rescue |
| evaluator leakage/self-scoring | family splits, blind labels, output freeze, strict role separation, independent review |
| geometry/scale ambiguity | narrow support envelope and mandatory refusal |
| false opening changes connectivity | typed unique host, zero-observed-critical-FP and exact topology gates |
| rights/privacy failure | human out-of-band acquisition only, named Rights Owner, private Layer B local/untracked |
| local UI/path attack | loopback, exact Host/Origin, launch secret, strict cookie/CSRF/no-store, containment/reparse tests |
| Windows lacks portable hard RSS sandbox | bounded input/output/time, killable no-child worker, soft 1.5 GiB target, verified tree termination; residual requires acceptance |
| deterministic-render variance | exact environment/lock/font, stripped metadata, normalized-pixel comparisons |
| stale approval | immutable supersession/invalidation and current-head resolution |
| labor overrun | approved cap; narrower scope instead of weaker gates; fresh cap for re-review |

Existing caps: source 50 MiB; 200,000 DXF entities; annotation 5 MiB; walls/rooms/openings 20,000/5,000/20,000; 10,000 vertices; coordinate magnitude 100,000 m; decoded raster 100 MP; overlay 70 MiB; worker output 1 MiB; DXF worker 30 s. Proposed approval items: 32,768 px maximum side, 60 s whole local run, and 1.5 GiB soft observed working-set target. No child spawn, network, auto-relaxation, or in-run retry. [S4 §§5,8]

Required security evidence includes non-loopback/Host/Origin rejection, CSRF replay, cookie/cache headers, traversal/symlink/junction/reparse escape, unauthenticated/listing/path rejection, decompression bombs, process-tree kill, and kill-during-atomic-finalization. Private evidence remains local/untracked; canonical evidence excludes timestamps, duration, host, PID, username, and absolute path.

## 10. Migration, rollback, and incident impacts

Migration is additive and applies to new runs only: exact carriers for `cad_exact`/`raster_auto` authorship, `source_class`, native line/arc paths, sourced thickness, room area basis, `passage`, recognition diagnostics, immutable `floorplan_review` lineage, raster-conditional G1 evidence, and new blocking topology codes. ADR-0006 explicitly supersedes only ADR-0004's geometry envelope and no-third-party-dataset context; published history stays unchanged. Exact schema/catalog/bundle/code versions remain U-9 pending live WP0 review. Historical bytes remain identical; old consumers reject unknown versions predictably; new consumers prove historical round trips. `scene_geometry`/PLAN-003 are untouched. [S4 §9]

Default remains the baseline; new routes are default-off and named. Rollback disables the route, stops new runs, kills/verifies workers, preserves finalized immutable history, quarantines bounded staging/logs, reproduces on sanitized data, reverts unpublished activation/code or deprecates additive versions without deletion, reruns baseline/adversarial/migration/determinism checks, and requires fresh independent review plus Moshe's applicable gate before re-enable. No rollback relabels evidence, weakens a gate, retries in-run, or routes to human correction. [S4 §10]

SEV-1: path/external access, disclosure, finalized mutation, unkillable process. SEV-2: nondeterminism, contract/G1 misrouting, resource-control bypass, critical false opening. SEV-3: bounded malformed-input/performance defect without integrity impact.

## 11. Every independent-review finding and disposition

All original severities are preserved: 15 BLOCKING, 8 MAJOR, 1 MINOR. “Drafted/adapted” is not “closed.” **F-1 through F-24 all remain OPEN.** [S5 §§1–3]

| ID | Severity | Proposed disposition and rationale | Closure evidence still required |
|---|---|---|---|
| F-1 | BLOCKING | ACCEPT: ADR-0006 must explicitly supersede ADR-0004 clauses; no silent ADR amendment | approved ADR/numbered D-0xx decisions, migration matrix, fresh review |
| F-2 | BLOCKING | ACCEPT/ADAPT: product authorship only `cad_exact`/`raster_auto`; human truth isolated | exact schemas/enums and negative/finalization tests |
| F-3 | BLOCKING | ACCEPT: immutable approval supersession/invalidation lineage and current-head resolution | state schema/transitions, stale/concurrency/history tests |
| F-4 | BLOCKING | ACCEPT: source-bound `source_class` and conditional raster review artifact; G1 remains machine | state-machine version/fixtures and historical compatibility |
| F-5 | BLOCKING | ACCEPT: segmentation-neutral chain canonicalization; geometric host equivalence | matcher/label guide, segmentation/host fixtures, evaluator review |
| F-6 | BLOCKING | ACCEPT: macro plus slice and per-plan floors; one bad plan blocks | aggregator tests/reports and missing/rejected accounting |
| F-7 | BLOCKING | MANUAL-OPERATOR PART SUPERSEDED; independence retained and strict QA/label/adjudicator separation selected | approved role matrix, identities, custody/freeze/leakage audit, fresh evaluation review |
| F-8 | BLOCKING | CONDITIONALLY ACCEPT CPU-only Pillow/NumPy option; capability remains speculative | approved hardest-stratum spike, measured accuracy/yield/runtime/memory/determinism, stop decision |
| F-9 | BLOCKING | ACCEPT: acquisition is human/out-of-band with exact rights/privacy/spend approval | source/license manifest, owner/attestations, ADR, no-network audit |
| F-10 | BLOCKING | ACCEPT exact A arcs/junctions/rooms/thickness/area semantics | exact DXF/schema contract and positive/negative geometry fixtures |
| F-11 | BLOCKING | ACCEPT `passage` as third opening type | schema/label guide/host/topology/migration fixtures and U-13 minima |
| F-12 | BLOCKING | ACCEPT one-sided 95% `3/n`, exact bound, no population-zero wording | frozen units/strata, executable calculation/results, claim review |
| F-13 | BLOCKING | ACCEPT revised 16–26 week/700–1,200 h estimate, but unvalidated | auditable WBS, throughput/contingency/spike basis, approved cap |
| F-14 | BLOCKING | ACCEPT restored early Anthropic session/A-only dissent and later supersession | source-backed metadata/fallback unknowns and fresh provenance review |
| F-15 | BLOCKING | ACCEPT append-only new blocking codes; no severity mutation | exact codes/outcomes, ADR and compatibility/topology tests |
| F-16 | MAJOR | ACCEPT prerequisite; files remain untracked and this task may not commit | tracked exact bytes, commit SHA, packet hash link, independent verification |
| F-17 | MAJOR | B0 edit defect SUPERSEDED; define append-only automatic recognition provenance/new immutable runs | schema/version binding/replay/cancellation tests and proof no edit API |
| F-18 | MAJOR | ACCEPT exact environment, font, metadata, same-env bytes/cross-env normalized pixels | environment schema, font/chunk/pixel tests, repeated clean runs |
| F-19 | MAJOR | ACCEPT measurable CVD/contrast/collision criteria | reference transforms/fixtures, glyph bounds, all-zoom review |
| F-20 | MAJOR | ACCEPT full UI/containment/cancellation adversarial matrix | Windows adversarial suite, tree/staging assertions, threat review |
| F-21 | MAJOR | ACCEPT restored tight tolerances, raster-only pixels, bounded short-wall rule | frozen evaluator/boundary fixtures and approved future-delta table |
| F-22 | MAJOR | ADAPT: confidence diagnostic only and never overrides; calibration/G1 behavior unresolved | U-14 calibration semantics, thresholds/findings, G1/reliability tests or ADR |
| F-23 | MAJOR | ACCEPT `legacy_manual` only in external hash-bound index; no history rewrite | index contract, before/after hashes, migration/claim-filter tests |
| F-24 | MINOR | ACCEPT corrected physical-dimension and sRGB wording | exact-hash wording review, crop/anchor/ICC/privacy fixtures |

A fresh opposite-provider independent review must inspect this exact packet hash, the revised A+B-AUTO semantics, and S5 before any finding may close. Scope approval is necessary but is not technical closure.

## 12. Provider, model, hosting, data, and fallback metadata

### 12.1 Proposed product execution paths

| Path | Provider/model/version | Hosting/data handling | Fallback and limits |
|---|---|---|---|
| current baseline | no AI; project deterministic Python; exact runtime to be pinned | local Windows; verified local snapshots; no upload/model call | no in-run fallback; rollback target; lacks arcs/thickness/raster |
| Product A | no AI; `ezdxf`; lock currently `ezdxf==1.4.4`; final exact environment at WP0 | local CPU/Windows; CAD remains local; no external refs | ambiguity/unsupported fails closed; route disable returns to baseline; exact new versions unknown |
| Product B-AUTO | no AI; project deterministic NumPy/Pillow; lock currently `numpy==2.4.6`, `Pillow==12.3.0`; algorithms/config to be versioned | local CPU/Windows, loopback UI/child; private raster/evidence local/untracked; no network/model | stage/security/resource failure fails closed; route disable returns baseline; WP0 infeasibility returns for explicit 2A/narrower/new-plan decision; CPU feasibility and hard RSS unknown |
| broader B | no provider/model selected; version unknown | locality/data terms require a new packet | no fallback defined; unsupported fails closed; scope/corpus/dependencies/cost unknown |
| Product C | no provider/model/version/host/vendor selected | no upload/retention/training terms approved; none authorized | no chain authorized; data/licenses/cost/latency/OOD/security/compute all unknown |

Fallback never means a weaker silent algorithm, human correction, or remote provider. Product runs emit conforming output or fail closed. [S4 §6]

### 12.2 Planning/review provenance (not product dependencies)

| Work | Provider / requested / actual | Hosting and data | Effort/runtime/cost; fallback; skills/session; unknowns |
|---|---|---|---|
| early geometry synthesis | Anthropic first-party Claude Code; `opus` / `claude-opus-5` | remote provider; repository/planning excerpts | high requested; none observed; session `e89cd83c-215a-430e-a058-664d64724fae`; skill/build/runtime/region/policy unknown |
| critical geometry memo | Anthropic first-party Claude Code; `opus` / `claude-opus-5` | remote provider; planning/repo text | high; none observed; `computer-vision-expert`; session `81405d64-8518-4e5d-b1ec-ac134c9e59d4`; detailed runtime/build/region/policy unknown |
| evaluation memo | OpenAI Codex `gpt-5.6-sol` active/default | remote via Hermes; local planning files | runtime/cost/build/policy/region/configured chain unavailable; none observed |
| operations memo | OpenAI Codex `gpt-5.6-sol` active/default | same | task `t_1d699970`; runtime/cost unavailable; none observed |
| PLAN-002R synthesis | OpenAI Codex `gpt-5.6-sol` active/default | same | task `t_e50c0bd4`; runtime/cost unavailable; none observed |
| independent review | Anthropic first-party Claude Code; `opus` / `claude-opus-5` | remote; exact predecessor and contract excerpts; read-only | plan mode; 833.342 s wall, 798.428 s API, 26 turns, 58,028 output tokens, USD 3.866225; none observed; skills `computer-vision-expert`,`advanced-evaluation`,`threat-modeling-expert`; session `53971edf-2b1e-48b8-86a9-3f81040a5dbb`; build/retention/region unknown |
| initial/revised packets | OpenAI Codex `gpt-5.6-sol` active/default | remote via Hermes; planning files | Kanban runs 34–35; none observed; Hermes `kanban-worker`,`plan`; runtime/cost/build/policy unavailable |
| delivery memo | OpenAI Codex `gpt-5.6-sol` active/default | remote via Hermes; planning/contracts | task `t_1cac6675`; none observed; `kanban-worker`; runtime/cost/build/region/policy/configured fallback unknown |
| scope/acceptance memo | OpenAI Codex `gpt-5.6-sol` active/default | remote via Hermes; planning files | task `t_f5978aca`; none observed; `kanban-worker`,`plan`; runtime/cost/build/region/policy/configured fallback unknown |
| findings register | OpenAI Codex `gpt-5.6-sol` active/default | remote via Hermes; review/planning files | task `t_9471e9b3`; none observed; `kanban-worker`; runtime/cost/build/region/policy/configured fallback unknown |
| this assembly | OpenAI Codex `gpt-5.6-sol` active/default | remote via Hermes; S1–S6 planning/review text; no production corpus/credentials intentionally supplied | task `t_68bd94ab`, run 39; none observed; Hermes `kanban-worker`,`plan`; runtime/cost/build/region/retention/training/configured fallback unknown |

The early A-only Opus dissent is retained. The later Anthropic A+B0 recommendation is historical and superseded by Moshe's RETURN WITH CHANGES requiring A+B-AUTO and no manual product operation. Unknown metadata is not inferred. A required provider mismatch, unavailable opposite-provider reviewer, or silent substitution blocks the applicable gate. [S4 §§6–7]

## 13. Unresolved conflicts and required decisions

Evidence resolves the raster-count inconsistency as 55 supported raster families plus 5 unsupported refusal families = 60 total raster families. It resolves the MAJOR count discrepancy in favor of the enumerated F-16..F-23 set = 8 MAJOR. It resolves F-7's role ambiguity by recommending strict QA/labeler/adjudicator separation. The following remain unresolved and are not defaults:

| ID | Decision required | Why unresolved / owner |
|---|---|---|
| U-1 | exact length-weighted chain partial-credit numerator/denominator | AT-09/10 not reproducible; Moshe + Evaluation Reviewer |
| U-2 | exact two-anchor scale fit, weighting, and disagreement formula | AT-15 metric ambiguous; Moshe + Geometry/Evaluation Reviewer |
| U-3 | exact supported circular-arc radius/sweep and sampling bounds | “bounded arc” not executable; Moshe + Geometry Reviewer |
| U-4 | exact deterministic clustering/gap/merge/T-split/tangent/dedup bounds | semantic-repair risk; Moshe + Contract/Geometry Reviewer |
| U-5 | fixed B symbol/style guide and machine-readable support classifier | support/yield could be gamed; Moshe + Evaluation Owner |
| U-6 | names and forbidden overlap matrix; select strict QA≠labeler≠adjudicator | independence/accountability incomplete; Moshe + Governance Approver |
| U-7 | corpus sources/licenses/rights owner/privacy/retention/zero-spend feasibility | no lawful corpus or cost claim; Moshe + Rights Owner |
| U-8 | exact CPU feasibility-spike protocol and stop thresholds | B capability unproven; Moshe + independent reviewer |
| U-9 | exact schema/catalog/bundle/error versions and lineage/G1/code shapes | current contracts cannot carry proposal; separate ADR/contract review |
| U-10 | accept 32,768 px/60 s/soft 1.5 GiB on named workstation | no benchmark evidence; Moshe + Security/Performance Reviewer |
| U-11 | pinned renderer/font/CVD and normalized-pixel contract | determinism/legibility not executable; QA/Security/Reproducibility Reviewers |
| U-12 | final labor/cost cap and consequence below Option 2B | scope/yield must shrink; Moshe |
| U-13 | replacement fail-closed CAD cases and minimum passage coverage | inherited corpus conflicts with supported arcs/bulges and lacks passage denominator; Moshe + Corpus/Evaluation/Geometry Reviewers |
| U-14 | confidence calibration, `LOW_CONFIDENCE_THRESHOLD=0.5` mapping, and exact G1 behavior | F-22 remains materially underspecified; Moshe + Contract/Evaluation Reviewers or ADR |
| U-15 | durable Git anchor timing for this packet/review/register | `.hermes/` remains untracked; governance owner + Moshe; no commit authorized here |

Any unresolved item may remain explicitly blocked, but no affected metric, implementation package, finding closure, or release may proceed by implication.

## 14. Moshe decision form — answer every line explicitly

Record this file's exact path and post-finalization SHA-256 with the response. For each line mark exactly one of **APPROVE** or **REJECT/CHANGE**; blanks and silence are not approval.

1. **Exact scope and artifact** — [ ] APPROVE [ ] REJECT/CHANGE: this exact packet/hash as the controlling scope/acceptance baseline.
2. **Product path** — [ ] APPROVE [ ] REJECT/CHANGE: Option 2B A+B-AUTO recommended; A-only requires an explicit fallback decision and leaves raster unmet; B-MANUAL rejected; C deferred.
3. **Automatic-only obligation** — [ ] APPROVE [ ] REJECT/CHANGE: zero marking/drawing/correction/per-plan tuning/manual rescue in product runs; emit or fail closed.
4. **Geometry coverage** — [ ] APPROVE [ ] REJECT/CHANGE: native arbitrary-angle lines, bounded circular arcs, line/bulge paths; non-circular curves and unsupported cases fail closed.
5. **CAD semantics** — [ ] APPROVE [ ] REJECT/CHANGE: centreline rooms, shared quantized source-endpoint junctions, exact room/face match, explicit `PWA_METADATA/THICKNESS_M`, distinct door/window/passage.
6. **Human-in-the-loop obligations** — [ ] APPROVE [ ] REJECT/CHANGE: two blind truth labels, independent adjudicator, strict QA role separation, frozen-output QA on all 100, no output edits, no personal Moshe per-plan review.
7. **Wall/opening thresholds and yield** — [ ] APPROVE [ ] REJECT/CHANGE: A 1.000/1.000; B wall macro/slice ≥0.995/0.995, opening macro ≥0.995/0.990, every emitted plan ≥0.980/0.980, ≤1° angle, ≥95% overlap, width error ≤`max(0.020 m,2%)`, clean/scanned yields ≥95%/≥85%.
8. **Zero-critical-false-positive rule** — [ ] APPROVE [ ] REJECT/CHANGE: zero observed per plan/locked set, exact one-sided 95% `3/n` bounds, named residual risk, no population-zero claim.
9. **Spatial/scale tolerances** — [ ] APPROVE [ ] REJECT/CHANGE: §5 spatial rules; A scale ≤0.01%; B two-anchor median residual ≤1% and disagreement ≤2%; unknown/contradictory scale fails closed, subject to U-2.
10. **Topology requirements** — [ ] APPROVE [ ] REJECT/CHANGE: 100% valid faces and exact intended adjacency each emitted plan; leak, crossing, dangling boundary, room mismatch, or false-opening topology change blocks.
11. **Population/evidence** — [ ] APPROVE [ ] REJECT/CHANGE: 100-family composition, anti-leakage/refusal accounting, AT-01..AT-26, eight per-family records, three PNG zooms, SVG, determinism, legibility/CVD, and current immutable lineage.
12. **Contracts/migration/rollback** — [ ] APPROVE [ ] REJECT/CHANGE: additive new versions/new-runs only, ADR-0006, authorship/source class/passage/conditional G1/lineage/new codes; historical bytes preserved; default-off and rollback rules.
13. **Security/resources/feasibility** — [ ] APPROVE [ ] REJECT/CHANGE: existing caps plus 32,768 px, 60 s, soft 1.5 GiB; acknowledge Windows hard-RSS residual; CPU-only WP0 stop; no silent dependency/model/manual fallback.
14. **Cost/schedule** — [ ] APPROVE [ ] REJECT/CHANGE: Option 2B 16–26 weeks, 700–1,200 engineering/QA h, 260–520 corpus/label/adjudication h, 20–50 delegated QA h; lower cap narrows scope/yield rather than gates.
15. **Reviewer register** — [ ] APPROVE [ ] REJECT/CHANGE: all F-1..F-24 dispositions are proposals; all remain open until evidence and fresh exact-hash opposite-provider review.
16. **Local-only Part 1 boundary** — [ ] APPROVE [ ] REJECT/CHANGE: no current implementation, production-code edits, dependency/data acquisition, merge/push, provisioning/spend, H200/GPU/cloud/remote, G7/G8, activation, or PLAN-003.
17. **U-1 through U-15** — [ ] APPROVE recommended resolution where stated [ ] KEEP BLOCKED [ ] REJECT/CHANGE; attach an explicit resolution per ID before any dependent work.
18. **Authorization semantics** — [ ] ACKNOWLEDGE [ ] REJECT/CHANGE: approval only authorizes later, separately tracked planning/implementation proposals; each still needs its own approval and evidence gates.
19. **Final decision** — [ ] APPROVE EXACT SCOPE AND ACCEPTANCE TARGETS [ ] REJECT [ ] RETURN WITH CHANGES: `____________________________`.

# BLOCKED — pending Moshe’s explicit approval of scope and acceptance targets.
