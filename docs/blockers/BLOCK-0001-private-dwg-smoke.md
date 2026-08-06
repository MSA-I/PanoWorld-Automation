# BLOCKER

- Blocker ID: BLOCK-0001
- PLAN_ID: PLAN-001
- Owner: Moshe
- Severity: medium
- Opened at: 2026-08-06
- Status: RESOLVED
- Resolved at: 2026-08-06

## Exact failure

אין בריפו או ב־runs קובץ DWG אמיתי שניתן להשתמש בו ל־acceptance smoke.

## Input/command

```text
rg --files -g "*.dwg" -g "!runs/**" -g "!.venv/**"
```

## Expected

קובץ DWG חוקי, פרטי ולא־רגיש, שניתן לקלוט תחת `runs/` בלי להכניסו ל־Git.

## Actual

לא נמצא קובץ. בדיקות אוטומטיות מכסות header/version סינתטי בלבד.

## Root cause

known — ה־fixture חייב להגיע מהמשתמש; PLAN-001 אוסר הורדת fixture לא מאושר.

## Impact

- blocked stage: DWG real-file acceptance בלבד.
- downstream that can continue: review של PNG/JPG/PDF/DXF, packager, validator ו־security.

## Recommendation

משה יספק נתיב לקובץ DWG חוקי ולא־רגיש. הסוכן יריץ intake, יאמת byte hash ויכתוב evidence מצונזר ללא שם/נתיב המקור.

## Exit criteria

DWG smoke exit 0; manifest/report schema-valid; hash המקור וה־original זהים; `dwg-intake-redacted.json` נשמר; הקובץ עצמו אינו tracked.

## Resolution

- A local generic, non-sensitive DWG from the user's CAD block library was used without copying its source name/path into evidence.
- `RUN-20260806-060723-42cc1f60` completed with exit code 0; detected real header/version `AC1024` and 1,249,292 bytes.
- Source and immutable copied-original SHA-256 values matched: `1ba59cf2fa7b34c191e59901b9fb625fba0c1714a90a60fde558c3860a9aad1d`.
- `project_manifest`, `input_quality_report` and `panoworld_manifest` each validated with 0 schema errors; package validator returned 0 errors and 0 warnings.
- The run remains ignored under `runs/`; the DWG is not tracked. Redacted evidence: `evidence/PLAN-001/dwg-intake-redacted.json`.
