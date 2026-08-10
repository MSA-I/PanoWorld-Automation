Continue the same PLAN-002 task from the current worktree. The prior follow-up reached 167 passing tests but stopped during evidence regeneration. Do not merely regenerate evidence yet: perform a strict final gap audit against the approved design brief, especially sections 13 and 14.2.

Current verified state from supervisor:
- Full suite fresh currently passes 167 tests.
- Focused PLAN-002 suites now also pass after minimal tests/__init__.py package markers were added by the supervisor.
- The implementation is still NOT review-ready because the approved brief requires one executable row per §13 fixture and explicit AC-1..AC-23 traceability. Current tests/integration/test_plan002_failures.py has only 4 tests, several unit tests bundle many cases, tests/golden/test_floorplan_golden.py is absent, and parse-failure-matrix.json still contains only 4 old rows. Do not claim full compliance while these gaps remain.

Required bounded work:
1. Use strict TDD to close all feasible Part 1 §13/AC-1..AC-23 gaps. Add parametrized tests where appropriate so each approved fixture is an individually named executable case with exact code/severity/outcome/overlay/finalized/status/CLI assertions. Do not weaken or edit the approved design brief.
2. Add the named golden adapter-equality coverage (or an exactly equivalent test file/node IDs aligned with the brief), including canonical hash, adapter-specific confidence/units, stable IDs, overlay security/determinism, and all boundary fixtures.
3. Ensure production behavior actually supports every new test. Fix root causes only; no silent fallback, no dependency changes, no unrelated edits.
4. Regenerate evidence from actual executions: fresh unique full-suite JUnit/coverage/command log/summary, complete parse-failure-matrix with one row per §13 fixture, canonical parse/overlay/determinism artifacts, AC traceability, source pre/post hash evidence, and acceptance.md.
5. Record routing exactly: PROVIDER=openai (requested), REQUESTED_MODEL=gpt-5.4, ACTUAL_MODEL_ID=gpt-5.4, EFFORT=high, FALLBACK=none, MODEL_REASON=approved bounded implementation model, runtime provider from session metadata=model_provider=headroom, REVIEWER_MODEL=claude-opus-5, CROSS_PROVIDER_REVIEW=pending/required. Distinguish requested provider from runtime provider.
6. Keep G7/G8, H200/GPU, cloud/remote execution, network access, uploads, provisioning and spending DEFERRED TO PART 2. Do not perform them.
7. Use repository .venv Python 3.11 only. Do not modify pyproject.toml or uv.lock. Remove/avoid disposable .tmp evidence from the final working tree if safely possible, but do not delete unrelated user files.
8. Finish by running focused tests, full pytest with fresh unique basetemp and evidence, git diff --check, and git diff -- pyproject.toml uv.lock. Give an honest final report with any exact remaining gap.

If a genuinely new contract or critical geometry decision is required, stop and report the exact decision instead of guessing. Otherwise continue until review-ready.