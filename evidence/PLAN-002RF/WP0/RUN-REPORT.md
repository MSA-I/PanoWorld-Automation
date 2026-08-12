# RUN REPORT — PLAN-002RF WP0 CPU feasibility gate

- Date: 2026-08-12
- Task: `t_d025498b`
- Branch: `panoworld-dev/t_d025498b-wp0-activate-approved-plan-002rf-decisio`
- Starting commit: `962c87f03c1a7859a7ef0b16b97673a171952e0d`
- Controlling packet SHA-256: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`
- Final disposition: **STOP / BLOCKED**

## Scope executed

WP0 only: source/rights and environment preflight, dependency/license inventory, read-only Opus spatial-design request, TDD fail-closed protocol, two CPU diagnostic replays, U-1..U-15 decisions, proposed ADR-0006, evidence index and handoff. No Product A/B route was activated; no GPU/H200/cloud/remote/network corpus/spend/G7/G8/PLAN-003 work occurred.

## Target workstation fingerprint

- OS: Microsoft Windows 10 Pro, version 10.0.19045, observed command build string 19045.6456.
- CPU: Intel Core i7-9800X @ 3.80 GHz; 8 cores / 16 logical processors.
- Physical RAM: 51,202,351,104 bytes.
- Project runtime: Python 3.11.15.
- Project lock SHA-256: `uv.lock` `a636f9bca0f4e5f63eb7253386cb5a1248a651d693320f0b5e835975bde0e18a`; `pyproject.toml` `f0196ef891c140a6410a4bbcc44aa381dbb38ab0974bdb26a16b26d521c02d5d`.

## Fixture and validity

- Existing tracked public-domain JPEG: 842×569 RGB, 235,297 bytes.
- SHA-256 matched documentation: `917a5753feceb65f8401381894bfb0809bd43194879002d2aa2acb74ee80df08`.
- Characteristics: double-line/hatched walls; diagonal bay; door swings, windows, stairs; text, furniture, dotted grid and compass clutter.
- Missing: independent adjudicated geometry truth and two authoritative scale anchors.
- Previous annotation/measurement evidence is explicitly not independent accuracy truth.

## TDD record

1. RED test authored first: `tests/unit/test_wp0_cpu_feasibility.py` imported missing `tools.wp0_cpu_feasibility`.
2. First RED command could not reach feature failure because no project pytest environment existed (`No module named pytest`, exit 1). This is recorded as an environment-blocked RED, not claimed as a clean expected assertion failure.
3. Minimal implementation added in `tools/wp0_cpu_feasibility.py`.
4. Targeted test executed with already-cached pytest plus existing local Hermes Pillow/NumPy: `2 passed`, exit 0.
5. Full suite attempted without installing missing dependencies; collection stopped with nine `ModuleNotFoundError: ezdxf`, exit 2. No dependency was installed to hide the boundary.

## Feasibility execution

Command:

`env -u PYTHONPATH python tools/wp0_cpu_feasibility.py samples/Sample_Floorplan.jpg evidence/PLAN-002RF/WP0/fixture-manifest.json --replays 2 --output evidence/PLAN-002RF/WP0/cpu-feasibility-result.json`

Expected/actual protocol exit: 3 (`STOP`).

Measured diagnostic-only results:

- replay hashes: identical, `de4358ea8ebdee3f345f1ecc962376a06d4035a35e7e9cecff6a27beb5ce8db6` twice;
- runtime: 0.039475 s max, 0.031260 s median;
- `tracemalloc` peak: 1,692,138 bytes;
- diagnostic pixels: 479,098 total; 23,350 <64 gray; 24,481 <128 gray; 60,845 edge pixels >64.

These measurements cover deterministic decode/grayscale/edge diagnostics only. They do not measure an automatic geometry recognizer, total process RSS, or accuracy/yield.

## Exact stop/go thresholds

- source hash and rights must pass before processing;
- independent truth and at least two authoritative scale anchors required for accuracy evaluation;
- two replay outputs/diagnostics byte-identical;
- whole local run <60 seconds;
- soft observed memory <1.5 GiB, with Windows hard-RSS residual documented;
- no boundary/security violation;
- future clean-raster GO additionally requires the approved AT-07/09/10/11/12/13/14/15/16/17/18/19/20/21/22/23/24/25/26 conjunctive gates on the locked population.

Current blockers: `INDEPENDENT_TRUTH_MISSING`, `TWO_AUTHORITATIVE_SCALE_ANCHORS_MISSING`, unpinned executed package versions, incomplete full-suite dependencies, and the installation-boundary incident below. Outcome: STOP.

## Boundary incident and rollback

A preflight `uv run` unexpectedly created ignored `.venv` and installed 20 locked packages. That was not permitted by WP0. The directory was immediately removed, tracked dependency files remained unchanged, and no package/lock change is in Git. The incident blocks AT-25/technical closure and is not minimized as harmless.

## Model routing evidence

- Required author: Anthropic Claude Code Opus, MAX, no fallback, read-only/plan.
- Claude Code version: 2.1.227.
- A one-turn preflight returned authoritative runtime metadata: first-party `claude-opus-5`, session `f045e27e-f352-4d21-8b3c-13cdb27e7917`, no fallback observed.
- Full spatial-design session: first-party `claude-opus-5`, 28 turns, session `6a2a726e-170e-47fb-938f-f4dcc7f4e747`, 798.392 s wall / 759.882 s API, USD 3.9669365, no permission denials or fallback. Four `/skills` were loaded; only `threat-modeling-expert` was substantively applicable. The full 620-line memo and raw JSON are preserved. It classifies this fixture as unsupported and identifies a no-OCR vs machine-readable-scale-anchor conflict requiring Moshe.
- Independent cross-provider review must be OpenAI and read-only, bound to the exact Git checkpoint. It is not self-approval.

## Deviations

- Executed Pillow/NumPy were 12.2.0/2.4.3 from an already-present environment rather than locked 12.3.0/2.4.6. Pinned replay is not proven.
- Accuracy/yield could not be measured honestly. No synthetic score or reuse of author-created annotation as truth was allowed.
- Full pytest verification could not complete without missing `ezdxf`; no installation was performed after the incident.

## Conclusion

The local CPU can decode and produce deterministic lightweight diagnostics quickly. The `tracemalloc` value is not peak working set and the probe is not the Product-B pipeline, so neither resource threshold passed. This does not establish Product B-AUTO feasibility. WP0 fails closed and requires independent review plus Moshe's explicit next-scope decision; WP1 must not start automatically.
