<!-- Archived verbatim by the orchestrator. The reviewer wrote this document; the only changes
to the captured text are mechanical - repair of a cp862 mangling of em dashes introduced by the
capture pipeline, and removal of zero-width characters. No wording was altered.

Runtime metadata, from the harness rather than self-description:
  task: NA-3h, independent review of the fifth bounded rework (NA-3g)
  provider: anthropic
  requested_model: opus / claude-opus-5
  actual_model_id: claude-opus-5   (requested route honoured, no substitution)
  effort: not exposed by the CLI; the reviewer declined to invent a value
  route: claude CLI headless (-p), --strict-mcp-config, read-only allowlist, plus a workspace
         directory outside the repository holding the pre-materialised patch
  session_id: 25f0ef2f-504c-4e1c-9e49-557c9484757d
  turns: 43 | wall clock: 15.5 min | output tokens: 50,979
  cache read / creation: 3,322,025 / 199,274 | cost: USD 6.31
  permission denials: 1 (a chained read-only command; the reviewer did not retry it verbatim and
         substituted two narrower queries, and disclosed this itself)
  subject: branch panoworld-dev/na-3g-residues at 99ea552
  dispatch: evidence/PLAN-002/reviews/na3g-rework5-dispatch-20260811.md
  verdict: ACCEPT, with one must-fix follow-up (R-1) folded into NA-6

TOOL DISCLOSURE, made by the reviewer itself and reproduced here because it is the honest kind:
Bash, Edit and Write were all present despite the read-only mandate. It made no edit, wrote no
file, and ran no state-changing command, and it listed every Bash command it did run so the claim
is auditable. The orchestrator has verified those commands are all non-mutating reads.
-->

VERDICT: ACCEPT

# NA-3h — Independent Anthropic review of the fifth bounded rework (NA-3g)

## Runtime metadata (from harness, not self-description)

| Field | Value |
|---|---|
| Runtime provider | Anthropic |
| Model id | `claude-opus-5` |
| Reasoning effort | Not exposed by this harness. The harness reports the model id and a "fast mode" toggle; it does not surface a numeric or named effort level to the running agent. I decline to invent one. |
| Tools present | `Read`, `Grep`, `Glob`, `Bash`, `Edit`, `Write`, `Skill`, `ToolSearch`, and a set of deferred/agent tools |

**Tool-use disclosure.** As the previous reviewer found, a `Bash` tool is present despite the read-only mandate, and `Edit`/`Write` are present as well. I made no edit, wrote no file, and ran no state-changing command. I used `Bash` only for non-mutating reads, all of which are listed here for audit: `ls schemas`, `git log --oneline -3 main`, `git log --oneline 1946815..HEAD -- <paths>`, `git show --stat --oneline 99ea552`, and `wc -l` / `git show <ref>:PROJECT-STATE.yaml | wc -l`. None touches the index, the working tree, or history. One chained command of mine was refused by the permission layer; I did not retry it verbatim, and substituted two narrower read-only queries that answered the question more directly.

I invoked `/skills` and used **differential-review** as the methodology for this review (risk-first triage, evidence with `file:line`, blast-radius reasoning, adversarial pass). Its "always write a report file" step is overridden by the dispatch: this stdout document **is** the report artifact, and writing a file would violate the read-only boundary.

I read the four required documents in the required order before reading any code, then read the materialised patch, then read the working tree independently of the patch.

---

## 1. Per-fix verdicts

### Fix 1 — residual-state reporting and staging-report replacement: **CLOSED**

Three distinct defects were named; all three are closed.

**1a. The residual state left `overlay_omitted_reason`.**
`src/pwa/floorplan/builder.py:132` adds `residual_state: str | None = None` to `_diagnostic`, and `:162-164` emits it as a top-level key only when set. `_staged_operational_result` at `:441-475` no longer accepts `overlay_omitted_reason` at all — the parameter is now `residual_state` (`:449`) and is threaded into `_diagnostic` at `:458`. Both `parse_run` call sites pass it via the same expression (`:1090-1094`, `:1118-1122`):

```
residual_state=("finalized_directory_left_behind" if isinstance(exc, FinalizedRunLeftBehindError) else None)
```

I verified the negative side of this independently of the patch: `overlay_omitted_reason` now appears in `builder.py` only at `:864-871` and `:890`, all three assignments being overlay-vocabulary values. No operational-failure path writes that field. This restores the exact §11.4 closed vocabulary at `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md:585` — including its sentence "It is never produced for operational failures," which was false before this round and is true now.

**1b. The CLI discarded the diagnostic.**
`src/pwa/floorplan/cli.py:34-35` writes the diagnostic to stderr as `sort_keys=True` JSON when `residual_state == "finalized_directory_left_behind"`. A double fault is no longer invisible to an operator. (This line is also the site of finding R-1 below; the defect it closes is genuinely closed, and R-1 concerns the new line's own failure mode, not its function.)

**1c. Retained staging kept a `complete` report.**
`builder.py:460-474`. When staging survives and `parse/parse-report.json` already exists (the successful-rollback case), the operational-failure report is written to an exclusively-created sibling and `os.replace`d over the stale file. When it does not exist, the previous plain exclusive write is unchanged. The overwrite of an exclusively-created artifact is deliberate and, importantly, is confined to *staging* — no published run directory is ever overwritten.

**Reversion tests I confirmed exist in the tree, not merely in the report:**
- `tests/integration/test_plan002_parse_run.py:194-196` asserts the rolled-back staging report is not `complete`.
- `tests/integration/test_plan002_parse_run.py:228-229` asserts `residual_state` carries the value and that `overlay_omitted_reason` is absent — this test fails if 1a regresses in either direction.
- `tests/integration/test_plan002_cli.py::test_main_surfaces_finalized_directory_left_behind_diagnostic` (new in the patch) fails if the CLI discards the diagnostic again.

### Fix 2 — bounded raster read: **CLOSED**

`src/pwa/floorplan/annotation_source.py:78-88`. One `open("rb")`, one `stream.read(MAX_SOURCE_RASTER_BYTES + 1)`, an explicit `len(...) > MAX_SOURCE_RASTER_BYTES` check raising the pre-existing `PARSE_RESOURCE_LIMIT`, and only then the digest. The limit constant is imported at `:13` from `pwa.floorplan.config`; `config.py:17` still reads `MAX_SOURCE_RASTER_BYTES = 50 * 1024 * 1024` and is unchanged.

Two properties matter and both hold:
- **The bound precedes the expensive work.** The digest at `:88`, the Pillow decode at `:93`, and the returned snapshot at `:140` all consume the already-bounded `image_bytes`. Nothing reads the file a second time. This is exactly the F-6 idiom the previous review accepted for JSON, now applied to the raster, with no new limit key and no new error code.
- **The single-snapshot property from F-2 survives.** One read supplies digest, dimensions and embedded overlay pixels. That is what makes the hash a hash *of the bytes that ship*, and it is intact.

`PARSE_RESOURCE_LIMIT` is the correct code without any contract edit: `contracts/error_codes.md:63` already defines it as "A configured byte/count/pixel/overlay/resource bound was exceeded," and `docs/plans/PLAN-002-floorplan-parsing.md:345` already requires "Enforce file-size limits before JSON/DXF parsing."

**Reversion tests confirmed in the tree:** `tests/unit/test_floorplan_sources.py:121-163` pins `image_reads == 1` **and** `read_sizes == [MAX_SOURCE_RASTER_BYTES + 1]`, so it fails both if the read becomes unbounded and if a second snapshot is taken; `:166-173` pins overflow → `PARSE_RESOURCE_LIMIT`. The `read_sizes` assertion is the stronger of the two and is the one I would have written.

### Fix 3 — shared component grammar on the read side: **CLOSED**

`src/pwa/floorplan/runs.py:168` now calls `parts = _contained_parts(relpath)` and `:173-174` walks those parts, replacing the duplicated narrower check. The two independent defenses the previous review credited are retained verbatim: the lexical ancestor walk with reparse checks at `:174-180`, and the `resolve()`/`relative_to()` containment proof at `:185-190`. One function (`:18-26`) now defines a legal component for both the read and write sides, so the two grammars cannot drift.

**Reversion tests confirmed in the tree:** `tests/integration/test_plan002_failure_matrix.py:124-129` (read side rejects an ADS component) and `:132-163`, which monkeypatches `floorplan_runs._contained_parts` with a recorder and asserts `grammar_calls == legitimate_paths` over every derived-manifest inventory path plus the four fixed artifacts. The second test is the one that actually pins *routing* rather than *outcome* — it fails if someone reintroduces an equivalent inline check that happens to produce the same answers. That is the right test to have written, and I note the implementer's claim at `rework5-report-20260811.md:99-101` that it injects no drive letter is correct as written; the dispatch's warning about volume-dependent tests is respected.

---

## 2. Ruling on W-1: **acceptable residual. Do not fix now.**

The orchestrator recorded the sequence correctly, but it is not reachable through `parse_run()`. My reasoning, in the order I checked it:

1. A stale `parse/parse-report.operational-failure.tmp` can only exist inside a **retained staging directory**. It is created at `builder.py:466` on a path where staging survives, and the only way it survives the round is if `atomic_replace` at `:473` fails.
2. For the second double fault to encounter it, the second run must reach `builder.py:460` **for the same run id**. But `parse_run` guards that far earlier: the `destination_exists` check at `builder.py:558-571` returns a failed-domain result before any staging work when the run directory is already present.
3. Even bypassing that guard, staging creation at `:789-791` goes through `create_contained_directory`, which raises `FileExistsError` on an existing directory (`runs.py:66`) — caught, producing an operational failure without ever reaching the replacement branch.
4. So the only route is a TOCTOU race between the `:559` check and `:789` creation, *and* a prior double fault, *and* a second finalization double fault in the racing run. Three independent conditions.
5. In that residual-of-a-residual case the outcome degrades to precisely the pre-round state — a staging directory whose report says `complete` — **plus** a `.tmp` sibling that contains the truth. It is strictly more informative than what shipped before this round. `parse_run()` still does not raise (`FileExistsError` is an `OSError`, caught at `:474`), and the returned diagnostic is still accurate, because the diagnostic is built from the in-memory report and never read back from disk.

Ruling: **acceptable as a residual.** Requiring a sixth round to close a three-condition path whose worst case is a stale file inside an already-failed staging directory is not a good trade against the risk of another edit to the finalization path.

If the orchestrator wants it closed opportunistically inside some later touch of this function, the one-line form is `replacement_path.unlink(missing_ok=True)` immediately before `_write_staged_json(replacement_path, report)` at `builder.py:466`. I prefer that to a unique name: a unique name accumulates debris in staging on every failure, whereas the unlink keeps exclusive-creation semantics for the new bytes while guaranteeing the exclusive create can succeed. It needs no new test beyond the existing V-4 test. **It is not a condition of this acceptance.**

---

## 3. Regression hunt

I treated the four named vectors as hypotheses to disprove, and I derived each conclusion from the code rather than from the verifier's green result.

### (a) Does replacing an exclusively-created artifact open a window that did not exist before? — **No.**

The exclusive-creation invariant is about *published run artifacts*, and it is unbroken: the new bytes are themselves created exclusively (`src/pwa/files.py:48-55` → `open("x")`), and `os.replace` is atomic on both POSIX and Windows, so no reader can observe a truncated or absent report. The window a naive `open("w")` would have opened — a moment where the report is zero-length or partially written — does not exist here.

Three narrower checks:
- **Can the replacement escape staging?** No. `report_path` is derived as `staging_run / "parse" / "parse-report.json"` and `replacement_path` via `with_name()` on a constant, so both are siblings inside the staging tree by construction. No attacker-controlled component participates.
- **Can it clobber a finalized run?** No. The branch is guarded by `staging_run.is_dir()` at `:462`; on the `FinalizedRunLeftBehindError` path staging is gone by definition, so the branch does not execute at all.
- **Does it widen what an interleaved reader sees?** It narrows it. Previously the retained report asserted `complete` indefinitely; now it asserts the operational failure, atomically.

### (b) Can the CLI's new stderr write fail in a way that changes the exit code? — **Yes. Finding R-1, real, non-blocking.**

`src/pwa/floorplan/cli.py:20-33` wraps `parse_run` in `try: ... except Exception: return 2`. The new `print(..., file=sys.stderr)` at `:34-35` sits **outside** that block, after it. So:

- A `BrokenPipeError`, a closed or redirected-to-full-disk stderr, or any other `OSError` from the write propagates out of `main()`. The process exits **1 with a traceback** instead of the documented **2**.
- This happens on exactly the path whose purpose is to report that a finalized run directory was left behind — the operator loses the exit code precisely when the residual state is worst.
- The blast radius is bounded by the fact that `pyproject.toml` declares **no `[project.scripts]` console entry point**, so the affected surface is `python -m` invocation and any in-process caller of `main()`; an in-process caller receives an exception where the contract promises an `int`.

One hypothesis I raised and **disproved**: `ensure_ascii=False` plus an unconstrained `run_id` (`schemas/envelope/v1/envelope-1.0.0.schema.json:13` types it `["string","null"]` with no pattern) suggested a `UnicodeEncodeError` on a legacy-codepage stderr. It is not reachable — CPython initialises `sys.stderr` with the `backslashreplace` error handler, so non-encodable characters degrade to escapes rather than raising. R-1 is an `OSError` finding only.

Severity: **medium, non-blocking.** It requires a filesystem/pipe failure to trigger, it cannot corrupt state, and it cannot make `parse_run()` raise. The fix is two lines — move `:34-35` inside the existing `try`, or wrap the `print` in `except OSError: pass` — and I recommend it as a named follow-up rather than a sixth rework, since folding it into NA-6 costs nothing.

### (c) Does routing the READ side through `_contained_parts` reject any path the parser actually resolves? — **No.**

I checked the reasoning, not the verifier's 17/17. `_contained_parts` (`runs.py:18-26`) rejects a component when it is `""`, `"."`, `".."`, or contains `":"`. The old read-side check rejected a strict subset of those. So the only paths newly rejected are those containing a colon component — the Windows drive-relative anchor and the NTFS ADS suffix that the previous round's findings were about. The question is therefore whether any *legitimate* parser-resolved path can contain a colon.

The set of paths this function resolves is closed and enumerable: the four fixed artifacts (`project/project_manifest.json`, `project/input_quality_report.json`, `parse/annotation.json`, and `parse/overlay.svg` — the last written as a literal at `builder.py:941` and `:1032`), plus every inventory relpath from the derived manifest. The fixed four contain no colon. Inventory relpaths originate from source manifests, and any that contained a colon was already rejected on the **write** side by the same grammar before it could be copied into a run — so a colon-bearing inventory path cannot reach a state where the read side needs to accept it. The grammar is now no narrower on read than on write, which is precisely a *widening* of the accepted set on the read side relative to nothing and a narrowing only of paths that write already refused.

Independent of that argument, the accept-side test at `test_plan002_failure_matrix.py:132-163` enumerates the real path set from an actual run and asserts each one resolves, so the reasoning and the empirical check agree.

### (d) Does the bounded raster read change the bytes reaching the overlay or `source_sha256`? — **No.**

`io.BufferedReader.read(n)` returns `min(n, remaining)` bytes; for any file at or under the limit that is the entire file, byte-identical to the previous `read_bytes()`. Above the limit the run fails before any digest is computed, so no hash is produced from truncated bytes — the ordering at `:79-88` (read, check length, *then* hash) is what makes this safe, and reversing those two statements would have been a real defect. The same `image_bytes` object flows to the digest (`:88`), the dimension decode (`:93`) and the returned snapshot (`:140`), so there is no path on which the hashed bytes and the embedded bytes can differ.

This is consistent with, but not dependent on, the orchestrator's cross-adapter re-run holding the canonical projection at `sha256:05e6ce8218d11d09fb5f64181441ef1868e0bba2b18f21f55fb0c89d84ac36c6` with identical overlay byte counts (10,479 and 234,276).

Two secondary observations, neither a defect:
- The downstream check at `src/pwa/floorplan/overlay.py:108-115` still validates the **sanitized** bytes against `MAX_SOURCE_RASTER_BYTES` and `width*height` against `MAX_SOURCE_PIXELS`. Fix 2 is defense in depth *ahead* of it, not a replacement for it. Correct layering.
- `read(n)` preallocates an `n`-byte buffer, so the peak allocation for a small file is now nominally the limit rather than the file size. CPython shrinks the buffer on return; this is a transient and does not raise the ceiling above the 50 MiB the limit already sanctions.

**No other regression found.** In particular, `_source_binding` at `builder.py:321-346` retains a `source_path.read_bytes()` fallback at `:323`, but it is unreachable for the annotation path — bytes are always supplied at `:860` — so Fix 2 leaves no unbounded read behind it on any live route. I flag it as dead-code-shaped rather than as a defect.

---

## 4. Boundaries

| Boundary | Held? | Evidence |
|---|---|---|
| No contract change | Yes | `contracts/error_codes.md` unchanged; `PARSE_RESOURCE_LIMIT` reused, already documented at `:63` |
| No schema change | Yes | Nothing under `schemas/` in the patch; `ls schemas` shows no `parse_report` entry to change |
| No new error code | Yes | No new token in `contracts/error_codes.md`; every raise in the diff uses an existing code |
| No dependency change | Yes | `pyproject.toml` and `uv.lock` absent from the patch |
| No new `limits_snapshot()` key | Yes | `src/pwa/floorplan/config.py` absent from the patch; `limits_snapshot()` at `:35-59` unchanged; `MAX_SOURCE_RASTER_BYTES` was already a key |
| `_APPROVED_ANNOTATION_IMAGE_KINDS` untouched | Yes | `src/pwa/floorplan/annotation_source.py:26`, still `{"floorplan"}`; the only change to that file is the bounded read and its import |
| Nothing under `evidence/` rewritten | Yes | The patch adds two files under `evidence/PLAN-002/reviews/` and modifies none |
| Nothing under `docs/plans/` rewritten | Yes | `docs/plans/` absent from the patch entirely |
| Golden expectations untouched | Yes | `tests/golden` absent from the patch |

**The `PROJECT-STATE.yaml | 163 ++-------------------` line in the diffstat is not a boundary breach.** It looked like a rewrite of a governance file, so I checked it directly rather than accepting it. `git show --stat --oneline 99ea552` shows the NA-3g commit touches exactly ten files — two evidence additions and eight source/test files, 408 insertions and 22 deletions — and never touches `PROJECT-STATE.yaml`. `git log --oneline -3 main` shows the roadmap commit `a411a69` (+133 lines) landed on `main` *after* this branch was cut from `1946815`, and the line counts confirm it (main 1854 lines, branch head and working tree 1721). The diffstat entry is a branch-versus-`main` topology artifact of comparing against a moved base, not an edit by this round. I mention it because a reader of the diffstat alone would reasonably conclude otherwise.

### `residual_state` as contract surface: **confirmed not contract surface**

The previous reviewer's premise holds and I re-verified it at source rather than inheriting it. `docs/plans/PLAN-002-floorplan-parsing.md:167` describes `parse-report.json` as "raw deterministic finding/metric evidence, deliberately not an envelope artifact and not entered in the schema catalog," and `:338` repeats that it "is deterministic JSON with a tested internal shape … but is not claimed to be schema-valid." The `schemas/` listing contains no `parse_report` entry. Adding a top-level key to a file that is by design not schema-catalogued and not an envelope is not a contract change.

There is a stronger point available, and I think it should be on the record: **`residual_state` is never persisted to `parse-report.json` at all.** It is set only for `FinalizedRunLeftBehindError`, and that error by construction means the staging directory no longer exists — so `staging_run.is_dir()` at `builder.py:462` is False and no report is written on that path. The field lives only in the in-memory diagnostic and on stderr. It is not merely "not contract surface"; on the current code it is not even a new on-disk field.

**Repository-relative paths only.** No absolute path and no OS account name appears in this review. The two patch files live outside the repository and are referred to throughout as *the materialised patch*.

---

## 5. `parse_run()` must never raise — adversarial pass on the new double-fault path

I enumerated every statement this round adds inside `parse_run`'s reach and asked what each can throw.

- `_diagnostic(..., residual_state=...)` — dict construction and a single conditional assignment (`:132`, `:162-164`). Cannot raise.
- `staging_run.is_dir()` (`:462`) and `report_path.exists()` (`:463`) — both can raise `OSError` on a hostile filesystem; both are inside the `try` whose handler at `:474` catches `(OSError, ValueError)`.
- `report_path.with_name("parse-report.operational-failure.tmp")` (`:466`) — `with_name` raises `ValueError` only for an empty name; the name is a constant. Caught regardless.
- `_write_staged_json(replacement_path, report)` (`:467`) → `write_json_exclusive` (`src/pwa/files.py:48-55`) — raises `ValueError` on a missing or non-regular parent, `OSError` from the parent `lstat` reparse check, and `OSError`/`FileExistsError` from `open("x")`. All caught. The one escape is `json.dump` raising `TypeError` on a non-serializable value, which is **not** in the handler tuple.
- `atomic_replace(replacement_path, report_path)` (`:473`) — `OSError` only. Caught.

The `TypeError` deserves its own paragraph, because this round newly reaches a `json.dump` where the old code skipped the write entirely (when the report already existed). I checked whether it is actually reachable. On the new branch the report is always built from the two call sites at `:1084` and `:1112`, neither of which passes a `finding`, so `terminal_finding` is `None` and `findings` is empty — the two fields that could carry a non-primitive. Everything else in the report is a primitive, a list of primitives, or `limits_snapshot()`, whose `DXF_UNITS` entry is already stringified at `config.py`. The `FloorplanError` call site that *does* carry a finding (`:1096`) is reached only from errors raised before the report is written, so it lands on the `else` branch, exactly as before. **The new branch cannot raise `TypeError` on any reachable input.** The pre-existing theoretical `TypeError` exposure on the `else` branch is unchanged from what the previous review accepted.

On Fix 2's path: `image_path.open("rb")` and `stream.read()` raise `OSError`, which `parse_run` catches at `:1104`; the `FloorplanError` for overflow is caught at `:1063`. `MemoryError` remains outside every handler, but Fix 2 *reduces* that exposure by capping the allocation at the configured limit instead of the attacker's file size — this is a strict improvement on the pre-round state, not a new hole.

On Fix 3's path: `_contained_parts` raises `ValueError`, and every call site of `resolve_contained_relpath` is already inside a region that catches `ValueError` — `annotation_source.py:79` and `builder.py:806`/`:822` under the `try` at `builder.py:802` whose tuple at `:1104` includes `ValueError`; `builder.py:578` under its own guard; and the `finalize_run` verifiers under the post-rename handler that triggers rollback. No new escape.

**Conclusion: `parse_run()` still never raises.** The one exception that does escape this round is R-1, and it escapes from `main()` in `cli.py`, strictly outside `parse_run()`.

---

## 6. Has anything the previous review moved moved back?

| Item | Prior state | Now | Note |
|---|---|---|---|
| AC-4 | MET with residual | **MET, improved** | The bounded raster read closes the last unbounded materialisation on the annotation path; the residual the previous review named is now smaller, not larger |
| AC-18 | MET with residual | **MET, improved** | Fix 3 removes the read/write grammar divergence that the residual was about |
| AC-20 | MET with residual | **MET, improved** | Fix 1 makes the double-fault state operator-visible and stops retained staging asserting `complete`. R-1 slightly degrades the *exit code* on this path without degrading the *state*, which is why it is a follow-up and not a re-opening |
| GC3-2 | CLOSED | **still CLOSED** | Containment defenses at `runs.py:174-190` retained in full; Fix 3 only replaced the component test with the shared one |
| GC3-3 | CLOSED | **still CLOSED** | Exclusive creation retained everywhere; the single deliberate replacement is atomic, staging-scoped, and itself exclusively created |
| F-1 … F-8 | all CLOSED | **all still CLOSED** | No fix in this round reverts any F-item; F-2's single-snapshot property and F-6's read-limit idiom are both preserved and F-6's idiom is now extended to the raster |
| V-2 / V-3 / V-4 | recorded residues | **closed by fixes 1a+1b, 2, 3** | These were this round's scope and are the three verdicts in §1 |

Nothing has moved back. The baseline the dispatch told me not to let regress is intact.

---

## 7. Judgement on the routed design-record amendment

The implementer correctly did not edit `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md` — it is approved and append-only, and editing it would have been the more serious error than leaving §11.4 stale. Routing it was right.

**The proposed text is right in substance.** Its three claims each match the code: `overlay_omitted_reason` is confined to the three overlay values (`builder.py:864-871`, `:890`); residual filesystem state is recorded top-level as `residual_state: "finalized_directory_left_behind"` (`:162-164`, `:1090-1094`, `:1118-1122`); and the retained staging report is replaced because its `complete` claim is no longer true (`:460-474`).

**It is incomplete on four points, and I would not route it as written:**

1. **It does not say where `residual_state` lives.** As established in §4, on the current code it appears in the returned diagnostic and on stderr and is *never written to `parse-report.json`*. An amendment that says "recorded at the top level" without naming the surface invites a future reader to look for it on disk and conclude the code is broken. Name the diagnostic as the carrier.
2. **It should state the closed vocabulary of `residual_state` itself.** §11.4's value is that it closes a vocabulary. Introducing a second vocabulary without closing it repeats the mistake that produced this round's Fix 1a. Today the set is exactly `{"finalized_directory_left_behind"}`.
3. **It should restate, not merely imply, §11.4's "never produced for operational failures" sentence** — that sentence was violated before this round and is now true again, and the amendment is the place to record that it is once more load-bearing.
4. **It should name the transient sibling `parse/parse-report.operational-failure.tmp` and state that it may survive inside a retained staging directory if the atomic replacement itself fails.** That is W-1's blast radius, and an operator who finds the file needs the design record to explain it rather than treat it as corruption.

Recommendation: route the amendment **with those four additions**. It is an append-only design record; nothing above requires retracting the implementer's wording, only extending it.

---

## 8. CANNOT_VERIFY

Everything below is a claim I could not execute under the read-only boundary. None of it changes the verdict, because in each case I verified the underlying code by reading rather than by running. I name the command I would have run.

| Claim | Why not verified | Command I would have run |
|---|---|---|
| 356 passed, exit 0 | Running the suite writes to `.tmp/` and the pytest cache — state change | `.venv/Scripts/python -m pytest -q` with `PYTHONPATH` cleared |
| Golden suite 9 passed and the golden hash still `sha256:e5041dd…7e77e` | Same | `.venv/Scripts/python -m pytest -q tests/golden` |
| Working tree matches the materialised patch exactly, with no unstaged extras | Requires no state change, but I chose not to lean on it; I read the eight source/test files directly in the tree instead | `git status --porcelain` and `git diff --stat HEAD -- src tests` |
| Each reversion test actually fails when its fix is reverted | Requires editing source | Revert each hunk in a scratch copy, run the named test, expect failure |
| The 17/17 containment verifier result, including the `subst` cross-drive root | Creating a `subst` mapping is a state change | The orchestrator's verifier script against a `subst`-mapped root |
| `read(n)` transient allocation behaviour on this CPython build | Needs a measured run | `tracemalloc` around `extract_with_image_snapshot` on a small raster |
| R-1's exit-code behaviour end to end | Needs a run with a closed stderr | `python -m pwa.floorplan.cli … 2>&-` on a forced double-fault fixture, checking `$?` is 1 not 2 |

The orchestrator's verification document records the first two and the fifth as executed, and I have no reason to doubt them; I am marking them CANNOT_VERIFY because the dispatch asked me to distinguish what I proved from what I was told, and the report was explicitly not to be trusted.

---

## 9. Verdict and required follow-up

**VERDICT: ACCEPT.**

All three dispatched residues are CLOSED with reversion tests that pin routing and not merely outcome. No boundary was breached. Nothing the accepting NA-3f review established has regressed. `parse_run()` still never raises, including on the new double-fault path under adversarial input.

**One must-fix follow-up, not a blocker:**

- **R-1** — `src/pwa/floorplan/cli.py:34-35`. Move the stderr write inside the existing `try/except Exception: return 2` at `:20-33`, or wrap it in its own `except OSError: pass`. Without it, an `OSError` on stderr turns the documented exit 2 into an uncaught exception and exit 1, on exactly the path that reports a left-behind finalized run. Two lines. Fold it into NA-6.

**One accepted residual, explicitly not requiring a sixth round:**

- **W-1** — unreachable via `parse_run()` behind three independent conditions; worst case degrades to the pre-round state plus a `.tmp` file containing the truth. Optional one-line hardening at `builder.py:466` if the function is touched again.

**One routing action:**

- The design-record amendment should be appended with the four additions in §7 before it is considered closed.
