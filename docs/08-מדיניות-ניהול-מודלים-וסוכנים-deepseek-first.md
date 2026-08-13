# מדיניות ניהול מודלים וסוכנים — DeepSeek/OpenRouter אוטונומי

## סטטוס וסמכות

- Policy ID: `MODEL-AGENT-MANAGEMENT-v4-AUTONOMOUS`.
- סטטוס: `READY FOR ACTIVATION — TOOL-CALL PROBE BLOCKED`.
- תאריך: 2026-08-13.
- תחולה: כל חלק 1 המקומי, מסגירת PLAN-002 ועד קבלת חלק 1.
- מסמך זה אינו activation בפני עצמו.
- snapshot המקור נשמר ב־[`originals-pre-automation-20260813/`](originals-pre-automation-20260813/); snapshot Omni נשמר ב־[`omni-automation-20260813/`](omni-automation-20260813/).

## מודלים ו־gateway

- Gateway: `openrouter`.
- Primary: `deepseek/deepseek-v4-pro-0813`.
- Mechanical-only: `deepseek/deepseek-v4-flash-0731`.
- Secret: `OPENROUTER_API_KEY`, מחוץ לריפו.
- אין `auto`, ‏`latest`, fallback או מודל שאינו DeepSeek.

### תוצאות preflight חיות שכבר הושגו

- Pro chat: HTTP 200, returned model זהה, exact reply עבר.
- Flash chat: HTTP 200, returned model זהה, exact reply עבר עם effort נמוך.
- reasoning ו־usage/cost metadata התקבלו.
- `json_object` עבר.
- Hermes CLI דרך פרופיל `panoworld` החזיר תשובה מדויקת מ־Pro.
- tool calling חסום כרגע ב־OpenRouter: `No endpoints available matching your guardrail restrictions and data policy`.
- `json_schema` קשיח אינו נתמך ב־backend שנבחר; הפרויקט משתמש ב־`json_object` + validation מקומי.

## יעד הקמפיין

`AUTONOMOUS_PART1_COMPLETION_GATE`:

> המשך אוטומטית עד שכל התוצרים המקומיים של חלק 1 בנויים, נבדקו, נסקרו, מוזגו מקומית ונמסרו עם evidence; עצור רק ב־circuit breaker אמיתי.

## הרשאה לאחר activation יחיד

לאחר הוראת Full Part 1 אחת, ה־orchestrator רשאי:

1. לסגור את יתרת PLAN-002/PLAN-002RF.
2. לתכנן ולהפעיל PLAN-003 Geometry.
3. להמשיך ל־Cameras, Rendering/Depth/Extrinsics, Style, Source Panorama מקומי, Packaging, Local QA, Dashboard, Hardening וקבלת חלק 1.
4. לבחור ברירת מחדל מומלצת בכל החלטה הפיכה בתוך scope.
5. ליצור ADR, code, tests, evidence, reviews, rework ו־checkpoints.
6. למזג מקומית לאחר tests ו־review.
7. לעבור אוטומטית ל־PLAN הבא כאשר תנאי היציאה עברו.

אין צורך באישור משה בין PLANs או ב־visual/geometry approval שגרתי.

## מחזור חובה לכל PLAN

```text
PLAN
→ independent-session review
→ IMPLEMENT (TDD)
→ TEST
→ SECURITY/CONTRACT CHECK
→ VISUAL/SPATIAL METRICS where relevant
→ REVIEW
→ bounded REWORK
→ fresh VERIFY
→ CHECKPOINT / local MERGE
→ AUTOMATED GATE
→ next PLAN
```

## שערים אוטומטיים

| Gate | תנאי מעבר אוטומטי |
|---|---|
| G0 Input | schema/hash/scale/rights checks ירוקים; קלט חסר נכשל סגור |
| G1 Parse | accuracy/topology/overlay/evidence thresholds עברו |
| G2 Geometry | topology, dimensions, collision, overlay ו־review עברו |
| G3 Camera | coverage, visibility, no-collision ו־extrinsics עברו |
| G4 Render | RGB/depth/extrinsics validity ודטרמיניזם עברו |
| G5 Style | style contract, metrics, provenance ו־review עברו |
| G6 Package | validator, compatibility ו־round-trip עברו |
| Local G9 | geometry/style/consistency/security QA עברו; מסירה מסומנת conceptual |

G7/G8 אינם חלק מחלק 1 המקומי ואינם נדרשים לסיום הקמפיין.

## החלטות ברירת מחדל

כאשר יש כמה אפשרויות חוקיות והפיכות:

1. בחר את האפשרות הבטוחה, הפשוטה והדטרמיניסטית ביותר.
2. העדף compatibility ו־default-off על migration מסוכנת.
3. העדף fail-closed על ניחוש.
4. תעד ADR, alternatives, rationale, tests ו־rollback.
5. המשך ללא שאלה.

## ביקורת ומניעת self-approval

- author ו־reviewer הם Pro sessions נפרדים.
- reviewer ראשון read-only.
- rework מתבצע ב־run אחר.
- artifacts חזותיים נשמרים ומוערכים במדדים; reviewer נפרד בוחן אותם.
- אין לתאר Pro→Pro כ־cross-provider.
- אין סגירה כאשר Critical/Major פתוח.

## Auto-recovery

- עד 3 retries טכניים עם backoff.
- crash: resume מה־checkpoint המאומת האחרון.
- finding מקצועי: bounded rework חדש, לא retry עיוור.
- test failure: root cause → תיקון → suite טרי.
- אין החלשת threshold או שינוי contract כדי לעבור.

## Circuit breakers

רק אלה עוצרים את הקמפיין ומבקשים פעולה אנושית:

- OpenRouter auth/model identity/tool calling failure.
- rights/privacy/security blocker מהותי.
- חסר קלט מהותי שאין default בטוח עבורו.
- בדיקה דטרמיניסטית שנשארת כושלת לאחר bounded rework.
- פעולה בלתי־הפיכה/הרסנית ללא rollback.
- H200/GPU/cloud/remote/production.
- חריגה מתקציב OpenRouter שאושר מראש.

Circuit breaker אינו מוחק התקדמות: נשמר checkpoint, evidence ו־next action מדויק.

## גבולות

- חלק 1 מקומי בלבד.
- אין H200/GPU/cloud/remote, ‏G7/G8 או production.
- אין שליחת קלט לקוח רגיש ללא privacy approval.
- אין שינוי secrets/permissions אוטומטי לאחר ההגדרה הראשונית.
- אין force-push, history rewrite או מחיקת branches.

## תנאי activation

1. OpenRouter privacy policy מאפשרת endpoint שתומך tools עבור Pro.
2. chat, model identity, reasoning, tool call, JSON ו־Hermes CLI probes עוברים.
3. תקציב OpenRouter וגבול פרטיות מאושרים.
4. board משקף Full Part 1 ולא רק WP0–WP6.
5. tests, Git, worktrees ו־observer עוברים preflight.
6. משה נותן activation יחיד ל־Full Part 1.

לאחר סעיף 6 אין שערי אישור שגרתיים עד דוח הסיום.
