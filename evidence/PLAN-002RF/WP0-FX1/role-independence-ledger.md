# WP0-FX1 role and independence ledger

| Role | Provider/model | Evidence | Independence |
|---|---|---|---|
| Critical spatial architect | Anthropic first-party `claude-opus-5` / MAX requested | `opus-runtime-metadata.json`, session `c0d9917d-ce87-4f1c-9f92-e58d3c72c28a` | Designed geometry; no recognizer output existed or was consumed. |
| Implementer | OpenAI Codex `gpt-5.6-sol` | Kanban run 61 | Implemented deterministic generator/tests from approved task and spatial design. |
| Truth producer | Local deterministic Python | `fixture/fx1-source-geometry.json` → `fixture/fx1-truth.json` | Truth declares `recognizer_inputs: []` and derives only from source geometry. |
| Independent reviewer | pending opposite-provider read-only review | review artifact to be added against exact checkpoint | Must not edit producer files. |

The source geometry was authored before any recognition. The raster and frozen truth are sibling derivations from the source. No Product A/B route, OCR, recognizer, accuracy scoring, or yield measurement was executed.
