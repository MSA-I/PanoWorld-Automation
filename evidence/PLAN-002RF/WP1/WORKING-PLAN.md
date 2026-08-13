# PLAN-002RF WP1 — Corpus and evaluator lock — working plan

- Task: `t_2f261417`
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Parent WPs: `t_4f9188e9` (supervision verify), `t_d025498b` (WP0 closure) — both DONE.
- Status: executing under Moshe full-campaign authorization (2026-08-13).

## 1. Scope statement

Lock the corpus and the evaluator before any Product A/B recognition implementation.
WP1 produces frozen, hash-bound artifacts and tooling; it does NOT implement a
recognizer and does NOT acquire any corpus from the network (HARD boundary:
local-only, no third-party bytes, no spend, no route activation, no PLAN-003).

Concrete deliverables:

1. **Rights & provenance lock** — name the Rights Owner, freeze the local-synthetic
   provenance chain, record the privacy/retention posture for the local corpus.
2. **Family splits + leakage controls** — train / dev / blind splits of the synthetic
   family with an explicit family-boundary leakage check (no family may cross a split
   boundary; the blind family is never scored during development).
3. **Role matrix** — name and strictly separate the Rights Owner, two blind labelers,
   the adjudicator, the QA delegate, and the independent reviewer; a forbidden-overlap
   matrix makes overlap a fail-closed condition.
4. **Frozen evaluator architecture** — matcher, canonicalization, macro/micro/per-plan
   statistics, refusal accounting, 95% rule-of-three calculator, support
   classifier/style guide. Frozen before truth is opened; scoring is deterministic.
5. **Hash-bound truth & evaluator artifacts** — every truth file, role ledger, split
   manifest, and evaluator spec is bound to a git blob + sha256 in an evidence index.
6. **Independent read-only review** — separate reviewer session (NOT described as
   cross-provider under the active DeepSeek/OpenRouter policy; see §3).

## 2. Model & provider provenance (recorded, not inferred)

- Active governing policy: `docs/08-מדיניות-ניהול-מודלים-וסוכנים-deepseek-first.md`
  (`MODEL-AGENT-MANAGEMENT-v4-AUTONOMOUS`), read 2026-08-13.
- Active runtime (this agent session), from `profiles/panoworld/config.yaml`:
  - `model.default`: `deepseek/deepseek-v4-pro-0813`
  - `provider`: `openrouter`
  - `fallback_providers`: `[]` (none)
  - `custom_providers`: `Local (127.0.0.1:20128)` = OmniRoute gateway, model `auto/coding`.
- OmniRoute gateway probe (2026-08-13): `GET http://127.0.0.1:20128/v1/models` → HTTP 200,
  live; exposes `auto/best-*`, `auto/pro-*`, etc. It is reachable but is NOT the active
  routing for this session.
- Therefore: **implementer = deepseek/deepseek-v4-pro-0813 via openrouter** (this session).
  Cross-provider review is declared UNAVAILABLE by the active policy
  (`PROJECT-STATE.yaml → model_policy.cross_provider_review_available: false`).
  The independent review is a separate deepseek-v4-pro read-only-first session plus
  deterministic evidence — explicitly NOT labelled cross-provider.
- No Anthropic Opus / OmniRoute model substitution is claimed. WP1 contains no
  geometry-critical new spatial design: the circular-arc / topology spatial truth is
  already designed (WP0 `claude-opus-5`, `opus-spatial-design-full.md`) and WP1 only
  locks it as frozen truth — no new spatial reasoning is produced.

## 3. Role matrix (U-6 closure)

Strict separation (fail-closed): no person holds two roles from a forbidden pair.

| Role | Holder | Notes |
|---|---|---|
| Rights Owner | Moshe (human) | Only Moshe may authorise rights/scope changes or a third-party byte. |
| Labeler A (blind) | deepseek-v4-pro session A (separate) | Producer of the `train`/`dev` family's chain-of-walls truth review. See §7 for what "blind" means on a synthetic corpus. |
| Labeler B (blind) | deepseek-v4-pro session B (separate) | Independent second pass over the same truth; disagreement → adjudicator. |
| Adjudicator | deepseek-v4-pro session C (separate) | Resolves A/B disagreements; cannot be A or B. |
| QA delegate | deepseek-v4-pro session D (separate) | Signs frozen output; cannot be a labeler or the adjudicator. |
| Independent reviewer | read-only-first review session (separate) | Approves the lock; cannot be the implementer. |
| Implementer | this session (deepseek-v4-pro via openrouter) | Cannot label, adjudicate, or self-approve. |

Forbidden-overlap matrix (row ∩ column = FAIL-CLOSED):

|            | Impl. | Lab.A | Lab.B | Adjud. | QA | Reviewer |
|-----------:|:----:|:----:|:----:|:----:|:--:|:--:|
| Implementer|  —   |  X   |  X   |  X   | X  |  X  |
| Labeler A  |  X   |  —   |  X   |  X   | X  |  X  |
| Labeler B  |  X   |  X   |  —   |  X   | X  |  X  |
| Adjudicator|  X   |  X   |  X   |  —   | X  |  X  |
| QA delegate|  X   |  X   |  X   |  X   | —  |  X  |
| Reviewer   |  X   |  X   |  X   |  X   | X  |  —  |

Note on "blind" labelers over a synthetic corpus: the truth is frozen and independent
of any recognizer, so labelers verify the authored geometry rather than recognizer
output (`recognizer_inputs=[]` guaranteed by construction). Blindness is enforced as
"no labeler sees the other's verdict before recording its own", which the ledger's
append-only ordering enforces.

## 4. Family splits & leakage controls (U-4, U-5, U-13)

The local synthetic corpus is organized into disjoint **families** (structural
templates). A family boundary is the leakage unit: a family may appear in exactly one
split. Splits:

- `train` — families used to develop the matcher/canonicalizer (when WP3/WP4 begin).
- `dev` — disjoint families used for threshold/calibration during development.
- `blind` — disjoint families reserved for final scoring; never read during development.

Leakage controls (enforced by the split tool + tests):
1. A family id maps to exactly one split (no family in two splits).
2. Duplicate detection by content hash across the whole corpus (no near-duplicate
   families straddling splits).
3. The blind split's truth is never opened by development-time tools (the split
   manifest allows exclusion; a scorer bound to the frozen evaluator may only be run
   against `blind` at the final gate, and never during tuning).

## 5. Frozen evaluator architecture (U-1, U-3, U-14)

Frozen before truth is opened; scoring is deterministic and hash-replayable.

- **Matcher** — wall/opening matching by deterministic id and quantized geometry,
  NOT by recognizer output. A wall in a prediction matches a truth wall iff their
  quantized endpoint projection is within the frozen tolerance and their canonical key
  is identical.
- **Canonicalization** — every geometric record is canonicalized (unit-normalized,
  key-sorted, quantized to the frozen grid) before hashing or matching, so byte-equal
  canons imply equal geometry.
- **Metrics** — `macro` (mean of per-plan metric), `micro` (aggregate over all
  predictions), `per-plan` (each plan's own metric); frozen formula in the evaluator spec.
- **Refusal accounting** — a prediction that refuses (unsupported input) is counted
  separately and never silently promoted to a correct answer; a refusal on a supported
  plan is a false negative, and refusal rate is reported, not hidden.
- **95% rule-of-three** — lower bound of the 95% Wilson score interval for a
  proportion `k/n` (a.k.a. "rule of three" when `k=0`: `3/n`); frozen as a pure
  function with `k` and `n` so "0 errors in n" cannot be reported as 100%.
- **Support classifier / style guide** — a predeclared taxon of supported motifs
  (segment walls, circular-arc walls with stated sagitta bound, door/window/passage
  openings, orthogonal + one diagonal 3-4-5 family) and a style guide naming what is
  OUT of scope (double-line hatched walls, text, furniture, stairs, dotted grids,
  arbitrary diagonals). Anything outside the predeclared taxon → `unsupported` →
  refusal path.

## 6. Implementation plan (TDD)

All code changes follow RED→GREEN. New files:

- `tools/make_wp1_evaluator_lock.py` — builds the frozen evaluator spec + role ledger
  + split manifest + support taxonomy, writes them under the WP1 fixture dir, and
  emits a deterministic replay manifest (mirrors `make_wp0_fx1_fixture.py`).
- `src/pwa/evaluator/metrics.py` — frozen pure functions: canonical key, quantize,
  matcher match score, macro/micro/per-plan, refusal accounting, rule-of-three.
  (New module; no production schema/contract change.)
- `tests/unit/test_wp1_evaluator.py` — RED then GREEN over metrics + leakage + roles.

No dependency is installed (all stdlib + already-vendored `pwa.files`). No contracts /
schemas in `schemas/` / `contracts/` are mutated.

## 7. Evidence & acceptance

Acceptance (from task body):
- rights and role matrix approved → `WP1/rights-and-role-matrix.md` + role ledger.
- evaluator independently reviewed → separate review session verdict recorded.
- all truth/evaluation artifacts hash-bound → `WP1/evidence-index.json` referencing
  `git_blob` + `sha256` for every produced artifact.

Exit gate: both freeze documents exist and are hash-bound; leakage/split/role tests
pass; independent read-only review returns APPROVE (or APPROVE_WITH_FIXES with all
fixes closed); otherwise WP1 remains non-evaluable / BLOCKED — NOT auto-passed.
