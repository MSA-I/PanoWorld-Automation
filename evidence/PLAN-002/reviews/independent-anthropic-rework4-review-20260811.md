<!-- Archived verbatim by the orchestrator. The reviewer wrote this document. The only changes
made to the captured text are mechanical: repair of an OEM-codepage mangling of em dashes
introduced by the capture pipeline (PowerShell decoded the CLI's UTF-8 stdout as cp862) and
removal of zero-width characters that would break greps. No wording was altered.

Runtime metadata, from the harness rather than from the reviewer's self-description:
  task: NA-3f, independent review of the fourth bounded rework (NA-3e)
  provider: anthropic
  requested_model: opus / claude-opus-5
  actual_model_id: claude-opus-5   (requested route honoured, no substitution)
  effort: not exposed by the CLI as a parameter separate from the model tag
  route: claude CLI headless (-p), --strict-mcp-config, read-only allowlist, plus a workspace
         directory outside the repository holding the pre-materialised patch
  session_id: 48b8de51-dd20-4e8f-90e6-16d214c34aa7
  turns: 48 | wall clock: 15.3 min | output tokens: 50,727
  cache read / creation: 2,644,930 / 259,924 | cost: USD 6.57
  permission denials: 0
  subject: branch panoworld-dev/na-3e-major-fixes at 5ae8144, cut from main at c1cbc45
  dispatch brief: the NA-3f prompt derived from
    evidence/PLAN-002/reviews/na3e-rework4-dispatch-20260810.md

ONE CORRECTION THE REVIEWER MAKES TO ITS OWN DISPATCH, recorded because it bears on weight: the
prompt asserted it had no Bash tool. It did have one. It states that it ran no command with it -
no shell, no git, no pytest - and that every claim rests on file reads, naming the commands it
would have run instead. The orchestrator ran those commands separately and recorded the results in
evidence/PLAN-002/reviews/orchestrator-verification-na3e-20260810.md.
-->

VERDICT: ACCEPT

## Runtime metadata (from the harness, not self-description)

| Field | Value |
|---|---|
| Provider | Anthropic |
| Model id | `claude-opus-5` |
| Reasoning effort | **Not exposed to me by the harness.** The environment block reports provider and model id and no effort value. Recorded rather than guessed; take it from the dispatch record. |
| Access | Real read-only access to the repository working tree, plus the materialised patch (diffstat + full change set) supplied in a directory outside the repository. |
| Tooling | **Correction to the dispatch's premise, recorded because it bears on how this evidence should be weighed:** a Bash tool *is* present in this harness. I ran no command with it — no shell, no git, no pytest — and every claim below rests on file reads. Where execution was needed I named the command instead, per the read-only constraint. |
| Skills | `/skills` invoked at dispatch; `differential-review` applied (risk-first triage, evidence-based findings with file:line, adversarial phase against the handler tuple and the containment family). |
| Session ID | `48b8de51-dd20-4e8f-90e6-16d214c34aa7` |
| Subject | Branch `panoworld-dev/na-3e-major-fixes`, HEAD `5ae8144`, cut from `main` at `c1cbc45`. |

---

## Why ACCEPT

All eight findings are closed, each with a test that fails if the fix is reverted. The four regressions the brief named as suspicions are ruled out by tracing, not by assertion. Every boundary held. The working tree agrees with the materialised patch on every hunk I examined.

What remains is three residues — the DXF subprocess reopen (explicitly mandated out of scope by the brief), the unbounded raster read (V-2, pre-existing, relocated not created), and the `overlay_omitted_reason` overload (V-3, new in this round, blast radius one in-memory field on a double-fault path). None re-opens a gate. Two of the three cannot be fixed properly without the contract boundary the dispatch forbade this implementer from touching. Blocking a fifth round on residues that the brief itself put out of reach would be reviewing the brief, not the work.

I answer the orchestrator's direct question on V-3 below: **yes, the boundary is the thing that should give** — but as a separately named work item, not as NA-3e rework five.

---

## Per-finding verdicts

| ID | Verdict | Primary evidence | Reversion test |
|---|---|---|---|
| F-1 | **CLOSED** | `src/pwa/floorplan/runs.py:305-325` | `tests/integration/test_plan002_parse_run.py:169`, `:196` |
| F-2 | **CLOSED** for the raster path; the DXF residue is the brief's own mandated exclusion | `src/pwa/floorplan/annotation_source.py:77-88`; `src/pwa/floorplan/builder.py:316-341`, `:802`, `:846` | `tests/unit/test_floorplan_sources.py:120`; `tests/unit/test_floorplan_builder.py:112` |
| F-3 | **CLOSED** | `src/pwa/floorplan/runs.py:12-22`, `:29-51` | `tests/integration/test_plan002_failure_matrix.py:96`, `:110` |
| F-4 | **CLOSED** | `src/pwa/files.py:27-58`; `src/pwa/floorplan/runs.py:212-231`; `src/pwa/floorplan/builder.py:1036-1041` | `tests/integration/test_plan002_parse_run.py:299` |
| F-5 | **CLOSED** | `src/pwa/floorplan/runs.py:241-302` | `tests/integration/test_plan002_parse_run.py:228`, `:251` |
| F-6 | **CLOSED** | `src/pwa/floorplan/builder.py:692-693`, `:704` | `tests/integration/test_plan002_parse_run.py:1245` |
| F-7 | **CLOSED** | `src/pwa/floorplan/runs.py:15-18` | `tests/integration/test_plan002_failure_matrix.py:103` |
| F-8 | **CLOSED** | `src/pwa/floorplan/annotation_source.py:77-79` | `tests/unit/test_floorplan_sources.py:146` |

Both test gaps are also closed: overlay escaping at `tests/unit/test_floorplan_overlay.py:368`, GC3-5 real-subprocess composition at `tests/integration/test_plan002_parse_run.py:592`.

### F-1 — CLOSED

`finalize_run` at `src/pwa/floorplan/runs.py:305-325` now has exactly the shape the brief required:

```python
verify_run_inventory(staging_run, manifest)
verify_run_derived_artifacts(staging_run)
os.replace(staging_run, final_run)
try:
    verify_run_inventory(final_run, manifest)
    verify_run_derived_artifacts(final_run)
except (OSError, ValueError):
    try:
        os.replace(final_run, staging_run)
    except OSError as rollback_error:
        raise FinalizedRunLeftBehindError(
            "finalized directory left behind after rollback failure"
        ) from rollback_error
    raise
```

The finalized directory is not deleted; it is renamed back. `FinalizedRunLeftBehindError` subclasses `OSError` (`runs.py:24-25`), so the existing handler tuple catches it and `parse_run()` still returns rather than raising.

The brief's instruction to strengthen rather than duplicate was followed: `tests/integration/test_plan002_parse_run.py:169-193` is the same test, now asserting all four required properties — `cli_exit == 2` (`:190`), `diagnostic["outcome"] == "operational_failure"` (`:191`), `not result.final_run.exists()` (`:192`), `result.staging_run.is_dir()` (`:193`). That is precisely the assertion whose absence let the defect through in NA-3d. The rollback-failure branch has its own test at `:196-225`.

**Residual, stated plainly.** In the double-fault case (post-rename verification fails *and* the rename-back fails), the finalized directory is left on disk, still containing a `parse/parse-report.json` reading `complete`/`0`. That is the shape the dispatch prescribed. The signal that this happened lives only in the returned in-memory diagnostic — see V-3.

### F-2 — CLOSED (raster path)

`src/pwa/floorplan/annotation_source.py:77-88` is a single snapshot with everything derived from it:

```python
image_root = source_root if source_root is not None else Path(path).parent
image_path = resolve_contained_relpath(image_root, image_ref)
image_bytes = image_path.read_bytes()
image_sha256 = "sha256:" + hashlib.sha256(image_bytes).hexdigest()
if image_sha256 != payload["image"]["sha256"]: ...
if source_inventory is not None and image_sha256 != source_inventory[image_ref]["sha256"]: ...
with Image.open(io.BytesIO(image_bytes)) as image:
    width_px, height_px = image.width, image.height
```

One read, one digest, both comparisons against that digest, dimensions decoded from those same bytes in memory. The inventory comparison at `:83` is digest-to-inventory, which is strictly stronger than the declaration-to-declaration compare it replaces.

The snapshot then reaches the overlay unbroken: `builder.py:802` takes it from `extract_with_image_snapshot()`, `:846` passes it as `source_bytes=`, and `_source_binding` at `builder.py:316-341` uses it for all three of the decode (`:319`), the sanitized overlay bytes (`:328`, `:336`) and the lineage hash (`:335`, `hashlib.sha256(source_bytes)` — **not** a second `sha256_file`). I checked this specifically because the third read in NA-3d's F-2 was exactly this `source_sha256`. The surviving `sha256_file(source_path)` at `builder.py:365` is in the DXF branch only.

`tests/unit/test_floorplan_sources.py:141` asserts `image_reads == 1`, which is the falsifiable form of the property.

**Mandated residue:** the DXF worker still reopens the staged path in a subprocess. The brief put this out of scope and the implementer recorded it. Confirmed unchanged.

### F-3 and F-7 — both CLOSED

`src/pwa/floorplan/runs.py:12-22` rejects any component containing `:`, which closes the drive-relative anchor and the ADS channel together. `validate_contained_destination` at `:29-51` gains the closing independent proof:

```python
root_resolved = root.resolve(strict=True)
resolved = cursor.resolve(strict=False)
try:
    resolved.relative_to(root_resolved)
except ValueError as exc:
    raise ValueError("path escapes containment root") from exc
```

`strict=True` on the root is safe: the function already requires the root to be an existing directory before this point.

All five write-side helpers now route through `_contained_parts` — `validate_contained_destination`, `create_contained_directory`, `resolve_contained_output`, `write_bytes_contained`, and `copy_immutable`'s destination (which comes from `resolve_contained_output`). The asymmetry that F-3 named is gone.

The defense-in-depth test at `tests/integration/test_plan002_failure_matrix.py:110-120` is now environment-independent, which is the GC4-1 fix: it injects `Q:` unless the temp root is already on `Q:`, in which case `R:` (`:114`), with the comment naming the different-drive requirement. That is the correct fix — the previous version's `C:` was silently a no-op whenever `tmp_path` landed on `C:`.

### F-4 — CLOSED

`src/pwa/files.py:27-58` adds `*, create_parents: bool = True` to `copy_immutable` and `write_json_exclusive`; the `False` branch requires an existing regular non-reparse parent. The PLAN-001 default is preserved, so intake and packager are untouched in behaviour. `write_bytes_contained` gains the equivalent at `src/pwa/floorplan/runs.py:212-231`, including a `destination.exists() or destination.is_symlink()` pre-check that raises `FileExistsError`.

I verified completeness by enumerating every `mkdir`/`exist_ok=True` under `src/`. After this change the only survivors are `src/pwa/files.py:32,50` (behind the PLAN-001 default), `src/pwa/intake.py:87,114` and `src/pwa/packager.py:94,200` — all PLAN-001. The floorplan package's only remaining `mkdir` is the bare, per-component, reparse-checked `runs.py:68 cursor.mkdir()`. The overlay write at `builder.py:1036-1041` is the one the finding named, and it is now `write_bytes_contained(..., create_parents=False)`.

The test at `tests/integration/test_plan002_parse_run.py:299-326` displaces `staging_run/parse` mid-run and asserts the parent is *not* recreated (`:326`) — the exact property, not a proxy for it.

### F-5 — CLOSED

`verify_run_derived_artifacts` at `src/pwa/floorplan/runs.py:241-302` re-validates the six required envelopes and recomputes each `content_hash`, handles the optional `parse/annotation.json` through `resolve_contained_relpath(..., must_exist=False)`, and re-hashes every overlay declaration found in `floorplan_parse.payload.overlay` and `parse_report.overlay` against the contained overlay file. It is called on both sides of the rename (`:307`, `:311`).

No new manifest of derived hashes was invented; the checks read declarations that already exist. That is what the brief asked for.

`_load_json_document` and `_verify_envelope` are both defensively bounded — `UnicodeDecodeError`, `JSONDecodeError`, `RecursionError`, `KeyError`, `TypeError`, `ValueError` — so this new machinery cannot introduce a raise. See the `parse_run()` analysis below.

### F-6 — CLOSED

`src/pwa/floorplan/builder.py:692-693` reads at most `MAX_ANNOTATION_BYTES + 1`, inside the existing `except OSError` stage handler; the sentinel byte lands on the pre-existing `PARSE_RESOURCE_LIMIT` branch at `:704`. `src/pwa/floorplan/config.py` is byte-identical to `main`, so no limit and no `limits_snapshot()` key was added.

The test at `tests/integration/test_plan002_parse_run.py:1283` asserts `read_sizes == [MAX_ANNOTATION_BYTES + 1]` — it pins the read size, not just the resulting exit code, so an unbounded `read_bytes()` reintroduced later fails it.

### F-8 — CLOSED

`src/pwa/floorplan/annotation_source.py:77-79` resolves `source_image_ref` through `resolve_contained_relpath` inside the adapter, before the first open. The caller's later check at `builder.py:808-811` is retained as defense in depth, and — this matters for suspicion (c) — it resolves the *same* ref.

The `source_inventory=None` shape now has a real gate for the first time, which is the half of F-8 that had none. `tests/unit/test_floorplan_sources.py:146-175` plants a junction and asserts rejection before the open.

---

## GC3-2 and GC3-3 — the two gates whose unclosed halves this round targeted

**GC3-2: CLOSED.** The gate's literal requirement (a post-finalization check) was already satisfied in NA-3b. The invariant it exists to protect — "an operational failure leaves no finalized run" — is now satisfied too, by the rollback at `runs.py:315-322`, and the gate's own test asserts it at `tests/integration/test_plan002_parse_run.py:192-193`. F-5 closed the second half (the check covered only `payload.inputs`); `verify_run_derived_artifacts` now covers the envelopes and the overlay. Both halves are closed.

**GC3-3: CLOSED for every input the gate can reach; the DXF subprocess is an explicitly recorded exclusion.** Manifest, quality report and annotation JSON were already single-snapshot. The raster is now single-snapshot end to end, which was the specific defect. The DXF path cannot be made single-snapshot without changing the worker interface to take bytes or an inherited descriptor — the brief ruled that out for this round, and I agree with the ruling: it is a design change, not a fix. I would record GC3-3 as CLOSED with a named, plan-level follow-up rather than leave it PARTIALLY_CLOSED indefinitely, because "partially closed" on a gate whose remaining half is out of scope by decision stops carrying information.

---

## Regression hunt

### (a) Can the F-1 rename-back leave a third state, neither staging nor final? — **No.**

`staging_run` is `runs_root/.staging/<id>` and `final_run` is `runs_root/<id>` (`builder.py:519-520`, `:766-768`). Same volume, so `os.replace` is atomic in both directions. Exactly three terminal states are reachable:

1. Both verifications pass → final exists, staging gone, CLI 0.
2. Post-rename verification fails, rollback succeeds → staging restored, no final, the original exception re-raised (`runs.py:322`) → caught → CLI 2. This is the invariant `tests/integration/test_plan002_parse_run.py:277` asserts for every other operational failure.
3. Rollback itself fails → final exists, staging gone, `FinalizedRunLeftBehindError` → caught as `OSError` → CLI 2 with the explicit reason.

There is no window where neither path exists: `os.replace` does not have an intermediate observable state on the same volume. I also checked the one place that could crash on the missing staging directory — `_staged_operational_result` guards its write with `if staging_run.is_dir()` (`builder.py:450`), so state 3 skips the write instead of raising.

### (b) Does rejecting `:` over-reject a legitimate path? — **No, for anything the pipeline produces.**

I enumerated every path `src/pwa/intake.py` emits: `floorplan{suffix}` and `style_reference{suffix}` (`intake.py:162-164`), `derivatives/dxf/preview.svg` (`:178`), and `derivatives/pdf/page-%04d.png` (`:208-210`). None contains a colon. Every literal write-site path in `builder.py` is a constant (`project/source-manifest.json`, `parse/floorplan_parse.json`, and so on). `parse_run_id` already passed `_PARSE_RUN_ID_RE`, which excludes `:` (`builder.py:55`).

The orchestrator's PoC independently confirms the negative side: `project/source-manifest.json`, `a/b/c.json` and a bare `x.json` are all still accepted, and `..`, absolute and empty are still rejected.

Residual, informational: on POSIX, a hand-authored source run containing a filename with a literal `:` would now fail with CLI 2 instead of parsing. That is the dispatch-mandated behaviour and the correct trade — the Windows aliasing hazard is not conditional on the host, since a manifest is portable.

One asymmetry worth recording for a future reader: the `:` rejection lives in `_contained_parts`, which the *write* side uses. `resolve_contained_relpath` (the read side) does not call it and still relies on its `resolve()`/`relative_to()` proof alone (`runs.py:168-177`). That proof does hold — I traced `Path(root) / "C:"` through it and the drive-swapped cursor fails `relative_to`, which is what the orchestrator's PoC line 6 measured — so this is not a gap. It is an inconsistency that will read as one to the next maintainer.

### (c) Does the F-2 single snapshot alter overlay bytes or the golden hash? — **No.**

The snapshot is read from `resolve_contained_relpath(staging_run, image_ref)` at `annotation_source.py:78`; the caller resolves *the same* `source_image_ref` at `builder.py:808-811` and previously read the same file. Same path, same bytes, and `_sanitize_raster_bytes` has pinned encoder settings (`builder.py:303-304`, `:307-313`), so the sanitized output is byte-identical.

The golden hash cannot be affected regardless: `tests/golden/test_floorplan_golden.py` pins `canonical_projection` of the *geometry*, which contains no raster bytes, and `tests/golden/` is absent from the diffstat. The golden test also calls `AnnotationSource().extract(annotation_path)` with no `source_root` and no `source_inventory`, which exercises the F-8 `image_root = Path(path).parent` branch — so the new containment resolution is under golden coverage rather than bypassed by it.

### (d) Can the F-5 finalisation checks fail on a legitimate run? — **No, on every path I could trace.**

All six entries of `_REQUIRED_ENVELOPE_PATHS` (`runs.py:241-248`) are written before every one of the five `finalize_run` call sites. `parse/annotation.json` is optional by construction (`must_exist=False`). The overlay check skips any declaration that is not a dict or lacks `"path"` — which is exactly the shape `_failed_scale_artifacts` produces, whose `failed_payload` carries no `"overlay"` key and whose parse report's `"overlay"` is `{"overlay_omitted_reason": ...}`. So failed-domain CLI 3 runs finalize normally.

I did chase one hypothesised ordering hazard to ground: a failed-domain `FloorplanError` raised by `copy_source_inventory` at `builder.py:789` would occur *before* `source-manifest.json` and `source-quality-report.json` are written at `:790-791`, which would make `verify_run_derived_artifacts` fail on a run that should have been CLI 3 — downgrading it to CLI 2. It is unreachable: the only code `copy_source_inventory` raises is `PARSE_SOURCE_HASH_MISMATCH`, and that code is **absent** from `_FAILED_DOMAIN_CODES` (`builder.py:371-387`, read in full), so it takes the operational branch and never reaches `finalize_run` at all. This is the same mechanism the NA-3d review relied on for AC-20's first preflight case, and it still holds.

### Adversarial pass on the handler tuple — `parse_run()` still cannot raise

The tuple at `builder.py:1090-1097` is unchanged in membership (`OSError`, `ValueError`, `UnicodeDecodeError`, `json.JSONDecodeError`, `Image.DecompressionBombError`, `Image.DecompressionBombWarning`); only the binding changed to `as exc`. I attacked every exception source this round introduces:

- `FinalizedRunLeftBehindError` — subclasses `OSError` (`runs.py:24-25`). Caught.
- `root.resolve(strict=True)` in `validate_contained_destination` — `FileNotFoundError` is an `OSError`, and the function already requires the root to exist before reaching it. Caught either way.
- `_load_json_document` (`runs.py:250-262`) — catches `UnicodeDecodeError`, `JSONDecodeError`, `RecursionError`, and re-raises as `ValueError`; requires a dict, so a JSON scalar at top level cannot produce an `AttributeError` downstream.
- `_verify_envelope` (`runs.py:265-280`) — catches `KeyError`, `TypeError`, `ValueError`, `RecursionError` around `validate_artifact` and `compute_content_hash`.
- The overlay declaration loop — guards on `isinstance(declaration, dict)` and `"path" in declaration` before any subscript.
- The bounded annotation read (`builder.py:692-693`) — inside the existing `except OSError` stage handler.
- The `create_parents=False` branches — raise `ValueError` and `FileExistsError` (an `OSError`). Both caught.

Two theoretical escapes survive, neither introduced by this round:

- `MemoryError` from `image_path.read_bytes()` (`annotation_source.py:79`) or from `_load_json_document`. `MemoryError` is not in the tuple. This is V-2 and it predates the round.
- `AttributeError` if an envelope's `payload` were JSON `null`. Blocked in practice because `_verify_envelope` runs before any payload access and `validate_artifact` rejects it.

The `except Exception: return 2` guard at `src/pwa/floorplan/cli.py:25` remains the deliberate outer net, documented in place. It is a backstop, not the contract.

---

## Rulings on the orchestrator's open items

**V-1 — RESOLVED.** The GC4-1 fix at `tests/integration/test_plan002_failure_matrix.py:110-120` is correct and is the right kind of fix: it makes the test assert the property on any machine rather than papering over the environment. Dispatching it back to the same implementer rather than patching it in the orchestrator seat was the right call under section 17.

**V-2 — RESIDUE, not a regression, and I would fix it next.** `MAX_SOURCE_RASTER_BYTES` (50 MiB) is enforced only at `src/pwa/floorplan/overlay.py:110`, on `source["image_bytes"]`, i.e. after full materialisation. The full read at `annotation_source.py:79` is unbounded. But the *same* single full materialisation existed before this round at `builder.py:318` inside the same `try`; F-2 moved it earlier without adding a second one, and the F-2 test pins the count at exactly one. So the exposure is unchanged in kind and reduced in count.

It is still worth closing, for the reason F-6 was closed: a limit that does not bound the read it names is not a limit, and the escape hatch is `MemoryError`, which is outside the handler tuple. The fix is symmetric with F-6 — read `MAX_SOURCE_RASTER_BYTES + 1` and raise the existing `PARSE_RESOURCE_LIMIT`. It needs no new limit key. **Recommend as a named follow-up, not a blocker.**

**V-3 — REAL FINDING. My answer to the orchestrator's question: yes, the boundary should give.**

`builder.py:1076-1080` and `:1104-1108` set `overlay_omitted_reason` to `"finalized_directory_left_behind"`. The approved design record at `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md:585` closes that field's vocabulary at three values — `no_normalized_geometry`, `overlay_exceeds_max_bytes`, `source_raster_exceeds_limits` — and states the overlay is never produced for operational failures. This round adds an undeclared fourth value whose meaning is orthogonal to the field's name: it reports a filesystem rollback failure, not a rendering decision.

Three things bound the damage, and I weighed each:

1. `parse-report.json` has no JSON Schema — it is the non-envelope document `verify_run_derived_artifacts` parses directly — so this is *not* ADR-0005 schema surface. It is design-record surface. Amending it is cheap.
2. In the rollback-failure path the value is never persisted: staging is gone, so `_staged_operational_result` skips its write (`builder.py:450`). The value exists only in the returned in-memory diagnostic, which is what `tests/integration/test_plan002_parse_run.py:225` asserts.
3. `src/pwa/floorplan/cli.py` discards `result.diagnostic` entirely and returns only `result.cli_exit`, so **no CLI operator ever sees this signal.** An operator facing a left-behind finalized run sees exit code 2 and nothing else.

Point 3 is the one that matters. The dispatch's requirement was "make the returned diagnostic say plainly that a finalized directory was left behind", and the API-level diagnostic does. But the condition it reports — a published run directory that must not be trusted — is precisely the one an operator needs told, and the only surface an operator has is silent about it.

The implementer had no way to do better inside the boundaries, so this is not a failure of the work. It is a correctly-identified place where the brief's constraint bites. **Recommended follow-up, scoped:** add a distinct diagnostic field (or a distinct `outcome` value) for residual-state reporting, amend the design record's vocabulary rather than overloading it, and surface it through `cli.py` on the exit-2 path. That is a bounded change to a non-schema document plus a few lines in the CLI.

**V-4 — RESIDUE, no action needed this round, and it should be recorded in the same follow-up as V-3.** After a *successful* rollback, staging is restored complete with a `parse/parse-report.json` reading `"outcome": "complete"`, because `_staged_operational_result` will not overwrite an exclusively-created artifact. The published invariant holds — no finalized run, accurate returned diagnostic — but a human inspecting the retained staging directory reads a success report for a failed run. The orchestrator was right to record rather than fix it: both available fixes (overwrite an `O_EXCL` artifact, or add a new one) are exactly the kind of thing that needs a decision before code. It belongs with V-3 because both are the same question — where does a run record its residual state.

---

## Boundary verification

| Boundary | Verdict | Evidence |
|---|---|---|
| No contract or schema change | **HELD** | `schemas/` and `contracts/` absent from the diffstat (16 files, none under either). |
| No error-code change | **HELD** | `_FAILED_DOMAIN_CODES` at `builder.py:371-387` read in full; membership unchanged. F-6 reuses `PARSE_RESOURCE_LIMIT`, F-2 reuses `PARSE_SOURCE_HASH_MISMATCH`. `FinalizedRunLeftBehindError` is an internal exception type, not an error code. |
| No new dependency | **HELD** | `pyproject.toml` and `uv.lock` absent from the diffstat. The report's SHA-256 claims corroborate; I did not compute them (see CANNOT_VERIFY 3). |
| No new key in `limits_snapshot()` | **HELD** | `src/pwa/floorplan/config.py` absent from the diffstat; I read the file and counted the returned keys against the pre-existing set — identical. |
| `_APPROVED_ANNOTATION_IMAGE_KINDS` untouched | **HELD** | `= {"floorplan"}` at `src/pwa/floorplan/annotation_source.py:25`. |
| Nothing under `evidence/` rewritten | **HELD** | The four `evidence/` entries in the diffstat are pure additions (`+124`, `+255`, `+162`, `+106`); no deletions on any of them. |
| `docs/plans/PLAN-002-floorplan-parsing.md` untouched | **HELD** | No `docs/plans/` entry in the diffstat. |
| Golden hash not moved | **HELD** by inspection | `tests/golden/` absent from the diffstat; the expected value in `tests/golden/test_floorplan_golden.py` is unedited. Execution: CANNOT_VERIFY 2. |

One correction to the implementer's report, which does not affect any verdict: `evidence/PLAN-002/reviews/rework4-report-20260810.md:79` states "No diff exists in … `docs/`". The diffstat shows `docs/PROGRESS.md | 14 ++`. That file is an orchestrator commit, not this implementer's, and the boundary as written named `docs/plans/PLAN-002-floorplan-parsing.md`, which is genuinely untouched. The boundary held; the report's sentence is broader than what it verified.

---

## Acceptance-criteria re-assessment

| AC | Prior | Mine | Basis |
|---|---|---|---|
| **AC-4** (atomic finalisation; existing IDs/paths, stale staging and overwrite attempts fail safely) | NOT MET (F-1) | **MET, with one named residual** | The clause F-1 falsified is repaired at `runs.py:315-322`: an operational failure no longer leaves a finalized run. The second clause was already covered (`builder.py:537-549`, `runs.py:218-219`, `create_contained_directory`'s `FileExistsError`). The residual is the double-fault state 3 above — the brief authorised it explicitly, it is signalled, and it requires two independent filesystem failures. I record it as an accepted residual rather than reopening the AC, but it should be visible in the plan record, not only in this review. |
| **AC-13** (parse and assumptions validate, hashes recompute, provenance on every emitted entity) | CANNOT_VERIFY | **Now verifiable in principle; still CANNOT_VERIFY here** | F-5 materially improves the position: `verify_run_derived_artifacts` recomputes every envelope's `content_hash` at finalisation (`runs.py:265-280`), so "hashes recompute" is now an enforced runtime property rather than a construction-time one, and `tests/integration/test_plan002_parse_run.py:251` pins it. The blocker is unchanged and is not a code question: the AC line does not enumerate what "PLAN-002-required provenance" comprises, so completeness cannot be judged against it. **This is closable by writing the enumeration into the plan, not by more code.** |
| **AC-14** (source-aligned overlay, deterministic byte-for-byte, XML-valid, no active/external content) | PARTIALLY MET / CANNOT_VERIFY | **Now verifiable for the XML-validity clause; the determinism clause remains CANNOT_VERIFY** | The escaping gap disclosure 2 opened is closed: `tests/unit/test_floorplan_overlay.py:368-376` parses the generated fragment with `ET.fromstring` and asserts round-trip equality of a hostile label containing `<`, `&`, `>` and `"`. That is a real XML-validity proof, not a substring check. `escape()` is applied at every text site in `src/pwa/floorplan/overlay.py` (`:63`, `:91`, `:97`, `:101`, `:124`, `:210`). Byte-determinism still requires execution, and F-9's undeclared `ezdxf` ordering dependency is untouched by this round — correctly, it was not dispatched. |
| **AC-18** (over-size input fails pre-parse; limits fail with exact codes) | MET for code-mapping; byte caps weaker than they read | **MET for code-mapping; one of the two cap qualifications repaired** | F-6 fixed the annotation cap: `builder.py:692-693` bounds the read to the cap plus one. The DXF cap qualification is unchanged (checked on reads that are not the parse read — the mandated F-2 residue), and `MAX_SOURCE_RASTER_BYTES` remains post-materialisation (V-2). Codes and classification are unchanged and exact. Net: strictly better, not yet complete. |
| **AC-20** (failure decision table incl. exact code, severity, finalized-artifact presence/status, CLI exit) | PARTIALLY MET | **MET** | The clause that failed was "finalized-artifact presence/status", falsified by F-1's finalized-present/CLI-2 combination. That combination is gone in the normal case and is now an explicitly-reported double-fault. All three approved preflight cases still verify: hash mismatch → `PARSE_SOURCE_HASH_MISMATCH` + CLI 2 + no finalized run (absent from `_FAILED_DOMAIN_CODES` at `builder.py:371-387`, routed to `_staged_operational_result`); incomplete/blocked source quality → CLI 2; complete-but-unknown-scale → `PARSE_SCALE_UNKNOWN` + failed set + CLI 3. GC3-5's end-to-end composition through the real subprocess is now pinned at `tests/integration/test_plan002_parse_run.py:592-623`, asserting the code read back out of the *finalized* run with `cli_exit == 3`. |

---

## CANNOT_VERIFY

Each item names the command the orchestrator should run. These are evidence gaps, not hedges on findings.

1. **Suite result `351 passed`, exit 0, baseline 338.** Not run — no command executed by me.
 → `.venv/Scripts/python.exe -m pytest -q` with inherited `PYTHONPATH` cleared.
2. **Golden canonical-projection hash still `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`.** Requires execution; the expected value is unedited and `tests/golden/` is not in the diffstat, which is necessary but not sufficient.
 → `.venv/Scripts/python.exe -m pytest tests/golden -q`
3. **`pyproject.toml` and `uv.lock` byte-identical to `main`.** The diffstat's silence is strong evidence; the report's SHA-256 values are the implementer's own and I did not recompute them.
 → `git diff --stat main -- pyproject.toml uv.lock schemas contracts docs/plans` (expect empty)
4. **Working tree byte-equals the materialised patch for `src/` and `tests/`.** I read `runs.py`, `annotation_source.py`, `files.py`, `config.py`, `cli.py`, `overlay.py` and the relevant regions of `builder.py` in the working tree, plus the new and strengthened tests, and every hunk agreed with the patch. I could not prove byte equality across the whole change set.
 → `git status --porcelain` (expect clean) and `git diff --stat HEAD -- src tests` (expect empty)
5. **Every fix fails if reverted.** I verified each test *asserts the right property* by reading it; I did not run a revert-and-fail experiment for any of the eight.
 → For the two that carry the most weight: revert `runs.py:315-322` (the rollback block) and run `pytest tests/integration/test_plan002_parse_run.py -k "post_finalization" -q` — **expect 2 failures**. Revert `annotation_source.py:79-88` to `sha256_file` + `Image.open(image_path)` and run `pytest tests/unit/test_floorplan_sources.py::test_annotation_source_reads_one_raster_snapshot_for_hash_and_dimensions -q` — **expect 1 failure** on `image_reads == 1`.
6. **V-2's `MemoryError` escape is reachable in practice.** Needs a raster large enough to exhaust memory; not attemptable read-only and arguably not worth attempting at all.
 → Cheaper partial: `pytest tests/integration/test_plan002_parse_run.py -k raster -q` after adding a bounded read, to confirm no legitimate raster regresses.
7. **The GC3-5 real-worker test's `PYTHONPATH` override is portable.** `tests/integration/test_plan002_parse_run.py:600` *replaces* rather than prepends `PYTHONPATH`, so the subprocess reaches `pwa` through the installed environment. On this repository that holds. On a source-layout checkout where `pwa` is importable only via `PYTHONPATH`, the worker would fail to import and the test would fail its `cli_exit == 3` assertion — loudly, not silently, so it is fail-safe. Informational only.
 → `.venv/Scripts/python.exe -m pytest tests/integration/test_plan002_parse_run.py::test_real_dxf_worker_subprocess_maps_cumulative_entity_overflow_to_cli3 -q`
8. **AC-14 byte-determinism and F-9's `ezdxf` ordering dependency.** Needs a second `ezdxf` version. Out of scope for this round; unchanged by it.
9. **My own reasoning-effort value.** Not reported by the harness. Take it from the dispatch record.
10. **GC3-8, GC3-9, GC3-10.** Not re-opened, per the brief. Nothing in this change set makes any of them worse; `_APPROVED_ANNOTATION_IMAGE_KINDS` is verified unchanged and the GC3-8 amendment draft is a pure addition under `evidence/`.

---

## What I am not claiming

- This review does not decide merge. Merge requires Moshe's separate authorisation, and G1 additionally requires the human visual gate GC3-10 / NA-4.
- I ran no command. Items 1-8 above are open on execution, and item 1 in particular means "351 passed" is the implementer's claim corroborated by the orchestrator's own run of a 350-passed predecessor, not something I observed.
- Severities and the ACCEPT/NEEDS_REWORK line are mine. Where I differ from the orchestrator it is on V-3, and only on emphasis: the orchestrator asked whether the boundary should give and I am answering yes, while agreeing the implementer had no better option inside it.

---

## Recommended follow-ups (none blocking this round)

1. **Residual-state reporting** (V-3 + V-4 together): a distinct diagnostic field or `outcome` value for "a finalized directory was left behind", surfaced through `src/pwa/floorplan/cli.py` instead of discarded, plus the design-record vocabulary amendment at `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md:585`. Not schema surface — `parse-report.json` has no schema.
2. **Bound the raster read** (V-2), symmetric with F-6: read `MAX_SOURCE_RASTER_BYTES + 1` at `src/pwa/floorplan/annotation_source.py:79`, map overflow to the existing `PARSE_RESOURCE_LIMIT`. No new limit key.
3. **Enumerate AC-13's provenance requirement** in `docs/plans/PLAN-002-floorplan-parsing.md` so the criterion becomes decidable. This is the only thing standing between AC-13 and a verdict.
4. **DXF single-snapshot** (GC3-3's recorded exclusion): a worker interface taking bytes or an inherited descriptor. A design change, and it should be planned as one.
5. **Apply `_contained_parts` to `resolve_contained_relpath`** for consistency across the read and write sides. Not a gap — the read side's `resolve()` proof holds — but the asymmetry will read as one.
