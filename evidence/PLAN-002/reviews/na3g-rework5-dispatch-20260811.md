<!-- NA-3g dispatch brief: fifth bounded rework, the three residues the NA-3f reviewer named as
     work items. Authored by the orchestrator. Repository-relative paths only (section 12). -->

# NA-3g — fifth bounded rework: the three residues NA-3f named

You are the PLAN-002 rework implementer, continuing on a fresh branch. Three bounded fixes, no
more. The NA-3f review returned **ACCEPT** on the previous round; nothing here re-opens a gate.
These are the residues that review explicitly listed as follow-up work items.

Read first:

1. `evidence/PLAN-002/reviews/independent-anthropic-rework4-review-20260811.md` — the ACCEPT
   review. Its "what should happen next" list is items 1, 2 and 5 below, in its own words.
2. `evidence/PLAN-002/reviews/orchestrator-verification-na3e-20260810.md` — V-2, V-3 and V-4,
   which are the same three residues seen from the orchestrator's side.

## Fix 1 — report a left-behind finalized directory properly (V-3 + V-4)

Today, when a post-rename verification fails **and** the rollback also fails, the residual state
is signalled by setting `overlay_omitted_reason` to `"finalized_directory_left_behind"`. That field
exists to say why an overlay was omitted; using it to report a filesystem rollback failure is a
semantic overload, and a consumer reading it is misled about what kind of thing went wrong.

The previous brief forbade new contract surface, which is why the implementer had no better
option. **The reviewer's ruling is that this boundary is the thing that should give**, and it also
established the fact that makes it cheap: `parse/parse-report.json` **has no schema**, so a new
diagnostic field there is not schema surface.

Required:

- Give the diagnostic a distinct field or `outcome` value that says a finalized directory was left
  behind. Do not keep smuggling it through `overlay_omitted_reason`; restore that field to
  reporting overlay omission only.
- Surface it through `src/pwa/floorplan/cli.py` rather than discarding it. Today the only record of
  a double fault dies with the process.
- V-4, the same failure's other half: after a **successful** rollback, staging retains the
  happy-path `parse/parse-report.json` saying `"outcome": "complete"`, because
  `_staged_operational_result` skips writing its failure report when one already exists at that
  path. Fix that too, in whatever way you can defend: the retained staging directory must not
  claim success for a run that failed. Do not overwrite an exclusively-created artifact silently -
  if you add a second file, say why in your report.
- `contracts/error_codes.md` must remain unchanged; no new error-code token. Schemas under
  `schemas/` must remain unchanged. `limits_snapshot()` must gain no key.
- The reviewer also names a vocabulary amendment at
  `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md:585`. **Do not edit that
  file** - everything under `evidence/` is append-only and it is an approved design record. Report
  what the amendment would need to say and the orchestrator will route it.

## Fix 2 — bound the raster read (V-2)

`src/pwa/floorplan/annotation_source.py` reads the whole staged raster with `read_bytes()`, and
`MAX_SOURCE_RASTER_BYTES` is only enforced later, at `src/pwa/floorplan/overlay.py:110`. So the cap
does not bound the read it names, and `MemoryError` - which is not in the handler tuple - stays
reachable. This is the exact shape of F-6, which was fixed for the annotation JSON in the previous
round and not for the raster.

Required: read at most `MAX_SOURCE_RASTER_BYTES + 1` bytes and map the overflow to the existing
`PARSE_RESOURCE_LIMIT`. No new limit key, no new error code. Keep the single-snapshot property F-2
established - one read, one digest, the same bytes for dimensions and for embedding.

## Fix 3 — apply the component grammar on the read side too (reviewer item 5)

`_contained_parts` is applied on the write side. `resolve_contained_relpath` does its own
validation and does not call it, so the two sides disagree about what a legal component is. The
reviewer is explicit that this is **not a gap** - the read side's `resolve()` / `relative_to()`
proof holds - but that the asymmetry will read as one to the next person.

Required: route `resolve_contained_relpath`'s component validation through `_contained_parts` so
one function defines a legal component for both sides. Keep the read side's existing `resolve()`
containment proof; this is about removing a divergence, not replacing a check.

**Watch for over-rejection.** `_contained_parts` rejects any component containing `:`. Prove by
test that every legitimate path the parser actually resolves still resolves - the manifest
inventory paths, `project/project_manifest.json`, `project/input_quality_report.json`,
`parse/annotation.json` and the overlay path. If any real path would now be rejected, stop and
report rather than loosening the grammar.

## Boundaries

- No contract, schema, error-code or dependency change. `pyproject.toml` and `uv.lock`
  byte-identical.
- Do not touch GC3-8, GC3-9 or GC3-10. `_APPROVED_ANNOTATION_IMAGE_KINDS` stays
  `{"floorplan"}` — its amendment is approved but belongs to a different round.
- Do not edit `docs/plans/PLAN-002-floorplan-parsing.md` or anything under `evidence/`.
- `parse_run()` must never raise. Fix 1 touches a double-fault path; keep it inside the tuple.
- The golden canonical projection hash must not move:
  `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`.
- Baseline to preserve: **351 passed, exit 0**, repository `.venv`, cleared `PYTHONPATH`.
- Every fix leaves at least one test that fails if it is reverted, named per fix in your report.
- Do not commit. The orchestrator commits.

## A specific warning from the last round

Your NA-3e test `test_destination_containment_is_reproved_if_component_grammar_misses_drive_anchor`
passed in your sandbox and failed on the machine of record, because it hardcoded `C:` as the
injected drive and `pathlib` only discards the left-hand path when the drive differs from the
root's. **Do not write another test whose outcome depends on which volume `pytest` puts `tmp_path`
on.** If a test needs a foreign drive letter, derive it from the root's drive at run time.

## Deliverable

`evidence/PLAN-002/reviews/rework5-report-20260811.md` with, per fix: the defect, the change, the
reversion test, and anything you could not do. Plus the full suite result, confirmation that the
boundaries above held, and your runtime metadata read from the session rollout.
