<!-- Independent cross-provider review of the PLAN-002 second rework (NA-3, round 3).
     PROVIDER: openai | MODEL_ID_EXACT: gpt-5.6-sol | EFFORT: EXTRA / xhigh
     Route: Codex CLI 0.144.6, `codex exec --sandbox read-only --disable hooks`,
     run against this worktree with DIRECT read-only filesystem access. This is the
     material change NA-3 called for: the round-2 reviewer judged an inline package
     assembled by the orchestrator and had to return CANNOT_VERIFY for code M-8 and
     M-9 and for src/pwa/files.py. This reviewer read the repository itself, so no
     packaging gap exists and no file could be omitted.
     Model identity was verified by the orchestrator from the Codex session rollout
     (turn_context.model = "gpt-5.6-sol", effort = "xhigh") rather than taken from
     the reviewer's own claim - see the plan-002-implementer silent-substitution
     precedent recorded in PROJECT-STATE.yaml.
     Hooks were disabled for the run so no persona/skill hook could bias the review.
     LANGUAGE DEVIATION: the reviewer answered in Hebrew although the brief and every
     other evidence file in this project are English. Archived verbatim regardless -
     a reviewer's words are never rewritten by the orchestrator.
     Orchestrator verification of this review's two most consequential findings is
     recorded separately in orchestrator-verification-na3-20260810.md. -->
<!-- PROVIDER: openai | MODEL_ID_EXACT: gpt-5.6-sol
     EFFORT: xhigh | Route: Codex CLI, read-only sandbox, direct filesystem access -->
# VERDICT: `NEEDS_REWORK`

GC-6 תוקן נכון, ורוב התיקונים הנקודתיים מסבב 2 אכן קיימים. עם זאת, נשאר נתיב **CRITICAL** לכתיבה מחוץ ל־`runs_root` דרך junction ב־`.staging`, ובנוסף נמצאו כשלי lineage, snapshot, פרטיות, PDF-page ומגבלת DXF שמאפשרים פלט סופי תקין-סכמתית אך שגוי או בלתי ניתן לאימות. הסתמכתי על תוצאת 316 הבדיקות שנקבעה כעובדה על ידי ה־orchestrator ולא הרצתי את הסוויטה מחדש.

## 1. Round-2 checklist disposition

| item | status | evidence (file:line) | note |
|---|---|---|---|
| GC-1 | `CLOSED` | `src/pwa/floorplan/builder.py:44-57`, `445-463`, `481-503` | `parse_run_id` מוגבל למקטע ASCII יחיד לפני בניית נתיב ממנו. נתיבים שנדחים מוחלפים ב־placeholders קבועים. חור היעד דרך `.staging` הוא כשל נפרד, לא bypass של הדקדוק. |
| GC-2 | `CLOSED` | `src/pwa/floorplan/runs.py:11-59`, `62-110` | `runs_root` ושורש `resolve_contained_relpath` נבדקים לפני `resolve()`, וההליכה נעשית על הרכיבים הלקסיקליים המקוריים. הדבר אינו מגן על אבות שמעל שורש יעד לא-קיים; ראו C-NA3-1. |
| GC-3 | `CLOSED` | `src/pwa/floorplan/builder.py:514-533` | גם manifest וגם quality-report עוברים דרך `resolve_contained_relpath()` לפני הקריאה. |
| GC-4 | `PARTIALLY_CLOSED` | `src/pwa/floorplan/annotation_source.py:37-47`; `src/pwa/floorplan/builder.py:661-681`, `712-721`, `873-881` | hash מחושב מחדש ו־ID/hash נקשרים ל־`floorplan_parse.inputs[]`, אך הקובץ נקרא שוב לצורך parsing בעוד ה־document הישן משמש ל־lineage. החלפה בין הקריאות מאפשרת parse של B עם binding ל־A. |
| GC-5 | `PARTIALLY_CLOSED` | `src/pwa/floorplan/annotation_source.py:15-23`, `49-56`; `src/pwa/intake.py:173-180`; `docs/plans/PLAN-002-floorplan-parsing.md:200-204` | style-reference נחסם. מנגד, כל PDF-page שנוצר ב־intake מקבל `kind="other"` ולכן נחסם, בניגוד מפורש ל־§6. היעדר בדיקה קודמת אינו הופך אובדן capability לאי-רגרסיה. |
| GC-6 | `CLOSED` | `src/pwa/floorplan/normalize.py:156-183`, `287-325`; `tests/unit/test_floorplan_normalize.py:294-397` | ההיטל מחושב על וקטור היחידה של הקיר שנבחר ורק לאחר resolution. דוגמת 0.05/0.04 מחזירה 0.03 מ׳; span מאונך של 0.04 מ׳ נכשל ב־`PARSE_RESOURCE_LIMIT`; ודוגמת 0.9 מ׳ מחזירה 0.8991 מ׳ ואינה מפיקה `PARSE_OPENING_WIDTH_EXCEEDS_WALL`. |
| GC-7 | `PARTIALLY_CLOSED` | `src/pwa/floorplan/builder.py:288-331`; `src/pwa/floorplan/overlay.py:108-125`; `tests/unit/test_floorplan_builder.py:38-150` | תחת snapshot יציב, EXIF/PNG text/ICC/DPI אינם מועברים, ההטמעה דטרמיניסטית וה־hash הוא של קובץ המקור ולא של ה־re-encode. JPEG מקודד בגלוי ב־quality 95, ורק PNG נטען כ־pixel-perfect. עם זאת, הפיקסלים וה־hash נקראים מהנתיב בשתי פעולות נפרדות ולכן ניתן לקשור hash של B לפיקסלים של A. |
| A | `CLOSED` | `src/pwa/floorplan/runs.py:113-128` | ה־hash של הבתים שהועתקו מושווה ל־hash המוצהר. מיקום ההעתקה שגוי, אך זה כשל נפרד. |
| B | `PARTIALLY_CLOSED` | `src/pwa/floorplan/builder.py:519-552`, `634-681`, `585-599`, `694-706` | המקרים המדווחים של schema חסרה ו־annotation חסר נסגרים. `sha256_file()`, `source_floorplan.stat()` ו־`staging_run.mkdir()` עדיין יכולים להעלות `OSError` מחוץ ל־`parse_run()`. |
| C | `CLOSED` | `src/pwa/floorplan/builder.py:386-415`; `tests/integration/test_plan002_parse_run.py:825-874` | cardinality findings משולבים עם `raw.errors` וממוינים לפי precedence; ARC-only מדווח כ־`PARSE_UNSUPPORTED_FEATURE`. |
| D | `CLOSED` | `src/pwa/floorplan/overlay.py:175-203`, `205-265`; `tests/unit/test_floorplan_overlay.py:173-225`, `228-321` | bounds כוללים source ודטקציות, והרדיוס/גופן פרופורציונליים ל־extent. שינוי הציפייה בבדיקה היה תיקון לגיטימי: כעת היא מוכיחה שהפער נראה ואינו נחתך. |
| E | `PARTIALLY_CLOSED` | `src/pwa/floorplan/builder.py:932-955` | `open("xb")` מונע overwrite ומעקב אחרי symlink קיים ב־leaf. אבות הנתיב, לרבות `.staging` ו־`parse`, עדיין יכולים להיות junction/symlink ולהיעקב. |
| M-6 | `PARTIALLY_CLOSED` | `src/pwa/floorplan/dxf_source.py:18-23`, `98-110`; `src/pwa/floorplan/config.py:9-20` | תוצאת worker מעל 1 MiB כבר אינה נחתכת, אך תוצאה חוקית מעל 50 MiB נחתכת בשקט ואז מסווגת malformed/CLI 2. זה נשאר edge case מוגבל ברמת `INFO`, לא blocker עצמאי. |
| M-8 | `CLOSED` | `src/pwa/contracts.py:61-78`; `tests/unit/test_contract_versions.py:139-181` | שתי הבדיקות החדשות מגיעות בפועל לענפי duplicate pair ו־duplicate `$id`, ולא נעצרות ב־filename guards. |
| M-9 | `CLOSED` | `tests/integration/test_plan002_failure_matrix.py:713-785` | הבדיקה מצלמת `{relative path: sha256}` ומאמתת שוויון לאחר success, warning, failed-domain ו־operational outcomes. |
| `copy_immutable()` / `is_link_or_reparse()` | `PARTIALLY_CLOSED` | `src/pwa/files.py:11-16`, `27-41` | `lstat` ו־Windows reparse attribute נכונים; היעד נוצר בלעדית ומבוצע fsync/hash verification. אין פתיחה אטומית עם no-follow לאחר הבדיקה, ו־`destination.parent.mkdir()` עוקב אחרי reparse באבות. |

## 2. New findings

### C-NA3-1 — CRITICAL — junction ב־`.staging` מאפשר כתיבה מחוץ ל־`runs_root`

**File/function:** `src/pwa/floorplan/builder.py::parse_run`, `src/pwa/floorplan/runs.py::resolve_contained_relpath`

הקוד בודק containment לקסיקלי בלבד ואז יוצר את staging דרך אבות שלא נבדקו:

```python
final_run = runs_root / parse_run_id
staging_run = runs_root / ".staging" / parse_run_id
...
staging_run.mkdir(parents=True, exist_ok=False)
```

`src/pwa/floorplan/builder.py:481-488`, `504-513`, `706-710`.

בצד היעד, `resolve_contained_relpath()` מקבל `staging_run / "project"` כשורש. אם הוא טרם קיים, הוא אינו בודק את `.staging` שמעליו, ולאחר מכן `resolve(strict=False)` מנרמל את שניהם לאותו יעד חיצוני ולכן בדיקת `relative_to` עוברת (`src/pwa/floorplan/runs.py:71-84`, `92-109`).

**Concrete failure scenario:** צור junction בשם `runs/.staging` שמצביע ל־`D:\victim`, והשאר את `D:\victim\<parse-id>` לא קיים. עבור source תקין ו־annotation עם `content_hash` ישן, בדיקת `staging_run.exists()` מחזירה false; `mkdir()` יוצר `D:\victim\<parse-id>`, ו־`copy_source_inventory()` כותב אליו. כשל ה־annotation מתרחש רק לאחר ההעתקה ומשאיר את הקבצים החיצוניים ב־CLI 2 (`src/pwa/floorplan/builder.py:708-716`, `976-985`).

**Required fix:** ליצור ולאמת את `.staging` כ-directory בבעלות התהליך, לדחות כל reparse בכל שרשרת יעד החל מ־`runs_root`, ולהשתמש בפתיחות/handles שאינן מאפשרות החלפת ancestor או leaf בין check ל־write.

---

### M-NA3-1 — MAJOR — inventory מועתק ל־`project/project/...` בעוד ה־manifest מצהיר `project/...`

**File/function:** `src/pwa/floorplan/runs.py::copy_source_inventory`

```python
staging_project = staging_run / "project"
...
destination_item = resolve_contained_relpath(
    staging_project, item["path"], must_exist=False
)
```

`src/pwa/floorplan/runs.py:113-118`.

נתיבי intake הם כבר run-relative וכוללים את התחילית `project/inputs/...` (`src/pwa/intake.py:207-210`). ה־derived manifest משמר אותם ללא שינוי (`src/pwa/floorplan/builder.py:806-820`).

**Concrete failure scenario:** parse רגיל של PNG מסתיים `complete`. הקובץ נמצא בפועל ב־`<final>/project/project/inputs/originals/floorplan.png`, אך `project_manifest.payload.inputs[0].path` נשאר `project/inputs/originals/floorplan.png`. Validator downstream שפותח את הנתיב המוצהר מקבל `FileNotFoundError`; הריצה הסופית אינה self-contained למרות שסומנה complete.

**Required fix:** לפתור יעדי inventory ביחס ל־`staging_run`, לא ל־`staging_run/project`, ולהוסיף בדיקה הפותחת כל path מתוך ה־derived manifest ומאמתת את ה־SHA-256 לאחר finalization.

---

### M-NA3-2 — MAJOR — parsing, copying ו־lineage אינם משתמשים באותו snapshot

**File/function:** `src/pwa/floorplan/builder.py::parse_run`, `AnnotationSource.extract`, `_source_binding`

ה־annotation נקרא ב־preflight:

```python
annotation_document = json.loads(Path(annotation).read_text(...))
```

אך נקרא שוב בתוך `extract()` (`src/pwa/floorplan/annotation_source.py:37-47`), מועתק לאחר מכן, בעוד binding נבנה מה־document הראשון:

```python
raw = AnnotationSource().extract(annotation, ...)
copy_immutable(annotation, copied_annotation)
...
*([_annotation_input(annotation_document)] ...)
```

`src/pwa/floorplan/builder.py:661-681`, `712-721`, `873-881`.

גם מקור DXF מועתק ואז נקרא שוב מה־source run המקורי (`src/pwa/floorplan/builder.py:708-710`, `745-756`). ב־raster, הפיקסלים וה־hash נקראים בשתי פעולות נפרדות על אותו path (`src/pwa/floorplan/builder.py:313-331`).

**Concrete failure scenario 1:** לאחר preflight של annotation A, החלף אותו ב־annotation B תקין עם geometry ו־content hash חדשים. `extract()` מפרש את B, `copy_immutable()` מעתיק את B, אך `floorplan_parse.inputs[]` קושר את artifact/hash של A. הריצה יכולה להסתיים complete עם lineage כוזב.

**Concrete failure scenario 2:** לאחר `copy_source_inventory()` החלף את floorplan DXF A ב־B. `DxfSource.extract()` מפרש את B, בעוד ה־derived inventory מכיל את A. אין hash verification לאחר parsing.

**Required fix:** לקרוא כל input פעם אחת ל־snapshot בלתי-משתנה, לבצע validation/hash/parsing/copying מאותם בתים, ולפרש רק את עותקי staging שאומתו. עבור raster יש לחשב original hash ו־sanitized bytes מאותו buffer פתוח.

---

### M-NA3-3 — MAJOR — תמיכת PDF-page המחייבת בחוזה הוסרה

**File/function:** `src/pwa/floorplan/annotation_source.py::AnnotationSource.extract`

```python
_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan"}
...
if source_inventory[image_ref].get("kind") not in ...:
    raise ValueError(...)
```

`src/pwa/floorplan/annotation_source.py:15-23`, `49-56`.

intake מסמן את ה־PDF המקורי כ־`floorplan`, אך כל page PNG נגזר כ־`other` (`src/pwa/intake.py:173-180`, `207-210`). PLAN-002 מחייב לאפשר selected intake-generated PDF page (`docs/plans/PLAN-002-floorplan-parsing.md:200-204`).

**Concrete failure scenario:** ingest של `plan.pdf` מייצר `project/inputs/derivatives/pdf/page-0001.png`. Annotation תקין שמפנה ל־page הזה, עם hash וממדים נכונים, נכשל תמיד בבדיקת kind ומחזיר operational CLI 2 במקום parse.

**Required fix:** להגדיר contract חד-משמעי ל־PDF-page derivative—role/kind ייעודי או allowlist מאושר המבוסס על provenance מפורש—ולכסות אותו בבדיקת integration. זהו שינוי ב־§6 ולכן נדרש אישור אנושי.

---

### M-NA3-4 — MAJOR — שמות פרטיים עדיין זולגים לארטיפקטים, ונתיבים מוחלטים כבר נמצאים בראיות tracked

**File/function:** `dxf_worker._scan_layout`, `builder._source_binding`, `overlay._legend_lines`

DXF source refs כוללים את שמות ה־layout וה־layer ללא redaction:

```python
source_ref = f"dxf:{layout.name}/{layer}#{handle}"
```

`src/pwa/floorplan/dxf_worker.py:61-81`.

הם מועברים ל־overlay labels (`src/pwa/floorplan/builder.py:359-364`) ול־parse-report (`src/pwa/floorplan/builder.py:918-926`). `escape()` מונע XML injection אך אינו מסיר מידע פרטי (`src/pwa/floorplan/overlay.py:57-64`).

**Concrete failure scenario:** DXF עם layer לא ממופה בשם `Alice_SecretClient` מפיק partial run שב־`parse-report.json` וב־overlay legend מופיעים שם המשתמש ושם הלקוח במלואם.

בנוסף, דליפה קיימת כבר עכשיו: נתיב worktree מוחלט נמצא ב־`evidence/PLAN-002/reviews/gc6-gc7-report-20260810.md:3-6`, ו־`C:\Users\art1\...` נמצא ב־`evidence/PLAN-002/reviews/independent-anthropic-code-review-20260810.md:275-280`, `524-531`. הדבר סותר ישירות את §12 (`docs/plans/PLAN-002-floorplan-parsing.md:340-351`).

**Required fix:** להשתמש ב־opaque source refs שאינם מכילים layout/layer חופשיים, לבצע redaction עקבי בראיות, ולפתור אנושית את ההתנגשות בין מחיקת המידע שכבר פורסם לבין מדיניות append-only.

---

### M-NA3-5 — MAJOR — `MAX_DXF_ENTITIES` נאכף רק על modelspace

**File/function:** `src/pwa/floorplan/dxf_worker.py::extract_dxf`

```python
modelspace = document.modelspace()
if len(modelspace) > MAX_DXF_ENTITIES:
    raise ValueError("PARSE_RESOURCE_LIMIT")
```

`src/pwa/floorplan/dxf_worker.py:143-151`.

לאחר מכן כל entity בכל layout נוסף נסרק ללא cumulative limit (`src/pwa/floorplan/dxf_worker.py:169-182`).

**Concrete failure scenario:** DXF עם wall/room תקינים ב־modelspace ו־200,001 LINEs ב־paperspace עובר את בדיקת הכמות. ה־worker סורק ומייצר מאות אלפי findings; התוצאה היא `PARSE_UNSUPPORTED_FEATURE`, timeout, או truncation ל־CLI 2—לא `PARSE_RESOURCE_LIMIT` בגבול הישות המוצהר.

**Required fix:** לאכוף מונה כולל לפני ובמהלך סריקת כל ה־layouts, לעצור בדיוק בחריגה ולמפות אותה ל־`PARSE_RESOURCE_LIMIT`.

---

### M-NA3-6 — MAJOR — finality, cardinality ועקביות בין source artifacts אינן מאומתות

**File/function:** `resolve_contained_run`, `parse_run`

`resolve_contained_run()` מקבל כל directory מקונן שקיים מתחת ל־root; אין בדיקה שהוא child ישיר ואינו תחת `.staging` (`src/pwa/floorplan/runs.py:36-59`). לאחר validation נפרד של manifest ו־quality, הקוד בודק רק hash/status/blockers (`src/pwa/floorplan/builder.py:539-575`) ובוחר את floorplan הראשון:

```python
floorplan_entry = next(
    item for item in source_manifest["payload"]["inputs"]
    if item["kind"] == "floorplan"
)
```

`src/pwa/floorplan/builder.py:585-611`. סכמת manifest אינה מחייבת floorplan יחיד או paths ייחודיים (`schemas/project_manifest/v1/project_manifest-1.0.0.schema.json:26-38`).

**Concrete failure scenario 1:** עותק תקין של source run תחת `runs/.staging/RUN-src` מתקבל ומייצר parse סופי, למרות הדרישה “Parse only a finalized source run”.

**Concrete failure scenario 2:** project manifest מפרויקט A ו־quality report תקין מפרויקט B, עם hashes תקינים ו־`status=complete`, מתקבלים יחד. ה־derived manifest/parse משתמשים ב־project A, בעוד ה־derived quality משתמש ב־project B (`src/pwa/floorplan/builder.py:813-829`, `870-881`).

**Concrete failure scenario 3:** manifest תקין-סכמתית עם שני `kind=floorplan` מתקבל; הראשון נבחר בשקט במקום preflight failure.

**Required fix:** לדרוש source run סופי וישיר, התאמת directory/run_id/project_id/artifact lineage, בדיוק floorplan אחד, ו־inventory paths ייחודיים.

---

### N-NA3-1 — MINOR — `parse_run()` עדיין יכול להעלות חריגות preflight/filesystem

`sha256_file(input_path)` ו־`source_floorplan.stat()` אינם עטופים ב־`OSError`, ו־`staging_run.mkdir()` נמצא מחוץ ל־try הראשי (`src/pwa/floorplan/builder.py:585-599`, `683-706`).

**Concrete failure scenario:** inventory file קיים אך ACL מונע קריאה. containment מצליח, ואז `sha256_file()` מעלה `PermissionError` במקום להחזיר `ParseRunResult(cli_exit=2)`. ה־CLI החיצוני ממיר זאת ל־2 באמצעות guard כללי (`src/pwa/floorplan/cli.py:18-31`), אך חוזה ה־API של `parse_run()` נשבר.

**Required fix:** לעטוף את כל פעולות preflight/staging ולשמר diagnostic עקבי ללא exception החוצה.

---

### I-NA3-1 — INFO — תוצאת worker חוקית מעל 50 MiB עדיין הופכת ל־malformed JSON

`_bounded_text()` חותך בשקט (`src/pwa/floorplan/dxf_source.py:18-23`) ו־worker result נקרא עם `MAX_DXF_BYTES` (`src/pwa/floorplan/dxf_source.py:98-110`).

**Concrete failure scenario:** DXF עד 50 MiB עם 200,000 ישויות לא-ממופות ושמות ארוכים יכול להפיק JSON גדול מהמקור עקב source refs/messages חוזרים. ה־JSON נחתך ומוחזר operational CLI 2 במקום partial או resource-limit. זהו edge case מוגבל ולכן נשאר `INFO`.

---

### I-NA3-2 — INFO — שינוי `.gitattributes` חורג מבעלות §16

PLAN-002 אינו מונה `.gitattributes` בין הקבצים המותרים (`docs/plans/PLAN-002-floorplan-parsing.md:465-494`), אך נוספו כללים גלובליים ל־SVG/DXF/XML/log (`.gitattributes:14-21`).

**Concrete failure scenario:** binary DXF עתידי יקבל בטעות text/EOL normalization, דבר שיכול לשנות בתים ו־hash בעת checkout. לא הוכח כשל נוכחי ב־Part 1, ולכן זה `INFO`, אך השינוי דורש תיעוד/אישור scope או צמצום.

## 3. Acceptance criteria

| AC | verdict | reason | citation |
|---|---|---|---|
| AC-1 | `VERIFIED` | exact 1.0.0/1.1.0 lookup וענפי duplicate נבדקים בפועל. | `src/pwa/contracts.py:56-78`, `99-115`; `tests/unit/test_contract_versions.py:75-101`, `139-181` |
| AC-2 | `VERIFIED` | ריצת 316 הנוכחית היא עובדה stipulated; ה־command log tracked מראה שגם PLAN-000/001 וה־schema suites נכללו. | `evidence/PLAN-002/test-results/RUN-PLAN002-REWORK-20260810/command.log:9-30` |
| AC-3 | `VERIFIED` | הקוד אינו כותב ל־source run והבדיקה משווה hash tree לפני/אחרי בארבעת סוגי outcome. | `tests/integration/test_plan002_failure_matrix.py:713-785` |
| AC-4 | `NOT_MET` | `.staging` ancestor יכול להיות junction חיצוני, ולכן staging/finalization אינם מוכחים contained או same-volume. | `src/pwa/floorplan/builder.py:481-513`, `706-710`; `src/pwa/floorplan/runs.py:71-109` |
| AC-5 | `VERIFIED` | staging קיים נדחה; exception paths משאירים staging ואין קוד delete/resume. | `src/pwa/floorplan/builder.py:504-513`, `957-996` |
| AC-6 | `VERIFIED` | Layer A של שני adapters מפיק canonical projection ו־hash זהים. | `tests/golden/test_floorplan_golden.py:17-27` |
| AC-7 | `VERIFIED` | units, transform ו־confidence שונים ומאומתים במפורש לכל adapter. | `tests/golden/test_floorplan_golden.py:30-51` |
| AC-8 | `VERIFIED` | reordering שומר IDs; anchor-extension מכוסה; duplicate openings נכשלות. | `tests/unit/test_floorplan_normalize.py:132-171`; `src/pwa/floorplan/validate.py:264-282` |
| AC-9 | `VERIFIED` | canonical winding, uniqueness, nonzero area וכל non-adjacent intersection נאכפים. | `src/pwa/floorplan/normalize.py:75-82`; `src/pwa/floorplan/validate.py:175-207` |
| AC-10 | `VERIFIED` | wall resolution, span collinearity, projected width ו־half-width-at-both-ends קיימים; שלושת counter-examples תוקנו. | `src/pwa/floorplan/normalize.py:287-325`; `src/pwa/floorplan/validate.py:130-172`; `tests/unit/test_floorplan_normalize.py:294-397` |
| AC-11 | `VERIFIED` | scale contradiction ו־dimension tolerance מפיקים את הקודים המחייבים. | `src/pwa/floorplan/builder.py:721-750`; `src/pwa/floorplan/validate.py:286-291` |
| AC-12 | `VERIFIED` | security-sensitive DXF kinds מסווגים error לפני unknown-layer warning; raw errors נשמרים ב־precedence. | `src/pwa/floorplan/dxf_worker.py:72-87`; `src/pwa/floorplan/builder.py:386-415` |
| AC-13 | `NOT_MET` | artifacts עצמם schema-valid, אך inventory paths אינם קיימים במקום המוצהר ו־annotation/source lineage יכול להיקשר ל־snapshot שונה. | `src/pwa/floorplan/runs.py:113-128`; `src/pwa/floorplan/builder.py:661-716`, `873-881` |
| AC-14 | `NOT_MET` | renderer דטרמיניסטי ובטוח תחת input יציב, אך source יכול להשתנות בין extract, embed ו־hash ולכן overlay יכול להציג מקור שאינו מקור הדטקציות. | `src/pwa/floorplan/builder.py:313-331`, `712-756`; `tests/unit/test_floorplan_overlay.py:46-67` |
| AC-15 | `NOT_MET` | XML escaping נכון, אך שמות layer/layout נשמרים; בנוסף נתיבים מוחלטים ושם המשתמש נמצאים כבר ב־tracked evidence. | `src/pwa/floorplan/dxf_worker.py:61-81`; `src/pwa/floorplan/overlay.py:57-64`; `evidence/PLAN-002/reviews/independent-anthropic-code-review-20260810.md:275-280`, `524-531` |
| AC-16 | `VERIFIED` | errors/warnings ממופים ל־failed/partial, וריצה קיימת אינה ניתנת ל־overwrite או resume. | `src/pwa/floorplan/builder.py:801-804`, `504-513` |
| AC-17 | `NOT_MET` | source-side lexical reparse tests נסגרו, אך destination reparse ו־post-preflight source replacement שוברים containment/hash-before-parse מקצה לקצה. | `src/pwa/floorplan/runs.py:11-110`; `src/pwa/floorplan/builder.py:706-756` |
| AC-18 | `NOT_MET` | מגבלות bytes/geometry קיימות, אך entity cap אינו כולל paperspace וכל layouts נוספים. | `src/pwa/floorplan/config.py:9-20`; `src/pwa/floorplan/dxf_worker.py:143-182` |
| AC-19 | `VERIFIED` | IMAGE/XREF/OLE/INSERT מסווגים ללא פתיחת path חיצוני; אין dereference של השדה החיצוני. | `src/pwa/floorplan/dxf_worker.py:17-23`, `72-79` |
| AC-20 | `NOT_MET` | מטריצת הכשל רחבה, אך paperspace entity overflow יכול לקבל unsupported/timeout/CLI 2 במקום `PARSE_RESOURCE_LIMIT` + CLI 3; אין row שמכסה זאת. | `src/pwa/floorplan/dxf_worker.py:143-182`; `src/pwa/floorplan/dxf_source.py:98-110` |
| AC-21 | `VERIFIED` | 316/0/0/0 ו־clean `git diff --check` נמסרו כעובדות stipulated; ראיית git tracked היא exit 0. | `evidence/PLAN-002/implementation/git-verification.json:1-10` |
| AC-22 | `VERIFIED` | dependency diff ריק; הדבר גם stipulated עבור כל עבודת PLAN-002. | `evidence/PLAN-002/implementation/git-verification.json:7-10` |
| AC-23 | `WEAK_EVIDENCE` | לא נמצאו קוד/dependencies ל־cloud/GPU/network, אך “לא התרחשה פעולה” היא עובדת תהליך שאינה ניתנת להוכחה עצמאית מה־filesystem בלבד. | `docs/plans/PLAN-002-floorplan-parsing.md:39-45`, `494-496`; `evidence/PLAN-002/acceptance.md:16-17` |

## 4. Challenged and held

- **Absolute/relative `parse_run_id` escape:** ערכים עם `/`, `\`, `:`, `..`, drive או UNC אינם עוברים את ה־allowlist, וה־rejected result אינו משתמש בערך לבניית יעד. החזיק (`src/pwa/floorplan/builder.py:44-57`, `445-463`).
- **In-root junction alias ו־junction ב־`runs_root`:** שני השורשים והשרשרת הלקסיקלית נבדקים לפני resolve; החזיק בצד המקור (`src/pwa/floorplan/runs.py:11-59`).
- **Manifest/quality symlink ancestor:** שתי הקריאות עוברות containment לפני `read_text`; החזיק (`src/pwa/floorplan/builder.py:514-533`).
- **GC-6 counter-examples:** 0.05→0.03, 0.04 perpendicular→fail, ו־0.9→0.8991/pass; שלושתם מוחזקים בקוד ובבדיקות (`tests/unit/test_floorplan_normalize.py:294-397`).
- **Static raster metadata attack:** EXIF ו־PNG text אינם מועברים, original hash אינו sanitized hash, ושתי קריאות יציבות מפיקות אותם בתים. החזיק בהיעדר filesystem race (`src/pwa/floorplan/builder.py:288-331`; `tests/unit/test_floorplan_builder.py:38-150`).
- **Overlay leaf symlink/pre-existing file:** `"xb"` נכשל לפני overwrite ומשאיר את הקובץ הנטוע ללא שינוי. החזיק עבור ה־leaf עצמו (`tests/integration/test_plan002_parse_run.py:708-744`).
- **DXF source/detection independence:** שינוי הבדיקה אינו weakening; היא מאמתת source קצר מול detection ארוך בתוך viewBox מורחב, כך שהפער נראה בפועל (`tests/unit/test_floorplan_overlay.py:173-225`).
- **Unsupported ARC precedence:** ARC-only wall נשמר כ־`PARSE_UNSUPPORTED_FEATURE` ולא נדרס ב־empty geometry (`tests/integration/test_plan002_parse_run.py:825-874`).
- **M-8/M-9 evidence:** duplicate branches מקבלים fixtures שמגיעים לענף הנכון, ו־AC-3 מכיל assertions ממשיים (`tests/unit/test_contract_versions.py:139-181`; `tests/integration/test_plan002_failure_matrix.py:713-785`).
- **Append-only/schema/dependency discipline:** error codes נוספו בסוף, 1.0.0 לא שונה, ו־dependency diff ריק (`contracts/error_codes.md:44-67`; `evidence/PLAN-002/implementation/git-verification.json:7-10`).

## 5. Required gate conditions before approval

1. **`bounded code fix`** — לסגור את C-NA3-1 באמצעות destination containment מלא ואטומי עבור `.staging`, כל directories הביניים וכל leaf writes.
2. **`bounded code fix`** — לפרש, להעתיק, לסניטז ולקשור hashes מאותו immutable snapshot; אין לקרוא שוב source/annotation מקוריים לאחר snapshot verification.
3. **`bounded code fix`** — לתקן את שורש העתקת inventory ולהוכיח לאחר finalization שכל path המוצהר ב־derived manifest קיים וה־hash שלו תואם.
4. **`bounded code fix`** — לאכוף source-run finality, התאמת run/project/artifact identity, בדיוק floorplan אחד ו־inventory paths ייחודיים.
5. **`requires human decision (PLAN-002 §20)`** — לבחור ולאשר contract חד-משמעי ל־selected PDF-page derivatives, ואז להחזיר את ה־capability המחייבת עם integration test.
6. **`bounded code fix`** — להסיר שמות layer/layout חופשיים מארטיפקטים באמצעות opaque/redacted source refs.
7. **`requires human decision (PLAN-002 §20)`** — להכריע כיצד להסיר את הנתיבים/שם המשתמש שכבר נמצאים ב־tracked evidence בלי להפר את מדיניות ה־append-only.
8. **`bounded code fix`** — לאכוף `MAX_DXF_ENTITIES` במצטבר על modelspace וכל layouts, עם outcome מדויק של `PARSE_RESOURCE_LIMIT`.
9. **`bounded code fix`** — להבטיח שכל preflight/staging filesystem failure מוחזר מ־`parse_run()` כ־CLI-2 result ולא כחריגה.
10. **`requires human decision (PLAN-002 §20)`** — לאחר כל התיקונים, לחדש את Layer A artifacts/overlays ולהעביר את ה־Visual/Geometry evidence gate המחייב שב־§20.