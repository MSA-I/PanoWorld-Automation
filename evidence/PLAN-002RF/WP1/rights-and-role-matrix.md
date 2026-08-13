# PLAN-002RF WP1 — Rights & role matrix (frozen)

- Task: `t_2f261417`
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Status: FROZEN — this document is part of the WP1 lock; any change requires a
  versioned amendment and an independent read-only re-review.

## 1. Rights Owner

- **Rights Owner: Moshe (human).** Only Moshe may authorise: a rights/scope change,
  a privacy/retention change, spend, credentials/permissions, or the admission of
  any third-party byte or asset into the corpus.
- The Rights Owner is NOT an automated role and may not be merged into any
  execution role (implementer, labeler, adjudicator, QA delegate, or reviewer).

## 2. Corpus rights & provenance (U-7 closure scope)

- Current corpus: project-owned deterministic synthetic fixtures only
  (`third_party_bytes: 0`, `third_party_assets: []`, `network_acquisition: none`,
  `local_only: true` — see `evidence/PLAN-002RF/WP0-FX1/fixture/fx1-rights-provenance.json`).
- WP1 does NOT acquire any corpus from the network. Network acquisition, and any
  admission of third-party bytes, remain a HUMAN gate that only the Rights Owner
  may open.
- Privacy/retention posture (local corpus): all fixtures are synthetic and
  project-generated; there is no personal-data or customer content. If a private
  real-plan fixture is ever needed, it is admitted only as a local, ignored,
  hash-bound sample with a redacted evidence record (per the private-local-
  acceptance-artifact rule) — never committed, never transmitted.

## 3. Role matrix (U-6 closure)

Strict separation is fail-closed: overlap between a forbidden pair invalidates the
affected artifact's approval and blocks the gate.

| Role | Holder | Separation obligation |
|---|---|---|
| Rights Owner | Moshe (human) | may not double as any automated execution role |
| Implementer (producer) | deepseek-v4-pro via openrouter (WP1 producer session) | cannot label, adjudicate, QA-sign, or review its own output |
| Labeler A (blind) | separate deepseek-v4-pro session A | cannot equal B or the adjudicator |
| Labeler B (blind) | separate deepseek-v4-pro session B | cannot equal A or the adjudicator |
| Adjudicator | separate deepseek-v4-pro session C | cannot equal A or B |
| QA delegate | separate deepseek-v4-pro session D | cannot equal a labeler or the adjudicator |
| Independent reviewer | read-only-first separate reviewer session | cannot equal the implementer |

Forbidden-overlap matrix (X = a role pairing that is prohibited):

```text
                 Impl.  LabA  LabB  Adjud QA    Rev   Rights
Implementer       —      X     X     X     X     X     X
Labeler A         X      —     X     X     X     X     X
Labeler B         X      X     —     X     X     X     X
Adjudicator       X      X     X     —     X     X     X
QA delegate       X      X     X     X     —     X     X
Reviewer          X      X     X     X     X     —     X
Rights Owner      X      X     X     X     X     X     —
```

Blind-labeler note (synthetic corpus): truth is authored independently of any
recognizer (`recognizer_inputs=[]`), so "blindness" means neither labeler may see
the other's verdict before recording its own. The append-only role ledger enforces
this ordering; the adjudicator resolves disagreements.

The machine-readable role matrix (`lock/wp1-role-matrix.json`) carries the same
forbidden-overlap set and `overlap_is_fail_closed: true`.

## 4. Role-independence ledger

See WP0-FX1 `role-independence-ledger.md` for the producer/reviewer separation
precedent. WP1 appends its own ledger entries (implementer → reviewer) at closure.

## 5. Approval status

- Rights and role matrix: FROZEN and subject to independent read-only review
  (see the WP1 review record). A rights/role failure is a human/security blocker,
  never a technical fallback.
