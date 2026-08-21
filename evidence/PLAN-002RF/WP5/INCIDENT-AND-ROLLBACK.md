# WP5 — Incident procedures and rollback rehearsal (Product B-AUTO, Local-only Part 1)

- Task: `t_dfa6f24f` (WP5 supported scans / shadow / security / rollback rehearsal).
- Scope: Option 1A (Moshe 2026-08-19) — honest reduced scope. Routes remain **off**.
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`.

This document records the incident/rollback procedures that WP5 is required to
*rehearse locally*. It drafts the runbook and records what was actually rehearsed
against the current (route-off, additive-only) tree, without claiming any
production activation.

## 1. Severity classification (packet §10, line 170)

| SEV | Meaning | Examples |
|---|---|---|
| SEV-1 | path/external access, disclosure, finalized-artifact mutation, unkillable process | reparse/symlink escape, leaked absolute path, `os.replace` leaving a half-finalized run, worker spawn that survives timeout |
| SEV-2 | nondeterminism, contract/G1 misrouting, resource-control bypass, critical false opening | two runs differ; a wall/room routed to the wrong source class; a cap bypassed; a false opening changes connectivity |
| SEV-3 | bounded malformed-input/performance defect without integrity impact | a legal-looking input fails with a mapped finding instead of a clean refusal |

## 2. Rollback procedure (packet §10, line 168)

Rollback is unidirectional and never relabels evidence, weakens a gate, retries
in-run, or routes to human correction. Order:

1. **Disable the named route** — currently a no-op: no `cad_exact`/`raster_auto`
   route is activated (default-off). The disabling surface is the absence of a
   route enabling flag; nothing in `src/pwa` activates either route.
2. **Stop new runs** — reject new parse-run dispatch for the affected route.
3. **Kill/verify workers** — `_kill_process_tree` (dxf_source) uses OS
   `taskkill /T /F` on Windows / `killpg(SIGKILL)` on POSIX so a worker's
   children cannot survive; verified by
   `test_dxf_worker_timeout_kills_the_process_tree_not_just_the_child`.
4. **Preserve finalized immutable history** — `finalize_run` atomically
   `os.replace`s staging→final and, on a failed post-finalization verify,
   attempts `os.replace(final→staging)`; a failure there raises
   `FinalizedRunLeftBehindError` (run-builder). History is never rewritten.
5. **Quarantine bounded staging/logs** — staging dirs are `tempfile`
   TemporaryDirectory; logs are capped to `MAX_WORKER_STDIO_BYTES`.
6. **Reproduce on sanitized data, then revert code or deprecate additive
   versions** without deletion.
7. **Rerun baseline + adversarial + migration + determinism checks**, then
   require fresh independent review + Moshe's applicable gate before re-enable.

## 3. Rollback rehearsal performed (this WP)

The following were exercised locally and recorded with test/exit evidence:

| # | Rehearsal | Mechanism | Evidence |
|---|---|---|---|
| R1 | route-off by construction | grep for activation surfaces; no enable flag exists | `src/pwa` has no route-enable path |
| R2 | atomic finalization + rollback on verify failure | `runs.finalize_run` `os.replace` + `FinalizedRunLeftBehindError` | `test_write_bytes_contained_is_exclusive_and_fsynced`, `tests/integration/test_plan002_parse_run.py::test_post_finalization_rollback_failure_reports_finalized_directory_left_behind` |
| R3 | process-tree kill | `_kill_process_tree` `taskkill /T /F` | `tests/unit/test_floorplan_sources.py::test_dxf_worker_timeout_kills_the_process_tree_not_just_the_child` |
| R4 | containment/reparse rejection | `runs.validate_contained_destination` + `resolve_contained_run` | `test_wp5_hardening.py` C-section |
| R5 | lineage invalidation without mutation | `recognition.supersede` returns a new head, old is immutable | `test_wp5_hardening.py` E-section |
| R6 | degradation refusal is deterministic | synthesized blur/noise/contrast adversaries | `test_wp5_hardening.py` A-section |

A genuine *route* rollback rehearsal (disable a live route, restore baseline,
re-run migration checks) is **NOT_EVALUABLE** for the same reason as the route
itself: no route is activated, so there is nothing to disable. The procedure is
drafted and its building blocks (R1–R6) are rehearsed; the end-to-end route
rollback is exercised at WP6 activation, never here.

## 4. Incident response owners and gates (unchanged from packet)

- SEV-1: immediate stop; Moshe notified; no auto-recovery.
- SEV-2: bounded rework (≤3 attempts), then block for human input.
- SEV-3: mapped-finding fix; no severity change without an ADR.

No gate here weakens a threshold or substitutes a human decision.
