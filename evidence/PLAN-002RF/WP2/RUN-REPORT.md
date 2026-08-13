# PLAN-002RF WP2 — RUN REPORT

- Task: `t_0fc0a9e4` (WP2 — additive contracts and lifecycle)
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Implementation checkpoint: `b49c78d` (contracts + lifecycle)
- Fix checkpoint: `6201705` (MINOR example arc-sign consistency)
- Parent: `t_2f261417` (WP1) — DONE, evidence-bound at `75b0c7b`
- Governing policy: `docs/08-מדיניות-ניהול-מודלים-וסוכנים-deepseek-first.md` + Moshe full-campaign authorization (2026-08-13)
- Implementer model: `deepseek/deepseek-v4-pro-0813` via `openrouter` (runtime-verified; no fallback)
- Independent reviewer: `felo/felo-chat` via OmniRoute `auto/best-coding` (cross-provider; identity from HTTP trailer headers)

## What was done

Additive, new-runs-only contract round. No historical byte changed; no route activated.

1. **Bundle version** — `CONTRACTS_BUNDLE_VERSION` 1.2.0 → 1.3.0, single source of truth
   in `src/pwa/contracts.py`; `src/pwa/intake.py` re-exports it. Historical finalized
   manifests keep their recorded 1.2.0.
2. **`floorplan_parse` 1.2.0 schema** (additive): `source_class` enum
   (`cad_exact`/`raster_auto`/`annotation`/`dxf`); wall `kind` (`segment`|`circular_arc`)
   + `arc` sub-object; sourced `thickness_m`; room `area_m2`; opening `type` + `passage`.
   All additive fields optional → 1.0.0/1.1.0 documents remain valid.
3. **`floorplan_review` 1.0.0 schema** (new): immutable review-chain artifact
   (`reviewed_artifact`, `verdict`, `findings[]`, `reviewer`, `lineage`).
4. **Frozen recognition vocabulary** (`src/pwa/floorplan/recognition.py`, pure/no I/O):
   `source_class` vocabulary + product-author split; arc/bulge invariants;
   sourced-thickness requirement; passage span bound (3.0 m); centreline shoelace area;
   append-only `ReviewHead` lineage with current-head invalidation via `supersede`.
5. **Append-only blocking codes** (`contracts/error_codes.md`): `RECOGNITION_*` /
   `REVIEW_*` / `SCHEMA_VERSION_*` — all `error` (fail-closed), append-only.
6. **Old-consumer rejection** — `pwa.contracts.contract_rejection_reason` helper returns
   a machine-readable `SCHEMA_VERSION_UNSUPPORTED_BY_CONSUMER` reason; purely diagnostic,
   never mutates the doc.
7. **Historical byte preservation** — 1.0.0/1.1.0 schemas + envelope byte-pinned by
   exact SHA-256 in tests (`test_wp2_historical_schema_bytes_are_identical`).

## TDD evidence

- 37 tests written RED→GREEN in `tests/unit/test_wp2_contracts.py`, sections S1–S10:
  versioning, additive round-trip, source-class authorship, arc/thickness/area
  invariants, passage span, review lineage + current-head invalidation, append-only
  error vocabulary, old-consumer rejection, historical byte-identity, concurrency.
- MINOR fix (independent review): round-trip example arc declared `ccw` + `bulge:-1.0`,
  contradicting the frozen `arc_invariants` convention (ccw ⇒ bulge>0). Fixed to
  `+1.0` and locked by a new consistency test
  `test_wp2_full_payload_arc_is_consistent_with_invariants` (38 tests total).

## Commands run (authorized, local-only)

```
uv run python -m pytest tests/unit/test_wp2_contracts.py -v        # RED then GREEN (37 -> 38)
uv run python -m pytest tests/ --ignore=tests/unit/test_wp0_cpu_feasibility.py   # full suite -> 431 passed
```

## Test results

- Targeted (WP2): **38 passed** in 0.63s — `test-results/wp2-targeted.log`
- Full suite: **431 passed, 2 warnings** (pre-existing Pillow deprecation) in 96.79s — `test-results/wp2-full-suite.log`
- `test_wp0_cpu_feasibility.py` excluded via `--ignore` (pre-existing collection error,
  `tools/__init__.py` missing; OUTSIDE WP2 scope, unchanged from WP1).

## Known limits / non-goals

- No recognizer ran; `recognition_or_scoring_performed: false`. Routes remain default-off;
  no route activation.
- No H200/GPU/cloud/remote execution, no spend, no G7/G8, no Product C, no PLAN-003.
- No dependency installed.
- No push/merge-to-remote (local commits only).
- Pinned-environment proof remains pending (unchanged from WP0/WP1).
- Cross-provider review used the only live OmniRoute route (felo-chat); Anthropic/Opus
  direct routes (`aug/*`) and DDG proxy (`ddgw/*`) were unavailable (see
  `model-provenance.json`). No new spatial/geometry reasoning was produced, so the
  Opus spatial gate is not newly triggered.

## Verification checklist

- [x] additive `floorplan_parse` 1.2.0 + `floorplan_review` 1.0.0 schemas round-trip
- [x] 1.0.0/1.1.0 schemas byte-identical (SHA-256 pinned by tests)
- [x] frozen source_class vocabulary + product-author split
- [x] arc/bulge/thickness/area/passage invariants (fail-closed)
- [x] review lineage + current-head invalidation (append-only)
- [x] append-only blocking error vocabulary (all error severity)
- [x] old-consumer rejection predictable + explained
- [x] migration/round-trip/negative/lineage/concurrency/security/determinism tests pass
- [x] independent cross-provider read-only review (APPROVE + MINOR fixed)
- [x] routes default-off; no activation

## Next dependency

WP2 closure does NOT authorize WP3. The next card (`t_aa5fb2fb`) remains a human
`needs_input` gate until its dependency is DONE and Moshe explicitly approves
continuation.
