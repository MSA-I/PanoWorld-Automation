# Orchestrator verification of NA-3g (PLAN-002, fifth bounded rework)

Subject: branch `panoworld-dev/na-3g-residues`, cut from the NA-3e head at `1946815`.
Implementer report: `evidence/PLAN-002/reviews/rework5-report-20260811.md`.
Dispatch: `evidence/PLAN-002/reviews/na3g-rework5-dispatch-20260811.md`.
Date: 2026-08-11. Author: orchestrator (Anthropic `claude-opus-5[1m]`, EXTRA).

The report was not accepted as evidence. Everything below was executed or read here.

## Executed

| Check | Result |
|---|---|
| Full suite, repository `.venv`, cleared `PYTHONPATH` | **356 passed, exit 0** (dot count confirmed independently of the summary line); dispatched baseline 351, so five tests added |
| Containment verifier, 17 checks, cross-drive root via `subst` | **17/17**, unchanged from NA-3e. Fix 3 rewired the read side, so this had to be re-run: every escape still rejected and every legitimate path still accepted |
| F-1 probe (out-of-tree, reuses the repository fixtures) | **passes** — `final_run` absent, staging retained, `cli_exit` 2 |
| Cross-adapter harness re-run | canonical projection **unchanged** at `sha256:05e6ce8218d11d09fb5f64181441ef1868e0bba2b18f21f55fb0c89d84ac36c6`, both adapters still identical, overlay byte counts identical (10,479 and 234,276), room areas identical |
| `git diff --stat main -- pyproject.toml uv.lock schemas contracts docs` | empty |
| `git diff --stat main -- src/pwa/floorplan/config.py tests/golden` | empty, so no new `limits_snapshot()` key and no edited golden expectation |
| `_APPROVED_ANNOTATION_IMAGE_KINDS` | `{"floorplan"}`, untouched |
| `git diff --check` | exit 0 |

The cross-adapter re-run matters more than it looks: fix 2 changed how the annotation raster is
read, which is the code path that feeds the overlay's embedded pixels and the `source_sha256`. If
that fix had perturbed the bytes by even one byte the projection hash would have moved. It did not.

## Read-through

- **Fix 2** is the same shape as F-6: `stream.read(MAX_SOURCE_RASTER_BYTES + 1)` and overflow onto
  the existing `PARSE_RESOURCE_LIMIT`, with no new limit key and no new error code. The single
  snapshot F-2 established is preserved — one read still supplies the digest, the dimension decode
  and the embedded bytes.
- **Fix 3** replaces `resolve_contained_relpath`'s private component check with `_contained_parts`
  and keeps the lexical ancestor walk and the independent `resolve()` / `relative_to()` proof. One
  function now defines a legal component for both sides, which is exactly what the reviewer asked
  for, and the verifier proves it did not narrow what the parser can actually resolve.
- **Fix 1** puts the double-fault signal in a new top-level `residual_state` diagnostic field,
  returns `overlay_omitted_reason` to overlay vocabulary only, and prints the diagnostic to stderr
  from `src/pwa/floorplan/cli.py` so a double fault is no longer invisible to an operator. The
  retained staging report is replaced by writing an exclusively-created
  `parse/parse-report.operational-failure.tmp` sibling and `os.replace`-ing it over the stale
  report. That is a deliberate overwrite of an exclusively-created artifact, which the dispatch
  required be justified rather than done silently, and the justification holds: the file being
  replaced is a claim that is no longer true, it lives in staging and not in a published run, and
  the replacement itself is atomic.

## One observation, for the reviewer rather than resolved here

**W-1 (minor).** The replacement sibling is created in exclusive mode. If a previous double fault
left `parse/parse-report.operational-failure.tmp` behind — which the implementer's own report says
happens when the atomic replacement fails — a second double fault's exclusive create raises
`FileExistsError`, which the surrounding `except (OSError, ValueError): pass` swallows, and the
stale `complete` report survives in staging. The returned diagnostic is still accurate and
`parse_run()` still does not raise, so the blast radius is a misleading file inside a retained
staging directory after two independent filesystem failures. Recorded rather than fixed: the
obvious remedies are to unlink a stale sibling first or to use a unique name, and both are the
reviewer's call now that a fifth round's residue would otherwise become a sixth round.

## Routed, not applied

The implementer correctly did **not** edit
`evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md`, which is an approved
append-only design record, and instead reported what the vocabulary amendment must say:
`overlay_omitted_reason` stays limited to `no_normalized_geometry`,
`overlay_exceeds_max_bytes` and `source_raster_exceeds_limits`; residual filesystem state is
recorded top level as `residual_state: "finalized_directory_left_behind"` and emitted by the CLI on
exit 2; and after a successful rollback the retained staging report is replaced because its
`complete` claim is no longer true. That amendment is now the orchestrator's to route.

## An orchestrator error to record

I switched the shared checkout to `main` and merged NA-3e while this implementer was still writing
to the same working tree. No damage resulted — the merged `main` tree and the NA-3g branch tree
were byte-identical for `src/` and `tests/`, so the in-flight edits carried across cleanly, and the
implementer correctly left them alone and flagged the situation in its report instead of trying to
fix it with git. One pytest run of mine raced the implementer's writes and exited non-zero for that
reason and was re-run afterwards. The lesson is simple and mine: do not change HEAD in a checkout
that a background implementer is writing to.
