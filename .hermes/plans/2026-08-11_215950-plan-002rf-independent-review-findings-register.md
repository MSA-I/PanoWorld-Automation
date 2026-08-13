# PLAN-002RF independent-review findings register

- Date: 2026-08-11
- Kanban task: `t_9471e9b3`
- Purpose: planning-only register for direct inclusion in the final remediation plan and approval packet
- Independent review: `.hermes/reviews/independent-anthropic-plan-002r-review-20260811.md`
- Review SHA-256: `a6e00121da07316e148fb63e44044c9677361e82e59c88f166fb76e9ab126e48`
- Artifact reviewed by that review: `.hermes/plans/2026-08-11_171713-plan-002r-bounded-recognition-remediation.md`
- Reviewed artifact SHA-256: `1c466214c1231cbc790cf534984eadf8762ec30022f21a6a69b64a69d9992562`
- Current revised plan: `.hermes/plans/2026-08-11-plan-002rf-final-bounded-recognition-remediation.md`
- Current revised plan SHA-256: `de506463fedfe5b233215b15914d009502e3dfbb85ab3dc683b1f61f5ab9ea10`
- Current approval packet: `.hermes/plans/2026-08-11-plan-002rf-approval-packet-for-moshe.md`
- Current approval-packet SHA-256: `8e7de8da2341985f8ab3e4a1005f965efae3f15083058dfd2fc2bfb5028fddf3`
- Boundary: Local-only Part 1 planning. No implementation, production-code or contract edit, dependency installation, corpus acquisition, compute/spend, H200, GPU, cloud/remote execution, G7, G8, merge/push, activation, or PLAN-003 work is authorized.

## 1. Source and status rules

The independent review enumerates 24 findings: F-1 through F-15 are `BLOCKING`, F-16 through F-23 are material `MAJOR` non-blocking findings, and F-24 is `MINOR`. The invocation record says a reviewer signature count was normalized from nine to eight MAJOR findings; the enumerated F-16..F-23 set contains eight and is the authoritative count. No enumerated finding is omitted or downgraded here.

The review applies to the predecessor PLAN hash `1c466214…`, not to the current A+B-AUTO revision hash `de506463…`. Moshe's later `RETURN WITH CHANGES` materially replaced B0/manual product operation with end-to-end automatic raster processing and human QA only. Therefore:

- `DISPOSITION DRAFTED` means the current plan proposes a response; it does not mean the reviewer accepted it.
- `SUPERSEDED BY APPROVED SCOPE CHANGE` means the exact predecessor mechanism is no longer in the product path, but the underlying invariant still needs evidence.
- `OPEN` means closure evidence is absent. Every finding in this register remains open until the stated evidence exists.
- No finding may be closed solely because the current plan's §13 or packet §12 says it is incorporated.
- A fresh independent opposite-provider review must inspect the exact revised hash and this register. Approval of scope is necessary where stated but is not technical closure.

## 2. Summary register

| ID | Severity | Disposition state | Remains open | Primary closure dependency |
|---|---|---|---|---|
| F-1 | BLOCKING | disposition drafted | YES | exact ADR-0006/WP0 governance wording and approval |
| F-2 | BLOCKING | disposition adapted to B-AUTO | YES | exact schema carrier and validation tests |
| F-3 | BLOCKING | disposition drafted | YES | immutable lineage contract and G1 resolution evidence |
| F-4 | BLOCKING | disposition drafted | YES | conditional state-machine contract and discriminator tests |
| F-5 | BLOCKING | disposition drafted | YES | frozen canonical matcher specification and evaluator evidence |
| F-6 | BLOCKING | disposition drafted | YES | per-plan/macro gate implementation and aggregation tests |
| F-7 | BLOCKING | predecessor operator issue superseded; evaluation risk remains | YES | role-separation matrix and leakage audit for B-AUTO QA |
| F-8 | BLOCKING | speculative CPU-only option selected | YES | feasibility/design spike and explicit stop/go decision |
| F-9 | BLOCKING | disposition drafted | YES | rights/source approval and ADR-0006 amendment |
| F-10 | BLOCKING | disposition drafted | YES | exact CAD geometry contract and conformance tests |
| F-11 | BLOCKING | `passage` selected | YES | approved enum/schema and topology fixtures |
| F-12 | BLOCKING | disposition drafted | YES | frozen statistical method and generated bound evidence |
| F-13 | BLOCKING | estimate revised for B-AUTO | YES | auditable work breakdown and approved cap |
| F-14 | BLOCKING | routing record restored/adapted | YES | source-backed metadata verification in exact packet |
| F-15 | BLOCKING | new-code approach selected | YES | error-code/ADR mapping and compatibility tests |
| F-16 | MAJOR | explicitly deferred prerequisite | YES | tracked immutable Git anchor and recorded commit SHA |
| F-17 | MAJOR | product edit log superseded by B-AUTO | YES | recognition replay/immutability specification and tests |
| F-18 | MAJOR | disposition drafted | YES | environment schema and determinism evidence |
| F-19 | MAJOR | disposition drafted | YES | measurable CVD/collision implementation and fixtures |
| F-20 | MAJOR | disposition drafted | YES | adversarial UI/containment/cancellation test evidence |
| F-21 | MAJOR | tighter tolerances restored | YES | approved evaluator rules and boundary fixtures |
| F-22 | MAJOR | adapted to B-AUTO diagnostic confidence | YES | calibration semantics and G1 interaction tests |
| F-23 | MAJOR | external-index approach selected | YES | immutable historical-byte proof and index contract |
| F-24 | MINOR | wording corrected | YES | exact-hash review confirms both corrections |

## 3. Detailed findings and dispositions

### F-1 — ADR-0004 contradiction and missing superseding ADR

- **Source:** independent review lines 69–75; predecessor PLAN lines 7, 51–56, 69, 71, 379–392; `docs/decisions/ADR-0004-floorplan-parser-baseline.md:7`; `docs/OPEN-DECISIONS.md:4`.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** Product A geometry envelope, third-party corpus framing, decision governance, WP0 approval validity.
- **Required remediation:** Stop claiming ADR-0004 is preserved unchanged; require ADR-0006 to supersede ADR-0004 decision 2 and its no-third-party-dataset context while retaining ADR-0004 as published history; register approved decisions as `D-0xx` before implementation.
- **Proposed disposition:** ACCEPT. Current PLAN lines 8–9 and 216 require ADR-0006 and preserve published history; packet lines 125 and 182 repeat the governance requirement.
- **Rationale:** A plan cannot silently amend an accepted ADR by prose. Native arcs/bulges and a third-party corpus materially change the accepted baseline.
- **Evidence needed to close:** approved exact ADR-0006 text; numbered decision entries; exact-version migration matrix; independent review confirming no accepted history is deleted/relabelled; Moshe's approval of the supersession.
- **Remains open:** YES — ADR-0006 and numbered decisions do not yet exist, and the revised plan has not received fresh independent review.

### F-2 — Truth-in-labelling has no machine-readable schema carrier

- **Source:** independent review lines 77–83; predecessor PLAN lines 29–36 and 304–307; current `floorplan_parse-1.1.0` provenance definitions.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** per-entity provenance, canonical output validity, recognition claims, G1 eligibility.
- **Required remediation:** Add required per-entity authorship plus an authorship reference; confine candidates to diagnostics; treat missing/unknown/inconsistent authorship as blocking; do not represent deletion as an entity label.
- **Proposed disposition:** ACCEPT AND ADAPT TO APPROVED AUTOMATIC SCOPE. Current PLAN lines 63–74 restrict product output to `cad_exact` or `raster_auto`, bind `authorship_ref`, and isolate human labels in evaluation contracts. Packet lines 31 and 125 mirror this.
- **Rationale:** Moshe rejected manual product operation, so the predecessor's human-authored product vocabulary is superseded. The underlying truth-in-labelling invariant remains mandatory.
- **Evidence needed to close:** exact schemas and enums; validation/finalization tests for missing, unknown, candidate, human-label, and source-inconsistent values; proof candidates cannot enter canonical parse output; fresh review of the adapted vocabulary.
- **Remains open:** YES — only plan prose exists; no schema or tests were authorized.

### F-3 — Approval invalidation is incompatible with immutable finalized runs without lineage

- **Source:** independent review lines 85–91; ADR-0005 immutability clauses; predecessor PLAN lines 141–142, 262, 282, 296.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** review validity, stale approval rejection, immutable lifecycle, raster G1 eligibility.
- **Required remediation:** Create a new immutable lineage/head record for approval, supersession, and invalidation; consumers and G1 must resolve the current head without mutating prior records.
- **Proposed disposition:** ACCEPT. Current PLAN lines 76–84 define immutable `approved`, `superseded_by`, and `invalidated` lineage and require head resolution; packet lines 32, 75, 107, and 125 carry the same direction.
- **Rationale:** Otherwise a stale approval can remain machine-satisfying forever despite changed source, algorithm, evaluator, or evidence.
- **Evidence needed to close:** exact lineage schema and state transition table; tests for supersession/invalidation ordering, changed-bound-input hashes, stale-head rejection, concurrency, and historical immutability; independent contract review.
- **Remains open:** YES — design direction only.

### F-4 — Raster-only G1 prerequisite is not expressible and the raster predicate is undefined

- **Source:** independent review lines 93–99; `contracts/state_machine.yaml:44,89`; predecessor PLAN lines 143–145 and 152.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** Product A machine path, B-AUTO eligibility, G1 contract semantics.
- **Required remediation:** Add an explicit conditional-required-artifacts construct and a required source-bound `source_class` discriminator; never infer raster from `provenance.source_kind`; preserve G1's machine label.
- **Proposed disposition:** ACCEPT. Current PLAN lines 69 and 81 specify `source_class` and `conditional_required_artifacts`; packet lines 125 and 182 include the migration.
- **Rationale:** A prose-only or heuristic condition can either break CAD or let raster bypass review evidence.
- **Evidence needed to close:** versioned state-machine schema; exact condition semantics; fixtures proving CAD does not require raster review, raster does, missing/invalid source class fails closed, and G1 remains `human: false`; historical compatibility evidence.
- **Remains open:** YES.

### F-5 — Wall/opening metrics are segmentation- and entity-ID-dependent

- **Source:** independent review lines 101–106; predecessor PLAN lines 179–183, 193, 195, 216–217, and 273.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** headline wall/opening precision and recall, host matching, all corpus gates.
- **Required remediation:** Canonicalize labels and predictions identically into maximal tangent-continuous chains split only at frozen semantic junctions; score chain-level length-weighted matches; determine opening host equivalence geometrically, not by ID.
- **Proposed disposition:** ACCEPT. Current PLAN line 105 and packet line 64 define chain canonicalization, diagnostic primitive counts, and geometric host equivalence.
- **Rationale:** Correct geometry must not fail because one side splits a wall differently.
- **Evidence needed to close:** frozen label guide; deterministic matcher specification; one-to-many/segmentation invariance fixtures for collinear lines and arcs; opening-host equivalence fixtures; evaluator review and versioned outputs.
- **Remains open:** YES.

### F-6 — No per-plan machine floor and ambiguous aggregate definition

- **Source:** independent review lines 108–113; predecessor PLAN lines 216–222, 262, and 400.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** B-AUTO locked-corpus acceptance; prevention of a poor individual plan being hidden by averages.
- **Required remediation:** Define macro versus micro explicitly; require each emitted plan to meet wall/opening floors, zero critical FP, and topology; one failing plan blocks the corpus.
- **Proposed disposition:** ACCEPT. Current PLAN lines 109–125 and packet lines 52–64 set macro/slice thresholds, per-plan `0.980/0.980` floors, zero critical FP, full topology, and non-substitutability of micro figures.
- **Rationale:** The rejected visual outcome was an individual-plan failure; aggregate-only gates can reproduce that defect.
- **Evidence needed to close:** aggregator specification and tests where one poor plan fails an otherwise passing corpus; macro/micro/slice reports; missing-plan and rejected-input accounting; independent evaluation review.
- **Remains open:** YES.

### F-7 — Human-role independence and evaluator leakage

- **Source:** independent review lines 115–120; predecessor PLAN lines 171, 175, 214–226.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** validity of locked-corpus accuracy estimates and human QA.
- **Required remediation:** Under predecessor B0, separate operator from labelers/adjudicator and hide truth. Under Moshe's approved change, eliminate the product operator, freeze automatic output before truth opens, retain independent labels/adjudication, and define QA role boundaries.
- **Proposed disposition:** SUPERSEDED IN PART BY APPROVED SCOPE CHANGE; ACCEPT UNDERLYING INDEPENDENCE REQUIREMENT. Current PLAN lines 95–100 and packet lines 66–75 freeze automatic output, require independent labels/adjudication, bar QA edits, and make the gate non-evaluable if separation is unavailable.
- **Rationale:** The exact B0 self-scoring path no longer exists, but label/adjudication/QA leakage can still bias B-AUTO evaluation. The current text does not explicitly state whether the QA delegate may also be a labeler or adjudicator.
- **Evidence needed to close:** explicit role-separation matrix; identity records; custody/opening timeline; proof outputs and thresholds were frozen before truth; conflict-of-interest rule for QA versus labels/adjudication; leakage audit.
- **Remains open:** YES — material adaptation requires fresh advanced-evaluation review.

### F-8 — Required rendering/geometry capability is absent or unproven in the locked dependencies

- **Source:** independent review lines 122–128; `pyproject.toml`; original PLAN-002 dependency statement; evaluation spec browser assumptions.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** PNG/SVG evidence, CVD simulation, line/arc face derivation, B-AUTO recognition, 60-second CPU limit, cost/schedule credibility.
- **Required remediation:** Choose and approve the evidence/geometry/recognition dependency envelope; attach license/offline/determinism/hour implications; stop if infeasible rather than silently adding a dependency or manual fallback.
- **Proposed disposition:** CONDITIONALLY ACCEPT. Current PLAN line 140 and packet line 81 select a Pillow/NumPy CPU-only option and require a separately authorized WP0 feasibility spike with stop/replan on failure.
- **Rationale:** The option is honest but speculative. Fixed NumPy thresholding, arc voting, symbol classification, topology search, and face derivation are substantially broader than the review's original evidence-rendering concern and have not been demonstrated.
- **Evidence needed to close:** approved spike specification; representative hardest clean-raster fixtures; measured accuracy/yield/runtime/memory; arc-aware face and CVD correctness checks; determinism evidence; explicit dependency/model/license/compute decision if it fails; revised hours.
- **Remains open:** YES — this is an explicit feasibility gate, not a resolved capability.

### F-9 — Corpus acquisition conflicts with local-only and ADR-0004

- **Source:** independent review lines 130–136; predecessor PLAN lines 169, 173, and 294; ADR-0004 context.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** dataset representativeness, rights/privacy, zero-spend claim, local-only boundary.
- **Required remediation:** Treat acquisition as out-of-band human activity; prohibit pipeline retrieval; approve exact sources, licenses, rights owner, privacy treatment, and spend constraint; record the ADR amendment.
- **Proposed disposition:** ACCEPT. Current PLAN lines 95–101 and packet lines 112, 117, and 125 distinguish out-of-band acquisition from no-network product execution and require rights approval plus ADR-0006.
- **Rationale:** Real external families cannot be silently assumed under a no-retrieval/no-third-party baseline.
- **Evidence needed to close:** source/license manifest; named rights owner; non-sensitivity attestations; spend decision; private Layer B handling; ADR-0006; audit showing no pipeline network retrieval.
- **Remains open:** YES — acquisition itself is forbidden by this planning task and no source approvals exist.

### F-10 — Product A exact-geometry semantics are incomplete

- **Source:** independent review lines 138–147; predecessor PLAN lines 62, 67, 69, 71, 73; geometry memo requirements.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** Product A `1.000/1.000`, arcs, junctions, room-face identity, thickness, room area semantics.
- **Required remediation:** Define concentric ARC openings and reject chord-on-arc; quantized endpoint-only junctions and mid-span fail-closed behavior; exact canonical room/face matching; centreline area basis; exact thickness carrier.
- **Proposed disposition:** ACCEPT. Current PLAN lines 46–52 specify XDATA `PWA_METADATA/THICKNESS_M`, concentric arcs, quantized shared endpoints, canonical room sequences, and `area_basis`; packet lines 43–45 and 176 mirror them.
- **Rationale:** An exact deterministic claim is meaningless if geometry identity and encoding are ambiguous.
- **Evidence needed to close:** exact DXF/schema contract; positive/negative fixtures for line/arc hosts, chord rejection, crossings, quantization boundaries, winding/cyclic room equivalence, thickness units, and area basis; independent geometry review.
- **Remains open:** YES.

### F-11 — Missing `passage` opening type

- **Source:** independent review lines 149–155; geometry memo; current schema enum `[door, window]`.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** opening recall/type accuracy, room adjacency, leafless openings.
- **Required remediation:** Add `passage`, or explicitly reject every leafless-opening plan as out of domain.
- **Proposed disposition:** ACCEPT `passage`. Current PLAN lines 35 and 51 and packet lines 29, 45, 176 select the third type.
- **Rationale:** Omitting or misclassifying a passage can change topology and reproduce the missing-opening defect.
- **Evidence needed to close:** approved enum/schema; CAD and raster label-guide semantics; host/topology fixtures; migration/old-version rejection tests.
- **Remains open:** YES.

### F-12 — Zero-critical-FP statistical wording is incomplete/unverifiable

- **Source:** independent review lines 157–162; predecessor PLAN lines 199 and 404.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** accuracy claim, locked corpus, production wording, residual-risk acceptance.
- **Required remediation:** Define one-sided 95% method, report `3/n` by stratum when zero is observed, state the number, avoid population-zero claims, and limit outside-corpus claims to detected defects.
- **Proposed disposition:** ACCEPT. Current PLAN line 125 and packet lines 35–37 and 179 state the rule, `5.0%` example for 60 raster families, and residual-risk wording adapted to automatic execution.
- **Rationale:** “Zero observed” is not “zero risk,” and production plans have no ground truth.
- **Evidence needed to close:** frozen unit of analysis and strata; executable calculation; generated bounds from the locked manifest; claim-language review; incident path for undetected critical FP.
- **Remains open:** YES — no locked results exist and the exact statistical evaluator is unimplemented.

### F-13 — Cost/labour estimate omits material work

- **Source:** independent review lines 164–170; predecessor PLAN line 371; superseded packet estimate and label/review arithmetic.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** Option 2B schedule, labor cap, label/adjudication/QA work, re-review contingency.
- **Required remediation:** Publish label arithmetic, review/QA hours, development/regression work, and fresh-cap treatment for invalidation; revise engineering effort for the selected automatic path.
- **Proposed disposition:** ACCEPT BUT UNVALIDATED. Current PLAN lines 181–195 and packet lines 85–97 revise A+B-AUTO to 16–26 weeks, 700–1,200 engineering/QA hours, 260–520 label/corpus/adjudication hours, and 20–50 delegated-QA hours; locked labels are estimated at 100–200 hours; re-review needs a fresh cap.
- **Rationale:** Automatic raster recognition without correction increases technical risk and engineering scope; the predecessor estimate cannot simply be reused.
- **Evidence needed to close:** auditable work-breakdown structure by WP/role/corpus split; assumptions and throughput basis; feasibility-spike result; contingency ranges; explicit approved cap. Estimates must be revised again if F-8 changes the architecture.
- **Remains open:** YES.

### F-14 — Routing/provenance record silently drops an Anthropic session and dissent

- **Source:** independent review lines 172–178; superseded packet and prior OpenAI review; session `e89cd83c-215a-430e-a058-664d64724fae`.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** complete provider/model/fallback record and integrity of dissent handling.
- **Required remediation:** Restore the early session and A-only dissent; explicitly explain later recommendation changes rather than silently normalizing them.
- **Proposed disposition:** ACCEPT. Current PLAN lines 197–210 and packet lines 154–167 restore the session, early dissent, later A+B0 memo, and Moshe's final A+B-AUTO scope change; A-only remains an option.
- **Rationale:** Critical planning provenance must preserve contrary expert judgments and model-routing facts.
- **Evidence needed to close:** source-backed session/model metadata; exact fallback/effort “unknown” markers where unavailable; fresh review of the complete routing table against Kanban/session sources.
- **Remains open:** YES — source comparison has not been independently re-run against the revised hash.

### F-15 — Silent severity promotion of a published fail-open warning

- **Source:** independent review lines 180–186; `contracts/error_codes.md:3–4,67`; ADR-0005.
- **Severity:** BLOCKING.
- **Affected scope / acceptance target:** topology gating, compatibility, error-code governance, G1 behavior.
- **Required remediation:** Add new append-only blocking topology codes or explicitly ADR-authorize a severity change; do not silently repurpose `PARSE_ROOM_BOUNDARY_UNMATCHED`.
- **Proposed disposition:** ACCEPT NEW CODES. Current PLAN line 83 and packet line 125 propose new blocking codes and preserve the old severity.
- **Rationale:** Published code meaning is part of the contract and cannot be changed by implication.
- **Evidence needed to close:** exact code list and outcome mapping; ADR decision; old/new consumer compatibility tests; fixtures for crossing, leak, dangling boundary, and unmatched-warning behavior.
- **Remains open:** YES.

### F-16 — Hash-approved artifacts are untracked in Git

- **Source:** independent review lines 188–194; live `git status` still reports `?? .hermes/`.
- **Severity:** MAJOR, material non-blocking.
- **Affected scope / acceptance target:** durable approval anchor, artifact provenance, later proof of exact reviewed bytes.
- **Required remediation:** Track the exact plan, packet, register, review, and cited planning memos; record commit SHA alongside file SHA-256 before approval/release as governance allows.
- **Proposed disposition:** ACCEPT AS EXPLICIT PREREQUISITE, NOT EXECUTED. Current PLAN line 231 and packet line 137 acknowledge the missing anchor.
- **Rationale:** A working-tree hash can be lost or replaced with no durable history.
- **Evidence needed to close:** clean tracked paths; commit containing exact hashes; approval packet updated with commit SHA; independent verification that committed bytes match approved hashes.
- **Remains open:** YES — `.hermes/` is still untracked, and this task forbids commit/merge.

### F-17 — Append-only edit replay lacks explicit undo

- **Source:** independent review lines 196–200; predecessor PLAN lines 124 and 130.
- **Severity:** MAJOR.
- **Affected scope / acceptance target:** predecessor B0 edit replay; under current scope, B-AUTO diagnostic replay and immutable reruns.
- **Required remediation:** For B0, add append-only `revert_op`; under the approved automatic-only change, remove product edits entirely and define deterministic append-only recognition provenance, with changed algorithm/config producing a fresh run.
- **Proposed disposition:** SUPERSEDED BY APPROVED SCOPE CHANGE. Current PLAN lines 54–61 has no product `edit_ops`; it defines append-only `recognition_ops`, exact replay, frozen output, and immutable later revisions.
- **Rationale:** The exact undo defect is in a rejected manual product path. It must not be marked “fixed” by pretending B0 remains. The replacement still needs deterministic replay and revision lineage.
- **Evidence needed to close:** recognition-operation schema; algorithm/config version binding; repeat-run byte identity; cancellation/partial-op behavior; proof no edit/correction API can mutate or promote product output; fresh reviewer acceptance that F-17 is inapplicable rather than omitted.
- **Remains open:** YES.

### F-18 — Determinism environment is under-specified

- **Source:** independent review lines 202–207; source evaluation spec `environment.json` requirement.
- **Severity:** MAJOR.
- **Affected scope / acceptance target:** byte-identical SVG/PNG/geometry/diagnostics and reproducibility.
- **Required remediation:** Record commit, dirty flag, OS, Python, lock hash, renderer, locale, fonts, scale, and seeds; strip nondeterministic metadata; pin/outline fonts; distinguish same-environment byte identity from cross-environment normalized-pixel equality.
- **Proposed disposition:** ACCEPT. Current PLAN line 142 and packet line 83 restore these requirements.
- **Rationale:** Renderer/font/environment variance makes unqualified byte identity unfalsifiable.
- **Evidence needed to close:** exact `environment.json` schema; pinned font artifact/hash; PNG chunk tests; normalized-pixel algorithm; repeated clean-run evidence on the supported environments.
- **Remains open:** YES.

### F-19 — Legibility/CVD gates are not measurable

- **Source:** independent review lines 209–213; predecessor PLAN lines 253 and 258.
- **Severity:** MAJOR.
- **Affected scope / acceptance target:** visual evidence usability, label collisions, color-blind accessibility.
- **Required remediation:** Name CVD transform/deficiency/severity, define post-simulation contrast threshold, and define collision geometry.
- **Proposed disposition:** ACCEPT. Current PLAN lines 144–150 and packet line 83 specify Viénot/Brettel, protanopia/deuteranopia/tritanopia severity 1.0, `3:1`, and glyph-box collision definitions.
- **Rationale:** Subjective “distinguishable” cannot be an automated acceptance gate.
- **Evidence needed to close:** deterministic transform implementation/reference vectors; contrast fixtures; glyph-bound calculation; collision tests at all zooms; independent accessibility/evidence review.
- **Remains open:** YES.

### F-20 — Required UI/containment/cancellation controls lack adversarial tests

- **Source:** independent review lines 215–219; predecessor PLAN §§9–10; ADR-0005 finalization/staging rules.
- **Severity:** MAJOR.
- **Affected scope / acceptance target:** loopback UI, CSRF/DNS-rebinding controls, path containment, worker kill, atomic finalization.
- **Required remediation:** Add tests for peer/Host/Origin rejection, CSRF replay, cookie/cache headers, traversal/reparse, listings/auth, process-tree termination, cancellation, and kill-during-finalization.
- **Proposed disposition:** ACCEPT. Current PLAN lines 154–169 and packet lines 115–121 enumerate the required controls and evidence.
- **Rationale:** An untested security or cancellation control is not an acceptance control.
- **Evidence needed to close:** platform-specific adversarial suite, including real Windows junction/reparse cases; process-tree and staging assertions; sanitized reports; independent threat-model review.
- **Remains open:** YES.

### F-21 — Tolerances were loosened without rationale; pixel rules were undefined for CAD

- **Source:** independent review lines 221–226; geometry memo tighter tolerances; predecessor PLAN lines 187–195.
- **Severity:** MAJOR.
- **Affected scope / acceptance target:** line/opening matching, CAD/raster comparability, short-wall scoring.
- **Required remediation:** Restore or explicitly justify each delta; mark pixel terms raster-only; bound relaxed short-wall orientation and use endpoint scoring below the bound.
- **Proposed disposition:** ACCEPT. Current PLAN lines 107 and 123 and packet line 64 restore ≤1° angle, ≥95% overlap, width error ≤`max(0.020 m,2%)`, raster-only pixel terms, and endpoint-only scoring below 0.20 m.
- **Rationale:** Unannounced looser tolerances can conceal exactly the offset/overrun/opening errors being remediated.
- **Evidence needed to close:** frozen evaluator spec; boundary fixtures immediately below/at/above each tolerance; CAD fixtures proving no pixel term; approved delta table for any future relaxation.
- **Remains open:** YES.

### F-22 — Confidence semantics conflict with existing G1 rules

- **Source:** independent review lines 228–232; ADR-0005 low-confidence rule; PLAN-002 threshold; geometry memo.
- **Severity:** MAJOR.
- **Affected scope / acceptance target:** B-AUTO entity schema, review ordering, low-confidence findings, G1 eligibility.
- **Required remediation:** Define product-specific confidence semantics and prove confidence never overrides invariants or promotes unsupported output; preserve the existing low-confidence block unless an explicit ADR changes it.
- **Proposed disposition:** ADAPTED, PARTIALLY SPECIFIED. Current PLAN line 60 gives B-AUTO calibrated diagnostic confidence and forbids override/promotion; line 74 blocks inconsistent authorship; packet line 139 records the adapted disposition.
- **Rationale:** Unlike predecessor B0 human-verified entities, B-AUTO cannot simply label every accepted entity `1.0`. The current plan does not yet define calibration method, threshold-to-finding mapping, or exact interaction with `LOW_CONFIDENCE_THRESHOLD = 0.5`.
- **Evidence needed to close:** confidence/calibration specification; schema ranges and semantics; threshold/finding mapping; tests showing low confidence blocks G1 and cannot be hidden by aggregate accuracy; reliability/calibration evidence by stratum; ADR review if existing behavior changes.
- **Remains open:** YES — this is a material unresolved adaptation, not merely a wording change.

### F-23 — `legacy_manual` conflicts with no historical relabelling

- **Source:** independent review lines 234–237; predecessor PLAN lines 27 and 300.
- **Severity:** MAJOR.
- **Affected scope / acceptance target:** historical evidence immutability and recognition claims.
- **Required remediation:** Put `legacy_manual` only in a new external evidence index; never edit or annotate historical artifact bytes.
- **Proposed disposition:** ACCEPT. Current PLAN line 72 and packet line 125 use an external index and preserve historical bytes.
- **Rationale:** Historical evidence can be excluded from claims without rewriting the record.
- **Evidence needed to close:** index contract and hash binding; before/after byte hashes of historical artifacts; migration tests proving no historical rewrite; claim filter tests.
- **Remains open:** YES.

### F-24 — Scale and color-sanitization wording defects

- **Source:** independent review lines 239–242; predecessor PLAN lines 232 and 294.
- **Severity:** MINOR.
- **Affected scope / acceptance target:** physical-dimension invariance, missing-anchor handling, contrast measurement, privacy sanitization.
- **Required remediation:** Say crop/resampling may not alter recovered physical dimensions and missing anchors yield `PARSE_SCALE_UNKNOWN`; convert to declared sRGB before contrast rather than stripping ICC blindly.
- **Proposed disposition:** ACCEPT. Current PLAN line 171 and packet line 83 contain both corrections.
- **Rationale:** Resampling changes metres-per-pixel, and removing color profiles can change measured color.
- **Evidence needed to close:** exact-hash independent wording review; crop/resample/anchor fixtures; ICC-to-sRGB and contrast reference tests; metadata privacy tests.
- **Remains open:** YES — revised text has not been independently accepted.

## 4. Missing, contradictory, or unverified source material

1. **Review target mismatch:** the only independent review applies to predecessor hash `1c466214…`. The current A+B-AUTO plan hash `de506463…` materially changes F-2, F-7, F-8, F-13, F-17, and F-22 and has no fresh independent review.
2. **Count normalization:** the review invocation record notes a signature count normalized from nine to eight MAJOR findings. The enumerated report has exactly eight (F-16..F-23); this register uses the enumerated set and preserves the discrepancy.
3. **Git anchoring:** live status still shows `.hermes/` untracked. F-16 is not closed by file hashes alone.
4. **Feasibility evidence:** no evidence currently proves the proposed CPU-only Pillow/NumPy B-AUTO path can meet accuracy, emit yield, topology, determinism, 60-second, or 1.5-GiB targets. F-8 and F-13 remain dependent on a separately authorized spike.
5. **Evaluation-role ambiguity:** the revised plan removes the B0 operator and freezes automatic outputs, but does not explicitly state whether the all-plan QA delegate may also be a labeler or adjudicator. F-7 requires that policy before closure.
6. **Confidence gap:** the revised plan names calibrated diagnostic confidence but does not define calibration, the low-confidence finding mapping, or its exact G1 behavior. F-22 remains materially open.
7. **No implementation evidence:** the independent review was document/contract-only and ran no tests. This task also performs planning only; no schema, contract, evaluator, corpus, UI, security, or geometry capability is claimed implemented.

## 5. Required approval-packet insertion

The final approval packet should include or link this register and state:

> All 24 enumerated independent-review findings are retained at their original severities. The current PLAN contains proposed dispositions, but no finding is declared closed by plan prose alone. Every finding remains open pending its named closure evidence. The prior review targets SHA-256 `1c466214…`; a fresh independent opposite-provider review must inspect the exact revised A+B-AUTO PLAN SHA-256 `de506463…`, this register, and the companion packet. F-16 additionally remains open until the artifacts have a tracked Git commit anchor. Approval of scope does not authorize implementation and does not itself close technical findings.

## 6. Closure gate for this register

This register is complete when all F-1..F-24 are present with source, severity, affected target, remediation, disposition, rationale, closure evidence, and open state. It does not close the findings. Downstream closure requires:

1. Moshe's explicit approval or return decision on the exact revised scope and targets;
2. a fresh independent review of the exact revised hashes and material B-AUTO adaptations;
3. approved ADR/contract/evaluator/corpus/feasibility artifacts where listed;
4. implementation and test evidence only through later separately authorized work packages; and
5. a durable tracked Git anchor before an artifact is treated as approval/release evidence.

# REGISTER STATUS: COMPLETE FOR PLANNING — ALL 24 FINDINGS REMAIN OPEN
