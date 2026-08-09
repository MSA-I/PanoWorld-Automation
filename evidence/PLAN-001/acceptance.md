# PLAN-001 — Acceptance record

- Status: **DONE / VERIFIED / LOCAL MAIN MERGED**
- Branch lineage: `plan/PLAN-001` → P1-01 closeout branch → local `main`; not pushed
- Producer: historical OpenAI Codex implementation (exact original harness model not exposed); closeout rework: OpenAI `gpt-5.6-sol` / HIGH, no fallback
- Independent reviewer: Anthropic `claude-sonnet-5` / HIGH; cross-provider review satisfied
- Contracts bundle: 1.0.0 unchanged

## Acceptance criteria

| AC | Result | Evidence |
|---|---|---|
| AC1 plan/templates tracked from clean baseline | PASS | commit `d5ce48f` |
| AC2 originals byte-identical + manifest SHA | PASS for automated formats | `test_all_floorplan_formats_keep_original_and_emit_valid_contracts` |
| AC3 malformed input/link/reparse/existing run rejected | PASS | PLAN-001 integration tests, including real Windows junction/reparse coverage |
| AC4 PDF preview, DXF SVG, DWG real smoke | PASS | `dwg-intake-redacted.json`; PDF/DXF tests pass |
| AC5 unknown scale creates blocker, no package | PASS | `test_unknown_scale_finalizes_blocked_run_without_package` |
| AC6 manifests schema-valid + canonical content hash | PASS | PLAN-001 intake tests |
| AC7 tiny with-config + golden scene-only validators | PASS | `fixtures/{tiny,golden}-validator.json` |
| AC8 stable package hash + mutation detection | PASS | `test_package_hash_is_stable_detects_mutation_and_run_is_exclusive` |
| AC9 map insertion order retained | PASS | `test_fixture_packages_validate_and_manifest_is_schema_valid` |
| AC10 duplicate run ID never overwrites | PASS | PLAN-001 packager test |
| AC11 validator wrapper without PYTHONPATH | PASS | test + runtime CLI exit 0 |
| AC12 evidence runs append-only | PASS | six retained run directories; first invalid run marked `INVALID.md` |
| AC13 PLAN-000 + PLAN-001 suite | PASS | fresh closeout run: 122 tests, 0 failures/errors/skipped |
| AC14 no forbidden systems | PASS | no Blender/PanoWorld/model/H200/cloud operations |

## Fresh verification

- `uv run python tools/run_checks.py --plan-id PLAN-001` → exit 0.
- Latest: `test-results/RUN-20260806-052400-223281/` — 120/120.
- `uv run python tools/verify_fixture_roundtrip.py` → exit 0, 17/17 byte-identical.
- Tiny runtime: 0 errors/warnings, with-config.
- Golden runtime: 0 errors/warnings, scene-only.
- Real local DWG smoke: `RUN-20260806-060723-42cc1f60` → exit 0; real header `AC1024`; source/copy SHA-256 equal; 3/3 artifacts schema-valid; run ignored and source identity redacted.
- Closeout: `test-results/RUN-20260809-070251-128119/` → 122/122, including a real Windows junction and pre-verify image-cap regression.
- `uv run python tools/verify_fixture_roundtrip.py` → 17/17 byte-identical; golden validator → 0 errors/warnings.
- Independent review: `reviews/independent-anthropic-review-20260809.md`; closure report: `RUN-REPORT-PLAN-001-CLOSEOUT-20260809.md`.

## Deviations / residual risks

1. `package_validator_report` remains raw evidence by explicit plan decision; no schema/bundle bump.
2. DWG support intentionally validates only signature/version; full parse/preview is deferred.
3. PDFium and ezdxf parse untrusted input in-process with file/page/image limits; process sandboxing remains future hardening.
4. First evidence run hit a UTF-8 decode error in the harness and is retained as invalid evidence. Later runs prove the fix.
5. Pillow header dimensions are now checked against the explicit 100MP cap before `verify()`; PDFium/ezdxf remain in-process as disclosed above.

## Independent-review closure

- M-1: explicitly ratified because Moshe-approved Part 1 Kanban setup is canonical, docs/state-only, and already part of the kickoff lineage.
- M-2: standalone mandatory-format RUN-REPORT added.
- M-3: real privilege-free Windows junction exercises `FILE_ATTRIBUTE_REPARSE_POINT` detection.
- M-4: explicit image pixel cap precedes Pillow verification, with regression coverage.
- Verdict after rework and fresh verification: **APPROVED / DONE**.
