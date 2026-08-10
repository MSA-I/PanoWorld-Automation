<!-- Archived verbatim by the orchestrator. The reviewer wrote this document. Two mechanical
repairs were made to the captured text and nothing else: an OEM-codepage mangling of em dashes
introduced by the capture pipeline (PowerShell decoded the CLI's UTF-8 stdout as cp862), and the
removal of stray zero-width joiners the model emitted inside the word "cursor", which would
otherwise break every grep for that identifier. No wording was altered.

Runtime metadata, from the harness rather than from the reviewer's self-description:
  task: NA-3d, fourth independent review of PLAN-002 (round 4), second pass
  provider: anthropic
  requested_model: opus / claude-opus-5
  actual_model_id: claude-opus-5    (requested route honoured; no substitution)
  effort: not exposed by the CLI as a parameter separate from the model tag
  route: claude CLI, headless (-p), --strict-mcp-config, read-only allowlist, NO Bash tool
  session_id: 5d392e28-1a97-43ff-b3dc-8b19c6f67133
  turns: 37 | wall clock: 19.2 min | tokens in/out: 818,905 / 63,875
  cache read / creation: 1,255,235 / 602,942 | cost: USD 13.56
  permission denials: 0
  subject: branch panoworld-dev/na-3b-gc3-fixes, commit 6eaef17
  dispatch brief: evidence/PLAN-002/reviews/na3d-anthropic-review-dispatch-20260810.md

WHY THERE ARE TWO REVIEWS FOR THIS ROUND. The Opus 5 route was attempted first and returned HTTP
429 (rate limit, reset after 59m 54s) with zero tokens and no review, so Sonnet 5 ran instead and
its review is archived as independent-anthropic-rework3-review-20260810.md with VERDICT: ACCEPT.
This is the queued Opus pass, run after the window reopened. It reaches VERDICT: NEEDS_REWORK.
Both documents stand as written and neither has been edited. Where they disagree, the difference
in evidence is recorded rather than resolved by preference: the Sonnet pass was denied git-diff
access by an orchestrator error in its tool allowlist and judged only the current code, while this
pass received the full change set as a pre-materialised patch (diffstat plus the complete src/ and
tests/ diff 11ef553 -> 6eaef17) in a directory added to its workspace, and had no Bash tool at
all. That is the gap the orchestrator committed to closing, and it is closed here.

CORROBORATION, recorded because it bears on weight. Before this pass ran, the orchestrator
independently verified the Sonnet findings and ran a Windows path-aliasing experiment, writing the
results to orchestrator-verification-na3d-findings-20260810.md. This reviewer had no access to
that document - it was created after its dispatch brief and is not referenced in its prompt - and
arrived at the same two previously unreported defects by reading the code: its F-3 is the
orchestrator's O-NA3D-1 (drive-relative component defeats the write-side containment walk) and its
F-7 is O-NA3D-2 (alternate data stream smuggled through every containment check). Its F-1 is the
same defect the orchestrator raised as a severity upgrade over the Sonnet pass's F2. Two
independent routes, same conclusions; the orchestrator's document also carries the executable
proof-of-concept output for F-3 and F-7, which this reviewer could only predict because it had no
shell. Its predictions matched the measured results exactly.
-->

VERDICT: NEEDS_REWORK

## Runtime metadata (as reported by the harness, not self-described)

| Field | Value |
|---|---|
| Provider | Anthropic |
| Model name / id | Opus 5 / `claude-opus-5` |
| Reasoning effort | **not exposed to me by the harness.** The environment block states provider and model id but no effort value. Recorded in CANNOT_VERIFY rather than guessed. |
| Access | Real read-only filesystem access to the repository working tree, plus the materialised patch (diffstat + full `src/`+`tests/` diff `11ef553` → `6eaef17`) supplied outside the repository. |
| Tooling constraint | No shell. No git command was run by me. Every claim below rests on file reads; every command I would have run is named in the CANNOT_VERIFY section. |
| Skills | `/skills` invoked at dispatch; `code-review-checklist` and `file-path-traversal` applied (the latter targeted at the containment helpers in `src/pwa/floorplan/runs.py`, as the brief directs). |

## Why NEEDS_REWORK and not ACCEPT

Five of the eight gates are closed on the evidence, and the direction of the rework is right — the CRITICAL arbitrary-write escape is genuinely gone, and I could not break it. But two findings sit *inside* the gates this rework was commissioned to close, not outside them:

- **F-1** is a new defect introduced by GC3-2's own implementation: when the post-rename inventory check (the thing GC3-2 asked for) fails, the finalized run is left on disk, self-describing as `complete` with `cli_exit: 0`, while the API returns CLI 2. That is a direct violation of AC-4's atomicity clause, and the rework's own test for that gate is written so as not to see it.
- **F-2** is the residue of GC3-3 on the raster path. GC3-3's text is *"the raster's pixels and hash come from two separate reads of the same path"*. After the fix the staged raster is read **three** times, and the read that is hash-verified is still not the read whose pixels are embedded. The defect moved from the source run into staging; it was not eliminated.

F-1 and F-2 compose. Taken together they produce a finalized run directory whose overlay was rendered from bytes that no hash check ever covered, with a `parse-report.json` inside it that says `complete`, while the caller is told CLI 2. That is the outcome the staging/`os.replace` design exists to make impossible.

I also disagree with one line of the orchestrator's per-gate record: `GC3-2: "CLOSED"` and `GC3-3: "CLOSED by inspection"` do not survive contact with the code. Both are PARTIALLY_CLOSED. Everything else in the orchestrator's verification that I could check independently held up, and one hypothesis I formed against GC3-5 (that `scanned_before` carried only the modelspace count) was **wrong** — see the gate table.

## Findings

| ID | Severity | file:line | Claim |
|---|---|---|---|
| F-1 | MAJOR | `src/pwa/floorplan/runs.py:221` | A failed post-rename inventory check leaves the finalized run in place, reported as CLI 2, with `parse-report.json` inside it saying `complete`/`0`. |
| F-2 | MAJOR | `src/pwa/floorplan/annotation_source.py:60` | The staged raster is read three times; the hash-verified bytes are not the dimension-checked bytes and not the bytes embedded in the overlay or recorded as `source_sha256`. |
| F-3 | MAJOR (latent, not currently reachable) | `src/pwa/floorplan/runs.py:14` | `_contained_parts` accepts a Windows drive-relative component and the four write-side helpers omit the `resolve()`/`relative_to(root)` check the read-side helper has. |
| F-4 | MINOR | `src/pwa/floorplan/builder.py:1023` | Six staged write sites bypass the new checked helpers and use `mkdir(parents=True, exist_ok=True)`, so a mid-run junction at `staging_run/parse` or `staging_run/project` is followed. |
| F-5 | MINOR | `src/pwa/floorplan/runs.py:207` | `verify_run_inventory` covers only `payload.inputs`; neither the pre- nor the post-rename check touches the five derived envelopes, `parse/overlay.svg` or `parse/annotation.json`. |
| F-6 | MINOR | `src/pwa/floorplan/builder.py:684` | `MAX_ANNOTATION_BYTES` is enforced after the entire file has been read into memory, so the byte limit does not bound the read it names. |
| F-7 | MINOR | `src/pwa/floorplan/runs.py:14` | `name:stream` passes every containment check, so a manifest-declared NTFS alternate data stream is copied into the finalized run, invisible to directory listings. |
| F-8 | MINOR | `src/pwa/floorplan/annotation_source.py:59` | The annotation's `source_image_ref` is raw-joined onto `source_root`; containment for that value is only checked *after* `extract()` returns. |
| F-9 | INFO | `src/pwa/floorplan/dxf_worker.py:96` | Opaque-token numbering depends on `ezdxf` layout/entity iteration order; no test pins overlay bytes for a DXF with more than one unknown layout. |
| F-10 | INFO | `src/pwa/floorplan/builder.py:621` | The run-id/directory-name identity check compares the *caller's* spelling of the path, which on a case-insensitive volume need not equal the on-disk name. |
| F-11 | INFO | `src/pwa/floorplan/runs.py:106` | Nothing prevents a previous *parse* run from being used as a source run; a parse run satisfies every finality and identity predicate. |
| F-12 | INFO | `src/pwa/floorplan/builder.py:104` | `content_hash` is a keyless public function, so GC3-3/GC3-4 hold against a racing attacker but not against one who can write the source run before the parse starts. |
| F-13 | INFO | repository root | Two zero-byte junk files (`'` and `-,`) are untracked in the repository root per this session's git-status snapshot — disclosure #4's class recurred after the commit. |

---

### F-1 — MAJOR — `src/pwa/floorplan/runs.py:221`

```python
verify_run_inventory(staging_run, manifest)
os.replace(staging_run, final_run)
verify_run_inventory(final_run, manifest)    # line 222
```

The post-rename call is the check GC3-2 asked for. What is missing is what happens when it fails. It raises `ValueError("finalized inventory hash mismatch")`, which propagates out of `finalize_run`, out of the `try` opened at `src/pwa/floorplan/builder.py:779`, and into the handler at `builder.py:1069-1076`, which returns `_staged_operational_result(...)` → CLI 2. Nothing rolls back the rename.

`_staged_operational_result` then tries to record the failure at `staging_run/parse/parse-report.json`, but `builder.py:450` guards that write with `if staging_run.is_dir()` — and `staging_run` no longer exists, it was renamed away one line earlier. The write is silently skipped.

**Failure scenario.** A valid annotation run, `parse_run_id="RUN-A"`. The happy path writes `overlay.svg` and all five envelopes into staging (`builder.py:1022-1030`), including `parse/parse-report.json` with `"outcome": "complete"`, `"cli_exit": 0`, and `project/project_manifest.json` with `"status": "complete"`. `finalize_run` re-hashes staging (passes), renames staging to `runs/RUN-A`, then a declared inventory file under `runs/RUN-A/project/inputs/originals/` differs from its declared hash. Out:

- `parse_run()` returns `cli_exit=2`, `diagnostic.outcome="operational_failure"`, and `staging_run` pointing at a path that does not exist.
- `runs/RUN-A/` exists, fully populated, and `runs/RUN-A/parse/parse-report.json` reads `complete` / `0`.
- No report of the operational failure is written anywhere on disk.
- A retry with the same id now hits the `destination_exists` gate at `builder.py:537-549` and returns CLI 2 forever, with still no on-disk explanation.

Any downstream stage that enumerates finalized runs — the whole point of the staging/`os.replace` split — consumes a run whose inventory is *known* corrupt and whose own report says it is complete.

**Test evidence that this was not seen.** `tests/integration/test_plan002_parse_run.py:169-191` is the gate's test. It asserts exactly two things: `cli_exit == 2` and `diagnostic["outcome"] == "operational_failure"`. It does not assert `not result.final_run.exists()`. The test immediately following it, at line 194, is named `test_operational_failure_retains_staging_and_no_finalized_run` — so "operational failure ⇒ no finalized run" is this file's own stated invariant everywhere else. The gate test's name, `..._is_not_reported_complete`, is accurate about the *report object* and silent about the *directory*, which is where the damage is.

**Remediation shape** (not prescriptive): rename back, or write the run to a quarantine name, or verify before the rename only and treat a post-rename mismatch as a hard `raise` rather than a CLI-2 return — but the finalized directory must not be left claiming completeness.

---

### F-2 — MAJOR — `src/pwa/floorplan/annotation_source.py:60`

GC3-3's text names this exact defect. Counting reads of the staged floorplan raster on the annotation path, after the fix:

1. `src/pwa/floorplan/annotation_source.py:60` — `sha256_file(image_path)`, compared against `payload["image"]["sha256"]` and, at line 62, against the inventory entry. **This is the only integrity-checked read.**
2. `src/pwa/floorplan/annotation_source.py:64` — `with Image.open(image_path)`, whose `width`/`height` are compared to the annotation's declared dimensions at line 66.
3. `src/pwa/floorplan/builder.py:317` — `_source_binding` does its own `source_path.read_bytes()`. These are the bytes decoded at line 318, sanitized into the overlay at line 327, and hashed into `source_sha256` at line 334. That value is compared to nothing.

So the bytes proven to match the declaration are not the bytes whose dimensions are validated, and neither is the byte string that ends up embedded in `parse/overlay.svg` and recorded as the artifact's lineage hash.

The rework touched `annotation_source.py` in this very diff — the `document=` parameter at line 36 applies snapshot discipline to the annotation **JSON**. It was not applied to the raster the JSON points at.

**Failure scenario.** Threat model is the one GC3-1 already accepts: an attacker who can write under `runs_root` (GC3-1's own test plants a junction at `runs_root/.staging` before the run). Staging paths are fully predictable — `runs_root/.staging/<parse_run_id>/<manifest-declared path>`.

In: a valid annotation run. The attacker overwrites `runs_root/.staging/RUN-A/project/inputs/originals/floorplan.png` after read #1 completes at `annotation_source.py:60` and before read #3 at `builder.py:317`, substituting a same-dimensions raster with different content. Out:

- Read #1 passed: hash matches the manifest and the annotation.
- Read #2 passed: dimensions still match.
- `parse/overlay.svg` embeds the attacker's raster. `floorplan_parse.json`'s `source_sha256` is the attacker's hash. Nothing compares it to the declared inventory hash.
- `finalize_run` → `verify_run_inventory(staging_run, ...)` at `runs.py:220` *does* catch the drift and raises. So the run does not finalize — **unless** the attacker's write lands after that check and before/around the rename, at which point F-1 takes over and the corrupt run is finalized anyway while CLI 2 is reported.

**On the gate's own test.** `tests/unit/test_floorplan_builder.py:91-109` proves that swapping the file *inside* `_sanitize_raster_bytes` cannot split `_source_binding`'s hash from its pixels. That is true and worth having. It says nothing about the three-read structure spanning `annotation_source.py` and `builder.py`, which is the structure GC3-3 describes.

**The DXF path has the same shape for a different reason.** `DxfSource().extract(staged_floorplan)` (`builder.py:822`) checks the byte cap in the parent at `src/pwa/floorplan/dxf_source.py:57` and then parses in a *subprocess* that re-opens the path (`src/pwa/floorplan/dxf_worker.py:175`). The size gate and the parse are structurally different reads in different processes, and `_source_binding` adds a further `sha256_file` at `builder.py:364`. A single immutable snapshot is not achievable for DXF while the worker takes a path rather than bytes or an inherited descriptor. This is the honest reason GC3-3 cannot be marked CLOSED by inspection.

---

### F-3 — MAJOR (latent; no current call site reaches it) — `src/pwa/floorplan/runs.py:14`

```python
invalid_component = any(part in {"", ".", ".."} for part in candidate.parts)
if candidate.is_absolute() or not candidate.parts or invalid_component:
    raise ValueError("path must be a contained relative path")
```

On Windows, `PureWindowsPath("C:evil.txt")` is **not** absolute (drive, no root) and its `.parts` are `('C:', 'evil.txt')` — neither `""`, `"."` nor `".."`. It passes. Then in `validate_contained_destination` at `runs.py:32`, `cursor = cursor / part` with `part == "C:"` replaces the drive and discards `root` entirely; the function returns that cursor at line 36 with **no** `resolve()` + `relative_to(root)` re-check.

`resolve_contained_relpath` — the read side — *does* have that check, at `runs.py:172-177`. The four write-side helpers (`validate_contained_destination`, `create_contained_directory`, `resolve_contained_output`, `write_bytes_contained`) do not. That asymmetry is the finding.

The hazard is documented *in this diff*, by the implementer, at `src/pwa/floorplan/builder.py:50-54`: *"Joining a Path with an absolute or drive-relative operand silently discards the left-hand prefix (Path.__truediv__ semantics)"*. The insight was applied to `parse_run_id` via `_PARSE_RUN_ID_RE` (`builder.py:55`, which correctly excludes `:`) and not to the shared containment primitive.

**Reachability — stated precisely, because it changes the severity.** I traced every caller:

- `create_contained_directory(runs_root, Path(".staging") / parse_run_id)` and `validate_contained_destination(runs_root, parse_run_id)` (`builder.py:519-520`, `766-768`; `runs.py:217`) — `parse_run_id` has already passed `_PARSE_RUN_ID_RE`, which forbids `:`. Safe.
- `write_bytes_contained(staging_run, "project/source-manifest.json", …)` (`builder.py:781-782`, `787`) — constant literals. Safe.
- `resolve_contained_output(staging_run, item["path"])` in `copy_source_inventory` (`runs.py:184`) — the only attacker-influenced input. It is gated twice: `builder.py:645-657` runs `resolve_contained_relpath(source_run, item["path"])` over *every* inventory entry before staging begins, and `runs.py:183` runs it again per item. For `"C:evil.txt"` that helper's ancestor walk with `must_exist=True` fails, and even if the attacker pre-creates the target, the `relative_to` check at `runs.py:174-177` rejects it. Safe.

So **no current call site is exploitable.** I am reporting it MAJOR anyway because these four functions are named, documented and positioned as *the* containment chokepoint — the abstraction GC3-1 created for future callers to trust — and they do not contain. The next caller that passes a manifest-derived string without first routing it through the read-side helper reintroduces the CRITICAL that GC3-1 closed. Two one-line changes remove the class: reject any part containing `:` in `_contained_parts`, and add the `resolve()`/`relative_to(root)` check to `validate_contained_destination`.

---

### F-4 — MINOR — `src/pwa/floorplan/builder.py:1023`

```python
overlay_path = staging_run / "parse" / "overlay.svg"
overlay_path.parent.mkdir(parents=True, exist_ok=True)
with overlay_path.open("xb") as stream:
```

`staging_run/parse` was created and reparse-checked by `create_contained_directory` at `builder.py:768`. This site re-creates it with `exist_ok=True`, which succeeds silently against a junction. The five `write_json_exclusive` calls that follow (and the identical blocks at `builder.py:814-818`, `848-852`, `867-871`, `1046-1050`) do the same thing inside `src/pwa/files.py`, which calls `path.parent.mkdir(parents=True, exist_ok=True)`. `copy_immutable` in the same file does likewise.

**Failure scenario.** Between `builder.py:768` and `builder.py:1023`, an attacker with write access under `runs_root` replaces `runs_root/.staging/RUN-A/parse` with a junction to `C:\Users\<other>\Documents`. `mkdir(exist_ok=True)` returns quietly; `open("xb")` creates `overlay.svg` and the four JSON artifacts in the junction target. `O_EXCL` prevents clobbering an *existing* file at the leaf but does nothing about a redirected parent.

GC3-1's text is about the *creation* of the destination chain, and its own PoC plants the junction before the run — so this is outside the gate's literal scope and I am not marking GC3-1 short because of it. It is the residual half of the same hardening: staged directories are created through the checked helpers and then written through unchecked joins.

---

### F-5 — MINOR — `src/pwa/floorplan/runs.py:207`

```python
for item in manifest["payload"]["inputs"]:
```

Both inventory verifications — pre-rename at `runs.py:220` and post-rename at `runs.py:222` — iterate only the manifest-declared inputs. Not covered: `project/project_manifest.json`, `project/input_quality_report.json`, `project/source-manifest.json`, `project/source-quality-report.json`, `parse/floorplan_parse.json`, `parse/assumptions.json`, `parse/parse-report.json`, `parse/annotation.json`, `parse/overlay.svg`. Nor is any envelope's `content_hash` recomputed at finalisation, even though `floorplan_parse.json` carries the overlay's declared `sha256` at `builder.py:913` and never re-checks it.

**Failure scenario.** An attacker modifies `runs_root/.staging/RUN-A/parse/floorplan_parse.json` (changing a room polygon) after `builder.py:1028` writes it and before `finalize_run` at `builder.py:1031`. Both inventory checks pass — the inputs are untouched. `runs/RUN-A/` finalizes as `complete`, CLI 0, carrying geometry that no hash ever covered and whose own `content_hash` field is now internally inconsistent with its payload. GC3-2's post-finalization check is real but narrow; the run's *outputs* have no finalisation-time integrity check at all.

---

### F-6 — MINOR — `src/pwa/floorplan/builder.py:684`

```python
annotation_bytes = Path(annotation).read_bytes()   # 684
...
if len(annotation_bytes) > MAX_ANNOTATION_BYTES:   # 695
```

The whole file is materialised in memory before the cap that exists to prevent exactly that. `annotation` is an operator-supplied CLI path, so this is unbounded memory on our own process rather than an attacker primitive — the impact is a `MemoryError`, which is **not** in the handler tuple at `builder.py:1069-1076` and would escape `parse_run()`, breaking the same API contract GC3-7 exists to protect.

**Failure scenario.** Operator points `--annotation` at a 16 GB file (or a `\\?\` path to something pathological). In: that path. Out: the process allocates until it fails; if `read_bytes` raises `MemoryError`, it escapes `parse_run()` rather than returning CLI 2, and only `cli.main()`'s broad guard at `src/pwa/floorplan/cli.py:25` converts it. The gate's requirement was that `parse_run()` itself never raise.

Bounding the read (`open(...).read(MAX_ANNOTATION_BYTES + 1)`) fixes both the limit and the exception surface in one line. This is pre-existing, not introduced here, but it is inside GC3-7's and AC-18's stated scope so I am recording it.

---

### F-7 — MINOR — `src/pwa/floorplan/runs.py:14`

`PureWindowsPath("floorplan.png:payload").parts` is a single component `('floorplan.png:payload',)`. It is not absolute, not `..`, and `Path.exists()`/`lstat()` both succeed on an NTFS alternate data stream, so `is_link_or_reparse` sees nothing. `resolve(strict=False).relative_to(root)` also succeeds — the stream path is lexically under the root. Every containment check passes.

**Failure scenario.** An attacker with write access to the *source* run creates `project/inputs/originals/floorplan.png:payload`, declares it in `payload.inputs` with `kind: "other"` and its true `sha256`, and recomputes `content_hash` (see F-12 — the function is keyless, so this is free). In: that source run. Out: `copy_source_inventory` at `runs.py:184-185` copies the stream into `runs_root/.staging/RUN-A/project/inputs/originals/floorplan.png:payload`; `verify_run_inventory` re-hashes it and is satisfied; the run finalizes `complete`, CLI 0. The smuggled bytes are absent from `os.listdir`, absent from any recursive glob, and absent from `sha256_file` of the main stream — but present in the finalized run and in anything that archives it.

Pre-existing rather than introduced, and gated behind source-run write access, hence MINOR. Rejecting `:` in `_contained_parts` closes this and F-3 together.

---

### F-8 — MINOR — `src/pwa/floorplan/annotation_source.py:59`

```python
image_path = (source_root / image_ref) if source_root is not None else (Path(path).parent / image_ref)
```

`image_ref` comes from the annotation payload at line 51 and is joined onto `source_root` (which `builder.py:790` sets to `staging_run`) with no containment check of its own. The only thing standing between it and an arbitrary read is the membership test at line 52 against `source_inventory`, whose keys `builder.py:645-657` has validated.

The ordering is worth noting: `builder.py:794-797` calls `resolve_contained_relpath(staging_run, …source_image_ref)` — the right check — but *after* `extract()` has already returned, i.e. after `sha256_file` and `Image.open` have both opened the unchecked path. Correct today, backwards, and dependent on a caller two files away. `source_inventory=None` is still a supported call shape (line 35), and in that mode there is no gate at all.

---

### F-9 — INFO — `src/pwa/floorplan/dxf_worker.py:96`

`_opaque_name` numbers tokens by first-encounter order (`dxf_worker.py:26-31`), and first-encounter order is `document.layouts` iteration order (line 204) crossed with per-layout entity order (line 86). Both are `ezdxf` behaviours, not pinned by anything in this repository. For a DXF with two or more unknown layouts or layers, which token maps to which name — and therefore the bytes of `parse/overlay.svg` and the `source_ref` strings in `floorplan_parse.json` — depends on the installed `ezdxf` version's ordering guarantees.

AC-14 requires the overlay to be *"deterministic byte-for-byte"*. That property now has an undeclared third-party dependency, and no test covers a multi-unknown-layout DXF across repeated renders. The privacy property GC3-6 was asked for is delivered; the determinism cost is undocumented.

### F-10 — INFO — `src/pwa/floorplan/builder.py:621`

`source_manifest["run_id"] != source_run.name` compares against the name **as the caller spelled it**: `resolve_contained_run` returns the lexical cursor it walked (`runs.py:127`), not the resolved path. On a case-insensitive volume, `--source-run runs/RUN-A` opens the directory `runs/run-a` and `source_run.name` is `"RUN-A"`. If the manifest also says `"RUN-A"`, the identity check passes and every derived artifact records `source_run_id: "RUN-A"` for a directory named `run-a`. Lineage that a later stage resolves case-sensitively (an archive, a Linux consumer) will not find it. Fail-safe in the opposite direction, hence INFO.

### F-11 — INFO — `src/pwa/floorplan/runs.py:106`

GC3-4's finality predicate is "a direct child of `runs_root` whose name does not start with `.`", plus `source_quality["status"] == "complete"` (`builder.py:635`). A previously finalized **parse** run satisfies all of it: its `project/project_manifest.json` is `status: "complete"` with `run_id == <its own directory name>` (`builder.py:890`), its `input_quality_report.json` matches (`builder.py:902`), its `payload.inputs` are inherited verbatim from its own source (`builder.py:886`), and `copy_source_inventory` has already populated every declared path inside it. So `parse_run(source_run=<a parse run>)` succeeds and chains. Whether that is intended is a plan question, not a code defect — flagging it because "source-run finality" is GC3-4's stated subject and nothing distinguishes an intake run from a parse run.

### F-12 — INFO — `src/pwa/floorplan/builder.py:104`

`compute_content_hash` takes only the document (`builder.py:99-104`: placeholder hash, then compute, then validate). No key, no signature. So `content_hash` is a transport-integrity check, not an authenticity check, and an attacker who can write the source run can produce a manifest, quality report and inventory that are mutually consistent and pass every check in `parse_run` — including the GC3-4 identity block and `verify_run_inventory`.

This bounds what GC3-3 and GC3-4 can be said to guarantee: they defeat a *concurrent* attacker racing the pipeline, which is real and worth having, but not an attacker who owned the input before the run started. Worth recording explicitly because the per-gate record reads as though the fixes establish input authenticity, and they cannot.

### F-13 — INFO — repository root

The session's git-status snapshot lists `?? '` and `?? -,` as untracked files in the repository root. These are not part of `6eaef17`, so they are not a finding against the commit — but disclosure #4 records three files of exactly this class being created and deleted during NA-3b, and two more now exist. The pattern is recurring, and the accepted GC3-9 deviation means this repository is public.

---

## Per-gate verdicts

| Gate | Verdict | Basis (file:line) |
|---|---|---|
| GC3-1 (CRITICAL — destination ancestor containment incl. `.staging`) | **CLOSED** | `runs.py:39-56` creates one checked component at a time and re-checks each for reparse-ness after `mkdir()`; `runs.py:20-36` walks every existing component lexically before any `resolve()`; `builder.py:766-778` routes staging creation through it under `except (OSError, ValueError)`. I attacked this with drive-relative components, trailing dots/spaces, ADS and case folding and could not reach an out-of-`runs_root` write **through a reachable call path** — `_PARSE_RUN_ID_RE` (`builder.py:55`) and the read-side gate at `builder.py:645-657` hold every input. F-3 and F-4 are hardening gaps against the helper and the write sites, not a re-opening of the escape. |
| GC3-2 (inventory copy root + post-finalisation check) | **PARTIALLY_CLOSED** | Copy root fixed: `runs.py:184` uses `staging_run` as root, so staged copies land where `derived_manifest` declares them (`builder.py:886` inherits `payload.inputs` verbatim) — this closes the "project/project/…" defect and makes `verify_run_inventory` resolvable. Post-finalisation check added: `runs.py:222`. **But** its failure path leaves the finalized run in place while returning CLI 2 (F-1), and it covers only `payload.inputs` (F-5). The gate's literal text ("add a post-finalization check") is satisfied; the invariant it exists to protect is not. |
| GC3-3 (one immutable snapshot per untrusted input) | **PARTIALLY_CLOSED** | Genuinely closed for three of four inputs: manifest and quality report are read once as bytes and both parsed and staged from those bytes (`builder.py:558-561` → `781-782`); the annotation JSON likewise (`builder.py:684`, `707`, `787-792`, and the new `document=` parameter at `annotation_source.py:36-39`); the source-run DXF swap-after-copy is defeated because parsing now reads the staged copy (`builder.py:783`, `822`). **Not** closed for the raster: three separate reads, only one hash-checked (F-2). Not achievable as written for DXF: the byte cap is checked in the parent (`dxf_source.py:57`) and the parse happens in a subprocess that re-opens the path (`dxf_worker.py:175`). This is the gate the brief told me to assume was weakest, and it is. |
| GC3-4 (source-run finality and identity) | **CLOSED** for all four stated requirements | Direct non-dot child of `runs_root`: `runs.py:106-107`. Manifest/quality same project and run, and run id equal to the directory name: `builder.py:619-621`. Exactly one `kind == "floorplan"`: `builder.py:622` with `floorplan_entries` from `builder.py:616`. Unique inventory paths: `builder.py:623`. I checked whether the identity block could raise `KeyError`/`TypeError` on a schema-valid manifest — it cannot: `schemas/project_manifest/v1/project_manifest-1.0.0.schema.json:26-38` requires `path`/`sha256`/`kind`, types them, and sets `additionalProperties: false` with `minItems: 1`. Residual gaps are INFO only: F-10 (case), F-11 (parse-of-parse), and exact-string uniqueness means `x.png` and `x.png ` are distinct declarations — but the second copy then fails `FileExistsError` → `OSError` → CLI 2, i.e. fail-safe. |
| GC3-5 (cumulative `MAX_DXF_ENTITIES`, mapped to `PARSE_RESOURCE_LIMIT`) | **CLOSED** | `dxf_worker.py:87-88` compares `scanned_before + scanned`. **I formed and then disproved a hypothesis here**, and record it because it bears on how the code reads: `dxf_worker.py:208` is `scanned_entities += _scan_layout(..., scanned_before=scanned_entities, ...)`, which looks like every extra layout receives the modelspace-only baseline. It does not — Python evaluates the argument before the `+=` store, and `scanned_entities` has already absorbed all previous layouts, so layout *n* correctly sees the running total. Accumulation across multiple paperspace layouts is genuinely cumulative. The mapping also composes end-to-end, contrary to disclosure #3's caution: `dxf_worker.py:246-248` converts the `ValueError` into `fatal_error_code`, `dxf_source.py:124-125` converts that into `FloorplanError("PARSE_RESOURCE_LIMIT")`, and `builder.py:372` puts that code in `_FAILED_DOMAIN_CODES` → CLI 3 with a failed artifact set. The cap is off-by-nothing: `MAX_DXF_ENTITIES` total entities are permitted and the next one raises, consistent between the pre-check at `dxf_worker.py:177` and the loop. |
| GC3-6 (no free-text DXF layout/layer names in artifacts) | **CLOSED** | `dxf_worker.py:93-99`: `layout.name` passes through only for the literal `"Model"`, `layer` only for `_KNOWN_LAYERS` (`dxf_worker.py:16`, our own reserved names), everything else becomes `unknown-layout-NNNN` / `unknown-layer-NNNN`. I checked every consumer of the layer/layout strings in that file — `_unmapped` (line 46), `_unsupported` (lines 109/118/122/136/139/155), and the `source_ref` at line 99 — and all use the tokenised values. `labels` in the overlay derive from `raw.unmapped[*].source_ref` (`builder.py:339`, `366`), so tokens propagate to `overlay.svg`. The DXF entity `handle` still appears verbatim; it is file-structural, not client free-text. F-9 is a determinism note, not a leak. |
| GC3-7 (every preflight/staging filesystem failure returns CLI 2, never raises) | **CLOSED**, with a named residue | Per-stage handlers now cover `resolve_contained_run` (`builder.py:496`), the containment re-proof (`521`), manifest/quality read+decode+parse (`562`, including `RecursionError`), the inventory containment loop (`648`), the floorplan resolve (`661`), the annotation read (`685`) and parse (`708`), staging creation (`769`), and `validate_artifact`'s own `ValueError`/`KeyError` (`581`, `717`). The outer tuple is at `builder.py:1069-1076`. I attacked the tuple as instructed: `subprocess.TimeoutExpired` is converted at `dxf_source.py:89-91`; a worker crash from `ezdxf.DXFStructureError`, `struct.error`, `zlib.error` or `RecursionError` exits non-zero and is converted to `ValueError` at `dxf_source.py:92-94`; `taskkill` failing raises `OSError`, which is caught; `KeyError`/`TypeError` on manifest access are excluded by the closed schemas; deep-nesting `RecursionError` is caught at the `json.loads` sites and cannot arise later because every schema in `schemas/` sets `additionalProperties: false` with fully-typed leaves, bounding validated document depth. The residue is `MemoryError` reachable via F-6, which is not in the tuple. `cli.py:25`'s broad guard is retained deliberately and documented at `cli.py:28-29`; that is by design, not a gap. |
| GC3-11 (`DecompressionBombError` escaping the narrowed handler) | **CLOSED** | `builder.py:1074-1075` adds both `Image.DecompressionBombError` (a direct `Exception` subclass, which is why it escaped) and `Image.DecompressionBombWarning`. Both raster open sites — `annotation_source.py:64` and `builder.py:318` — are inside the `try` opened at `builder.py:779`, so both are covered. |

## Disclosure judgments

**Disclosure 1 — the removed pre-staging inventory hash check. Verdict: CORRECTION, with a cost that should be recorded.**

This is the call the brief assigns to me, so here is the reasoning rather than the conclusion alone.

*Why it is a correction.* The removed loop performed a second `sha256_file()` read of the source file, and `copy_immutable` (`src/pwa/files.py`) then read it a third time to copy it. Keeping the check would have meant keeping the exact two-read structure GC3-3 exists to eliminate — and worse, it would have made the *checked* read not the *copied* read. What replaced it is strictly stronger: `copy_immutable` digests the same chunks it writes and returns that digest, and `runs.py:189` compares that digest against the immutable declaration. One read of the source, hash of exactly those bytes, compared to the declaration. That is the right shape.

*Why the rewritten test is not the tail wagging the dog.* I checked the contract the test is supposed to protect rather than taking either report's word. AC-20's approved preflight semantics require, verbatim, *"every pre-parse source hash mismatch is `PARSE_SOURCE_HASH_MISMATCH` + CLI 2 + no finalized derived run"*. All three still hold, and I verified the mechanism independently: `PARSE_SOURCE_HASH_MISMATCH` is **absent** from `_FAILED_DOMAIN_CODES` (`builder.py:370-386`), so the `FloorplanError` raised at `runs.py:190` takes the `builder.py:1061-1068` branch — `_staged_operational_result`, CLI 2, `finalize_run` never called. `tests/integration/test_plan002_parse_run.py:356+` asserts the code and CLI 2. AC-20 never constrained staging, so the changed assertion (`staging_run.is_dir()` instead of `not staging_run.exists()`) does not relax an approved property. Moshe's approved semantics are intact.

*The cost, which the disclosure states accurately and which I would have the record keep.* Hash-mismatching — i.e. untrusted, unverified — bytes are now written under `runs_root/.staging/<id>/` before rejection, and retained there indefinitely because staging is deliberately kept on operational failure. The old code rejected before writing anything. That is a real enlargement of blast radius on a security-relevant path, and it is invisible in the diff unless you read the test rename. I would ask for the staging tree to be removed on this specific failure, or for the disclosure text to become a comment at `runs.py:186-194` so the next reader does not re-add the second read.

**Disclosure 2 — the `f-hostile-label` assertion flip. Verdict: ACCEPTABLE, with a real coverage loss to close.**

Asserting the hostile name is absent and a token present is the stronger property, and it is the property GC3-6 asked for. But it retires the only test that exercised XML escaping in `src/pwa/floorplan/overlay.py`. Escaping is still needed — tokenisation covers DXF layout/layer names, not every string that can reach the overlay — and it is now untested, so a regression there is silent. This is a coverage gap, not a defect: I would ask for one direct unit test on the escaping path so both properties are pinned.

**Disclosure 3 — the GC3-5 test reaching CLI 3 through an in-process `DxfSource.extract` substitute. Verdict: ACCEPTABLE, honestly disclosed, and less serious than the disclosure suggests.**

The disclosure is right that no single test spans both halves. But I traced the real subprocess path by hand and the two halves do compose correctly: `dxf_worker.py:88` raises `ValueError("PARSE_RESOURCE_LIMIT")` → `main()` at `dxf_worker.py:246-248` catches `ValueError` and writes `fatal_error_code` with exit 0 → `dxf_source.py:124-125` raises `FloorplanError("PARSE_RESOURCE_LIMIT")` → `builder.py:372` classifies it failed-domain → CLI 3 with the failed artifact set. The gap is one end-to-end test, not a behavioural risk. Worth adding, not worth blocking on.

**Disclosure 4 — the three junk files. Verdict: NOT A CODE MATTER, but the class recurred.**

Deleting them before committing was right. Per the session's git-status snapshot, two more (`'` and `-,`) are untracked in the repository root now (F-13). Given GC3-9's decision made this repository's evidence public, the recurring pattern deserves a guard — a pre-commit check for zero-byte files with non-identifier names would cost less than the next round of disclosure.

## Acceptance-criteria re-assessment

I changed a verdict only where I have direct file evidence, and said CANNOT_VERIFY otherwise. AC text is from `docs/plans/PLAN-002-floorplan-parsing.md`.

| AC | NA-3 | Mine | Basis |
|---|---|---|---|
| AC-4 — *derived parse run finalizes atomically; existing IDs/paths, stale staging and overwrite attempts fail safely* | NOT MET | **NOT MET** (new reason) | The second clause is now well covered: `builder.py:537-549` rejects an existing final or staging path, `runs.py:218-219` re-checks at finalisation, and `create_contained_directory` raises `FileExistsError` on an occupied leaf (`runs.py:51`). The **first** clause fails on F-1: a failed post-rename verification leaves a finalized run while reporting CLI 2. Atomicity means the finalized directory exists only when the run succeeded, and it can now exist when the run failed. |
| AC-13 — *parse and assumptions validate, hashes recompute, provenance present on every emitted entity* | NOT MET | **CANNOT_VERIFY** (moved in the right direction) | Positives I confirmed: `_artifact` recomputes `content_hash` and hard-fails on schema errors (`builder.py:104-107`); every room, wall and opening carries `confidence` and `provenance` (`builder.py:914-944`); GC-4 added the annotation's `artifact_id`/`content_hash` to the parse artifact's `inputs` (`builder.py:956`). What I cannot settle: "PLAN-002-required provenance" is not enumerated in the AC line, and I do not have NA-3's specific basis for NOT MET, so I cannot say the requirement is now fully met. Not a defect I can name — an assessment I cannot close. |
| AC-14 — *source-aligned overlay shows source and detections, deterministic byte-for-byte, XML-valid, no active/external content* | NOT MET | **PARTIALLY MET / CANNOT_VERIFY** | "No active/external content" is well served: the raster is re-encoded through Pillow with pinned settings (`builder.py:306-312`), which drops metadata, and `dxf_worker.py:22` blocks `IMAGE`/`INSERT`/`OLE2FRAME`/`XREF` regardless of layer. "Source-aligned" is real since M-4 built the source primitives from the raw adapter output (`builder.py:349-361`). "Deterministic byte-for-byte" now carries the undeclared `ezdxf`-ordering dependency of F-9, and confirming byte-determinism requires running the golden test, which I could not do. |
| AC-15 — *hostile labels are escaped; private source data never enters tracked evidence* | NOT MET | **NOT MET as written** (residue is a decision, not a defect) | First clause: hostile DXF names can no longer reach artifacts at all (`dxf_worker.py:98`), which is better than escaping — but the escaping itself is now untested (disclosure 2). Second clause: falsified by the GC3-9 accepted deviation, which places the OS account name in tracked evidence in a public repository. That is Moshe's recorded decision of 2026-08-10 and I am not re-opening it; the AC text simply does not match the accepted state. This should be reconciled by amending the AC or recording it as an accepted deviation against AC-15, not by code. |
| AC-17 — *traversal, ancestor reparse point and source hash mismatch fail before parsing* | NOT MET | **MET** | All three clauses now hold on the read path. Traversal: `runs.py:154` rejects absolute and `..`, `runs.py:174-177` re-proves containment after `resolve()`, and `builder.py:645-657` applies it to every inventory entry before staging. Ancestor reparse point: checked per component at `runs.py:33-35`, `runs.py:111-114` and `runs.py:151-152`, always on the *lexical* cursor before `resolve()` can substitute it away — I attacked this specifically and the ordering is correct. Source hash mismatch before parsing: `copy_source_inventory` (`runs.py:181-194`) runs at `builder.py:780`, before any adapter `extract()` at `788` or `822`. F-3's write-side asymmetry is a hardening gap on a path AC-17 does not name, and F-7's ADS channel needs source-run write access, so neither falsifies the AC. |
| AC-18 — *over-size input fails pre-parse; timeout/entity/vertex/count limits fail with exact codes* | NOT MET | **MET for the code-mapping clause; the byte caps are weaker than they read** | Codes are exact and correctly classified: `PARSE_RESOURCE_LIMIT` (cumulative entities, `dxf_worker.py:88`; DXF bytes, `dxf_source.py:58` and `builder.py:754`; annotation bytes, `builder.py:696`; overlay bytes, `builder.py:855-861`) and `PARSE_TIMEOUT` (`dxf_source.py:91`), all in `_FAILED_DOMAIN_CODES` → CLI 3. Over-size does fail pre-parse. The qualifications: the annotation cap is applied after the whole file is in memory (F-6), and the DXF cap is checked on reads that are not the parse read (F-2). |
| AC-20 — *failure decision table tests exact code, severity, finalized-artifact presence/status and CLI exit, including the three approved preflight cases* | NOT MET | **PARTIALLY MET** | All three approved preflight cases verified in code: hash mismatch → `PARSE_SOURCE_HASH_MISMATCH` + CLI 2 + no finalized run (`builder.py:370-386` + `1061-1068`); incomplete or blocked source quality → CLI 2 + no finalized run (`builder.py:635-644`); complete and blocker-free but missing or contradictory scale → `PARSE_SCALE_UNKNOWN` + failed diagnostic set + CLI 3 (`builder.py:800-820`). The clause that fails is *"finalized-artifact presence/status"*: F-1 produces a case where a finalized artifact set is present and reads `complete` while the CLI exit is 2, and no row of the table covers it. |
| AC-23 — *no H200/GPU/remote/cloud/network action occurred; G7/G8 remain deferred* | WEAK | **still WEAK** | Nothing in this diff adds network, GPU or remote behaviour — the only process launches are `sys.executable -m pwa.floorplan.dxf_worker` (`dxf_source.py:27`) and `taskkill` (`dxf_source.py:40`), both local, with `stdin=DEVNULL` and a bounded timeout. But the rework adds no *positive* evidence either: no test asserts the absence of egress, and "WEAK" was about the evidence, not the behaviour. Unchanged. |

## CANNOT_VERIFY

Everything here is a gap in my evidence, not a hedge on a finding. Each item names the command I would have run.

1. **Suite result (338 passed, exit 0; baseline 316).** Not run — no shell. → `uv run pytest -q`
2. **Golden canonical-projection hash unchanged** (`sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e`). Requires test execution. → `uv run pytest tests/golden -q`
3. **Working tree equals `6eaef17` for `src/` and `tests/`.** I read `runs.py`, `builder.py`, `dxf_worker.py`, `dxf_source.py` and `annotation_source.py` in the working tree and they agree with the materialised patch on every changed hunk I examined; I could not prove byte equality, and I read the four test files only through the patch plus targeted working-tree greps. → `git diff --stat 6eaef17 -- src tests` (expect empty) and `git status --porcelain`
4. **`pyproject.toml`/`uv.lock` byte-identical to `main`; `schemas/`, `contracts/`, `docs/` untouched.** → `git diff --stat 11ef553 6eaef17 -- pyproject.toml uv.lock schemas contracts docs` (expect empty)
5. **F-1, the finding the verdict rests on.** Two checks, both cheap:
   - Append `assert not result.final_run.exists()` after `tests/integration/test_plan002_parse_run.py:191` and run `uv run pytest tests/integration/test_plan002_parse_run.py::test_post_finalization_inventory_hash_drift_is_not_reported_complete -q`. **Expected: FAIL** — the finalized run exists.
   - In the same test, after the `parse_run` call, print `sorted(p.relative_to(result.final_run).as_posix() for p in result.final_run.rglob("*"))` and `json.loads((result.final_run / "parse" / "parse-report.json").read_text(encoding="utf-8"))["outcome"]`. **Expected: a fully populated run and `"complete"`.**
6. **F-3, drive-relative escape through the write-side helpers.** In a scratch directory, not the repository: `python -c "from pathlib import PureWindowsPath as P; print(P('D:/x')/'C:evil.txt', P('C:evil.txt').is_absolute(), P('C:evil.txt').parts)"` — expected `C:evil.txt False ('C:', 'evil.txt')`. Then call `write_bytes_contained(<a tmp dir>, "C:pwa-escape-probe.txt", b"probe")` and report where the file landed. **Expected: created relative to the process CWD on drive `C:`, outside the root.** Delete the probe afterwards.
7. **F-7, ADS smuggling.** Call `write_bytes_contained(<tmp>, "floorplan.png:payload", b"smuggled")` after creating `floorplan.png`, then report `os.listdir(<tmp>)`, `sha256_file(<tmp>/"floorplan.png")` before and after, and `Path("<tmp>/floorplan.png:payload").read_bytes()`. **Expected: the stream is readable, the listing does not show it, the main-stream hash is unchanged.**
8. **F-2's exploitable window.** Proving the interleaving needs a harness the orchestrator already noted it does not have. A partial check: monkeypatch `pwa.floorplan.annotation_source.sha256_file` to overwrite the staged raster with a same-dimensions, different-content image after returning the original digest, then report `result.cli_exit`, whether `result.final_run` exists, and whether the raster embedded in `parse/overlay.svg` is the substituted one. My prediction is CLI 2 with the drift caught at `runs.py:220` — which is the pre-rename check, so the F-1 composition needs the substitution to land after that line instead.
9. **F-9, overlay determinism across `ezdxf` versions.** Needs a second `ezdxf` version installed; out of reach here and arguably out of scope for this round. A cheaper partial: render a DXF with two unknown layouts twice in one process and confirm identical bytes (necessary, not sufficient).
10. **My own reasoning-effort value.** The harness did not report it to me. It should be taken from the dispatch record, not from this document.
11. **AC-13's provenance-completeness clause and AC-14's byte-determinism clause.** Both need artifacts I cannot generate read-only. Marked CANNOT_VERIFY in the table rather than guessed.
12. **GC3-8, GC3-9, GC3-10.** Not re-opened, per the brief. I found nothing in this diff that makes any of them worse. GC3-6's tokenisation strictly reduces what GC3-9's accepted deviation exposes going forward.

This review does not decide merge. Merge requires Moshe's separate authorisation, and G1 additionally requires the human visual gate GC3-10 / NA-4. My recommendation for the next round is narrow: **F-1 and F-2 are in scope because they are the unclosed halves of GC3-2 and GC3-3; F-3 plus F-7 close together in two lines of `_contained_parts` and `validate_contained_destination`; F-4, F-5, F-6 and F-8 are cheap and independent.** F-9 through F-13 are records, not work items.
