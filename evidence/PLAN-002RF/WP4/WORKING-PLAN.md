# PLAN-002RF WP4 — Product B-AUTO clean-raster engine — working plan

- Task: `t_f2830a3e`
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
  (verified this session: `sha256sum .hermes/plans/2026-08-11_220700-plan-002rf-final-remediation-approval-packet.md` matches)
- Parent: `t_aa5fb2fb` (WP3 — Product A cad_exact) — DONE, evidence-bound at `79ba20c`.
- Status: executing under Moshe full-campaign authorization (2026-08-13).

## 1. Scope statement

WP4 implements **Product B-AUTO (`raster_auto`)**: the deterministic, CPU-only,
no-OCR, no-learned-model automatic recognition of a supported clean raster
floorplan into `floorplan_parse` 1.2.0 (`source_class: raster_auto`), scored
against the FX1 frozen truth via the frozen WP1 evaluator (exact-by-key).

Mirroring WP3 (`cad_exact`), WP4 is an ADDITIVE pipeline. It introduces a new
`raster_auto` author class (already frozen in `recognition.SOURCE_CLASSES` /
`PRODUCT_SOURCE_CLASSES` by WP2) and never changes the historical
`dxf`/`annotation` path or any existing byte.

Capabilities (implemented, per task body §10 operations and the packet §2.2
no-OCR envelope, all deterministic):
1. Intake + containment + canonical decode (fail-closed before allocation).
2. Thresholding + connected-component clutter suppression (union-find, bounded).
3. Line/arc voting (2-parameter Hough for segments; contour + algebraic circle
   fit for circular-arc walls) with paired-edge thickness recovery.
4. Bounded opening-symbol detection (door/window/passage discr., passage ≤ 3.0 m).
5. Two-anchor scale validation (median residual + disagreement, fail-closed).
6. Topology/face derivation + confidence diagnostics (diagnostic-only).
7. Fail-closed unsupported-input classification (skew, low-contrast, clutter,
   unexplained-ink, unsupported-format refusals).

## 2. Model & provider provenance (recorded, not inferred)

- Active runtime this session: `deepseek/deepseek-v4-pro-0813` via `openrouter`
  (`profiles/panoworld/config.yaml`), `fallback_providers: []`.
- Implementer = `deepseek/deepseek-v4-pro-0813` via `openrouter`.
- Independent read-only review follows the same WP3 pattern: a SEPARATE
  qualified reviewer session via the OmniRoute gateway (`http://127.0.0.1:20128/v1`),
  with actual provider/model recorded from HTTP trailer headers
  (`x-omniroute-provider` / `x-omniroute-model`) — never inferred.
- **Spatial/geometry gate:** WP4 produces NEW raster-vision geometry reasoning
  (voting, paired edges, arc fit), so the Anthropic-Opus spatial review gate IS
  triggered. If an Opus-level route cannot be proven reachable via OmniRoute,
  apply the pre-approved fallback: record requested vs actual provider/model,
  reason and impact; preserve the independent read-only review; never weaken
  thresholds. Failure to record a real provider/model identity → block.

## 3. Blocking finding — acceptance corpus/truth/scale prerequisites

**The WP4 acceptance gate (`≥29/30 clean emits` + P/R thresholds + zero critical
FP + independent truth) is NOT verifiable from the current repository, and the
missing prerequisites are human-gated (`BLOCKED`), not technical failures.**

Evidence (all read this session):

- Packet AT-07: "B clean emit yield ≥95% | R0=30; at least 29 emit". AT-09/10/11/12
  require P/R ≥0.995/0.980 over a supported-scan corpus. AT-13 requires zero
  critical FP with an exact rule-of-three bound over "all 100 families".
  Packet line 71: "Locked acceptance contains 100 source families: R0 30…".
- The repository contains exactly ONE supported clean raster with frozen truth:
  `evidence/PLAN-002RF/WP0-FX1/fixture/fx1.png` (`fx1_hall`), plus its
  independent truth (`recognizer_inputs=[]`) and three hash-bound anchors.
- The frozen WP1 split manifest (`evidence/PLAN-002RF/WP1/lock/wp1-split-manifest.json`)
  declares only three family names — `fx1_hall` (train), `fx1_apse` (dev),
  `fx1_blind` (blind) — and ONLY `fx1_hall` has materialized raster + truth.
  `fx1_apse` and `fx1_blind` are placeholders ("arc topology derived from fx1",
  "reserved; truth frozen, never scored during development") with no raster and
  no truth in the tree.
- WP0 numbered-decisions record (`numbered-decisions-u1-u15.md`) still leaves
  **BLOCKED**: U-2 (exact two-anchor scale fit/weight/disagreement formula),
  U-3 (arc radius/sweep/sampling bounds), U-4 (clustering/merge limits),
  U-5 (fixed B symbol/style guide). AT-21 (independent truth via two blind
  labelers + independent adjudicator) has no realized labeler/adjudicator output.
- WP0 closure was `STOP / NOT_EVALUABLE` for Product-B accuracy for exactly this
  reason: "Product-B accuracy/yield/resource feasibility is unproven."

**Consequence:** emitting geometry for a fabricated 30-family corpus, or scoring
a fabricated "29/30" against invented truth, would violate the packet's own
anti-gaming rules (AT-18 no tuning, AT-21 no fabricated truth, W-17 emitting
geometry for unproven inputs is CRITICAL). WP4 therefore implements the engine
and proves its behavior on the single real supported fixture (fx1) + locally
synthesized adversarial/refusal inputs, and **blocks** on the corpus/truth/scale
prerequisites rather than fabricating them.

## 4. Design

### 4.1 New module `src/pwa/floorplan/raster_auto_geometry.py`

Pure, deterministic NumPy/Pillow primitives (no OCR, no model, no network):
- global Otsu with frozen tie-break + separability gate;
- 8-connected union-find component labelling;
- 2-parameter (θ, ρ) Hough accumulator for segment walls;
- contour following + Kåsa/Pratt algebraic circle fit (RMS residual) for arcs;
- paired-edge thickness recovery (parallel-edges → centreline + thickness);
- two-anchor scale fit (median residual + max pairwise disagreement);
- face/topology derivation reusing `builder` validators + `findings` codes.

### 4.2 `raster_auto_worker.py` + `raster_auto.py`

Subprocess worker boundary (mirror `dxf_source.py`/`cad_exact_worker.py`):
intake → containment → canonical decode → binarize → components → vote
→ paired edges → openings → scale → topology → confidence → emit or refuse.
Emitter outputs `floorplan_parse` 1.2.0 (`source_class: raster_auto`, m units,
quantized mm for scoring), an FX1-truth scorer, and a deterministic SVG overlay.

### 4.3 Fail-closed refusals

Reuse frozen `findings` codes plus the frozen WP2 `RECOGNITION_*` blocking codes;
draft WP0 refusal conditions (RASTER_LOW_CONTRAST, SCALE_ANCHORS_INSUFFICIENT,
RASTER_CLUTTER_EXCEEDS_ENVELOPE, RASTER_UNEXPLAINED_INK, RASTER_UNSUPPORTED_FORMAT,
PATH_REPARSE_POINT, …) are recorded as the refusal-condition list, with final
code shapes assigned append-only (U-9 continues to govern exact code text).

## 5. Acceptance that IS verifiable this WP (engine behavior)

- determinism (parse + emit + SVG byte-identical across replays);
- fail-closed negative/adversarial refusals (low-contrast, clutter-over-band,
  unexplained-ink, unsupported-format, missing/contradictory anchors, skew);
- resource caps (MAX_SOURCE_RASTER_BYTES, MAX_SOURCE_PIXELS, header-only decode);
- topology refusal (leak/dangling/self-intersect) on derived faces;
- rollback (pure/idempotent; source immutable; route default-off);
- fx1 supported-fixture behavior (structure recovered; score bound to frozen truth).

## 6. Acceptance that is NOT verifiable this WP (→ BLOCKED, not fabricated)

- ≥29/30 clean emits (R0 corpus absent: n=1);
- wall/opening P/R ≥0.995/0.980 (no adjudicated labeler truth);
- zero critical FP with exact 3/n bound over 100 families (corpus absent);
- two-anchor scale fit/disagreement formula (U-2 BLOCKED);
- fixed symbol/style guide (U-5 BLOCKED).

## 7. Evidence & handoff

- `evidence/PLAN-002RF/WP4/` — run report, targeted + full-suite logs,
  model-provenance.json, independent review, evidence-index.json bound to the
  exact checkpoint, and `HANDOFF-WP4-to-WP5.md`.
- Git checkpoint on `main` (local commits only; no push).
- Closure records the blocker and does NOT authorize WP5 (`t_dfa6f24f`).
