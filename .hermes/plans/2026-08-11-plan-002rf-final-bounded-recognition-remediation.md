# PLAN-002RF — Final bounded floorplan-recognition remediation plan

- Date: 2026-08-11
- Status: **PLANNING ONLY — BLOCKED PENDING MOSHE'S EXPLICIT SCOPE AND ACCEPTANCE-TARGET APPROVAL**
- Kanban approval-packet task: `t_301c6952`
- Incorporates independent review: `.hermes/reviews/independent-anthropic-plan-002r-review-20260811.md`
- Supersedes for approval: `.hermes/plans/2026-08-11_171713-plan-002r-bounded-recognition-remediation.md`
- Preserves: accepted PLAN-002 history, ADR-0005, immutable historical runs, exact-version validation, and published ADR history.
- Supersedes if approved: ADR-0004 decision 2's DXF geometry envelope and its “no third-party dataset” context clause. WP0 must create ADR-0006; ADR-0004 remains published and unchanged.
- Hard boundary: Local-only Part 1. No H200, GPU, cloud, remote execution, G7, G8, purchase/spend, production activation, implementation, merge, push, or PLAN-003 work is authorized.

## 1. Executive decision and achievable claim

Recommended scope is **Product A + Product B-AUTO**:

- **A — deterministic compliant CAD parsing:** automatic only because the source explicitly carries the approved PWA semantics.
- **B-AUTO — bounded automatic raster recognition:** a local CPU-only pipeline converts a supported image or rendered PDF page into canonical walls, rooms, scale, and typed hosted openings without human marking, drawing, correction, or parameter tuning during a product run. A run either emits machine-generated geometry that passes every machine gate or fails closed.

Not selected in this approval:

- **B-MANUAL — manual or semi-automatic raster marking/correction:** rejected as a product path. It may not be used to rescue, complete, or promote a product run.
- **C — arbitrary-raster automatic recognition:** deferred outside Part 1.
- “100% automatic accuracy for arbitrary raster plans”: rejected as unachievable.
- Generic CAD inference, automatic topology repair, silent geometry approximation, and confidence-based promotion: rejected.

Achievable claim: exact deterministic parsing for a narrow, project-owned CAD convention and fully automatic recognition for a narrow, declared raster envelope, subject to the locked-corpus targets below. The raster targets are acceptance goals, not a pre-existing accuracy claim; until all gates pass, B-AUTO remains research/shadow-only and cannot satisfy G1. Finite corpus results are not population guarantees. Human work is limited to dataset truth, independent QA, adjudication, and release acceptance; it never changes the product-run geometry.

## 2. Supported and unsupported matrix

| Product/path | Supported | Unsupported / fail-closed | Final label |
|---|---|---|---|
| A source | DXF; 2D modelspace; zero elevation; one floor; explicit mm/cm/m units; exact case-sensitive `PWA-*` layers | arbitrary layers/symbols; 3D; paperspace; blocks/INSERT; xrefs; images/OLE; hatches; multiple layouts/storeys; external references | `cad_exact` |
| A walls | arbitrary-angle `LINE`; bounded circular `ARC`; ordered line/bulge-arc `LWPOLYLINE` paths | SPLINE, ellipse, NURBS, non-circular curves, guessed wall bands, snapping/gap closure/extension/merge | `cad_exact` |
| A rooms | closed `PWA-ROOM` line/bulge polylines on wall centrelines, exactly matching derived bounded faces after quantization | duplicate/ambiguous/nested mismatch, self-intersection, centreline/clear-face ambiguity | `cad_exact` |
| A openings | `door`, `window`, `passage`; unique typed host; line on line host; concentric arc on arc host | chord opening on arc host; ambiguous/off-wall/over-wide/wrong-type opening | `cad_exact` |
| B-AUTO source | one orthographic 2D floor per image/rendered PDF page; high-contrast black/white linework; fixed supported symbol guide; skew within ±5°; two machine-readable scale anchors | photos, perspective/isometric, hand sketches, severe damage/occlusion, multiple floors, handwriting, unknown symbols, contradictory/missing scale, non-circular curves | `raster_auto` |
| B-AUTO walls | automatically recovered native line/arc centrelines and thickness from paired edges or declared single-line convention | unresolved centreline/thickness, unsupported raster style, silent extension, topology repair that changes semantics | `raster_auto` or fail closed |
| B-AUTO rooms/openings | automatically derived bounded faces; `door`/`window`/`passage`; unique host and adjacency; every machine invariant passes | ambiguous host/type, unresolved leak/crossing, unsupported symbol, any output needing human correction | `raster_auto` or fail closed |
| B-MANUAL | dataset annotation and QA tooling only, isolated from product execution | manual/semi-automatic marking, correction, parameter tuning, or acceptance as part of a product run | not a product output |
| C | none under this approval | arbitrary-raster canonical recognition, OCR/models/training/weights | deferred |

## 3. Exact geometry and provenance contract proposed for approval

### 3.1 Product A

1. Wall truth is a declared centreline. Optional thickness is encoded only in DXF XDATA registered under application ID `PWA_METADATA`, key `THICKNESS_M`, as a positive decimal metre value after unit normalization. Missing thickness stays unknown; it is never guessed.
2. Openings on straight hosts are `LINE`; openings on arc hosts are concentric `ARC` entities. Chord-encoded openings on arc hosts fail closed.
3. Two wall primitives form a junction only when they share an endpoint after canonical quantization at repository `QUANTUM_M = 1e-4 m`. A mid-span crossing without a shared source vertex fails closed; it is never inferred or split.
4. `PWA-ROOM` polylines lie on wall centrelines. An explicit room matches a derived face only when canonical primitive type/order and quantized vertex/arc sequences are identical, modulo winding and cyclic start.
5. Every room records `area_basis` as `centreline` or `clear_internal_face`; this plan selects `centreline` for Product A. Consumers may not silently reinterpret it as clear area.
6. Door, window, and untyped passage are distinct opening types. Plans with leafless openings are supported only through `passage`.
7. Accepted A structural confidence is `1.0`, meaning explicit source semantics, not learned probability.

### 3.2 Product B-AUTO

1. Geometry uses ordered native line/arc paths. Source edges, derived centreline, thickness, source coordinates, and recognition diagnostics remain distinct.
2. The fixed automatic stages are: sanitize/render → classify support envelope → deskew/binarize → recover scale anchors → extract line/arc and paired-edge candidates → classify opening motifs → generate host bindings → solve bounded topology → canonicalize → run machine gates → emit or fail closed. No interactive input, per-plan tuning, correction UI, or hidden operator step is permitted between source ingestion and final outcome.
3. Endpoint clustering, tiny-gap closure, collinear merge, T-junction split, arc-line tangent join, and duplicate suppression are allowed only as deterministic, versioned transforms within approved numerical bounds. Any candidate transform that could create/delete an opening, bridge an opening, change room count, or exceed tolerance fails the run; it is never presented for human repair.
4. `recognition_ops` is append-only diagnostic provenance containing stage, algorithm/config version, source references, candidates, accepted/rejected transform, and reason. Exact replay with the pinned environment must reproduce the same canonical bytes and outcome. There are no product `edit_ops`.
5. Accepted entities carry `authorship: raster_auto`, `authorship_ref` to a recognition operation, and calibrated diagnostic confidence. Confidence never overrides an invariant, promotes an unsupported case, or serves as an accuracy claim.
6. Human QA may inspect frozen outputs, label truth, adjudicate, and accept/reject a corpus or release. QA cannot edit the output under test. A defect becomes a new labeled case and later separately authorized code/config revision; the original run remains immutable.

## 4. Truth-in-labelling and schema carriers

New exact-version contracts must require:

- per-entity `authorship ∈ {cad_exact, raster_auto}` for product output; human-authored labels remain confined to evaluation contracts;
- `authorship_ref` naming the source entity or recognition operation that produced the entity;
- `source_class ∈ {cad_conforming, raster}` bound to verified source bytes;
- native line/arc paths, sourced thickness, room `area_basis`, opening type including `passage`, and approved-review reference;
- intermediate raster candidates only in diagnostic evidence, never in canonical parse output;
- `legacy_manual` only in a new external evidence index; historical artifacts stay byte-unchanged and unannotated.

Missing, unknown, or source-inconsistent authorship is CRITICAL and blocks finalization. Candidate geometry never appears in canonical parse output.

## 5. Immutable review lineage and G1 migration

1. B-AUTO evaluation creates a separate immutable `floorplan_review` run binding source, untouched automatic parse, diagnostic evidence, truth labels, metrics, QA disposition, labelers, adjudicator, reviewer authority, and hashes.
2. Approval status changes are represented by a new immutable lineage record with status `approved`, `superseded_by:<run-id>`, or `invalidated:<reason,changed-bound-input-hash>`. Prior records are never changed or deleted.
3. Consumers resolve the lineage head. G1 rejects an approval superseded or invalidated by a later lineage record.
4. The versioned state-machine contract gains `conditional_required_artifacts`, with `floorplan_review` required when `floorplan_parse.payload.source_class == raster`. `provenance.source_kind` is not the discriminator. G1 remains machine-labelled (`human: false`).
5. Until the migration, evaluator, locked corpus, and B-AUTO implementation are separately approved, implemented, and version-verified, B-AUTO is diagnostic/shadow only and cannot satisfy G1. Product A retains machine eligibility.
6. New blocking topology codes (for example `PARSE_ROOM_BOUNDARY_CROSSING` and `PARSE_EXTERIOR_LEAK`) are append-only and mapped to ADR-0005 outcomes. Existing `PARSE_ROOM_BOUNDARY_UNMATCHED` severity is not silently changed.
7. Exact schema/bundle versions are selected in WP0 after live catalog review. Historical bytes and exact-version behavior remain valid.

## 6. Corpus, rights, and independence

Proposed corpus:

- development: 60 source families;
- deterministic regression: 40 single-defect micro-plans;
- locked acceptance: 100 families (30 clean raster, 30 degraded raster, 25 conforming CAD, 15 fail-closed CAD);
- optional algorithm-development corpus: 200 families, declared unused for Product A and excluded from locked acceptance; no model training is selected in Part 1.

Source-family grouping keeps every crop, scan, rotation, render, export, annotation, and derivative in one split. Leakage checks use source hash, perceptual raster hash, canonical geometry hash, provenance/license ID, and manual collision review.

Corpus acquisition is an out-of-band, human-performed, approval-gated activity. No parser/UI/evaluator component performs network retrieval. Moshe must approve sources, licenses, a named rights owner, and zero-spend constraint. ADR-0006 records the amendment to ADR-0004's dataset framing.

Every locked plan receives two independent labels without parser-output visibility plus independent adjudication. The automatic output is frozen before truth is opened. QA compares only after adjudication and may record pass/fail and findings but may not alter either output or truth. Identities are recorded and verified. If label/adjudication separation cannot be staffed, the B-AUTO accuracy gate is **not evaluable** and no accuracy figure may be approved. Moshe has no required personal review role; QA/release reviewers are pre-named delegates.

Private Layer B source/evidence remains local and untracked; only approved redacted hashes/counts/metrics may enter Git. Rights and non-sensitivity require Moshe's attestation.

## 7. Canonical matching and acceptance targets

Before matching, labels and predictions undergo the identical canonicalization: join primitives into maximal tangent-continuous chains and split only at semantic junctions defined in the frozen label guide. Wall precision/recall is chain-level with length-weighted partial credit; raw primitive counts are diagnostic. Opening host equivalence is geometric—the canonical chain containing the matched centre—not entity-ID equality.

Pixel terms do not apply to CAD. Raster pixel terms use adjudicated source resolution. Relaxed orientation applies only to walls in `[0.20 m, 0.50 m)`; shorter walls use endpoint distance only.

| Gate | Product A conforming CAD | Product B-AUTO raster |
|---|---:|---:|
| wall chain P/R | 1.000 / 1.000 per plan and slice | aggregate macro ≥0.995/0.995; every slice ≥0.995/0.995; every plan ≥0.980/0.980 |
| opening P/R | 1.000 / 1.000 | aggregate macro ≥0.995/0.990; every plan ≥0.980/0.980 |
| critical false positives | zero observed | zero observed per plan and locked set |
| room topology | 100%; explicit/derived exact match | 100% valid faces and intended adjacency per plan |
| scale | relative error ≤0.01% | two-anchor median residual ≤1%; disagreement ≤2% |
| replay/determinism | byte-identical canonical output | byte-identical recognition outcome, canonical output, and diagnostics in pinned environment |
| automation | no interactive step | 100% of locked runs complete as emit-or-fail-closed with zero marking/drawing/correction/tuning |
| supported-set yield | n/a | report emit/fail-closed by stratum; target ≥95% emit on clean and ≥85% on supported scans; no accuracy credit for rejected inputs |
| unresolved findings | none | none |

“Overall” means macro-average across plans; micro metrics are reported and cannot substitute. Any plan below a floor blocks the corpus regardless of aggregate.

Matching tolerance proposal (restoring the geometry memo unless a stricter stratum limit applies): line orientation ≤1°, longitudinal overlap ≥95%, opening width error ≤`max(0.020 m, 2%)`; raster Hausdorff/endpoint/centre tolerances are evaluated at adjudicated resolution. Any requested relaxation requires a recorded delta, rationale, and fresh approval.

“Zero critical false positives” means zero observed in the locked set. Report exact one-sided 95% upper bounds by stratum using `3/n` when zero is observed; zero across 60 raster families implies an upper bound of 5.0% per-family. For plans outside the locked corpus the claim is only “automatic checks detected no critical false positive”; human QA is release/evaluation evidence, not a per-run product dependency. Undetected defects remain a named residual risk; no population-zero claim is made.

## 8. Evidence requirements

Every locked plan has separately hash-bound:

1. sanitized source alone;
2. adjudicated truth over source;
3. accepted geometry alone;
4. source + accepted geometry;
5. matched/FP/FN/tolerance diff;
6. topology/leak/junction view;
7. machine-readable metrics/findings;
8. immutable per-plan QA disposition and lineage head, with the automatic output left untouched.

Recommended no-new-dependency evidence and recognition envelope: deterministic SVG plus direct Pillow/NumPy PNG rendering; fixed NumPy implementations for thresholding, connected components, line/arc voting, paired-edge analysis, bounded symbol templates, topology search, face derivation, and CVD transforms. No OCR, learned model, browser, or network service is selected. WP0 must independently spike the hardest clean-raster stratum before architecture lock. If the CPU-only Pillow/NumPy path cannot plausibly meet accuracy, yield, and 60 s limits, stop for a revised dependency/model/license/compute plan; never add software or fall back to manual correction silently.

A deterministic `environment.json` records commit, dirty flag, OS, Python, lock hash, renderer version, locale, bundled font hash, device scale, and seeds, with paths/usernames redacted. SVG text is converted to paths or uses a bundled hash-pinned font subset. PNG time/text metadata is stripped. Byte identity is claimed only within the pinned environment; cross-environment equality uses normalized-pixel hashes.

Legibility:

- text ≥12 CSS px and legend ≥14 CSS px at 100%; text contrast ≥4.5:1; geometry contrast ≥3:1;
- no always-visible IDs/confidence over geometry;
- a collision is any glyph-bounding-box intersection with another glyph box, wall centreline, opening glyph, or room boundary;
- CVD simulation uses the Viénot/Brettel transform for protanopia, deuteranopia, and tritanopia at severity 1.0; accepted strokes must retain ≥3:1 contrast against source;
- door/window/passage distinguishable without color alone; no clipping or active/external SVG content.

A pre-named QA delegate reviews every locked plan; no sampling and no personal Moshe review is required. Review records pass/fail and findings only; it cannot modify an output. QA and machine gates are conjunctive for release acceptance, while product execution remains automatic.

## 9. Determinism, security, resource, and adversarial evidence

Required adversarial tests include geometry/scale/decoy/tolerance boundaries plus:

- reject non-loopback peers and Host/Origin mismatch;
- reject missing/stale/replayed CSRF; assert SameSite=Strict, HttpOnly, and `Cache-Control: no-store`;
- path traversal, symlink/reparse escape, arbitrary path, directory-listing, and unauthenticated draft rejection;
- process-tree termination on timeout and user cancellation;
- kill during atomic finalization: no finalized run, retained non-resumable staging;
- lineage-head invalidation after every bound-input/evaluator change.

Existing caps remain: source 50 MiB, entities 200,000, annotation 5 MiB, walls/rooms/openings 20,000/5,000/20,000, vertices 10,000, coordinate magnitude 100,000 m, decoded raster 100 MP, overlay 70 MiB, worker output 1 MiB, DXF worker 30 s.

Proposed additional caps requiring approval: 32,768 px max side, 60 s whole local run, 1.5 GiB soft observed working-set target. Windows has no claimed portable hard-RSS sandbox. Workers are killable, no-network, no-child-spawn processes. No automatic limit relaxation or in-run retry.

Local UI: loopback only, exact Host/Origin, unguessable per-launch URL secret, strict cookies, CSRF, no-store, reviewer authority, permission-restricted drafts, no listings/arbitrary paths. Local-only prohibits upload, telemetry, model calls, cloud backup, and pipeline network retrieval.

Sanitization removes EXIF/comments/GPS/author metadata and converts to declared sRGB before contrast measurement; original bytes stay hash-bound. Rotation/crop/resampling may not alter recovered physical dimensions; crop removing all anchors yields `PARSE_SCALE_UNKNOWN`.

## 10. Rollback, migration, and incident impact

Migration is additive and new-runs-only. Historical schemas/manifests/runs/evidence remain byte-identical. New consumers must prove historical round trips; old versions must reject new fields predictably. `scene_geometry` and PLAN-003 semantics remain untouched.

Default remains the current baseline. New paths are default-off and named per run. Rollback disables the affected route, stops new runs, verifies worker termination, preserves immutable history, quarantines bounded staging, runs baseline/adversarial/migration/determinism checks, and requires independent review plus Moshe's applicable gate before re-enable. No rollback deletes history, relabels evidence, or weakens gates.

SEV-1: path escape, external access, disclosure, finalized mutation, unkillable worker. SEV-2: nondeterminism, contract misrouting, incorrect G1 eligibility, resource-control bypass, critical false opening. SEV-3: bounded malformed-input/performance defect without integrity impact.

## 11. Phases, schedule, and cost options

All ranges are planning estimates; approvals/private-data waiting is excluded. Incremental infrastructure spend is USD 0 only if the existing Pillow/NumPy rendering/geometry path and rights-cleared zero-cost corpus are approved and feasible.

| Option | Scope | Calendar / labor | Decision impact |
|---|---|---|---|
| 1 | Preserve current line-only baseline | 1–2 weeks; 5–8 engineer-days | lowest risk; does not close arcs/thickness/raster usability |
| 2A | Product A only | 4–7 weeks; 180–300 engineering/QA h; 40–80 corpus/review h | safest automatic claim; does not serve raster inputs |
| 2B recommended | A + B-AUTO | 16–26 weeks; 700–1,200 engineering/QA h; 260–520 labeling/corpus/adjudication h; 20–50 delegated QA h | bounded CAD plus bounded automatic raster; highest technical risk; stop/go after each stratum |
| 3 later | broaden B-AUTO raster styles | not estimated; new corpus and gates required | separately approved; no manual fallback |
| C | arbitrary-raster research | not estimated/authorized | separate rights/model/compute plan required |

Locked-set labeling alone is 200 independent labels: 100–200 h at 30–60 min each, before adjudication, development/regression preparation, or QA. Re-review after invalidation is unbudgeted contingency requiring a fresh decision and cap. The larger B-AUTO engineering range reflects automatic line/arc, symbol, scale, and topology recovery without operator correction; if Option 2B is capped below the approved range, scope/yield must shrink rather than introducing manual operation or weakening gates.

Phases: WP0 decision/ADR/CPU feasibility spike plan; WP1 corpus/evaluator lock; WP2 additive contracts/lifecycle; WP3 A; WP4 B-AUTO clean-raster engine; WP5 supported-scan hardening and local shadow/rollback rehearsal; WP6 named bounded activation decision. Each phase has a stop/go gate; failure never routes to manual correction. Approval of this plan authorizes none of those implementation packages; each requires separately tracked work.

## 12. Provider/model/fallback record

| Role | Provider route | Requested | Actual | Effort/runtime | Fallback | Skills/session |
|---|---|---|---|---|---|---|
| early geometry synthesis | Anthropic first-party via Claude Code | `opus` | `claude-opus-5` | high requested; other runtime not recorded | none observed | session `e89cd83c-215a-430e-a058-664d64724fae`; skill record unavailable in final source |
| critical geometry memo `t_66d1d834` | Anthropic first-party via Claude Code | `opus` | `claude-opus-5` | high; detailed runtime not recorded | none observed | `computer-vision-expert`; session `81405d64-8518-4e5d-b1ec-ac134c9e59d4` |
| evaluation memo `t_5800b432` | OpenAI Codex | active/default | `gpt-5.6-sol` | runtime default; not exposed | none observed | not Claude; no Claude skills |
| operations memo `t_1d699970` | OpenAI Codex | active/default | `gpt-5.6-sol` | runtime default; not exposed | none observed | not Claude; no Claude skills |
| PLAN-002R synthesis `t_e50c0bd4` | OpenAI Codex | active/default | `gpt-5.6-sol` | runtime default; not exposed | none observed | not Claude; no Claude skills |
| independent review `t_b1633bf1` | Anthropic first-party via Claude Code | `opus` | `claude-opus-5` | plan mode; 833.342 s wall; 798.428 s API; 26 turns; effort field not exposed | none observed | `computer-vision-expert`, `advanced-evaluation`, `threat-modeling-expert`; session `53971edf-2b1e-48b8-86a9-3f81040a5dbb` |
| initial final disposition/packet `t_301c6952`, run 34 | OpenAI Codex | active/default | `gpt-5.6-sol` | runtime default; not exposed | none observed at authoring time | Hermes `kanban-worker`; no Claude session |
| automatic-only revision after Moshe decision, run 35 | OpenAI Codex | active/default | `gpt-5.6-sol` | runtime default; not exposed | none observed at revision time | Hermes `kanban-worker` + `plan`; no Claude session |

The early A-only Opus dissent is retained: it judged A-only the safest automatic Part 1 claim. The later Anthropic geometry memo's A+B0 recommendation is retained as historical context but superseded by Moshe's RETURN WITH CHANGES, which requires A+B-AUTO and forbids manual product operation. A-only remains Option 2A. Unavailable metadata is explicitly marked—not inferred. Any required opposite-provider mismatch or substitution blocks the gate.

## 13. Independent-review dispositions

| Findings | Disposition in this plan |
|---|---|
| F-1 | ADR-0006 supersession and decision registration required in WP0 |
| F-2 | product authorship restricted to `cad_exact`/`raster_auto`; human labels isolated in evaluation contracts |
| F-3 | immutable approval lineage and head resolution |
| F-4 | source_class and conditional_required_artifacts |
| F-5 | chain canonicalization and geometric host equivalence |
| F-6 | per-plan floors plus macro/micro definitions |
| F-7 | independent labelers/adjudicator and post-freeze QA; non-evaluable fail-closed; no product operator |
| F-8 | selected CPU-only Pillow/NumPy automatic recognition/evidence envelope; feasibility spike and stop decision |
| F-9 | out-of-band acquisition, rights owner, zero-spend approval, ADR-0006 |
| F-10 | exact arc opening, quantized junction, room match/area basis, XDATA thickness semantics |
| F-11 | `passage` selected as third type |
| F-12 | 95% `3/n` bound and production residual-risk wording |
| F-13 | revised automatic-pipeline labor arithmetic, delegated QA hours, re-review contingency |
| F-14 | restored early session/dissent and explicit supersession |
| F-15 | new append-only blocking codes; no silent severity mutation |
| F-16 | exact file hashes recorded in packet; Git commit anchor remains a pre-implementation/release prerequisite because this task may not commit |
| F-17 | no product edit log; append-only recognition provenance and immutable reruns |
| F-18 | deterministic environment, pinned font, metadata stripping, normalized pixel hash |
| F-19 | measurable CVD and collision criteria |
| F-20 | complete UI/containment/cancellation adversarial set |
| F-21 | restored tighter memo tolerances; pixel applicability and short-wall rules |
| F-22 | B-AUTO diagnostic confidence semantics; never a gate override |
| F-23 | external legacy index; no historical relabeling |
| F-24 | corrected scale and sRGB wording |

## 14. Approval boundary

Approval must identify this exact file hash and the selected clauses in the companion decision form. Silence, prior-plan approval, or general approval does not authorize implementation. Approval only authorizes later, separately tracked planning/implementation cards. No code, schema, dependency, dataset acquisition, compute provisioning, merge, activation, or PLAN-003 work begins under this document.

# BLOCKED — revised after Moshe's RETURN WITH CHANGES; pending approval of the automatic-only scope and adapted acceptance targets
