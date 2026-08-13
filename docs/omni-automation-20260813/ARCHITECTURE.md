# ARCHITECTURE — PanoWorld Automation

- Status: `VERIFIED` — אושר יחד עם PLAN-000 ‏(משה, ‏2026-08-05). ‏PLAN-000 בוצע ומוזג: החוזים ‏(C9 חלקית — ‏validator בלבד), ‏schemas ו-state machine קיימים בפועל ב-main.
- מסמכים סמכותיים: [01](01-חזון-וארכיטקטורת-האוטומציה.md), [03](03-תוכנית-בנייה-מפורטת-לפי-שלבים.md), [08](08-מדיניות-ניהול-מודלים-וסוכנים-omni-first.md), [09](09-מדיניות-האוטומציה-החדשה-WP0-WP6.md) ו־[10](10-תוכנית-האוטומציה-המפורטת-WP0-WP6.md). מסמך 06 נשמר כ-baseline תפקידי.
- כללי סימון: **[מאושר]** = הוחלט במסמכי התכנון וקיבל את אישור משה במסגרתם. **[Candidate]** = מועמד הדורש spike/ADR/אישור. אין לממש Candidate בלי החלטה ב-OPEN-DECISIONS → ADR.

## 1. Context

```text
┌─────────────┐   floorplan + style ref   ┌──────────────────────────────┐
│    משה      │ ─────────────────────────▶│  PanoWorld-Automation        │
│ (human      │ ◀──── approvals (3 gates) │  (מכונה מקומית, Windows)      │
│  gates)     │ ◀──── evidence/dashboards │                              │
└─────────────┘                           └──────────┬───────────────────┘
                                                     │ validated package
                                                     ▼
                                          ┌──────────────────────────────┐
                                          │  H200 cloud server (Linux)   │
                                          │  PanoWorld inference          │
                                          └──────────┬───────────────────┘
                                                     │ panoramas / 3DGS / logs
                                                     ▼
                                          QA → human approval → delivery
```

- **[מאושר]** הפיתוח וההכנה מקומיים; ‏PanoWorld inference רק על H200 בענן (מסמך 02).
- **[מאושר]** המכונה המקומית אינה מריצה PanoWorld ‏(5GB VRAM, cc 6.1 — אומת ב-preflight: ‏[evidence](../evidence/SESSION-001/preflight-report.md)).

## 2. Components

| # | רכיב | תפקיד | סטטוס החלטה |
|---|---|---|---|
| C1 | Orchestrator | ‏state machine, הקצאת עבודה, merges, human gates | **[מאושר]** קונספטואלית; מנוע ה-workflow עצמו **[Candidate]** (D-002) |
| C2 | Intake service | ‏originals, hashes, metadata, input QA | **[מאושר]** |
| C3 | Floorplan parser | ‏raster/vector → ‏`floorplan_parse.json` | **[מאושר]** קונספטואלית; בחירת CubiCasa/baseline **[Candidate]** |
| C4 | Geometry compiler | ‏parse → ‏white model ‏(Blender headless) | **[מאושר]** |
| C5 | Camera planner | ‏viewpoints, extrinsics, גרף קשרים | **[מאושר]** |
| C6 | Render adapter | ‏BlenderProc → ‏place_image/depth/scale/extrinsics | **[מאושר]** קונספטואלית; אימות equirectangular **[Candidate]** (spike) |
| C7 | Style analyzer | ‏style reference → ‏`style_spec.json` | **[מאושר]** |
| C8 | Source panorama generator | פנורמת התחלה מעוצבת | **[מאושר]** קונספטואלית; ‏provider ‏(API/מודל ענן) **[Candidate]** |
| C9 | PanoWorld packager + validator | בניית package + אימות מלא מולו | **[מאושר]** — נבנה ראשון (PLAN-000) |
| C10 | H200 runner | ‏lifecycle של שרת, upload/run/download/terminate | **[מאושר]** קונספטואלית; ספק ענן **[Candidate]** |
| C11 | QA engine | ‏geometry/style/consistency checks | **[מאושר]** |
| C12 | Dashboard | פיקוח, approvals, evidence | **[מאושר]** קונספטואלית; ‏stack **[Candidate]** |
| C13 | State/artifact store | ‏PROJECT-STATE, runs, evidence | ‏layout **[מאושר]** (מסמך 04); ‏DB/queue **[Candidate]** (D-003) |

## 3. Data flow

הזרימה הקנונית והחוזים (9 artifacts) מוגדרים במסמך [01](01-חזון-וארכיטקטורת-האוטומציה.md) — ‏"נוסחת העבודה" ו-"חוזי הביניים". תמצית לצורך הקשר:

```text
inputs → project_manifest.json → floorplan_parse.json → scene_geometry.json
      → camera_plan.json → control assets (place_image/depth/scale/extrinsics per viewpoint)
      → style_spec.json → source panorama → panoworld package (map JSON + viewpoints/)
      → run_manifest.json (H200) → qa_report.json → human approval
```

- **[מאושר]** כל מעבר בין רכיבים הוא קובץ עם schema + version; אין תקשורת חבויה בין סוכנים.
- **[מאושר]** ‏`assumptions.json` נצבר לאורך כל ה-pipeline ומוצג בכל gate אנושי.
- **[מאושר]** ‏runs תחת `runs/<run-id>/` ‏immutable; ‏evidence תחת `evidence/<plan-id>/` (מסמך 04).

## 4. Trust boundaries

| # | גבול | סיכון | בקרות |
|---|---|---|---|
| TB-1 | קלטי משתמש (floorplan, style image) | קבצים זדוניים/פגומים ‏(PDF exploits, zip bombs) | ‏validation לפני parsing; עיבוד ב-sandbox/container ‏**[Candidate]**; אין הרצת מאקרו/סקריפט מקלט |
| TB-2 | הרצת Blender Python / BlenderProc | ‏arbitrary code execution בסביבה המקומית | סקריפטים דטרמיניסטיים מה-repo בלבד; אין eval על תוכן שנוצר ע"י LLM ללא review; ‏Blender MCP מוגבל לתיקון חריגים ידני, לא ל-batch (מסמך 05) |
| TB-3 | קוד שנכתב ע"י סוכני AI | ‏drift, שינויים מחוץ ל-scope, החלשת בדיקות | ‏ownership בלעדי, tests, cross-provider review, רק orchestrator ממזג (מסמך 04) |
| TB-4 | מכונה מקומית ↔ H200 | דליפת secrets, שרת יתום (עלות), exfiltration | ‏secrets מחוץ לריפו (env/secret store); ‏terminate ב-finally path; חשבון ענן עם הרשאות מינימליות; ‏telemetry של עלות |
| TB-5 | מודלים/weights של צד שלישי | רישוי (GPL/MIT/Apache mix), supply chain | ‏license matrix; ‏pinning של גרסאות ו-hashes; רכיבי GPL כ-tools חיצוניים מבודדים, לא כ-library מקושר |
| TB-6 | ‏outputs של PanoWorld | תוכן לא צפוי; טענות דיוק | ‏QA דטרמיניסטי + human gate; סימון קונספטואלי (ראו [REQUIREMENTS.md](REQUIREMENTS.md) §3) |

## 5. החלטות מאושרות מול Candidates — סיכום

### מאושר (במסמכי התכנון; מימוש עדיין דורש PLAN מאושר)
1. ארכיטקטורת pipeline דטרמיניסטית עם סוכנים מתזמרים — לא LLM יחיד (מסמך 01).
2. ‏Contracts-first: ‏schemas ו-package validator לפני parser/Blender (מסמכים 00/03).
3. ‏state machine ו-gates G0–G9 (מסמכים 01/04).
4. שלושה human gates מינימליים (מסמך 01).
5. ‏model governance: OmniRoute מנהל; Anthropic מועדפת כאשר זמינה; fallback כשיר ומתועד ללא החלשת gates (מסמכים 08–10).
6. ‏PanoWorld inference בענן בלבד; הכנה מקומית (מסמך 02).
7. סדר מימוש: Contracts → Intake → Packager מוקדם → Parsing → Geometry → ... (מסמך 03).

### הוכרעו ב-PLAN-000 (ראו docs/decisions/)
- ‏D-001 → ‏**ADR-0001**: ‏Git בשורש הנוכחי, ‏branch לכל PLAN, נתיבים פנימיים ASCII. **מיושם.**
- ‏D-008 → ‏**ADR-0002**: ‏envelope + ‏semver פר-schema + ‏bundle version. **מיושם** ‏(schemas/ + ‏compute_content_hash).
- חלק מ-D-010 → ‏**ADR-0003**: ‏vendoring תת-סט scene0000 כ-golden fixture. **מיושם.**

### Candidates פתוחים (ראו [OPEN-DECISIONS.md](OPEN-DECISIONS.md))
- ‏D-002: ‏workflow engine ‏(Prefect/Temporal/מינימלי).
- ‏D-003: ‏storage/state ל-MVP ‏(SQLite/Postgres, ‏queue).
- ‏D-004: ‏floorplan parser baseline.
- ‏D-005: ‏source panorama provider.
- ‏D-006: ספק ענן H200.
- ‏D-007: ‏dashboard stack.
- ‏D-009: תשתית cross-provider review.
- ‏D-010 (יתרה): ‏license matrix מלא לפני שימוש מסחרי.
- ‏D-011: קרדינליות style references.
