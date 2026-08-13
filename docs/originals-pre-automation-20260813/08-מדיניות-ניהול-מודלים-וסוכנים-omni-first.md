# מדיניות ניהול מודלים וסוכנים — Omni-First

## סטטוס וסמכות

- Policy ID: `MODEL-AGENT-MANAGEMENT-v2`
- סטטוס: `APPROVED FOR AUTOMATION PREPARATION`
- בתוקף: מ־2026-08-13 ועד הודעה חדשה של משה.
- תחולה: PanoWorld Automation, חלק 1 המקומי, לרבות WP0–WP6.
- מסמך זה משלים את `06-מדיניות-ניתוב-מודלים-ומאמץ.md`. במקרה של סתירה זמנית לגבי זהות המתזמר או fallback עקב אי־זמינות Anthropic, מסמך זה גובר עד הודעה חדשה.
- מסמך זה מגדיר מדיניות בלבד. הוא אינו מפעיל את האוטומציה ואינו מאשר לבדו WP, deployment או route activation.

## החלטת הניהול הנוכחית

**OmniRoute הוא שכבת התכנון, הניתוב והניהול הראשית של הקמפיין.**

עד הודעה חדשה:

1. כל תכנון מקצה לקצה, פירוק משימות, ניהול dependencies, בחירת סוכנים, retries, checkpoints ו-handoffs ינוהלו דרך פרופיל PanoWorld המחובר ל־OmniRoute.
2. כאשר Anthropic זמינה ומתאימה לתפקיד, OmniRoute ינתב אליה את המשימה.
3. כאשר Anthropic אינה זמינה עקב quota, ‏HTTP 429, outage, auth failure, timeout או העדר המודל הנדרש, העבודה **לא תיעצר רק בשל אי־הזמינות**: OmniRoute ימשיך באמצעות מודל מתאים הזמין דרכו.
4. אין fallback שקט. בכל run יירשמו המודל והספק שהתבקשו, המודל והספק שהופעלו בפועל, סיבת ה־fallback והאם נדרשת ביקורת משלימה.
5. מעבר למודל חלופי אינו מתיר להחליש acceptance criteria, tests, security, evidence או scope.

## הבחנה מחייבת: OmniRoute לעומת מודל

OmniRoute הוא מנהל ונתב; הוא אינו הוכחה לזהות המודל שביצע את העבודה. לכן בכל משימה יש להפריד בין:

- `ORCHESTRATOR`: ‏OmniRoute.
- `REQUESTED_PROVIDER/MODEL`: היעד המועדף.
- `ACTUAL_PROVIDER/MODEL`: הזהות שהוחזרה ב־runtime metadata או logs מוסמכים.
- `FALLBACK_REASON`: מדוע היעד המועדף לא הופעל.

אסור להסיק את זהות המודל מטקסט חופשי שהמודל כתב על עצמו.

## סדר הניתוב

### 1. תכנון וניהול הקמפיין

- מנהל ראשי: OmniRoute.
- אחריות: dependency graph, סדר WP, חלוקת תפקידים, budget, checkpoints, retries, status ו-handoffs.
- המודל הפנימי ייבחר לפי זמינות והתאמה, תוך רישום הזהות בפועל.

### 2. משימות spatial/geometry/3D קריטיות

סדר מועדף:

1. Anthropic Opus ברמת המאמץ הגבוהה הזמינה.
2. אם Anthropic אינה זמינה: מודל reasoning/spatial מתקדם הזמין דרך OmniRoute.
3. אם גם חלופה כשירה אינה זמינה: חסימה טכנית מתועדת, ללא המצאת evidence וללא החלשת gate.

כאשר בוצע fallback מ־Anthropic, יש לסמן את התוצר `FALLBACK_REVIEW_REQUIRED` ולדרוש ביקורת נוספת של מודל מתקדם אחר לפני סגירת gate קריטי, כאשר ספק כזה נעשה זמין. אין צורך לעצור עבודה הפיכה שאינה סוגרת gate.

### 3. תכנון מערכות, contracts, security ו-debugging מורכב

- OmniRoute יבחר מודל reasoning מתקדם.
- Anthropic מועדפת כאשר היא זמינה ומתאימה.
- אחרת ממשיכים דרך OmniRoute עם החלופה הכשירה ביותר.
- שינוי contract או boundary עדיין כפוף למדיניות האישור האנושי במסמך האוטומציה.

### 4. מימוש, tests ו-refactor

- OmniRoute ינתב למודל coding מתאים.
- אין חובה להמתין ל־Anthropic אם מודל coding כשיר זמין דרך OmniRoute.
- כל שינוי קוד כפוף ל־TDD, tests רלוונטיים, diff review ו-checkpoint.

### 5. ביקורת עצמאית

- ברירת המחדל היא reviewer שונה מהמחבר, ועדיפות לספק שונה.
- אם Anthropic זמינה והיא אינה המחבר: ניתן להשתמש בה לביקורת.
- אם Anthropic אינה זמינה: OmniRoute יבחר reviewer מתקדם אחר שאינו אותו agent/session של המחבר.
- אם אין ספק שני זמין, מותר לבצע ביקורת עצמאית באמצעות session ומודל שונים דרך OmniRoute, אך יש לרשום `SAME-PROVIDER EXCEPTION`.
- artifact קריטי אינו נסגר על סמך self-review בלבד.

### 6. משימות מכניות

עדכוני state, formatting, סיכומים ובדיקות קישורים יכולים לרוץ במודל חסכוני דרך OmniRoute. מודל כזה אינו רשאי להכריע geometry, security, contracts או gate קריטי.

## סוגי סוכנים ואחריות

| סוכן | אחריות | הרשאות עיקריות | איסורים |
|---|---|---|---|
| Omni Orchestrator | תכנון כולל, routing, dependencies ו-state | יצירת briefs, הקצאה, retries טכניים ו-checkpoints | שינוי scope או עקיפת human gate |
| Planner/Architect | תוכניות, contracts ו-ADRs | קריאה, ניתוח וכתיבת תוכנית | implementation לפני שהשלב מורשה |
| Implementer | קוד ושינויים תחומים | TDD, tests ו-commit/checkpoint | self-merge או הרחבת scope |
| Tester | אימות acceptance ו-failure paths | tests ו-evidence | החלשת assertions כדי להשיג pass |
| Reviewer | ביקורת עצמאית | read-only pass ראשון וממצאים מדורגים | תיקון שקט במהלך review ראשון |
| Fix Agent | תיקון findings שאושרו | שינוי תחום ומבחנים חוזרים | דחיית finding ללא נימוק מתועד |
| Orchestrator/Merger | reconciliation ו-handoff | אימות commit ומיזוג מורשה | merge ללא evidence וביקורת |
| Reporter/Observer | סטטוס והתראות | קריאה ודיווח | unblock, dispatch או שינוי כרטיסים |

## כללי fallback

Fallback אוטומטי מותר רק כאשר כל התנאים הבאים מתקיימים:

1. הכשל הוא טכני או זמינותי, לא כשל איכות או security.
2. החלופה נמצאת ברשימת המודלים הזמינים של OmniRoute ומתאימה לסוג המשימה.
3. scope, tests, thresholds ו-gates נשארים ללא שינוי.
4. נשמר runtime evidence של הכשל ושל זהות החלופה.
5. מספר הניסיונות מוגבל; ברירת המחדל היא עד שלושה ניסיונות עם backoff.
6. אין שימוש ב־GPU, cloud, שירות בתשלום או provider חדש שאינו מאושר במסגרת חלק 1.

Fallback אוטומטי אסור כאשר:

- נדרש שינוי scope או contract.
- tests או acceptance נכשלו מהותית.
- קיימת בעיית security, זכויות, credentials או פרטיות.
- אין הוכחה לזהות המודל בפועל.
- החלופה תוביל להפעלת route, deployment, תשלום או עבודה מחוץ לחלק 1.

## Evidence חובה לכל run

```text
TASK_ID:
AGENT_ROLE:
ORCHESTRATOR: OmniRoute
REQUESTED_PROVIDER:
REQUESTED_MODEL:
ACTUAL_PROVIDER:
ACTUAL_MODEL_ID:
EFFORT_REQUESTED:
EFFORT_ACTUAL:
FALLBACK_OCCURRED: yes/no
FALLBACK_REASON:
SESSION_OR_RUN_ID:
AUTHOR_IDENTITY:
REVIEWER_IDENTITY:
TESTS_AND_EVIDENCE:
CHECKPOINT:
```

אם runtime metadata אינו מוכיח את `ACTUAL_PROVIDER` ו־`ACTUAL_MODEL_ID`, אין לטעון שהמודל המבוקש הופעל.

## זמינות Anthropic

Anthropic נחשבת זמינה רק לאחר probe או run אמיתי שהחזיר תשובה תקינה מהמודל הנדרש. עצם קיום credential או הופעת מודל ברשימה אינו מספיק.

אירועים כגון 429 או quota exhaustion יירשמו כ־`ANTHROPIC_UNAVAILABLE_TEMPORARY`. במקרה כזה OmniRoute ממשיך לפי מדיניות ה־fallback לעיל. חזרת Anthropic לזמינות אינה מבטלת תוצרים תקינים שנוצרו דרך OmniRoute, אך מאפשרת ביקורת משלימה במקום שבו סומן `FALLBACK_REVIEW_REQUIRED`.

## גבולות שאינם משתנים

- חלק 1 נשאר local-only.
- אין H200/GPU/cloud/remote execution, ‏G7/G8, ‏PLAN-003 או הוצאה כספית בלי אישור חדש.
- אין מחיקת נתונים, שינוי credentials או הרשאות ללא אישור אנושי.
- אין route activation, production deployment או self-merge אוטומטי.
- אין החלשת gates כדי למנוע עצירה.
- החלטות בלתי־הפיכות נשארות בידי משה.

## שינוי המדיניות

- משה רשאי לשנות את קדימות Anthropic/OmniRoute בכל עת.
- שינוי קבוע של גבולות, מודלי 3D מועדפים או חריגי review יירשם ב־ADR.
- עד שינוי מפורש, הכלל הפעיל הוא: **OmniRoute מתכנן ומנהל; Anthropic מופעלת כאשר היא זמינה; כאשר אינה זמינה ממשיכים דרך OmniRoute עם חלופה כשירה ומתועדת.**
