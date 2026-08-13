You are the independent opposite-provider reviewer for Kanban task t_b1633bf1. The primary drafting provider was OpenAI Codex gpt-5.6-sol. You must review only; do not edit any repository file, implement remediation, start PLAN-003, or authorize implementation.

First invoke Claude Code's /skills capability to discover and use the most relevant review/spatial/geometry skills. State which skills you selected.

Review this exact PLAN artifact and SHA-256:
- .hermes/plans/2026-08-11_171713-plan-002r-bounded-recognition-remediation.md
- 1c466214c1231cbc790cf534984eadf8762ec30022f21a6a69b64a69d9992562

Read relevant repository contracts/ADRs/plans as needed to verify claims rather than trusting the PLAN. Independently challenge whether the PLAN fully addresses:
- omitted angled/rotated/curved walls; missing and false-positive openings; centreline offset/overrun; overlapping IDs;
- manual annotation versus automatic recognition truth-in-labelling;
- product boundaries and geometry semantics;
- representative datasets, leakage, adjudication, and metric definitions;
- zero-critical-false-positive handling and statistical wording;
- topology and scale tolerances;
- overlay evidence and legibility;
- fail-closed behavior and human approval;
- adversarial tests;
- local security, privacy, resource limits, cancellation, rollback, schedule/cost realism, and contract/state migration.

Explicitly verify Local-only Part 1 excludes H200, GPU, cloud, remote execution, G7, G8, spending, implementation authorization, and PLAN-003 work.

Return a rigorous Markdown review report only (no edits). Include:
1. exact artifact path/hash reviewed;
2. provider = Anthropic, requested model = opus, actual model if exposed, effort/runtime metadata if exposed, fallback provider/model/reason (or none observed), and selected /skills;
3. verdict: either SIGNED OFF / READY FOR APPROVAL, or NOT READY;
4. numbered findings ordered by severity, each with PLAN line references, rationale, blocking status, and concrete recommended wording/edits;
5. an explicit coverage checklist for every challenge above;
6. explicit boundary confirmation (or violation);
7. approval decisions still required from Moshe;
8. a concise signature block identifying you as the independent Anthropic/Claude reviewer.

Do not soften a blocking defect into a suggestion. Do not claim implementation or test execution. If evidence is ambiguous or a claim cannot be verified, mark it as such.