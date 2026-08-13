# ADR-0006 — PLAN-002RF WP0 automatic CAD/raster direction and fail-closed feasibility result

- Status: PROPOSED — WP0 closure candidate preserves truthful `STOP / NOT_EVALUABLE`; routes remain default-off
- Date: 2026-08-12
- Controlling approval packet: `D:/משה פרוייקטים/פיתוח אתרים/PanoWorld-Automation/.hermes/plans/2026-08-11_220700-plan-002rf-final-remediation-approval-packet.md`
- Approved packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Scope: PLAN-002RF WP0, Local-only Part 1

## Context

The approved direction is Product A (`cad_exact`) plus Product B-AUTO (`raster_auto`), automatic-only and default-off. Product B must emit conforming immutable machine geometry or fail closed; manual marking, correction, tuning, rescue, OCR, learned models, GPU/H200, cloud/remote execution, network corpus acquisition and silent dependency additions are excluded.

ADR-0004 remains authoritative for the implemented PLAN-002 baseline. This ADR proposes a future additive envelope only; it does not modify published contracts or activate either route.

## Decision

1. Retain Product A+B-AUTO as the approved planning direction, not an implemented or activated capability.
2. Product authorship is limited to `cad_exact` and `raster_auto`; human-created truth/evidence is never product output.
3. Product B is automatic-only and fail-closed. Confidence cannot promote or rescue output.
4. Native straight and bounded circular-arc geometry, sourced thickness, centreline room basis, and distinct `door`/`window`/`passage` remain required future contract properties.
5. The original WP0 sample remains unsuitable for scoring because its prior author-created annotation is not independent truth and it has no two authoritative scale anchors.
6. The separately tracked WP0-FX1 package supplies a project-owned, rights-cleared clean synthetic raster, frozen truth derived only from source geometry (`recognizer_inputs=[]`), and three hash-bound authoritative scale anchors at exactly `0.005 m/px`. Its deterministic fixture replay is valid 5/5, targeted tests pass 7/7, and the existing approved environment full suite passes 376/376 with two pre-existing Pillow warnings.
7. WP0-FX1 is an evidence fixture, not a recognizer. Accuracy, supported yield, recognition runtime and recognition peak working set remain `NOT_EVALUABLE`; the earlier 0.039475 s / 1,692,138-byte probe is diagnostic only. Consequently the binding feasibility verdict is `STOP`, without inferring failure or success of a future Product-B engine.
8. Moshe's full-campaign authorization of 2026-08-13 permits the already planned Local-only WP1–WP6 technical chain to proceed dependency-by-dependency after fresh evidence and review. It does not activate Product A/B routes, authorize PLAN-003, weaken any gate, or turn this fixture into product output.
9. Migration, if later authorized, is additive/new-runs-only. Historical schemas, manifests, bytes, and PLAN-002 evidence remain immutable. Default route stays the current baseline.
10. Any new error codes are append-only; no severity mutation. Exact schema/catalog/bundle/code shapes remain blocked pending contract design/review.
11. Local-only boundaries remain: no upload/telemetry/network/model call by product execution, no GPU/H200/cloud/remote, no spend, no G7/G8, no PLAN-003.

## Moshe decisions — 2026-08-13

1. **1A — bounded fixture evidence authorized.** A separately tracked Local-only WP0 package (`t_c6b406c5`, `WP0-FX1`) may create a rights-cleared clean-raster fixture with frozen independent geometry truth and two authoritative scale anchors. This is evidence production only: it does not authorize Product-B implementation, scoring by a nonexistent recognizer, route activation, or WP1.
2. **2A — installation incident disposition.** Moshe accepts the documented deletion/lock-preservation rollback as closure of the unauthorized `uv run` incident. Pinned-environment replay and the full suite remain pending and may not be inferred from that acceptance.
3. **3B — reviewer identity exception.** Moshe explicitly accepts the existing `gpt-5.6-sol`, provider-alias `headroom` review as the cross-provider exception despite unavailable first-party/fallback proof. Its BLOCKED findings remain substantive; the exception changes provenance acceptance, not the technical verdict.

WP0-FX1 was completed at checkpoint `6c8c3784fd83989ac3cc72733355bf9406ff6688`. Its fresh independent OmniRoute read-only review approved implementation `fc3a9c3cd75875aa80274827656f4cbc2086ac49` plus index checkpoint `e2fbd32fabe868462b421dedc2bdea2426e1624f` with no findings. Moshe's later full-campaign authorization supersedes the inter-WP continuation stop while preserving all substantive gates and the separate WP6 route-activation decision.

## Relationship to ADR-0004

This ADR explicitly proposes to supersede only ADR-0004's geometry-envelope and no-third-party-dataset assumptions for future named `cad_exact`/`raster_auto` routes. It does not rewrite ADR-0004, alter the existing parser, or claim its replacement has been implemented. Until additive contracts and their independent review pass, ADR-0004 and the existing baseline remain active.

## WP0 measured evidence

- Fixture SHA-256: `917a5753feceb65f8401381894bfb0809bd43194879002d2aa2acb74ee80df08`.
- Rights: public domain; tracked provenance in `samples/README.md`.
- Environment: Windows 10 build 19045, Intel i7-9800X (8C/16T), 51,202,351,104 RAM bytes, Python 3.11.15.
- Executed environment packages: Pillow 12.2.0, NumPy 2.4.3. This differs from `uv.lock` (Pillow 12.3.0, NumPy 2.4.6), so pinned-environment acceptance is not proven.
- Diagnostic replays: 2; canonical hash identical (`de4358ea8ebdee3f345f1ecc962376a06d4035a35e7e9cecff6a27beb5ce8db6`).
- Runtime max: 0.039475 s. Python `tracemalloc` peak: 1,692,138 bytes. These measure only a diagnostic grayscale/edge probe, not a recognition pipeline or peak working set, and therefore do not pass U-10.
- Accuracy/yield: not scored and not inferable.
- Stop blockers: `INDEPENDENT_TRUTH_MISSING`, `TWO_AUTHORITATIVE_SCALE_ANCHORS_MISSING`.

## Consequences

- Positive: no invented accuracy claim, no manual fallback, no provider/model dependency in product execution, and no accidental route activation.
- Negative: Product B recognition feasibility remains unproven; no accuracy/yield/resource claim exists yet.
- Residual: Windows hard-RSS enforcement remains unavailable; current memory measurement is diagnostic-only. One synthetic fixture cannot support the approved 30-case clean-raster yield gate or required slices. The future no-OCR scale-discovery mechanism remains a WP1/WP4 contract and evaluator problem; fixture-side authoritative anchors are evaluation truth, not product input.

## Rollback

This proposal changes no production contract or route. Rollback is deletion/reversion of the WP0 branch before merge. If later additive routes exist, rollback disables the named route, preserves immutable finalized history, quarantines staging, reruns baseline/security/determinism evidence, and requires fresh independent review plus explicit approval before re-enable.
