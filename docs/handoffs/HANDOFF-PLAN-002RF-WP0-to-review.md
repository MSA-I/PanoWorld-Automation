# HANDOFF — PLAN-002RF WP0 to independent review / Moshe gate

- Producer task: `t_d025498b`
- Status: STOP / independent review BLOCKED / Moshe decision required
- Approved packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Branch: `panoworld-dev/t_d025498b-wp0-activate-approved-plan-002rf-decisio`

## What exists

- Proposed ADR-0006 explicitly preserves ADR-0004 history and keeps routes default-off.
- Exact U-1..U-15 table: U-8 is a candidate protocol pending review; every dependent decision remains blocked or constrained pending evidence/checkpoint/owners.
- Rights/dependency/license inventory and workstation fingerprint.
- TDD fail-closed diagnostic protocol with source-hash preflight, two replays, runtime/memory evidence, and explicit exit 3 on STOP.
- Durable run report and evidence index.
- Anthropic Opus MAX read-only spatial-design output with runtime metadata.

## Result the consumer must preserve

The fixture is lawful and the diagnostic is deterministic/cheap, but it is unsupported: it has neither independent truth nor two authoritative scale anchors. Accuracy and yield were not measured and must not be inferred from the previous author-created annotation. Resource feasibility is also unproven because the probe is not the recognition pipeline and `tracemalloc` is not peak working set. Product B-AUTO feasibility is unproven; WP1 and route activation remain blocked.

## Known deviations/incidents

1. Preflight `uv run` created an ignored `.venv` and installed 20 packages despite the no-install boundary. It was deleted immediately; dependency files stayed unchanged. This blocks AT-25/technical closure.
2. Executed Pillow/NumPy 12.2.0/2.4.3 differ from lock 12.3.0/2.4.6, so pinned-environment replay is not proven.
3. Targeted new tests pass (2/2) via already-cached local packages. Full suite collection stopped on missing `ezdxf`; no corrective installation was made.
4. TDD RED was environment-blocked before the expected missing-module failure, so no clean RED claim is made.

## Independent review result (2026-08-13)

The recovered read-only review is preserved at `evidence/PLAN-002RF/WP0/independent-openai-review-20260813.md`. It is bound to checkpoint `d9ee296058b2bb7d550f2279ca3a6801c9c4675b` and returned **BLOCKED**: 2 CRITICAL, 8 MAJOR, 2 MINOR findings. It found a Git-blob evidence-index mismatch, incomplete U-8 decision logic, untrusted-manifest acceptance, missing resource/security controls, ambiguous machine-readable STOP semantics, incomplete installation-incident evidence, unpinned replay/TDD limits, unverified Opus MAX effort, and U-15 still open.

The review runtime reports exact model `gpt-5.6-sol`, effort `xhigh`, CLI `0.144.6`, session `019ff98d-150a-7a63-a337-e2f91e712835`, but provider alias `headroom` and no authoritative fallback field. Therefore it is independent review evidence but does **not** satisfy the packet's fail-closed proof of OpenAI first-party/no substitution.

This rework checkpoint fixes the manifest trust bypass, distinguishes unsupported-fixture refusal from Product-B feasibility, and regenerates the evidence index from Git blobs. It does not claim to implement the unapproved full recognition/resource/security protocol. U-8, U-15, WP0 technical closure, and WP1 remain blocked.

## Remaining reviewer obligations

Any closure review must bind findings to the corrected exact checkpoint and inspect:

- approved packet and its exact hash;
- `docs/decisions/ADR-0006-plan002rf-automatic-routes-and-wp0-feasibility.md`;
- `evidence/PLAN-002RF/WP0/numbered-decisions-u1-u15.md`;
- code/tests and raw result;
- model metadata/result;
- installation incident, version mismatch, test limitations, and no-network/local-only audit.

Return severity-tagged, file/line/evidence-backed findings and verdict. Do not edit. Cross-provider requirement is met only if runtime metadata confirms OpenAI `gpt-5.6-sol` (or the explicitly authorized exact OpenAI model) with no silent substitution.

## Moshe decision required after review

Choose explicitly; no automatic WP1:

- authorize a new bounded WP0 fixture package with independent truth and two authoritative scale anchors;
- select Product A-only;
- narrow Product B support while retaining all gates;
- stop/reject Product B;
- separately accept or reject the local installation-boundary incident and remediation.

No option may introduce manual product correction or weaken acceptance/security gates.
