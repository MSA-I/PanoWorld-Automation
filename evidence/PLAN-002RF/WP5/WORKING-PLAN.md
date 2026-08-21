# WP5 — WORKING PLAN (Option 1A honest reduced scope)

- Task: `t_dfa6f24f` (WP5 supported scans / shadow / security / rollback rehearsal).
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`.
- Authorization: Moshe Option 1A (2026-08-19) — harden ALL locally-exercisable items;
  report corpus/role-gated items NOT_EVALUABLE with exact rationale; never fabricate.
- Model: `deepseek/deepseek-v4-pro-0813` via `openrouter` (OmniRoute), recorded from
  runtime context. No Opus-level spatial work in scope (§5/AT-14 matcher is a blocked
  sibling card `t_d1a5436b`).

## Scope decision

WP5's headline acceptance (AT-08 ≥22/25 supported-scan emits) and several hardening
items are gated on human decisions or components that do not exist. Per Option 1A I
harden what is locally-exercisable and report the rest honestly.

### Locally-exercisable (DO)
1. Degradation/refusal handling — synthesized adversaries (blur/noise/contrast/skew/
   damaged anchors) must fail closed and deterministically.
2. Renderer/font/CVD/legibility contracts — pure deterministic checkers (contrast,
   font size, CVD simulation) as the measurable criteria a future pinned renderer
   must pass.
3. Containment/reparse/path/cancellation/process-tree/atomic-finalization adversarial
   tests over the existing `runs.py` + `dxf_source` layers.
4. Resource controls — re-assert the absolute ink-pixel cap.
5. Lineage invalidation — supersede immutability + append cycle/reuse rejection.
6. Local shadow comparison — read-only harness vs frozen corpus + FX1 (replay-hash
   integrity + structural convergence, NO yield/spatial claim).
7. Incident procedures + rollback rehearsal — drafted runbook + rehearsed building
   blocks (R1–R6).

### NOT_EVALUABLE / BLOCKED (report, do not fabricate)
- AT-08 (≥22/25) — R1/R2 degradation strata do not exist; prerequisites U-5/U-6/U-7
  human-gated.
- §5/AT-14 spatial tolerance matcher — owned by blocked sibling card `t_d1a5436b`.
- Loopback UI security / CSRF / Host/Origin — no loopback UI or HTTP server exists.
- Delegated QA of frozen outputs — no pre-named QA delegate (U-6).
- Renderer/font/CVD *execution* — U-11 (pinned renderer/font) BLOCKED; checkers only.
- End-to-end route rollback — no route activated (route is off); building blocks only.

## Deliverables
- `tests/unit/test_wp5_hardening.py` (15 tests, TDD)
- `src/pwa/floorplan/render_contracts.py` (pure legibility/CVD checkers)
- `tools/wp5_shadow_comparison.py` (read-only shadow harness)
- `evidence/PLAN-002RF/WP5/` (RUN-REPORT, HANDOFF, INCIDENT-AND-ROLLBACK, shadow/)
- Independent cross-provider read-only review (delegated)

## Hard boundaries (fail-closed)
No dependency install; no network/model call in engine; no H200/GPU/cloud/remote; no
spend; no G7/G8/Product C/PLAN-003; no route activation; no push/merge-to-remote
(local commit only); no fabricated truth/threshold/yield; no manual rescue.
