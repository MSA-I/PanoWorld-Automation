# PLAN-002 — Floorplan-recognition remediation: security, delivery, rollback, and contract-migration memo

- Status: **PLANNING ONLY — NOT APPROVED FOR IMPLEMENTATION**
- Scope: bounded, local-only Part 1 remediation planning
- Authority consulted: `PLAN-002-floorplan-parsing.md`, ADR-0004, ADR-0005, the versioned schemas, `contracts/state_machine.yaml`, `contracts/error_codes.md`, and the current implementation limits
- Hard boundary: Part 1 contains no H200, GPU, cloud, remote execution, G7, G8, network provisioning, purchase, or spend. Those remain a separate later research decision.
- Change control: this memo changes no code, schema, contract, infrastructure, activation state, or committed schedule.

## 1. Executive recommendation

Keep the current narrow DXF adapter and schema-validated manual raster annotation as the only canonical Part 1 producers. If product value requires recognition assistance, prefer a **local draft-assist path** that proposes a `floorplan_annotation` document for human correction and then enters the existing deterministic validator. Do not let an uncalibrated recognizer directly claim `floorplan_parse.status=complete`, invent `source_kind=annotation`, or advance G1.

This recommendation minimizes migration risk: existing annotation, normalization, geometry, opening, overlay, immutable-run, and exact-version validation contracts remain authoritative. A direct automatic recognizer is a separate product choice requiring a new versioned provenance contract, labeled evaluation data, and explicit Moshe approval.

## 2. Supported product choices and planning estimates

The estimates below are option ranges, not schedule changes or authorizations. They assume one engineer familiar with the repository, the current Python 3.11 dependency set, synthetic fixtures, and no procurement. Calendar ranges include review and one bounded rework round but exclude time waiting for human approval or private-data availability.

| Choice | Product behavior | Contract impact | Engineering estimate | Calendar estimate | Incremental infrastructure spend |
|---|---|---|---:|---:|---:|
| **A — Harden current baseline** | Narrow DXF plus manual raster annotation only | None if limits and behavior stay unchanged; operational policy/evidence only | 5–8 engineer-days | 1–2 weeks | USD 0 |
| **B — Local draft assist (recommended if recognition is needed)** | A local CPU process proposes annotation; a human reviews/corrects it; only the validated annotation enters the canonical parser | Prefer no canonical-output change. A draft format may remain explicitly non-canonical or receive its own later schema | 15–25 engineer-days, plus labeling/review time | 3–5 weeks | USD 0 infrastructure; ordinary workstation time only |
| **C — Local automatic canonical recognizer** | A local recognizer emits canonical geometry without mandatory correction | New exact-version contract, provenance token/shape, confidence calibration, evaluation gate, and migration work required | 30–50 engineer-days, plus labeled dataset work | 6–10 weeks | USD 0 infrastructure, but CPU feasibility and accuracy are unproven |

Choice A is the lowest-risk closure. Choice B is the preferred recognition remediation because it preserves the existing deterministic trust boundary. Choice C must not be described as a small adapter addition: `floorplan_parse` 1.1.0 only permits `provenance.source_kind` values `dxf` and `annotation`, and schema validity alone does not establish production accuracy.

A later GPU/cloud investigation, if Moshe opens it, should be a separate research plan with a 5–10 engineer-day comparison/spike budget before any implementation estimate. Vendor usage cost is intentionally **unpriced here**: no provider, model, workload, data policy, retention policy, or approval exists, so quoting a spend would be false precision. That later plan must not activate G7/G8 or rent hardware without an explicit budget and approval.

## 3. Trust boundaries and accepted inputs

### 3.1 Fail-closed allowlist

Part 1 accepts exactly these parser inputs after immutable source-run preflight:

1. DXF following the approved `PWA-WALL`, `PWA-ROOM`, `PWA-DOOR`, and `PWA-WINDOW` convention.
2. A `floorplan_annotation` 1.0.0 JSON document bound to either:
   - one manifest entry of `kind=floorplan` that decodes as PNG or JPEG; or
   - one intake-produced `kind=floorplan_page` entry that decodes as PNG.

Raw PDF, DWG entity content, TIFF, SVG, archive files, CAD previews, style references, generic derivatives, embedded files, and unknown formats fail closed with a stable code and no fallback adapter. File extensions are routing hints only; accepted raster type and dimensions must come from decoded bytes, and hashes must bind the immutable original bytes.

### 3.2 Source-run preflight

Before parsing or recognition work:

- require a finalized direct child of the configured `runs_root`, never `.staging`;
- reject traversal, drive-relative/absolute paths, symlinks, junctions, and reparse points over the full ancestor chain;
- exact-version validate source manifest and quality report and recompute their `content_hash` values;
- require one unique `kind=floorplan`, unique inventory path strings, a complete quality report, and no blockers;
- snapshot, copy, and hash every consumed input once; downstream decoding and overlay creation use that verified snapshot rather than reopening a mutable source path;
- never resolve XREF, IMAGE, OLE, external href, embedded attachment, or network location.

Any unsupported or ambiguous input, invalid source contract, hash mismatch, failed snapshot, or unsafe path is an operational failure: CLI 2, no finalized derived run, bounded staging at most.

## 4. Malicious, malformed, and decompression handling

### 4.1 DXF

- Check the 50 MiB cap before worker launch.
- Parse in a child process with no child-spawn permission, bounded stdout/stderr files, a 1 MiB capture cap, a 30-second timeout, and verified process-tree termination on timeout or cancellation.
- Treat worker output as untrusted: require bounded size, valid UTF-8/JSON, an object root, and the expected closed shape before use.
- Enforce the 200,000-entity limit cumulatively across modelspace and all layouts; enforce wall/room/opening and polygon-vertex caps before expensive geometry loops.
- Unsupported entities are never expanded or resolved. Known unsupported semantics fail after a bounded scan; unknown layers may only produce the already-defined warning and ignored-entity behavior.
- Do not claim the entity cap protects the DXF library's initial load. The byte cap, child-process boundary, timeout, and kill-tree behavior are the pre-load protections.

### 4.2 Raster and intake-produced page PNG

- Accept only decoded PNG/JPEG for `kind=floorplan` and decoded PNG for `kind=floorplan_page`.
- Enforce source bytes ≤50 MiB and decoded pixels ≤100,000,000 before materialization or base64 work wherever the decoder permits.
- Convert Pillow decompression-bomb warnings to rejection and catch both warning/error forms at the operational boundary. Truncated, malformed, unsupported-mode, overflow, recursive, or decoder-error inputs fail closed without stack traces.
- Decode dimensions fresh from the verified snapshot and require exact equality with annotation metadata. Do not trust manifest detail fields for decoded dimensions.
- The overlay embeds a deterministic sanitized image representation with EXIF, ICC, comments, GPS, author fields, and all other metadata omitted; its metadata binds the SHA-256 of the original verified bytes.
- Never pass raster metadata, file names, private paths, or free text into tracked artifacts.

### 4.3 PDF and archive/decompression boundary

The parser does not parse raw PDF and does not accept archives. PDF handling remains an intake responsibility: at most 20 pages are rendered, and the parser selects exactly one approved PNG page derivative. Nested archives, compressed CAD packages, and embedded PDF files are unsupported and must not be auto-expanded. A page-count breach or render/decode limit fails at intake, before recognition.

### 4.4 Limits requiring an explicit decision

Current limits bound total raster pixels but not the length of a single image side. Before a recognition component is approved, select and test a `MAX_RASTER_SIDE_PX` value; **32,768 px is the planning recommendation**, in addition to the existing 100-megapixel total cap. This is not active until Moshe approves it and an approved PLAN assigns the contract/error behavior.

## 5. Resource, cancellation, and deterministic execution budgets

### 5.1 Existing locked limits to preserve

| Budget | Current Part 1 value |
|---|---:|
| DXF input | 50 MiB |
| DXF entities | 200,000 |
| Annotation JSON | 5 MiB |
| Walls / rooms / openings | 20,000 / 5,000 / 20,000 |
| Vertices per polygon | 10,000 |
| Coordinate magnitude | 100,000 m |
| Raster input / decoded pixels | 50 MiB / 100,000,000 |
| Overlay | 70 MiB |
| Worker stdout/stderr | 1 MiB |
| DXF worker wall time | 30 seconds |

### 5.2 Proposed remediation budgets

The current Windows implementation truthfully has no portable hard RSS limit and no whole-run deadline. Do not claim otherwise. For a future remediation, the recommended acceptance target is:

- a 60-second whole-run wall-clock deadline for one local Part 1 parse, including overlay generation, while retaining the stricter 30-second DXF-worker deadline;
- a configurable soft working-set ceiling, with **1.5 GiB as the planning default**, enforced by pre-allocation byte/pixel/count checks and parent monitoring where available;
- process isolation for any recognition worker so timeout, cancellation, or memory breach can terminate its process tree;
- no retry inside one run; a retry uses a fresh parse-run ID;
- no automatic relaxation of a limit after failure.

The 60-second and 1.5-GiB values require Moshe approval and benchmark evidence on the target Windows workstation before becoming requirements.

### 5.3 Cancellation semantics

Cancellation is fail-closed and must be possible between preflight, snapshot/copy, extraction, normalization, validation, overlay, artifact validation, and finalization. The parent owns a cancellation token and checks it at stage boundaries and in bounded loops. Cancellation must:

1. stop launching new work;
2. terminate and verify termination of a worker process tree;
3. close decoder/file handles;
4. never publish a final run;
5. retain only bounded staging for diagnosis under the existing immutable-run policy; and
6. return a sanitized operational result.

Do not reuse `RUN:CANCELLED` or invent a `PARSE_CANCELLED` error code without a contract decision. Until such a decision, user cancellation remains an operational non-finalization event and is recorded only in operational audit metadata.

## 6. Privacy, retention, and audit metadata

### 6.1 Privacy rules

- Local-only means no network upload, telemetry export, remote model call, or cloud backup performed by the parser/recognizer.
- Source names, absolute/private paths, OS user names, client free text, EXIF, GPS, author metadata, and raw stack traces do not enter canonical or tracked evidence.
- Private Layer B data requires Moshe's prior rights/non-sensitivity attestation. Inputs and overlays remain untracked; Git receives only redacted hashes, counts, metrics, and verdicts.
- Logs use opaque run/artifact IDs and stable finding codes. Messages are not API contracts and must remain sanitized.

### 6.2 Retention classes

1. **Finalized runs:** immutable and retained according to project retention policy; never mutated or auto-deleted by rollback.
2. **Operational staging:** current contract retains stale staging for diagnosis and forbids silent deletion/resume. Remediation may report age/size, but automated expiry requires a revised approved policy.
3. **Synthetic Layer A evidence:** may be tracked indefinitely with its project-created provenance notice.
4. **Private Layer B material:** local and untracked. The recommended policy is explicit human deletion after an approved diagnostic window, with no content in Git or external logs.

Recommended future operational policy: notify at 24 hours for stale staging and require a named human purge decision at 7 days. This is advisory only because auto-deletion would conflict with the accepted current lifecycle.

### 6.3 Deterministic artifact metadata

Canonical parse artifacts and `parse-report.json` should continue to record only deterministic data:

- schema ID/version and contracts bundle;
- source and derived run/artifact IDs and cryptographic bindings;
- adapter/source kind and opaque source references;
- normalization parameters and limit snapshot;
- entity counts, findings, outcome, overlay binding or omission reason;
- canonical projection hash.

No timestamp, duration, machine name, absolute path, or process ID belongs in deterministic evidence.

### 6.4 Separate operational audit record

Observability needs nondeterministic facts, so keep them in a separate local operational log, not in canonical artifacts. Record:

- event timestamp in UTC, opaque run ID, stage name, and terminal status;
- provider/adapter implementation version and feature-flag snapshot;
- elapsed time, peak observed working set if available, bytes/pixels/entity counts, and cancellation/kill verification;
- stable finding code and sanitized message;
- retention action and human actor/approval reference, without source names or content.

Operational logs must be bounded, access-controlled, locally retained, and excluded from deterministic hashes and tracked private evidence.

## 7. Contract migration analysis

### 7.1 Raster annotation contract

`floorplan_annotation` 1.0.0 is a closed, data-only JSON envelope with exact image/hash/dimension/scale bindings and `additionalProperties:false`. Preserve it byte-for-byte for Choices A and B.

For draft assist, the recognizer may generate a candidate in memory or in a clearly non-canonical draft file. It becomes canonical annotation only after explicit human review and normal schema/hash validation. Do not add hidden confidence, model, or candidate fields to 1.0.0; they would be rejected and would blur authorship.

If draft provenance must be durable, create a separately named, exact-versioned draft/evidence contract in a later approved PLAN. Do not overload `floorplan_annotation`.

### 7.2 Recognition contract

There is no current canonical recognition contract. `floorplan_parse` 1.1.0 permits only `source_kind=dxf|annotation`; an automatic recognizer must not claim either token unless it actually consumed that approved source construct under the documented semantics.

Choice C therefore requires one of these approved migrations:

- **Recommended:** new `floorplan_recognition` evidence contract for candidates/uncertainty plus a promotion step into a new `floorplan_parse` version after validation; or
- new additive `floorplan_parse` version with a `recognition` provenance variant, producer/model identity, deterministic preprocessing identity, confidence-calibration version, and source-region geometry.

Use the existing exact-version catalog. Freeze 1.0.0/1.1.0, never relabel a document, never rewrite historical manifests, and bump the contracts bundle only for new runs after approval. A semantic change to existing geometry, ID, or G1 meaning requires a major version; a genuinely optional new provenance variant can be proposed as a minor version but still needs compatibility tests.

### 7.3 Geometry contract

Canonical output remains metres, y-up, quantized to `1e-4 m`, normalized by the wall-endpoint anchor, deterministically ordered, and content-addressed by stable IDs. A recognizer must pass the same cardinality, finite-value, coordinate-bound, polygon, duplicate, dimension, and ordering checks. It may not emit a different coordinate convention behind the same schema version.

`scene_geometry` 1.0.0 is downstream and adds 3D-facing requirements such as wall height/thickness and opening height/sill. Recognition remediation must not manufacture these values or silently alter that contract. PLAN-003 or another approved stage owns those decisions.

### 7.4 Opening contract

Current openings are only `door|window`, bind to exactly one wall, use a metric center and positive width, fit fully within the wall, and carry deterministic provenance. DXF width is projected onto the resolved wall direction; annotation width is explicitly supplied in metres.

A recognizer must not emit opening types, wall adjacency, room connectivity, heights, sills, swing direction, or inferred wall thickness under the current parse contract. Uncertain wall binding, type, center, or width fails promotion; it must remain a draft finding requiring correction.

### 7.5 Overlay contract

The canonical overlay remains source-aligned, self-contained, deterministic, sanitized, and bound to original source bytes. Recognition layers may be added only under a versioned/approved overlay policy with fixed ordering and labels; they must not replace or obscure source, canonical geometry, IDs, confidence, or legend layers.

Choice B should visualize draft candidates separately before promotion. A candidate overlay is not G1 evidence. Only the overlay regenerated from the accepted canonical annotation/parse can satisfy the existing gate.

### 7.6 Compatibility matrix

| Producer | Consumer behavior |
|---|---|
| Historical `floorplan_parse` 1.0.0 | Continue exact-version validation; no provenance/normalization claim |
| Current `floorplan_parse` 1.1.0 from DXF/annotation | Continue unchanged; runtime still requires PLAN-002 provenance and normalization |
| Draft recognition candidate | Never accepted as `floorplan_parse`; human review or explicit unsupported failure |
| Future recognition schema/version | Rejected by old consumers as unknown exact version; accepted only after catalog, bundle, consumer, and migration tests land together |
| Unsupported or ambiguous source | Fail closed; no fallback, no guessed geometry, no G1 transition |

Compatibility tests must prove historical byte round trips, exact-version selection, old-version rejection of new fields, new-consumer handling of both old and new versions, stable failure codes, unchanged canonical geometry for existing fixtures, and no mutation of finalized runs.

## 8. Isolation, rollout gates, and observability

### 8.1 Feature isolation

No partially remediated recognizer becomes the default. Use equivalent isolation at the adapter registry/CLI boundary:

- `baseline_only` — current DXF/manual annotation; default and rollback target;
- `draft_assist` — local candidate generation only; no automatic promotion;
- `recognition_canonical` — unavailable unless a later contract/evaluation PLAN explicitly enables it.

The exact flag/config syntax is an implementation decision. The requirements are default-off recognition, per-run recorded mode, no silent fallback, and the ability to disable the new path without deleting schemas or artifacts.

### 8.2 Rollout gates

| Gate | Exit criteria |
|---|---|
| **R0 — approval** | Moshe approves product choice, limits, cancellation semantics, retention policy, and exact contract clauses |
| **R1 — contracts** | Exact-version schemas/error behavior approved; historical fixtures byte-unchanged; migration matrix tests pass |
| **R2 — adversarial local verification** | Malformed DXF/JSON/raster, decompression bombs, page/byte/pixel/entity/vertex/output caps, traversal/reparse, timeout, cancellation, and kill-tree tests pass |
| **R3 — deterministic shadow** | Synthetic Layer A plus approved private Layer B shadow runs; no canonical publication; repeat hashes and redacted metrics agree |
| **R4 — bounded pilot** | Feature explicitly enabled for named local runs; human correction required; zero G1 advancement from draft-only output |
| **R5 — default eligibility** | Independent cross-provider review has no CRITICAL/MAJOR findings; Moshe accepts the visual/geometry evidence and product accuracy threshold |

A green unit suite alone is insufficient. Each gate requires the named evidence, negative tests, and a recorded reviewer/provider/model identity.

### 8.3 Observability and service objectives

For local Part 1, report by mode and stable outcome code:

- run counts by complete/partial/failed/operational/cancelled;
- p50/p95 wall time and peak observed memory;
- bytes, pixels, DXF entities, geometry counts, and overlay size;
- timeout, resource-limit, malformed-input, hash-mismatch, cancellation, and worker-termination counts;
- determinism mismatches on repeated synthetic runs;
- draft-assist acceptance/correction/rejection rates, measured only on labeled or reviewed data;
- stale staging count and total size.

Suggested pilot stop thresholds: any path escape, external read/network attempt, unverified worker termination, canonical determinism mismatch, finalized-run mutation, unsanitized private metadata, or G1 advancement from draft output triggers immediate disablement. Performance thresholds must be approved from benchmark evidence rather than guessed from one machine.

## 9. Rollback triggers and procedure

### 9.1 Immediate rollback triggers

- containment, symlink/reparse, arbitrary read/write, or external-reference resolution failure;
- hash/provenance mismatch or use of bytes other than the verified snapshot;
- decoder/worker escape, failed cancellation, or unverified process-tree termination;
- deterministic output mismatch for identical inputs;
- private metadata/path/source content in canonical or tracked evidence;
- historical schema/run mutation or consumer misvalidation;
- direct G1 advancement from partial, warning, draft, unsupported, or unapproved recognition output;
- material error-rate regression or resource use above an approved pilot budget.

### 9.2 Rollback procedure

1. Disable `draft_assist`/recognition at the registry/config boundary and return to `baseline_only`.
2. Stop accepting new affected runs; cancel active workers and verify process-tree termination.
3. Preserve finalized runs and published schema/error/ADR history. Do not delete, rewrite, or relabel them.
4. Quarantine affected staging and operational logs locally; record hashes, opaque run IDs, mode, and incident code without private content.
5. Reproduce with synthetic/minimized data, classify contract versus implementation failure, and assess whether any tracked evidence leaked private data.
6. Revert runtime activation or code before publication; after publication, deprecate superseded adapters/versions rather than deleting append-only history.
7. Re-run the full baseline, adversarial, exact-version, determinism, and migration suites.
8. Require independent review and the applicable Moshe gate before re-enabling the affected mode.

Rollback never auto-deletes source or parse runs and never relaxes a gate to restore throughput.

## 10. Incident handling

Severity guidance:

- **SEV-1:** path escape, external access, source disclosure, finalized-run mutation, or unkillable worker. Disable immediately, preserve bounded evidence, and notify Moshe.
- **SEV-2:** deterministic mismatch, contract/version misrouting, incorrect G1 eligibility, or repeatable resource-control bypass. Disable affected mode and block rollout.
- **SEV-3:** bounded malformed-input failure, performance regression, or non-sensitive operational-log defect with no integrity impact. Keep baseline available; fix before the next gate.

Every incident record should contain UTC times, opaque run IDs, affected mode/version, stable finding codes, impact, containment action, termination verification, retention decision, root cause, tests added, and re-enable approval. It must exclude raw client files, private paths, user names, secrets, EXIF, and stack traces. Security/integrity incidents cannot be auto-retried; a new run ID is required after remediation.

## 11. Decisions requiring Moshe's explicit approval

1. Product choice A, B, or C; recommendation: A unless recognition assistance is needed, then B.
2. Whether a draft-assist artifact needs a durable new schema or remains non-canonical local working data.
3. Any new `floorplan_parse` provenance variant/version and the exact G1 promotion semantics.
4. Proposed single-side raster limit (recommended 32,768 px), whole-run deadline (recommended 60 s), and soft memory target (recommended 1.5 GiB).
5. Cancellation vocabulary: operational-only versus a new append-only error/status contract.
6. Stale-staging/private Layer B retention and human purge policy; current lifecycle forbids silent auto-deletion.
7. Accuracy metrics, labeled dataset rights, minimum thresholds, and sample size for any recognition claim.
8. Any change to coordinate transforms, quantization/IDs, DXF convention, opening semantics, overlay security/alignment, source-hash behavior, or G1 eligibility.
9. Layer B rights/non-sensitivity attestation and later visual/geometry acceptance.
10. Any future GPU/cloud/H200/G7/G8 research plan, vendor access, data transfer, budget, or spend.
11. Activation beyond a named local pilot and any committed delivery date or staffing assignment.

Silence, acceptance of this memo, or approval of an earlier PLAN revision is not approval of these decisions. The approval request must name the exact memo/PLAN commit and changed clauses.

## 12. Provider, model, skills, and fallback record

This memo was prepared in the Hermes Kanban worker runtime:

- provider: `openai-codex`
- actual model ID: `gpt-5.6-sol`
- fallback observed: none
- task: `t_1d699970`
- Claude session used: no

Any future Claude planning, implementation, or review dispatch must explicitly instruct Claude to invoke `/skills` and select relevant skills before work. Its run report must record requested provider/model, actual provider/model from runtime metadata, effort/thinking setting, runtime/token/cost data when exposed, fallback provider/model, fallback reason, and reviewer provider/model. A provider/model mismatch or unavailable required cross-provider reviewer blocks the gate; no silent substitution is allowed.
