# PLAN-002 acceptance

- Verification run: `RUN-PLAN002-REWORK-20260810` -- bounded rework closing the 2026-08-10 independent
  code/security/contracts (`evidence/PLAN-002/reviews/independent-anthropic-code-review-20260810.md`) and
  spatial/geometry (`evidence/PLAN-002/reviews/independent-anthropic-spatial-review-20260810.md`) review
  findings; both reviews had returned `NEEDS_REWORK`. Supersedes `RUN-20260809-173417-586650`.
- Full pytest: **291 passed**, `failures=0`, `errors=0`, `skipped=0` (baseline before this rework: **261 passed**).
- Full-suite command: `python -m pytest -v --basetemp .tmp/pytest-plan002-rework-20260810 --junitxml evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/junit.xml --cov=src/pwa --cov-report=xml:evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/coverage.xml` via repository `.venv` Python 3.11.
- Failure matrix: `coverage_status=complete`, `rows=65` (added `f-duplicate-opening` for C-1 spatial and
  `f-opening-not-collinear` for M-2 spatial), `missing_fixture_rows=[]`, `duplicate_fixture_rows=[]`.
- Layer A raster parse: `complete`, CLI 0. Layer A DXF parse: `complete`, CLI 0.
- Determinism: canonical projection hash `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e` for both adapters (unchanged); overlay hashes changed from the pre-rework run (DXF overlay now renders rooms/doors/ids/confidence from independent source primitives per M-4/M-11; raster overlay derives its media type from source bytes per M-5) and are repeat-run identical per adapter, verified across two independent `parse_run()` invocations per adapter.
- Routing requested: `PROVIDER=openai`, `REQUESTED_MODEL=gpt-5.4`, `EFFORT=high`, `FALLBACK=none`, `MODEL_REASON=approved bounded implementation model`.
- Routing runtime: `runtime_provider=headroom`, `ACTUAL_MODEL_ID=gpt-5.4` from local Codex session `019fe716-d621-7881-b2b9-f23978c760c0` (`<home>/.codex/sessions/2026/08/09/rollout-2026-08-09T18-14-21-019fe716-d621-7881-b2b9-f23978c760c0.jsonl`) lines 1 and 6. (M-10, code review 2026-08-10: redacted -- §12 forbids absolute paths/user names in tracked evidence; the session id and line numbers keep the claim independently verifiable.)
- Reviewer routing: `REVIEWER_MODEL=claude-opus-5`, `CROSS_PROVIDER_REVIEW=pending/required`.
- Git verification: `git diff --check` clean; `git diff -- pyproject.toml uv.lock` empty.
- Hard boundary statement: no network, install, upload, provisioning, spending, GPU, H200, cloud, or remote execution performed; G7/G8 remain deferred to Part 2.
- Review readiness: **Part 1 implementation review-ready**. Remaining downstream gates only: fail-closed human visual/geometry approval of first implementation-generated Layer A overlay, and pending cross-provider review.

## Evidence Paths

- Test results: `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/`
- Canonical parses: `evidence/PLAN-002/parse/layer-a-1-raster.json`, `evidence/PLAN-002/parse/layer-a-1-dxf.json`
- Canonical overlays: `evidence/PLAN-002/overlays/layer-a-1-raster.svg`, `evidence/PLAN-002/overlays/layer-a-1-dxf.svg`
- Determinism: `evidence/PLAN-002/determinism/geometry-projection-hashes.json`
- Failure matrix: `evidence/PLAN-002/failures/parse-failure-matrix.json`
- Runtime metadata: `evidence/PLAN-002/implementation/runtime-metadata.json`
- Source pre/post hash evidence: `evidence/PLAN-002/implementation/source-hash-evidence.json`
- Git verification: `evidence/PLAN-002/implementation/git-verification.json`
- AC traceability: `evidence/PLAN-002/implementation/ac-traceability.md`

## Acceptance Notes

- `f-existing-final` is recorded as `finalized_set=none` and `finalized_new_derived_run=false`; a pre-existing final directory is not counted as a newly finalized derived run.
- `f-low-confidence` remains unit-only exactly as allowed by the approved brief for unreachable Part 1 source coverage.
- `real-plan-redacted.json` remains the canonical redacted evidence artifact; hostile-label escaping is evidenced by `tests/unit/test_floorplan_overlay.py::test_hostile_label_escaped` and the `f-hostile-label` row in the failure matrix.
- 2026-08-10 bounded rework: full disposition table, before/after test counts and explicit no-contract/no-dependency/no-network/no-merge statement are recorded in `evidence/PLAN-002/reviews/rework-report-20260810.md`.
