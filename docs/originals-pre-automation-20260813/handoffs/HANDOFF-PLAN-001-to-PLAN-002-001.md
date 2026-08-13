# HANDOFF

- Handoff ID: `HANDOFF-PLAN-001-to-PLAN-002-001`
- Producer: PLAN-001 Intake and Packager Baseline
- Producer status: `VERIFIED` pending orchestrator-only local merge
- Consumer: P1-02 Floorplan Parsing planning lifecycle
- Date: 2026-08-09
- Contract version: bundle 1.0.0 unchanged

## Stable producer artifacts

1. Immutable local intake for PNG/JPG/PDF/DXF/DWG-header inputs with SHA-256 originals.
2. Schema-valid `project_manifest`, `input_quality_report`, and `panoworld_manifest` artifacts.
3. Tiny/golden fixture packaging, deterministic inventory hash, retained map insertion order, and validator wrapper.
4. Real Windows junction/reparse detection coverage and explicit pre-verify 100-megapixel image cap.
5. Fresh evidence: `evidence/PLAN-001/test-results/RUN-20260809-070251-128119/` — 122/122 passing.
6. Independent Anthropic review and closure report under `evidence/PLAN-001/`.

## Consumer boundaries

- Do not modify the PLAN-001 contracts bundle or intake semantics without a new approved PLAN and versioning analysis.
- Start P1-02 with a bounded Floorplan Parsing PLAN covering contracts, fixtures/datasets, security, acceptance, tests, and rollback.
- Block for Moshe approval after planning and before implementation.
- Route spatial design to Anthropic Opus 5 and implementation/tests to exact approved OpenAI Codex, with cross-provider review.
- Part 1 remains local-only. H200/GPU/remote and G7/G8 are **DEFERRED TO PART 2**.

## Verification

```bash
env -u PYTHONPATH ./.venv/Scripts/python.exe tools/run_checks.py --plan-id PLAN-001
# 122 passed

env -u PYTHONPATH ./.venv/Scripts/python.exe tools/verify_fixture_roundtrip.py
# 17/17 byte-identical

env -u PYTHONPATH ./.venv/Scripts/python.exe tools/validate_package.py tests/golden/panoworld_demo_subset --json
# 0 errors, 0 warnings
```

## Open blockers

None for PLAN-001. Floorplan Parsing implementation remains unapproved and must not begin until its new PLAN receives Moshe's explicit approval.
