# PLAN-001 — Intake and Packager Baseline

- Plan ID: `PLAN-001-intake-and-packager-baseline`
- Status: **`DONE`** — review חוצה־ספקים, תיקוני findings, evidence טרי ומיזוג orchestrator-only הושלמו מקומית
- Branch: `plan/PLAN-001`
- Policy: `MODEL-ROUTING-v1`
- Requested implementer: OpenAI Codex / HIGH

## Goal

לקלוט floorplan ותמונת style, לשמור originals ביט־זהים עם SHA-256, להפיק
`project_manifest` ו־`input_quality_report` לפי schemas 1.0.0, ולבנות package
מ־fixtures קיימים שעובר את ה־validator — ללא parsing, Blender, PanoWorld או H200.

## Scope

- immutable run תחת `runs/<run-id>/`, שנבנה תחילה תחת `runs/.staging/`.
- PNG/JPG דרך Pillow; PDF raster preview; DXF audit + SVG preview; DWG header/version בלבד.
- fixture packager עבור Layer A הסינתטי ו־Layer B golden.
- `panoworld_manifest` לפי schema קיים, map order נשמר, package tree hash דטרמיניסטי.
- wrapper עובד ל־validator ו־evidence harness שאינו מוחק ראיות קודמות.
- raw `package-validator.json`; אין schema או bundle bump חדשים.

## Non-goals

- אין OCR, floorplan parsing, geometry, cameras, rendering, style understanding,
  source panorama, workflow engine, Blender, PanoWorld, H200 או cloud.
- אין preview/entity parsing ל־DWG ואין artifacts מזויפים לשלבים שלא קיימים.

## Tasks

1. להכניס ל־Git את שלושת prompt templates הקיימים ללא שינוי ולוודא baseline נקי.
2. לממש copy/hash/staging בטוח ו־intake לכל הפורמטים המאושרים.
3. להפיק manifests schema-valid ו־content hashes דרך `pwa.contracts` הקיים.
4. לבנות package מה־fixtures, לשמר map insertion order ולחשב inventory hash.
5. להריץ את ה־validator הקיים ולשמור raw report.
6. לתקן את CLI import path ואת מחיקת evidence ב־`tools/run_checks.py`.
7. להוסיף tests, evidence, reviews ו־handoff; לא למזג.

## Acceptance criteria

- originals נשמרים byte-identical וה־SHA שלהם תואם ל־manifest.
- manifests עוברים את schemas הקיימים; חוסר units/scale יוצר blocker ולא ניחוש.
- symlink/reparse point, format mismatch, קובץ פגום ו־run-id קיים נדחים ללא overwrite.
- PDF מפיק page metadata + previews; DXF מפיק audit/metadata + SVG; DWG מפיק header/version.
- Layer A עובר with-config ו־Layer B עובר scene-only ללא errors.
- package hash יציב לאותם bytes ומשתנה לאחר mutation.
- map order נשמר; אין `sort_keys=True` בכתיבת map/manifest.
- wrapper ה־validator עובד ללא `PYTHONPATH`.
- evidence runs נשמרים בתיקיות ייחודיות ואינם מוחקים היסטוריה.
- כל בדיקות PLAN-000 והבדיקות החדשות עוברות; Git נקי למעט artifacts ignored.
- DWG acceptance אמיתי עבר על קובץ מקומי לא־רגיש; שם/נתיב המקור צונזרו והקובץ לא נכנס ל־Git.

## Security / rollback

- regular files בלבד; paths יחסיים; אין `shell=True`; אין שמות מקור/EXIF/נתיבים
  אבסולוטיים ב־artifacts או logs.
- finalized run אינו נכתב מחדש. כשל נשאר ב־staging ולא הופך ל־run.
- rollback בקוד דרך revert של commits; finalized runs אינם נמחקים אוטומטית.
- אין merge, push, התקנת כלי מערכת או פעולה בענן בתוכנית זו.

## Evidence and handoff

- `evidence/PLAN-001/test-results/<evidence-run-id>/`
- `evidence/PLAN-001/acceptance.md`
- `evidence/PLAN-001/reviews/`
- `docs/handoffs/HANDOFF-PLAN-001-to-review-001.md`

PLAN-001 יהיה `DONE` רק לאחר evidence טרי, review בלתי תלוי, תיקון findings
קריטיים/מהותיים, merge ועדכון state. סוכן זה יעצור לפני review/merge.

## Closeout record — 2026-08-09

- Anthropic Sonnet 5 / HIGH ביצע review בלתי תלוי וחוצה־ספקים: `APPROVE_WITH_FIXES`, ללא ממצאי CRITICAL/MAJOR.
- M-1 אושרר במפורש: commit ‏`3baedba` נשאר בענף משום שהקמת קמפיין Kanban לחלק 1 אושרה בידי משה והפכה קנונית ב-kickoff; הוא docs/state-only ואינו מרחיב את runtime של PLAN-001.
- M-2 נסגר ב־`evidence/PLAN-001/RUN-REPORT-PLAN-001-CLOSEOUT-20260809.md`.
- M-3/M-4 תוקנו ב־`87f00db`: בדיקת junction אמיתית ב-Windows ו-cap של 100MP לפני `Image.verify()`.
- verification טרי: 122/122 tests, ‏17/17 fixture round-trip, ו-validator עם 0 errors/0 warnings.
- אין Floorplan Parsing, ‏H200/GPU/remote/cloud; ‏G7/G8 נשארים **DEFERRED TO PART 2**.
