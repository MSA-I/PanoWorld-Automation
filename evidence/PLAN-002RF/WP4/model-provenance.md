# WP4 (t_f2830a3e) — Model & provider provenance record

- Task: `t_f2830a3e` — WP4 Product B-AUTO clean-raster engine.
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7` (verified).
- Committed code HEAD: `560b752` (local only, no push).

## Active runtime (implementer)

- provider: `openrouter`
- model: `deepseek/deepseek-v4-pro-0813`
- fallback_providers: `[]`
- source: session header (`Model: deepseek/deepseek-v4-pro-0813`, `Provider: openrouter`).

## Model routing policy (recorded, not inferred)

- WP4 produces NEW raster-vision geometry reasoning (voting, paired-edge stroke
  thickness, arc fit, opening motif classification), so the Anthropic-Opus
  spatial review gate is triggered (packet §12.2 + WORKING-PLAN §2).
- Opus-level routes were unreachable in the prior WP3 run (HTTP 000 timeout /
  401 / 403 egress / 502), so the pre-approved fallback is applied: independent
  cross-provider read-only review via the OmniRoute gateway
  (`http://127.0.0.1:20128/v1`), with actual provider/model recorded from
  `x-omniroute-provider` / `x-omniroute-model` HTTP headers. Thresholds are
  never weakened.

## OmniRoute gateway

- reachable: true (GET /v1/models -> HTTP 200).
- Used ONLY for the independent read-only review; not the implementer routing.

## Independent review routing (filled after the review completes)

- requested: anthropic opus-level (critical geometry) — NOT via OmniRoute (user-directed).
- method: `claude -p --model opus` (Claude Code CLI), read-only, code pasted as data.
- resolved_provider: anthropic (Claude Code CLI)
- resolved_model: `claude-opus-5` (confirmed from transcript `"model":"claude-opus-5"`)
- cross_provider_from_implementer: openrouter (deepseek) -> anthropic (claude-opus-5)
- verdict: **NEEDS_REWORK** (2 CRITICAL, 7 MAJOR, 4 MINOR, 1 INFO) —
  see `independent-review-opus-20260817.md`.
