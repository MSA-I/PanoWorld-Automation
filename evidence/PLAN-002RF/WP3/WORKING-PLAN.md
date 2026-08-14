# PLAN-002RF WP3 — Product A cad_exact — working plan

- Task: `t_aa5fb2fb`
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Parent: `t_0fc0a9e4` (WP2 — additive contracts + lifecycle) — DONE, evidence-bound.
- Status: executing under Moshe full-campaign authorization (2026-08-13).

## 1. Scope statement

WP3 implements and verifies **Product A (`cad_exact`)**: the exact, deterministic,
local-only CAD/DXF parsing pipeline for the approved geometry envelope. It is the
first recognizer in the WP0–WP6 chain and emits purely against the frozen WP2
contracts (`floorplan_parse` 1.2.0, `source_class = cad_exact`), the frozen WP1
evaluator (`src/pwa/evaluator/metrics.py`) and the FX1 frozen truth.

The existing `dxf` source class (PLAN-002 §12 path, `src/pwa/floorplan/dxf_source.py`
+ `dxf_worker.py`) deliberately REJECTS `ARC`/`SPLINE`/bulge geometry as
`PARSE_UNSUPPORTED_FEATURE`. Product A is a NEW additive pipeline that keeps that
historical path byte-compatible while adding a native `cad_exact` path that:

1. parses native arbitrary-angle LINE walls,
2. parses bounded circular arcs / bulges (native `ARC`, and `LWPOLYLINE` bulge),
3. computes exact quantized junctions / rooms / opening hosts,
4. carries sourced thickness metadata,
5. discriminates door / window / passage opening types (passage ≤ 3.0 m),
6. fails closed on scale / topology / resource / security refusals (same frozen
   finding codes + the frozen `RECOGNITION_*` blocking codes from WP2),
7. renders evidence (SVG overlay) for arcs/bulges, and
8. preserves migration compatibility (historical `dxf`/`annotation` output is
   byte-identical; `floorplan_parse` 1.0.0/1.1.0 consumers reject the new
   additive `cad_exact` output predictably via `contract_rejection_reason`).

### Hard boundary (unchanged)

Local-only; no H200/GPU/cloud/remote execution; no spend; no G7/G8; no Product C;
no PLAN-003; no route activation (routes remain default-off); no dependency
install; no push/merge-to-remote (local commits only).

## 2. Model & provider provenance (recorded, not inferred)

- Active runtime this session: `deepseek/deepseek-v4-pro-0813` via `openrouter`
  (`profiles/panoworld/config.yaml`), `fallback_providers: []`. Identity from
  runtime metadata, not prose.
- OmniRoute gateway `http://127.0.0.1:20128/v1` is reachable and used ONLY for the
  independent read-only review. Reported requested route `auto/best-coding`
  resolved to `felo/felo-chat` in WP2; WP3 re-probes at review time and records
  the actual provider/model from HTTP trailer headers (`x-omniroute-provider` /
  `x-omniroute-model`), never inferred.
- **Spatial/geometry gate:** WP3 produces NEW arc/bulge/thickness/junction geometry
  (novel geometry reasoning), so the Anthropic-Opus spatial review gate IS
  triggered. If an Opus-level route cannot be proven reachable via OmniRoute, apply
  the pre-approved fallback: record requested vs actual provider/model, reason,
  and impact; preserve the independent read-only review; never weaken thresholds.
  Failure to record a real provider/model identity → block (fail-closed).

## 3. Design

### 3.1 New module: `src/pwa/floorplan/cad_exact_source.py` (+ `cad_exact_worker.py`)

Convention-consistent with the existing `dxf_source.py` (subprocess worker boundary,
tree-kill on timeout, bounded result channel). The worker parses, in addition to
what `dxf_worker` already accepts:

- `PWA-WALL`: native `LINE` (arbitrary angle — already supported) AND bounded
  `ARC` (`center`, `radius`, `start_angle`, `end_angle`) → wall `kind: circular_arc`
  with `arc` sub-object; sourced `thickness_m` read from a `PWA-THICK`/`xdata`
  channel or a per-wall attribute, fail-closed `RECOGNITION_THICKNESS_MISSING`
  when absent.
- `PWA-ROOM`: `LWPOLYLINE` WITH bulge (bounded), tessellated per the FX1 sagitta
  rule (max_sagitta_px ≤ 0.5), area_m2 via centreline shoelace.
- `PWA-DOOR` / `PWA-WINDOW` / `PWA-PASSAGE`: opening `type` with `passage` span
  bound 3.0 m (`RECOGNITION_PASSAGE_SPAN_EXCEEDS_BOUND` fail-closed).

The raw geometry model is extended additively (new optional fields on `RawWall` /
`RawOpening`, or new dataclasses), so the historical `dxf`/`annotation` path is
untouched.

### 3.2 Emitter → `floorplan_parse` 1.2.0 with `source_class: cad_exact`

A new normalization+validation entry produces a `floorplan_parse` 1.2.0 artifact
whose payload declares `source_class: "cad_exact"`, carries wall `kind`/`arc`/
`thickness_m`, room `area_m2`, and opening `type` (door/window/passage), and whose
`producer` records the deterministic local author. Every output is validated
against the 1.2.0 schema and the frozen recognition invariants before emission.

### 3.3 Evaluation (accuracy 1.000/1.000)

Bind Product A output against the FX1 frozen truth using the frozen evaluator
(`canonical_key` / `match_wall` / `support_taxon_supported` / `per_plan_score`) —
NOT against any recognizer self-attestation. Accuracy, topology, determinism,
adversarial, resource and rollback gates are all exercised by fresh tests.

## 4. Implementation plan (TDD, RED→GREEN)

New files (RED then GREEN each):
- `src/pwa/floorplan/cad_exact_worker.py` — native arc/bulge/thickness/passage parse.
- `src/pwa/floorplan/cad_exact_source.py` — adapter + subprocess boundary.
- `src/pwa/floorplan/cad_exact_types.py` (or additive extension of `types.py`).
- `tests/unit/test_wp3_cad_exact.py` — the TDD suite.

No dependency is installed. No existing `schemas/`, `contracts/`, or historical
source file is edited except additive-only changes.

## 5. Acceptance (from task body)

- accuracy 1.000/1.000; topology, determinism, adversarial, resource, rollback gates
  all pass; otherwise the route stays disabled (routes are default-off and WP3
  activates nothing).
- migration / round-trip / negative / refusal / determinism tests pass RED→GREEN.
- independent cross-provider read-only review returns APPROVE or APPROVE_WITH_FIXES
  with all fixes closed (record actual provider/model from headers).
- routes default-off; no activation.

## 6. Evidence & handoff

- `evidence/PLAN-002RF/WP3/` — run report, targeted + full-suite logs,
  model-provenance.json, independent review, evidence-index.json bound to the
  exact checkpoint (generator `tools/make_wp3_evidence_index.py`), and
  `HANDOFF-WP3-to-WP4.md`.
- Git checkpoint on `main` (local commits only; no push).
- Closure does NOT authorize WP4 (`t_f2830a3e`) — it remains a human needs_input
  gate until Moshe explicitly approves continuation.
