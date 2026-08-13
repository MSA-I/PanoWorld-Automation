# PLAN-002 acceptance

## Final acceptance record — 2026-08-13

PLAN-002 (Floorplan Parsing) is **accepted and G1 evidence is claimed**. Moshe gave the
final visual/geometry approval on 2026-08-13 on the dedicated human gate
(`t_f442d3dc`, "P1-02G — Moshe visual approval for PLAN-002 overlay"). With that single
remaining §20 human gate closed, every acceptance gate the plan reserved is now shut:

- Five review rounds and five bounded reworks (NA-3b → NA-3e → NA-3g), each
  independently cross-provider reviewed, ended in ACCEPT (NA-3f, NA-3h).
- GC3-8 (annotating one selected intake-generated PDF page) was implemented as its own
  contract round (NA-6) and independently reviewed (NA-6b): verdict ACCEPT, all nine
  acceptance criteria MET, "GC3-8: CLOSE".
- AC-13's provenance requirement was enumerated as a plan amendment (NA-7), reviewed by an
  independent OpenAI reviewer, and applied — converting a three-round CANNOT_VERIFY into a
  decidable criterion that the reviewer stated it would now mark MET.
- NA-4 (Layer A visual/geometry gate) and NA-5 (annotated public-domain sample smoke) are
  both closed; the two adapters emitted the IDENTICAL canonical projection from one
  measured geometry, the first empirical evidence for §6's cross-adapter equivalence claim.
- Moshe APPROVED the Layer A overlay on 2026-08-13 as sufficient G1 evidence.

## Fresh verification — closeout

- Fresh full suite run from a clean state on `main` (2026-08-13), inherited `PYTHONPATH`
  cleared, root `.venv` Python 3.11:
  **393 passed**, `failures=0`, `errors=0`, `skipped=0`, exit 0 (~4 min).
  (Earlier rounds: 261 → 291 → 306 → 316 → 338 → 351 → 356 → 369 → 393. The count grew as
  each accepted rework and contract round landed on main.)
- Command: `env -u PYTHONPATH ./.venv/Scripts/python.exe -m pytest --basetemp .tmp/pytest-closeout-fresh`
- `git diff --check` clean; `pyproject.toml` and `uv.lock` unchanged across the whole line;
  no tracked file deleted; no path or OS-user-name leak in regenerated evidence (GC3-6 /
  §12 forward rule holds for new evidence).

## Gate conditions

- Round-2 gate conditions GC-1..GC-7: all settled (GC-6 projected width, GC-7 raster
  metadata sanitisation — both Moshe-decided and implemented).
- Round-3 gate conditions GC3-1..GC3-10: all closed. GC3-1..GC3-7 and GC3-11 were bounded
  code fixes, verified by the orchestrator with proofs-of-concept rather than the
  implementer's report. GC3-8 (contract, Moshe-decided) implemented/reviewed. GC3-9
  (evidence privacy, Moshe-decided) accepted-and-documented. GC3-10 (= NA-4 visual gate)
  is now approved.

## Known limitations — recorded honestly, not glossed

- **Label overlap / legibility.** Every entity's opaque device ID is drawn as a label in the
  overlay. At the Layer A entity count the labels overlap each other and the source, so the
  overlay is correct but hard to read. This is the unpriced legibility cost of GC3-6's
  tokenisation and was called out explicitly to Moshe before approval. Moshe accepted it as
  sufficient G1 evidence with the overlap "noted". Future plan work (PLAN-003 geometry
  compilation) should budget for a legible label strategy.
- **Angled/curved walls.** Part 1's deliberately narrow DXF convention and the manual
  annotation adapter support straight (axis-aligned) walls. Rotated/curved/angled walls were
  reported by Moshe during the visual gate; the supported-geometry boundary is documented in
  PLAN-002 §2, and extending it is future plan work, not a defect of the delivered scope.
- **JPEG overlay sanitisation is a second lossy encode** (quality pinned at 95), so the
  embedded image is not bit-identical to the source; the SHA-256 binding still ties it to the
  exact original bytes. Acceptable for a human-review overlay.
- **ACK deviation (GC3-9).** The already-committed absolute paths and OS user name in legacy
  evidence are accepted and documented retroactively; new evidence must comply with §12.
- `tests/unit/test_floorplan_builder.py` uses `PIL.Image.getdata()`, deprecated for Pillow 14
  (2027-10-15); cosmetic, switch to `get_flattened_data()` when convenient.

## Hard boundary statement

No network, install, upload, provisioning, spending, GPU, H200, cloud, or remote execution
was performed at any point in PLAN-002. Model routing stayed local (OpenAI implementer via
Codex CLI, Anthropic reviewer via `claude` CLI; the documented gpt-5.4 silent-substitution
deviation was recorded retroactively and the work reviewed rather than reimplemented).
**G7/G8 and H200/GPU are DEFERRED TO PART 2** (AC-23). PLAN-003 is not started from here.

## Evidence paths

- Visual gate: `evidence/PLAN-002/visual-gate/` (`na4-layer-a-dxf-overlay-rendered.jpg`,
  `na5-sample-raster-overlay-rendered.jpg`, `na4-na5-record-20260811.md`, `harness-summary.json`).
- Reviews: `evidence/PLAN-002/reviews/` (five independent rounds + orchestrator verifications).
- Decisions: `evidence/PLAN-002/decisions/` (GC3-8 amendment, AC-13 enumeration).
- Test results: `evidence/PLAN-002/test-results/`.
- Handoff: `docs/handoffs/HANDOFF-PLAN-002-to-PLAN-003-001.md`.

## Rollback

PLAN-002 is merged into `main` as preserved, reviewed, accepted work. Rollback for any future
change is standard git: branch from `main`, review, and do not force-push or rewrite history
(append-only evidence policy). The merge was preservation-plus-acceptance; the code carries
its own immutable derived-run artifacts and never mutates a finalized PLAN-001 run.
