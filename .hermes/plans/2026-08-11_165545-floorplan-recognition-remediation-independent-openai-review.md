# Independent OpenAI Cross-Provider Review — PLAN-002R Remediation

Date: 2026-08-11
Scope: planning artifacts only
Reviewer provider/model: OpenAI `gpt-5.6-sol`, solver/xhigh profile
Fallback: none reported by active runtime
Compared architect: Anthropic `claude-opus-5`, completed synthesis session `e89cd83c-215a-430e-a058-664d64724fae`
Verdict: **APPROVE for Moshe's scope decision; NOT approval to implement**

## Review basis

Reviewed the repository's current PLAN-002 contract, visual-gate record, state-machine semantics, schemas/types/overlay shape, the remediation plan, approval packet, and the completed Opus synthesis. The review asks whether the packet is decision-complete and honest, not whether the proposed system already meets its metrics.

## Findings and disposition

### O-1 — MAJOR — Manual annotation could still be mistaken for recognition

Risk: a geometrically accurate human-corrected artifact could be marketed or recorded as automatic output, repeating the root PLAN-002 claim failure.

Disposition: **fixed**. The plan now makes truth-in-labelling a blocking invariant, records per-entity method, labels human-touched output `human-verified`, and excludes legacy manual evidence from automatic-accuracy claims.

### O-2 — MAJOR — A+B recommendation concealed the geometry architect's safer A-only recommendation

Risk: decision-makers would see consensus where there is a material scope disagreement.

Disposition: **fixed**. The full plan and approval packet preserve Opus's A-only Part 1 recommendation as an explicit dissent and require Moshe to choose A-only or A+B with B separately labelled human-verified.

### O-3 — MAJOR — Aggregate metrics could hide failure on angled/curved walls

Risk: high aggregate scores from axis-aligned walls could reproduce the rejected omissions.

Disposition: **fixed**. Metrics are now both entity-wise and length-weighted, with separate axis/angled/arc buckets, signed endpoint under-run/overrun, one-to-one matching, arc fidelity, host-aware opening matching, and an absolute zero-critical-opening-false-positive gate.

### O-4 — MAJOR — Final human accuracy alone did not prove Product B had product value

Risk: a correction UI could pass because people redraw every plan manually.

Disposition: **fixed**. Product B now has median correction-time targets (≤8 minutes clean, ≤20 minutes supported scans) and a kill criterion when correction is no faster than redraw.

### O-5 — MINOR — Overlay readability and replayability were qualitative

Disposition: **fixed**. The plan adds zero label-collision, ≥11 px text, ≥4.5:1 contrast, leader-line requirements, clean/diff/audit views, append-only `edit_ops`, and deterministic replay over the proposal hash.

### O-6 — MINOR — Future implementation paths were not exact

Disposition: **fixed**. Review UI and lifecycle tests now have exact proposed paths under `src/pwa/floorplan/` and `tests/integration/`.

### O-7 — DECISION — Per-plan approval versus current machine-labelled G1

The current state machine declares G1 non-human. The remediation must not silently flip it. The packet correctly offers a new hash-bound review artifact as a machine-verifiable prerequisite and makes a human-G1 semantic change a separate explicit choice. This remains a Moshe decision, not a review defect.

### O-8 — DECISION — Thresholds and labor estimates are proposals, not evidence

The metrics, dataset sizes and labor ranges are sufficiently concrete for scope approval, but they are not validated performance claims. Implementation must retain red tests, hidden-set evaluation, correction-time measurement and stop/escalate behavior; it may not weaken thresholds or expand scope without approval.

## Security and migration conclusion

The plan carries forward containment, immutable runs, hashes, SVG restrictions and current resource caps, then adds UI/CV-specific bounds, localhost-only binding, CSRF/CSP, no arbitrary URLs/paths, proposal/search limits and adversarial cases. Migration is additive and preserves historical schemas/runs. Rollback disables the new route without deleting published contracts/evidence.

## Final review conclusion

The artifacts are adequate to ask Moshe for the eight listed decisions. They do not claim arbitrary raster 100% automation, do not erase the rejected evidence, and do not authorize implementation, PLAN-003, GPU/H200/cloud, G7 or G8. Approval should create a new bounded implementation card only after Moshe chooses product scope, contract/gate treatment, quantitative gates, dataset budget and labor cap.
