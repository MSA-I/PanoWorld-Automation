# תוכנית אוטומציה — DeepSeek Full Part 1

## סטטוס וסמכות

- Plan ID: `PWA-DEEPSEEK-FULL-PART1-v2`.
- סטטוס: `READY FOR ACTIVATION — TOOL-CALL PROBE BLOCKED`.
- תאריך: 2026-08-13.
- תחולה: כל חלק 1 המקומי, לא רק WP0–WP6.
- מודל: `deepseek/deepseek-v4-pro-0813` דרך OpenRouter.
- reporter מכני: `deepseek/deepseek-v4-flash-0731`.

## 1. יעד

להשלים את כל פיתוח חלק 1 המקומי בריצה אוטונומית לאחר אישור יחיד, תוך שמירת tests, evidence, ביקורת, security, rollback ו־scope.

## 2. מפת הקמפיין

| Workstream | תוצר | Gate אוטומטי |
|---|---|---|
| WS0 | יישור OpenRouter/DeepSeek, board ו־state | probes + tests + graph |
| WS1 | סגירת PLAN-002/PLAN-002RF | parser/evaluator/contracts evidence |
| WS2 | PLAN-003 Geometry Compiler | topology/dimensions/overlay review |
| WS3 | Camera Planner | coverage/visibility/collision/extrinsics |
| WS4 | Rendering/Depth | RGB/depth/extrinsics/determinism |
| WS5 | Style Understanding | style contract/provenance/metrics |
| WS6 | Local Source Panorama | local/mock artifact + QA; no remote generation |
| WS7 | Package Integration | schema/validator/round-trip |
| WS8 | Local End-to-End QA | consistency/security/resource/rollback |
| WS9 | Dashboard | local monitoring and conceptual labels |
| WS10 | Hardening | adversarial, migration, observability |
| WS11 | Part 1 Acceptance | full audit, handoff, report |

## 3. Dependency graph

```text
WS0 → WS1 → WS2 → WS3 → WS4 → WS5 → WS6 → WS7 → WS8 → WS9 → WS10 → WS11
```

אפשר fan-out רק לתת־משימות עצמאיות בתוך WS. successor Workstream מתחיל אוטומטית לאחר Gate ירוק.

## 4. תבנית כל Workstream

```text
PREFLIGHT
→ PLAN (Pro)
→ PLAN REVIEW (new Pro session)
→ IMPLEMENT (Pro, TDD)
→ TARGETED TESTS
→ FULL RELEVANT SUITE
→ ARTIFACT/METRIC INSPECTION
→ SECURITY/CONTRACT REVIEW
→ INDEPENDENT-SESSION REVIEW
→ REWORK if needed
→ FRESH VERIFY
→ CHECKPOINT + LOCAL MERGE
→ AUTOMATED GATE
→ NEXT WS
```

## 5. WS0 — יישור תשתית

### Inputs

- OpenRouter key ב־secret store.
- pinned model IDs.
- מסמכים 06 ו־08–10.
- board `panoworld-dev`.

### Pass conditions

- Pro/Flash chat ו־identity probes עברו.
- Pro tool calling עבר.
- JSON object עבר.
- Hermes CLI probe עבר.
- full pytest עבר.
- Git/worktrees/board נקיים או reconciled.
- כל כרטיסי Omni הישנים עודכנו/הוחלפו.
- תקציב ו־privacy boundary נרשמו.

## 6. WS1 — PLAN-002/PLAN-002RF

- סגירת WP0–WP6 כ־subgraph של WS1, לא סוף הקמפיין.
- החלטות פתוחות מקבלות default בטוח ומתועד.
- Product A/B routes נשארים default-off עד acceptance.
- visual gate היסטורי נבחן מחדש באמצעות metrics ו־Pro reviewer; אין המתנה למשה.
- Gate: tests, evaluator, rights, contracts, security, overlays ו־review ירוקים.

## 7. WS2 — Geometry Compiler / PLAN-003

- Pro/`MAX` לתכנון ו־review.
- closed topology, dimensions, wall/opening semantics, transforms ו־determinism.
- unit/property/adversarial tests.
- top-down overlay ו־3D preview נשמרים כ־evidence.
- Gate אוטומטי: metrics + no Critical/Major + reviewer approval.

## 8. WS3 — Cameras

- viewpoints, coverage, collision avoidance ו־extrinsics.
- property tests על coordinate conventions.
- visual coverage artifacts.
- Gate: coverage threshold, zero collision, valid transforms ו־review.

## 9. WS4 — Rendering/Depth

- Blender/BlenderProc integration מקומי כאשר ניתן ללא remote/GPU inference.
- RGB/depth/extrinsics contracts.
- deterministic smoke fixtures.
- Gate: formats, dimensions, depth semantics, reproducibility ו־review.

## 10. WS5 — Style

- style_spec contract, provenance ו־unsupported behavior.
- local extraction/fixtures בלבד.
- Gate: schema, deterministic evidence, metrics ו־review.

## 11. WS6 — Source Panorama מקומי

- mock/local preparation בלבד; אין שירות generation מרוחק ללא scope חדש.
- artifact validity, equirectangular geometry ו־style consistency checks.
- Gate: local artifact contract ו־QA; quality target שאינו זמין מקומית מסומן deferred ולא מזויף.

## 12. WS7 — Package Integration

- map JSON, viewpoints, depth, extrinsics ו־manifest.
- validator, compatibility, round-trip ו־hash binding.
- Gate: package validator ירוק ו־historical compatibility.

## 13. WS8 — End-to-End QA

- pipeline מקומי מלא מהקלט עד package.
- adversarial/security/resource/cancellation/rollback.
- consistency בין geometry, cameras, render ו־style.
- Gate: suites מלאים, no Critical/Major, evidence מלא.

## 14. WS9 — Dashboard

- local monitoring, runs, evidence, costs ו־conceptual disclaimer.
- no production deployment.
- Gate: functional/accessibility/security tests ו־review.

## 15. WS10 — Hardening

- malformed inputs, path containment, reparse protection, resource caps.
- migration/versioning/rollback rehearsal.
- observability ו־incident instructions.
- Gate: adversarial suite ו־rollback rehearsal ירוקים.

## 16. WS11 — Part 1 Acceptance

- full fresh pytest.
- verify all requirements and gates.
- reconcile Git, state, board, evidence and handoffs.
- ensure H200/GPU/cloud/G7/G8 deferred.
- produce final acceptance report.
- local merge/checkpoint allowed; push only if separately permitted by repository policy.

Final status:

- `PART1_LOCAL_ACCEPTED_AUTONOMOUSLY`, או
- `PART1_BLOCKED_BY_CIRCUIT_BREAKER` עם next action יחיד וברור.

## 17. Default decision algorithm

```text
if reversible and within approved scope:
    choose safest deterministic compatible option
    record ADR + rationale + rollback
    continue
elif technical failure is allowlisted and retries < 3:
    recover from checkpoint
elif bounded rework can close evidence/test/review gap:
    create rework run and continue
else:
    trigger circuit breaker
```

## 18. Gate rubric

כל Gate דורש במצטבר:

- acceptance criteria `MET`.
- targeted/full relevant tests `PASS`.
- evidence hash-bound.
- reviewer session שונה מה־author.
- no unresolved Critical/Major.
- rollback point קיים.
- model identity מדויקת.

אין majority vote של מודלים ואין self-attestation.

## 19. דיווח

- עדכון מיידי במעבר Workstream, recovery או circuit breaker.
- heartbeat כל 15 דקות בזמן worker פעיל.
- דיווח על usage/cost מצטבר.
- המשתמש אינו נדרש לענות אלא אם circuit breaker הופעל.

## 20. גבולות קשיחים

- local-only Part 1.
- אין H200/GPU/cloud/remote או G7/G8.
- אין production deployment.
- אין נתוני לקוח רגישים ללא privacy approval.
- אין חריגה מתקציב OpenRouter.
- אין החלשת tests/thresholds.
- אין force-push/history rewrite/destructive cleanup.

## 21. Activation readiness

- [x] OpenRouter key מותקן מחוץ לריפו.
- [x] Pro chat/identity/reasoning עבר.
- [x] Flash chat/identity עבר.
- [x] JSON object עבר.
- [x] Hermes CLI Pro probe עבר.
- [ ] OpenRouter tool-call probe עבר.
- [ ] תקציב ו־privacy boundary אושרו.
- [ ] board הומר ל־Full Part 1.
- [ ] full preflight טרי עבר לאחר reconciliation.
- [ ] activation יחיד התקבל.

אין dispatch לפני שכל הסעיפים פתורים.
