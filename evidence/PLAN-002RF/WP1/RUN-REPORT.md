# PLAN-002RF WP1 — RUN REPORT

- Task: `t_2f261417` (WP1 corpus & evaluator lock)
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Implementation checkpoint: `7b3ac9657e4af0562fd690f1c70845197eed6a49`
- Governing policy: `docs/08-מדיניות-ניהול-מודלים-וסוכנים-deepseek-first.md`
- Implementer model: `deepseek/deepseek-v4-pro-0813` via `openrouter` (runtime-verified
  from `profiles/panoworld/config.yaml`; no fallback, no OmniRoute routing active).

## What was done

1. **Rights & role matrix** frozen (`rights-and-role-matrix.md` + `lock/wp1-role-matrix.json`):
   Rights Owner = Moshe (human); two blind labelers, adjudicator, QA delegate,
   reviewer and implementer are strictly separated via a forbidden-overlap matrix
   (`overlap_is_fail_closed: true`).
2. **Corpus rights/provenance** reaffirmed as project-owned synthetic, zero
   third-party bytes, no network acquisition (U-7 closed for the bounded corpus).
3. **Family splits + leakage controls** (`lock/wp1-split-manifest.json`): train/dev/blind
   disjoint families + leakage controls (family-in-one-split, hash duplicate
   detection, blind truth never opened during development).
4. **Frozen evaluator** (`src/pwa/evaluator/metrics.py` + `lock/wp1-evaluator-spec.json`):
   canonical key, exact-by-key matcher, macro/micro/per-plan metrics, refusal
   accounting, 95% rule-of-three, support classifier.
5. **Frozen truth/matcher/canonicalization** documented (`frozen-truth-matcher-canonicalization.md`),
   binding FX1 truth by hash (source/raster/truth/anchors).
6. **Hash-bound artifacts** — `lock/wp1-manifest.json` replay hash and
   `evidence-index.json` binding every artifact to a git blob + sha256.
7. **Model/provenance record** (`model-provenance.json`) — honest provider/model
   record; cross-provider review declared unavailable under active policy.

## TDD evidence

- RED: `tests/unit/test_wp1_evaluator.py` first run failed 2 tests with real
  behavioural bugs (id leaking into canonical key; wall self-match failing on an
  incorrect longitudinal-projection formula).
- Fixes: canonical key strips non-geometry fields; matcher simplified to exact-by-key
  (the projection-tolerance relaxation was removed as contradictory — a 2 mm shift
  is genuinely different geometry and must not match).
- GREEN: 14/14 targeted tests pass; full suite passes (see `test-results/`).

## Commands run (authorized, local-only)

```
uv run python -m pytest tests/unit/test_wp1_evaluator.py -v     # RED then GREEN
uv run python -m pytest tests/ -q --ignore=tests/unit/test_wp0_cpu_feasibility.py   # full suite
uv run python tools/make_wp1_evaluator_lock.py --out evidence/PLAN-002RF/WP1/lock
uv run python tools/make_wp1_evaluator_lock.py --verify evidence/PLAN-002RF/WP1/lock
uv run python tools/make_wp1_evidence_index.py
```

## Known limits / non-goals

- No recognizer ran; `recognition_or_scoring_performed: false`. Accuracy, yield,
  recognition runtime and peak working set remain NOT_EVALUABLE (unchanged from WP0).
- No corpus acquired from the network; no third-party bytes.
- No schema/contract/route/product change; no PLAN-003; no H200/GPU/cloud/remote.
- `test_wp0_cpu_feasibility.py` has a pre-existing collection error (imports
  `tools.wp0_cpu_feasibility` without a `tools/__init__.py`); it is OUTSIDE WP1
  scope and was excluded (`--ignore`) for the full-suite evidence, not silently
  passed.
- Pinned-environment proof remains pending (unchanged from WP0).

## Verification checklist

- [x] rights & role matrix frozen + independent-review-bound
- [x] frozen truth bound by hash (source/raster/truth/anchors)
- [x] evaluator core frozen + byte-pinned by tests
- [x] family splits + leakage controls declared and pinned
- [x] rule-of-three, refusal accounting, support classifier implemented
- [x] evidence index binds all artifacts to git blobs
- [ ] independent read-only review verdict recorded (next step)

## Next dependency

Independent read-only review (separate session) must return APPROVE /
APPROVE_WITH_FIXES (all fixes closed) before WP1 can close. WP1 closure does NOT
authorize WP2; WP2 remains a human-needs_input gate until its dependency and gates pass.
