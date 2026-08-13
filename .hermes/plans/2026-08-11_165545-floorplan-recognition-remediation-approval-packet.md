# PLAN-002R Floorplan Recognition Remediation — Approval Packet

Date: 2026-08-11
Kanban: `t_67280b4a`
Status: PLANNING ONLY — BLOCKED pending Moshe approval

## Why this packet exists

The PLAN-002 visual gate was rejected. The sample showed roughly 50% useful marking, omitted angled/curved walls and many openings, included at least one false opening marker, offset/overrunning centrelines, and unreadable overlapping IDs. The raster route was manual annotation, not automatic recognition. Green tests proved contract behavior, not real-plan recognition accuracy.

## Recommended approval

Approve **Product A + Product B** only:

- **A — deterministic PWA CAD:** exact, narrow DXF convention with arbitrary-angle lines, circular arcs and straight/bulged polylines; explicit centreline semantics; no arbitrary CAD inference.
- **B — local raster human-in-the-loop:** CPU-only deterministic proposals plus mandatory correction UI and hash-bound per-plan human approval.
- **C — arbitrary automatic raster recognition:** deferred. It cannot honestly be guaranteed at 100% and needs a separate labeled-data/model/compute decision.

Truth-in-labelling is a hard gate: any artifact containing human-confirmed, edited or drawn geometry is labelled **human-verified**, never automatic recognition. Existing PLAN-002 raster evidence remains `legacy_manual` and is excluded from future automatic-accuracy claims.

No H200, GPU, cloud, remote execution, G7, G8 or PLAN-003 work is authorized.

## Acceptance target proposed for approval

- Product A compliant CAD: wall/opening precision and recall 1.000/1.000; zero critical false openings.
- Product B proposals: walls ≥0.97 precision / ≥0.93 recall; openings ≥0.995 precision / ≥0.80 recall; uncertain openings remain candidates only.
- Product B approved final: walls ≥0.995/≥0.995; openings ≥0.995/≥0.99; zero critical false openings absolute.
- Geometry: line angle error ≤1°; wall symmetric Hausdorff P95 ≤`max(4 px, 0.025 m)`; endpoint P95 ≤`max(3 px, 0.020 m)`; arc radius error ≤2%; sweep overlap ≥95%.
- Scale: CAD ≤0.01%; raster residual ≤1% with at least two anchors and ≤2% anchor disagreement.
- Topology: 100% valid approved room graph; no self-intersections, dangling boundaries or ambiguous opening hosts.
- Overlay: IDs/confidence hidden by default, zero overlapping always-visible labels, distinct door/window glyphs, clean/diff/audit views, deterministic safe SVG.
- Every plan requires source-vs-overlay evidence and human approval bound to source, annotation, parse, overlay and metric hashes.

## Dataset/budget proposed for approval

Minimum 100 rights-cleared plans, 3,000 wall primitives, 800 openings and 300 rooms, grouped 60/20/20 development/validation/hidden-test split. Include clean CAD exports, real raster diversity, deterministic degradation and adversarial fixtures. Hidden labels are double-annotated/adjudicated. Private source bytes never enter Git.

Recommended schedule: **10–12 elapsed weeks**, approximately **450–650 engineering hours + 200–350 labeling/QA hours**. A-only fallback is 3–4 weeks / 160–240 hours but does not solve raster usability. Product B also has a value gate: median correction time ≤8 minutes on clean exports and ≤20 minutes on supported scans; if correction is no faster than redrawing, B is stopped.

**Recorded Opus dissent:** the spatial/geometry architect recommends A-only as the safest Part 1 acceptance claim, keeping B separate until its hidden-set and correction-time gates are demonstrated. This packet recommends A+B as bounded products but requires Moshe to resolve that difference explicitly.

## Contract/migration choice

Recommended additive path:

- `floorplan_parse` 1.2.0;
- `floorplan_annotation` 1.1.0;
- new `floorplan_review` 1.0.0, or explicitly approved extension of `approval_record`;
- contracts bundle 1.3.0 for new runs only;
- all historical schemas/runs remain byte-unchanged and independently valid.

Recommended state treatment: keep G1 machine-verifiable and require the human review artifact as a prerequisite for an eligible raster result. Changing G1 itself to a human gate is a separate explicit decision.

## Decisions required from Moshe

1. **Scope:** choose A-only for the narrowest Part 1 claim, or A+B with B explicitly human-verified; C deferred.
2. **Geometry:** native line+arc paths; explicit centreline; thickness only when sourced/confirmed.
3. **Acceptance:** metric table and absolute zero-critical-opening-FP gate.
4. **Dataset:** 100 plans / 3,000 walls / 800 openings minimum and rights rules.
5. **Human control:** mandatory correction and per-plan hash-bound approval.
6. **Workflow:** new review artifact while G1 stays machine-verifiable, or explicitly change gate semantics.
7. **Budget:** recommended 10–12 week scope, A-only fallback, or a different cap.
8. **Boundary:** local Part 1 only; no GPU/H200/cloud/G7/G8; no PLAN-003.

## Evidence and review record

- Full plan: `.hermes/plans/2026-08-11_165545-floorplan-recognition-remediation.md`
- Critical routing: Anthropic Claude Code requested `opus`, transcript actual `claude-opus-5`, no fallback observed; `/skills` loaded `computer-vision-expert`; exploration session `f8b8a36f-455b-4ba9-a7c5-1e34fd5a411f`.
- Completed Opus synthesis: session `e89cd83c-215a-430e-a058-664d64724fae`, actual `claude-opus-5`, first-party Anthropic, one turn, high effort requested, no fallback, success, duration 329197 ms. Its truth-in-labelling, edit-op replay, bucket metrics, legibility/value gates and A-only dissent are included in the full plan.
- Independent review: `.hermes/plans/2026-08-11_165545-floorplan-recognition-remediation-independent-openai-review.md`; OpenAI `gpt-5.6-sol`, solver/xhigh profile, no fallback reported; verdict **APPROVE for Moshe's scope decision, not implementation**. All four major and two minor drafting findings are incorporated; state-gate treatment and proposed thresholds remain explicit approval decisions.
- The first exploratory Opus print pass exceeded the foreground cap. It is recorded as incomplete; the separate synthesis above completed successfully.

## Approval effect

Approval authorizes a new bounded remediation implementation card only. It does not approve the rejected overlay, retroactively turn manual annotation into automatic recognition, start PLAN-003, or waive later visual/metric/security reviews.
