You are the bounded OpenAI Codex implementer for approved PLAN-002 in this worktree. Work to completion in this one invocation. Use strict test-driven development: for each vertical slice, add a focused failing test, execute it and confirm the expected failure, implement the minimum production code, then execute the focused test and relevant regression tests. Do not commit, merge, push, install, sync dependencies, access the network, or touch any H200/GPU/cloud/remote infrastructure. G7/G8 are DEFERRED TO PART 2.

Authoritative inputs:
- docs/plans/PLAN-002-floorplan-parsing.md
- evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md (canonical approved implementation specification, including exact modules, schemas, algorithms, fixtures, failure matrix, TDD slices, and AC-1..AC-23 traceability)
- ADR-0004 and ADR-0005

Implement the approved local floorplan parser and only minimum Part 1 integration. Preserve the pre-existing modified canonical design artifact; it is an upstream approved change and must not be reverted. Add exact-version schema catalog support, floorplan_annotation 1.0.0, floorplan_parse 1.1.0, parser modules, normalized frozen types, deterministic findings/errors, annotation and bounded DXF adapters, normalization, validation, secure deterministic overlays, immutable derived-run lifecycle, CLI/shim, approved local fixtures, tests, and reproducible PLAN-002 evidence. Follow the design exactly; do not invent adjacency fields or new contracts. Ensure the source files and tests cover the acceptance matrix at a review-ready level. Run fresh local verification using the existing environment only (python -m pytest and git diff --check; pyproject.toml and uv.lock must remain unchanged). Retain commands, JUnit/coverage/test summary, determinism hashes, overlays, failure matrix, environment/routing metadata, and acceptance evidence in canonical evidence/PLAN-002 paths.

Routing metadata to record, with no silent fallback:
PROVIDER=openai
REQUESTED_MODEL=gpt-5.4
ACTUAL_MODEL_ID must be read from the Codex runtime/event metadata, not self-described
EFFORT=high
FALLBACK=none (if unavailable/auth/quota error, stop and report exact blocker)
MODEL_REASON=approved bounded Codex implementation of contract-sensitive deterministic geometry/parser code
REVIEWER_MODEL=claude-opus-5
CROSS_PROVIDER_REVIEW=required, pending separate reviewer task

If you discover any contract ambiguity, critical geometry decision not already fixed by the approved documents, unavailable capability, quota/auth failure, or need for a dependency/install/network action, stop without guessing and report the exact next action. Otherwise continue until implementation and fresh tests are complete. Do not claim human Visual/Geometry approval: the first implementation-generated Layer A overlay remains a fail-closed human gate. At the end report changed files, exact tests and results, evidence paths, actual model/runtime metadata if available, and any retained gates.