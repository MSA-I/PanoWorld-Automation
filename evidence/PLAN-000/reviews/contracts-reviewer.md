# REVIEW — contracts-reviewer (PLAN-000 execution)

> נשמר verbatim ע"י ה-Orchestrator. ‏Reviewer: Anthropic Fable 5 (מודל שונה מהמחבר Opus 5). ‏Verdict: ‏NEEDS_REWORK — ‏3 MAJOR + ‏8 MINOR, ללא CRITICAL. **כל ה-MAJOR והמינורים המעשיים תוקנו באותו סשן** (ראו acceptance.md §Review record); ‏MINOR-11 (blocker schema) נרשם כ-residual מוצהר.

---

AGENT: contracts-reviewer
ACTUAL_MODEL: claude-fable-5 (Fable 5), as declared by the runtime environment
VERDICT: **NEEDS_REWORK** — no CRITICAL findings and the architecture is sound; the rework is 3 targeted MAJOR fixes (a hashing-definition paragraph, a vocabulary-enforcement decision, an evidence-vocabulary cleanup), not a redesign. Everything else is MINOR.

FINDINGS:

**MAJOR-1 — `content_hash` scope and canonicalization are undefined; self-reference is unresolved.**
Evidence: `schemas\envelope\v1\envelope-1.0.0.schema.json` line 38 (only a format pattern), line 5 ("integrity hash" — no scope); `schemas\README.md` line 13 ("Hashes are always sha256:<64 hex>" — nothing more); `contracts\state_machine.yaml` line 83 (invariant: approval "bound to the exact content_hash approved"); `schemas\approval_record\...` line 19 (`target_content_hash`); envelope `inputs[].content_hash` lines 26-37. Nowhere is it defined WHAT is hashed (whole document? then it includes `content_hash` itself — mathematically impossible; payload only? document minus `content_hash`?) or HOW it is canonicalized (key order, whitespace, UTF-8, float formatting). The provenance chain, the human-gate binding invariant, and AC4's "semantic equality" all rest on this mechanism, and `tests/unit/test_schemas_roundtrip.py` only checks the string format, never a computed hash. Two independent implementations today would produce incompatible chains. Fix is one normative paragraph in `schemas/README.md` + envelope `$comment` (e.g., "sha256 over canonical UTF-8 JSON of the document with the `content_hash` member removed; canonical form = ...") plus one test that computes it. Note the interaction: `schemas/README` must scope the map-file `sort_keys` prohibition vs. any envelope canonicalization that sorts keys.

**MAJOR-2 — Finding-7 vocabulary separation (AC5) is declarative only; the colliding tokens survive in data at rest.**
Evidence: `contracts\state_machine.yaml` lines 3-4 declare `"namespace": "RUN"` in prose, but the actual state strings `BLOCKED`, `REWORK`, `CANCELLED` (lines 16) are byte-identical to the doc 04 PLAN statuses (`docs\04-...md` lines 23, 25, 29), and `APPROVED` collides with nothing in doc 04 but `schemas\qa_report\...` line 38 re-uses the bare triple `["APPROVED","REWORK","BLOCKED"]` as `decision`. The researcher's warning was precisely that agents reading bare strings will mix the vocabularies; a `namespace` field inside one JSON file does not travel with the value into PROJECT-STATE.yaml, reports, or artifacts. `tests/unit/test_state_machine.py` never asserts anything about the namespace. AC5 claims finding 7 closed; it is partially closed. Fix: either prefix the four colliding states (`RUN_BLOCKED`...) or add a binding serialization rule ("any state value written outside state_machine.yaml MUST be written `RUN:<STATE>`") + align `qa_report.decision`, and add a test.

**MAJOR-3 — Gate evidence names without contracts, and a gated transition with zero required artifacts.**
Evidence: `contracts\state_machine.yaml` line 22 (`overlay_svg`), line 25 (`control_asset_validation`), line 28 (`package_validator_report`) — none of these are among the 13 schemas; the plan (§6 note, line 135) explicitly deferred `render_validation_report`/`source_panorama_candidates` because "אין להם consumer עדיין" — but the state machine now consumes them as gate evidence, recreating contract-researcher finding 4's exact complaint ("כל תוצר שהוא תנאי gate חייב חוזה"). Also line 42: the G4-gated transition has `"required_artifacts": []`, which satisfies invariant 1 only vacuously and contradicts doc 01's "no transition without artifact". The structural tests (test_state_machine.py) never validate evidence/required_artifact names against any vocabulary — a typo'd artifact name in a future edit would pass every test except the human-gate one. Fix: annotate non-schema evidence entries (e.g., `"contract": "deferred:PLAN-00X"` or move them out of `evidence`), give G4 a required artifact, and add a test that all artifact names ∈ {13 schema ids} ∪ declared-raw-evidence list.

**MINOR-4 — Structural test gaps beyond MAJOR-3.** `tests\unit\test_state_machine.py`: (a) no assertion that REWORK/BLOCKED/CANCELLED never appear in transition rows (`POLICY_STATES` discipline is implicit); (b) no single-outgoing-edge determinism check per state; (c) lines 50-51 verify the blocked/cancelled policies only via `startswith("any")` prose sniffing; (d) no check that `rework_policy` targets precede the failing stage in chain order (only membership in STATES, line 59-61); (e) line 49 is a near-tautology (`fail_targets | {"BLOCKED"}` always contains BLOCKED).

**MINOR-5 — `run_id` optional AND nullable everywhere.** `envelope` line 13: run-scoped artifacts (`run_manifest`, `remote_job`, `qa_report`) do not require `run_id` — a run_manifest with no run linkage validates. Also two encodings of "no run" (absent vs null) is a canonicalization hazard that feeds MAJOR-1. Fix: per-schema `"required": ["run_id"]` tightening in the run-scoped artifacts.

**MINOR-6 — `approval_record.gate_id` cannot represent cancellation.** `contracts\state_machine.yaml` lines 76-79: `cancelled_policy` requires "an approval_record or documented human decision", but `approval_record` (line 16) enumerates only G0-G9 — a cancellation record must borrow a gate id. Also the enum permits approval records for machine gates (harmless but unstated). Fix: add `"CANCEL"` to the enum or constrain to `{G2,G5a,G5b,G9,CANCEL}`.

**MINOR-7 — `retry_request.target_state` is a free string** (`retry_request` line 16, `minLength: 1` only), not tied to the state enum, although `rework_policy` (state_machine line 55) requires it to name "an explicit earlier state". Inline the states enum or note that the deterministic orchestrator enforces it.

**MINOR-8 — Two compat-recommended checks missing from the locked error vocabulary.** `evidence\SESSION-001\agent-reports\panoworld-compat.md` line 228 recommends warn on a viewpoint appearing twice across keys *within one map* (it would be regenerated) — no such code in `contracts\error_codes.md` (`DUPLICATE_MAP_KEY` covers duplicate keys only); line 237 recommends checking that `65535/scale` covers the scene's true max range (scale saturation/clipping) — `DEPTH_RANGE_IMPLAUSIBLE` does not cover saturation at 65535. The vocabulary is append-only so they can be added later, but locking now was the stated point of T8.

**MINOR-9 — Map filename convention hardcoded despite compat discrepancy 1.** `error_codes.md` line 11 (`NO_MAP_FILE`: "No `map*.json`") and `panoworld_manifest` line 24 (`^map[A-Za-z0-9_]*\.json$`) — panoworld-compat explicitly warned "Our validator must not hardcode the name" (the upstream contract is data-list-txt-driven; `viewpoints/` sibling is the only hard requirement). As a convention for OUR generated packages it is defensible, but it is nowhere declared as a deliberate narrowing; scene-only validation of a foreign scene with a differently named map errors incorrectly. Also the data-list txt relationship (compat implications, line 229) appears in no contract.

**MINOR-10 — `style_spec` silently answers open question 6.** `style_spec` payload has no reference-image linkage and no per-room styling (doc 01 line 83 "מספר תמונות סגנון לחדרים מסוגים שונים"; researcher OPEN_QUESTION 6 said cardinality undefined). v1 implicitly locks "one global style, no reference provenance in payload". Additive-MINOR fixable later, but the decision should be recorded (ADR-worthy sentence), not implicit.

**MINOR-11 — Machine-readable blocker record still missing.** `state_machine.yaml` line 72: `blocked_policy` requires "a blocker record (docs/04 format)" — which is the markdown template that finding 12 flagged as not machine-readable; rec 4 asked for a blocker schema. Not promised by the plan's 13, so this is a recorded residual, not a broken promise.

**Observations (no severity):** the envelope's partial/failed⇒errors conditional (lines 57-62) is correctly constructed and works; `status: "complete"` with a non-empty `errors` array is allowed and its semantics (warnings?) are undefined; `remote_job.telemetry` is an unconstrained object (borderline vs the no-ambiguous-fields rule, acceptable for telemetry); `checks[].result` is enum-constrained so it does not violate the ambiguous-field ban; error_codes test-case cross-references cover exactly cases 1-15 with no gaps; case 7 WARN, intra-map-only duplicates, VRAM warn-only, and the NTFS redefinition of case 12 all match the amended plan decisions precisely; contracts/README security principles 1-3 faithfully and fully capture critical findings 2-3 and finding 16, including the exact `remote_job` required-fields list matching the schema.

FINDINGS_COVERAGE_TABLE (contract-researcher finding/rec → closure):

| # | Closed by | Status |
|---|---|---|
| F1 (no fail edges) | state_machine.yaml transitions `on_fail` + rework_policy + blocked_policy | CLOSED |
| F4 (10th artifact + missing gate contracts) | input_quality_report schema exists; but overlay_svg / control_asset_validation / package_validator_report are gate evidence with no contract (MAJOR-3); candidates/render_validation deferred per plan | PARTIALLY CLOSED |
| F5 (approval record) | approval_record schema + target_content_hash + human-gate invariant + test | CLOSED (MINOR-6 nit) |
| F6 (G5 merge) | G5a/G5b split + STYLE_SPEC_APPROVED state | CLOSED |
| F7 (vocabulary collision) | `namespace: "RUN"` declaration only; tokens still collide, qa_report.decision reuses them | PARTIALLY CLOSED (MAJOR-2) |
| F8 (assumptions multi-writer) | assumptions schema: required `stage`, per-stage artifact, append-only comment | CLOSED |
| F9 (camera VRAM budget) | camera_plan resolution + max_views_per_lrm_batch(=8 verified) + VIEWPOINT_BUDGET_EXCEEDED(error) + VRAM_BUDGET_WARNING(warn) | CLOSED (note: budget fires in package validator, not at G3 time) |
| F12 (error/partial semantics + retry) | envelope status/errors + conditional + retry_request schema | CLOSED except machine-readable blocker (MINOR-11) |
| F13 (manifest vs map relation) | panoworld_manifest $comment: manifest = source of truth, ordered entries array, sort_keys ban in contracts/README | CLOSED |
| R1 (canonical transition table) | delivered (fail target via reason-prefix map rather than per-row) | CLOSED |
| R2 (envelope) | delivered; hash scope undefined | CLOSED except MAJOR-1 |
| R3 (versioning) | schemas/README + versioned $id + layout + contracts_bundle_version in both manifests | CLOSED |
| R4 (missing contracts) | 3 of 6 delivered; 2 deferred with justification; blocker schema absent | PARTIALLY CLOSED |
| R5 (vocab separation) | see F7 | PARTIALLY CLOSED |
| R9 (camera budget + cross-check) | fields + error codes delivered | CLOSED |
| R11 (manifest as source + round-trip) | contract relation declared; round-trip validator is future implementation | CLOSED (contract level) |
| R12 (assumptions per-stage) | assumptions schema | CLOSED |

EVIDENCE: files read (all absolute, under the repo root): contracts\state_machine.yaml, contracts\README.md, contracts\error_codes.md, schemas\README.md, schemas\envelope\v1\envelope-1.0.0.schema.json, all 13 artifact schemas under schemas\<name>\v1\, tests\unit\test_state_machine.py, tests\unit\test_schemas_roundtrip.py, docs\plans\PLAN-000-repository-bootstrap-and-contracts.md, docs\04-מתודיקת-ניהול-סוכנים-ומעקב.md, evidence\SESSION-001\agent-reports\contract-researcher.md, evidence\SESSION-001\agent-reports\panoworld-compat.md. Read-only review — no files were created or modified.
