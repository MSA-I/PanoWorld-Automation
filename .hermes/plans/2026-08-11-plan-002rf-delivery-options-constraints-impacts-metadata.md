# PLAN-002RF — delivery options, constraints, impacts, and provider metadata

- Date: 2026-08-11
- Kanban task: `t_1cac6675`
- Consumer: final assembly task `t_68bd94ab`, then approval task `t_301c6952`
- Status: **PLANNING ONLY — NOT AN IMPLEMENTATION OR SPEND AUTHORIZATION**
- Planning baseline: `.hermes/plans/2026-08-11-plan-002rf-final-bounded-recognition-remediation.md`
- Approval baseline: `.hermes/plans/2026-08-11-plan-002rf-approval-packet-for-moshe.md`
- Hard boundary: no production/code/contract/state changes, dependency installation, corpus acquisition, compute provisioning, merge/push, activation, H200/GPU/cloud/remote execution, G7/G8, or PLAN-003 work is authorized.

## 1. Executive delivery recommendation

Recommend **Option 2B: Product A + Product B-AUTO**, delivered through WP0–WP6 as default-off, Local-only, CPU-only, emit-or-fail-closed work. Product A deterministically parses the declared PWA CAD convention. Product B-AUTO processes only the approved raster envelope, with no human marking, drawing, correction, or per-plan tuning during a product run. Human work is restricted to rights approval, truth labels, adjudication, frozen-output QA, release acceptance, and incident decisions.

This is an estimate and a proposed decision envelope, not a commitment. Planning range: **16–26 elapsed weeks**, **700–1,200 engineering/QA hours**, **260–520 corpus/labeling/adjudication hours**, and **20–50 delegated frozen-output QA hours**. Approval and private-data waiting time, staffing contention, procurement, re-review after invalidation, and future scope expansion are excluded.

Incremental infrastructure spend is estimated at **USD 0 only conditionally**: the existing local workstation, locked Python environment, direct Pillow/NumPy path, and rights-cleared zero-cost corpus must prove sufficient. This is not a commitment. Any new dependency, paid data, vendor service, model, GPU, cloud, or remote execution requires a new approval packet before acquisition or use.

## 2. Options and consequences

| Option | Scope | Estimate | Dependencies | Consequence / decision impact |
|---|---|---|---|---|
| 1 — preserve current line-only baseline | Existing narrow baseline only | 1–2 weeks; 5–8 engineer-days | Current locked environment | Lowest change risk; does not close arc, thickness, or raster usability needs |
| 2A — Product A only | Automatic deterministic conforming CAD | 4–7 weeks; 180–300 engineering/QA h; 40–80 corpus/review h | ADR-0006, exact geometry contracts, CAD fixtures | Safest automatic claim; raster requirement remains unmet |
| **2B — A + B-AUTO (recommended)** | Automatic conforming CAD plus bounded automatic raster | **16–26 weeks; 700–1,200 engineering/QA h; 260–520 labeling/corpus/adjudication h; 20–50 delegated QA h** | All WP0–WP6 gates below | Meets the requested automatic CAD+raster product direction inside a narrow support envelope; highest technical and evaluation risk |
| 3 — broaden B-AUTO later | More raster styles/quality strata | Not estimated | New corpus, thresholds, rights, security/resource evidence | Separate scope approval; no manual fallback |
| C — arbitrary-raster research | OCR/learned or other general recognizer | Not estimated or authorized | New provider/model/data/license/compute/security plan | Outside Local-only Part 1; no universal-accuracy promise |

Option 2A is a **planning fallback**, not an in-run fallback and not an equivalent fulfillment of the raster requirement. Switching to 2A after a failed B-AUTO feasibility gate requires Moshe's explicit scope decision. A lower hour cap for Option 2B reduces supported styles, yield, or phase coverage; it may not introduce manual product operation or weaken accuracy/security gates.

## 3. Phased schedule, labor, dependencies, and decision gates

The phase ranges below total the Option 2B labor range. Calendar work may overlap only where evidence independence is preserved; the overall elapsed estimate remains 16–26 weeks.

| Phase | Planning range | Outputs and prerequisites | Stop/go gate | Failure consequence |
|---|---:|---|---|---|
| WP0 — decisions, ADR, feasibility design | 60–100 h; 2–3 weeks | Exact approved plan hash; D-0xx decisions; ADR-0006; target workstation; dependency/license inventory; hardest-clean-raster CPU spike protocol | Moshe approves scope/targets/resources; spike shows a plausible route to gates within 60 s and soft 1.5 GiB | Stop. Return with revised dependency/model/license/compute/hour options; no manual rescue |
| WP1 — corpus and evaluator lock | 80–140 h engineering plus 260–520 h corpus/labels/adjudication; 3–5 weeks | Rights owner; source-family splits; label guide; two independent labels; adjudicator; hidden locked truth; deterministic evaluator | Rights, independence, leakage, metrics, and corpus manifests independently reviewed | B-AUTO accuracy is non-evaluable; no accuracy claim or activation |
| WP2 — additive contracts/lifecycle | 80–140 h; 2–3 weeks | New exact versions; `authorship`, `source_class`, native line/arc semantics, `passage`, review lineage, conditional G1 artifact, append-only codes | Historical byte round trips; old/new compatibility; immutable lineage/head tests | Keep baseline; new routes remain unavailable |
| WP3 — Product A | 120–200 h; 3–4 weeks | Conforming CAD parser and exact 1.000/1.000 evidence | All A geometry, determinism, migration, adversarial, and resource gates pass | Disable A route; baseline remains default |
| WP4 — B-AUTO clean raster | 180–300 h; 4–6 weeks | Fixed automatic stages for clean supported raster; emit/fail-closed only | Clean stratum reaches ≥95% emit yield and all per-plan/aggregate accuracy, topology, scale, determinism, and zero-observed-critical-FP gates | Stop B-AUTO or revise scope through approval; no product correction flow |
| WP5 — supported scans, shadow, rollback | 140–240 h; 3–5 weeks | Scan hardening; local shadow; security/cancellation/resource/rollback/migration drills; 20–50 h delegated QA | Scan stratum reaches ≥85% emit yield; all machine+QA gates; no unresolved critical/major review finding | Disable B-AUTO, preserve evidence, return to baseline or approved A-only scope |
| WP6 — bounded activation decision | 40–80 h; ~1 week | Named local-run scope, evidence index, incident owners, rollback authority, independent review | Separate Moshe activation approval; exact versions and evidence hashes recorded | Remain default-off/shadow-only |

No phase begins because this memo exists. Each implementation package must be separately tracked and approved. Approval waiting, corpus access delay, and re-review are not hidden inside the estimates.

## 4. Staffing and operational dependencies

Required roles may be held by the same person only where independence is not compromised:

1. decision owner: Moshe for scope, thresholds, rights, caps, and later activation;
2. engineering owner familiar with Python 3.11, exact-version contracts, geometry, Windows process isolation, and repository lifecycle;
3. corpus rights owner responsible for provenance, license, non-sensitivity, and local retention;
4. two independent truth labelers per locked plan, blind to automatic output;
5. independent adjudicator, blind to the automatic output until truth is frozen;
6. pre-named QA delegate reviewing all 100 frozen comparisons without editing output; no personal Moshe review is required;
7. independent opposite-provider planning/review role where the gate requires it;
8. incident/rollback authority able to disable routes and preserve immutable evidence.

If label/adjudication separation cannot be staffed, B-AUTO is non-evaluable. If the QA delegate is unavailable, release evidence is incomplete. If opposite-provider review is unavailable or silently substituted, the applicable review gate blocks.

## 5. Compute and dependency envelope

### 5.1 Selected execution stack

- Hosting/locality: the named local Windows workstation; loopback-only UI; killable local child processes.
- Runtime: Python `==3.11.*` under `uv`; exact interpreter patch and OS build must be captured in `environment.json` at evidence time.
- Lock-source versions currently recorded: `ezdxf==1.4.4`, `jsonschema==4.26.0`, `numpy==2.4.6`, `Pillow==12.3.0`, `pypdfium2==5.12.1`.
- Recognition/evidence method: deterministic project code using NumPy/Pillow operations for thresholding, connected components, line/arc voting, paired edges, bounded symbol templates, topology search/face derivation, CVD transforms, SVG, and direct PNG generation.
- AI/model dependency: **none selected for product execution**. No OCR, learned model, weights, inference API, browser service, network service, GPU, or cloud fallback is selected.
- Input/data handling: verified immutable local snapshots only; EXIF/comments/GPS/author metadata stripped from rendered evidence after conversion to declared sRGB; private Layer B remains local and untracked; no pipeline upload, telemetry, cloud backup, model call, or network corpus retrieval.

### 5.2 Resource limits

Preserve existing caps: 50 MiB source; 200,000 DXF entities; 5 MiB annotation; 20,000/5,000/20,000 walls/rooms/openings; 10,000 vertices; 100,000 m coordinate magnitude; 100 MP decoded raster; 70 MiB overlay; 1 MiB worker output; 30 s DXF-worker time.

Proposed approval-required additions: 32,768 px maximum side, 60 s whole local run, and 1.5 GiB soft observed working-set target. Windows has no claimed portable hard-RSS sandbox. There is no child spawn, network access, automatic limit relaxation, or in-run retry. A retry receives a fresh immutable run ID.

### 5.3 Feasibility trigger

WP0 must test the hardest clean-raster stratum before architecture lock. If direct NumPy/Pillow cannot plausibly meet the approved accuracy, emit-yield, determinism, 60 s, and soft-memory gates, the authorized action is **stop and return for decision**. It is not permissible to install a package, use a remote model, provision compute, send data externally, weaken gates, or insert a human correction step.

## 6. Complete product-path provider/model/fallback metadata

| Product path | Provider / model identifier | Version | Hosting/locality | Data handling | Fallback order and trigger | Capability limits / unknowns |
|---|---|---|---|---|---|---|
| Option 1 baseline | No AI provider/model. Project-owned deterministic Python pipeline | Exact package/runtime versions must be environment-pinned | Local Windows workstation | Local verified snapshots; no upload/model call | No in-run fallback. Operational rollback target is this baseline | Does not provide required arcs/thickness/raster automation |
| Option 2A Product A | No AI provider/model. `ezdxf` + project deterministic geometry | Current lock includes `ezdxf==1.4.4`; final exact environment chosen at WP0 | Local CPU/Windows | CAD bytes remain local; external refs never resolved | Unsupported/ambiguous CAD fails closed. Strategic fallback to baseline on route disable | Only declared PWA CAD convention; no arbitrary CAD inference; final schema/bundle versions unknown until WP0 |
| Option 2B Product B-AUTO | No AI provider/model. Project-owned deterministic NumPy/Pillow algorithms | Current lock includes `numpy==2.4.6`, `Pillow==12.3.0`; algorithm/config versions must be newly assigned and pinned | Local CPU/Windows; loopback-only UI; child worker | Raster/PDF-page snapshots and private evidence remain local/untracked; no network/model call | Stage failure → fail closed. Resource/security/integrity trigger → disable B-AUTO and return to baseline. WP0 infeasibility → explicit decision between narrower B-AUTO, 2A, or a new plan | Narrow orthographic/high-contrast envelope; no OCR/learned semantics; CPU accuracy/yield/runtime feasibility unknown until spike; no portable hard RSS |
| Option 3 broader B-AUTO | **No provider/model selected** | Unknown | Must remain local unless a future packet changes the boundary | Unknown pending new rights/privacy review; no data transfer authorized | No fallback defined; unsupported styles fail closed under current plan | Corpus, algorithms, dependencies, schedule, licenses, thresholds, and compute are all unapproved/unknown |
| Product C research | **No provider, model, version, host, endpoint, or vendor selected** | Unknown | None authorized; GPU/H200/cloud/remote prohibited in Part 1 | No upload/retention/training/data-transfer terms approved | No fallback chain authorized. Any future route requires explicit ordered providers, trigger conditions, and no-silent-substitution rule | Training data, OCR/model stack, licenses, cost, latency, accuracy, OOD refusal, security, retention, and compute unknown; unestimated |

For Option 2B, “fallback” never means silently producing geometry through a weaker algorithm, a human correction path, or a remote provider. Product runs either emit conforming machine-generated geometry after every invariant or fail closed. Rollback and scope change are external, explicit decisions.

## 7. Planning/review provider metadata

This table records providers used to create/review the planning evidence. These services are not proposed product-runtime dependencies.

| Work | Provider/model | Hosting/locality and data handling | Fallback | Known runtime/version metadata | Unknowns |
|---|---|---|---|---|---|
| early geometry synthesis | Anthropic first-party via Claude Code; requested `opus`, actual `claude-opus-5` | Provider-hosted remote inference; repository excerpts processed in session; no production corpus use recorded | None observed | session `e89cd83c-215a-430e-a058-664d64724fae`; high effort requested; one-turn synthesis reported elsewhere | Model build/version beyond canonical ID, retention/training terms, region, and full runtime unavailable |
| critical geometry memo | Anthropic first-party via Claude Code; requested `opus`, actual `claude-opus-5` | Provider-hosted remote inference; planning/repository text only | None observed | session `81405d64-8518-4e5d-b1ec-ac134c9e59d4`; `computer-vision-expert`; detailed runtime unavailable | Same provider-policy/version unknowns |
| evaluation memo | OpenAI Codex `gpt-5.6-sol` | Provider-hosted remote inference through Hermes; local files read into planning context; no production corpus use recorded | None observed | active/default route; runtime/cost not exposed | Canonical build, retention/training terms, region, configured fallback chain unavailable |
| operations memo | OpenAI Codex `gpt-5.6-sol` | Same as above | None observed | task `t_1d699970`; runtime/cost not exposed | Same unknowns |
| PLAN-002R synthesis | OpenAI Codex `gpt-5.6-sol` | Same as above | None observed | task `t_e50c0bd4`; runtime/cost not exposed | Same unknowns |
| independent review | Anthropic first-party via Claude Code; requested `opus`, actual `claude-opus-5` | Provider-hosted remote inference; exact plan and repository contract excerpts reviewed; read-only conduct | None observed | session `53971edf-2b1e-48b8-86a9-3f81040a5dbb`; plan mode; 833.342 s wall, 798.428 s API, 26 turns, 58,028 output tokens, USD 3.866225 reported; skills `computer-vision-expert`, `advanced-evaluation`, `threat-modeling-expert` | Effort field, build beyond canonical ID, provider retention/training terms, and region unavailable |
| initial/final packet revisions | OpenAI Codex `gpt-5.6-sol` | Provider-hosted remote inference through Hermes; planning files only | None observed at authoring | Kanban runs 34–35; Hermes `kanban-worker`, plus `plan` in revision | Runtime/cost/build/provider-policy metadata unavailable |
| this delivery memo | OpenAI Codex `gpt-5.6-sol` | Provider-hosted remote inference through Hermes; local planning/contract files supplied as context; no production corpus, credentials, or intentional secrets | None observed at authoring | task `t_1cac6675`; Hermes `kanban-worker`; exact runtime/cost not exposed | Configured fallback order, retention/training terms, region, and model build beyond ID unavailable |

Required metadata rule for future planning/review/implementation sessions: record provider, requested model, actual model, model/version identifier, hosting/locality, data classes exposed, retention/training policy reference, effort, runtime/token/cost when exposed, selected skills, fallback order, actual fallback and reason, and independent reviewer provider/model. Unknown fields must be marked unknown; they may not be inferred. A required provider mismatch, unavailable opposite-provider reviewer, or silent substitution blocks the gate.

## 8. Security and privacy constraints

1. Local-only product execution: no upload, telemetry, remote model call, cloud backup, pipeline network retrieval, or external-reference resolution.
2. Loopback-only UI with exact Host/Origin validation, unguessable per-launch URL secret, SameSite=Strict/HttpOnly cookies, CSRF, `Cache-Control: no-store`, permission-restricted drafts, no directory listing, and no arbitrary paths.
3. Full ancestor-chain traversal/symlink/junction/reparse checks; immutable source snapshot and hash before decode/parse.
4. Child-process isolation, bounded output, timeout/cancellation checkpoints, verified process-tree termination, no child spawn, and atomic non-finalization on kill.
5. Private source/evidence is local and untracked. Git may contain only approved redacted hashes/counts/metrics/verdicts.
6. Corpus acquisition is out-of-band, human-performed, rights-approved, and not executed by product/evaluator code.
7. Canonical deterministic artifacts exclude timestamp, duration, hostname, PID, username, and absolute path; nondeterministic facts live in bounded local operational logs.
8. Required adversarial evidence includes non-loopback/Host/Origin rejection, CSRF replay, cookie/cache headers, traversal/reparse escape, unauthenticated access, decompression bombs, limit boundaries, kill-tree behavior, and kill during atomic finalization.

## 9. Migration impacts

Migration is additive and applies to new runs only. It requires exact-version carriers for product authorship (`cad_exact`/`raster_auto`), source class, native line/arc geometry, sourced thickness, room area basis, `passage`, append-only recognition diagnostics, immutable `floorplan_review` lineage, conditional raster G1 evidence, and new blocking topology codes.

Impacts and obligations:

- ADR-0006 must explicitly supersede ADR-0004's geometry envelope and dataset-context clause; ADR-0004 remains published.
- Historical schemas, manifests, runs, and evidence remain byte-identical and are not relabeled.
- Old consumers predictably reject unknown new exact versions; new consumers prove historical round trips and support the approved version matrix.
- G1 remains machine-labelled (`human: false`); human QA is evaluation/release evidence, not product-run input.
- B-AUTO remains shadow-only until contract, evaluator, corpus, security/resource, migration, and independent-review gates pass.
- `scene_geometry`, wall/opening heights, camera, 3D semantics, and PLAN-003 remain untouched.
- Schema/catalog/bundle/error-code selection is unknown until a live WP0 catalog review; no version is guessed here.

## 10. Rollback and incident impact

Default remains the existing baseline. New routes are default-off and named per run. Rollback order:

1. disable the affected route at registry/config boundary and stop new runs;
2. cancel active workers and verify process-tree termination;
3. preserve all finalized immutable artifacts and approval lineage;
4. quarantine bounded staging and local operational logs without private-content leakage;
5. reproduce on synthetic/minimized data and classify contract, implementation, data, or environment cause;
6. revert unpublished runtime activation/code, or deprecate published additive versions without deleting history;
7. rerun baseline, adversarial, migration, determinism, and environment-pinning checks;
8. require independent review and the applicable Moshe gate before re-enable.

Immediate disable triggers: path/external-access failure, disclosure, finalized mutation, unkillable process tree, nondeterminism, wrong schema/G1 routing, resource-control bypass, critical false opening, changed bound input without lineage invalidation, or material threshold regression. Rollback does not auto-delete history, relabel evidence, weaken a gate, retry inside the same run, or route to human correction.

Incident classes: SEV-1 for containment/disclosure/finalized-mutation/unkillable-worker failures; SEV-2 for determinism, contract routing, G1 eligibility, resource-control bypass, or critical false opening; SEV-3 for bounded malformed-input/performance defects without integrity impact.

## 11. Evidence required before any commitment or activation

### WP0/architecture evidence

- exact plan/packet hash and approved D-0xx/ADR-0006 decisions;
- target-workstation CPU/RAM/OS/Python and lock hash;
- license/offline-installability inventory and rights owner;
- hardest-clean-raster feasibility protocol and results;
- measured wall time and peak observed working set;
- explicit stop recommendation if gates are not plausible.

### Corpus/evaluation evidence

- source-family provenance/license/rights/non-sensitivity records;
- family-isolated development/regression/locked splits and collision checks;
- two blinded labels, independent adjudication, identity/separation attestations;
- frozen automatic output before truth opening;
- chain-level canonical matching, per-plan floors, macro/micro/slice results;
- exact one-sided 95% `3/n` bound by stratum when zero critical FPs are observed.

### Per-plan release evidence

Eight separately hash-bound views/records: sanitized source; adjudicated truth; automatic accepted geometry; source+geometry; matched FP/FN/tolerance diff; topology/leak/junction view; machine metrics/findings; immutable QA disposition and lineage head. Deterministic SVG and PNG at 100%/200%/400%, environment fingerprint, pinned font hash, stripped PNG metadata, normalized-pixel hash, collision checks, and CVD contrast results are required.

### Operational evidence

- all security/resource/cancellation/adversarial cases pass;
- byte-identical canonical output and outcome in the pinned environment;
- baseline and historical-version compatibility pass;
- rollback rehearsal completes without history mutation;
- independent review has no unresolved critical/major finding;
- named local activation scope and incident/rollback authorities are approved.

Evidence is a prerequisite to a later commitment. The estimates here do not become dates, staffing assignments, accuracy claims, or budgets merely because the packet is approved.

## 12. Assumptions, unknowns, and required confirmations

### Assumptions behind estimates

- one engineer familiar with the repository plus access to the independent human roles above;
- current local workstation remains available and representative;
- Python 3.11 and currently locked libraries remain usable and licensable for distribution;
- no procurement or paid corpus is required;
- supported raster envelope remains narrow and does not add OCR/learned semantics;
- one bounded rework round per phase; no broad redesign;
- private inputs arrive on time with rights/non-sensitivity approval;
- no implementation begins before exact scope and acceptance approval.

### Unknowns that must remain explicit

- CPU-only accuracy, yield, 60-second runtime, and soft-memory feasibility before WP0 results;
- exact schema/catalog/bundle/error-code versions;
- actual staffing availability and label/adjudication throughput;
- corpus source list, licenses, and acquisition timing;
- target workstation benchmark variance;
- re-review hours after any invalidation;
- provider data-retention/training/region terms for planning AI sessions;
- any Product C provider/model/compute/data/security/cost details;
- committed start date, delivery date, and budget owner.

### Decision consequences

- Approve 2B: authorizes only later separately tracked planning/implementation cards inside the stated caps and gates; it starts no work.
- Change to 2A: reduces technical/evaluation risk but explicitly leaves raster automation unmet.
- Lower cap: requires narrower support/yield/phase coverage and a revised estimate; gates and automatic-only operation remain fixed.
- Reject resource/security residuals: B-AUTO cannot proceed under the current Windows/local design.
- Reject human evidence obligations: B-AUTO has no valid accuracy/release claim.
- Require broader rasters or learned models: return with a new Product 3/C rights/model/provider/compute/security packet; do not stretch Option 2B.

# HANDOFF STATUS — planning material complete; no implementation, provisioning, spend, activation, or PLAN-003 work authorized
