# ADR-0006 — PLAN-002RF WP0 automatic CAD/raster direction and fail-closed feasibility result

- Status: PROPOSED — WP0 evidence complete enough for a stop decision; independent review and Moshe continuation decision required
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
5. The WP0 fixture is rights-cleared and computationally cheap, but it has no independent truth and no two authoritative scale anchors. Its prior hand-authored annotation is not independent truth.
6. Therefore the fixture is unsupported and accuracy/yield are not evaluable. Geometry emission from it would be a CRITICAL outcome inversion. The measured result is `STOP`, despite two byte-identical diagnostic replays. Their time and `tracemalloc` figures are diagnostic-only and cannot establish the 60 s / soft 1.5 GiB recognition thresholds.
7. No Product B implementation package, corpus scoring, finding closure, activation, or WP1 starts from this result. A new explicit decision may authorize a rights-cleared independently labeled/scale-anchored WP0 fixture set, select Product A-only, narrow scope, or reject the route. Gates may not be weakened.
8. Migration, if later authorized, is additive/new-runs-only. Historical schemas, manifests, bytes, and PLAN-002 evidence remain immutable. Default route stays the current baseline.
9. Any new error codes are append-only; no severity mutation. Exact schema/catalog/bundle/code shapes remain blocked pending contract design/review.
10. Local-only boundaries remain: no upload/telemetry/network/model call by product execution, no GPU/H200/cloud/remote, no spend, no G7/G8, no PLAN-003.

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
- Negative: Product B feasibility remains unproven; WP1 and all dependent B metrics remain blocked.
- Residual: Windows hard-RSS enforcement remains unavailable; current memory measurement is diagnostic-only. One fixture cannot support the approved 30-case clean-raster yield gate or required slices. The no-OCR rule conflicts with an unspecified mechanism for obtaining two machine-readable raster scale anchors; Moshe must resolve that conflict without weakening fail-closed scale semantics.

## Rollback

This proposal changes no production contract or route. Rollback is deletion/reversion of the WP0 branch before merge. If later additive routes exist, rollback disables the named route, preserves immutable finalized history, quarantines staging, reruns baseline/security/determinism evidence, and requires fresh independent review plus explicit approval before re-enable.
