# Contracts — binding principles (PLAN-000 T4)

## Security principles (contract-level, mandatory for every future PLAN)

1. **Blender is templates-only.** Geometry is produced exclusively by pre-approved,
   reviewed script templates that consume `scene_geometry` JSON. **No per-run code
   generation by any LLM agent** — an agent that generates Blender Python per run is
   remote code execution on the local machine (contract-researcher critical finding 2).
   Blender MCP is for manual, human-supervised exception fixing only, never batch.
   Future execution: headless, no network, run-directory mount only, memory/time limits.

2. **Cloud secrets never enter an LLM context.** The H200 key lives only in the thin,
   deterministic runner service exposing `create_job / status / cancel / download`.
   Safety is server-side by contract: `remote_job` REQUIRES `ttl_minutes` (provider
   auto-stop), `max_cost_usd`, `heartbeat_interval_s` and `terminate_verified` — a
   `finally` block is NOT a guarantee (contract-researcher critical finding 3).

3. **Server outputs are untrusted data.** Logs/JSON/images returned from remote runs
   are consumed only through deterministic parsers and metrics before any LLM agent
   reads them (prompt-injection surface — contract-researcher finding 16).

## State machine

`state_machine.yaml` is the canonical transition table (RUN_* vocabulary, distinct
from PLAN statuses of docs/04). Implementation note: the file content is JSON syntax,
which is a valid YAML subset — it keeps the planned filename while remaining parseable
with the locked dependency set (no PyYAML). Structure is enforced by
`tests/unit/test_state_machine.py`.

## Error codes

`error_codes.md` is the locked vocabulary of the package validator. Codes are
`UPPER_SNAKE_CASE`, each with a fixed severity (`error` fails validation, `warn` does
not). Downstream consumers (dashboard, QA) must match on codes, never on message text.
Additions are append-only; changing a code's meaning or severity requires an ADR.

## Vocabulary separation (binding)

Pipeline RUN states and PLAN work-statuses (docs/04) are disjoint vocabularies.
Outside `contracts/state_machine.yaml`, run states are ALWAYS serialized as
`RUN:<STATE>` (see schemas/README.md). `qa_report.decision` deliberately uses
distinct tokens (`approve`/`rework`/`block`) so no bare collision exists.

## Map filename convention (deliberate narrowing)

Upstream PanoWorld locates maps via a data-list txt — the filename is arbitrary
and only the `viewpoints/` sibling is a hard requirement. OUR packages narrow
this: generated map files match `map*.json` in the scene root, and the validator
(`NO_MAP_FILE`) enforces the narrowed convention. Foreign scenes that name maps
differently are out of scope for scene-only validation (they still work in
PanoWorld itself); revisit only if we ever ingest third-party scenes.

## Map JSON ordering

PanoWorld's start node is the FIRST key of the map JSON in insertion order (verified
against upstream `dataset.py`). Any code writing map files MUST preserve insertion
order — `sort_keys=True` is forbidden repository-wide for map/manifest serialization.
