# RUN REPORT — PLAN-001 Closeout

- RUN_ID: `PLAN-001-CLOSEOUT-20260809`
- Project ID: `panoworld-automation`
- PLAN_ID: `PLAN-001-intake-and-packager-baseline`
- Started: `2026-08-09T09:04:00+03:00`
- Finished: `2026-08-09T10:04:02+03:00`
- Status: `VERIFIED`

## Mandatory agent update

```text
PLAN_ID: PLAN-001-intake-and-packager-baseline
STATUS: VERIFIED
PROVIDER: OpenAI
MODEL_ID_EXACT: gpt-5.6-sol
EFFORT: HIGH normalized / high provider value
OWNERSHIP: Independent-review triage, bounded M-3/M-4 rework, deterministic verification, closeout state and handoff
COMPLETED: M-1 ratified; M-2 standalone report created; M-3 real Windows junction coverage added; M-4 image cap moved before verify; fresh gates passed
EVIDENCE: evidence/PLAN-001/reviews/independent-anthropic-review-20260809.md; evidence/PLAN-001/test-results/RUN-20260809-070251-128119/
FILES_CHANGED: src/pwa/intake.py; tests/integration/test_plan001_intake.py; PLAN-001 closeout docs/evidence
TESTS_RUN: 122
TEST_RESULT: 122 passed, 0 failures, 0 errors, 0 skipped
BLOCKERS: N/A
RISKS: PDFium/ezdxf remain in-process; Pillow is now explicitly capped before verify; G7/G8 deferred to Part 2
NEXT_ACTION: orchestrator-only fast-forward merge to local main, post-merge sanity, then allow P1-02 planning only
COMMIT: 87f00db17df8091f0becf431f3e8c2190b7855e4
```

## Agent model execution

- PROVIDER: `OpenAI`
- REQUESTED_MODEL: `gpt-5.6-sol`
- ACTUAL_MODEL_ID: `gpt-5.6-sol` (Codex canonical `turn_context`)
- EFFORT: normalized `HIGH`; provider value `high`
- FALLBACK: `no`
- MODEL_REASON: bounded Python security/test rework for deterministic local intake
- AUTHOR_MODEL: historical PLAN-001 implementation used OpenAI Codex; exact original harness model was not exposed
- REVIEWER_MODEL: `claude-sonnet-5`, Anthropic Sonnet 5 / HIGH
- CROSS_PROVIDER_REVIEW: `yes`
- Codex CLI/session: `0.144.6` / `019fe54f-eb34-7293-82fc-b21f530b414f`
- Token/cost/runtime: 890,936 input tokens (830,720 cached), 8,738 output, 4,816 reasoning; cost not exposed; about 4 minutes

## Scope and finding closure

- M-1: explicitly ratified. Commit `3baedba` is retained because Moshe approved the Part 1 Kanban campaign and the kickoff baseline made that orchestration setup canonical. It is documentation/state-only and does not widen PLAN-001 runtime behavior.
- M-2: closed by this standalone report in the mandatory docs/04 format.
- M-3: closed by a Windows-only privilege-free `mklink /J` regression that proves the real `FILE_ATTRIBUTE_REPARSE_POINT` branch is detected without monkeypatching.
- M-4: closed by checking extension/format and header dimensions against `MAX_IMAGE_PIXELS` before invoking Pillow `verify()`; regression proves `verify()` is not called above the cap.
- No Floorplan Parsing, Blender, PanoWorld execution, H200/GPU, remote, cloud, install, push, or spend occurred. G7/G8 are **DEFERRED TO PART 2**.

## Commands and results

```bash
env -u PYTHONPATH ./.venv/Scripts/python.exe -m pytest tests/integration/test_plan001_intake.py -q --basetemp ./.venv/.pytest-tmp-hermes-targeted
# 9 passed

env -u PYTHONPATH TMP="$PWD/.venv/tmp" TEMP="$PWD/.venv/tmp" PYTEST_ADDOPTS='--basetemp=./.venv/.pytest-tmp-plan001-fresh' ./.venv/Scripts/python.exe tools/run_checks.py --plan-id PLAN-001
# RUN-20260809-070251-128119: 122 passed, 0 failed/errors/skipped

env -u PYTHONPATH ./.venv/Scripts/python.exe tools/verify_fixture_roundtrip.py
# 17/17 byte-identical

env -u PYTHONPATH ./.venv/Scripts/python.exe tools/validate_package.py tests/golden/panoworld_demo_subset --json
# 0 errors, 0 warnings
git diff --check
# pass
```

The initial Codex probe and first targeted pytest attempt encountered local temp-directory permission errors under `D:\\tmp`; rerunning with a worktree-local `--basetemp` passed. This was an environment-path issue, not a product failure.

## Decision

`APPROVED` for orchestrator-only local merge after the closeout docs commit. All PLAN-001 acceptance gates and independent-review findings are closed.

## Next action

Fast-forward local `main`, run post-merge pytest sanity, then complete P1-01. P1-02 may create a bounded Floorplan Parsing plan but must block for Moshe approval before implementation.
