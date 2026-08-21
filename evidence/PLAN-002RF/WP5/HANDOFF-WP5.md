# HANDOFF — WP5 (Product B-AUTO hardening, Option 1A) → next WP

- Task: `t_dfa6f24f` (WP5 supported scans / shadow / security / rollback rehearsal) — honest
  reduced-scope closeout.
- Committing HEAD: `2d6df15` + WP5 checkpoint commit (local only, no push).
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`.
- Successor: WP6 `t_a67d5f86` remains a **human needs_input gate** — WP5 completion does NOT
  authorize WP6, and WP6 is decision-packet-only (no route activation).

## What was delivered (Option 1A — harden what is locally-exercisable)

- **Degradation/refusal handling**: synthesized blur/noise/contrast/scale adversaries fail closed
  and deterministically; low-contrast and damaged/missing-anchor scans refuse with no geometry.
- **Renderer/font/CVD/legibility contracts**: `src/pwa/floorplan/render_contracts.py` — pure
  deterministic checkers for the frozen packet §7 thresholds (text ≥12 CSS px, legend ≥14, text
  contrast ≥4.5:1, geometry ≥3:1, CVD severity-1.0 simulation). Contract layer only.
- **Containment/reparse/path/atomic-finalization/cancellation/process-tree**: adversarial tests over
  `runs.py` + `dxf_source`; escape/reparse-point/junction refusal; exclusive+fsynced writes;
  process-tree kill re-verified.
- **Resource controls**: `MAX_STRUCTURAL_INK_PIXELS` cap re-asserted (`PARSE_RESOURCE_LIMIT`).
- **Lineage invalidation**: `recognition.supersede` immutability + `append_review` cycle/reuse
  rejection.
- **Local shadow comparison**: `tools/wp5_shadow_comparison.py` — read-only harness proving replay
  -hash integrity and structural count convergence (no yield/spatial claim). 60/60 wall-count
  convergence; FX1 9/3/6 fully recovered.
- **Incident procedures + rollback rehearsal**: `evidence/PLAN-002RF/WP5/INCIDENT-AND-ROLLBACK.md`
  (SEV-1/2/3 runbook + rehearsed building blocks R1–R6).
- **Tests**: `tests/unit/test_wp5_hardening.py` 15 passed; full suite 591 passed (excluding the
  pre-existing `test_wp0_cpu_feasibility.py` collection error — see note below).

## What is explicitly NOT_EVALUABLE (do NOT treat as done)

1. **AT-08 (≥22/25 supported-scan emits)** — R1/R2 degradation strata do not exist; prerequisites
   U-5/U-6/U-7 human-gated. No yield claim made.
2. **§5/AT-14 spatial tolerance matcher** — owned by blocked sibling `t_d1a5436b` (WP4-TOL).
3. **Loopback UI security / CSRF / Host-Origin** — no loopback UI/HTTP server exists (N/A).
4. **Delegated QA of frozen outputs** — no QA delegate named (U-6).
5. **Renderer/font/CVD execution** — U-11 BLOCKED; only checkers delivered.
6. **End-to-end route rollback** — no route activated; building blocks only.

## Critical notes for the successor

- The exact-by-key `match_wall` in `src/pwa/evaluator/metrics.py` remains a frozen sanity matcher,
  NOT the §5/AT-14 spatial matcher. Do not treat it as the acceptance scorer.
- Review findings #9/#10/#11/#12/#13 are **open on sibling cards**, not WP5: `t_32c47e7d` (WP4-FIX)
  and `t_d1a5436b` (WP4-TOL), both `spawn_failed ×3` (their `workspace_kind=worktree` but
  `workspace_path` points at the main repo, not a valid worktree root). `t_f7a9ca90` (WP4-REVIEW)
  depends on both. WP5's "no unresolved critical/major review finding" gate transitively depends on
  these, so it is NOT independently satisfiable from WP5 alone.
- A **stash and a saved diff** preserve scoped-out work that belongs to WP4-FIX, not WP5:
  - `git stash@{0}` — "WP4-FIX orphan uncommitted work (review #10/#11/#12/#13)…" (uses
    `M.project_truth_wall`/`M.project_prediction_wall` API).
  - `/tmp/wp5-scope-creep-wp4fix-2nd-implementation.diff` — a second, divergent WP4-FIX
    implementation (`M.project_wall_geometry` API) left in the working tree by a crashed run and
    reverted here; saved so nothing is lost.
  These two are NOT committed in the WP5 tree. WP4-FIX's worker must reconcile which one (if
  either) is authoritative.
- **Pre-existing collection error** (not WP5): `tests/unit/test_wp0_cpu_feasibility.py` fails
  import (`No module named 'tools.wp0_cpu_feasibility'`) because the Hermes CLI's own
  `hermes-agent/tools/__init__.py` shadows the repo's `tools/` namespace package on `sys.path`.
  It is independent of any WP change; excluded from the passing count here.

## What the successor must NOT do

- Do not claim AT-08, §5/AT-14, or any yield/spatial metric as met.
- Do not weaken thresholds, fabricate an R1/R2 corpus, or name labelers/adjudicators without Moshe.
- Do not activate any route (WP6 is decision-packet-only; routes remain off).
- Do not merge/push to remote — WP5 is a local-only checkpoint.

## Files

- `src/pwa/floorplan/render_contracts.py` (new)
- `tests/unit/test_wp5_hardening.py` (new, 15 tests)
- `tools/wp5_shadow_comparison.py` (new)
- `contracts/error_codes.md` (+1 missing recognition code row, append-only)
- `evidence/PLAN-002RF/WP5/{WORKING-PLAN,RUN-REPORT,INCIDENT-AND-ROLLBACK}.md`,
  `shadow/{shadow-report.json,SHADOW-REPORT.md}`
