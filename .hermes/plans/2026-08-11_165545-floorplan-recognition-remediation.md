# Floorplan Recognition Remediation Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Replace the rejected PLAN-002 visual result with an honest, bounded floorplan product whose CAD path is deterministic, whose raster path is explicitly human-corrected, and whose outputs meet measurable geometry and safety gates before any PLAN-003 handoff.

**Architecture:** Keep three products separate. Product A is a narrow deterministic CAD parser for an explicit PWA convention. Product B is a local CPU-only raster proposal engine plus mandatory correction/approval UI. Product C is true automatic recognition of arbitrary raster plans and is deferred: it is neither promised nor smuggled into Part 1. Both active products emit versioned line/arc geometry, immutable evidence, and fail-closed findings through the existing derived-run boundary.

**Tech Stack:** Python 3.11, existing `numpy`, `Pillow`, `ezdxf`, `jsonschema`, deterministic SVG, pytest. Any new CV/UI dependency requires a separate approved dependency/license decision; the default spike must first use existing dependencies and a local loopback-only UI.

---

## 0. Rejection and scope baseline

Moshe rejected the first G1 visual gate because the artifact was only roughly 50% useful: rotated/angled/curved walls and many openings were omitted, at least one opening marker was a false positive, wall centrelines were offset or overran their source walls, and opaque IDs overlapped until the overlay was unreadable. The repository confirms the declared simplifications at `evidence/PLAN-002/visual-gate/na4-na5-record-20260811.md:90-100` and the manual annotation path at `PROJECT-STATE.yaml:1854-1892`.

This is a remediation plan, not authorization to implement it. Under card `t_67280b4a` no production code, contract, lockfile, historical evidence, state-machine semantics, merge, push, PLAN-003 work, GPU, H200, cloud, G7 or G8 may begin.

**Truth-in-labelling is a blocking invariant.** Every artifact declares the producing route and every entity's method (`cad_exact`, `auto_candidate`, `human_confirmed`, `human_edited`, `human_drawn`, or `human_deleted`). An artifact containing any human-authored or human-edited geometry may be described only as **human-verified**, never as automatic recognition. A mislabelled claim fails the gate even when the geometry itself is accurate. Existing PLAN-002 raster evidence is retained as `legacy_manual` evidence and excluded from future automatic-accuracy claims.

## 1. Product decision

### Product A — narrow deterministic DXF/CAD parsing: SUPPORTED and required

Supported input is an explicit PWA modelspace convention, not arbitrary CAD inference:

- 2D, zero-elevation modelspace only; declared `$INSUNITS` in mm/cm/m.
- Wall centreline geometry on approved PWA layers as `LINE`, `ARC`, or `LWPOLYLINE`; each polyline is deterministically decomposed into ordered line segments and circular bulge arcs with parent-handle provenance.
- Any line angle is supported. Circular arcs are supported within declared radius/sweep bounds. `SPLINE`, ellipse, NURBS, 3D polylines, blocks, xrefs, images, OLE, hatches, nonzero elevation, paperspace geometry and multiple storeys remain unsupported and fail closed.
- The canonical wall primitive is a centreline plus optional explicit `thickness_m`. Source wall edges are not silently treated as centrelines and are not paired heuristically in Product A. If the file supplies only edges, it is unsupported unless a later approved convention supplies an unambiguous wall-band entity.
- Door/window geometry carries type, host wall primitive, centre, clear width along the host tangent, and optional swing/direction metadata. A valid opening must resolve to exactly one host, fit fully within that host, and preserve wall continuity on both sides. On an arc, width is arc length along the host. Ambiguous, off-wall, duplicate, wrong-type, or over-wide openings fail.

For contract-compliant CAD, the parser is expected to be exact and deterministic. It does not claim to interpret arbitrary architect layer names or recover semantics from generic drafting.

### Product B — manual/semi-automatic raster annotation: SUPPORTED and recommended

Product B is the realistic Part 1 raster product. It is not “automatic recognition.” A deterministic local proposal stage may suggest wall bands/centrelines, arcs and opening candidates using thresholding, connected components, morphology, line-segment/Hough-style voting and geometric consistency. Every proposal remains editable and no raster run can become approved without a human correction record bound to the exact source, annotation, parse and clean overlay hashes.

Initially supported raster envelope:

- one 2D floor, orthographic plan, PNG/JPEG or approved rendered PDF page;
- 150–600 effective DPI, no perspective, deskew within ±5° after explicit correction;
- high-contrast printed linework; straight walls and circular arcs; standard door/window symbols only as proposals;
- at least two independent scale anchors for automatic scale acceptance.

Unsupported or mandatory-manual cases include photographs, perspective plans, hand sketches, severe compression/occlusion, mixed floors, arbitrary symbols, missing scale, non-circular curves, and plans whose topology cannot be made unambiguous. Unsupported means `partial`/`failed`, visible findings, and no G1/PLAN-003 handoff — never a guess.

The correction UI must provide: pan/zoom; source/detection/diff layers; draw/edit/split/merge line and arc walls; choose centreline or paired edges; set explicit thickness; add/delete/retype openings; bind/rebind a host; edit width and tangent; add at least two scale anchors; snap with preview and undo; topology diagnostics; confidence queue; keyboard navigation; save draft; and a final immutable approval action. IDs and confidence are off by default and appear on selection/hover or in a side table.

### Product C — true automatic raster recognition: DEFERRED

Arbitrary raster plans cannot be guaranteed 100% automatic accuracy. The same pixels can represent walls, dimensions, furniture, hatching, text, demolition layers or scanning artefacts; scale may be absent; opening symbols vary by region and era; and rasterization destroys original CAD semantics. Classical CPU-only CV can generate useful candidates on a bounded visual domain but cannot resolve every semantic ambiguity. Learned recognition would still require a large licensed labeled corpus, held-out evaluation and human review, and would not produce a universal guarantee.

Product C is a future research/product decision only. No model weights, OCR stack, learned parser, training, dataset download, GPU or cloud work is included in local-only Part 1.

## 2. Geometry and topology contract

The next additive contract should represent a wall path as ordered native primitives:

- `line`: start/end;
- `arc`: start/end/center/radius/sweep/direction;
- a wall may contain a contiguous ordered primitive list and optional explicit thickness;
- overlay tessellation is rendering-only and never replaces native arc identity.

Centreline policy:

1. CAD PWA centreline entities remain centreline truth.
2. Raster double-edge walls derive a candidate centreline midway between matched boundaries and record both source edges and estimated thickness.
3. Raster single-line walls are tagged `single_line_assumption` and cannot be auto-approved when thickness/centre is ambiguous.
4. Extension beyond observed support is prohibited unless a human explicitly performs and approves the edit. Every repaired endpoint records before/after provenance.

Topology repair is proposal-only until approved. Candidate operations are endpoint clustering, tiny-gap closure, collinear merge, T-junction split, arc-line tangent join, and duplicate suppression. Each operation has a bounded tolerance, is deterministic, individually reversible, and records provenance. No repair may create/delete an opening, bridge across a detected opening, change room count, or move a primitive beyond tolerance without human confirmation.

Human correction is represented as append-only `edit_ops`; the approved geometry must be reproducible by replaying those operations over the exact proposal hash. This makes edits reversible and reviewable instead of silently replacing the machine result.

Opening semantics:

- match requires correct type, unique host, centre distance to host within tolerance, tangent-consistent span, and width fit;
- a “critical false positive” is any accepted opening where ground truth has solid wall, or an accepted opening attached to the wrong host/type such that downstream geometry would create a false passage or exterior breach;
- candidate-only markers are visually distinct and never serialized as accepted openings;
- zero critical false positives is an absolute final-output gate.

Scale:

- CAD uses verified `$INSUNITS`; expected relative scale error ≤0.01% after quantization.
- Raster automatic acceptance requires at least two independent declared dimensions; median fitted scale residual ≤1% and anchor disagreement ≤2%.
- One anchor is `partial` and requires explicit human acknowledgement; no reliable anchor or contradiction >2% fails with `PARSE_SCALE_UNKNOWN`.

## 3. Labeled dataset and split

Before tuning thresholds, create a rights-cleared dataset manifest with at least 100 plans, 3,000 wall primitives, 800 openings and 300 rooms:

- 30 clean vector-to-raster exports with exact CAD ground truth;
- 30 real licensed/public raster plans spanning line weights, rotations, angled bays and circular walls;
- 20 degraded copies with deterministic blur, JPEG artefacts, skew, noise and downsampling;
- 20 adversarial plans containing furniture lines, dimension chains, grids, hatching, near-parallel walls, tiny wall gaps, opening-like symbols, nested rooms and scale contradictions.

Split 60/20/20 into development/validation/hidden test by source building/template, never by pages or augmentations. Each item stores license/provenance, source hash, pixel dimensions, scale evidence, native line/arc walls, wall edges/thickness where knowable, typed/hosted openings, room cycles, unsupported flags and annotator notes. Two annotators label the hidden set; disagreements are adjudicated. Private plans remain untracked; only redacted aggregate metrics/hashes may enter Git.

## 4. Measurable acceptance gates

Metrics use one-to-one assignment so one prediction cannot satisfy multiple labels. A wall match requires primitive type agreement, angular error ≤1° for lines, at least 95% longitudinal overlap, and symmetric source-space Hausdorff distance within `max(4 px, 0.025 m)`. Endpoint P95 must be within `max(3 px, 0.020 m)`. Arc matches additionally require radius error ≤2% and sweep overlap ≥95%.

Wall precision/recall is reported both entity-wise and length-weighted. Recall is also reported separately for axis-aligned, angled (>2°), and circular-arc buckets; aggregate success cannot hide a failed geometry class. Endpoint error records signed under-run/overrun, and any extension past a true junction is reported separately.

An opening match requires correct door/window type, correct host wall, centre error within `max(4 px, 0.050 m)`, and width error within `max(0.020 m, 2%)`.

Required hidden-test results:

| Gate | Product A, compliant CAD | Product B proposals | Product B human-approved final |
|---|---:|---:|---:|
| Wall precision / recall | 1.000 / 1.000 | ≥0.97 / ≥0.93 | ≥0.995 / ≥0.995 |
| Opening precision / recall | 1.000 / 1.000 | ≥0.995 / ≥0.80 | ≥0.995 / ≥0.99 |
| Critical opening false positives | 0 | 0 accepted; candidates allowed | 0 absolute |
| Valid room topology | 100% | diagnostic only | 100% |
| Supported arbitrary wall angles | 100% fixtures | ≥95% matched | 100% labeled |
| Supported circular-arc coverage | 100% fixtures | ≥90% matched | 100% labeled |
| Scale tolerance | ≤0.01% | ≤1% residual, ≤2% disagreement | same or explicit approved override |

Every approved final must also have: no self-intersections, duplicate entities, dangling room boundaries, ambiguous hosts or unresolved topology findings; all intended rooms represented as valid cycles; deterministic byte-identical output on repeat; and per-plan human approval bound to hashes. Aggregate metrics never waive a per-plan failure.

Overlay acceptance:

- provide a clean source-vs-detection overlay plus a diff/error layer and separate audit index;
- no always-visible entity IDs/confidence text over geometry; default clean view contains zero overlapping labels;
- every entity is selectable/addressable through the index, and doors/windows have distinct shape and color, not identical circles;
- reviewers can toggle source, wall edges, centrelines, arcs, openings, rooms, repairs and uncertainty;
- static evidence remains self-contained SVG with no script/external URL; the local correction UI is a separate loopback-only application;
- approval packet includes source, clean overlay, error/diff view, metric report and hash-bound approval record.
- at 100% evidence render, visible text is at least 11 px with WCAG contrast ≥4.5:1; any moved callout has a leader line; automated bounding-box collision count is zero.

Product B is also judged by correction effort: median correction time ≤8 minutes for clean exports and ≤20 minutes for supported scans. If correction takes as long as redrawing on a representative validation sample, Product B fails its value gate even if final human-corrected geometry is accurate.

## 5. Fail-closed behavior

No automatic threshold can promote a raster candidate directly to accepted geometry. `complete` requires supported input, valid scale, valid topology, no error finding, no unresolved low-confidence item, zero critical false-positive opening, all correction tasks resolved, and the required approval record. Otherwise output is diagnostic `partial`/`failed` and cannot advance.

Confidence is calibrated per primitive class on the validation set, but acceptance is rule-based. Confidence never overrides an invariant. Any unsupported curve, ambiguous centreline, ambiguous opening host, scale conflict, topology-changing repair, out-of-domain raster score, or resource-limit event blocks approval.

## 6. Security and resource limits

Carry forward PLAN-002 containment, immutable derived runs, hash verification, EXIF stripping, no external SVG references and append-only errors. Retain existing caps unless evidence justifies a lower value: 50 MiB source, 100 MP raster, 200,000 DXF entities, 20,000 walls/openings, 10,000 polygon vertices, 70 MiB overlay, 30 s parser timeout. Add bounded arc tessellation, connected-component count, proposal count, repair-search iterations and UI upload/body limits. The UI binds only to `127.0.0.1`, uses random per-session CSRF tokens and restrictive CSP, accepts no arbitrary URL/path, performs no network request, and never serves files outside the selected immutable run.

Adversarial regression includes traversal/reparse points, DXF xref/INSERT/path payloads, entity bombs, huge bulges/radii, NaN/Inf, degenerate arcs, Unicode/HTML labels, SVG injection, decompression bombs, dense-grid proposal explosion, scale contradictions, near-duplicate openings and timeout cleanup.

## 7. Contract migration and rollback

Recommended additive migration after approval:

- `floorplan_parse` 1.2.0: native line/arc wall paths, optional explicit thickness, repair provenance and proposal/accepted state where applicable;
- `floorplan_annotation` 1.1.0: line/arc walls, source edges, host bindings, scale anchors and correction provenance;
- new `floorplan_review` 1.0.0 (or an explicitly approved extension of `approval_record`) binding source, annotation, parse, overlay and metric hashes;
- contracts bundle 1.3.0 for new runs only; 1.0/1.1/1.2 remain byte-unchanged and independently valid;
- append-only `PARSE_*`/`REVIEW_*` codes.

Existing PLAN-002 runs remain auditable but are not grandfathered into the new acceptance claim. No historical run or schema is rewritten. Rollback disables the new adapter/UI behind explicit version selection and returns new inputs to `partial/unsupported`; published schemas and evidence remain. If per-plan review is enforced before G1 while G1 remains machine-labeled, the approval artifact becomes a machine-verifiable prerequisite. Changing G1 itself to a human gate is a separate state-machine decision and is not silently included.

## 8. Implementation tasks after explicit approval

### Task 1: Freeze rejected-gate evidence and metric definitions

**Files:** Create `evidence/PLAN-002R/rejection/`, `docs/plans/PLAN-002R-floorplan-recognition-remediation.md`; test `tests/unit/test_floorplan_metrics.py`.

1. Copy only approved/redacted source-vs-overlay evidence and hashes; do not rewrite PLAN-002 evidence.
2. Write failing one-to-one matching tests for duplicates, lines, arcs, openings and critical false positives.
3. Run `python -m pytest tests/unit/test_floorplan_metrics.py -v`; expected FAIL because evaluator is absent.
4. Implement only the evaluator; rerun to PASS.
5. Commit `test: define PLAN-002R recognition metrics`.

### Task 2: Version the geometry contracts

**Files:** Create `schemas/floorplan_parse/v1/floorplan_parse-1.2.0.schema.json`, `schemas/floorplan_annotation/v1/floorplan_annotation-1.1.0.schema.json`, approved review schema; modify `src/pwa/contracts.py`, `schemas/README.md` and contract tests.

1. Add red exact-version/additivity tests.
2. Add native line/arc union, optional explicit thickness, provenance and review hash bindings.
3. Prove historical schema bytes/examples unchanged.
4. Run contract/round-trip tests; commit `feat: version floorplan remediation contracts`.

### Task 3: Extend canonical geometry without tessellation loss

**Files:** Modify `src/pwa/floorplan/types.py`, `normalize.py`, `validate.py`, `config.py`; tests in `tests/unit/test_floorplan_normalize.py` and `test_floorplan_validate.py`.

1. Red tests for arbitrary angles, arc identity, continuity, tangency, radius/sweep bounds and stable IDs.
2. Add native primitives and deterministic normalization.
3. Add topology graph and reversible repair records.
4. Run targeted tests; commit `feat: represent line and arc wall paths`.

### Task 4: Implement Product A convention

**Files:** Modify `src/pwa/floorplan/dxf_source.py`, `dxf_worker.py`; add CAD fixtures under `tests/golden/floorplan/plan002r/`.

1. Red tests for `LINE`, `ARC`, straight/bulged `LWPOLYLINE`, arbitrary angles, arc openings and every unsupported entity.
2. Decompose polylines with handle/segment provenance.
3. Enforce unique host and along-path opening width.
4. Run golden/determinism tests; commit `feat: extend bounded PWA CAD parser`.

### Task 5: Build the rights-cleared dataset and evaluator

**Files:** Create `datasets/floorplan-recognition/manifest.json` or external-private manifest pointer, `tools/evaluate_floorplan_recognition.py`, adversarial fixture generator and redacted aggregate evidence.

1. Lock license/provenance rules and grouped split before threshold tuning.
2. Double-label/adjudicate the hidden set.
3. Generate deterministic degradations/adversarial fixtures.
4. Verify counts, no split leakage and no private bytes in Git.

### Task 6: Spike Product B proposals with existing dependencies

**Files:** Create `src/pwa/floorplan/raster_proposals.py`; test `tests/unit/test_floorplan_raster_proposals.py`.

1. Red tests for wall bands, arbitrary angles, arcs, opening-like decoys and bounded proposal counts.
2. Implement deterministic candidates using existing dependencies first.
3. Benchmark CPU/runtime and validation metrics.
4. If gates cannot be met, stop for a dependency/model decision; never weaken gates.

### Task 7: Build correction and approval UI

**Files:** Create `src/pwa/floorplan/review_ui/`; create `tests/integration/test_floorplan_review_ui.py`; test API containment, CSRF, undo, hash binding and accessibility.

1. Add geometry editing and scale/topology workflows.
2. Keep candidates visually distinct from accepted entities.
3. Generate immutable annotation/review artifacts only on explicit approve.
4. Prove localhost-only/no-network behavior and no path escape.

### Task 8: Replace cluttered overlay evidence

**Files:** Modify `src/pwa/floorplan/overlay.py`, `config.py`, `tests/unit/test_floorplan_overlay.py`.

1. Red tests: no default text labels, distinct door/window glyphs, line/arc/edge/centre/diff groups and audit index.
2. Preserve deterministic safe SVG and source alignment.
3. Generate dense-plan captures at 100%, 200% and fit-to-page.
4. Require Moshe visual approval.

### Task 9: Integrate fail-closed lifecycle and rollback

**Files:** Modify `src/pwa/floorplan/builder.py`, `src/pwa/floorplan/runs.py`, `src/pwa/floorplan/cli.py`, `contracts/error_codes.md`, the exact approved review/state contracts, `tests/integration/test_plan002r_review_lifecycle.py`, and `tests/integration/test_plan002r_failures.py`.

1. Red tests that absent approval, unresolved candidate, scale conflict, topology error and critical false opening cannot become eligible.
2. Preserve immutable source/derived runs.
3. Add version/adaptor selection and rollback tests.
4. Run full `pytest`, `git diff --check`, schema round-trip, dependency diff and private-data scan.

### Task 10: Independent reviews and final human gate

1. Opus reviews spatial/geometry behavior and source-vs-overlay evidence.
2. Independent OpenAI reviews contracts, metrics, security, migration and overclaiming.
3. Record provider, requested model, actual model, effort and fallback; Claude sessions invoke `/skills` before design/review.
4. Remediate findings, rerun deterministic tests and create approval evidence.
5. Block until Moshe approves the exact results. Do not begin PLAN-003.

## 9. Schedule and cost options

All estimates are local CPU-only labor ranges, not commitments:

- **Option A only:** 3–4 elapsed weeks, 160–240 engineering/QA hours. Delivers deterministic compliant CAD; does not solve raster recognition.
- **Recommended A+B:** 10–12 elapsed weeks with dataset work parallelized; 450–650 engineering hours plus 200–350 labeling/QA hours.
- **A+B plus Product C research:** at least 16–24 additional weeks, thousands of licensed labels and a new model/dependency/compute decision. Excluded from Part 1 and still cannot guarantee arbitrary-plan 100% accuracy.

The Opus geometry review recommends **A-only as the safest Part 1 acceptance claim**, with B remaining a separately labelled human-verification product until its correction-time and hidden-set gates are demonstrated. This dissent is intentionally preserved for Moshe's decision rather than silently normalized into the A+B recommendation.

## 10. Approval prerequisites

Implementation remains blocked until Moshe explicitly approves:

1. products A+B as Part 1 scope and Product C deferral;
2. native line/arc contract and centreline/thickness semantics;
3. quantitative acceptance table and zero-critical-opening-FP rule;
4. 100-plan/3,000-wall/800-opening dataset minimum and rights policy;
5. mandatory per-plan human correction/approval and chosen approval artifact/state treatment;
6. the 10–12 week/labor option or reduced scope;
7. no GPU/H200/cloud/G7/G8 and no PLAN-003 start.

## 11. Routing record

- Critical spatial/geometry architect: Anthropic Claude Code, requested `opus`, transcript model `claude-opus-5`, `/skills` discovery invoked and `computer-vision-expert` loaded, session `f8b8a36f-455b-4ba9-a7c5-1e34fd5a411f`; no fallback observed. The long print-mode pass exceeded the Hermes foreground cap, so no false completion claim is made.
- Detached Opus synthesis completed successfully: session `e89cd83c-215a-430e-a058-664d64724fae`, actual `claude-opus-5`, first-party Anthropic routing, one turn, high effort requested, no fallback, 329197 ms. Its truth-in-labelling, edit-op replay, per-geometry buckets, legibility metrics and Product-B value gate are incorporated above; its A-only Part 1 recommendation is preserved as a dissenting decision point.
- Independent cross-provider reviewer: OpenAI `gpt-5.6-sol` (this Kanban worker), solver/xhigh profile; fallback none reported by the active runtime.
- Every future Claude session must use `/skills` and record provider/requested model/actual model/effort/fallback in its evidence header.
