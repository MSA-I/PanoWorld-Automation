# OPEN DECISIONS — PanoWorld Automation

- Status: פעיל. נוצר ב-SESSION-001; עודכן בסגירת PLAN-000 ‏(2026-08-06).
- כלל: החלטה כאן היא **פתוחה**. כשמשה מאשר — היא הופכת ל-ADR תחת `docs/decisions/` ומסומנת כאן כ-RESOLVED. אין לממש על בסיס המלצה בלבד.
- Owner ברירת מחדל להכרעה: משה. ‏Owner להכנת החומר: כמצוין.

---

## החלטות שנסגרו

| ID | הוכרע | ADR | הערה |
|---|---|---|---|
| ‏D-001 ‏Git bootstrap | ‏Option A — שורש נוכחי, מיידי | [ADR-0001](decisions/ADR-0001-git-repository-bootstrap.md) | מיושם ‏(main פעיל). מוקש הנתיב העברי התממש חלקית ‏(editable ‏.pth) וטופל ב-`package=false` — ה-fallback ל-junction ‏ASCII נשאר זמין |
| ‏D-008 ‏Schema versioning | ‏Option A — ‏envelope+semver+bundle | [ADR-0002](decisions/ADR-0002-schema-versioning-strategy.md) | מיושם, כולל הגדרת ‏content_hash קנונית |
| ‏D-010 ‏(חלק ה-vendoring בלבד) | ‏vendoring תת-סט ‏scene0000 מותר | [ADR-0003](decisions/ADR-0003-golden-fixture-vendoring.md) | מיושם עם NOTICE+LICENSE; **יתרת D-010 (license matrix מסחרי) נותרה פתוחה — ראו בהמשך** |

---

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

## D-009 — ביצוע cross-provider review בפועל

- **הקשר:** ‏MODEL-ROUTING-v1 דורש review של OpenAI על תוצרי Anthropic קריטיים. הממשק הנוכחי (Claude Code) מאפשר סוכני משנה של Anthropic בלבד — אומת ב-SESSION-001 ‏([evidence](../evidence/SESSION-001/preflight-report.md)).
- **עדכון 2026-08-06:** עבור PLAN-000 משה בחר בפועל ב-B — אישר את התוכנית עם הביקורת הפנימית ‏(מודלים שונים, אותו ספק) כ**חריגה חד-פעמית מתועדת**. נותר פתוח: פתרון תשתיתי קבוע ‏(A או C) ל-PLANs הבאים, בפרט לפני artifacts קריטיים של geometry/H200.
- **Options:** ‏A. סשן review נפרד בכלי OpenAI ‏(Codex CLI/ChatGPT) עם דוח שנשמר ב-`docs/reviews/`. ‏C. חיבור OpenAI כ-MCP/CLI לסביבה.
- **Impact:** עמידה במדיניות; איכות ביקורת.
- **Owner (הכנה):** Orchestrator. **הכרעה:** משה.

## D-011 — קרדינליות style references ב-style_spec

- **הקשר:** ‏doc 01 מציע "מספר תמונות סגנון לחדרים מסוגים שונים"; שאלת ה-cardinality נותרה פתוחה (contract-researcher OQ-6). ‏schema v1 של style_spec ‏(PLAN-000) קיבע במשתמע: **סגנון גלובלי אחד, ללא provenance של תמונת המקור ב-payload** ‏(contracts-reviewer MINOR-10).
- **Options:** ‏A. להשאיר גלובלי ל-POC; הרחבה ל-per-room כ-MINOR אדיטיבי ‏(שדה `room_overrides`) כשיהיה צורך. ‏B. להרחיב כבר עכשיו.
- **Recommendation:** A — אין consumer ל-per-room עדיין.
- **Impact:** ‏schema evolution של style_spec; ‏UX של קלט.
- **Owner (הכנה):** ‏Vision/Style Analyst. **הכרעה:** משה בשלב 6.

## D-010 (יתרה) — ‏license matrix מלא לפני שימוש מסחרי

- **הקשר:** חלק ה-vendoring נסגר ‏(ADR-0003). נותר: אי-ההתאמה GitHub ‏Apache-2.0 מול ‏HF model card ‏MIT ‏(אומתה שוב ע"י panoworld-compat), ‏dataset ‏`license: other`, ורישיונות Qwen/control models — נדרש matrix מלא לפני שימוש מסחרי.
- **תוספת PLAN-001:** ננעלו ב-`uv.lock` ‏`ezdxf==1.4.4` ‏(MIT) ו-`pypdfium2==5.12.1` ‏(Apache-2.0 או BSD-3-Clause; ‏PDFium ורכיבי צד שלישי כפופים לרישיונות הנלווים). בדיקת הפצה מלאה שלהם נשארת בתוך D-010 ואינה נסגרת בשלב זה.
- **Options:** ‏A. license matrix מלא כ-task בשלב 12. ‏B. בדיקה מוקדמת אם יש כוונה מסחרית קרובה.
- **Recommendation:** A אם השימוש הקרוב מחקרי/פנימי; משה יצהיר על ייעוד התוצרים.
- **Impact:** חוקיות שימוש והפצה.
- **Owner (הכנה):** ‏Security/License Reviewer. **הכרעה:** משה.
