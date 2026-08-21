# RUN REPORT — PLAN-002RF WP5 (t_dfa6f24f) — Supported scans / shadow / security / rollback rehearsal

- Committing HEAD: `2d6df15` (baseline) + WP5 checkpoint commit (local only, no push).
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`.
- Authorization: Moshe **Option 1A** (2026-08-19) — honest reduced scope. Routes remain **off**.
- Model provenance: `deepseek/deepseek-v4-pro-0813` via `openrouter` (OmniRoute), recorded from
  the session runtime context, not self-identification prose. No Opus-level spatial routing was
  requested or observed — §5/AT-14 tolerance-matcher work is owned by blocked sibling card
  `t_d1a5436b`, not WP5.

## What was delivered (Option 1A locally-exercisable hardening)

1. **Degradation / refusal handling (A)** — synthesized blur/noise/contrast/scale adversaries over
   the frozen FX1 fixture. The engine must never crash, never hang, and be byte-deterministic
   across runs; low-contrast and missing/damaged-anchor scans fail closed (no geometry emitted).
2. **Renderer / font / CVD / legibility contracts (B)** — `src/pwa/floorplan/render_contracts.py`,
   pure deterministic checkers implementing the frozen packet §7 (line 118) thresholds: text
   ≥12 CSS px, legend ≥14 CSS px, text contrast ≥4.5:1, geometry contrast ≥3:1, and ≥3:1
   accepted-stroke contrast under Machado (2010) severity-1.0 protanopia/deuteranopia/tritanopia
   simulation. This is the *contract* layer only — the renderer itself is U-11 BLOCKED.
3. **Containment / reparse / path / atomic-finalization adversarial tests (C)** —
   `runs.validate_contained_destination` rejects `../` escape and reparse-point (junction/symlink)
   escape; `write_bytes_contained` is exclusive + fsynced; a reparse-point `runs_root` is refused
   before `resolve()` erases it; process-tree kill (`_kill_process_tree`) is re-verified by the
   existing `test_dxf_worker_timeout_kills_the_process_tree_not_just_the_child`.
4. **Resource controls (D)** — re-asserted `MAX_STRUCTURAL_INK_PIXELS` forces
   `PARSE_RESOURCE_LIMIT` with empty geometry.
5. **Lineage invalidation (E)** — `recognition.supersede` returns a new immutable head (old head
   never mutated); `append_review` rejects id-reuse (cycle) and absent-parent.
6. **Local shadow comparison (F)** — `tools/wp5_shadow_comparison.py`, a read-only harness over the
   60-fixture frozen corpus + FX1; proves replay-hash integrity and structural count convergence
   WITHOUT any yield/spatial claim.
7. **Incident procedures + rollback rehearsal** — `evidence/PLAN-002RF/WP5/INCIDENT-AND-ROLLBACK.md`
   drafts the SEV-1/2/3 runbook and records rehearsed building blocks R1–R6.

## Test results

- `tests/unit/test_wp5_hardening.py`: **15 passed** (TDD RED→GREEN; each behavior targeted a gap
  not proven by the WP4 suite).
- Full suite (excluding pre-existing `test_wp0_cpu_feasibility.py` collection error):
  **591 passed, 0 failed** (~118s).
- Shadow comparison (`tools/wp5_shadow_comparison.py`): replay hashes **intact** (True),
  structural wall-count convergence **60/60**; room 41/60; opening 36/60; FX1 **9 walls / 3 rooms /
  6 openings** recovered with zero errors. This is structural convergence only, NOT a spatial or
  yield claim.

## Pre-existing gap closed (minimal, contract-hygiene only)

The code at HEAD already emits `RECOGNITION_OPENING_SPAN_EXCEEDS_BOUND`
(`src/pwa/floorplan/recognition.py:36`), but the append-only vocabulary in
`contracts/error_codes.md` had never been updated, so `test_wp2_error_code_vocabulary_contains_new_codes_append_only`
failed at clean HEAD. Added the single missing table row (append-only, no ranking change). This is
a WP4 documentation gap, closed here so the suite is green; it is not a WP5 scope expansion.

## Honest acceptance status (fail-closed, no fabrication)

### MET (locally-exercisable hardening)
Degradation/refusal determinism, renderer/font/CVD contract *checkers*, containment/reparse/path/
atomic-finalization adverse tests, resource-cap coverage, lineage-invalidation immutability,
read-only local shadow comparison, incident/rollback procedure draft + rehearsed building blocks.

### NOT_EVALUABLE / BLOCKED (reported with exact rationale — never fabricated)

- **AT-08 (≥22/25 supported-scan emits): NOT_EVALUABLE.** The R1 (10 light) + R2 (15 heavy)
  degradation strata do not exist anywhere in the tree; the only raster corpus is the 60-fixture
  *synthetic clean* R0 set + FX1. Authoring an R1/R2 corpus would require rights clearance
  (U-7), a fixed symbol/style guide (U-5), and two blind labelers + an independent adjudicator
  (U-6/AT-21) — all human-gated/BLOCKED. No yield claim is made.
- **§5/AT-14 spatial tolerance matcher: NOT_EVALUABLE (owned elsewhere).** Assigned to blocked
  sibling card `t_d1a5436b` (WP4-TOL); not WP5's scope.
- **Loopback UI security / CSRF / Host-Origin: NOT_APPLICABLE.** No loopback UI or HTTP server
  exists in the codebase (grep for flask/fastapi/socket/listen/127.0.0.1 = SVG generators only);
  there is no component to harden in Part 1's local CLI/SVG pipeline.
- **Delegated QA of "all frozen outputs": NOT_EVALUABLE.** No pre-named QA delegate ≠ labeler ≠
  adjudicator (U-6 BLOCKED). No production-renderer frozen outputs exist.
- **Renderer/font/CVD *execution*: NOT_EVALUABLE.** U-11 (pinned renderer/font + normalized-pixel
  contract) BLOCKED. Only the deterministic checkers were built.
- **End-to-end route rollback rehearsal: NOT_EVALUABLE (building blocks only).** No route is
  activated (default-off), so there is nothing to disable. R1–R6 building blocks rehearsed; the
  full route rollback is exercised at WP6 route activation, never here.

## Hard boundaries honored

No dependency install; no network/model call in the engine; no H200/GPU/cloud/remote; no spend;
no G7/G8/Product C/PLAN-003; no route activation (default-off); no push/merge-to-remote (local
commit only); no fabricated truth/threshold/yield/spatial matcher; no manual rescue or per-plan
tuning. WP5 completion does NOT authorize WP6 — that card remains a human needs_input gate.
