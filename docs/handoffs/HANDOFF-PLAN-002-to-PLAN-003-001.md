# HANDOFF

- Handoff ID: `HANDOFF-PLAN-002-to-PLAN-003-001`
- Producer: PLAN-002 Floorplan Parsing
- Producer status: `ACCEPTED (G1 claimed)` — approved by Moshe 2026-08-13
- Consumer: PLAN-003 Geometry Compiler (Part 1, local; NOT auto-authorized by this handoff)
- Date: 2026-08-13
- Contract version: bundle `1.2.0` (project_manifest `1.1.0`, floorplan_parse `1.1.1`, floorplan_annotation `1.0.0`)
- Model policy: MODEL-ROUTING-v3-OPENROUTER-DEEPSEEK (historical MODEL-ROUTING-v1 records retained)

## What was delivered (contract half of Part 1)

PLAN-002 built a deterministic, local, reviewable bridge from a finalized PLAN-001 intake run
to a new immutable parse run. Two inputs behind one interface:

1. a deliberately narrow DXF convention; and
2. schema-validated manual annotation for raster inputs.

Both produce schema-valid `floorplan_parse.json`, `assumptions.json`, and a source-aligned SVG
overlay, and they agree on a canonical geometry projection (the two adapters emitted the
IDENTICAL canonical projection from one measured geometry). Two §20 contract changes were
Moshe-approved and implemented as revision 2 (projected opening width; sanitised raster
overlay), and two further amendments landed in their own rounds: GC3-8 (annotating one selected
intake-generated PDF page — `floorplan_page` token, contract bundle 1.2.0) and the AC-13
provenance enumeration (§9 Required Entity Audit Metadata).

## What is stable

- `src/pwa/floorplan/` package (source protocol, DXF adapter, annotation adapter, normalizer,
  validator, overlay renderer, parse-run builder, CLI) — accepted across five independent
  review rounds and five bounded reworks.
- Schemas: `floorplan_annotation` 1.0.0, `floorplan_parse` 1.1.1, `project_manifest` 1.1.0
  (additive; 1.0.0 left byte-identical).
- Immutable derived run semantics: no write to a finalized PLAN-001 run; append-only `PARSE_*`
  error vocabulary; source-run containment and destination containment (junctions/reparse
  points, drive-relative paths, ADS) enforced on both read and write sides.
- G1 evidence: Layer A overlay approved by Moshe; canonical projection hashes pinned
  (`e5041ddc…` for Layer A; `05e6ce82…` for the sample raster).

## Artifacts

| Path | Schema/version | Description |
|---|---|---|
| `evidence/PLAN-002/acceptance.md` | — | Final acceptance record (2026-08-13) |
| `evidence/PLAN-002/visual-gate/na4-layer-a-dxf-overlay-rendered.jpg` | — | Moshe-approved Layer A overlay |
| `evidence/PLAN-002/visual-gate/na5-sample-raster-overlay-rendered.jpg` | — | Sample raster smoke overlay |
| `evidence/PLAN-002/parse/layer-a-1-raster.json` | `floorplan_parse` 1.1.1 | Canonical raster parse |
| `evidence/PLAN-002/parse/layer-a-1-dxf.json` | `floorplan_parse` 1.1.1 | Canonical DXF parse |
| `evidence/PLAN-002/reviews/` | — | Five review rounds + orchestrator verifications |
| `evidence/PLAN-002/decisions/` | — | GC3-8 amendment, AC-13 enumeration |
| `docs/plans/PLAN-002-floorplan-parsing.md` | — | Approved plan (ACCEPTED/G1) |

## How to validate

```bash
# Fresh full suite on main, from a clean state (393 passed 2026-08-13):
env -u PYTHONPATH ./.venv/Scripts/python.exe -m pytest --basetemp .tmp/pytest-plan003-smoke

# Faithful end-to-end parser for a PLAN-001 run:
./.venv/Scripts/python.exe tools/parse_floorplan.py --help
```

## Test evidence

- Fresh closeout run 2026-08-13: **393 passed**, 0 failures/errors/skipped, exit 0.
- Test count grew 261 → 291 → 306 → 316 → 338 → 351 → 356 → 369 → 393 across accepted rounds.

## Known limitations (honest, accepted — not defects)

- **Label overlap / legibility.** Every entity's opaque device ID is drawn as a label; at the
  Layer A entity count labels overlap the source. Moshe accepted this as sufficient G1 evidence.
  PLAN-003 should budget a legible label strategy when it compiles geometry for human review.
- **Straight / axis-aligned walls only.** The deliberately narrow DXF convention and the manual
  annotation adapter do not support rotated/curved/angled walls. Extending the supported-geometry
  boundary is future plan work.
- **JPEG overlay sanitisation is a second lossy encode** (quality 95); image not bit-identical to
  source, but SHA-256 binding preserves the audit chain.
- **No OCR / learned raster parser.** Raster input requires manual annotation (§13: no accuracy
  claim without labelled ground truth — recognition is explicitly out of PLAN-002 scope).
- **ACK deviation (GC3-9):** legacy evidence carries absolute paths and the OS user name, accepted
  retroactively; new evidence must comply with §12.

## Consumer obligations (PLAN-003)

- Consume ONE immutable parse artifact per geometry compilation; do not attempt cross-edit
  identity (content-derived IDs are stable across reruns, not across geometry edits).
- Wall thickness belongs to PLAN-003 (DR-001: interior walls 10 cm; door depth = host wall
  thickness). PLAN-002 delivered centrelines only, with no thickness field.
- Do not modify the PLAN-002 contracts bundle or parse semantics without a new approved PLAN and
  versioning analysis (additive-only, ADR-0005).
- PLAN-003 geometry compilation is **NOT auto-authorized** by this handoff: it requires its own
  PLAN/packet and Moshe's separate approval (WP0–WP6 packet excludes PLAN-003).

## Breaking-change policy

Additive contracts only. Any schema/contract change is its own dispatch with an independent
cross-provider review and Moshe's §20 approval for contract wording, exactly as GC3-8 and AC-13
were routed.

## Open blockers

None for PLAN-002. G7/G8 and H200/GPU/cloud/remote remain **DEFERRED TO PART 2**.

## Approval

- Producer status: `ACCEPTED (G1 claimed)` — approved by Moshe 2026-08-13
- Reviewer status: five independent cross-provider rounds ended ACCEPT (NA-3f, NA-3h, NA-6b)
- Orchestrator status: verified — fresh 393-passing suite, git diff clean, boundaries held
