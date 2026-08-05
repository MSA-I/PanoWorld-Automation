# HANDOFF

- Handoff ID: HANDOFF-PLAN-000-to-PLAN-001-001
- PLAN_ID: PLAN-000
- Producer: Orchestrator (Anthropic, requested Fable 5 / actual `claude-opus-5[1m]`, EXTRA)
- Consumer: PLAN-001 (טרם נכתב — ‏Intake או Packager לפי סדר doc 03; הכרעת משה)
- Independent reviewers: Fable 5 (contracts), Sonnet 5 (code) — דוחות ב-`evidence/PLAN-000/reviews/`
- Date: 2026-08-05
- Contract version: contracts bundle 1.0.0 (כל ה-schemas בדראפט 1.0.0)
- Model policy: MODEL-ROUTING-v1

## What is stable

1. **Envelope + 13 artifact schemas** ‏(`schemas/`) — draft 2020-12, versioned `$id`,
   ‏`content_hash` קנוני מוגדר נורמטיבית ‏(schemas/README.md; ‏impl: ‏`pwa.contracts.compute_content_hash`).
2. **State machine** ‏(`contracts/state_machine.yaml`, ‏JSON-syntax) — ‏fail edges,
   ‏G5a/G5b, ‏BLOCKED-מכל-state, כלל serialization ‏`RUN:<STATE>`, ‏raw_evidence מוצהר.
3. **Error-code vocabulary** ‏(`contracts/error_codes.md`) — נעול; הוספות append-only.
4. **Package validator** ‏(`src/pwa/validator/`) — ‏scene-only + ‏with-config;
   ‏CLI: ‏`uv run python -m pwa.validator.cli <scene-dir>`.
5. **Fixtures** — ‏Layer A: ‏`pwa.fixtures.make_tiny_scene`; ‏Layer B: ‏
   `tests/golden/panoworld_demo_subset/` ‏(SHA ‏`55fa2245…`, ‏closure מלא של map0).
6. עקרונות אבטחה מחייבים ב-`contracts/README.md` ‏(Blender templates-only; ‏secrets
   מחוץ ל-LLM; פלטי שרת כ-data לא מהימן).

## Artifacts

| Path | Schema/version | Hash | Description |
|---|---|---|---|
| schemas/** | bundle 1.0.0 | ב-git ‏(main) | ‏14 קבצי schema |
| contracts/** | 1.0.0 | ב-git | ‏state machine, error codes, עקרונות |
| tests/golden/panoworld_demo_subset/** | — | ‏fixture-metadata.json ‏(sha256 פר-קובץ) | ‏golden fixture |
| tests/golden/expected_report_demo_subset.json | — | ב-git | ‏snapshot דוח ה-validator |

## How to validate

```bash
uv sync
uv run python tools/run_checks.py     # מריץ הכל + כותב evidence
uv run python -m pytest -q            # 109 tests
uv run python -m pwa.validator.cli tests/golden/panoworld_demo_subset --json
```

## Test evidence
- `evidence/PLAN-000/test-results/` ‏(junit.xml, summary.md, command.log, coverage.xml)
- `evidence/PLAN-000/fixture-roundtrip.log`, ‏`evidence/PLAN-000/acceptance.md`
- הערה: ‏red-phase.log ‏(ראיית ה-TDD האדום) לא נשתמר — ראו acceptance.md §TDD; ‏consumer: אל תסתמך עליו.

## Known limitations
1. ‏CLI ללא entry point ‏(`pwa-validate`) — מגבלת הנתיב העברי; ‏`python -m` בלבד.
2. ‏Blocker record עדיין markdown ‏(schema מכונה-קריא — ‏residual מוצהר).
3. ‏`overlay_svg` ו-`control_asset_validation` הם raw_evidence שנדחו ל-PLANs של
   שלבים 2/5 — ‏PLAN שנוגע בהם חייב לספק schema.
4. ‏VRAM heuristics ‏(VRAM_BUDGET_WARNING) מבוססות על המדריך המקומי, לא על מקור
   ראשוני — ‏warn בלבד עד מדידה על H200.
5. אין orchestrator/engine — ‏state machine הוא חוזה, טרם ממומש כקוד ריצה.

## Assumptions
- ‏A3 ‏(Z-up נדרש בפועל ע"י ה-control models) — פתוח עד smoke על H200; ה-validator מזהיר בלבד.
- ‏upstream ‏main יציב; כל רענון fixture חייב SHA חדש + עדכון metadata.

## Consumer obligations
- אין שינוי schema בלי bump לפי schemas/README.md; שבירה = ‏MAJOR + ‏ADR.
- כל כתיבת map JSON: לעולם לא `sort_keys=True`.
- מצבי RUN מחוץ ל-state_machine.yaml — תמיד ‏`RUN:<STATE>`.
- קודי שגיאה חדשים ל-validator — append-only ב-error_codes.md.

## Breaking-change policy
‏MAJOR חדש בתיקיית גרסה חדשה + ‏ADR + עדכון מטריצת דוגמאות; הדוגמאות הישנות לעולם לא נמחקות.

## Open blockers
- none

## Approval
- Producer status: VERIFIED ‏(כל ACs עם evidence)
- Reviewer status: ‏contracts NEEDS_REWORK → ‏rework יושם; ‏code APPROVE_WITH_MINOR_FIXES → יושם
- Orchestrator status: **DONE** — נסגר בהנחיית משה ‏(2026-08-06); ‏merge ‏`4ff4a41` ב-main המקומי (לא בוצע push)
