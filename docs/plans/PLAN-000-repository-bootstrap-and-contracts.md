# PLAN-000 — Repository Bootstrap and Contracts

- Plan ID: `PLAN-000-repository-bootstrap-and-contracts`
- Status: **`DONE`** — אושר ע"י משה ‏(2026-08-05), בוצע במלואו, מוזג ל-main המקומי ‏(merge ‏`4ff4a41`) ונסגר ‏(2026-08-06). ‏Acceptance: ‏[evidence/PLAN-000/acceptance.md](../../evidence/PLAN-000/acceptance.md); ‏Handoff: ‏[HANDOFF-PLAN-000-to-PLAN-001-001](../handoffs/HANDOFF-PLAN-000-to-PLAN-001-001.md). חריגה מתועדת: ראיית ה-TDD האדום לא נשתמרה ‏(acceptance §TDD).
- Session created: SESSION-001, ‏2026-08-05
- Author (Orchestrator): Anthropic — requested `Fable 5 EXTRA`, actual `claude-opus-5[1m]` ‏(Opus 5, ‏fallback מתועד — ראו [preflight](../../evidence/SESSION-001/preflight-report.md))
- Policy: ‏[MODEL-ROUTING-v1](../06-מדיניות-ניתוב-מודלים-ומאמץ.md)
- Inputs: דוחות שלב B — ‏[contract-researcher](../../evidence/SESSION-001/agent-reports/contract-researcher.md), ‏[panoworld-compat](../../evidence/SESSION-001/agent-reports/panoworld-compat.md), ‏[test-architect](../../evidence/SESSION-001/agent-reports/test-architect.md)
- Independent review: ‏[plan-reviewer](../../evidence/SESSION-001/agent-reports/plan-reviewer.md) ‏(Fable 5) — ‏verdict ‏NEEDS_REWORK; **כל הממצאים יושמו** (ראו §15 Review record). ‏cross-provider review מול OpenAI — פתוח ‏(D-009)
- מזהה קנוני קצר: **`PLAN-000`** — זו הצורה המחייבת ב-branch ‏(`plan/PLAN-000`), ‏commits, ‏evidence ‏(`evidence/PLAN-000/`) ודוחות

---

## 1. Goal

משפט אחד מדיד: לאתחל repository מנוהל Git שבו **חוזי ה-pipeline המגורסנים** (schemas + envelope + state machine) ו-**PanoWorld package validator** עוברים ירוק על fixture אמיתי מ-scene0000 ועל fixture סינתטי, ונכשלים נכון על 15 מקרי failure-injection — לפני שנכתבת שורת קוד אחת של parser/Blender.

## 2. Current verified state

| עובדה | Evidence |
|---|---|
| הפרויקט הוא מסמכי תכנון בלבד; אין Git, אין קוד, אין מודלים | [preflight-report.md](../../evidence/SESSION-001/preflight-report.md) §A1–A3, §A6 |
| המכונה: Win10, ‏P2000 5GB cc6.1 (לא מריץ PanoWorld), ‏Python מערכתי 3.14.4, ‏Blender לא מותקן, ‏Docker פעיל, ‏git 2.55, ‏**uv 0.11.26 זמין** | preflight §A5 |
| פורמט הקלט של PanoWorld אומת מול קוד המקור: ‏4 קבצי חובה פר-viewpoint; ‏extrinsics = ‏**c2w 4x4 row-major, ‏OpenCV axes ‏(X-right/Y-down/Z-forward), מטרים**; דמו ב-Z-up, גובה מצלמה 1.35 בדיוק; ‏**depth_m = pixel / scale** ‏(חלוקה); ‏2:1 hard-enforced; ‏full pipeline ב-2048x1024; ‏**סדר מפתחות ב-map JSON קובע את צומת ההתחלה** | [panoworld-compat.md](../../evidence/SESSION-001/agent-reports/panoworld-compat.md) §2–§5 |
| שם קובץ ה-map אינו קבוע (‏scene0001 שובר את הקונבנציה); רק scene0000 ניתן להרצה out-of-the-box | panoworld-compat §1, Discrepancies 1–2 |
| ‏upstream ללא tags/releases; ‏`pushed_at 2026-08-04`; ‏repo ~0.5GB (בעיקר demo data); ‏weights ‏68.89GB ‏(HF בלבד, לא נדרשים ל-validator) | panoworld-compat §7–§9 |
| רישוי: ‏GitHub ‏Apache-2.0, ‏HF model card ‏MIT, ‏HF dataset ‏`other` — אי-התאמה מאושררת | panoworld-compat §8 |
| ‏20 ממצאי חוזים/מערכת, כולל 3 קריטיים (state machine ללא fail edges; ‏Blender sandbox; ‏H200 shutdown/secrets) | [contract-researcher.md](../../evidence/SESSION-001/agent-reports/contract-researcher.md) |

## 3. Assumptions

| # | הנחה | Owner | תנאי אימות |
|---|---|---|---|
| A1 | ‏uv יכול לספק Python 3.11 מבודד על המכונה | Implementer | ‏T2: ‏`uv python install 3.11` + ‏`uv run python -V` |
| A2 | ‏place_depth.png הוא 16-bit חד-ערוצי (INFERENCE אריתמטי) | Implementer | ‏T6: קריאת header ב-PIL על ה-fixture שיובא; עדכון schema אם שונה |
| A3 | ‏Z-up world נדרש בפועל ע"י ה-control models (קוד agnostic, דאטה Z-up) | 3D Architect ‏(Opus 5) | ‏smoke על H200 בשלב 9; עד אז validator מזהיר (warning) ולא נכשל |
| A4 | ‏vendoring של קובצי דוגמה מ-scene0000 לריפו מותר תחת Apache-2.0 | משה (D-010) | אישור מפורש לפני commit של Layer B; ‏NOTICE + ‏SHA מוצמד |
| A5 | ‏main של PanoWorld יציב מספיק לעבודה מול commit מוצמד | Orchestrator | ‏SHA נרשם ב-fixture metadata; בדיקת drift בכל fetch עתידי |
| A6 | הנתיב העברי של הריפו לא ישבור את כלי שלב-0 ‏(git/uv/pytest/PIL) | Implementer | ‏T2/T8 רצים מתוך הנתיב הנוכחי; כשל → מעבר מבוקר ל-junction ‏ASCII ‏(D-001C) |

## 4. Scope / Non-goals

### In scope (PLAN-000 בלבד)
1. אתחול Git + היגיינת repo ‏(.gitignore, ‏.gitattributes, מבנה מינימלי).
2. סביבת Python 3.11 מבודדת דרך uv עם 5 תלויות בלבד: ‏pytest, ‏pytest-cov, ‏jsonschema, ‏Pillow, ‏numpy.
3. חוזים: ‏envelope אחיד, ‏12 schemas ‏(ראו §6), טבלת state-machine קנונית עם fail edges.
4. ‏fixtures: מחולל tiny-scene סינתטי + תת-סט golden מ-scene0000 ‏(fetch מוצמד SHA, ללא weights).
5. ‏PanoWorld package validator ‏(CLI + library) עם קודי שגיאה מכונה-קריאים.
6. ‏15 בדיקות failure-injection + ‏golden tests + ‏contract round-trip tests.
7. ‏evidence harness ‏(junit.xml, ‏command.log, ‏summary.md).

### Non-goals (מפורש)
- אין floorplan parser, אין Blender/BlenderProc (גם לא התקנה), אין camera planner, אין rendering, אין style/panorama, אין dashboard, אין workflow engine, אין DB/queue/MinIO, אין שכירת H200, אין הורדת weights/checkpoints/datasets ‏(תת-סט demo images בלבד, ראו T6).
- אין מימוש mock H200 runner — רק **חוזה** ה-interface שלו ‏(schema). המימוש ב-PLAN עתידי.
- אין שינוי במסמכי התכנון 01–06 (תיקוני המדריך שנמצאו — ב-PLAN-001 או בעדכון מתועד נפרד).

## 5. Architecture candidates והכרעות מוצעות (Phase C — ‏15 ההחלטות)

| # | החלטה | הצעה | הצדקה / trade-off |
|---|---|---|---|
| C1 | Git — מתי | **מיד עם אישור התוכנית** ‏(T1), בשורש הנוכחי | ‏source of truth לפי doc 04; דחייה משאירה תכנון בלי versioning. סיכון נתיב עברי ממותן: כל הנתיבים הפנימיים ASCII; ‏fallback מוכן ל-junction ‏(D-001) |
| C2 | מבנה תיקיות | המבנה המצומצם שב-§6 — תת-סט של doc 03, בלי `apps/` ובלי מודולים ריקים | איסור boilerplate; תיקייה נוצרת רק כשיש בה קובץ אמיתי |
| C3 | Backend + ‏Python | ‏Python **3.11** דרך uv, ‏`requires-python == 3.11.*` | ‏3.14 המערכתי שובר תלויות; ‏3.11 עדיף על 3.10 מקומית (הסביבה שלנו נפרדת מסביבת ה-H200 שתרוץ 3.10 לפי דרישות PanoWorld — אנחנו מייצרים קבצים, לא מייבאים את הקוד שלהם). אומת ש-uv קיים ‏(preflight A5) |
| C4 | Workflow engine | **דחייה** ‏(D-002 option C): ‏POC בלי engine — state table + ‏CLI דטרמיניסטי; ‏spike ‏Prefect/Temporal לפני MVP | ‏doc 03 דורש spike, לא בחירה שיווקית; אין מה לתזמר עד שיש ≥2 שלבים ממומשים |
| C5 | Storage/state | **קבצים בלבד** ‏(D-003 option A): ‏PROJECT-STATE.yaml + ‏JSON artifacts | תואם doc 04; אפס תשתית; ‏migration ל-SQLite כשיהיו queries אמיתיים |
| C6 | Artifact storage + ‏immutable runs | ‏`projects/<project-id>/` ו-`runs/<run-id>/` **מחוץ ל-git** ‏(תחת `D:\PanoWorld-Automation-Data\` — ‏ASCII, דיסק D), עם `SHA256SUMS` + ‏`env.json` בכל run; בריפו רק pointers/evidence קלים | ממצאי contract 10–11, 14–15, 19; דיסק C כמעט מלא; ‏binaries כבדים לא נכנסים ל-git |
| C7 | Schema versioning | ‏envelope עם `schema_id` + ‏`schema_version` ‏(semver); קבצים ב-`schemas/<name>/v<major>/`; ‏MINOR/PATCH אדיטיביים בלבד; שבירה = ‏MAJOR + ‏ADR; ‏`contracts_bundle_version` ב-manifests ‏(D-008) | המלצת contract-researcher #3; ‏diffable, ללא תשתית |
| C8 | Test framework | ‏pytest + ‏jsonschema ‏(Draft 2020-12) בלבד; לא pydantic/fastjsonschema בשלב זה | טבלת ה-trade-off של test-architect §1; ‏schemas ידניים = ‏source of truth ניטרלי-שפה |
| C9 | סצנות דוגמה בלי הורדת מודלים | ‏Layer A סינתטי (קוד, לא בינארים) + ‏Layer B תת-סט scene0000 ‏(~6–40MB, ‏SHA מוצמד) דרך GitHub raw — **לא** clone ולא HF | ‏test-architect §2 + ‏panoworld-compat §7: ‏validation לא דורש weights |
| C10 | Mock H200 interface | ב-PLAN-000 רק **חוזה**: ‏`remote_job.json` ‏schema ‏(create/status/cancel/download, ‏heartbeat, ‏cost, ‏TTL) | מימוש mock דורש החלטות שלב 9; החוזה מקדים consumer לפי doc 03 |
| C11 | Security boundaries | ראו §10: עקרונות Blender-sandbox ו-secrets נכנסים **לחוזים עצמם** כבר עכשיו | ממצאים קריטיים 2–3 של contract-researcher |
| C12 | License review | ‏task מתועד ‏(T11): ‏NOTICE ל-fixture + רישום אי-ההתאמה Apache/MIT/other ב-license-notes; ‏matrix מלא נשאר לשלב 12 ‏(D-010) | ‏panoworld-compat §8 |
| C13 | Model staffing | טבלה ב-§8 לפי MODEL-ROUTING-v1, כולל מגבלת הממשק ו-fallbacks | חובה לפי doc 06 |
| C14 | Worktree/branch strategy | ‏branch יחיד לכל PLAN בצורה הקנונית: ‏`plan/PLAN-000`; ‏worktrees רק כשיש שני PLANs מקבילים; רק Orchestrator ממזג ל-main | ‏doc 03 "branch/worktree אחד לכל PLAN, לא לכל סוכן"; מזהה אחיד לפי doc 04 |
| C15 | Rollback/cleanup | ראו §12 | — |

### הגדרת POC מוצלח (נדרש ע"י פרומפט הסשן)
‏POC-1 ייחשב מוצלח כאשר, על **תוכנית רצפה נקייה אחת** שמשה יבחר: קיים package בפורמט PanoWorld שנוצר על-ידי ה-pipeline שלנו (גם אם ה-parse ידני), ה-validator עובר עליו ירוק באותם checks בדיוק שעוברים על scene0000, המבנה שלו diff-זהה מבנית ל-scene0000 ‏(אותם קבצים, אותם פורמטים, ‏extrinsics תקינים, ‏depth בסקאלה נכונה), והגאומטריה אושרה על-ידי משה ב-gate G2. ‏POC-1 **אינו** דורש H200 ואינו דורש איכות ויזואלית — רק תאימות מבנית מוכחת. ‏(מימוש POC-1 = ‏PLAN-001+, לא תוכנית זו.)

## 6. Exact files planned

ייווצרו **רק** הקבצים הבאים (אין skeleton ריק):

```text
PanoWorld-Automation/
├── .gitignore                       # runs data dir, .venv, __pycache__, cad_mcp.log + לוגי MCP סביבתיים, .env*, *.pyc
├── .gitattributes                   # *.json/.txt/.md/.yaml → eol=lf; *.png → binary  (לפני כל commit של fixture!)
├── pyproject.toml                   # uv project, requires-python==3.11.*, deps: pytest, pytest-cov, jsonschema, Pillow, numpy
├── uv.lock                          # נוצר ב-T2
├── PROJECT-STATE.yaml               # (קיים — יעודכן)
├── schemas/
│   ├── README.md                    # מוסכמות versioning (T3)
│   ├── envelope/v1/envelope-1.0.0.schema.json
│   ├── project_manifest/v1/project_manifest-1.0.0.schema.json
│   ├── input_quality_report/v1/...        # ה-artifact ה"עשירי" (ממצא 4)
│   ├── floorplan_parse/v1/...
│   ├── scene_geometry/v1/...
│   ├── assumptions/v1/...                 # append-only per-stage (ממצא 8)
│   ├── camera_plan/v1/...                 # כולל resolution + max_views budget (ממצא 9)
│   ├── style_spec/v1/...
│   ├── panoworld_manifest/v1/...          # המקור שממנו נגזרים map+viewpoints (ממצא 13)
│   ├── run_manifest/v1/...
│   ├── qa_report/v1/...
│   ├── approval_record/v1/...             # human gates (ממצא 5)
│   ├── retry_request/v1/...               # (ממצא 12)
│   └── remote_job/v1/...                  # חוזה ה-H200 runner (C10) — נוצר ב-T5 יחד עם השאר
├── contracts/
│   ├── README.md                    # עקרונות אבטחה מחייבים: Blender templates-only (אין codegen פר-ריצה), secrets מחוץ ל-LLM context, parsing דטרמיניסטי של פלטי שרת (T4)
│   ├── state_machine.yaml           # טבלת מעברים קנונית: from/to/gate/artifacts/validator/fail_target
│   └── error_codes.md               # אוצר קודי השגיאה + חומרה (error/warn) לכל קוד (נעול ל-dashboard עתידי)
├── src/pwa/                         # package קצר, ASCII
│   ├── __init__.py
│   └── validator/
│       ├── __init__.py
│       ├── package_validator.py     # scene/viewpoint/config checks לפי panoworld-compat §Implications
│       └── cli.py                   # `uv run pwa-validate <scene-dir>` — תומך scene-only mode (ללא config)
├── tools/
│   ├── make_tiny_scene.py           # Layer A generator (Pillow)
│   ├── fetch_golden_fixture.py      # Layer B fetch, SHA-pinned, raw.githubusercontent בלבד
│   └── run_checks.py                # ה-evidence harness של T10
├── tests/
│   ├── conftest.py
│   ├── unit/test_schemas_roundtrip.py
│   ├── unit/test_extrinsics_checks.py
│   ├── integration/test_validator_failures.py   # 15 המקרים, parametrized
│   ├── golden/test_validator_golden.py          # Layer A + Layer B
│   ├── golden/NOTICE                            # attribution (T11)
│   ├── golden/LICENSE-panoworld-upstream        # עותק Apache-2.0 של upstream (T11; חובת הרישיון בהפצה חוזרת)
│   └── golden/panoworld_demo_subset/            # נוצר ע"י fetch: הסגירה המלאה של map_panoworld0.json (ראו T6) + fixture-metadata.json
└── docs/plans/PLAN-000-...md        # (מסמך זה)
```

בנוסף, מחוץ לעץ ה-git: ‏`evidence/PLAN-000/{test-results/, diffs/, acceptance.md}` בתוך הריפו (evidence קל נכנס ל-git), ו-`D:\PanoWorld-Automation-Data\` לתוצרים כבדים ‏(C6).

הערות: ‏T5 מייצר **13 artifact schemas** = ‏9 המקוריים + ‏input_quality_report + ‏approval_record + ‏retry_request + ‏**remote_job**; ‏envelope מיוצר ב-T3. ‏`source_panorama_candidates` ו-`render_validation_report` (המלצת contract #4) נדחים ל-PLANs של שלבים 5/7 — אין להם consumer עדיין.

## 7. Tasks

כל task קטן, בעל owner, עם בדיקה. סדר ביצוע מחייב, עם חריג מכוון: ‏**T7–T9 מתבצעים בשזירת TDD** — קודם נכתבים `error_codes.md` והבדיקות הנכשלות ‏(red) כנגד הקודים, ואחר כך ממומש כל check עד ירוק ‏(green). אין מימוש check לפני שקיימת בדיקה שנכשלת עליו. ‏(דרישת "יש לתכנן TDD" מפרומפט הסשן; ממצא M-3 של ה-reviewer.)

| ID | משימה | Owner (role) | Output | בדיקה/ראיה |
|---|---|---|---|---|
| T1 | ‏git init, ‏.gitignore, ‏.gitattributes, ‏commit ראשון של המסמכים הקיימים | Implementer | ‏repo על branch ‏`main` + ‏`plan/PLAN-000` | ‏`git log`; ‏`git check-attr`; אין קבצי זבל ב-status |
| T2 | ‏uv: ‏Python 3.11 + ‏pyproject + ‏uv.lock. דורש רשת; ‏CPython יורד ל-`%LOCALAPPDATA%\uv` ‏(כונן C, ‏~50MB — קביל) | Implementer | ‏`.venv` פעיל + ‏uv.lock | ‏`uv run python -V` == ‏3.11.x ‏(A1) |
| T3 | ‏envelope schema + מוסכמות versioning | System Architect | ‏envelope-1.0.0 + ‏schemas/README.md | ‏round-trip test על דוגמה |
| T4 | ‏state_machine.yaml — טבלת מעברים מלאה: ‏fail edges, ‏BLOCKED מכל state, הפרדת RUN_* מסטטוסי PLAN, פיצול G5, מיפוי G0–G9 — **וכן** ‏contracts/README.md עם עקרונות האבטחה המחייבים ‏(Blender templates-only, ‏secrets מחוץ ל-LLM, ‏parsing דטרמיניסטי של פלטי שרת) | System Architect | ‏contracts/state_machine.yaml + ‏contracts/README.md | בדיקת מבנה **בקוד** ‏(test ייעודי, לא meta-schema): כל state נכנס+יוצא, כל gate ממופה; ‏review של Fable |
| T5 | ‏**13 artifact schemas** ‏(דראפט 1.0.0), **כולל `remote_job`** עם שדות החובה ‏ttl_minutes/max_cost_usd/heartbeat/terminate_verified | System Architect + Implementer | ‏schemas/... | דוגמה valid + דוגמה invalid לכל schema ‏(AC4) |
| T6 | ‏fetch_golden_fixture.py + הרצתו: **הסגירה המלאה של `map_panoworld0.json`** — ‏viewpoints ‏**0000+0001+0008+0011** ‏(4 הקבצים בלבד לכל viewpoint, בלי style panos — ‏~8.5MB) + ‏map_panoworld0.json + ‏fixture-metadata.json. ‏**ה-SHA נקבע ברגע ההרצה** מ-HEAD של main ונרשם — לא נלקח מדוחות שלב B. אימות A2 ‏(PIL header). ‏**fetch בלבד — ללא commit** ‏(ה-commit ב-T11 עם ה-NOTICE, תנאי A4) | Implementer | ‏tests/golden/panoworld_demo_subset/ ‏(סגור-הפניות) | ‏hash הקבצים; ‏header dump ב-evidence; אימות שהסגירה מלאה מול המפה |
| T7 | ‏make_tiny_scene.py ‏(Layer A), כולל style pano סינתטי ל-start node ‏(מכסה את מסלול ה-config שלא קיים ב-Layer B) | Implementer | פונקציית factory ל-tmp_path | ‏validator עובר עליו ירוק כולל config mode |
| T8 | ‏package_validator + ‏cli + ‏error_codes.md — כל ה-checks מ-panoworld-compat §Implications ‏(orthonormality, ‏2:1 exact, ‏depth-scale sanity, ‏map insertion-order). **הכרעות סמנטיקה מחייבות:** ‏(א) שני מצבים — ‏scene-only ‏(ללא config; בדיקת start-image מדולגת) ו-with-config; ‏(ב) ‏`VIEWPOINT_NOT_IN_MAP` = ‏**WARN** כברירת מחדל ‏(scene0000 האמיתי מכיל 0019/0021 לא ממופים); ‏(ג) "conflicting map entries" מוגדר **תוך-מפה בלבד** ‏(מפתח כפול באותה מפה = error); אותו מפתח במפות שונות = לגיטימי ‏(כמו upstream); ‏(ד) ‏`viewpoint_max_view` ‏(=8 מה-config) נבדק כ-**error**; טבלת ה-VRAM מהמדריך = ‏**WARN** בלבד ‏(לא אומתה מול מקור ראשוני); ‏(ה) דוח ה-validator מנרמל נתיבים ל-יחסיים-ל-scene לפני snapshot | Implementer (לוגיקה) + 3D Architect ‏(Opus — checks מרחביים) | ‏src/pwa/validator/ + ‏error_codes.md עם חומרה לכל קוד | ‏T9 ‏(TDD: הבדיקות קודמות למימוש) |
| T9 | ‏15 failure-injection tests + ‏golden tests ‏(A+B) + ‏roundtrip tests. מקרה 12 מוגדר-מחדש ל-Windows/NTFS: שמות שמורים ‏(CON/NUL), נקודה/רווח סופיים — לא רצפי בתים לא-חוקיים ‏(בלתי אפשרי ב-NTFS) | Tester | ‏tests/ | ‏`uv run pytest` ירוק; ‏junit.xml |
| T10 | ‏tools/run_checks.py — ‏evidence harness שכותב ‏junit.xml, ‏command.log, ‏summary.md ל-`evidence/PLAN-000/test-results/` ‏(מרוקן/מתייארך לפני כל ריצה) | Tester | ‏tools/run_checks.py | קבצי evidence קיימים ונפתחים |
| T11 | ‏NOTICE + ‏**עותק LICENSE של upstream** ‏(חובת Apache-2.0 בהפצה חוזרת) + רישום אי-ההתאמה MIT/other + ‏**commit ה-fixture** ‏(רק אחרי אישור A4 שנכלל באישור התוכנית) | Implementer | ‏tests/golden/NOTICE + ‏LICENSE-panoworld-upstream + ‏commit | ‏review; ‏hash לפני/אחרי commit ‏(AC7) |
| T12 | עדכון ‏PROJECT-STATE.yaml, ‏PROGRESS.md, ‏MASTER-INDEX; ‏HANDOFF לפי התבנית ל-consumer הבא ‏(PLAN-001) | Orchestrator | docs מעודכנים | ‏link check; ‏review |

## 8. Model staffing (MODEL-ROUTING-v1)

מגבלת ממשק ידועה: סוכני משנה ב-Claude Code הם Anthropic בלבד. לכן לכל תפקיד OpenAI רשום ה-fallback המתועד מטבלת doc 06, וה-cross-provider review נרשם כ-D-009 (לביצוע בכלי OpenAI חיצוני אם משה דורש עמידה מלאה במדיניות).

| תפקיד | Requested (policy) | Effort | Fallback בפועל בממשק | Reviewer |
|---|---|---|---|---|
| Orchestrator | Fable 5 | EXTRA | ‏Opus 5 ‏(fallback שני מתועד) | ‏GPT-5.6 ‏(D-009) |
| System Architect ‏(T3–T5) | OpenAI GPT-5.6 | EXTRA | ‏Fable 5 | ‏Fable 5 ↔ מודל שונה מהמחבר |
| Implementer ‏(T1–T2, ‏T6–T8, ‏T11) | OpenAI Codex approved | HIGH | ‏Sonnet 5 | ‏Sonnet 5 / מודל שונה מהמחבר |
| 3D Architect ‏(checks מרחביים ב-T8) | **Opus 5** | EXTRA | — ‏(אין fallback; ‏3D לא עובר ל-Fable) | ‏GPT-5.6 ‏(D-009) או Sonnet |
| Tester ‏(T9–T10) | OpenAI GPT-5.6/Codex | HIGH | ‏Sonnet 5 | מודל שונה מהמחבר |
| Independent Plan Reviewer | ספק שונה מהמחבר | EXTRA | ‏Fable 5 ‏(ביקורת פנימית) + ‏D-009 | משה |

כל סבב ביצוע ירשום: ‏requested model, ‏actual model ID, ‏effort מנורמל + ערך ספק, ‏fallback yes/no + סיבה — בפורמט החובה של doc 04.

## 9. Acceptance criteria

- [ ] ‏AC1: ‏`uv run pytest` ירוק מקומית; ‏junit.xml נכתב ל-evidence. ‏(T2, ‏T9, ‏T10)
- [ ] ‏AC2: ה-validator עובר במצב scene-only על Layer B ‏(הסגירה המלאה של map0 מ-scene0000) ובמצב with-config על Layer A, עם דוח מובנה זהה-snapshot ‏(נתיבים מנורמלים יחסית ל-scene). ‏(T8–T9)
- [ ] ‏AC3: כל 15 מקרי ה-failure מחזירים את קוד השגיאה/אזהרה הספציפי שלהם כמוגדר ב-error_codes.md — לא crash ולא הצלחה שקטה. ‏(T9)
- [ ] ‏AC4: כל **13** ה-schemas ‏(כולל remote_job) + ‏envelope עם דוגמה valid+invalid עוברות/נכשלות בהתאמה; ‏envelope round-trip שומר שוויון סמנטי. ‏(T3, ‏T5)
- [ ] ‏AC5: ‏state_machine.yaml סוגר את ממצאים 1, ‏6, ‏7, ‏18, ‏20 של contract-researcher ‏(fail edges, פיצול G5, ‏RUN_* namespace, מיפוי G מלא). ‏(T4)
- [ ] ‏AC6: אין קובץ בינארי בריפו מחוץ ל-`tests/golden/panoworld_demo_subset/`; ‏fixture עם SHA מוצמד + ‏NOTICE. ‏(T6, ‏T11)
- [ ] ‏AC7: ‏`git status` נקי **בסינון ignored** ‏(שרת ה-CAD MCP הסביבתי כותב לוגים ל-cwd תוך כדי עבודה — מכוסים ב-.gitignore); אין קבצי זבל; ‏CRLF לא שינה אף fixture ‏(hash לפני/אחרי commit). ‏(T1, ‏T11)
- [ ] ‏AC8: ‏PROJECT-STATE, ‏PROGRESS, ‏MASTER-INDEX מעודכנים באותו merge. ‏(T12)

## 10. Security / License risks

| סיכון | טיפול בתוכנית זו |
|---|---|
| ‏Blender/LLM codegen = ‏RCE ‏(ממצא קריטי 2) | עיקרון ננעל בחוזה: ‏`scene_geometry` schema הוא ה-interface היחיד לגאומטריה; סקריפטי Blender עתידיים הם תבניות מאושרות-מראש הצורכות JSON בלבד — נרשם ב-contracts/README וב-ARCHITECTURE ‏(TB-2). אין Blender ב-PLAN-000 בכלל |
| ‏H200 secrets + ‏orphan server ‏(ממצא קריטי 3) | ‏`remote_job` schema כולל שדות חובה: ‏`ttl_minutes`, ‏`max_cost_usd`, ‏`heartbeat`, ‏`terminate_verified`; העיקרון "מפתח ענן רק בשירות דטרמיניסטי, לעולם לא ב-context של LLM" נרשם בחוזה. אין ענן ב-PLAN-000 |
| ‏outputs חיצוניים כ-data לא מהימן ‏(ממצא 16) | ‏error envelope מחייב parsing דטרמיניסטי; נרשם ב-contracts/README |
| ‏fetch מ-GitHub — ‏supply chain | ‏raw.githubusercontent בלבד, ‏SHA commit מוצמד, ‏hash לכל קובץ ב-fixture-metadata.json; אין הרצת קוד שהובא |
| רישוי fixture ‏(A4/D-010) | ‏vendoring רק אחרי אישור משה; ‏NOTICE + עותק LICENSE של upstream ‏(חובת Apache-2.0); אי-התאמת MIT/other מתועדת |
| רכיבי GPL עתידיים ‏(FloorplanToBlender3d, ‏BlenderProc) | **אין רכיב GPL ב-PLAN-000.** בידודם כ-tools חיצוניים והשלכות ההפצה — ‏D-004 ‏(parser) ו-license matrix של שלב 12 ‏(D-010) |
| נתיב עברי | קוד ונתיבים פנימיים ASCII; ‏pathlib בלבד; ‏subprocess בצורת list; ‏A6 עם fallback מוכן |
| ‏secrets | אין secrets בשלב זה; ‏.gitignore כולל ‏`.env*` מהיום הראשון |

## 11. Blockers / Open decisions

- אין blocker פעיל לביצוע התוכנית עצמה.
- החלטות שהתוכנית **מציעה לסגור באישורה**: ‏D-001 ‏(Git עכשיו, כאן), ‏D-008 ‏(versioning), ‏A4/D-010 ‏(vendoring fixture) — אישור PLAN-000 = אישורן, והן יתועדו כ-ADR-0001..0003 בתחילת הביצוע.
- נשארות פתוחות: ‏D-002 ‏(engine), ‏D-003 ‏(storage upgrade), ‏D-004..D-007, ‏D-009 ‏(cross-provider review בפועל).
- שאלות פתוחות שלא חוסמות: רשימות ה-OPEN_QUESTIONS בשלושת דוחות הסוכנים (משולבות ב-[OPEN-DECISIONS.md](../OPEN-DECISIONS.md) לפי צורך; חלקן ייענו רק על H200).

## 12. Rollback / Cleanup

- כל השינויים ב-git על branch ‏`plan/PLAN-000`; ‏rollback = מחיקת ה-branch לפני merge, או ‏revert של ה-merge commit אחריו.
- ‏`.venv` הוא מקומי לריפו: ‏`Remove-Item .venv` מסיר אותו. ‏CPython 3.11 של uv הוא user-scoped ומשותף בין פרויקטים — ‏`uv python uninstall 3.11` יבוצע **רק** אם `uv python list` מראה שאין פרויקט אחר שתלוי בו. אין שינוי מערכתי, אין PATH, אין registry.
- ‏fixture: מחיקת `tests/golden/panoworld_demo_subset/` — ה-fetch idempotent וניתן לשחזור מה-SHA.
- ‏`D:\PanoWorld-Automation-Data\` ‏(אם נוצר): מחיקה בטוחה — מכיל רק תוצרים משוחזרים.
- אין פעולה הרסנית על קבצים קיימים בשום שלב.

## 13. Tests / Expected evidence

- ‏evidence path: ‏`evidence/PLAN-000/test-results/{junit.xml, command.log, summary.md, coverage.xml}` + ‏`evidence/PLAN-000/diffs/` ‏(snapshot דוח ה-validator) + ‏`evidence/PLAN-000/acceptance.md`.
- ‏evidence מתחדש בכל טענת completion; אין שימוש חוזר בריצה ישנה ‏(doc 04 — "tests טריים").
- פירוט מלא של עיצוב הבדיקות: ‏[test-architect report](../../evidence/SESSION-001/agent-reports/test-architect.md) §3–§5.

## 14. Definition of Done

‏PLAN-000 יהיה DONE רק כאשר: כל AC1–AC8 עברו עם evidence; ‏review עצמאי עבר (ומשה הכריע על D-009); ‏docs/state עודכנו באותו merge; ‏HANDOFF ל-PLAN-001 נכתב; אין blocker קריטי פתוח; ומשה אישר. עד אז — ‏`REVIEW`.

### מה PLAN-000 מאפשר אחריו
‏PLAN-001 (מוצע): ‏Intake + ‏project_manifest בפועל, או ‏packager שממלא את החוזים — לפי סדר המימוש של doc 03 ‏(Contracts → Intake → Packager מוקדם). ההכרעה עם משה בסיום ביצוע PLAN-000.

---

## 15. Review record

| שלב | מבצע | תוצאה |
|---|---|---|
| ביקורת בלתי תלויה (פנימית) | ‏plan-reviewer — ‏Anthropic Fable 5 ‏(מודל שונה מהמחבר Opus 5; ספק זהה — מגבלת ממשק, ‏D-009) | ‏**NEEDS_REWORK**: ‏1 CRITICAL, ‏4 MAJOR, ‏6 MINOR, ‏6 missed risks — ‏[הדוח המלא](../../evidence/SESSION-001/agent-reports/plan-reviewer.md) |
| ‏rework | Orchestrator, באותו סשן | **כל הממצאים יושמו**: ‏C-1 ‏(fixture = סגירת map0 המלאה ‏0000+0001+0008+0011 + ‏scene-only mode + ‏style סינתטי ב-Layer A); ‏M-1 ‏(remote_job ב-T5 + ‏AC4); ‏M-2 ‏(§6 הושלם: ‏uv.lock, ‏READMEs, ‏NOTICE+LICENSE, ‏metadata, ‏run_checks.py; ‏contracts/README.md ל-T4); ‏M-3 ‏(TDD מחייב ב-T7–T9); ‏M-4 ‏(סמנטיקת WARN/conflict הוכרעה ב-T8); ‏m-1..m-6 ‏(טווח גודל, סדר T6/T11, ‏GPL, בדיקת מבנה בקוד, מזהה קנוני PLAN-000, ‏LICENSE upstream); ‏missed risks 1–6 ‏(מקרה 12 ל-NTFS, נרמול נתיבים ב-snapshot, ‏VRAM=WARN, ‏T2 network/rollback, ‏AC7 מסונן, ‏SHA בזמן ריצה) |
| ‏cross-provider review ‏(OpenAI) | — | לא בוצע — לא זמין בממשק; משה קיבל את הביקורת הפנימית כחריגה חד-פעמית ל-PLAN-000; ‏D-009 נותר פתוח כשאלת תשתית |
| אישור משה לתוכנית | משה | **אושר** — ‏2026-08-05 ‏("מאשר") |
| ביצוע | Orchestrator ‏(`claude-opus-5[1m]`) + ‏reviewers ‏Fable/Sonnet | ‏T1–T12 הושלמו; ‏109/109 בדיקות; ממצאי שני ה-reviews יושמו; ‏merge ‏`4ff4a41` |
| סגירה | משה ‏(הנחיית closure ‏2026-08-06) | **DONE** — ‏acceptance מעודכן, כולל תיקון ראיית ה-red-phase שלא נשתמרה |
