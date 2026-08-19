# תוכנית: תיקון ועדכון מסמכים בעקבות אימות מחקר הכלים

> **סטטוס:** ממתין לאישור משה. אין ביצוע לפני אישור.

**מטרה:** לאמת את ממצאי מחקר הכלים החיצוני מול המקור, ולתקן/לעדכן את מסמכי הפרויקט כך שישקפו את ההחלטות הנכונות (החלפת C8, פסילת openPlan3D כ-parser, אזהרות רישוי).

**היקף:** עדכון מסמכים בלבד. אין שינוי קוד, אין merge, אין push.

---

## אימות שהושלם (עובדות מאומתות מול המקור)

| נושא | הממצא המאומת |
|---|---|
| openPlan3D | עורך 2D/3D ידני (SvelteKit + Three.js), לא מודל זיהוי מתמונה. "room detection" = זיהוי חדרים מקירות שצוירו ידנית. |
| lab-camera-optimizer | אופטימיזציית מצלמות ל-motion capture (ביומכניקה). אלגוריתמים גנריים (FOV/line-of-sight/coverage/greedy) ניתנים למיחזור; פונקציית המטרה לא רלוונטית לפנורמות. |
| IQA-PyTorch | רישיון = PolyForm Noncommercial 1.0.0 (המחקר צדק). |
| CubiCasa5K data | Zenodo = CC BY-NC-SA 4.0 (חמור מ-CC BY-NC). |
| Raster2Seq | קיים, MIT, 40★, פעיל (2026-07). מועמד ל-C3, דורש spike. |
| SkyPilot | קיים, Apache-2.0, 10502★, פעיל. מועמד ל-C10. |
| MinIO | archived=True, AGPL-3.0 (המחקר צדק). |
| PanoWorld | 2D Generator הרשמי (2026-08-04) מחליף את הצורך ב-C8 נפרד. |

---

## שלב 1 — עדכון `docs/ARCHITECTURE.md`

**שינוי 1a — C3 (Floorplan parser):**
- החלפת הטקסט `בחירת CubiCasa/baseline [Candidate]` ב:
  `בחירת Raster2Seq [Candidate, נדרש spike]; CubiCasa5K נדחה (stack 2019; data CC BY-NC-SA 4.0)`

**שינוי 1b — C8 (Source panorama generator):**
- הוספת הערה שהרכיב מוחלף: C8 מוחלף ב-PanoWorld 2D Generator הרשמי (מנוהל דרך C9). אין צורך במחולל פנורמת-התחלה נפרד.

**שינוי 1c — C10 (H200 runner):**
- הוספת `SkyPilot [Candidate]` כמועמד ל-provider-neutral runner, עם הערת cost/TTL reaper עצמאי.

## שלב 2 — עדכון `docs/05-מקורות-וקישורים.md`

**שינוי 2a — הוספת מועמדים חדשים** (סעיף/רשימות חדשות):
- Raster2Seq (Cornell-VAILab, MIT) — מועמד ל-C3.
- Building Tools (ranjian0, MIT) — מועמד ל-C4 (אלגוריתמים, לא domain model).
- SkyPilot (Apache-2.0) — מועמד ל-C10.
- equilib (Apache-2.0), nvTorchCam (Apache-2.0) — המרות 360 ל-C6.
- TorchMetrics (Apache-2.0) — מדדי QA ל-C11.

**שינוי 2b — אזהרות רישוי (סעיף חדש):**
- IQA-PyTorch = PolyForm Noncommercial 1.0.0 — לא למוצר מסחרי.
- MinIO = AGPL-3.0 + הועבר לארכיון (אפריל 2026).
- CubiCasa5K data = CC BY-NC-SA 4.0.
- pyvispoly = GPL דרך CGAL (לא אומת נתיב הריפו המדויק).

**שינוי 2c — תיקון תיאורים:**
- openPlan3D: לתקן מ"זיהוי walls/doors/windows" ל"עורך 2D/3D ידני (מתאים לשכבת תיקון אנושי, לא כמודל זיהוי)".
- lab-camera-optimizer: לתקן — אופטימיזציית מצלמות ל-motion capture; מיחזור אלגוריתמים גנריים בלבד.

## שלב 3 — עדכון `docs/PROGRESS.md`

- רשומה חדשה בראש הקובץ: `TOOLING RESEARCH VERIFICATION — DOCS-ONLY — 2026-08-18`, המסכמת את אימות מחקר הכלים החיצוני והתיקונים שבוצעו.

---

## קבצים משתנים
- `docs/ARCHITECTURE.md`
- `docs/05-מקורות-וקישורים.md`
- `docs/PROGRESS.md`

## לא נוגעים
- `docs/04-מתודיקת-ניהול-סוכנים-ומעקב.md` — כבר modified לפני הסשן (לא שלנו).

## סיכונים / שאלות פתוחות
- כל הכלים החדשים נרשמים כ-**[Candidate]** (דורשים spike/ADR), לא כ"מאומצים" — תואם למוסכמת הפרויקט.
- Raster2Seq חדש וקטן (40★) — יירשם כ"דורש spike" ולא כבחירה סופית.
- pyvispoly — נתיב הריפו 404; יירשם כהערת זהירות כללית (GPL דרך CGAL) ללא קישור מדויק.

---

## אימות סופי
לאחר הביצוע: `git diff --stat` על שלושת הקבצים, ואישור שאין שינוי בקבצים אחרים. **אין commit/push בלי הוראה מפורשת.**
