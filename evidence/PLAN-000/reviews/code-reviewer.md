# REVIEW — code-reviewer (PLAN-000 execution)

> נשמר verbatim ע"י ה-Orchestrator. ‏Reviewer: Anthropic Sonnet 5 (מודל שונה מהמחבר Opus 5). ‏Verdict: ‏APPROVE_WITH_MINOR_FIXES — ‏MAJOR אחד (crash על depth-scale לא-UTF8, שוחזר בפועל) + מינור אחד (דליפת נתיב בהודעת IMAGE_UNREADABLE). **שניהם תוקנו באותו סשן** עם בדיקות חדשות.

---

AGENT: code-reviewer
ACTUAL_MODEL: claude-sonnet-5 (declared model name: "Sonnet 5")
VERDICT: APPROVE_WITH_MINOR_FIXES

FINDINGS:

1. **[MAJOR] Unhandled crash reading `place_depth_scale.txt` on non-UTF-8 bytes — inconsistent with the rest of the file's defensive pattern, untested.**
   `src\pwa\validator\package_validator.py:317`: `raw = present["place_depth_scale.txt"].read_text(encoding="utf-8").strip()` — the *only* file read in the validator not wrapped in a `try/except`. Every other read is protected: map JSON via `except (json.JSONDecodeError, ValueError, UnicodeDecodeError)`, extrinsics via `except Exception`, both image opens via `except Exception`. Reproduced live on this machine: writing invalid UTF-8 bytes to `place_depth_scale.txt` in an otherwise-valid tiny scene raises an uncaught `UnicodeDecodeError` out of `PackageValidator.validate()`, crashing the whole run instead of reporting `INVALID_DEPTH_SCALE`. `cli.py` has no catch-all around `.validate()` either, so the CLI would exit with a raw traceback rather than the documented exit codes. None of the 15 failure-injection cases exercise this. One-line fix: wrap the read in the same try/except pattern and emit `INVALID_DEPTH_SCALE`.

2. **[MINOR] `IMAGE_UNREADABLE` is completely untested, and its message can leak an absolute (possibly Hebrew) path, undermining the module's stated machine-independence goal.**
   Confirmed empirically: `PIL.Image.open()` on an unopenable file raises `PIL.UnidentifiedImageError` whose `str()` embeds the full absolute path; `_add(..., str(exc))` stores it verbatim in `finding["message"]`. The `path` field is verified scene-relative everywhere, but not the `message` in this branch. Latent snapshot trap + coverage gap (no test exercises `IMAGE_UNREADABLE`).

3. **No other error-code / severity mismatches found.** Every code in `contracts\error_codes.md` cross-checked against the implementation: 1:1 both directions. `WARN_CODES` exactly equals the rows marked `warn`. The three "error (config mode)" codes only ever emitted when `with_config` is true.

4. **Extrinsics math verified correct, no sign/transpose error.** `check_extrinsics_matrix` checks `R[:,1]` against `(0,0,-1)` — exactly matches the verified fact in panoworld-compat §2, independently re-derived by hand from the three sampled upstream extrinsics files. The `STANDARD` test fixture and `fixtures.py::_write_extrinsics` encode the identical rotation, verified orthonormal with det(R)=+1. The det(4x4) shortcut for `MATRIX_NOT_INVERTIBLE` is mathematically sound and creates no masking bug.

5. **Traversal-count formula (`num_keys + total_values`) independently re-derived and confirmed to exactly match the upstream `build_panoworld_batches` algorithm** (walked through 1-key and 2-key examples by hand).

6. **Test honesty: all 15 failure-injection cases assert a specific code via set membership; no vacuous tests found.** Case 12 re-verified live on this Windows machine: the `\\?\`-prefixed injection actually succeeds here (a file literally named `badname.` is created and enumerated), so the primary assertion path is what runs on this environment, with correct cleanup avoiding a Windows delete-lock hazard. Intra-map vs cross-map duplication correctly distinguished via exception-class ordering in `_parse_map`.

7. **Determinism/snapshot stability: solid.** Deterministic sort key `(path, code)`; all iterations sorted; `report.scene` stores only `.name`; all `path` fields hand-built with literal `/`. One caveat = finding 2 (message-field leak, not path-field).

8. **Fetch script is genuinely download-only**: stdlib urllib only, no subprocess/eval/exec, SHA-pinned, explicit and correct closure verification. PIL header dump parses untrusted images (standard low-severity surface, not "execution"). `verify_fixture_roundtrip.py` only invokes local `git checkout`.

9. **Windows/Hebrew-path handling otherwise clean**: explicit `encoding="utf-8"` on every other text read; `[tool.uv] package = false` correctly documents the cp1255 `.pth`-decode crash class it avoids.

EVIDENCE:
- Files read in full: src\pwa\validator\package_validator.py, src\pwa\validator\cli.py, src\pwa\contracts.py, src\pwa\fixtures.py, contracts\error_codes.md, tests\integration\test_validator_failures.py, tests\golden\test_validator_golden.py, tests\unit\test_extrinsics_checks.py, tests\conftest.py, tests\unit\test_schemas_roundtrip.py, tests\unit\test_state_machine.py, tests\golden\expected_report_demo_subset.json, tests\golden\NOTICE, tools\*.py, pyproject.toml, evidence\SESSION-001\agent-reports\panoworld-compat.md, evidence\PLAN-000\test-results\summary.md.
- Commands run (read-only): `uv run pytest -q` (exit 0), `uv run pytest -q --collect-only`, `git log --oneline -20`, `git status --short`, `git diff --stat HEAD~1 HEAD`.
- Live reproductions (in scratchpad, not in repo): (a) np.loadtxt/json.loads error messages do NOT embed file paths; (b) PIL.Image.open DOES embed the absolute path; (c) corrupting place_depth_scale.txt with invalid UTF-8 crashes validate() with uncaught UnicodeDecodeError while the same corruption in extrinsics.txt is caught as MATRIX_PARSE_ERROR; (d) the \\?\ trick in case 12 actually creates `badname.` on this machine and round-trips through Path.iterdir().
