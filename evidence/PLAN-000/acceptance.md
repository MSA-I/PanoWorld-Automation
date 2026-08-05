# PLAN-000 — Acceptance record

- Date: 2026-08-05
- Branch: `plan/PLAN-000` (merged to `main` at end of session)
- Executed by: Orchestrator — requested per staffing OpenAI Codex/GPT-5.6 for
  mechanical tasks; actual `claude-opus-5[1m]` for all tasks (documented
  deviation: in this interface, delegating mechanical work to subagents costs
  more than inline execution and OpenAI is unavailable; spatial checks in T8
  were Opus-owned per policy anyway).

## Acceptance criteria

| AC | תוצאה | Evidence |
|---|---|---|
| AC1 ‏pytest ירוק + junit | ✅ ‏**109 tests, 0 failures, 0 errors, 0 skipped** | test-results/{junit.xml, summary.md, command.log, coverage.xml} |
| AC2 ‏validator ירוק על Layer B ‏(scene-only) ו-Layer A ‏(with-config) + snapshot | ✅ ‏0 errors, 0 warnings על תת-הסט האמיתי; ‏snapshot תואם | test-results/junit.xml (test_validator_golden), tests/golden/expected_report_demo_subset.json |
| AC3 ‏15 מקרי failure עם קודים ספציפיים | ✅ ‏+ 6 בדיקות נוספות מה-reviews | test-results/junit.xml (test_validator_failures) |
| AC4 ‏13 schemas + envelope, ‏valid+invalid, ‏round-trip | ✅ | test-results/junit.xml (test_schemas_roundtrip) |
| AC5 ‏state machine סוגר ממצאים 1/6/7/18/20 | ✅ כולל אכיפת `RUN:` serialization ו-vocabulary tests שנוספו ב-rework | contracts/state_machine.yaml + test_state_machine |
| AC6 ‏fixture עם SHA מוצמד + NOTICE, בינארים רק שם | ✅ ‏SHA ‏`55fa2245dc01ad0b2cdff9c651b6767db672a702`, ‏17 קבצים, ‏8.3MB | tests/golden/{NOTICE, LICENSE-panoworld-upstream, panoworld_demo_subset/fixture-metadata.json} |
| AC7 ‏git status נקי (מסונן ignored); ‏fixtures שורדים round-trip ביט-זהה | ✅ ‏17/17 | fixture-roundtrip.log |
| AC8 ‏state/docs מעודכנים באותו merge | ✅ | PROJECT-STATE.yaml, docs/PROGRESS.md, docs/00-MASTER-INDEX.md, docs/handoffs/ |

## TDD

- RED: ‏test-results/red-phase.log ‏(בדיקות נכתבו מול contracts/error_codes.md לפני מימוש; כשלי NotImplementedError).
- GREEN: הרצות מלאות ב-test-results/ ‏(הרצה מתחדשת; ‏junit.xml נוכחי = הריצה האחרונה).

## Review record

| Review | Reviewer (actual) | Verdict | תוצאה |
|---|---|---|---|
| Contracts | Fable 5 | NEEDS_REWORK ‏(3 MAJOR, ‏8 MINOR, ‏0 CRITICAL) | **כל ה-MAJOR + מינורים מעשיים תוקנו**: ‏content_hash canonicalization ‏(+impl+test), ‏`RUN:` serialization rule ‏(+schema pattern+tests), ‏raw_evidence vocabulary + ‏G4 artifact ‏(+test), ‏run_id חובה ב-run-scoped, ‏gate CANCEL, ‏2 קודי warn חדשים, ‏narrowing מוצהר של map*.json, ‏D-011 נרשם. ‏Residual מוצהר: ‏blocker schema ‏(MINOR-11) — ל-PLAN עתידי | [reviews/contracts-reviewer.md](reviews/contracts-reviewer.md) |
| Code/tests | Sonnet 5 | APPROVE_WITH_MINOR_FIXES | **תוקן**: ‏depth-scale non-UTF8 → ‏INVALID_DEPTH_SCALE במקום crash ‏(+test); הודעות IMAGE_UNREADABLE ללא נתיב אבסולוטי ‏(+test דליפה) | [reviews/code-reviewer.md](reviews/code-reviewer.md) |
| Cross-provider (OpenAI) | — | לא בוצע | מגבלת ממשק; משה אישר את PLAN-000 עם הביקורת הפנימית — חריגה מתועדת ל-PLAN-000; ‏D-009 פתוח לתשתית עתידית |

## ממצא אמפירי ראוי לציון

ה-golden fixture הוכיח את ערכו כבר בסשן הראשון: היוריסטיקת `DEPTH_SCALE_SATURATED`
הראשונית ‏(`>=65535` = חשד) נכשלה על הדאטה האמיתי — ‏upstream מנרמל כך שהפיקסל
הרחוק ביותר = ‏65535 בדיוק. ההיוריסטיקה כוילה לפלטו ‏(>1% מהפיקסלים בתקרה) עם שתי
בדיקות (חיובית ושלילית). בלי fixture אמיתי זה היה false positive בכל חבילה תקינה.

## סטיות מהתוכנית (מתועדות)

1. ‏`package = false` + ‏CLI כ-`python -m pwa.validator.cli` במקום entry point ‏
   `pwa-validate` — ‏editable install כותב `.pth` עם הנתיב העברי ש-site מפענח
   ב-cp1255 וקורס. ‏(pyproject.toml מתעד; יתוקן אם הריפו יעבור לנתיב ASCII.)
2. ‏`state_machine.yaml` בתחביר JSON ‏(תת-קבוצה חוקית של YAML) — נשאר בשם המתוכנן
   בלי תלות PyYAML. ‏(contracts/README מתעד.)
3. ‏Staffing: כל המשימות בוצעו ע"י מודל הסשן ‏(Opus 5) במקום פיצול Codex/Sonnet —
   ‏OpenAI לא זמין; ‏delegation פנימי היה מייקר. ‏Reviews בוצעו במודלים שונים
   מהמחבר ‏(Fable/Sonnet) כנדרש.
