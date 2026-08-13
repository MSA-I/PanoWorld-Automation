# RUN REPORT — PLAN-002RF WP0-FX1

- RUN_ID: `KANBAN-61-WP0-FX1`
- PLAN_ID: `PLAN-002RF / WP0-FX1`
- Status: producer verification complete; independent review pending
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`

## Inputs
- Approved Kanban task `t_c6b406c5` under decision 1A.
- Anthropic spatial design: `opus-spatial-design.md`.
- Existing local dependencies only; no install, sync, download, corpus, cloud, GPU, Product A/B route, OCR, recognizer, scoring, G7/G8, or PLAN-003.

## Model execution
- Requested: Anthropic first-party Claude Code Opus / MAX; no fallback.
- Actual authoritative runtime model: `claude-opus-5` (`firstParty`).
- Session: `c0d9917d-ce87-4f1c-9f92-e58d3c72c28a`; fallback: no; web requests: 0.
- Implementation model: OpenAI Codex `gpt-5.6-sol`.

## TDD evidence
1. RED: `tests/unit/test_wp0_fx1_fixture.py` failed collection because `tools/make_wp0_fx1_fixture.py` did not exist.
2. GREEN: generator added; targeted tests passed.
3. RED: CLI-without-PYTHONPATH test failed; import-safe wrapper added.
4. RED: visual inspection exposed walls were not split at openings; pixel assertions failed (`0 != 255`).
5. GREEN: hosted segment/arc walls split before rendering; 3 targeted tests passed.

## Commands and results
- `../../.venv/Scripts/python.exe -m pytest tests/unit/test_wp0_fx1_fixture.py -q` → 3 passed, exit 0 (`test-results/targeted.log`).
- `../../.venv/Scripts/python.exe -m pytest -q` → 372 passed, exit 0; two pre-existing Pillow deprecation warnings in `test_floorplan_builder.py` (`test-results/full-suite.log`).
- `../../.venv/Scripts/python.exe tools/make_wp0_fx1_fixture.py --verify evidence/PLAN-002RF/WP0-FX1/fixture` → valid, 5 files verified, exit 0 (`test-results/replay-verify.log`).

## Outputs
- Exact source geometry, raster, frozen truth, three authoritative anchors, rights/provenance, and replay manifest under `fixture/`.
- Replay hash: `sha256:243ace7f0793be867a7e8b6cfeab2244bdf70a823e8ba9778334ee648c79bb87`.
- Recognition/scoring performed: `False`.

## Scope/claim limits
- This package proves fixture provenance, independent truth, anchors, deterministic replay, and local test behavior only.
- It makes no Product-B accuracy/yield claim and does not close pending pinned-environment proof.
- WP1 remains blocked and unauthorized.
