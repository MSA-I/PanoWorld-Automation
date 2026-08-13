# PanoWorld Automation — Master Index

## סטטוס
`WP0_INTEGRATED_PENDING_MAIN_AUDIT_WP1_SUPERVISION_HOLD` — מדיניות DeepSeek/OpenRouter הופעלה לאחר probes חיים ואישור משה. WP0 מוזג מקומית ל־`main` ב־`STOP / NOT_EVALUABLE` לאחר review חוזר `APPROVE`; WP1 נשאר חסום בשער `t_4f9188e9`. אין push, route activation, H200/GPU/cloud/remote, G7/G8 או PLAN-003.

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
   - `deepseek/deepseek-v4-pro-0813` לכל עבודה מקצועית וקריטית.
   - `deepseek/deepseek-v4-flash-0731` למשימות מכניות בלבד.
   - Effort, fallbacks וביקורת ב־session נפרד.

7. [סיכום והפעלת Hermes Kanban](07-סיכום-לפני-הפעלת-Hermes-Kanban.md)
   - לוח `panoworld-dev`, תחום חלק 1 בלבד ופקודת ההפעלה הידנית.
   - רשומת pre-activation היסטורית; הקמפיין הופעל ב־2026-08-09 ו־PLAN-001 נסגר.

8. [מדיניות ניהול מודלים וסוכנים — DeepSeek-First](08-מדיניות-ניהול-מודלים-וסוכנים-deepseek-first.md)
   - DeepSeek V4 Pro מתכנן, מממש, בודק ומבקר ב־sessions נפרדים.
   - Flash מוגבל לעבודה מכנית; אין fallback שקט לספק אחר.
   - הפעלה דורשת API probe, אישור עלות וגבול פרטיות.

9. [מדיניות האוטומציה — DeepSeek WP0–WP6](09-מדיניות-האוטומציה-DeepSeek-WP0-WP6.md)
   - תכנון מלא מראש, מחזור ביצוע מבוקר לכל WP ומטריצת אישורים.
   - auto-recovery מוגבל, checkpoints, rollback ושערים שאינם ניתנים לעקיפה.
   - המסמך אינו מפעיל את השרשרת; נדרשת הוראת הפעלה מפורשת של משה.

10. [תוכנית האוטומציה המפורטת — DeepSeek WP0–WP6](10-תוכנית-האוטומציה-DeepSeek-WP0-WP6.md)
   - מיפוי כל WP ל־inputs, agents, routing, tests, evidence, review, retry, checkpoint, rollback ו-gate.
   - WP6 הוא decision-only; ‏G7/G8 ו־H200/GPU/cloud/remote מחוץ לתחום. PLAN-003 הוא Geometry מקומי אפשרי, אך implementation שלו דורש PLAN/packet ואישור נפרדים ואינו חלק מ־WP0–WP6.

11. [עותקי המקור לפני עדכון האוטומציה](originals-pre-automation-20260813/)
   - snapshot של 27 מסמכי Markdown לפני העדכון; אינו מקור אמת פעיל.

12. [עותק מלא של גרסת Omni](omni-automation-20260813/)
   - snapshot של 28 מסמכי Markdown שנוצרו/עודכנו עבור Omni; אינו מקור אמת פעיל.

13. [המדריך המקורי](../PanoWorld-מדריך-והסבר.txt)
   - התקנה, חומרה, מודלים וקלטים.
   - הערה (SESSION-001): נמצאו בו 9 אי-דיוקים/השלמות מול קוד המקור — ראו Discrepancies ב-[דוח התאימות](../evidence/SESSION-001/agent-reports/panoworld-compat.md); המדריך טרם עודכן.

## מסמכי תוכניות

- [PLAN-001 — Intake and Packager Baseline](plans/PLAN-001-intake-and-packager-baseline.md) — **`DONE`**; ‏Acceptance: ‏[evidence/PLAN-001/acceptance.md](../evidence/PLAN-001/acceptance.md); ‏Review: ‏[independent Anthropic review](../evidence/PLAN-001/reviews/independent-anthropic-review-20260809.md); ‏Closeout: ‏[RUN-REPORT](../evidence/PLAN-001/RUN-REPORT-PLAN-001-CLOSEOUT-20260809.md); ‏Handoff: ‏[PLAN-001 to PLAN-002](handoffs/HANDOFF-PLAN-001-to-PLAN-002-001.md).
- [PLAN-000 — Repository Bootstrap and Contracts](plans/PLAN-000-repository-bootstrap-and-contracts.md) — **`DONE`** ‏(נסגר 2026-08-06; חריגה מתועדת: ראיית red-phase לא נשתמרה). ‏Acceptance: ‏[evidence/PLAN-000/acceptance.md](../evidence/PLAN-000/acceptance.md); ‏Handoff: ‏[HANDOFF-PLAN-000-to-PLAN-001-001](handoffs/HANDOFF-PLAN-000-to-PLAN-001-001.md).
- [PLAN-002 — Floorplan Parsing](plans/PLAN-002-floorplan-parsing.md) — **`ACCEPTED (G1 claimed)`** ‏(מאושר 2026-08-13). חמישה סבבי review עצמאיים + חמישה reworks נסגרו ב־ACCEPT; GC3-8 (עמוד PDF) יושם כ­סבב contract עצמאי; AC-13 נמנה; ושער §20 הוויזואלי (NA-4) אושר על ידי משה ב־2026-08-13. Acceptance: ‏[evidence/PLAN-002/acceptance.md](../evidence/PLAN-002/acceptance.md); ‏Handoff: ‏[HANDOFF-PLAN-002-to-PLAN-003-001](handoffs/HANDOFF-PLAN-002-to-PLAN-003-001.md). G7/G8 ו־H200/GPU נשארים DEFERRED TO PART 2; PLAN-003 אינו מופעל אוטומטית.
- ‏ADRs: ‏[ADR-0001 Git bootstrap](decisions/ADR-0001-git-repository-bootstrap.md) · [ADR-0002 Schema versioning](decisions/ADR-0002-schema-versioning-strategy.md) · [ADR-0003 Fixture vendoring](decisions/ADR-0003-golden-fixture-vendoring.md).
- [REQUIREMENTS.md](REQUIREMENTS.md) — דרישות פונקציונליות/לא-פונקציונליות, disclaimer, human gates.
- [ARCHITECTURE.md](ARCHITECTURE.md) — context, components, data flow, trust boundaries; מאושר מול candidates.
- [OPEN-DECISIONS.md](OPEN-DECISIONS.md) — ‏D-001..D-010.
- [PROGRESS.md](PROGRESS.md) — מה אומת ומה לא התחיל.
- `../PROJECT-STATE.yaml` — ‏state קנוני בשורש.

## Evidence

- [PLAN-001 acceptance](../evidence/PLAN-001/acceptance.md) · [real DWG smoke, redacted](../evidence/PLAN-001/dwg-intake-redacted.json).
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
- DeepSeek V4 Pro מוביל תכנון, coding, geometry, Blender, cameras, depth, security ו־QA.
- ביקורת נעשית ב־DeepSeek Pro session נפרד יחד עם tests/evidence; spatial gates קריטיים נשארים אנושיים.
- שלוש נקודות אישור אנושי מינימליות.
- אין להתחיל implementation בלי PLAN-000 מאושר.

## הפעולה הבאה המומלצת

להשלים audit read-only של `main` הממוזג. גם לאחר סגירת WP0, ‏WP1 נשאר חסום עד שחרור ידני של שער ההשגחה `t_4f9188e9`; verdict של reviewer או merge לבדם אינם מקדמים אותו. route activation נשאר חסום עד החלטת משה נפרדת ב־WP6.
