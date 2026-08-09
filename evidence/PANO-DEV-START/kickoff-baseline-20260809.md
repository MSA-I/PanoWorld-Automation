# PANO-DEV-START — Kickoff Baseline

- Captured at: `2026-08-09T08:47:24+03:00`
- Scope: Part 1 local development only
- Kanban task: `t_4ddc34f3`
- Board: `panoworld-dev`
- Result: `VERIFIED`

## Scope lock

No H200/GPU/remote infrastructure was accessed, provisioned, configured, uploaded to, executed on, or charged. Gates G7/G8 remain **DEFERRED TO PART 2**.

## Git reconciliation

| Ref | Commit |
|---|---|
| `main` | `df24d5c7291bc1bc7a6c8ed81b12b24dad06c14a` |
| `plan/PLAN-001` | `3baedba7f172821860c6cd9e08fdc4d7a1b1a773` |
| kickoff worktree HEAD before this report | `3baedba7f172821860c6cd9e08fdc4d7a1b1a773` |

- `main` is an ancestor of `plan/PLAN-001`.
- `plan/PLAN-001` contains five commits beyond `main`: the approved PLAN, implementation, acceptance/handoff evidence, real DWG smoke closeout, and dormant Kanban setup.
- The kickoff worktree was clean before baseline recording.
- `git diff main...plan/PLAN-001 --check` passed.
- PLAN-001 remains `REVIEW`; it is not merged and no future-stage implementation has started.

## Canonical-state reconciliation

- `PROJECT-STATE.yaml` correctly points to `PLAN-001-intake-and-packager-baseline`, branch `plan/PLAN-001`, status `REVIEW`.
- `BLOCK-0001` is resolved by the redacted real local DWG smoke evidence.
- The next canonical actions remain independent PLAN-001 review, finding triage/rework if needed, fresh verification, state/handoff update, and orchestrator-only merge.
- The orchestration contract names `PanoWorld.md`; the repository's sole matching source is `PanoWorld-מדריך-והסבר.txt`. This report records that path resolution; no source content or scope was changed.

## Kanban graph verification

Read-only inspection of the board database and `kanban_show` confirmed:

- 13 tasks total: kickoff plus `P1-01` through `P1-12`.
- 12 dependency edges form one serial, acyclic chain.
- Before kickoff completion: 1 `running`, 12 `todo`, 0 unrelated `ready` tasks.
- Every task is assigned to the existing `default` profile and uses goal mode.
- `t_6d733451` is the only direct child of kickoff and is the next safe dispatch.
- All later stages remain dependency-gated behind PLAN-001 closeout.

## CLI/provider/model availability

### Kickoff orchestrator

- PROVIDER: `openai`
- REQUESTED_MODEL: `gpt-5.6-sol`
- ACTUAL_MODEL_ID: `gpt-5.6-sol`
- EFFORT: normalized `EXTRA`; provider value not exposed by the Hermes worker
- FALLBACK: `no`
- MODEL_REASON: system reasoning, repository reconciliation, and deterministic verification
- REVIEWER_MODEL: `claude-sonnet-5` requested for PLAN-001 closeout
- CROSS_PROVIDER_REVIEW: available and required for PLAN-001 closeout

### Claude Code probe

- CLI: Claude Code `2.1.222`
- PROVIDER: `anthropic`
- REQUESTED_MODEL: `sonnet`
- ACTUAL_MODEL_ID: `claude-sonnet-5`
- EFFORT: bounded availability probe; session effort not exposed
- FALLBACK: `no`
- Result: `CLAUDE_AVAILABLE`
- Prompt explicitly instructed Claude to use `/skills`; plan permissions were used and no files were modified.

### Codex probe

- CLI: `codex-cli 0.144.6`
- PROVIDER: `openai`
- REQUESTED_MODEL: configured `gpt-5.6-sol`
- ACTUAL_MODEL_ID: `gpt-5.6-sol` (locked in Codex config; exec event did not repeat the model ID)
- EFFORT: provider `xhigh`, normalized `EXTRA`
- FALLBACK: `no`
- Result: `CODEX_AVAILABLE`
- Probe used ephemeral, read-only mode and did not modify repository files.
- Non-blocking environment warnings: stale model-cache schema plus three malformed global skill manifests; the session still completed successfully. Codex also reported that its model-visible skill list exceeded the 2% context budget, so bounded prompts must name only necessary skills.

## Fresh local verification

| Check | Result |
|---|---|
| `env -u PYTHONPATH uv run python -m pytest -q` | PASS — 120 tests |
| `uv run python tools/verify_fixture_roundtrip.py` | PASS — 17/17 byte-identical |
| `uv run python tools/validate_package.py tests/golden/panoworld_demo_subset --json` | PASS — 0 errors, 0 warnings |
| `git diff main...plan/PLAN-001 --check` | PASS |

The first unsanitized pytest invocation failed during collection because the Hermes worker inherited `PYTHONPATH` pointing at the Hermes Agent repository, causing `tests.conftest` to resolve to Hermes instead of this project. This is an execution-environment collision, not a PanoWorld test failure. Clearing `PYTHONPATH` produced the clean 120-test pass. Downstream Hermes workers must use `env -u PYTHONPATH` for Python/pytest commands in this repository.

## Next safe action

Complete this kickoff gate so dependency promotion makes `t_6d733451` ready. That card must independently review `main...plan/PLAN-001` with Anthropic Sonnet 5 HIGH, route any rework to OpenAI Codex/GPT-5.6, rerun verification with `PYTHONPATH` cleared, update canonical state/evidence/handoff, and merge only after all acceptance gates pass. It must not begin Floorplan Parsing.
