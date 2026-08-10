# PLAN-002 — Independent Anthropic code/security/contracts review

- Date: 2026-08-10
- Reviewer role: independent cross-provider code/security/contract reviewer (policy `MODEL-ROUTING-v1`)
- Worktree under review: `.worktrees/t_b7ade39e`, branch `panoworld-dev/t_b7ade39e-p1-02-floorplan-parsing`, **uncommitted working-tree state**
- Authoritative contract: `docs/plans/PLAN-002-floorplan-parsing.md` (read in full, 594 lines)
- Scope: code, security, contracts (§5, §11, §12, §14, §16). Spatial/geometry correctness is covered by a peer agent; geometry items are flagged where they overlap.

```text
PROVIDER: anthropic
MODEL: Opus 5
MODEL_ID_EXACT: claude-opus-5
EFFORT_NORMALIZED: HIGH
EFFORT_PROVIDER_VALUE: session-inherited
THINKING: independent adversarial code/security/contract review
MODEL_REASON: cross-provider review of OpenAI-authored implementation (author gpt-5.4 via headroom runtime)
FALLBACK_PROVIDER: none — blocked if unavailable (not exercised)
CROSS_PROVIDER_REVIEWER: human Moshe approval
```

---

## 1. Skills loaded (PLAN-002 §17 mandatory dispatch step)

Skill discovery tooling (`ListSkills` / `SearchSkills`) was loaded via `ToolSearch`, and the
following skills were invoked with the `Skill` tool **before** any review work:

| Skill | Loaded | Use in this review |
|---|---|---|
| `code-reviewer` | yes | severity taxonomy, structured findings, security-first review ordering |
| `security-audit` | yes | path traversal / file-path-traversal, XSS-in-markup, resource-cap and sandbox checklist |
| `python-patterns` | yes | module boundaries, exception strategy ("no stack traces to users"), typing/determinism review |
| `production-code-audit` | yes | production-readiness checklist, error-handling and leakage checks |
| `api-security-best-practices` | **not loaded — deliberately** | PLAN-002 §3/§12 forbid all network surface; there is no API/endpoint in scope. Loading it would have added no falsifiable check. |

Note on a skill-vs-mandate conflict: `production-code-audit` instructs the agent to *fix issues
automatically and not ask*. That instruction was **not followed** — the dispatch brief mandates
read-only review. No implementation file was modified. The only file written by this review is
this report.

---

## 2. Verdict

# `NEEDS_REWORK`

Justification: the primary containment control named in §12 and AC-17 (`resolve_contained_run`) is
**fully bypassable through the documented CLI argument**, proven end-to-end below; a second,
independent containment gap exists on manifest-supplied inventory paths; two reachable code paths
raise **uncaught Python exceptions out of `parse_run()`** (including one that prints an absolute
Windows path), which §11 requires to be CLI 2; and finalized failed-domain runs publish a **false
overlay binding** to a file that is never written. AC-12, AC-15 and AC-17 are NOT MET.

The work is otherwise of high quality: the run lifecycle, exit-code decision table, exact-version
catalog, determinism and the overall test suite are real and mostly well built. The failures are
concentrated and fixable; this is not a structural rejection.

---

## 3. Counts

| Severity | Count |
|---|---|
| CRITICAL | 1 |
| MAJOR | 11 |
| MINOR | 10 |
| INFO | 4 |

---

## 4. Findings table

| ID | Sev | Location | Summary |
|---|---|---|---|
| C-1 | CRITICAL | `src/pwa/floorplan/runs.py:11-31` | Absolute `--source-run` containing `..` escapes `runs_root`; containment check is lexical and skipped for absolute paths |
| M-1 | MAJOR | `src/pwa/floorplan/builder.py:392-406`, `runs.py:34-36`, `files.py:27-31` | Manifest-supplied `inputs[].path` is never containment-checked; reparse-point check covers only the leaf, not the ancestor chain |
| M-2 | MAJOR | `src/pwa/floorplan/builder.py:157-159` via `692-702` | `units == "unknown"` + DXF raises `ValueError` **inside the `except FloorplanError` handler** → uncaught exception escapes `parse_run()` |
| M-3 | MAJOR | `src/pwa/floorplan/builder.py:346-349` | Missing/malformed source manifest raises `FileNotFoundError`/`JSONDecodeError` out of `parse_run()` with an absolute path in the message |
| M-4 | MAJOR | `src/pwa/floorplan/builder.py:198` | Failed-domain runs finalize `floorplan_parse` with `overlay.path="parse/overlay.svg"` and an all-zero sha256 for a file that is never written |
| M-5 | MAJOR | `src/pwa/floorplan/dxf_source.py:62-65` | Timeout kills only the direct child; no process-group/tree kill on Windows or POSIX. "Worker forbidden to spawn children" is unenforced |
| M-6 | MAJOR | `src/pwa/floorplan/dxf_source.py:72` | Worker **data** channel is truncated at `MAX_WORKER_STDIO_BYTES` (1 MiB) → legal DXFs within `MAX_WALLS`/`MAX_DXF_ENTITIES` fail as "malformed JSON" / CLI 2 |
| M-7 | MAJOR | `src/pwa/floorplan/dxf_worker.py:66-74` | `IMAGE`/`OLE2FRAME`/`INSERT`/`ARC`/`SPLINE` on an **unknown** layer (e.g. `0`) is downgraded to a warning, contradicting the §6 disposition table |
| M-8 | MAJOR | `tests/unit/test_contract_versions.py:104-130` | The test that claims to prove duplicate `(schema_id, schema_version)` / `$id` rejection never reaches those branches |
| M-9 | MAJOR | evidence + tests | AC-3 (source run unchanged) has **no** assertion anywhere; traceability cites a non-existent test name for AC-5 |
| M-10 | MAJOR | `evidence/PLAN-002/acceptance.md:10`, `implementation/runtime-metadata.json:15`, `implementation/codex-followup-prompt.md:11` | Absolute Windows paths and the OS user name `art1` are staged into tracked evidence |
| M-11 | MAJOR | `src/pwa/floorplan/overlay.py:150-151,105-106,161-162` | DXF overlay never draws rooms or doors; `ids` and `confidence` groups are always empty in both renderers |
| M-12 | MAJOR | `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md` | Prior approved evidence rewritten in place (906+/309−) during implementation |
| m-1 | MINOR | `contracts/error_codes.md:44` | cp1255 mojibake `ג€”` instead of an em dash in the appended section heading |
| m-2 | MINOR | `src/pwa/contracts.py` `validator_for()` | `schema_version=None` path calls `load_all_schemas()` with no dir, ignoring a caller-supplied catalog's origin |
| m-3 | MINOR | `.tmp/` | Untracked scratch tree, not gitignored, outside the §16 ownership list |
| m-4 | MINOR | `src/pwa/floorplan/overlay.py:72` | Data URI hardcodes `image/png` for JPEG sources |
| m-5 | MINOR | `src/pwa/floorplan/validate.py:197` | `and` instead of `or` in the "at least one usable wall **and** room" invariant (§8.1) |
| m-6 | MINOR | `src/pwa/floorplan/validate.py:78-79` | `candidates[0]` comparison yields a false `PARSE_OPENING_OFF_WALL` (wrong code) when a declared wall is a valid but non-first candidate |
| m-7 | MINOR | `src/pwa/floorplan/builder.py:516-517` | Every `ValueError` from `render_overlay` is coerced into `PARSE_RESOURCE_LIMIT` and finalized |
| m-8 | MINOR | `schemas/floorplan_annotation/v1/...:16-19` | `relpath` pattern does not reject Windows backslash traversal |
| m-9 | MINOR | `src/pwa/floorplan/dxf_source.py:38-59` | Worker stdout/stderr temp files are capped on read, not on write |
| m-10 | MINOR | `tests/fixtures/contracts/examples.json` | Wholesale reformat of pre-existing examples beyond the additive requirement |
| i-1 | INFO | `src/pwa/floorplan/normalize.py:256-277` | `PARSE_LOW_CONFIDENCE` is unreachable in the real pipeline (all confidences are 1.0/0.9/0.6) |
| i-2 | INFO | `src/pwa/floorplan/normalize.py:39-40` | NaN/inf coordinates are reported as `PARSE_RESOURCE_LIMIT` |
| i-3 | INFO | `src/pwa/floorplan/dxf_worker.py:192-195` | `ezdxf.DXFStructureError` is not a `ValueError`; worker traceback reaches stderr (contained, never surfaced to artifacts) |
| i-4 | INFO | governance | `production-code-audit` skill instructed auto-fixing; read-only mandate was followed instead |

---

## 5. Findings in detail

### C-1 — CRITICAL — containment bypass: absolute `--source-run` with `..` escapes `runs_root`

**Location:** `src/pwa/floorplan/runs.py:11-31`

```python
def resolve_contained_run(runs_root: Path, candidate: Path) -> Path:
    runs_root = Path(runs_root).resolve(strict=True)
    candidate = Path(candidate)
    if not candidate.is_absolute():                       # <-- guard is relative-only
        if any(part == ".." for part in candidate.parts):
            raise ValueError("source_run must stay within runs_root")
        candidate = runs_root / candidate
    try:
        relative = candidate.relative_to(runs_root)       # <-- purely LEXICAL, never resolved
    except ValueError as exc:
        raise ValueError("source_run must stay within runs_root") from exc
```

`candidate` is **never** `.resolve()`d. `Path.relative_to()` is a lexical operation, so
`C:\...\runs\..\secret\evil-run` is happily reported as relative to `C:\...\runs` with parts
`('..', 'secret', 'evil-run')`. The ancestor loop then walks `runs_root / '..' / 'secret' / ...`,
each component of which exists and is not a reparse point, and returns a path outside `runs_root`.

**Proven, not inferred** (executed against the worktree source):

```
attack arg        : C:\...\Temp\pwa-poc-euvb_2rd\runs\..\secret\evil-run
RESULT: ACCEPTED -> C:\...\Temp\pwa-poc-euvb_2rd\runs\..\secret\evil-run
resolved.resolve(): C:\...\Temp\pwa-poc-euvb_2rd\secret\evil-run
ESCAPES runs_root : True
```

**Concrete failure scenario.** Operator (or any wrapper/automation) runs:

```
python -m pwa.floorplan.cli --runs-root <root> \
       --source-run "<root>/../../some-other-project/RUN-x" \
       --parse-run-id RUN-new
```

The parser accepts an arbitrary out-of-boundary directory as a "finalized source run", reads its
manifest, byte-copies its entire declared inventory into a new run under `runs_root`, and — on the
annotation path — base64-embeds the referenced raster into `parse/overlay.svg`, which §10/§13
designates as tracked Git evidence. Data from outside the trust boundary is thereby laundered into
the run store and into evidence.

**Why the test suite missed it:** `tests/integration/test_plan002_parse_run.py:237
test_source_run_traversal_is_rejected_without_staging` passes `Path("..") / source_run.name` — a
*relative* path, i.e. precisely the only case the guard covers. The absolute-with-`..` case is
untested.

**Suggested fix (described, not applied):** resolve the candidate before the containment test —
e.g. `candidate = Path(candidate).resolve(strict=False)` — then require
`candidate.is_relative_to(runs_root)` on resolved paths, and additionally reject any candidate
whose *raw* parts contain `..` regardless of absoluteness. Keep the existing per-component
reparse-point walk on the resolved relative parts. Add a red test with an absolute `..` argument.

---

### M-1 — MAJOR — manifest-supplied inventory paths are never containment-checked

**Location:** `src/pwa/floorplan/builder.py:392-394, 405-406`; `src/pwa/floorplan/runs.py:34-36`;
`src/pwa/files.py:27-31`

```python
    for item in source_manifest["payload"]["inputs"]:
        input_path = source_run / item["path"]            # builder.py:393
        if sha256_file(input_path) != item["sha256"]:
...
    floorplan_entry = next(item for item in source_manifest["payload"]["inputs"] if item["kind"] == "floorplan")
    source_floorplan = source_run / floorplan_entry["path"]   # builder.py:406
```

```python
def copy_source_inventory(source_run: Path, staging_run: Path, manifest: dict) -> None:
    for item in manifest["payload"]["inputs"]:
        copy_immutable(source_run / item["path"], staging_run / "project" / item["path"])
```

`schemas/project_manifest/v1/project_manifest-1.0.0.schema.json` constrains `path` only as
`{"type": "string", "minLength": 1}` — no `relpath` pattern, unlike the newer
`floorplan_annotation` schema. And `content_hash` is *self-consistent* (`compute_content_hash`
recomputes from the document itself), so a hand-written manifest authenticates nothing: any file
placed inside `runs_root` passes every preflight check in `parse_run`.

Verified path-join behaviour on this platform:

```
Path('C:/runs/r1') / 'C:/Windows/win.ini'                    -> C:\Windows\win.ini
Path('C:/runs/r1') / '../../../etc/passwd'                   -> C:\runs\r1\..\..\..\etc\passwd
Path('C:/runs/.staging/p1') / 'project' / '../../../../evil.png' -> C:\runs\.staging\p1\project\..\..\..\..\evil.png
```

**Concrete failure scenario.** A manifest inside `runs_root` declaring
`inputs: [{"path": "C:/Users/<user>/.ssh/id_rsa", "sha256": "<its real hash>", "kind": "other"}]`
causes `sha256_file` to read that file, and `copy_source_inventory` to `copy_immutable` it into the
derived run — and the *destination* join escapes staging too, so a `../../..` path writes outside
`.staging/<parse-run-id>` entirely, defeating the "bounded staging" guarantee of §11.

D-013 requires rejection of "traversal, symlinks/reparse points in every ancestor **from
`runs_root` to the file**". The implementation applies the ancestor walk only down to the run
*directory*; `manifest_path`, `quality_path`, every inventory entry and the annotation image path
get no containment or ancestor-reparse check at all. `copy_immutable` checks
`is_link_or_reparse(source)` on the **leaf only** (`files.py:29`), so a junctioned
`project/inputs/` directory passes.

**Suggested fix:** add a `relpath`-style pattern to `project_manifest` inputs (mirroring the
`floorplan_annotation` `$defs/relpath`, hardened per m-8), and route **every** file access through
a single `resolve_contained_file(runs_root, run_dir, rel)` helper that resolves, asserts
containment, and walks the ancestor chain for reparse points. Apply the same helper to the staging
destination.

---

### M-2 — MAJOR — uncaught `ValueError` escapes `parse_run()` when source units are `unknown`

**Location:** `src/pwa/floorplan/builder.py:156-159`, reached from `builder.py:505-507` via
`builder.py:692-702`

```python
    else:
        source_unit_scale_m = {"mm": 0.001, "cm": 0.01, "m": 1.0}.get(source_manifest["payload"]["units"])
        if source_unit_scale_m is None:
            raise ValueError("DXF failure artifacts require known source units")   # builder.py:159
```

```python
            manifest_units = source_manifest["payload"]["units"]
            if manifest_units == "unknown" or raw.frame.source_units != manifest_units:
                raise FloorplanError("PARSE_UNITS_MISMATCH", "DXF units do not match source manifest units")
```

`"unknown"` is a valid `project_manifest` units enum value. On the DXF path it raises
`PARSE_UNITS_MISMATCH`, which **is** in `_FAILED_DOMAIN_CODES`, so the handler at `builder.py:693`
calls `_failed_scale_artifacts(..., adapter="dxf")` — which then raises `ValueError`. That raise
happens **inside the `except FloorplanError` block**, which is not covered by the outer
`except Exception` at `builder.py:720`, so the exception propagates out of `parse_run()`.

**Proven** by direct invocation against the worktree source:

```
RAISES: ValueError DXF failure artifacts require known source units
```

**Concrete failure scenario.** A source run under `runs_root` whose manifest declares
`units: "unknown"`, quality `complete` with `blockers: []`, and a `.dxf` floorplan. `parse_run`
raises; `cli.main()` has no try/except, so the process exits with a Python traceback instead of the
CLI 2 that §11 mandates for "unexpected exception before a schema-valid diagnostic set", and
partially-written staging is left with no `parse-report.json`.

**Suggested fix:** never let `_failed_scale_artifacts` raise — fall back to omitting the optional
`normalization` block (or `source_unit_scale_m`) rather than raising — and wrap the
`except FloorplanError` body in its own guard that degrades to the operational CLI 2 diagnostic.
Add a red test for `units == "unknown"` + DXF.

---

### M-3 — MAJOR — unreadable/invalid source contract raises out of `parse_run()` with an absolute path

**Location:** `src/pwa/floorplan/builder.py:346-349` (outside the `try:` that begins at line 469)

```python
    manifest_path = source_run / "project" / "project_manifest.json"
    quality_path = source_run / "project" / "input_quality_report.json"
    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_quality = json.loads(quality_path.read_text(encoding="utf-8"))
```

**Proven** against the worktree source:

```
A no-manifest -> UNCAUGHT FileNotFoundError [Errno 2] No such file or directory:
                 'C:\Users\art1\AppData\Local\Temp\pwa-poc2-bg8ewdae\runs\RUN-src\project\...'
B bad-json    -> UNCAUGHT JSONDecodeError Expecting property name enclosed in double quotes: line 1 column 2
```

**Concrete failure scenario.** `--source-run` points at any directory under `runs_root` that is not
a completed intake run (a stale `.staging` sibling, an aborted run, a typo'd run id). §11 classifies
this as "unreadable/invalid source contract" ⇒ **CLI 2, no finalized run, bounded staging may
remain**. Instead the process dies with a traceback, and the message contains a full absolute
Windows path including the OS user name — violating §11's "No raw stack trace or absolute/private
path is emitted to user-facing artifacts" and §12's leakage rule.

**Suggested fix:** move the two reads inside a `try/except (OSError, json.JSONDecodeError)` that
returns the existing operational CLI 2 `_diagnostic(...)`, and give `cli.main()` a top-level
`except Exception: return 2` with a redacted message. Add red tests for both cases.

---

### M-4 — MAJOR — failed-domain runs finalize a false overlay binding

**Location:** `src/pwa/floorplan/builder.py:198` (inside `_failed_scale_artifacts`)

```python
            "overlay": {"path": "parse/overlay.svg", "sha256": "sha256:" + "0" * 64},
```

Every failed-domain finalization (`PARSE_SCALE_UNKNOWN`, `PARSE_TIMEOUT`, `PARSE_UNITS_MISMATCH`,
`PARSE_RESOURCE_LIMIT`, `PARSE_EMPTY_GEOMETRY`, …) writes a schema-valid `floorplan_parse` whose
payload asserts an overlay at `parse/overlay.svg` with an all-zero SHA-256 — while
`builder.py:687-689` (the only place `overlay.svg` is written) is never reached on those paths. The
project's own test confirms the file is absent:
`tests/integration/test_plan002_parse_run.py:228 assert not (result.final_run / "parse" / "overlay.svg").exists()`.

**Concrete failure scenario.** PLAN-003 (or any consumer) reads a finalized failed parse run,
follows `payload.overlay.path`, and gets `FileNotFoundError`; or it verifies
`payload.overlay.sha256` against a file it manages to find and gets a mismatch it cannot explain.
The zero hash is indistinguishable from a real binding by shape — the schema `sha256` pattern
accepts it — so nothing downstream can detect the lie except by trying the path.

D-012 item 1 describes this field as "**optional** binding to the generated overlay by relative path
and SHA-256", and `floorplan_parse-1.1.0.schema.json:128-130` does **not** list `overlay` in
`payload.required`. Omitting it is both legal and correct.

**Suggested fix:** omit `payload.overlay` entirely whenever no overlay is written, and let
`parse-report.json`'s `overlay.overlay_omitted_reason` (already correct) be the sole record. Add an
assertion to the failure-matrix tests that `"overlay" not in floorplan_parse["payload"]` for every
overlay-omitted row.

---

### M-5 — MAJOR — worker tree is not killed on timeout; "no child processes" is unenforced

**Location:** `src/pwa/floorplan/dxf_source.py:53-65`

```python
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | ...
            else:
                kwargs["start_new_session"] = True
            proc = subprocess.Popen(_worker_command(path, output_path), **kwargs)
            try:
                exit_code = proc.wait(timeout=PARSER_TIMEOUT_S)
            except subprocess.TimeoutExpired as exc:
                proc.kill()          # <-- TerminateProcess / SIGKILL on the DIRECT CHILD only
                proc.wait()
                raise FloorplanError("PARSE_TIMEOUT", "DXF worker timed out", source_ref=path.name) from exc
```

§12 requires: "the parent uses OS-specific stdlib/process-group termination to **kill the worker
tree** on timeout" and "the worker is **forbidden to spawn children**".

Neither is implemented. `CREATE_NEW_PROCESS_GROUP` only changes Ctrl-C/Ctrl-Break routing; it does
not make `proc.kill()` (which is `TerminateProcess` on a single handle) tree-aware. On POSIX,
`start_new_session=True` creates a new session but the code calls `proc.kill()` rather than
`os.killpg(os.getpgid(proc.pid), signal.SIGKILL)`. There is no Job Object with
`JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 1`, no `taskkill /T /F`, and no other mechanism preventing or
reaping grandchildren.

**Concrete failure scenario.** Any code executing inside the worker that spawns a grandchild (a
future ezdxf plugin, a DLL side-effect, or a malicious payload reached through a parser bug)
survives the timeout. Because the surviving grandchild inherits the open `worker.stdout.txt` handle,
`tempfile.TemporaryDirectory.__exit__` on Windows then fails with `PermissionError` during cleanup —
replacing the intended `FloorplanError("PARSE_TIMEOUT", …)` with an unrelated exception and leaking
both a process and a temp directory per attempt.

**Suggested fix:** on Windows, assign the child to a Job Object with `JOB_OBJECT_LIMIT_ACTIVE_PROCESS
= 1` and `KILL_ON_JOB_CLOSE` (or, at minimum, kill via `taskkill /PID <pid> /T /F`); on POSIX use
`os.killpg(os.getpgid(proc.pid), SIGKILL)`. Pass `ignore_cleanup_errors=True` to
`TemporaryDirectory` so cleanup cannot mask the terminal finding. Either enforce the no-children
rule or amend §12 to state that it is aspirational.

---

### M-6 — MAJOR — worker **data** channel is truncated at the *stdio* cap

**Location:** `src/pwa/floorplan/dxf_source.py:17-22, 72`

```python
def _bounded_text(path: Path, limit: int) -> str:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        data = data[:limit]          # <-- silent truncation
    return data.decode("utf-8", errors="replace")
...
            return json.loads(_bounded_text(output_path, MAX_WORKER_STDIO_BYTES))
```

`MAX_WORKER_STDIO_BYTES = 1 MiB` is documented in §8 as the cap on the worker's **stdout/stderr**,
not on its result payload. Applying it to `worker-output.json` silently truncates the geometry
result and then reports the truncation as a *malformed worker*.

**Concrete failure scenario.** A DXF with ~12,000 wall lines — well inside the documented
`MAX_WALLS = 20_000` and `MAX_DXF_ENTITIES = 200_000` — produces a worker JSON of roughly
12,000 × ~100 B ≈ 1.2 MB. `_bounded_text` cuts it at 1 MiB, `json.loads` raises, and
`_run_worker` raises `ValueError("worker emitted malformed JSON")`, which `builder.py:720` converts
into an **operational CLI 2** with a `finding: null` diagnostic. The user is told the worker is
broken; the true cause (a documented-legal input exceeding an undocumented internal cap) is
unreportable, and no `PARSE_RESOURCE_LIMIT` is ever emitted.

`tests/integration/test_plan002_parse_run.py:187 test_worker_garbage_is_operational_and_retains_staging`
*mocks* `_run_worker` to raise this exact string, so it locks in the symptom without ever exercising
the real cap.

**Suggested fix:** cap the worker result with its own limit derived from the entity limits (or
stream/parse it with `json.load(fp)` and enforce `MAX_*` counts after parsing), and reserve
`MAX_WORKER_STDIO_BYTES` for the log channels only. If the result genuinely exceeds a bound, raise
`FloorplanError("PARSE_RESOURCE_LIMIT", ...)` so it becomes a failed-domain outcome with the exact
code, not an operational CLI 2.

---

### M-7 — MAJOR — `IMAGE`/`OLE`/`INSERT`/`ARC`/`SPLINE` on an unknown layer is downgraded to a warning

**Location:** `src/pwa/floorplan/dxf_worker.py:66-74`

```python
        if layer not in _KNOWN_LAYERS:
            unmapped.append(_unmapped(source_ref, layer))     # warn, then ignored
            continue
        if layer == "PWA-DIM":
            errors.append(_unsupported(source_ref, "reserved PWA-DIM entities are unsupported"))
            continue
        if kind in _UNSUPPORTED_ENTITY_KINDS:                 # <-- only reached for PWA-* layers
            errors.append(_unsupported(source_ref, f"{kind} is unsupported on layer {layer}"))
```

The layer check precedes the entity-kind check, so the §6 disposition-table row

> `IMAGE`, XREF, OLE, `INSERT`, `ARC`, `SPLINE`, nonzero bulge/Z | `PARSE_UNSUPPORTED_FEATURE` / error | never resolve external data; finish bounded scan, then fail

is only honoured for entities that already sit on a `PWA-*` layer.

**Proven** against the worktree source, with an `IMAGE` entity on the default layer `0`:

```
errors  : []
unmapped: ['PARSE_UNMAPPED_SOURCE_ENTITY']
```

**Concrete failure scenario.** A DXF carrying a scanned raster underlay — placed on layer `0`, which
is the overwhelmingly common real-world convention — parses to `partial` / CLI 1 instead of
`failed` / CLI 3. AC-12 ("unsupported DXF semantics fail loudly") is not met. The security property
survives (AC-19 holds: nothing external is opened), but the approved DXF convention in §6 is a
retained critical *Geometry/Contract* gate under §20, so a silent deviation from it is exactly the
class of change that requires a revised PLAN plus Moshe approval.

`tests/unit/test_floorplan_sources_matrix.py:110 test_external_refs_never_opened` places the IMAGE
on `PWA-WALL`, i.e. the one case that is handled, so the gap is untested.

**Suggested fix:** hoist the `kind in _UNSUPPORTED_ENTITY_KINDS` check above the layer check for the
security-relevant kinds (`IMAGE`, `OLE2FRAME`, `INSERT`, `ARC`, `SPLINE`), keeping
`PARSE_UNMAPPED_SOURCE_ENTITY` for ordinary geometry on unknown layers. Add a matrix row for
`IMAGE` on layer `0`.

---

### M-8 — MAJOR — the duplicate-schema test never reaches the duplicate branches

**Location:** `tests/unit/test_contract_versions.py:104-130`, guards at `src/pwa/contracts.py`
`load_schema_catalog`

D-012 requires: "duplicate `(schema_id, schema_version)` or `$id` is rejected". The test asserts
only `pytest.raises(ValueError)`, and **both** parametrized fixtures trip *earlier, unrelated*
guards. Proven by capturing the actual messages:

```
floorplan_parse-1.1.0-copy.schema.json -> ValueError: Schema filename does not end with a semantic version: ...
floorplan_parse-1.1.1.schema.json      -> ValueError: Schema version does not match filename for ...
```

Neither `raise ValueError(f"Duplicate schema version pair: {key}")` nor
`raise ValueError(f"Duplicate schema $id: {schema['$id']}")` is executed by any test.

**Concrete failure scenario.** A future contributor adds
`schemas/floorplan_parse/v2/floorplan_parse-1.1.0.schema.json` (a legal filename, correct internal
consts, wrong directory major). The duplicate-key branch would fire — but if that branch were ever
regressed (e.g. changed to `out.setdefault(key, schema)`), the suite stays green and a silently
shadowed schema version ships. The stated D-012 protection is unproven.

**Suggested fix:** assert on the message (`pytest.raises(ValueError, match="Duplicate schema version pair")`
and `match="Duplicate schema \\$id"`), and build fixtures that actually reach those branches — e.g. a
second directory `schemas/floorplan_parse/v2/floorplan_parse-1.1.0.schema.json` for the pair case,
and two differently-named-but-consistent files sharing one `$id` for the `$id` case.

---

### M-9 — MAJOR — AC-3 is untested and AC-5 traceability cites a non-existent test

**Location:** `evidence/PLAN-002/implementation/ac-traceability.md:11,13`; `tests/**`

```
| AC-3 | evidenced | `tests/integration/test_plan002_parse_run.py`, `tests/integration/test_plan002_failure_matrix.py` | ... |
| AC-5 | evidenced | `test_staging_left_on_operational_failure`, `f-worker-garbage` | ... |
```

AC-3 requires: "existing finalized source run bytes and hashes are unchanged after success **and
every failure path**". A repository-wide search finds **zero** assertions that hash or re-read the
source run after `parse_run` returns:

```
$ grep -rn "sha256_file(.*source" tests/          -> (no matches)
$ grep -rn "unchanged|immutab|snapshot" tests/integration/test_plan002_*.py
  ...only test_dependencies_unchanged and limits_snapshot()
```

AC-5's cited test name `test_staging_left_on_operational_failure` **does not exist**; the real test
is `test_operational_failure_retains_staging_and_no_finalized_run`
(`tests/integration/test_plan002_parse_run.py:147`).

**Concrete failure scenario.** A future change to `copy_source_inventory` or `copy_immutable`
(e.g. switching to `shutil.move`, or adding a "repair" step) would mutate the finalized source run
and the entire suite would stay green — AC-3 has no tripwire. Combined with C-1/M-1 (writes whose
destination can escape staging), the absence of an AC-3 tripwire is materially risky.

**Suggested fix:** add a fixture that records `{relpath: sha256}` for the whole source run tree
before `parse_run` and re-asserts it after, and parametrize it across success, warning, failed-domain
and operational rows of the failure matrix. Correct the AC-5 test name in the traceability doc.

---

### M-10 — MAJOR — absolute paths and OS user name leak into tracked evidence

**Location:**
- `evidence/PLAN-002/acceptance.md:10`
- `evidence/PLAN-002/implementation/runtime-metadata.json:15`
- `evidence/PLAN-002/implementation/codex-followup-prompt.md:11`

```
- Routing runtime: `runtime_provider=headroom`, `ACTUAL_MODEL_ID=gpt-5.4` from
  `C:\Users\art1\.codex\sessions\2026\08\09\rollout-...jsonl` lines 1 and 6.
```
```json
    "source_file": "C:\\Users\\art1\\.codex\\sessions\\2026\\08\\09\\rollout-...jsonl",
```

§12 states plainly: "**No** network, secrets, source names, absolute paths, EXIF or **user names**
in artifacts/**evidence**." AC-15 requires "private source data never enters tracked evidence".

These files are currently untracked (`?? evidence/PLAN-002/implementation/`,
`?? evidence/PLAN-002/acceptance.md`) and will be committed by the next `git add`. The
`implementation/` directory is 8.3 MB of raw agent transcripts (`codex-events.jsonl`,
`codex-stderr.log`, …) that have not been redacted.

**Concrete failure scenario.** The commit lands, and the repository permanently records the
developer's Windows account name and home-directory layout — an append-only history per §18, i.e.
not removable by a later commit. This is the *evidence* leakage AC-15 exists to prevent.

**Suggested fix:** redact absolute paths to repository-relative or `<home>`-tokenised form, keep the
line/`sha256` citations that make the claim verifiable, and either drop the 8.3 MB raw transcripts
or gate them behind the same Layer-B untracked rule (§13) with only hashes/counts in Git.

---

### M-11 — MAJOR — DXF overlay omits rooms and doors; ID and confidence layers are always empty

**Location:** `src/pwa/floorplan/overlay.py:150-151, 161-162, 105-106`; `builder.py:259-271`

```python
    lines.append('<g id="rooms"></g>')        # _dxf_svg:150 — always empty
    lines.append('<g id="doors"></g>')        # _dxf_svg:151 — always empty
...
    lines.append('<g id="ids"></g>')          # both renderers — always empty
    lines.append('<g id="confidence"></g>')   # both renderers — always empty
```

`_source_binding` builds `primitives` from `geometry.walls` only, so the DXF `<g id="source">` layer
also shows only wall lines — no room polylines, no door/window spans.

§10 requires: "layers distinguish source, walls, rooms, doors, windows, IDs, confidence and legend"
and "DXF: … renders the accepted source primitives **and normalized detections** in aligned groups".
AC-14 requires the overlay to "show source **and detections**".

**Concrete failure scenario.** §20 makes the first Layer-A source-aligned overlay a **retained
critical Visual/Geometry evidence gate**: Moshe must approve it before it counts as G1 evidence or
reaches PLAN-003. The DXF overlay he would be shown cannot display room detection, door placement,
entity IDs or per-entity confidence — precisely the things a visual gate exists to check. The
placeholder `<g>` elements satisfy the letter (the groups exist) while defeating the purpose.

**Suggested fix:** extend `_source_binding` to carry room polygons and opening spans for the DXF
path, render them in `#rooms`/`#doors`, and populate `#ids`/`#confidence` with `<text>` labels
(deterministically ordered, XML-escaped). Re-generate the Layer-A goldens and present the regenerated
overlay at the §20 gate.

---

### M-12 — MAJOR — prior approved evidence rewritten in place

**Location:** `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md`
(`git diff --stat`: **906 insertions, 309 deletions**)

The brief was committed in `a047b7c` "PLAN-002: approve bounded floorplan parsing plan" — it is
*prior* evidence, and the document the implementation is reviewed against. §16 states:

> Read-only: … prior evidence.
> Forbidden: … mutation/removal of historical schemas/error codes/**evidence**/runs …

Deleted content includes the architect's original section 0 BLOCKER table and the explicit
`Status of this document: read-only architectural brief. No code was written, no test was run, no
file in the repo was modified.` line.

I note the genuine ambiguity: `evidence/PLAN-002/**` also appears in the §16 "may create/modify"
list. The two clauses conflict. But the document itself already demonstrated the correct pattern —
it carried an append-only "Resolution addendum (canonical project update, 2026-08-09)" precisely so
that superseded statements could be corrected **without** rewriting the record.

**Concrete failure scenario.** The reviewer (me) and Moshe are asked to judge an implementation
against a brief that the implementation session edited. Any divergence between code and brief can
be closed by editing the brief, and the diff is large enough (1215 changed lines) that a human gate
cannot practically distinguish reflow from substantive relaxation.

**Suggested fix:** restore the brief to its `a047b7c` content and append a dated, signed addendum
recording what is superseded. Escalate to Moshe per the dispatch `ESCALATE_WHEN: contract mutation`.

---

### MINOR findings

**m-1 — `contracts/error_codes.md` mojibake.** Byte inspection of line 44:
`b'Floorplan parser \xd7\x92\xe2\x82\xac\xe2\x80\x9d append-only'` — i.e. `ג€”`, the classic cp1255
round-trip corruption of an em dash (U+2014). Every other section heading in the file uses a proper
`—`. Cosmetic, but it is in a governance contract file. *Fix:* replace with U+2014, write with
explicit `encoding='utf-8'`. (The file is otherwise strictly append-only: `git diff --numstat` =
`24 0`, zero deleted lines — AC verified.)

**m-2 — `validator_for` ignores a custom catalog's origin.** In `src/pwa/contracts.py`, the
`schema_version is None` branch calls `load_all_schemas()` with no argument, so it reads the default
`SCHEMAS_DIR` even when the caller passed a catalog built from a different directory. Latent
inconsistency for any test or tool that isolates a schema tree. *Fix:* derive the latest view from
the supplied `catalog` rather than re-reading disk.

**m-3 — `.tmp/` is untracked and not gitignored.** `git check-ignore .tmp` returns nothing;
the directory holds working artifacts (`plan002-evidence-RUN-*`, `debug-ambiguous`, …) and is not in
the §16 ownership list. A `git add -A` would commit it. *Fix:* add to `.gitignore`.

**m-4 — data URI hardcodes PNG.** `overlay.py:72` emits `href="data:image/png;base64,…"` regardless
of the actual source format, while §5 admits PNG **and** JPEG floorplans. A JPEG source yields an
SVG whose declared media type contradicts its payload. *Fix:* derive the media type from the decoded
image format.

**m-5 — §8 invariant 1 uses `and` where the spec says both are required.**
`validate.py:197`: `if geometry.walls and geometry.rooms and (not usable_wall_ids and not usable_room_ids)`.
§8 requires "at least one non-degenerate wall **and** one valid positive-area room", i.e. the guard
should fire when *either* set is empty (`or`). I could not construct a scenario in which no other
error also fires, so this is reported as MINOR rather than MAJOR. *Fix:* change to `or`.

**m-6 — false `PARSE_OPENING_OFF_WALL` with the wrong code.** `validate.py:78-79`:
`if candidates and declared_wall.id != candidates[0].id: return None, [make_finding("PARSE_OPENING_OFF_WALL", "opening binds a different wall")]`.
`candidates` follows `geometry.walls` order, so a declared wall that *is* a legitimate candidate but
not the first one is rejected. Scenario: an annotated opening between two parallel walls ~1 cm apart
(a double-wall) declaring `wall_index` for the second wall → spurious error, CLI 3, on a valid plan;
and per §8 the correct code for a genuine multi-match would be `PARSE_AMBIGUOUS_WALL_REF`. Borders
the geometry peer's scope. *Fix:* test membership (`declared_wall.id in {c.id for c in candidates}`)
and emit `PARSE_AMBIGUOUS_WALL_REF` when more than one candidate remains.

**m-7 — `ValueError` coercion in the overlay handler.** `builder.py:516-517`:
`reason = "source_raster_exceeds_limits" if str(exc) == "source_raster_exceeds_limits" else "overlay_exceeds_max_bytes"`
maps **any** `ValueError` from `render_overlay` — including
`ValueError(f"unsupported overlay source kind: …")` (`overlay.py:176`) or a `min()` on an empty
sequence (`overlay.py:119`) — onto `PARSE_RESOURCE_LIMIT` / `overlay_exceeds_max_bytes`, and then
**finalizes an immutable run** carrying that wrong code. §11 requires exact codes. *Fix:* raise a
dedicated `OverlayLimitError` from the two real cap checks and let everything else fall through to
the operational CLI 2 path.

**m-8 — `relpath` pattern misses Windows separators.**
`schemas/floorplan_annotation/v1/floorplan_annotation-1.0.0.schema.json:18`:
`"^(?!/)(?![A-Za-z]:)(?!.*(?:^|/)\\.\\.(?:/|$)).+"`. The `..` lookahead is anchored on `/` only.
Verified: `"..\\..\\secret.png"` **matches** (i.e. is accepted), and on this platform
`Path('C:/runs/r1') / '..\\..\\secret.png'` resolves outside the run. The inventory-membership check
in `annotation_source.py:33` is what actually blocks it today, so this is defence-in-depth rather
than an independent hole — but the pattern is doing less than it appears to. *Fix:* add `\\\\` to the
separator class and reject any string containing a backslash.

**m-9 — worker log files capped on read, not on write.** `dxf_source.py:38` opens
`worker.stdout.txt` / `worker.stderr.txt` as plain files; the worker can write unbounded bytes and
only the *read* is capped at `MAX_WORKER_STDIO_BYTES`. §12 says "captures stdout/stderr through
**capped** temporary files". Disk-exhaustion vector, low likelihood with ezdxf. *Fix:* enforce the
cap on the writing side, or accept and reword §12.

**m-10 — `examples.json` wholesale reformat.** D-012 item 7 asks only to *add*
`floorplan_annotation` valid/invalid examples; the diff instead re-indents every pre-existing
example (391 changed lines), obscuring the additive change and stressing the "existing examples …
byte-round-trip unchanged" clause. *Fix:* revert the formatting churn and keep only the additions.

### INFO

- **i-1** `PARSE_LOW_CONFIDENCE` is unreachable in the real pipeline: `normalize.py:256-277` assigns
  confidences of `1.0` / `0.9` / `0.6`, and `LOW_CONFIDENCE_THRESHOLD = 0.5` with `<0.5` being low.
  In practice `partial`/CLI 1 can only arise from `PARSE_UNMAPPED_SOURCE_ENTITY` or
  `PARSE_ROOM_BOUNDARY_UNMATCHED`. Consistent with §9's stated constants, so INFO — but worth stating
  explicitly so nobody believes the low-confidence path is exercised end to end.
- **i-2** `normalize.py:39-40` reports NaN/inf coordinates as `PARSE_RESOURCE_LIMIT`. §7 mandates
  rejection but no specific code; semantically odd, not a violation.
- **i-3** `dxf_worker.py:192` catches only `ValueError`; `ezdxf.DXFStructureError` escapes and its
  traceback lands in `worker.stderr.txt`, then in a `ValueError` message that is swallowed by
  `builder.py:720`. Contained today — no artifact receives it — but one refactor away from M-3's
  leakage class.
- **i-4** The `production-code-audit` skill instructs the agent to fix issues automatically and not
  ask. That instruction was not followed; the read-only review mandate governs. Recorded for audit.

---

## 6. AC-by-AC verdict (ACs in this review's scope)

| AC | Verdict | Reason |
|---|---|---|
| **AC-1** exact-version schema lookup | `WEAK_EVIDENCE` | `load_schema_catalog()` is keyed on `(schema_id, schema_version)`, `validate_artifact()` requires and uses the declared `schema_version`, `build_registry()` is built from **all** catalog values (`contracts.py` `build_registry(catalog.values())`), `load_all_schemas()` picks latest by parsed semver tuple, and `test_validate_artifact_uses_declared_exact_version` genuinely proves 1.0.0 vs 1.1.0 selection plus mislabel rejection. **But** the duplicate `(id, version)` / duplicate `$id` branches required by D-012 are never executed by any test (M-8). |
| **AC-2** existing examples/tests green | `VERIFIED` | Orchestrator's full run: 261 passed, exit 0. Independently re-ran `tests/integration/test_plan002_parse_run.py` + `tests/unit/test_contract_versions.py` with `PYTHONPATH` cleared: 17 passed. |
| **AC-3** source run bytes/hashes unchanged on every path | `WEAK_EVIDENCE` | Code inspection shows the source run is opened read-only (`sha256_file`, `copy_immutable` reads, `read_bytes`) and never written, and finalization targets only `runs/<parse-run-id>`. **But there is no test at all** (M-9), and C-1/M-1 create write destinations that can escape staging, so the property is asserted by nobody. |
| **AC-4** atomic finalize; existing IDs/paths/stale staging fail safely | `VERIFIED` | `finalize_run` is a same-volume `os.replace(staging, final)` (both under `runs_root`); `builder.py:336` rejects pre-existing `final_run` **or** `staging_run` before `mkdir(exist_ok=False)`; covered by `test_existing_final_run_id_is_rejected_before_staging` and `test_existing_staging_run_id_is_rejected_before_staging`, both asserting the *other* path was not created. |
| **AC-5** crash before finalize leaves only staging, no auto delete/resume | `VERIFIED` | No code path deletes or reuses `.staging/<id>`; pre-existing staging is a hard CLI 2 reject, never a resume. `test_operational_failure_retains_staging_and_no_finalized_run` asserts `staging_run.is_dir()`, `not final_run.exists()`, and the presence of `parse-report.json`. Traceability cites a wrong test name (M-9), which is a documentation defect, not a behaviour defect. |
| **AC-12** unsupported DXF fails loudly; unknown layers reported never dropped | `NOT_MET` | Proven: `IMAGE` on layer `0` yields `unmapped: ['PARSE_UNMAPPED_SOURCE_ENTITY']` and `errors: []` (M-7). Unknown layers *are* reported rather than dropped, so half the AC holds; the "fails loudly" half does not for the security-relevant entity kinds. |
| **AC-13** parse/assumptions validate, hashes recompute, provenance present | `WEAK_EVIDENCE` | For `complete`/`partial` runs this holds: `_artifact()` computes `content_hash` then hard-fails on any schema error, and `normalize()` populates `source_kind`/`source_ref`/`source_start|end`/`source_polygon`/`source_center` on every entity (schema `required` enforces the shapes). **But** failed-domain runs finalize a fabricated `payload.overlay` binding (M-4), so a finalized artifact makes a claim that is false by construction. |
| **AC-15** hostile labels escaped; private data never in tracked evidence | `NOT_MET` | Escaping is correct — `xml.sax.saxutils.escape` is applied to legend labels (text nodes) and to the `<metadata>` block, and both shipped Layer-A overlays contain zero `script`/`foreignObject` occurrences with the only `href` being `data:image/png;base64,…`. **The second clause fails**: absolute Windows paths and the OS user name are staged into `evidence/PLAN-002/**` (M-10). |
| **AC-17** traversal, ancestor reparse point, source hash mismatch fail before parsing | `NOT_MET` | Hash-mismatch preflight is correct and well tested (manifest, quality report and full inventory, all before `staging_run.mkdir`). Traversal is **not** met: absolute `..` bypasses containment (C-1, proven), and manifest-supplied inventory paths get no check at all (M-1). The ancestor reparse walk covers only `runs_root`→run directory, not run→file as D-013 requires. |
| **AC-18** over-size fails pre-parse; timeout/entity/vertex/count exact codes | `WEAK_EVIDENCE` | Byte caps genuinely precede parsing (`builder.py:419` annotation, `builder.py:456` DXF, plus a second check in `_run_worker`); `MAX_DXF_ENTITIES` is honestly documented as post-load; vertex/count caps fire in `_prevalidate_raw` and `_validate_room`; `PARSE_TIMEOUT` finalizes with the exact code. **But** M-6 makes legal large inputs fail as an operational CLI 2 instead of any exact code, and the timeout test mocks `_run_worker` rather than exercising a real timeout. |
| **AC-19** XREF/IMAGE/OLE never open external paths | `VERIFIED` | `ezdxf.readfile` does not resolve external references, no code path dereferences an image/xref filename, and `test_external_refs_never_opened` instruments `builtins.open` and asserts the declared `C:/should-not-open.png` is never opened. The *classification* problem is AC-12's, not this one's. |
| **AC-20** failure decision table incl. the three approved preflight cases | `WEAK_EVIDENCE` | All three approved cases are implemented in the correct, unambiguous order and cannot be confused: hash mismatch (`builder.py:360/371/394`) → `PARSE_SOURCE_HASH_MISMATCH` + CLI 2 + no staging; non-complete/blocked quality (`builder.py:382`) → CLI 2 + no staging; and only then, after `complete`+blocker-free, a missing/contradictory scale (`builder.py:482-501`) → `PARSE_SCALE_UNKNOWN` + finalized failed set + CLI 3. Each has a dedicated test. **But** two reachable inputs escape the table entirely by raising uncaught exceptions instead of returning CLI 2 (M-2, M-3), and every failed row carries the false overlay binding (M-4). |
| **AC-21** full pytest green; `git diff --check` clean | `VERIFIED` | 261 passed / exit 0 per the orchestrator; `git diff --check` clean; independently confirmed on the PLAN-002 subset. |
| **AC-22** `pyproject.toml` / `uv.lock` unchanged | `VERIFIED` | `git diff -- pyproject.toml uv.lock` empty (orchestrator), and `test_dependencies_unchanged` enforces it in-suite via `git diff --name-only`. No new imports outside the existing dependency set (`ezdxf`, `PIL`, `jsonschema`, `referencing` — all already present). |
| **AC-23** no H200/GPU/remote/cloud/network; G7/G8 deferred | `VERIFIED` | Static sweep of `src/pwa/floorplan/**` and `tools/*floorplan*` for `socket`, `requests`, `urllib`, `http.client`, `httpx`, `urlopen`, `torch`, `cuda`, `boto3`, `azure`: **zero** matches. The only `Popen` is `dxf_source.py:59` spawning `sys.executable -m pwa.floorplan.dxf_worker` locally with `stdin=DEVNULL`. The only network-shaped strings in the new code are non-dereferenced JSON-Schema `$id` URIs under `panoworld-automation.local`. |

---

## 7. Scope compliance (§16) and network/GPU/cloud statement

### Files touched vs the §16 ownership list

| Path | §16 status |
|---|---|
| `src/pwa/contracts.py` | allowed |
| `src/pwa/intake.py` | allowed — **bundle constant only**, verified: the entire diff is `CONTRACTS_BUNDLE_VERSION = "1.1.0"` plus its single use site |
| `src/pwa/floorplan/**` (14 modules) | allowed |
| `tools/parse_floorplan.py`, `tools/make_floorplan_fixtures.py` | allowed |
| `schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json`, `schemas/floorplan_annotation/v1/…` | allowed; **no 1.0.0 schema file was modified** (verified: `floorplan_parse-1.0.0.schema.json` untouched, 1.1.0 is strictly additive — `normalization`, `overlay`, `*_provenance` `$defs` and optional payload properties only) |
| `contracts/error_codes.md` | allowed, **append-only verified**: `git diff --numstat` = `24 0`, zero deletions |
| `tests/unit/test_schemas_roundtrip.py`, `tests/fixtures/contracts/examples.json` | allowed |
| `tests/unit/test_floorplan_*.py`, `tests/integration/test_plan002_*.py`, `tests/golden/test_floorplan_golden.py` | allowed |
| `PROJECT-STATE.yaml` | allowed |
| `evidence/PLAN-002/**` (new files) | allowed |
| **`evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md`** | **contested — see M-12**: `evidence/PLAN-002/**` is may-modify, but "prior evidence" is read-only and evidence mutation is Forbidden. Rewritten 906+/309−. |
| `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py` | not enumerated in §16 (which lists specific test files). Benign packaging files; noted for completeness. |
| **`.tmp/`** | **outside the ownership list**, untracked and not gitignored (m-3) |

**No forbidden change was found** in the categories that matter most: no dependency or lock change
(AC-22 verified two ways); **no mutation of any historical 1.0.0 schema**; error codes strictly
append-only; `contracts/state_machine.yaml` **byte-unchanged** (not modified at all, so no state,
gate, transition or policy semantics were altered — the permitted descriptive `overlay_svg` note
simply was not written); no finalized run or historical evidence under `evidence/PLAN-001/**`
touched; no merge, push or self-approval. The single scope concern is M-12.

Not-yet-delivered §15/§16 items (not violations — §18 sequences them after this review):
`docs/handoffs/HANDOFF-PLAN-002-to-PLAN-003-001.md`, `docs/OPEN-DECISIONS.md`, `docs/PROGRESS.md`,
`schemas/README.md`, and the descriptive `contracts/state_machine.yaml` overlay note.

### Network / GPU / cloud statement

**No network, GPU, H200, remote or cloud action is evidenced anywhere in this change.**

- Static sweep of all new/modified source for network, cloud-SDK and GPU symbols: zero matches
  (detail under AC-23).
- The single `subprocess.Popen` invocation launches the local Python interpreter on a local module
  with `stdin=subprocess.DEVNULL`, a copied environment, and `cwd` set to the repo root.
- `evidence/PLAN-002/real-plan-redacted.json` records
  `{"status": "not-run", "reason": "Layer B real-plan smoke was intentionally not used …"}` — Layer B
  was correctly not exercised, so the §20 rights/sensitivity attestation gate was not implicated.
- G7/G8 remain deferred; nothing in the diff references them.
- Caveat on provenance, not on behaviour: this statement rests on static inspection of the diff plus
  the orchestrator's local test run. I did not, and could not, audit the implementer's own session
  for out-of-band actions; `evidence/PLAN-002/implementation/runtime-metadata.json` self-reports
  `runtime_provider=headroom`, `ACTUAL_MODEL_ID=gpt-5.4`, which is consistent with the cross-provider
  requirement (OpenAI implementer, Anthropic reviewer) but is the implementer's own claim.

---

## 8. What must change before this can pass

**Blocking (must fix and re-review):**

1. C-1 — resolve before containment; reject absolute `..`. Add the red test.
2. M-1 — containment + ancestor reparse checks on every manifest/annotation-derived file path, on
   both the read side and the staging destination; constrain `project_manifest` `inputs[].path`.
3. M-2, M-3 — no uncaught exception may escape `parse_run()`; both cases must return CLI 2 with a
   redacted message. Add `cli.main()` top-level containment.
4. M-4 — omit `payload.overlay` when no overlay is written.
5. M-7 — restore the §6 disposition-table precedence for `IMAGE`/`OLE`/`INSERT`/`ARC`/`SPLINE`.
6. M-10 — redact evidence before it is committed.

**Should fix in the same pass:** M-5, M-6, M-8, M-9, M-11.

**Escalations required by the dispatch brief** (`ESCALATE_WHEN: any CRITICAL finding, contract
mutation, …`):

- C-1 is a CRITICAL security finding — escalate to Moshe.
- M-12 is a mutation of approved prior evidence — escalate to Moshe.
- M-7 and M-11 touch §20 retained critical gates (exact DXF convention; overlay alignment/visual
  evidence). Under §20 these cannot be settled by the implementer or by me; they need Moshe's
  explicit decision on the regenerated overlay and the corrected disposition table.
