# BLOCKER

- Blocker ID: BLOCK-0001
- PLAN_ID: PLAN-001
- Owner: Moshe
- Severity: medium
- Opened at: 2026-08-06
- Status: OPEN

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

- fill only when resolved.
