# AGENT REPORT — contract-researcher (SESSION-001, Phase B)

> נשמר verbatim על ידי ה-Orchestrator מתוך דיווח הסוכן. ‏Requested: OpenAI GPT-5.6 EXTRA (לא זמין בממשק); ‏Actual: Anthropic Fable 5 ‏(fallback מתועד לפי MODEL-ROUTING-v1). ‏Effort: יורש מהסשן (לא ניתן לקביעה פר-סוכן בממשק).

---

AGENT: contract-researcher
ROLE: Contract/Systems Researcher
REQUESTED_MODEL: OpenAI GPT-5.6 (EXTRA) — unavailable in this interface
ACTUAL_MODEL: Claude Fable 5 (claude-fable-5), Anthropic — as declared by the runtime environment
STATUS: REVIEW

הערה למתזמר (להעברה למשה): כל הממצאים להלן מבוססי ציטוט (FACT) או מסומנים כהמלצה (OPINION). לא בוצע שום שינוי קובץ. קראתי גם את doc 00, doc 02, התבניות ו-PROJECT-STATE.yaml כראיות תומכות. וידאתי ש-doc 06 קיים פיזית (לא נקרא לעומק — מחוץ ל-scope).

FINDINGS:

1. [CRITICAL] ה-state machine ליניארי בלבד — אין מעברי כשל/חזרה. FACT: doc 01 שורות 188–206 מגדירות שרשרת חד-כיוונית NEW→…→QA_REVIEW→APPROVED/REWORK/BLOCKED. REWORK ו-BLOCKED מופיעים רק כיעד סופי אחרי QA_REVIEW; אין הגדרה לאן REWORK חוזר, ואין BLOCKED ממצב ביניים (למרות ש-doc 01 שורה 128 מדבר על "blocker אם אין scale" כבר בשלב Intake). doc 01 שורה 217 דורש "כל retry משנה פרמטר אחד" אך אין state של retry. OPINION: בלי טבלת מעברים מלאה (כולל fail edges לכל gate) ה-orchestrator לא ניתן למימוש דטרמיניסטי.

2. [CRITICAL] הרצת Blender Python = הרצת קוד שרירותי ללא sandbox מוגדר. FACT: doc 01 שורות 134–137 (Geometry Agent יוצר גאומטריה "דרך Blender Python"), שורה 211 ("סקריפטים דטרמיניסטיים") ושורה 212 (Blender MCP לחריגים). אין בשום מסמך דרישת בידוד (container/WSL, ללא רשת, mount מוגבל), אין allowlist ל-API, ואין gate של code-review לסקריפט לפני הרצה. doc 02 שורה 45 מציין ש-Blender כלל לא מותקן — כלומר ההחלטה איך להריץ אותו טרם התקבלה. OPINION: סוכן LLM שמחולל סקריפט Blender פר-ריצה הוא RCE על המכונה של משה; חובה לקבע ב-PLAN-000 שסקריפטים הם תבניות מאושרות מראש שמוזנות מ-JSON בלבד.

3. [CRITICAL] "guaranteed shutdown in finally path" אינו guarantee, וסודות H200 בידי סוכן LLM. FACT: doc 03 שורה 247 ("guaranteed shutdown in finally path") ושורה 258 ("no orphan GPU instance"); doc 01 שורה 113 מציב את H200 Runner כסוכן LLM (GPT-5.6/Codex); doc 01 שורה 216 רק "secrets נשמרים מחוץ לריפו"; doc 04 שורה 148 ("חייב להבטיח shutdown של GPU"). אין: TTL/auto-stop בצד הספק, watchdog חיצוני לתהליך, תקרת עלות, הגדרת secret store, scoping של המפתח, או rotation. OPINION: קריסת התהליך/ניתוק רשת עוקפים finally; ההגנה חייבת להיות server-side. מפתח ענן צריך לשבת בשירות runner דטרמיניסטי דק, לא ב-context של סוכן.

4. [HIGH] רשימת 9 ה-artifacts אינה סגורה — קיים artifact עשירי לא מוכרז ועוד חוזים חסרים. FACT: doc 03 שורה 88 מוסיף `input_quality_report.json` שאינו ברשימת doc 01 שורות 88–96. חסרים חוזים לתוצרים ש-doc 03 מייצר: מועמדי source panorama + דירוג + provenance (doc 03 שורות 209–214 — אין artifact בשם מוגדר), דוח validator של control assets (doc 03 שורה 186), ו-SVG overlay (doc 03 שורה 109) שהוא ראיית gate G1 אך ללא חוזה. OPINION: כל תוצר שהוא תנאי gate חייב חוזה עם שם, schema וגרסה.

5. [HIGH] אין חוזה לרשומת אישור אנושי (approval record). FACT: doc 01 שורות 180–184 מגדירות שלוש נקודות אישור; PROJECT-STATE.yaml שורות 59–62 מחזיק רק pending/…; doc 04 אינו מגדיר artifact של החלטת אדם (מי, מתי, על איזה hash). רק qa_report.json כולל "החלטה" (doc 01 שורה 96). OPINION: בלי approval_record.json חתום על content_hash, הדרישה "אין מעבר state בלי artifact, validation וראיה" (doc 01 שורה 208) אינה ניתנת לאכיפה בשלושת ה-human gates.

6. [HIGH] G5 ממזג שני אישורים אנושיים נפרדים, ולמצב style אין state של אישור. FACT: doc 04 שורות 227–228 — G5 = "style spec ו-source panorama approval" בגייט אחד; אבל doc 03 שורות 203–204 (Gate אנושי לשלב 6) ושורות 215–217 (Gate אנושי לשלב 7) הם שני גייטים נפרדים; וב-doc 01 שורות 199–201 יש SOURCE_PANO_APPROVED אך אין STYLE_SPEC_APPROVED. שלושת המסמכים לא מסכימים. ראו טבלה בהמשך.

7. [HIGH] שני אוצרות-מילים של סטטוסים עם מונחים חופפים ומשמעות שונה. FACT: doc 04 שורות 17–31 מגדירות 11 סטטוסי עבודה (כולל BLOCKED, REWORK) ברמת PLAN, בעוד doc 01 שורות 188–206 משתמשות ב-BLOCKED/REWORK כמצבי pipeline של ריצה. RUN-REPORT.md שורה 67 משתמש ב-APPROVED/REWORK/BLOCKED. OPINION: בלי הפרדה מפורשת (למשל קידומת RUN_*) סוכנים יערבבו סטטוס תוכנית עם מצב ריצה — בדיוק סוג ה-drift ש-doc 04 מנסה למנוע.

8. [HIGH] `assumptions.json` הוא artifact מרובה-כותבים בסתירה לעקרון הבעלות הבלעדית. FACT: doc 01 שורה 91 ("כל ערך שהמערכת הניחה" — Intake, Vision, Geometry, Style כולם מניחים הנחות: שורות 132, 141 ו-doc 03 שורות 88, 140–141), מול doc 03 שורה 332 ("ownership בלעדי לקבצים"). OPINION: להגדיר assumptions כ-append-only per-stage (assumptions/<stage>.json) או כרשומות בתוך כל artifact, לא קובץ יחיד משותף.

9. [HIGH] חוזה camera_plan חסר תקציב VRAM/מספר-מבטים — סיכון OOM מתועד. FACT: המדריך, סעיף 4 (שורות 103–109): LRM עם 12 תצוגות ב-2048x1024 = OOM גם על H200 141GB; 8 תצוגות 2048 = ‏108.4GB. doc 01 שורה 92 ו-doc 03 שורות 144–161 אינם מזכירים מגבלת מספר viewpoints או רזולוציה כשדה חוזה או כבדיקת gate G3. OPINION: camera_plan.json חייב שדות resolution + view-count budget ו-validator שמצליב מול טבלת הזיכרון של PanoWorld.

10. [HIGH] מיקום האחסון של ה-artifacts לא מוגדר — runs/ ו-evidence/ בתוך עץ git עם binaries כבדים. FACT: doc 03 שורות 35–36 שמות runs/ ו-evidence/ בריפו; doc 04 שורות 53–65 מפרטות layout; המדריך שורות 256–259 — ‏64GiB מודלים + מאות GB תוצרים; doc 02 שורה 78 ("artifacts גדולים בדיסק D") ושורה 76 מציעה MinIO — אך אין החלטה (git? LFS? object store?). OPINION: להכריע ב-PLAN-000; אחרת ה-immutability תישבר בפועל.

11. [HIGH] לא מוגדר היכן חיים 9 חוזי הביניים ביחס ל-runs/<run-id>. FACT: doc 04 שורות 53–59 מפרטות ב-run רק run_manifest, logs, inputs, outputs, metrics, qa_report — אין artifacts/ עבור floorplan_parse, scene_geometry, camera_plan וכו', ואין layout ברמת project (project_manifest הוא פר-פרויקט, doc 03 שורה 65). גם ברשימת המזהים (doc 04 שורות 69–74) אין פורמט project-id. OPINION: להוסיף projects/<project-id>/ + runs/<run-id>/artifacts/ וקישור run→project ב-run_manifest.

12. [MEDIUM] סמנטיקת שגיאה/תוצאה-חלקית אינה מוגדרת באף חוזה. FACT: doc 03 שורה 68 מזכיר "state machine וקודי שגיאה" כפריט לבנייה, doc 01 שורה 131 מזכיר confidence פר-ישות, doc 03 שורה 276 מזכיר "retry ממוקד עם reason code" — אך אין הגדרת envelope לשגיאה, אין דגל partial, אין ספי confidence, ואין חוזה retry_request (doc 01 שורה 177 מזכיר "retry request ממוקד" ללא schema). templates/BLOCKER.md הוא markdown, לא מכונה-קריא.

13. [MEDIUM] כפילות panoworld_manifest.json מול map_panoworld*.json ללא הגדרת יחס. FACT: doc 01 שורה 94 ("מיפוי מלא לקלטי PanoWorld") מול doc 03 שורה 223 (מחולל map_panoworld*.json) והמדריך שורות 179–187 (הפורמט ש-PanoWorld באמת קורא). לא מוגדר מי הנגזר של מי ומי מאמת עקביות ביניהם.

14. [MEDIUM] תפיסת סביבה מכונה-קריאה חסרה ב-run layout. FACT: RUN-REPORT.md שורות 14–20 תופס env כ-markdown ידני; doc 03 שורה 259 ("logs, config, model hashes ו-runtime נשמרים") חל על שלב 9 בלבד; רינדור מקומי (שלב 5, שורות 179–183 דורש repeatability עם seed) ללא דרישת env capture מקבילה. OPINION: להוסיף env.json (versions, docker digest, CUDA, blender, pip freeze) חובה בכל run.

15. [MEDIUM] אין hash-manifest כולל לריצה. FACT: doc 01 שורה 95 — run_manifest כולל "hashes" בלי הגדרת היקף; doc 03 שורה 235 — "package hash קבוע" לחבילה בלבד. OPINION: SHA256SUMS על כל inputs/, artifacts/ ו-outputs/ + שרשור hash של שרשרת ה-artifacts (כל artifact מפנה ל-hash של קודמיו) — זה מה שהופך "evidence" לניתן לאימות.

16. [MEDIUM] פלטי H200 הם data לא-מהימן — אין לכך התייחסות. FACT: אין בשום מסמך אזכור לכך שלוגים/JSON/תמונות שחוזרים מהשרת עוברים validation לפני שסוכן LLM (QA/Reporting) קורא אותם. OPINION: סיכון prompt-injection דרך תוכן artifact; ה-QA Agent צריך לצרוך תוצרים רק דרך parsers/metrics דטרמיניסטיים.

17. [MEDIUM] הנתיב העברי של הריפו מסוכן לכלי ה-pipeline. FACT: doc 02 שורה 74 מודה בכך ("לשמור על path קצר באנגלית... אם כלי מסוים נכשל בעברית"), אך doc 03 מציע ליצור runs/ ו-evidence/ בתוך `D:\משה פרוייקטים\...`. Blender headless, MMCV, וכלי CV ישנים הם בדיוק הכלים שנשברים על נתיבי unicode. OPINION: להחליט ב-PLAN-000 על נתיב עבודה ASCII (WSL clone או junction) לפני bootstrap.

18. [LOW] אין CANCELLED ברמת pipeline (קיים רק כסטטוס PLAN, doc 04 שורה 29), אין מצב "awaiting human" נפרד ל-QA_REVIEW, ואין א-סימטריה מוסברת: לגאומטריה יש GEOMETRY_REVIEW (doc 01 שורה 194) אבל ל-source panorama אין SOURCE_PANO_REVIEW.

19. [LOW] מדיניות retention/גיבוי ל-runs נדחית לשלב 12 (doc 03 שורות 301–308) בעוד דיסק C עם 56GB פנויים בלבד (doc 02 שורה 14) — כדאי לקבע "הכל ב-D" כחוק כבר בחוזה ה-layout.

20. [LOW] gates של doc 03 מוגדרים כטקסט חופשי ("validator ירוק", "overlay מאושר") בלי מיפוי לקודי G0–G9 של doc 04 — אין reference הדדי בין המסמכים (doc 03 אינו מזכיר G-IDs כלל).

STATE-GATE-STAGE MAP:

| doc 01 state | doc 04 gate | doc 03 stage | סטטוס |
|---|---|---|---|
| NEW | — | — (כניסה) | תקין |
| INGESTED | — | 1 Intake | פער: אין gate; ראיית intake לא מוגדרת |
| INPUT_VALIDATED | G0 Input | 1 Intake | תקין |
| FLOORPLAN_PARSED | G1 Parse | 2 Parsing | תקין |
| GEOMETRY_BUILT | — | 3 Geometry | state ללא gate (בדיקות שלב בלבד) |
| GEOMETRY_REVIEW | — | 3 Geometry | state ללא gate; מכוסה רק ע"י תהליך Review הכללי (doc 04 שורות 101–105) |
| GEOMETRY_APPROVED | G2 Geometry | 3 Geometry | תקין (human) |
| CAMERAS_PLANNED | G3 Camera | 4 Cameras | תקין; חסר קריטריון VRAM (ממצא 9) |
| CONTROL_ASSETS_RENDERED | G4 Render | 5 Rendering | תקין |
| STYLE_SPEC_READY | G5 (חלקי) | 6 Style | אי-התאמה: doc 03 דורש gate אנושי לשלב 6, אין state אישור ואין gate נפרד (ממצא 6) |
| SOURCE_PANO_READY | G5 (חלקי) | 7 Source Panorama | אין state של review מקביל לגאומטריה |
| SOURCE_PANO_APPROVED | G5 | 7 Source Panorama | אי-התאמה: G5 אחד מול שני gates אנושיים ב-doc 03 |
| PANOWORLD_PACKAGE_READY | G6 Package | 8 Packager | תקין |
| H200_SMOKE_PASSED | G7 Smoke | 9 Runner | אין מצב/מעבר לכשל smoke |
| FULL_GENERATION_COMPLETE | G8 Full Run | 9 Runner | תקין |
| QA_REVIEW | G9 Final QA | 10 QA | תקין |
| APPROVED | G9 עבר | 10 QA | תקין (טרמינלי) |
| REWORK | — | — | אי-התאמה: אין יעד חזרה מוגדר; מתנגש עם REWORK כסטטוס PLAN (doc 04 שורה 27) |
| BLOCKED | — | — | אי-התאמה: בדיאגרמה נגיש רק אחרי QA; בפועל נדרש מכל state (doc 01 שורה 128) |
| — | — | 0 Contracts | שלב בנייה, ללא state ריצה — תקין |
| — | — | 11 Dashboard | שלב בנייה — תקין |
| — | — | 12 Hardening | שלב בנייה — תקין |

סיכום אי-התאמות: 3 states ללא gate (INGESTED, GEOMETRY_BUILT, GEOMETRY_REVIEW); gate אנושי אחד ב-doc 03 (שלב 6) ללא state; G5 ממזג שני אישורים; REWORK/BLOCKED ללא סמנטיקת מעברים; אפס אזכור של קודי G ב-doc 03.

RECOMMENDATIONS_FOR_PLAN_000 (כולן OPINION):

1. טבלת מעברים קנונית אחת: לכל מעבר — from_state, to_state, gate_id, required_artifacts, validator, fail_target (REWORK עם target_state מפורש), והרשאת BLOCKED מכל state עם artifact חסם. רציונל: סוגר ממצאים 1, 6, 18, 20 והופך את ה-orchestrator לדטרמיניסטי.

2. Envelope אחיד לכל artifact: `schema_id`, `schema_version` (semver), `artifact_id`, `project_id`, `run_id`, `created_at`, `producer` (agent+provider+model+effort), `inputs: [{artifact_id, content_hash}]`, `content_hash`, `status: complete|partial|failed`, `errors[]` עם reason codes. רציונל: ממצאים 4, 12, 15 — versioning, שרשרת provenance וסמנטיקת partial במקום אחד.

3. אסטרטגיית גרסאות: JSON Schema draft 2020-12 בתיקיות `schemas/<name>/v<major>/<name>-<semver>.schema.json` עם `$id` מגורסן; MINOR/PATCH אדיטיביים בלבד (בדיקת CI); שבירה = MAJOR חדש + ADR; ובנוסף `contracts_bundle_version` יחיד שנרשם ב-project_manifest וב-run_manifest. Trade-off: semver פר-schema מדויק אך דורש מטריצת תאימות; גרסת bundle יחידה פשוטה אך מקפיצה הכל — ההיברידי נותן את שניהם במחיר שדה אחד.

4. השלמת חוזים חסרים: `input_quality_report.json` (ויישור רשימת doc 01 ל-10), `source_panorama_candidates.json`, `approval_record.json` (לשלושת ה-human gates, חתום על content_hash), `retry_request.json`, `render_validation_report.json`, ו-schema מכונה-קריא ל-blocker. רציונל: ממצאים 4, 5, 12.

5. הפרדת אוצרות מילים: מצבי pipeline יקבלו קידומת (למשל RUN_BLOCKED, RUN_REWORK) או namespace נפרד מסטטוסי PLAN של doc 04. רציונל: ממצא 7.

6. Layout אחסון: `projects/<project-id>/` + `runs/<run-id>/artifacts/` + `SHA256SUMS` + `env.json` חובה בכל run; runs/ ו-evidence/ מחוץ ל-git (MinIO/דיסק D) עם pointers-בלבד בריפו. רציונל: ממצאים 10, 11, 14, 15, 19.

7. Sandbox ל-Blender: הרצה headless בתוך container/WSL בלי רשת, mount של תיקיית ה-run בלבד; סקריפטים הם תבניות מאושרות-מראש שמקבלות אך ורק JSON מ-scene_geometry — אסור codegen פר-ריצה; מגבלות זיכרון/זמן. רציונל: ממצא 2 + תקדימי ה-OOM המתועדים אצל משה.

8. גבול סודות: שירות remote-runner דטרמיניסטי מחזיק את מפתח הענן (env/secret store מוגדר), חושף API מצומצם (create_job, status, cancel, download); סוכני LLM לעולם לא רואים את המפתח; TTL/auto-stop בצד הספק + תקרת עלות + watchdog חיצוני בנוסף ל-finally. רציונל: ממצא 3.

9. חוזה camera_plan יכלול `resolution`, `max_views_per_lrm_batch` ו-validator מול טבלת ה-VRAM של PanoWorld (המדריך סעיף 4); בדיקת G3 תיכשל על תוכנית שחורגת. רציונל: ממצא 9 — זה כשל שיתגלה רק על H200 בתשלום אם לא ייתפס מקומית.

10. הכרעת נתיב: לקבע ב-PLAN-000 נתיב עבודה ASCII קצר (WSL clone או junction ל-D:\pw-auto) לכל הרצת כלי-צד-שלישי, עם הריפו העברי כ-origin בלבד. רציונל: ממצא 17.

11. להגדיר את panoworld_manifest.json כמקור שממנו נגזרים map_panoworld*.json ומבנה viewpoints, עם round-trip validator (הקיים כבר כרעיון ב-doc 03 שורה 229). רציונל: ממצא 13.

12. assumptions כ-append-only פר-שלב (או רשומות בתוך כל artifact) עם מיזוג read-only לתצוגה. רציונל: ממצא 8.

OPEN_QUESTIONS:

1. האם ה-state machine הוא פר-project או פר-run? מה קורה בריצה שנייה על אותו project (שימוש חוזר בגאומטריה מאושרת)?
2. לאן REWORK חוזר — תמיד ל-state שנכשל, או לפי reason code (למשל כשל doorway consistency חוזר ל-CAMERAS_PLANNED ולא ל-QA)?
3. איזה artifact מהווה ראיה ל-INGESTED — project_manifest או דוח intake נפרד?
4. האם runs/ ו-evidence/ נכנסים ל-git (LFS?) או ל-object store, ומה מדיניות ה-retention?
5. איזה ספק ענן ל-H200 ואיזה secret store (env, SOPS, מנהל סודות של הספק)?
6. doc 01 שורה 83 מציע "מספר תמונות סגנון לחדרים מסוגים שונים" — האם style_spec.json תומך בריבוי רפרנסים פר-חדר? קרדינליות החוזה לא הוגדרה.
7. מי מוסמך ללחוץ approve ב-dashboard (doc 03 שורה 286) ואיך אישור אנושי מאומת (auth) ונרשם?
8. האם ספי confidence (doc 03 שורה 94 "confidence מתחת לסף") הם חלק מהחוזה (per-artifact) או config גלובלי — ומי בעל הסמכות לשנותם?

EVIDENCE:

- docs\01-חזון-וארכיטקטורת-האוטומציה.md — נקרא במלואו (219 שורות): רשימת artifacts (שורות 85–96), סדר סוכנים (98–184), state machine (186–208), עקרונות בטיחות (210–218).
- docs\03-תוכנית-בנייה-מפורטת-לפי-שלבים.md — נקרא במלואו (349 שורות): מבנה ריפו (8–37), שלבים 0–12 עם gates, סדר מימוש (310–326), אסטרטגיית ענפים (330–338), DoD (340–348).
- docs\04-מתודיקת-ניהול-סוכנים-ומעקב.md — נקרא במלואו (308 שורות): סטטוסים (17–31), layout של runs/evidence (35–66), מזהים (68–76), gates G0–G9 (210–240).
- docs\02-היתכנות-על-המחשב-הנוכחי-ולוחות-זמנים.md — נקרא במלואו (150 שורות): מפרט חומרה (8–22), מגבלות (40–47), סביבת פיתוח (72–79).
- PanoWorld-מדריך-והסבר.txt — נקרא במלואו (301 שורות): דרישות קלט פר-סצנה (סעיף 6, שורות 168–216), טבלת VRAM (103–116), סביבה (64–82), רישוי (292–300).
- ראיות תומכות: templates\PROJECT-STATE.yaml, templates\RUN-REPORT.md, docs\00-MASTER-INDEX.md — נקראו במלואם; Glob על שורש הפרויקט אימת קיום docs\06-מדיניות-ניתוב-מודלים-ומאמץ.md (לא נקרא — מחוץ ל-scope).
