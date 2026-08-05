# AGENT REPORT — test-architect (SESSION-001, Phase B)

> נשמר verbatim על ידי ה-Orchestrator מתוך דיווח הסוכן. ‏Requested: OpenAI Codex/GPT-5.6 HIGH (לא זמין בממשק); ‏Actual: Anthropic Sonnet 5 ‏(fallback מתועד לפי MODEL-ROUTING-v1). ‏Effort: יורש מהסשן.

---

AGENT: test-architect
ROLE: Test/Verification Architect
REQUESTED_MODEL: OpenAI GPT-5.6 or approved Codex model (HIGH) — unavailable in this interface
ACTUAL_MODEL: claude-sonnet-5 (Sonnet 5)
STATUS: REVIEW

PROPOSAL:

**1. Test framework recommendation**

Recommend **pytest** as the locked stage-0 framework. Justification, not just default habit:
- Repo layout in `docs/03-...md` (lines 27-32) already assumes `tests/{unit,integration,fixtures,golden}` — pytest's directory-based collection and fixture scoping map directly onto this without extra config.
- The failure-injection matrix (section 3 below) is naturally a `@pytest.mark.parametrize` table — one assertion function, N mutated inputs. unittest would require 15 near-duplicate `test_*` methods or manual subTest loops.
- Per `docs/06-מדיניות-ניתוב-מודלים-ומאמץ.md` (staffing table, PLAN-000 row): Implementer = OpenAI Codex approved/HIGH, Reviewer = Sonnet 5/HIGH, and separately "Test Engineering | Tester | OpenAI GPT-5.6/Codex | HIGH | Sonnet 5 / HIGH". pytest is the common fluent ground for both providers — minimizes friction on a cross-provider-reviewed artifact.
- `--junitxml` is built into pytest core (no plugin) — directly satisfies the evidence requirement in section 4 with zero extra dependency risk.
- Reject bare `unittest` (weak parametrization, no fixture DI) and reject writing a custom runner (unjustified for a project this document-governed).
- Add `pytest-cov` (coverage evidence) as a dev dependency; treat `hypothesis` as optional/deferred (useful later for matrix-invertibility property tests, not required for PLAN-000).

JSON Schema validation library — three-way trade-off:

| Library | Strength | Weakness for this project | Verdict |
|---|---|---|---|
| `jsonschema` | Reference implementation, full Draft 2020-12 support, `iter_errors()` returns **all** violations with JSON-pointer paths (not just the first) | Pure Python — slower per-call than compiled options (irrelevant at validator-CLI scale, not a hot loop yet) | **Primary, locked for PLAN-000** |
| `fastjsonschema` | Compiles schema→Python source, 10-100x faster | Weaker error reporting (first-error-focused); doc 03 explicitly wants a validator that "מציג errors מפורטים" (detailed/multiple errors) — this is the failure mode the 15 injection tests need | Defer; revisit only if profiling in the future Packager runtime (stage 8) shows `jsonschema` is a bottleneck — swap is possible later without changing the schema files themselves |
| `pydantic v2` | Great DX for internal typed objects, Rust-core speed | Directional the wrong way: pydantic generates JSON Schema *from* Python types, but this project's governance (doc 03: "אין שדות עמומים... כל החוזים versioned") wants hand-authored `schemas/*.schema.json` as the language-agnostic source of truth reviewable independent of Python, since the repo layout (`apps/api`, `apps/dashboard`, `apps/worker`) implies non-Python consumers may eventually exist | Not the contract layer. Optional/deferred: could wrap validated dicts in pydantic models later for orchestrator ergonomics, generated from the schema, never the other way round |

Recommendation: `jsonschema` (Draft2020-12Validator) is the sole runtime validation dependency for PLAN-000. Don't add pydantic or fastjsonschema now — scope discipline per doc 04 ("שינויים מחוץ ל-scope נדחים גם אם 'טובים'").

**2. Fixture strategy — layered, and now backed by verified real numbers**

I fetched the real PanoWorld repo tree via `gh api repos/jjrCN/PanoWorld/git/trees/main?recursive=1` (public repo, no auth, read-only) rather than guessing sizes. Verified facts:
- `examples/` subtree = **218 files, ~432 MB total**, across exactly 3 scenes: `scene0000` (13 viewpoints), `scene0001` (21 viewpoints), `scene0002` (14 viewpoints) — confirming the guide's "שלוש סצנות דוגמה" claim.
- **~329.5 MB of that (76%)** is just 18 `panoImage_2048_{chinese,franch,simple}.png` files — the styled *starting* panoramas, each 15-30 MB, present only on a handful of "entry" viewpoints per scene (e.g. scene0000 viewpoints 0000, 0014, 0019, 0021).
- Excluding those style variants, the **core per-viewpoint package files** (`place_image.png` ~1.5-1.8MB, `place_depth.png` ~0.4-0.6MB, `extrinsics.txt` ~215 bytes, `place_depth_scale.txt` ~5 bytes) total **~102.6 MB** across all 48 viewpoints — about 2.1 MB/viewpoint.
- No `.gitattributes`/git-lfs in that repo (confirmed: sizes returned by the tree API are real byte counts, not LFS-pointer-sized ~130-byte stubs) — a sparse/partial fetch of `examples/` will not touch the ~64GiB model weights (those live only on Hugging Face, per `PanoWorld-מדריך-והסבר.txt` section 2).
- Map-file naming is **not fully consistent** upstream: scene0000 uses `map_panoworld0.json`/`1`/`2`; scene0001 instead uses `map_panoworld_modify_path_by_your_self.json`. Schema/validator must match by glob (`map_panoworld*.json`), not a fixed literal.
- No official release tag exists (confirmed in the guide, section 2: code lives only on `main`) — any vendored/pinned fixture must record the exact commit SHA at fetch time, not "main" as a moving target.

Given this, the "tens of MB" framing in the original ask undersells it — the full `examples/` tree is ~432MB, but a *curated* subset is genuinely small. Recommend a **layered** approach:

- **Layer A — synthetic `tiny-scene` (primary, fast CI fixture).** Hand-crafted, generated procedurally by a small Python factory (e.g. Pillow-drawn flat-color images), not committed as binary blobs. 2 viewpoints, minimal equirect dimensions (e.g. 16x8), trivial 4x4 identity-like extrinsics, a 2-entry map JSON, non-zero depth scale. Runs in milliseconds, fully offline, zero licensing question (we author it), and is the base every failure-injection test mutates via `tmp_path` + `shutil.copytree`.
- **Layer B — vendored real subset (golden compatibility fixture).** Copy a small slice of `scene0000` into `tests/golden/panoworld_demo_subset/`: `map_panoworld0.json` + viewpoints `0000` (includes one `panoImage_2048_*` to exercise the style-reference path, ~34MB) + `0001` + `0003` (plain viewpoints, no style images, ~2.1MB each) → roughly **~38MB total**, or drop viewpoint `0000`'s style image entirely for a **~6-7MB** golden subset if repo size is a concern, and cover the style-reference schema case with a synthetic stand-in instead. This is what "golden test against demo package" (doc 03, stage-0 tests) concretely runs against. Fetch script must pin the exact commit SHA (record it + fetch date in a small metadata file next to the fixture) since upstream has no release tag.
- **Layer C (optional, not for CI)** — a maintenance-only script (`tests/golden/refresh_demo_fixture.py`, pinned SHA) to re-pull Layer B if the upstream repo changes, run manually/rarely, never part of the default test run.

Rationale for layering: Layer A gives fast, deterministic, fully-controllable mutation targets for the 15 failure cases; Layer B is the only thing that can catch "our schema's assumptions about PanoWorld's real conventions were wrong" (actual extrinsics format, actual image mode/bit-depth, actual map-filename inconsistency) — which is exactly why doc 03 stage 0 lists "fixtures מתוך סצנות הדוגמה של PanoWorld" as a deliverable, not just synthetic data.

Open item: licensing of vendoring real image bytes into this private repo — the guide (section 10) says the GitHub repo is Apache 2.0, which should cover `examples/`, but this should get an explicit one-line ADR confirmation before committing binaries, per doc 04's decision-log discipline.

**3. Golden test design**

"Green on demo package" concretely means a test (e.g. `test_validator_golden.py::test_demo_package_validates`) that:
1. Points the validator at `tests/golden/panoworld_demo_subset/`.
2. Asserts an empty error list / success status / exit code 0.
3. Asserts structural expectations explicitly (N viewpoint dirs found, each with all 4 required files, map JSON parses and every referenced ID resolves to a directory) — not just "no exception."
4. Snapshot-compares the validator's structured report against a checked-in expected-report file, so a future validator refactor that silently changes the report shape is caught (a golden-master test on the validator's own output, separate from golden-master-on-input).
5. Also runs against Layer A (tiny-scene) and asserts pass, to prove the validator isn't secretly overfit to Layer B's specific directory shape.

TEST_CASE_LIST (failure-injection matrix, 15 cases, each built by mutating one copy of the tiny-scene fixture in `tmp_path`):

1. Delete `extrinsics.txt` from a viewpoint dir → `MISSING_REQUIRED_FILE` (viewpoint, file=extrinsics.txt) — explicitly named in doc 03 ("rejection של... missing file").
2. `extrinsics.txt` contains a 3x4 matrix instead of 4x4 → `INVALID_MATRIX_SHAPE` (expected 4x4, got 3x4) — explicitly named in doc 03 ("malformed matrix").
3. `extrinsics.txt` matrix is numerically singular/non-invertible (zero determinant) → `MATRIX_NOT_INVERTIBLE`.
4. `extrinsics.txt` has unparseable content (stray text, wrong delimiter) → `MATRIX_PARSE_ERROR`.
5. `place_depth.png` dimensions differ from `place_image.png` dimensions → `DEPTH_RGB_DIMENSION_MISMATCH`.
6. Map JSON references a viewpoint ID with no corresponding directory on disk → `MAP_REFERENCES_UNKNOWN_VIEWPOINT`.
7. A viewpoint directory exists on disk but is never referenced by any map JSON → `VIEWPOINT_NOT_IN_MAP` (recommend hard error by default, per doc's "no ambiguous field/state" governance, configurable severity if a future plan needs otherwise).
8. `place_image.png` saved in an unexpected image mode (RGBA/palette "P"/CMYK instead of the contracted mode) → `INVALID_IMAGE_MODE`.
9. `place_depth_scale.txt` contains `0` → `INVALID_DEPTH_SCALE` (zero/degenerate).
10. `place_depth_scale.txt` contains `NaN` or non-numeric text → `INVALID_DEPTH_SCALE` (non-finite).
11. `place_depth_scale.txt` file missing entirely → `MISSING_REQUIRED_FILE` (explicitly named in doc 03: "rejection של missing scale").
12. A filename/dirname with invalid/non-UTF-8 byte sequence → `INVALID_FILENAME_ENCODING` — worth its own case given this project's known Hebrew-path/encoding fragility (`docs/02-...md`, "Windows" section; global CLAUDE.md Windows-environment rules).
13. Zero-byte `place_image.png` (or any required file truncated to empty) → `EMPTY_FILE` / `TRUNCATED_ARTIFACT`.
14. Map JSON is malformed as JSON (trailing comma, root not an object) → `MAP_JSON_INVALID` (schema-validation-level error, before any semantic check runs).
15. Two map JSON files in the same scene define conflicting edges for the same source viewpoint ID → `DUPLICATE_OR_CONFLICTING_MAP_ENTRY` (relevant because scene0000 upstream genuinely ships 3 map files per scene — the validator must define what "conflicting" means across them, not silently pick one).

**4. Evidence format**

Per `docs/04-...md`'s canonical layout (`evidence/<plan-id>/{test-results,screenshots,diffs,acceptance.md}`), a test run for PLAN-000 must leave under `evidence/<plan-id>/test-results/`:
- `junit.xml` — via `uv run pytest --junitxml=evidence/<plan-id>/test-results/junit.xml`. Standard, machine-parseable, no proprietary format, consumable later by the stage-11 dashboard.
- `command.log` — the literal invoked command plus full captured stdout/stderr, satisfying doc 04's "no claim without evidence" rule and giving the mandatory agent-update field `TESTS_RUN`/`TEST_RESULT` (doc 04, "פורמט עדכון חובה") something concrete to point at, not narration.
- `coverage.xml` (optional, `pytest-cov`) — justified here because stage 0's whole deliverable *is* the validator's error paths; a coverage floor on those branches is a reasonable gate criterion.
- `summary.md` — a human-readable table mapping each of the 15 failure cases + the golden test to PASS/FAIL with a pointer into `junit.xml`, so Moshe can open one file (per doc 04's "בכל סוף סבב יש להציג דוח קצר" reporting cadence) instead of parsing XML.
- Any snapshot/report-diff output goes to `evidence/<plan-id>/diffs/`, per the existing canonical slot.
- Evidence must be regenerated fresh on every DONE claim (doc 04, Verification step: "tests טריים") — recommend the plan's task-runner script always timestamps or wipes this folder before running, so a stale pass can't be silently reused.

**5. Contract-testing approach for the 9 artifacts**

The 9 artifacts are enumerated exactly in `docs/01-חזון-וארכיטקטורת-האוטומציה.md` ("חוזי הביניים", lines 88-96): `project_manifest.json`, `floorplan_parse.json`, `scene_geometry.json`, `assumptions.json`, `camera_plan.json`, `style_spec.json`, `panoworld_manifest.json`, `run_manifest.json`, `qa_report.json`. Producer/consumer pairing (from doc 01's agent list, lines 117-184):

| Artifact | Producer | Consumer(s) |
|---|---|---|
| project_manifest.json | Intake Agent | everyone downstream |
| floorplan_parse.json | Floorplan Vision Agent | Geometry Agent |
| scene_geometry.json | Geometry Agent | Camera Planning, Render, Geometry Reviewer |
| assumptions.json | multiple (append-only) | Human Approval / Dashboard |
| camera_plan.json | Camera Planning Agent | Render Agent |
| style_spec.json | Style Agent | Source Panorama Agent |
| panoworld_manifest.json | Packaging Agent | H200 Runner Agent |
| run_manifest.json | H200 Runner Agent | QA Agent, Dashboard |
| qa_report.json | QA Agent | Human Approval / Dashboard |

Testing approach:
- **Schema round-trip tests**: for each artifact, generate/hand-write a minimal valid example, validate it, serialize→write→read→re-validate, and assert semantic (not just byte) equality — catches key-ordering/float-formatting drift that would silently break the packager's "package hash קבוע" requirement (doc 03, stage 8 Gate).
- **Example-based contract tests**: every schema ships at least one valid and one invalid example fixture under `tests/fixtures/contracts/<artifact>/`; CI validates all valid examples pass and all invalid examples fail with the expected error code.
- **Schema versioning tests (old consumer vs new producer)**: embed a `schema_version` field in each artifact per doc 03's "כל החוזים versioned" gate. Keep every historical version's example fixture permanently (never delete) as a regression suite. For a MINOR (additive) bump, assert the old consumer's schema still accepts the new producer's output; for a MAJOR (breaking) bump, assert an explicit `UNSUPPORTED_SCHEMA_VERSION` rejection rather than silent partial parsing — matches doc 04's rule that "migrations ו-schemas משתנים סדרתית" (one schema change at a time, never silent).

**6. What cannot be tested locally, and its stub layer**

Per `docs/02-...md` ("מה יחכה לענן", lines 64-70) and the P2000/5GB VRAM constraint (lines 13, 40-42):

| Cannot test locally | Why | Local stand-in |
|---|---|---|
| PanoWorld inference itself | 5GB VRAM vs required H200-class hardware; wheel built for SM80/SM90, incompatible with local GPU's compute capability 6.1 | Provider-neutral mock H200 adapter (doc 03 stage 9 "provider-neutral interface") returning canned/replayed outputs; test only the orchestrator's upload/poll/download/terminate lifecycle against a local fake HTTP server |
| Real VRAM/timing/telemetry | No H200 available locally | Stub returns fixed synthetic telemetry values; tests assert correct parsing/threshold logic, not real numbers |
| Full-resolution/photoreal visual quality | Needs the real model | Deterministic fixed-score stubs (`force_low_score` flags) to exercise QA Agent's retry/escalation branches; real metric *code* (SSIM-like) can be unit-tested against synthetic image pairs, but decision quality against real PanoWorld output is cloud-only (M3 in `templates/PROJECT-STATE.yaml`) |
| Heavy source-panorama (image-to-image) generation | Same VRAM ceiling | Mock provider returning a pre-baked tiny image, exercising candidate-generation/scoring loop offline |
| HouseCrafter / CubiCasa-modern stack | Needs ≥24GB VRAM / modernization (doc 02 lines 36, 30) | Partial: containerized CPU fallback where possible, otherwise explicitly out of scope for local CI |

Test-pyramid mapping: unit (schema/matrix-math logic) → integration (validator + orchestrator state machine against Layer A/B fixtures, mock H200 round-trip) → contract (9-artifact producer/consumer pairs) → cloud-only smoke/E2E (explicitly deferred, gated behind G7-G9 in doc 04, executed rarely due to GPU cost).

**7. Windows-specific test risks**

| Risk | Concrete failure mode | Mitigation |
|---|---|---|
| Hebrew + space in repo root (`D:\משה פרוייקטים\...`) | Some tools/subprocess calls built on ANSI-codepage APIs may mis-handle the path | Repo-relative `pathlib.Path` everywhere; never build subprocess command strings via concatenation — list-form `subprocess.run([...])` only (matches global CLAUDE.md guidance on Hebrew paths) |
| Hidden RTL control characters in folder names | `cd`/`Test-Path`-style lookups can fail on visually-identical names | Not directly relevant inside the repo tree itself, but any path constructed from user input/config should be `repr()`-dumped when a "file not found" looks anomalous |
| CRLF normalization by git on Windows | Text fixtures (`extrinsics.txt`, map JSON) silently gain `\r`, breaking naive `str.split('\n')` parsing or changing bytes used in the packager's hash | Add `.gitattributes` (`*.txt text eol=lf`, `*.json text eol=lf`, `*.png binary`) **before** the first fixture commit; parsing code uses `splitlines()`/`.strip()`, never raw `split('\n')` |
| MAX_PATH (260 chars) | Deeply nested `tests/fixtures/.../viewpoints/0000/...` under an already-long Hebrew root, plus long `evidence/<plan-id>/test-results/...` names | Keep generated dir/file names short (numeric viewpoint IDs, concise plan-id slugs); do not silently enable Windows long-path support (that's a system-setting change, out of scope for an agent to do unilaterally) — flag to Moshe as an explicit user-side option if it becomes a real blocker |
| Python 3.14 system vs 3.11 project (doc 02, line 43) | Bare `pytest`/`python` on PATH resolves to system 3.14 and silently breaks dependencies | Always invoke via `uv run pytest`; pin `requires-python = "==3.11.*"` in `pyproject.toml` so uv refuses a mismatched env |
| Windows file locking | PIL images/handles left open during teardown cause `Access is denied` on `tmp_path` cleanup | Always use `with` context managers for file/image handles in fixture generation and mutation code |

RECOMMENDATIONS_FOR_PLAN_000:
1. Lock `pytest` + `jsonschema` (Draft 2020-12) as the only stage-0 test/validation dependencies; defer `pydantic`/`fastjsonschema`.
2. Add `.gitattributes` (LF for text, binary for images) in the repo-bootstrap task, before any fixture is ever committed.
3. Build the `tiny-scene` fixture as generator code (Pillow-based factory), not committed binary PNGs.
4. Vendor a small curated real subset from `jjrCN/PanoWorld` `scene0000` (recommend viewpoints `0001`+`0003` at minimum, ~4MB, optionally `0000` for the style-panorama path at +~34MB) as the golden fixture; pin the exact commit SHA at fetch time (repo has no release tag) and record it in a metadata file alongside the fixture.
5. Run the golden test against both Layer A and Layer B to avoid overfitting the validator to either fixture's shape.
6. Freeze the 9-artifact list exactly as enumerated in `docs/01-...md` ("חוזי הביניים") as PLAN-000's schema scope; any addition/removal requires an ADR.
7. Implement the 15 failure-injection cases above as parametrized pytest tests over mutated copies of Layer A, each asserting a specific machine-readable error code — lock that error-code vocabulary now so the stage-11 dashboard can render it later without string-matching.
8. Wire `--junitxml` (+ optional `--cov`) plus a captured `command.log` into whatever task-runner script PLAN-000 introduces, writing to `evidence/<plan-id>/test-results/`.
9. Resolve, in the PLAN-000 architect pass, the exact relationship between contract #7 `panoworld_manifest.json` and PanoWorld's own native `map_panoworld*.json`/directory structure before finalizing the packager schema — they may not be the same file.
10. Have the schema for the map file explicitly match by glob pattern (`map_panoworld*.json`), not a fixed literal name — upstream `scene0001` already breaks the `map_panoworld{N}.json` convention (`map_panoworld_modify_path_by_your_self.json`).

OPEN_QUESTIONS:
1. Is `panoworld_manifest.json` (contract #7, doc 01) our own wrapper manifest, or is it meant to literally be PanoWorld's native `map_panoworld*.json`? This changes what the "golden test against demo package" is actually diffing against.
2. Should our own generated packages enforce a stricter/consistent map-filename convention than upstream (which is inconsistent across its own 3 example scenes), while the validator stays lenient when *ingesting* upstream examples?
3. Confirm via ADR that vendoring real PanoWorld example image bytes (Apache 2.0 per the guide, section 10) into this private repo is acceptable before Layer B fixtures are committed.
4. Confirm the exact commit SHA to pin for the golden fixture fetch (verified today against `main`; repo has no release tag, so this must be re-confirmed at the moment PLAN-000 actually executes the fetch, not reused from this proposal indefinitely).
5. Deferred, not blocking PLAN-000: will `jsonschema`'s pure-Python performance be acceptable once the same validator runs inside the Packaging Agent's production runtime path (stage 8), not just in tests? Revisit with profiling data before locking that stage's implementation.

EVIDENCE:
- docs\03-תוכנית-בנייה-מפורטת-לפי-שלבים.md (full file; stage 0, repo layout lines 8-37, DoD lines 340-348)
- docs\04-מתודיקת-ניהול-סוכנים-ומעקב.md (full file; evidence layout lines 61-66, DoD lines 197-209, mandatory update format lines 161-179)
- PanoWorld-מדריך-והסבר.txt (full file; sections 2, 3, 6, 10)
- docs\02-היתכנות-על-המחשב-הנוכחי-ולוחות-זמנים.md (full file)
- docs\01-חזון-וארכיטקטורת-האוטומציה.md (full file; "חוזי הביניים" lines 88-96; agent list lines 117-184)
- docs\06-מדיניות-ניתוב-מודלים-ומאמץ.md (full file; PLAN-000 staffing rows)
- templates\PROJECT-STATE.yaml (full file)
- Live, read-only GitHub API query against `jjrCN/PanoWorld` (`gh api repos/jjrCN/PanoWorld/git/trees/main?recursive=1`), executed during this task, to replace guessed `examples/` size estimates with verified numbers.
