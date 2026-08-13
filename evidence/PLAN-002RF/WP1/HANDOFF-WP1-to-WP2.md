# HANDOFF — WP1 to WP2 (PLAN-002RF)

- HANDOFF_ID: `HANDOFF-PLAN-002RF-WP1-to-WP2`
- Producer: `t_2f261417` (panoworld profile), implementer `deepseek/deepseek-v4-pro-0813` via `openrouter`
- Consumer: `t_0fc0a9e4` (WP2 — contracts additive & run lifecycle) — NOT yet authorized; human gate
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Checkpoint: `75b0c7b` (evidence-bound index against `0e5ba26`-held artifacts)

## What is locked (frozen, hash-bound)

- Rights Owner: Moshe (human). Corpus: project-owned synthetic, zero third-party bytes, no network acquisition.
- Role matrix: two blind labelers, adjudicator, QA delegate, reviewer, implementer — strictly separated, forbidden-overlap fail-closed (`lock/wp1-role-matrix.json`).
- Hidden truth: `fx1-truth.json` frozen, `recognizer_inputs=[]`, derived only from source geometry; bound to source/raster/truth/anchors by hash.
- Evaluator: `src/pwa/evaluator/metrics.py` — exact-by-key matcher, canonicalization, macro/micro/per-plan, refusal accounting, 95% rule-of-three (k=0 → 3/n), support classifier. Frozen spec: `lock/wp1-evaluator-spec.json`.
- Family splits: train/dev/blind disjoint families + leakage controls (`lock/wp1-split-manifest.json`).
- Everything hash-bound by `lock/wp1-manifest.json` (replay hash `sha256:3ba9f37e…`) and `evidence-index.json` (17 entries, each git_blob + sha256 + bytes).

## Verification (fresh, authorized commands)

- `tests/unit/test_wp1_evaluator.py` → 14/14 pass (RED first: 2 real bugs found and fixed).
- Full suite (excluding pre-existing `test_wp0_cpu_feasibility.py` collection error) → 390 collected, exit 0.
- Lock verify → `{"valid": true, "files_verified": 4}`.
- Evidence index → 17/17 entries verified against git blobs.

## Consumer obligations / gates for WP2

- WP2 must NOT begin on this handoff alone. WP2 (`t_0fc0a9e4`) is a human `needs_input`
  gate; Moshe must explicitly approve continuation.
- WP2 scope is additive contracts + run lifecycle (new-runs-only), NOT recognition.
  This WP1 lock does not unblock any route or recognizer.
- WP2 must bind its own recognizer-side scoring to THIS frozen evaluator when a
  recognizer appears (WP3/WP4); until then accuracy/yield/runtime/peak remain
  NOT_EVALUABLE.

## Remaining explicit limits (carried forward, unchanged)

- Pinned-environment proof pending; existing-env suite is not a substitute.
- Product-B accuracy/yield/resource feasibility unproven.
- No merge-to-remote / push performed (local commits only). No route activation.
- Cross-provider review still unavailable under active DeepSeek policy (D-009 open);
  WP1 used a separate read-only-first DeepSeek Pro reviewer session + deterministic
  evidence, explicitly NOT labelled cross-provider.
