# REQUIREMENTS — PanoWorld Automation

- Status: `VERIFIED` — אושר יחד עם PLAN-000 ‏(משה, ‏2026-08-05); משקף את הדרישות התקפות. עדכונים עתידיים דרך PLANs/ADRs.
- מסמכים סמכותיים: [01-חזון-וארכיטקטורת-האוטומציה.md](01-חזון-וארכיטקטורת-האוטומציה.md), [03-תוכנית-בנייה-מפורטת-לפי-שלבים.md](03-תוכנית-בנייה-מפורטת-לפי-שלבים.md), [PanoWorld-מדריך-והסבר.txt](../PanoWorld-מדריך-והסבר.txt)
- מסמך זה מרכז דרישות; הוא אינו מחליף את מסמכי התכנון ואינו מוסיף scope חדש.

## 1. Functional Requirements

### FR-1 — Intake
- FR-1.1: קליטת floorplan ‏(PDF/JPG/PNG/DWG/DXF) ושמירת ה-original ללא שינוי, עם checksum.
- FR-1.2: קליטת תמונת style reference אחת לפחות.
- FR-1.3: זיהוי/קליטת units ו-scale; היעדר scale פותח blocker (Gate G0), לא ניחוש שקט.
- FR-1.4: כל קלט מקבל `project_manifest.json` עם hashes וגרסאות.

### FR-2 — Floorplan parsing
- FR-2.1: זיהוי קירות, חדרים, דלתות וחלונות מתוכנית נקייה, עם confidence לכל ישות.
- FR-2.2: פלט `floorplan_parse.json` + ‏SVG overlay לביקורת אנושית.
- FR-2.3: כל פער/הנחה נרשמים ב-`assumptions.json`; אין השלמות שקטות.

### FR-3 — Geometry
- FR-3.1: המרה דטרמיניסטית של ה-parse למודל 3D סגור (white model) ב-Blender headless: קירות, רצפה, תקרה, פתחים.
- FR-3.2: פלט `.blend`, ‏GLB ו-`scene_geometry.json` מנורמל במטרים.
- FR-3.3: גאומטריה נוצרת בסקריפטים דטרמיניסטיים בלבד; ‏Blender MCP מותר רק לתיקון חריגים ידני.

### FR-4 — Cameras
- FR-4.1: הצבת viewpoints אוטומטית (מרכזי חדרים, מעברים, פתחים) ללא camera-wall collision.
- FR-4.2: פלט `camera_plan.json` + המרה ל-extrinsics 4x4 בפורמט ש-PanoWorld דורש.
- FR-4.3: גרף קשרים בין viewpoints התואם למבנה map JSON של PanoWorld.

### FR-5 — Control assets rendering
- FR-5.1: רינדור לכל viewpoint: ‏`place_image.png`, ‏`place_depth.png`, ‏`place_depth_scale.txt`, ‏`extrinsics.txt`.
- FR-5.2: התאמת פיקסל-לפיקסל בין RGB לעומק; רינדור דטרמיניסטי (seed/config קבועים).

### FR-6 — Style ו-source panorama
- FR-6.1: הפקת `style_spec.json` מתמונת הרפרנס (palette, materials, lighting, negative constraints) עם confidence.
- FR-6.2: יצירת פנורמת התחלה מעוצבת (equirectangular) התואמת את הגאומטריה; ריבוי מועמדים ודירוג.

### FR-7 — Packaging
- FR-7.1: בניית package מלא בפורמט PanoWorld: ‏map JSON, תיקיות viewpoints וכל הקבצים הנדרשים.
- FR-7.2: **package validator** שמאמת מבנה, schemas, מטריצות, מידות תמונה וקיום קבצים, עם הודעות שגיאה מפורטות. ה-validator קודם לכל פיתוח parser (ראו PLAN-000).
- FR-7.3: ‏package הוא immutable עם hash.

### FR-8 — H200 execution
- FR-8.1: ממשק runner ניטרלי-ספק: upload → smoke test ברזולוציה נמוכה → validation → full run → download → **terminate מובטח**.
- FR-8.2: ‏mock מקומי מלא של ה-runner לפיתוח ובדיקות ללא ענן.
- FR-8.3: ‏`run_manifest.json` לכל ריצה: מודלים, seeds, config, זמנים, עלות, hashes.

### FR-9 — QA
- FR-9.1: בדיקות geometry (silhouettes, doorways, depth), style similarity ו-cross-view consistency.
- FR-9.2: פלט `qa_report.json` עם החלטה: APPROVED / REWORK / BLOCKED; ‏retry ממוקד עם reason code ותקציב retry.

### FR-10 — Orchestration ופיקוח
- FR-10.1: ‏state machine כמוגדר במסמך 01; אין מעבר state בלי artifact + validation + evidence.
- FR-10.2: ‏dashboard שעונה בכל רגע על שש שאלות הפיקוח של משה (מסמך 03, שלב 11).
- FR-10.3: כל תשעת ה-artifacts החוזיים (מסמך 01, "חוזי הביניים") נכתבים עם schema version.

## 2. Non-Functional Requirements

- NFR-1 **דטרמיניזם**: אותו קלט + אותו config + אותו seed → אותם artifacts (עד לרמת hash היכן שאפשר).
- NFR-2 **Traceability**: כל טענת "הושלם" מגובה ב-evidence path; ‏source of truth הוא קבצים/Git, לא צ'אט.
- NFR-3 **Immutability**: ‏originals, packages ו-runs אינם משוכתבים; כל run תחת `runs/<run-id>/`.
- NFR-4 **Human-in-the-loop**: אין הרצת GPU יקרה לפני אישור אנושי בנקודות המוגדרות (סעיף 4).
- NFR-5 **עלות GPU**: ‏smoke test לפני full run; כיבוי שרת מובטח גם ב-failure path; טלמטריית עלות לכל run.
- NFR-6 **אבטחה**: ‏secrets מחוץ לריפו; בידוד הרצת Python/Blender שרירותי; אין push/deploy ללא אישור.
- NFR-7 **תאימות סביבתית**: פיתוח על Windows 10 המקומי (ללא GPU inference); ‏PanoWorld רץ על Linux/H200 בלבד. קוד הפרויקט חייב לרוץ בשני ההקשרים (pathlib, ללא הנחות OS).
- NFR-8 **Model governance**: כל agent עם provider/model/effort/fallback לפי [06-מדיניות-ניתוב-מודלים-ומאמץ.md](06-מדיניות-ניתוב-מודלים-ומאמץ.md); אין החלפה שקטה.
- NFR-9 **רישוי**: רכיבי GPL ‏(BlenderProc, FloorplanToBlender3d) מבודדים כ-tools חיצוניים; ‏license matrix לפני שימוש מסחרי.
- NFR-10 **שפות**: מסמכים בעברית; קוד, schemas, שמות קבצים והודעות שגיאה באנגלית; נתיבי קוד פנימיים ASCII בלבד (הגנה מבעיות path בעברית על Windows).

## 3. Conceptual-Output Disclaimer

התוצרים של המערכת — פנורמות, 3DGS והדמיות — הם **קונספטואליים בלבד**:
- אינם תחליף לתכנון אדריכלי או הנדסי מאושר.
- אינם מתאימים לבנייה, רישוי, היתרים או כתבי כמויות.
- דיוק ממדי תלוי באיכות התוכנית ובמידות שסופקו; הנחות המערכת רשומות ב-`assumptions.json` ואינן אמת מדודה.
- כל תוצר מסומן כקונספטואלי ב-metadata וב-UI.

## 4. Human Gates (מינימום מחייב)

| Gate | מה מאושר | מתי | מיפוי ל-gates במסמך 04 |
|---|---|---|---|
| HG-1 Geometry approval | ‏white model: ‏top-down overlay + ‏3D preview | לפני rendering ו-GPU | G2 |
| HG-2 Source panorama approval | פנורמת ההתחלה המעוצבת | לפני full run על H200 | G5 |
| HG-3 Final output approval | פנורמות/3DGS סופיים + ‏QA report | לפני מסירה | G9 |

בנוסף, אישורים נקודתיים נדרשים בכל מקום שבו confidence נמוך מהסף או שנרשמה סתירה בקלט (G0/G1). הרשימה המלאה של G0–G9 — במסמך [04](04-מתודיקת-ניהול-סוכנים-ומעקב.md).
