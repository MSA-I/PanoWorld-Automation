# Orchestrator verification of NA-6 (PLAN-002, the GC3-8 contract amendment)

Subject: branch `panoworld-dev/na-6-gc3-8`, cut from `main` at `e8e0e7e`.
Specification: `evidence/PLAN-002/decisions/gc3-8-amendment-rev2-approved-20260811.md` (approved).
Implementer report: `evidence/PLAN-002/reviews/na6-gc3-8-implementation-report-20260811.md`.
Date: 2026-08-11. Author: orchestrator (Anthropic `claude-opus-5[1m]`, EXTRA).

The report was not accepted as evidence. Everything below was executed or read here. The
verification script is `<scratch>/verify_na6.py`; it builds its own two-page PDF and compares
pixels rather than trusting either the report or the implementer's tests.

## 1. Executed — 24 independent checks, 24 pass

| Group | Checks | Result |
|---|---|---|
| Full suite, `.venv`, cleared `PYTHONPATH` | dot count read independently of the summary line | **369 passed, exit 0** (baseline 356, so 13 added) |
| AC 1/2 schema | catalog exposes exactly `1.0.0` and `1.1.0`; frozen 1.0.0 matches the pinned digest; 1.0.0 enum still lacks `floorplan_page`; 1.1.0 appends it | 4/4 |
| AC 4 two-page PDF intake | one `kind=floorplan` and it is the PDF; exactly two `floorplan_page`; both are PNG page renders under `derivatives/pdf/`; `style_reference` untouched; manifest declares 1.1.0 and validates | 6/6 |
| AC 5 page-2 selection | the two page renders differ in bytes (10,123 vs 16,163); the run parses; **the overlay embeds page 2's exact pixels — 480,000 pixels compared** and not page 1's; the recorded source hash is page 2's and not page 1's | 6/6 |
| AC 6/8 negatives | `style_reference`, raw PDF and a missing reference each give `PARSE_SOURCE_UNSUPPORTED` + CLI 2 + no finalized run; a wrong hash still gives `PARSE_SOURCE_HASH_MISMATCH` and **not** "unsupported" | 5/5 |
| AC 7 direct raster | a direct PNG floorplan annotation still parses; a non-PDF source produces no `floorplan_page` | 2/2 |
| R-1 | `sys.stderr` replaced by an object whose `write` raises `OSError`: `main()` returns **2** and does not raise | 1/1 |

On the page-2 binding: my first pass reported the recorded hash as `None` because I looked for it in
the parse payload. It is in the overlay's `<metadata>` block. Re-checked by hand:
`source_sha256 = sha256:377b7460…` equals page 2's inventory hash exactly and differs from page 1's.
That is the check the amendment's AC 5 actually asks for, and it passes.

## 2. Additive-ness, checked structurally rather than by eye

The strongest check available, and the implementer built the same one into
`tests/unit/test_contract_versions.py`: take 1.1.0, revert `$id`, revert the `schema_version` const
to `1.0.0`, remove `floorplan_page` from the enum, and assert the result **equals** 1.0.0. It does.
My own flattened key-by-key comparison of the two files finds **exactly three differences**:

```
/$id                                                    1.0.0 -> 1.1.0 filename
/allOf[1]/properties/schema_version/const               "1.0.0" -> "1.1.0"
/allOf[1]/.../inputs/items/properties/kind/enum[3]      (absent) -> "floorplan_page"
```

Three, which is exactly what the amendment authorises. Nothing else moved.

Bundle: the derived manifest declares `contracts_bundle_version: 1.2.0` and `schema_version: 1.1.0`;
new intake manifests do the same. Verified by reading a real run, not the report.

Forward/backward direction, verified on the real files: a manifest using `floorplan_page` validates
as 1.1.0 and **does not** validate as 1.0.0 — the intended direction for an additive minor bump.

## 3. A finding against the APPROVED TEXT, not against the implementation

**F-NA6-1 (text defect, needs the same gate the text came through).**

AC 2 of the approved amendment says, verbatim:

> Every historical 1.0.0 fixture validates unchanged under its declared version and under 1.1.0.

The second half is **literally unsatisfiable** in this contract system, and not because of anything
the implementer did. Every version of every schema here pins its own `schema_version` as a `const`.
So a document declaring `"schema_version": "1.0.0"` can never validate against the 1.1.0 schema —
the const forbids it by construction. Measured on the three committed 1.0.0 manifests in `runs/`:

```
runs/RUN-20260806-060723-42cc1f60/project/project_manifest.json  declared_ok=True  as_1.1.0=False
runs/RUN-20260806-140000-demo1/project/project_manifest.json     declared_ok=True  as_1.1.0=False
runs/RUN-20260806-141000-demo2/project/project_manifest.json     declared_ok=True  as_1.1.0=False
```

All three still validate under their declared version, which is the clause that matters. None
validates "under 1.1.0", which the AC also demands.

The implementer resolved this the only sane way — its test relabels the historical example to
1.1.0 and then validates, i.e. it proves the **payload shape** is forward-compatible — and reports
AC 2 as satisfied. I agree with the implementation and disagree with the text: as written, a future
reviewer reading AC 2 literally would mark it NOT MET and be right on the letter while wrong on the
substance.

Proposed one-sentence repair, for the NA-6b reviewer to rule on rather than for me to apply, since
the text passed a gate:

> Every historical 1.0.0 fixture continues to validate unchanged under its declared version, and its
> payload shape is valid under 1.1.0 when relabelled to that version. A document declaring
> `schema_version: "1.0.0"` is not expected to validate against the 1.1.0 schema, whose
> `schema_version` const forbids it by construction.

I am recording this rather than fixing it because the amendment went through a cross-provider gate
and a change to it needs the same gate. It changes no code.

## 4. Boundaries, checked here

| Boundary | Result |
|---|---|
| `contracts/error_codes.md` | unchanged; no new token, and `PARSE_SOURCE_UNSUPPORTED` already existed |
| `pyproject.toml`, `uv.lock` | unchanged |
| `src/pwa/floorplan/config.py`, `limits_snapshot()` | unchanged, no new key |
| `tests/golden` and the golden hash | unchanged; the golden suite passes and the hash is still `sha256:e5041ddc…b7e77e` |
| frozen 1.0.0 schema | byte-identical to the pinned digest |
| `evidence/` | nothing rewritten; the implementer's report is its only new file |
| `docs/plans/PLAN-002-floorplan-parsing.md` | changed — **authorised for this round only**, and confined to the two clauses the amendment names. This is the first round permitted to touch the plan, and the scope held |
| GC3-9, GC3-10 | untouched |

## 5. What this closes

GC3-8 was the last of the round-3 gate conditions with no implementation. PLAN-002 section 6 has
promised annotating a selected intake-generated PDF page since the plan was approved, and the code
could not reach it. It can now, and the negative paths are classified rather than collapsed into a
generic operational failure. On my evidence the plan text and the code finally agree.

I am not marking GC3-8 CLOSED here. That is the NA-6b reviewer's call, and it is also the reviewer
who should rule on F-NA6-1.
