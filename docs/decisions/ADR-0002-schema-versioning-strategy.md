# ADR-0002 — Schema versioning: envelope + per-schema semver + bundle version

- Status: ACCEPTED (משה, ‏2026-08-05, באישור PLAN-000; היה D-008)
- Context: ‏doc 01 מחייב "schema וגרסה" לכל artifact אך ללא אסטרטגיה קונקרטית; נדרשו provenance, סמנטיקת partial/error ותאימות producer/consumer ‏(ממצאי contract-researcher ‏2–4, ‏12, ‏15).
- Decision:
  1. ‏JSON Schema **draft 2020-12**; קבצים ב-`schemas/<name>/v<major>/<name>-<semver>.schema.json` עם `$id` מגורסן.
  2. **Envelope אחיד** לכל artifact: ‏`schema_id`, ‏`schema_version`, ‏`artifact_id`, ‏`project_id`, ‏`run_id`, ‏`created_at`, ‏`producer` ‏(agent/provider/model/effort), ‏`inputs[{artifact_id, content_hash}]`, ‏`content_hash`, ‏`status: complete|partial|failed`, ‏`errors[]` עם reason codes; התוכן הספציפי תחת `payload`.
  3. ‏MINOR/PATCH אדיטיביים בלבד (נאכף בבדיקות); שינוי שובר = ‏MAJOR חדש + ‏ADR.
  4. ‏`contracts_bundle_version` יחיד נרשם ב-project_manifest וב-run_manifest.
- Consequences: כל artifact נושא provenance מלא ושרשרת hash; מטריצת תאימות פשוטה; עלות — שדות envelope בכל קובץ (מקובל).
- Evidence: ‏PLAN-000 §5 C7; ‏schemas/envelope/v1/ ‏(T3).
