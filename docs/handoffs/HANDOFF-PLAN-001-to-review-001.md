# HANDOFF

- Handoff ID: HANDOFF-PLAN-001-to-review-001
- PLAN_ID: PLAN-001
- Producer: OpenAI Codex implementation agent
- Producer provider/model/effort: OpenAI / exact model ID not exposed / HIGH
- Consumer: Independent code/spec reviewer
- Consumer provider/model/effort: Anthropic / Sonnet 5 / HIGH requested
- Date: 2026-08-06
- Contract version: bundle 1.0.0 unchanged
- Model policy: MODEL-ROUTING-v1

## What is stable

1. Immutable intake snapshot under `runs/<run-id>/` with SHA-256 originals.
2. Existing `project_manifest`, `input_quality_report` and `panoworld_manifest` schemas are reused unchanged.
3. PNG/JPG/PDF/DXF intake is tested; a real local DWG header/version smoke passed with redacted evidence.
4. Tiny/golden fixture packages pass the existing validator.
5. `tools/validate_package.py` works without `PYTHONPATH`.
6. `tools/run_checks.py` keeps append-only, per-run evidence.

## Artifacts

| Path | Schema/version | Description |
|---|---|---|
| `src/pwa/intake.py` | project/input-quality 1.0.0 | intake and format QA |
| `src/pwa/packager.py` | panoworld_manifest 1.0.0 | fixture package builder + hash |
| `evidence/PLAN-001/acceptance.md` | raw evidence | AC matrix and residual risks |

## How to validate

```powershell
uv sync
uv run python -m pytest -q
uv run python tools/verify_fixture_roundtrip.py
uv run python tools/validate_package.py tests/golden/panoworld_demo_subset --json
git diff main...plan/PLAN-001 --check
```

## Test evidence

- `evidence/PLAN-001/test-results/RUN-20260806-052400-223281/`
- `evidence/PLAN-001/fixtures/`
- `evidence/PLAN-001/dwg-intake-redacted.json`

## Known limitations

- package validator report has no JSON Schema by explicit scope decision.
- No process sandbox around PDFium/ezdxf; strict local limits are implemented.

## Consumer obligations

- Review spec compliance and code/security separately.
- Verify map serialization never sorts keys.
- Do not weaken schemas or validator checks.
- Do not merge; return findings to the orchestrator.

## Breaking-change policy

No existing schema/contract was changed. Any future breaking change requires MAJOR + ADR.

## Open blockers

- None. `BLOCK-0001` is resolved by `RUN-20260806-060723-42cc1f60`.

## Approval

- Producer status: REVIEW
- Reviewer status: NOT_STARTED
- Orchestrator status: NOT_MERGED
