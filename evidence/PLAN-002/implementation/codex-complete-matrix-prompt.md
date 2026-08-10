Continue immediately. Do NOT stop at a partial matrix. The task acceptance criteria require review-ready implementation and the current evidence honestly says it is not review-ready. No new contract/geometry decision is needed: every expected row is already locked in approved brief §13.

Close every remaining_fixture_rows entry currently listed in evidence/PLAN-002/failures/parse-failure-matrix.json. Use parametrized tests to keep this bounded, but ensure pytest emits one distinct executable node ID per approved fixture and asserts the exact §13 code, severity, outcome, overlay rule, finalized set/status and CLI where applicable. Unit-only constructed rows are allowed only where the approved brief explicitly says they are unreachable from Part 1 sources (for example f-low-confidence); all other rows need the appropriate adapter/integration coverage required by §14.2.

Required procedure:
1. Read the current missing_fixture_rows list and §13 tables.
2. Add tests first and observe RED for each grouped slice.
3. Implement only root-cause changes needed to make all rows green. Do not edit the approved design brief, dependencies, contracts beyond already-approved semantics, or unrelated files.
4. Regenerate parse-failure-matrix.json from actual executed cases so coverage_status becomes complete and missing_fixture_rows becomes empty. Fix the incorrect f-existing-final evidence semantics: pre-existing final directory is not a newly finalized derived run; record finalized set according to the approved row.
5. Regenerate fresh unique full-suite JUnit/coverage/summary, acceptance.md and ac-traceability.md. Review readiness may be true only if all AC-1..AC-23 are evidenced. Keep visual/geometry human gate and cross-provider review pending; those are downstream gates, not implementation incompleteness.
6. Run focused §13 tests, full pytest, git diff --check, and dependency diff. No .tmp cleanup is required if policy blocks it; simply do not include .tmp as canonical evidence.

Do not return another progress-only or partial result. If and only if a specific approved row is technically impossible without a NEW unapproved semantic decision, stop and name that exact row and exact decision. Otherwise finish all rows.