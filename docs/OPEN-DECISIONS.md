# OPEN DECISIONS — PanoWorld Automation

- Status: פעיל. נוצר ב-SESSION-001.
- כלל: החלטה כאן היא **פתוחה**. כשמשה מאשר — היא הופכת ל-ADR תחת `docs/decisions/` ונמחקת/מסומנת כאן כ-RESOLVED. אין לממש על בסיס המלצה בלבד.
- Owner ברירת מחדל להכרעה: משה. ‏Owner להכנת החומר: כמצוין.

---

## D-001 — אתחול Git repository: מתי ואיך

- **Options:**
  - A. אתחול מיד עם אישור PLAN-000, בשורש הפרויקט הנוכחי, עם `.gitignore` המחריג runs כבדים, artifacts ו-`cad_mcp.log`.
  - B. דחייה עד תחילת כתיבת קוד (PLAN-001).
  - C. ‏repo נפרד בנתיב ASCII קצר (למשל `D:\dev\panoworld-automation`) והשארת מסמכי התכנון כאן.
- **Recommendation:** A — ‏Git הוא source of truth לפי מסמך 04, וכל דחייה משאירה את מסמכי התכנון בלי versioning. סיכון הנתיב העברי מטופל בכך שקוד ונתיבים פנימיים יהיו ASCII (ראו PLAN-000 §Risks). אם יתגלה כלי שנשבר על הנתיב — מעבר מבוקר ל-C יתועד כ-ADR.
- **Impact:** בסיס לכל ה-traceability; חוסם merge/branch strategy.
- **Owner (הכנה):** Orchestrator. **הכרעה:** משה באישור PLAN-000.

## D-002 — Workflow engine

- **Options:** ‏A. Prefect ‏(קל ל-MVP, ‏Python-native). ‏B. Temporal ‏(durable, כבד יותר תפעולית). ‏C. שלב ראשון ללא engine: ‏state machine מפורש + CLI runner דטרמיניסטי, ‏engine נבחר רק כשיש ≥2 workflows אמיתיים.
- **Recommendation:** C ל-POC, עם spike השוואתי Prefect/Temporal לפני MVP (כמתחייב ממסמך 03: "spike ולא בחירה שיווקית"). ההשוואה על תרחיש אמיתי: run של packager+validator עם retry ו-resume.
- **Impact:** משפיע על orchestrator, retries, observability. החלטה הפיכה יחסית אם ה-state נשמר בקבצים/DB ולא בתוך ה-engine.
- **Owner (הכנה):** ‏System Architect ‏(OpenAI GPT-5.6 לפי routing). **הכרעה:** משה אחרי ה-spike.

## D-003 — Storage/state ל-MVP

- **Options:** ‏A. קבצים בלבד ‏(PROJECT-STATE.yaml + JSON artifacts + ‏runs/). ‏B. SQLite ‏+ קבצים ל-artifacts. ‏C. Postgres+Redis+MinIO ב-Docker Compose מההתחלה.
- **Recommendation:** A ל-POC ‏(כבר מוגדר במסמך 04 ועובד עם Git); מעבר ל-B כשיש queries/concurrency אמיתיים; ‏C רק ב-MVP המתוזמר. אין להרים תשתית לפני שיש בה צורך מוכח.
- **Impact:** מורכבות תפעולית מקומית; קלות migration בהמשך.
- **Owner (הכנה):** ‏System Architect. **הכרעה:** משה ב-PLAN הרלוונטי.

## D-004 — Floorplan parser baseline

- **Options:** ‏A. CubiCasa5K adapter ‏(מודרניזציה נדרשת, stack ישן). ‏B. baseline היוריסטי ‏(FloorplanToBlender3d כרפרנס — ‏GPL, ‏בידוד נדרש). ‏C. VLM-assisted parsing עם validation דטרמיניסטי. ‏D. שילוב: התחלה ב-fixture ידני מסומן, ‏parser נבחר אחרי שה-contracts יציבים.
- **Recommendation:** D — ‏PLAN-000 בכוונה לא מכריע; ה-POC הראשון יכול לרוץ על parse ידני של תוכנית אחת כדי לא לחסום את שרשרת ה-geometry→package.
- **Impact:** דיוק, רישוי (GPL), עלות מודרניזציה.
- **Owner (הכנה):** ‏CV/Spatial Architect ‏(Opus 5). **הכרעה:** משה ב-PLAN-002 (parsing).

## D-005 — Source panorama provider

- **Options:** ‏A. API חיצוני ‏(image-to-image panorama). ‏B. מודל על שרת ענן זמני. ‏C. mock בלבד עד H200. ‏
- **Recommendation:** C לשלבי POC ‏(מסמך 02: "לא באיכות היעד מקומית"); הכרעה אמיתית רק כשמגיעים לשלב 7.
- **Impact:** איכות, עלות, תלות ספק.
- **Owner (הכנה):** ‏Visual Director ‏(Opus 5). **הכרעה:** משה בשלב 7.

## D-006 — ספק ענן H200

- **Options:** ייבחנו ספקים המציעים H200 יחיד לפי מחיר/שעה, אחסון NVMe, ‏API אוטומציה ומדיניות billing. (מסמך המדריך: "הספק פחות חשוב מהמפרט".)
- **Recommendation:** אין עדיין — נדרש מסמך השוואה קצר בשלב 9; עד אז כל הפיתוח מול mock.
- **Impact:** עלות, אבטחה, סיכון שרת יתום.
- **Owner (הכנה):** ‏Cloud/Systems Architect ‏(OpenAI GPT-5.6). **הכרעה:** משה לפני שכירה ראשונה.

## D-007 — Dashboard stack

- **Options:** ‏A. CLI + דוחות Markdown בלבד ל-POC. ‏B. אפליקציית web מקומית קלה. ‏C. תבנית ה-web הקיימת של משה (React+Vite) כשלב MVP.
- **Recommendation:** A ל-POC; ‏dashboard אמיתי רק בשלב 11 לפי סדר המימוש.
- **Impact:** נוחות פיקוח מול עלות פיתוח מוקדמת.
- **Owner (הכנה):** ‏Developer ‏(OpenAI Codex). **הכרעה:** משה בשלב 11.

## D-008 — אסטרטגיית schema versioning

- **Options:** ‏A. שדה `schema_version` ‏(semver) בכל artifact + ‏`schemas/<name>/<version>.json` בריפו + ‏CHANGELOG לכל schema. ‏B. גרסה בשם הקובץ בלבד. ‏C. registry מרכזי.
- **Recommendation:** A — מוצעת בפירוט ב-PLAN-000 §Contracts; פשוטה, ‏diffable ב-Git, ואינה דורשת תשתית.
- **Impact:** כל producer/consumer בפרויקט.
- **Owner (הכנה):** Orchestrator ‏(הצעה ב-PLAN-000). **הכרעה:** משה באישור PLAN-000.

## D-009 — ביצוע cross-provider review בפועל

- **הקשר:** ‏MODEL-ROUTING-v1 דורש review של OpenAI על תוצרי Anthropic קריטיים. הממשק הנוכחי (Claude Code) מאפשר סוכני משנה של Anthropic בלבד — אומת ב-SESSION-001 ‏([evidence](../evidence/SESSION-001/preflight-report.md)).
- **Options:** ‏A. סשן review נפרד בכלי OpenAI ‏(Codex CLI/ChatGPT) על קבצי ה-PLAN, עם דוח שנשמר ב-`docs/reviews/`. ‏B. ויתור זמני על cross-provider ל-PLAN-000 בלבד, עם review פנימי על מודל שונה (בוצע). ‏C. חיבור OpenAI כ-MCP/CLI לסביבה.
- **Recommendation:** A עבור PLAN-000 לפני אישורו הסופי אם משה רוצה לעמוד במדיניות במלואה; אחרת B מתועד כחריגה חד-פעמית. ‏C ייבחן כשיפור תשתית.
- **Impact:** עמידה במדיניות; איכות ביקורת.
- **Owner (הכנה):** Orchestrator. **הכרעה:** משה.

## D-011 — קרדינליות style references ב-style_spec

- **הקשר:** ‏doc 01 מציע "מספר תמונות סגנון לחדרים מסוגים שונים"; שאלת ה-cardinality נותרה פתוחה (contract-researcher OQ-6). ‏schema v1 של style_spec ‏(PLAN-000) קיבע במשתמע: **סגנון גלובלי אחד, ללא provenance של תמונת המקור ב-payload** ‏(contracts-reviewer MINOR-10).
- **Options:** ‏A. להשאיר גלובלי ל-POC; הרחבה ל-per-room כ-MINOR אדיטיבי ‏(שדה `room_overrides`) כשיהיה צורך. ‏B. להרחיב כבר עכשיו.
- **Recommendation:** A — אין consumer ל-per-room עדיין.
- **Impact:** ‏schema evolution של style_spec; ‏UX של קלט.
- **Owner (הכנה):** ‏Vision/Style Analyst. **הכרעה:** משה בשלב 6.

## D-010 — אימות רישוי PanoWorld ‏(Apache-2.0 מול MIT)

- **הקשר:** מסמך 05 מדווח אי-התאמה בין רישיון ה-GitHub ‏(Apache-2.0) לכרטיס המודל ב-HF ‏(MIT), ונדרשת בדיקה לפני שימוש מסחרי. גם ל-Qwen-Image-Edit ול-control models רישיונות נפרדים.
- **Options:** ‏A. license matrix מלא כ-task בשלב 12. ‏B. בדיקה מוקדמת כבר ב-PLAN-001 אם יש כוונה מסחרית קרובה.
- **Recommendation:** A אם השימוש הקרוב מחקרי/פנימי; משה יצהיר על ייעוד התוצרים.
- **Impact:** חוקיות שימוש והפצה.
- **Owner (הכנה):** ‏Security/License Reviewer. **הכרעה:** משה.
