# ADR-0001 — Git repository bootstrap in the current project root

- Status: ACCEPTED (משה, ‏2026-08-05, באישור PLAN-000; היה D-001)
- Context: הפרויקט נוהל כקבצים ללא versioning; ‏doc 04 מגדיר את Git כחלק מ-source of truth. הנתיב מכיל עברית ורווחים — סיכון ידוע לכלי צד-שלישי.
- Decision: אתחול Git **מיד**, בשורש הנוכחי ‏(`D:\משה פרוייקטים\פיתוח אתרים\PanoWorld-Automation`), ‏branch ראשי `main`, ‏branch עבודה `plan/<PLAN-ID>` לכל תוכנית; רק ה-Orchestrator ממזג. ‏.gitignore ו-.gitattributes ‏(LF לטקסט) קודמים לכל commit של fixture. כל הנתיבים הפנימיים בקוד — ASCII ויחסיים.
- Consequences: ‏traceability מלא מהיום; אם כלי עתידי (Blender/MMCV) ייכשל על הנתיב העברי — מעבר מבוקר ל-junction/clone בנתיב ASCII יתועד כ-ADR חדש (התשתית כבר repo-relative ולכן ניידת).
- Evidence: ‏commit ‏4d2703e; ‏PLAN-000 §5 C1.
