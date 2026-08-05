# AGENT REPORT — plan-reviewer (SESSION-001, ביקורת בלתי תלויה על PLAN-000)

> נשמר verbatim על ידי ה-Orchestrator. ‏Requested: ספק שונה מהמחבר (OpenAI) — לא זמין בממשק; ‏Actual: Anthropic Fable 5 — מודל שונה מהמחבר (Opus 5), אותו ספק; ‏D-009 נשאר פתוח. ‏Verdict: ‏NEEDS_REWORK. **כל הממצאים C-1, M-1..M-4 והמינורים יושמו ב-PLAN-000 באותו סשן** — ראו "Review record" בסוף PLAN-000.

---

AGENT: plan-reviewer
ROLE: Independent Plan Reviewer
REQUESTED_MODEL: different provider than author (OpenAI) — unavailable; internal review pass
ACTUAL_MODEL: Claude Fable 5 (claude-fable-5), Anthropic — as declared by the runtime environment (author of PLAN-000 was claude-opus-5[1m]; different model, same provider; D-009 remains open)
STATUS: REVIEW
VERDICT: NEEDS_REWORK — ממצא CRITICAL אחד (C-1) הופך את AC2 לבלתי-ניתן-להשגה כפי שנכתב, ו-4 ממצאי MAJOR. כל התיקונים מקומיים (T6, §6, §7) ואינם משנים את הארכיטקטורה או את 15 ההכרעות; לאחר תיקונם התוכנית ראויה להגשה למשה.

FINDINGS:

1. [CRITICAL] C-1 — ה-fixture המוזהב של T6 סותר את בדיקות ה-validator שהתוכנית עצמה מחייבת; AC2 בלתי-ניתן להשגה כפי שנכתב.
   Evidence: PLAN-000 §7 T6 קובע "viewpoints 0001+0003 + map_panoworld0.json"; אבל panoworld-compat §5 מאמת ש-`map_panoworld0.json` = `{"0000": ["0001","0008","0011"]}`. סגירת ההפניות של המפה היא {0000, 0001, 0008, 0011} — ואילו תת-הסט המובא הוא {0001, 0003}. לפי panoworld-compat §Implications (שאותם T8 מאמץ במפורש: "Validate every key AND every value resolves to an existing viewpoints/<name>/ directory"), ה-validator חייב להיכשל על ה-fixture הזה: המפתח 0000 והערכים 0008/0011 לא קיימים, ו-0003 (ששייך ל-map1) אינו מוזכר באף מפה. לכן AC2 ("ה-validator עובר על Layer B... ירוק") לא יכול לעבור — והסיכון המעשי הוא בדיוק מה ש-doc 04 אוסר: החלשת assertions כדי לקבל ירוק. שורש הבעיה: T6 אימץ את המלצת test-architect §2 ("viewpoints 0001+0003 at minimum") בלי להצליב מול תוכן המפות שאימת panoworld-compat — שני הדוחות לא הוצלבו.
   תיקון מוצע: (א) להביא את הסגירה המלאה של map0 — viewpoints 0000+0001+0008+0011 (~8.5MB ללא style panos), או את הסגירה של map_panoworld2.json ‏({"0014": ["0016","0022"]}, 3 viewpoints); (ב) להגדיר במפורש מצב "scene-only" ל-validator (ללא config) שבו בדיקת start-image מדולגת, או לספק קובץ style סינתטי ל-start node; (ג) אם בכל זאת בוחרים מפה מצומצמת — לתעד אותה כ-derived ולא כ-vendored verbatim.

2. [MAJOR] M-1 — ל-`schemas/remote_job/v1/` אין task מייצר ואין AC.
   Evidence: §6 מונה את הקובץ; §5 C10 מגדיר אותו כתוצר מחייב; §6 הערה: "remote_job ו-envelope בנפרד" — כלומר הוא אינו בין "12 ה-schemas" של T5, ו-envelope מיוצר ב-T3, אבל אף שורה ב-T1–T12 אינה מייצרת את remote_job, ואף AC (AC1–AC8) אינו בודק אותו. חומרה מוגברת: זהו בדיוק החוזה שנושא את הטיפול בממצא הקריטי 3 של contract-researcher ‏(H200 secrets/TTL, §10 שורה 2) — הטיפול הביטחוני נשען על קובץ שאין לו owner. תיקון: לצרף ל-T5 (13 schemas) או task ייעודי + כיסוי ב-AC4.

3. [MAJOR] M-2 — רשימת "Exact files planned" (§6, "ייווצרו **רק** הקבצים הבאים") אינה שלמה — לפחות 6 קבצים שהתוכנית עצמה דורשת חסרים בה.
   Evidence: ‏uv.lock ‏(T2: "pyproject + lock"); ‏schemas/README ‏(T3: "README קצר ב-schemas/"); ‏contracts/README ‏(§10 מפנה אליו פעמיים — עקרון ה-Blender-sandbox ועקרון ה-parsing הדטרמיניסטי "נרשמים ב-contracts/README"); ‏tests/golden/NOTICE ‏(T11); ‏fixture-metadata.json ‏(T6); סקריפט ה-harness של T10 ("סקריפט קצר ב-tools"); וקבצי evidence/PLAN-000/* ‏(§13). השלכת אבטחה: contracts/README הוא ה-artifact היחיד ב-PLAN-000 שבו עקרון ה-sandbox של Blender (ממצא קריטי 2) אמור להירשם — וכרגע אף task לא יוצר אותו. (ההפניה ל-ARCHITECTURE TB-2 תקפה — אומתה בקובץ docs/ARCHITECTURE.md שורה 67 — אבל ה-README המובטח יתום.)

4. [MAJOR] M-3 — TDD לא תוכנן, בניגוד לדרישה מפורשת של פרומפט הסשן.
   Evidence: ‏SESSION-001-START-PROMPT "איכות PLAN-000": "יש לתכנן TDD ו-cross-provider review". ‏cross-provider מטופל (D-009), אבל המילה TDD אינה מופיעה בתוכנית כלל, ו-§7 קובע "סדר ביצוע מחייב" שבו T8 (מימוש validator) קודם ל-T9 (בדיקות) — implementation-then-test. תיקון: לקבוע ש-T7–T9 מתבצעים בשזירה red-green (הבדיקות נכתבות כנגד error_codes.md לפני מימוש כל check), או לתעד סטייה מנומקת.

5. [MAJOR] M-4 — התוכנית מאמצת את 15 מקרי הכשל של test-architect ואת ה-checks של panoworld-compat בלי ליישב שתי סתירות ביניהם.
   Evidence: (א) מקרה 7 — ‏test-architect §3 ממליץ "VIEWPOINT_NOT_IN_MAP — hard error by default", אבל panoworld-compat §Implications קובע "Warn... allowed — the demo has 0019/0021"; אם זו שגיאה קשה, scene0000 האמיתי נכשל, בסתירה ל-AC2. (ב) מקרה 15 — "conflicting map entries" נותר בלתי-מוגדר (test-architect עצמו כתב "the validator must define what 'conflicting' means"), בעוד ש-scene0000 האמיתי מכיל את המפתח 0000 בשתי מפות שונות עם ערכים שונים (map0 ו-map1) — לגיטימי לפי panoworld-compat §5. ‏AC3 דורש שכל 15 המקרים יחזירו קוד שגיאה — בלי הגדרת הסמנטיקה, AC3 ו-AC2 עלולים להתנגש. תיקון: לקבוע בטבלת T8/error_codes את החומרה (7=WARN כברירת מחדל) ואת הגדרת ה"קונפליקט" (תוך-מפה בלבד, לא בין-מפות).

6. [MINOR] m-1 — אי-התאמה מספרית: §5 C9 מציין ‏"~6–40MB" ל-Layer B, בעוד T6 מציין "~4.5MB" — מחוץ לטווח המוצהר. (יתוקן ממילא עם C-1: סגירת map0 ≈ 8.5MB, בתוך הטווח.)

7. [MINOR] m-2 — סדר משימות מול תנאי A4: ‏A4 (§3) דורש "NOTICE + SHA מוצמד" לפני commit של Layer B, אבל T11 ‏(NOTICE) ממוקם אחרי T6 בסדר "מחייב". יש להצמיד את T11 ל-commit של ה-fixture או לציין ש-T6 הוא fetch בלבד ללא commit.

8. [MINOR] m-3 — פריט C-12 של פרומפט הסשן דורש license review "עבור GPL, weights ו-datasets"; ‏C12/T11 מכסים fixture/Apache/MIT/other ודוחים matrix לשלב 12, אבל GPL ‏(FloorplanToBlender3d, ‏D-004) אינו מוזכר בתוכנית במילה. שורה אחת שמפנה ל-D-004/שלב-12 סוגרת זאת.

9. [MINOR] m-4 — בדיקת T4 אומרת "schema-valid" עבור state_machine.yaml, אבל אף task אינו יוצר meta-schema ל-YAML הזה. להחליף ל"בדיקת מבנה בקוד (test)" או להוסיף meta-schema לרשימת הקבצים.

10. [MINOR] m-5 — עקביות מזהים (doc 04: "אותו ID חייב להופיע ב-branch, commits, reports ו-evidence"): שלושה slugs שונים — ‏plan id מלא, branch ‏`plan/PLAN-000-bootstrap`, evidence ‏`evidence/PLAN-000/`. לקבע צורה קנונית קצרה (PLAN-000) ולהצהיר עליה.

11. [MINOR] m-6 — ‏Apache-2.0 מחייב צירוף עותק הרישיון עצמו בהפצה חוזרת, לא רק NOTICE/attribution; ‏T11 צריך לכלול גם עותק LICENSE של upstream לצד ה-NOTICE.

CHECKLIST_15_DECISIONS:

| # | החלטת שלב C | מכוסה? | היכן | הערה |
|---|---|---|---|---|
| 1 | Git — האם ומתי | כן, מוצדק | C1, T1, D-001 | — |
| 2 | מבנה תיקיות מדויק | כן | C2, §6 | הרשימה חסרה 6 קבצים (M-2) |
| 3 | שפת backend + Python מבודד | כן, אומת | C3, A1, T2; preflight §A5 (uv 0.11.26) | — |
| 4 | Workflow engine + spike | כן — דחייה מנומקת | C4 (D-002 opt C) | תואם "spike ולא בחירה שיווקית" |
| 5 | Storage/state ל-MVP | כן | C5 (D-003 opt A) | — |
| 6 | Artifact storage + immutable runs | כן | C6 (data dir ASCII מחוץ ל-git, SHA256SUMS, env.json) | סוגר ממצאים 10-11, 14-15, 19 |
| 7 | Schema versioning | כן | C7 (D-008, envelope+semver+bundle) | — |
| 8 | Test framework + golden fixtures | כן | C8, C9 | — |
| 9 | סצנות דוגמה בלי הורדת מודלים | כן — אך פגום | C9, T6 | תת-הסט שגוי (C-1) |
| 10 | Mock H200 interface | חלקית — חוזה בלבד, דחייה מנומקת | C10 | אין task/AC ל-remote_job (M-1) |
| 11 | Security boundaries | כן | C11, §10 | contracts/README יתום (M-2) |
| 12 | License review: GPL/weights/datasets | חלקית | C12, T11, D-010 | GPL לא מוזכר (m-3) |
| 13 | Model staffing לפי MODEL-ROUTING-v1 | כן | C13, §8 | תואם טבלת ה-Fallbacks של doc 06 |
| 14 | Worktree/branch strategy | כן | C14 | תואם doc 03 §אסטרטגיית ענפים |
| 15 | Rollback/cleanup | כן | C15, §12 | — |

CHECKLIST_MANDATORY_SECTIONS:

| סעיף נדרש (שלב D פריט 1) | קיים? | הולם? |
|---|---|---|
| Goal | §1 | כן — משפט אחד מדיד |
| Current verified state | §2 | כן — כל שורה עם evidence path תקף (אומת מול preflight ושלושת הדוחות) |
| Assumptions | §3 | כן — לכל הנחה owner ותנאי אימות, כנדרש |
| Scope / Non-goals | §4 | כן — ה-Non-goals מכסים את כל מגבלות הסשן |
| Architecture candidates + trade-offs | §5 | כן |
| Exact files planned | §6 | קיים; לא מדויק (M-1, M-2) |
| Tasks קטנים ומסודרים | §7 | קיים; בעיות סדר/כיסוי (M-3, m-2, C-1) |
| Model/provider/effort לכל תפקיד | §8 | כן — כולל מגבלת הממשק ו-fallbacks מתועדים |
| Acceptance criteria | §9 | קיים; AC2 בלתי-ניתן להשגה כפי שנכתב (C-1) |
| Tests + expected evidence | §13 | כן |
| Security/license risks | §10 | כן — ראו M-2 על artifact הנחיתה |
| Blockers/open decisions | §11 | כן — מיזוג אישורי D-001/D-008/D-010 מוצהר בשקיפות |
| Rollback | §12 | כן |
| Definition of Done | §14 | כן — תואם doc 04, נשאר REVIEW, לא אושר עצמית |
| (איכות) הגדרת POC מוצלח | §5 | כן — מדיד, על תוכנית אחת |
| (איכות) TDD + cross-provider | §8/§11 | cross-provider כן (D-009); TDD לא (M-3) |

בדיקות רוחב נוספות: (e) שני הממצאים הביטחוניים הקריטיים מטופלים ברמת החוזה באופן אמיתי ולא רק מסופר — scene_geometry כ-interface יחיד + שדות חובה ttl/cost/heartbeat/terminate ב-remote_job — אך שניהם נשענים על קבצים יתומים (M-1, M-2). (f) סטטוסים: רק אוצר המילים של doc 04; התוכנית ב-REVIEW; ‏PROJECT-STATE.yaml תואם (status: REVIEW, branch: null). (g) כל 12 טענות ה-"verified" ב-§2 מפנות לנתיבי evidence קיימים שנפתחו ואומתו תוכנית; הקישורים היחסיים מ-docs/plans/ נפתרים נכון.

MISSED_RISKS:

1. מקרה כשל 12 ‏(INVALID_FILENAME_ENCODING, שם קובץ non-UTF-8) ככל הנראה בלתי-ניתן למימוש כמפורט על NTFS ‏(מערכת קבצים UTF-16 — אי אפשר ליצור רצפי בתים לא-חוקיים כמו ב-Linux). יש להגדיר מחדש ל-Windows: שמות שמורים (CON/NUL), נקודה/רווח סופיים, או unpaired surrogates.
2. ‏snapshot של דוח ה-validator ‏(AC2) עלול להטמיע נתיבים אבסולוטיים — שיכילו את הנתיב העברי — ולשבור את ההשוואה בין הרצות/מכונות. לחייב נרמול לנתיבים יחסיים-ל-scene בדוח לפני snapshot.
3. בדיקת "viewpoint budget מול טבלת VRAM" ב-T8 מקבעת בחוזה מספרים מהמדריך המקומי, שלא אומתו מול מקור ראשוני (arXiv ללא מספרים, לפי panoworld-compat §9). הבסיס המאומת היחיד הוא `viewpoint_max_view: 8` מה-config. מומלץ: הבדיקה המאומתת כ-error, טבלת ה-VRAM כ-WARN בלבד.
4. ‏T2 דורש רשת (uv מוריד CPython 3.11 ל-%LOCALAPPDATA% על כונן C); אין לכך fallback מתועד, ו-rollback ‏`uv python uninstall 3.11` (§12) הוא גלובלי למכונה — עלול לפגוע בפרויקטי uv אחרים שמשתמשים ב-3.11.
5. ‏cad_mcp.log נכתב באופן פעיל לשורש הריפו ע"י שרת MCP חיצוני תוך כדי הסשן (preflight §A3) — מכוסה ב-.gitignore, אבל בדיקת "git status נקי" (AC7) עלולה להיכשל חולף על קבצים זמניים של אותו שרת; כדאי דפוס exclusion רחב יותר או בדיקה מסוננת.
6. ‏raw.githubusercontent עם SHA מוצמד — תקין, אבל ה-repo נדחף יום לפני הסשן (pushed_at 2026-08-04); את ה-SHA יש לקבוע ברגע ההרצה של T6 ולא לשאוב מדוחות שלב B (כפי ש-test-architect עצמו הזהיר ב-OPEN_QUESTIONS 4 — אזהרה שלא שוקפה בגוף T6).

EVIDENCE (files actually read, in full unless noted):

- docs\plans\PLAN-000-repository-bootstrap-and-contracts.md — מלא (211 שורות)
- SESSION-001-START-PROMPT.txt — מלא; שלב C (שורות 92-108), שלב D פריט 1 (שורות 113-128), איכות PLAN-000 (שורות 169-175)
- evidence\SESSION-001\agent-reports\contract-researcher.md — מלא (20 ממצאים + המלצות)
- evidence\SESSION-001\agent-reports\panoworld-compat.md — מלא; §5 (תוכן המפות — הבסיס ל-C-1), §Implications
- evidence\SESSION-001\agent-reports\test-architect.md — מלא; §2 Layer B, §3 מקרים 7/15
- docs\OPEN-DECISIONS.md — מלא (D-001..D-010)
- docs\04-מתודיקת-ניהול-סוכנים-ומעקב.md — מלא (סטטוסים, DoD, gates, מזהים)
- docs\06-מדיניות-ניתוב-מודלים-ומאמץ.md — מלא (טבלאות routing/fallbacks)
- docs\03-תוכנית-בנייה-מפורטת-לפי-שלבים.md — מלא (שלב 0, סדר מימוש, אסטרטגיית ענפים)
- evidence\SESSION-001\preflight-report.md — מלא (A1-A6, ניתוב סוכני שלב B)
- docs\ARCHITECTURE.md — חלקי (grep TB-2, שורות 64-70 — אומת קיום TB-2)
- PROJECT-STATE.yaml — חלקי (grep — אומת status REVIEW, branch null, open decisions)

לא בוצע שום שינוי קובץ — הביקורת קריאה-בלבד כנדרש.
