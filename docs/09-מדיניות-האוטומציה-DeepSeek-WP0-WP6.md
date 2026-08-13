# מדיניות אוטומציה — Full Part 1 Autonomous

## סטטוס וסמכות

- Policy ID: `AUTOMATION-POLICY-v4-FULL-PART1`.
- סטטוס: `READY FOR ACTIVATION — TOOL-CALL PROBE BLOCKED`.
- תאריך: 2026-08-13.
- תחולה: מסגירת PLAN-002 ועד קבלת כל חלק 1 המקומי.
- תלות: [06](06-מדיניות-ניתוב-מודלים-ומאמץ.md), [08](08-מדיניות-ניהול-מודלים-וסוכנים-deepseek-first.md), [10](10-תוכנית-האוטומציה-DeepSeek-WP0-WP6.md).

## עקרון ההפעלה

אישור יחיד מפעיל את כל השרשרת:

```text
PLAN-002 closeout/remediation
→ PLAN-003 Geometry
→ Cameras
→ Rendering + Depth + Extrinsics
→ Style Understanding
→ Local Source Panorama
→ Package Integration
→ Local QA
→ Dashboard
→ Hardening
→ Part 1 Acceptance
```

אין `PLAN → המתן למשה → IMPLEMENT`. לאחר activation:

```text
PLAN → REVIEW → IMPLEMENT → TEST → REVIEW → REWORK → VERIFY → MERGE → NEXT PLAN
```

## סמכות מואצלת

ה־orchestrator הוא מקבל ההחלטה המוגדר לכל פעולה הפיכה בתוך scope. הוא:

- בוחר default מומלץ.
- רושם ADR ונימוק.
- שומר rollback.
- מפעיל author/reviewer sessions נפרדים.
- ממשיך כאשר automated gate ירוק.
- אינו מבקש אישור תוכנית, implementation, visual gate או מעבר PLAN שגרתי.

## מטרת־על

`AUTONOMOUS_PART1_COMPLETION_GATE` עובר רק כאשר:

- כל תוכניות חלק 1 המקומיות `VERIFIED` או `DONE`.
- כל suites הטריים ירוקים.
- אין Critical/Major פתוח.
- כל artifacts וה־evidence קשורים ל־checkpoints.
- compatibility, security, determinism ו־rollback מאומתים.
- H200/GPU/cloud/G7/G8 מסומנים במפורש `DEFERRED TO PART 2`.
- דוח קבלת חלק 1 נוצר ונמסר למשה.

## Automated gates במקום human gates

| סוג | החלטה |
|---|---|
| Plan approval | reviewer נפרד + checklist; תיקון עד APPROVE |
| Contract/architecture | ADR + compatibility/security tests + reviewer |
| Visual/geometry | metrics + overlays/renders + Pro reviewer session נפרד |
| Implementation | tests + static/contract/security checks |
| Merge | exact checkpoint, clean diff, tests, review, rollback |
| Next PLAN | תנאי יציאה ירוקים ו־dependency graph תקין |
| Final Part 1 | audit מלא ודוח; אין deployment |

סטטוס סגירה לשער חזותי: `AUTO_ACCEPTED_UNDER_DELEGATED_AUTHORITY`, עם metrics ו־artifact links.

## תכנון תוך כדי תנועה

אין חובה לכתוב מראש PLAN מפורט לכל יתרת הפרויקט לפני activation. לכל שלב:

1. Pro מייצר PLAN תחום מתוך requirements/architecture/state.
2. Pro reviewer session נפרד מחזיר APPROVE או REWORK.
3. REWORK חוזר עד approval או circuit breaker.
4. implementation מתחיל מיד לאחר approval האוטומטי.

## Failure handling

### Recovery אוטומטי

- network timeout/429/5xx: עד 3 retries.
- worker crash: resume מה־checkpoint.
- test regression: bounded debug/rework.
- review finding: bounded rework חדש.
- dependency/worktree lock טכני: repair מתועד.

### Circuit breaker

עצירה רק עבור:

- auth/tool/model identity לא תקינים.
- privacy, rights או security blocker מהותי.
- input חסר ללא default בטוח.
- deterministic failure שלא נסגר לאחר rework.
- שינוי בלתי־הפיך או מחוץ ל־scope.
- H200/GPU/cloud/remote/production.
- חריגה מתקציב OpenRouter.

## תקציב

- כל run רושם usage/cost.
- נדרש cap כספי לפני activation.
- התקרבות ל־80% שולחת התראה אך אינה עוצרת.
- 100% cap מפעיל circuit breaker.
- אין מעבר למודל זול שאינו המודל המקובע.

## Kanban

לפני activation יש להחליף את נוסחי כרטיסי Omni הישנים ולייצג את השרשרת המלאה. לאחר activation:

- כרטיס successor מקודם אוטומטית.
- אין `needs_input` בין PLANs.
- human-gate cards היסטוריים נסגרים כ־`superseded_by_delegated_authority` כאשר evidence מתאים.
- כל PLAN מקבל child cards ל־plan/review/implement/test/review/rework/checkpoint.
- observer מדווח; dispatcher מבצע.

## Checkpoint חובה

```text
PLAN_ID:
STATUS:
CHECKPOINT:
REQUESTED/ACTUAL MODEL:
AUTHOR/REVIEWER SESSIONS:
TESTS:
EVIDENCE:
OPEN FINDINGS:
AUTOMATED GATE:
ROLLBACK:
NEXT PLAN:
CIRCUIT BREAKER: none|reason
```

## Scope

נכלל:

- PLAN-002/PLAN-002RF closeout.
- PLAN-003 Geometry.
- Cameras.
- Rendering/Depth/Extrinsics.
- Style.
- Source panorama mock/local preparation.
- Package integration.
- Local QA.
- Dashboard.
- Hardening וקבלת חלק 1.

לא נכלל:

- H200 runner אמיתי.
- GPU/cloud/remote execution.
- G7/G8.
- production deployment.
- נתוני לקוח רגישים ללא privacy approval.

## הוראת activation היחידה

לאחר preflight מלא, הוראה אחת מספיקה:

```text
מאשר להפעיל את Full Part 1 Autonomous Campaign לפי מסמכים 06 ו־08–10,
עם DeepSeek V4 Pro דרך OpenRouter, ללא שערי אישור שגרתיים,
עד קבלת חלק 1 המקומי או circuit breaker אמיתי.
```

אישור זה אינו מאשר H200/GPU/cloud/production או חריגה מתקציב.
