# HANDOFF — WP0-FX1 to t_d025498b

- Producer: Kanban `t_c6b406c5`, OpenAI Codex `gpt-5.6-sol`
- Critical spatial architect: Anthropic first-party `claude-opus-5`, session `c0d9917d-ce87-4f1c-9f92-e58d3c72c28a`, MAX requested, no fallback
- Consumer: `t_d025498b`
- Contract: fixture-local `1.0.0`; no production schema or route change

## Stable artifacts
- `fixture/fx1-source-geometry.json`: project-owned explicit mm geometry.
- `fixture/fx1.png`: clean 2400×2000 grayscale raster with straight/diagonal/arc walls, typed motifs, topology-bearing rooms, bounded clutter, and three distributed no-text anchors.
- `fixture/fx1-truth.json`: frozen independent truth derived only from source geometry; `recognizer_inputs=[]`.
- `fixture/fx1-scale-anchors.json`: three hash-bound scale anchors; horizontal, vertical, diagonal; all exactly 0.005 m/px.
- `fixture/fx1-rights-provenance.json`: zero third-party bytes/assets and LOCAL-ONLY provenance.
- `fixture/fx1-manifest.json`: deterministic replay hash `sha256:243ace7f0793be867a7e8b6cfeab2244bdf70a823e8ba9778334ee648c79bb87`.
- `reviews/independent-omniroute-rework-review-e2fbd32.md`: fresh read-only review of implementation `fc3a9c3` plus evidence index `e2fbd32`; verdict `APPROVE`, no findings.

## Validation
Run only in an already-provisioned approved environment:
`python tools/make_wp0_fx1_fixture.py --verify evidence/PLAN-002RF/WP0-FX1/fixture`

## Consumer obligations
- Verify the exact reviewed checkpoint and evidence index before use.
- Preserve source→{raster, truth} independence; never derive truth from recognizer output.
- Do not infer recognition accuracy/yield from this fixture package.
- Do not activate Product A/B routes; the full-campaign authorization permits technical successors only after dependency completion and fresh gates, while WP6 activation remains a separate human gate.
- Keep pinned-environment proof pending; the existing-env suite is not a substitute.

## Known limits
- This is the approved clean synthetic envelope, not a private real-plan or degraded scan.
- Fixture-local truth represents circular arcs and passage motifs that current production schemas do not represent; no schema change is implied.
- The recovered review of `60c5978`, its bounded rework disposition, and the fresh approving review of `fc3a9c3` + `e2fbd32` are durable under `reviews/`.
