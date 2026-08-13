# WP0-FX1 role and independence ledger

| Role | Provider/model | Evidence | Independence |
|---|---|---|---|
| Critical spatial architect | Anthropic first-party `claude-opus-5` / MAX requested | `opus-runtime-metadata.json`, session `c0d9917d-ce87-4f1c-9f92-e58d3c72c28a` | Designed geometry; no recognizer output existed or was consumed. |
| Implementer | OpenAI Codex `gpt-5.6-sol` | Kanban run 61 | Implemented deterministic generator/tests from approved task and spatial design. |
| Truth producer | Local deterministic Python | `fixture/fx1-source-geometry.json` → `fixture/fx1-truth.json` | Truth declares `recognizer_inputs: []` and derives only from source geometry. |
| Independent reviewer (initial) | OmniRoute `auto/best-coding`; authoritative follow-up route identity `cx/gpt-5.6-sol` | `reviews/independent-omniroute-review-60c5978.md`, `reviews/omniroute-authoritative-identity.json` | Read-only review of `60c5978`; findings drove bounded producer rework, not reviewer edits. |
| Independent reviewer (rework checkpoint) | pending fresh read-only review | exact-checkpoint review artifact to be added | Must not edit producer files or reuse the stale verdict. |

The source geometry was authored before any recognition. The raster and frozen truth are sibling derivations from the source. No Product A/B route, OCR, recognizer, accuracy scoring, or yield measurement was executed.
