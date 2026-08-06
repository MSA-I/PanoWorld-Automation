# סיכום לפני הפעלת Hermes Kanban

## סטטוס
תשתית Hermes Kanban הוקמה ואומתה, אך הקמפיין נשאר **`DORMANT`** ולא הופעל. אין worker פעיל ואין כרטיס `ready` או `running`.

- Board: `panoworld-dev`
- Hermes Project: `panoworld-dev` (`p_0539c20f`)
- כרטיס הפעלה: `t_4ddc34f3` — ‏`blocked / needs_input`
- גרף: 13 כרטיסים — 1 חסום, 12 ממתינים לתלויות
- תקציבים: `agent.max_turns: 90`, ‏`goals.max_turns: 40`, וכרטיסים מורכבים: 60–80

## תחום האחריות
Hermes ינהל רק את **חלק 1 — פיתוח PanoWorld Automation**: תכנון, מימוש, בדיקות, ביקורת, evidence, handoffs ומיזוגים.

מחוץ לתחום: **H200 Runner**, שרת/GPU, credentials, עלויות, העלאות מרחוק, הפעלת PanoWorld על H200 ו־Gates ‏G7/G8. תלות ב־H200 תסומן `DEFERRED TO PART 2` ולא תיחשב כבדיקה שעברה.

## מה הוקם
1. נוצר לוח ייעודי המקושר למאגר המקומי ול־Hermes Project.
2. נוצר שער התחלה יחיד וחסום; כל יתר הכרטיסים נמצאים מאחוריו בשרשרת dependencies סדרתית.
3. הכרטיסים מכסים את סגירת PLAN-001 ואת שלבי Floorplan Parsing, Geometry, Cameras, Rendering/Depth, Style, Source Panorama מקומי, QA, Dashboard, Hardening וקבלת חלק 1.
4. כל כרטיס נועל scope מקומי, model-routing, רישום מודל בפועל, review חוצה-ספקים, tests, evidence ו־human gates.
5. retries הוגבלו ל־1 כדי למנוע צריכת קרדיטים חוזרת ושקטה.
6. מחזור העבודה נעול ל־`PLAN → APPROVAL → IMPLEMENT → TEST → REVIEW → REWORK → VERIFY → MERGE/HANDOFF`.

## פקודת ההפעלה הידנית
ביום שבו משה מאשר להתחיל:

```bash
hermes kanban --board panoworld-dev unblock t_4ddc34f3 \
  --reason "Approved by Moshe — start Part 1 development campaign"
```

ה־Gateway יאסוף את הכרטיס במחזור הבא. להפעלה מיידית לאחר ה־unblock אפשר להריץ גם:

```bash
hermes kanban --board panoworld-dev dispatch --max 1
```

`dispatch` לבדו אינו מפעיל את הקמפיין כל עוד כרטיס ההתחלה חסום.

## רציפות והתאוששות
הקמפיין לא יסתמך על צ׳אט אחד. הכרטיסים, התלויות והיסטוריית הריצות יישמרו באופן מתמשך. במקרה של crash, quota, timeout או צורך בהחלטה אנושית, הכרטיס יעבור ל־retry/blocked וימשיך מה־checkpoint האחרון; לא יתבצע fallback שקט.

## נקודות שבהן משה נדרש
- אישור תוכנית חדשה או שינוי scope/contracts.
- Geometry/Visual Gate קריטי.
- החלטה על blocker שלא ניתן לפתור מקומית.
- כל פעולה הקשורה לחלק 2 — H200 — דורשת אישור נפרד ואינה כלולה בקמפיין זה.
