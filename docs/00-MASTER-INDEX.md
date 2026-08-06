# PanoWorld Automation — Master Index

## סטטוס
`M1_PLAN_001_REVIEW` — ‏PLAN-000 נשאר `DONE`. ‏PLAN-001 intake + fixture packager מומש על `plan/PLAN-001`: ‏120/120 בדיקות ירוקות, tiny/golden validator ירוקים ו־evidence append-only. טרם בוצע merge; ‏DWG smoke פרטי ו-review בלתי תלוי עדיין פתוחים. לא הותקן Blender, לא הורדו PanoWorld/מודלים, לא הופעל H200 ולא בוצע push.

מבנה בפועל: ‏`schemas/` ‏(envelope+13), ‏`contracts/` ‏(state machine, error codes, עקרונות אבטחה), ‏`src/pwa/` ‏(validator), ‏`tools/`, ‏`tests/` ‏(כולל golden fixture ‏8.3MB), ‏`docs/decisions/` ‏(ADR-0001..0003), ‏`docs/handoffs/`, ‏`evidence/PLAN-000/`.

## מטרת הפרויקט
לבנות מערכת מתוזמרת שמקבלת floorplan + style reference, מכינה geometry/control assets/package תקין של PanoWorld, מריצה אותו על H200 ומבצעת QA עם human gates.

## מסמכים

1. [חזון וארכיטקטורת האוטומציה](01-חזון-וארכיטקטורת-האוטומציה.md)
   - pipeline מוצע.
   - סדר הסוכנים.
   - contracts ו-state machine.

2. [היתכנות על המחשב הנוכחי ולוחות זמנים](02-היתכנות-על-המחשב-הנוכחי-ולוחות-זמנים.md)
   - מפרט שנבדק בפועל.
   - מה ניתן לבנות מקומית.
   - הערכות POC/MVP/production.

3. [תוכנית בנייה מפורטת לפי שלבים](03-תוכנית-בנייה-מפורטת-לפי-שלבים.md)
   - 13 שלבים.
   - outputs, tests ו-gates.
   - סדר מימוש מומלץ.

4. [מתודיקת ניהול סוכנים ומעקב](04-מתודיקת-ניהול-סוכנים-ומעקב.md)
   - statuses, IDs, reviews ו-Definition of Done.
   - כיצד לפקח על עשרות סבבים.

5. [מקורות וקישורים](05-מקורות-וקישורים.md)
   - PanoWorld, floorplan parsing, Blender, agents ו-workflows.
   - מגבלות ורישיונות.

6. [מדיניות ניתוב מודלים ומאמץ](06-מדיניות-ניתוב-מודלים-ומאמץ.md)
   - Anthropic ו-OpenAI לפי תפקיד ושלב.
   - Opus 5 כברירת מחדל למשימות 3D קריטיות.
   - Effort, fallbacks ו-cross-provider review.

7. [המדריך המקורי](../PanoWorld-מדריך-והסבר.txt)
   - התקנה, חומרה, מודלים וקלטים.
   - הערה (SESSION-001): נמצאו בו 9 אי-דיוקים/השלמות מול קוד המקור — ראו Discrepancies ב-[דוח התאימות](../evidence/SESSION-001/agent-reports/panoworld-compat.md); המדריך טרם עודכן.

## מסמכי תוכניות

- [PLAN-001 — Intake and Packager Baseline](plans/PLAN-001-intake-and-packager-baseline.md) — **`REVIEW`**; ‏Acceptance: ‏[evidence/PLAN-001/acceptance.md](../evidence/PLAN-001/acceptance.md); ‏Handoff: ‏[HANDOFF-PLAN-001-to-review-001](handoffs/HANDOFF-PLAN-001-to-review-001.md).
- [PLAN-000 — Repository Bootstrap and Contracts](plans/PLAN-000-repository-bootstrap-and-contracts.md) — **`DONE`** ‏(נסגר 2026-08-06; חריגה מתועדת: ראיית red-phase לא נשתמרה). ‏Acceptance: ‏[evidence/PLAN-000/acceptance.md](../evidence/PLAN-000/acceptance.md); ‏Handoff: ‏[HANDOFF-PLAN-000-to-PLAN-001-001](handoffs/HANDOFF-PLAN-000-to-PLAN-001-001.md).
- ‏ADRs: ‏[ADR-0001 Git bootstrap](decisions/ADR-0001-git-repository-bootstrap.md) · [ADR-0002 Schema versioning](decisions/ADR-0002-schema-versioning-strategy.md) · [ADR-0003 Fixture vendoring](decisions/ADR-0003-golden-fixture-vendoring.md).
- [REQUIREMENTS.md](REQUIREMENTS.md) — דרישות פונקציונליות/לא-פונקציונליות, disclaimer, human gates.
- [ARCHITECTURE.md](ARCHITECTURE.md) — context, components, data flow, trust boundaries; מאושר מול candidates.
- [OPEN-DECISIONS.md](OPEN-DECISIONS.md) — ‏D-001..D-010.
- [PROGRESS.md](PROGRESS.md) — מה אומת ומה לא התחיל.
- `../PROJECT-STATE.yaml` — ‏state קנוני בשורש.

## Evidence

- [evidence/SESSION-001/preflight-report.md](../evidence/SESSION-001/preflight-report.md) — פקודות ותוצאות אמיתיות.
- [contract-researcher](../evidence/SESSION-001/agent-reports/contract-researcher.md) · [panoworld-compat](../evidence/SESSION-001/agent-reports/panoworld-compat.md) · [test-architect](../evidence/SESSION-001/agent-reports/test-architect.md) — דוחות סוכני המחקר (שלב B).
- [plan-reviewer](../evidence/SESSION-001/agent-reports/plan-reviewer.md) — ביקורת בלתי תלויה על PLAN-000 ‏(NEEDS_REWORK → כל הממצאים יושמו; ראו §15 בתוכנית).

## Session prompts
- `SESSION-001-START-PROMPT.txt` — פרומפט לסשן הראשון: preflight, ביקורת, PLAN-000 וחוזים בלבד; ללא התקנות או implementation.

## Templates
- `templates/AGENT-BRIEF.md`
- `templates/HANDOFF.md`
- `templates/BLOCKER.md`
- `templates/RUN-REPORT.md`
- `templates/PROJECT-STATE.yaml`

## החלטות ראשוניות
- פיתוח ההכנות יתבצע מקומית.
- PanoWorld עצמו ירוץ מאוחר יותר על H200.
- geometry pipeline יהיה דטרמיניסטי.
- סוכני AI יתזמרו, יכתבו קוד, יבקרו ויטפלו בחריגים.
- Opus 5 מוביל תכנון וביקורת של geometry, Blender, cameras, depth ו-3D QA; Fable אינו ברירת המחדל ל-3D.
- OpenAI משמש ל-reasoning, coding, tests, cloud/security ול-review חוצה-ספקים.
- שלוש נקודות אישור אנושי מינימליות.
- אין להתחיל implementation בלי PLAN-000 מאושר.

## הפעולה הבאה המומלצת
‏PLAN-000 סגור. הבא: **הכרעת משה על היקף PLAN-001 וכתיבתו** — ‏Intake ‏(לפי סדר doc 03) או ‏Packager ‏(builder של panoworld_manifest→map+viewpoints, שה-validator וה-fixtures שלו כבר קיימים). ‏PLAN-001 גם יתקן את התנהגות מחיקת ה-evidence של `tools/run_checks.py`.

אין להתחיל parsing או Blender לפני ש-PLAN ייעודי אושר.
