# ADR-0003 — Vendoring of PanoWorld demo-scene subset as golden fixture

- Status: ACCEPTED (משה, ‏2026-08-05, באישור PLAN-000; היה A4/חלק מ-D-010)
- Context: ‏doc 03 שלב 0 דורש "golden test מול demo package"; ה-validator חייב fixture אמיתי כדי לא להיות מכויל רק על דאטה סינתטי. ריפו PanoWorld הוא Apache-2.0 ‏(GitHub `license.spdx_id`), ללא tags/releases.
- Decision: ‏vendoring של **הסגירה המלאה של `map_panoworld0.json`** מ-`examples/full_pipeline_demo_datas/scene0000` — ‏viewpoints ‏0000/0001/0008/0011, ‏4 קבצי החובה בלבד לכל viewpoint ‏(ללא style panoramas, ‏~8.5MB) — אל `tests/golden/panoworld_demo_subset/`, עם: ‏commit SHA מוצמד שנקבע בזמן ה-fetch, ‏`fixture-metadata.json` ‏(מקור, ‏SHA, תאריך, ‏sha256 לכל קובץ), ‏`NOTICE` ועותק רישיון upstream ‏(חובת Apache-2.0 בהפצה חוזרת).
- Consequences: בדיקת תאימות אמיתית ללא הורדת weights ‏(68.9GB); ‏~8.5MB בינארי בריפו — מקובל; רענון ה-fixture רק בסקריפט ידני עם SHA חדש ותיעוד. אי-התאמת הרישוי model-card ‏(MIT) / dataset ‏(other) אינה נוגעת ל-fixture הזה (קבצי examples מהריפו ה-Apache בלבד); ‏license matrix מלא נשאר לשלב 12.
- Evidence: ‏PLAN-000 §5 C9 + ‏T6/T11; ‏panoworld-compat §7–8.
