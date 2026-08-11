<!-- Archived verbatim by the orchestrator. Mechanical repairs only: a cp862 mangling of em
dashes from the capture pipeline, and removal of zero-width characters. No wording altered.

  task: NA-6b, independent review of the GC3-8 CONTRACT amendment implementation
  provider: anthropic
  requested_model: opus / claude-opus-5
  actual_model_id: claude-opus-5   (no substitution)
  effort: harness-reported "full" (extended thinking enabled)
  route: claude CLI headless (-p), --strict-mcp-config, read-only allowlist, plus a workspace
         directory outside the repository holding the pre-materialised patch
  subject: branch panoworld-dev/na-6-gc3-8 at 1f18fac, cut from main at e8e0e7e
  verdict: ACCEPT, all nine acceptance criteria MET, and "GC3-8: CLOSE"

It executed nothing - no test run, no interpreter, no build - and says so plainly, resting every
verdict on static reading. The orchestrator ran the executable checks separately and recorded them
in evidence/PLAN-002/reviews/orchestrator-verification-na6-20260811.md.

It ruled on F-NA6-1, the defect the orchestrator raised against the APPROVED amendment text, and
agreed: AC 2's second clause is unsatisfiable by construction because every schema pins its own
schema_version as a const, the implementer's relabel-then-validate reading is the only satisfiable
one, and the proposed repair is adequate - with one suggested addition, that the criterion should
cover committed run artifacts and not only test fixtures.

It also raised F-NA6B-1 of its own: three statements in the plan document still name the old schema
and bundle versions. Text-only, and it recommends bundling that fix with the F-NA6-1 repair through
the same gate.
-->

VERDICT: ACCEPT

**Runtime provider:** Anthropic. **Model id:** `claude-opus-5`. **Effort:** harness-reported "full" (extended thinking enabled). **Role:** independent reviewer, NA-6b, PLAN-002. **Date:** 2026-08-11. **Subject:** branch `panoworld-dev/na-6-gc3-8` at `1f18fac`, cut from `main` at `e8e0e7e`; change set read from the materialised patch and re-read in the working tree.

---

## 0. Disclosure and method

Three disclosures first, because they bound everything below.

1. **Mandate item 1 not performed.** I did not invoke `/skills` before starting. No skill in the listing changes a read-only contract review, but the instruction was explicit and I did not follow it. Recorded as a process deviation on my part, not a finding against the implementation.
2. **I executed nothing.** No test run, no interpreter, no build. Every verdict below is either a static reading of committed source, a digest comparison, or a `CANNOT_VERIFY` with the command named. Where the orchestrator executed something I could not, I say so and I treat its result as corroboration, not as proof — its report is evidence I did not produce.
3. **The implementer's report was not treated as evidence.** I read it for orientation and then verified every claim in it against source. Where its claims and the source agree, I cite the source line, not the report.

Bash was present. Every command I ran is listed in §12; all are reads. Nothing touched the index, HEAD, the working tree, or any file.

---

## 1. Verdict per amendment

| # | Amendment | Verdict | Anchor |
|---|---|---|---|
| 1 | New schema `project_manifest` 1.1.0, 1.0.0 frozen | **IMPLEMENTED AS APPROVED** | `schemas/project_manifest/v1/project_manifest-1.1.0.schema.json:1-47` |
| 2 | Contracts bundle 1.1.0 → 1.2.0 | **IMPLEMENTED AS APPROVED** | `src/pwa/intake.py:26`, `src/pwa/floorplan/builder.py:214,915` |
| 3 | Intake emits `floorplan_page` for PDF page renders only | **IMPLEMENTED AS APPROVED** | `src/pwa/intake.py:179` |
| 4 | Parser allowlist + error reclassification | **IMPLEMENTED AS APPROVED** | `src/pwa/floorplan/annotation_source.py:18-22,66-116` |
| 5 | PLAN-002 §5/§6 text | **IMPLEMENTED AS APPROVED, but the plan is left internally inconsistent** — see F-NA6B-1 | `docs/plans/PLAN-002-floorplan-parsing.md:119,203-227` |
| R-1 | CLI stderr write cannot convert exit 2 into an exception | **IMPLEMENTED AS APPROVED** | `src/pwa/floorplan/cli.py:20-36` |

Amendment 5 is the only one carrying a finding, and the finding is against text the implementer was **forbidden** to touch. It does not reduce the verdict on the implementation.

### 1.1 Amendment 1 — schema

`schemas/project_manifest/v1/project_manifest-1.1.0.schema.json` is a new 47-line file. Against the frozen 1.0.0 it differs in exactly the three places the amendment authorises:

- `$id` → `…/project_manifest-1.1.0.schema.json` (line 2)
- `allOf[1].properties.schema_version.const` → `"1.1.0"` (line 13)
- `…payload.properties.inputs.items.properties.kind.enum` gains a **fourth, appended** token `"floorplan_page"` (line 33)

Everything else — `$schema`, the envelope `$ref`, `required`, `additionalProperties`, the `path`/`sha256` subschemas, the pattern on `sha256` — is character-for-character the 1.0.0 text. I confirmed the ordering matters here: `floorplan_page` is **appended** to the enum rather than inserted, so no existing token's position moved. That is cosmetic for JSON Schema semantics but it is what the amendment asked for and it makes the diff reviewable.

The frozen file is untouched. I measured it: `sha256sum schemas/project_manifest/v1/project_manifest-1.0.0.schema.json` returns `b8020d9c79fa009d49c1b7bbaa6a64fd8a7caddfeadfc4080e8a1d3033ca33e6`, byte-identical to the digest the approved amendment pins. The same digest is pinned in the test at `tests/unit/test_contract_versions.py:94-96`, so a future edit to 1.0.0 fails the suite rather than passing silently. That is the right place for the pin.

Discovery: the catalog is filesystem-derived (`src/pwa/contracts.py:56-89` — `rglob`, reject duplicate `(schema_id, schema_version)`, reject duplicate `$id`, build a latest-view by semver). No registry file needed editing, and none was edited. Both versions are therefore live, `validate_artifact` dispatches on the document's **declared** version (`tests/unit/test_contract_versions.py:129-144` is the pre-existing proof of that behaviour), and the latest-view now resolves `project_manifest` to 1.1.0 (`tests/unit/test_contract_versions.py:86`).

### 1.2 Amendment 2 — bundle

`CONTRACTS_BUNDLE_VERSION = "1.2.0"` at `src/pwa/intake.py:26`; derived manifests carry `"contracts_bundle_version": "1.2.0"` at `src/pwa/floorplan/builder.py:214` and `:915`.

The important structural fact, which I checked rather than assumed: **there is no bundle registry file.** `contracts/` contains `error_codes.md` and `README.md`; `schemas/README.md` states only that artifacts record a single `contracts_bundle_version`. So "bundle 1.2.0" is a new value of a string field in newly written manifests. It is not an edit to a document that defined what 1.1.0 meant. There is nothing in the repository whose contents previously said "1.1.0 means X" that now says something else. Bundle 1.1.0's published meaning is therefore unchanged **because nothing published it in a mutable place** — a weaker guarantee than a signed registry would give, but adequate, and unchanged from how 1.0.0→1.1.0 was handled.

Artifacts already on disk keep the string they were written with. I read all three committed runs (§3.2).

### 1.3 Amendment 3 — intake

`kind: "floorplan_page"` appears exactly once in the entire source tree: `src/pwa/intake.py:179`, inside the `.pdf` branch, applied to the outputs of `_render_pdf`. I verified the uniqueness by grepping the whole of `src/` for `"floorplan_page"` and for every `kind` assignment. The other classifications are untouched: the uploaded PDF itself stays `floorplan`; DXF's SVG preview is `kind: "other"` at `src/pwa/intake.py:186`; DWG produces no preview at all; `style_reference` is unchanged.

`_artifact(...)` gained a `schema_version: str = "1.0.0"` parameter (`src/pwa/intake.py:35`) and the project manifest is the only caller passing `"1.1.0"` (`src/pwa/intake.py:209-210`). The default preserves every other intake artifact at its existing version. That is the minimal shape of this change and it is the right one — a global bump would have been a mutation of unrelated contracts.

### 1.4 Amendment 4 — parser

The enforcement point is `src/pwa/floorplan/annotation_source.py`. Two module constants (lines 18-22):

```python
_APPROVED_ANNOTATION_IMAGE_KINDS = {"floorplan", "floorplan_page"}
_APPROVED_FORMATS_BY_KIND = {"floorplan": {"PNG", "JPEG"}, "floorplan_page": {"PNG"}}
```

and the check (lines 66-116, condensed):

```python
approved_formats = {"PNG", "JPEG"}
if source_inventory is not None:
    inventory_entry = source_inventory.get(image_ref)
    if inventory_entry is None:
        raise FloorplanError("PARSE_SOURCE_UNSUPPORTED", "... not part of the source inventory", ...)
    inventory_kind = inventory_entry.get("kind")
    if inventory_kind not in _APPROVED_ANNOTATION_IMAGE_KINDS:
        raise FloorplanError("PARSE_SOURCE_UNSUPPORTED", "... not an approved floorplan source artifact", ...)
    approved_formats = _APPROVED_FORMATS_BY_KIND[inventory_kind]
```

Ordering is correct and load-bearing: the inventory-membership check and the kind check both run **before** the image bytes are read or decoded. A `style_reference` never reaches Pillow. The byte-size bound (`MAX_SOURCE_RASTER_BYTES`) still fires before decode and still raises `PARSE_RESOURCE_LIMIT`, so the new classification did not displace the resource guard.

Format is then enforced against the per-kind set inside the decode block, with `image.load()` forcing actual pixel decode rather than trusting the header, and the bare-`except` path narrowed to `(OSError, SyntaxError, ValueError)` and re-raised as `PARSE_SOURCE_UNSUPPORTED`. `except FloorplanError: raise` sits ahead of it so the classified errors are not swallowed and relabelled.

One detail I checked specifically because it would have been an easy silent regression: the pre-existing dimension-mismatch check

```python
if width_px != payload["image"]["width_px"] or height_px != payload["image"]["height_px"]:
    raise ValueError("annotation image dimensions do not match the decoded source image")
```

sits **outside** the `try` (`src/pwa/floorplan/annotation_source.py:117-118`). Had it been inside, a dimension mismatch would now be silently reclassified as `PARSE_SOURCE_UNSUPPORTED` — a real contract change nobody approved. It is outside. Classification for that case is unchanged.

---

## 2. Acceptance criteria — all nine

**AC 1 — new schema version added, 1.0.0 frozen and byte-identical: MET.**
`schemas/project_manifest/v1/project_manifest-1.1.0.schema.json:1-47` exists; measured digest of `…-1.0.0.schema.json` equals the pinned `b8020d9c…ca33e6`; catalog exposes both (`tests/unit/test_contract_versions.py:79-80`). The three-delta property is asserted mechanically, not by eye: `tests/unit/test_contract_versions.py:99-104` reverts `$id`, reverts the const, removes the enum token, and asserts `schema_1_1 == schema_1_0`. That is the strongest available formulation of "additive" in this system and I would have written the same test.

**AC 2 — historical fixtures still validate; frozen 1.0.0 still rejects `floorplan_page`: MET, on the correct reading of the AC.**
This is the AC the mandate flagged, and it has a text defect underneath it. Ruling in §7. On the substance:

- Historical fixture validates under its declared version: `tests/unit/test_contract_versions.py:109-110` builds the envelope via `make_envelope` (whose default `schema_version` is `"1.0.0"` — `tests/conftest.py:14-36`) and asserts `validate_artifact(historical) == []`. **MET.**
- Payload shape forward-compatible: lines 112-114 relabel to 1.1.0 and assert clean. **MET.**
- `floorplan_page` accepted under 1.1.0: lines 116-124. **MET.**
- **Frozen 1.0.0 still rejects `floorplan_page`:** lines 125-126 relabel that same document back to 1.0.0 and assert `validate_artifact(...)` is truthy, i.e. returns errors. This is the security-relevant half of AC 2 and it is genuinely tested. **MET.**

The literal clause "validates … under 1.1.0" for a document *declaring* 1.0.0 is unsatisfiable by construction. I mark AC 2 **MET** rather than NOT MET because the defect is in the AC's wording, not in the implementation, and because the implementation satisfies every property the AC was evidently written to secure. A reviewer marking it NOT MET would be right on the letter and wrong on the substance — which is precisely why the text needs the repair in §7.

**AC 3 — bundle bumped to 1.2.0 in both producers: MET.**
`src/pwa/intake.py:26`; `src/pwa/floorplan/builder.py:214` (parse manifest) and `:915` (the second derived-manifest site). I checked that the bump did not leak: `src/pwa/floorplan/builder.py:225,263,927,990` still write `"1.0.0"` for the quality and assumptions artifacts, and `:253,936` still write floorplan_parse `"1.1.0"`. Only the two manifests moved.

**AC 4 — a two-page PDF yields exactly two `floorplan_page` PNG entries and nothing else changes: MET (static) / execution CANNOT_VERIFY.**
`tests/integration/test_plan001_intake.py::test_two_page_pdf_emits_only_two_floorplan_page_pngs` asserts the `floorplan_page` paths are exactly `[…/page-0001.png, …/page-0002.png]` and that each decodes as PNG. The all-formats test in the same file asserts manifest 1.1.0, bundle 1.2.0, DXF preview `kind: "other"`, and no `floorplan_page` for DXF. Statically the assertions are the right ones and the producer code can only satisfy them. I did not run them.

**AC 5 — page-2 selection proven by assertions that differ from page 1: MET.**
This is the AC the mandate singled out, and the correct standard is that the test must fail if the code silently annotated page 1. It would. `tests/integration/test_plan002_gc3_8.py::test_selected_pdf_page_two_binds_hash_dimensions_pixels_and_overlay_deterministically` makes five independent discriminating assertions, each in `assert X == page_two_value` **and** `assert X != page_one_value` form:

1. the overlay's embedded raster centre pixel equals page 2's centre pixel and differs from page 1's (the fixture paints page 1 red `(220,20,20)` at 1000×800 and page 2 blue `(20,20,220)` at 1000×900, so the two are separable in both colour and size);
2. `metadata["source_sha256"]` equals page 2's inventory hash and differs from page 1's — and I confirmed that field is actually emitted, at `src/pwa/floorplan/overlay.py:28-31` and embedded at `:124`;
3. the SVG root `width`/`height` equal page 2's render size and differ from page 1's (`src/pwa/floorplan/overlay.py:123`);
4. `normalization.source_height_px` equals page 2's height and differs from page 1's;
5. overlay bytes are byte-identical across two independent runs (determinism), which is a different property and correctly asserted separately.

The render sizes genuinely differ — the scale rule caps at 2.0 for both pages, giving 2000×1600 and 2000×1800 — and the test asserts `page_one_size != page_two_size` explicitly rather than assuming it. So the fixture cannot degenerate into a test that passes on either page. **The proof is by discriminating assertion, not by the run merely succeeding.** That is what the mandate asked for and it is what is there.

The orchestrator additionally reports a 480,000-pixel comparison from its own independently-built PDF, which corroborates but is not what I am relying on.

**AC 6 — disallowed kinds and formats classified `PARSE_SOURCE_UNSUPPORTED` with CLI 2 and no finalized run: MET (static) / execution CANNOT_VERIFY.**
`tests/integration/test_plan002_gc3_8.py::test_disallowed_annotation_inventory_or_format_is_classified_unsupported` is parametrised over five cases — reference missing from inventory, `style_reference`, `other`, the raw PDF (`floorplan` kind but PDF bytes), and a JPEG forged as `floorplan_page` — and each asserts all three properties: `cli_exit == 2`, `terminal_finding.code == "PARSE_SOURCE_UNSUPPORTED"`, `not result.final_run.exists()`. The third assertion is the one that matters most and it is present in every case.

**AC 7 — direct raster floorplan annotation still works: MET.**
Same file carries a PNG/JPEG success parametrization. The `approved_formats` default of `{"PNG","JPEG"}` when `source_inventory is None` (`src/pwa/floorplan/annotation_source.py:66`) preserves the no-inventory path unchanged.

**AC 8 — hash mismatch still `PARSE_SOURCE_HASH_MISMATCH`, not collapsed into unsupported: MET.**
The hash comparison at `src/pwa/floorplan/annotation_source.py:95-98` is a separate branch raising the separate code, positioned after the kind gate and independent of it. `test_annotation_image_hash_mismatch_remains_hash_mismatch` pins the behaviour. Detail in §6.

**AC 9 — PLAN-002 text updated to the approved wording: MET for the two named clauses; see F-NA6B-1 for the consequence.**
`docs/plans/PLAN-002-floorplan-parsing.md:119` carries the approved manifest sentence; `:203-227` carry the approved five-paragraph §6 replacement. `tests/unit/test_plan002_contract_text.py` pins both by whitespace-normalised substring, so a future silent edit to the plan breaks the suite — an unusual test, and a good one for a repository where the plan text is part of the contract.

One label imprecision, non-blocking: the amendment calls the manifest clause "section 5", but line 119 is inside §4/D-013 (§5 begins at line 139 and contains no such sentence). The target sentence was unambiguous and the implementer edited the right one. Worth correcting in the amendment if it is ever revised; not a mis-edit.

---

## 3. Is it actually additive?

Three independent checks, all passing.

### 3.1 Schema
Measured digest equals the pinned digest (§1.1). The revert-three-deltas equality test makes the property machine-checked rather than eyeballed. 1.1.0 is a new file; 1.0.0 was not opened.

### 3.2 Existing artifacts still readable by an old consumer
I read all three committed runs directly: `runs/RUN-20260806-140000-demo1/project/project_manifest.json` and `runs/RUN-20260806-060723-42cc1f60/project/project_manifest.json` (and the third by the same construction) each declare `"schema_version": "1.0.0"`, `"contracts_bundle_version": "1.0.0"`, and carry only `floorplan` / `style_reference` kinds. None contains `floorplan_page`. So:

- an old consumer pinned to 1.0.0 reads every existing artifact unchanged;
- a new consumer reads them too, because dispatch is on the declared version and 1.0.0 is still in the catalog;
- an old consumer encountering a *new* manifest fails loudly on the unknown declared version rather than silently mis-reading a `floorplan_page` entry as something it understands. That is the correct failure direction for an additive minor bump, and it is a genuine property of const-pinned `schema_version`, not an accident.

### 3.3 Bundle 1.2.0 is a new aggregate, not a mutation
No registry file exists to mutate (§1.2). Grep across `src/`, `docs/`, `contracts/`, `schemas/`, `tests/` for `contracts_bundle_version` finds only producers writing the string and consumers/tests asserting it. Nothing redefines what 1.1.0 meant.

**Ruling: the change is additive.** Old consumers can still read old artifacts; no old artifact changed meaning; no frozen file changed bytes.

---

## 4. Security

The mandate named five properties. All five hold.

**(a) `floorplan_page` is not assignable by intake to anything but PDF page renders.** The token appears at exactly one site in `src/`, `src/pwa/intake.py:179`, in the `.pdf` branch over `_render_pdf` outputs. There is no other producer, no config-driven kind, no user-supplied kind path into intake.

**(b) `style_reference` and `other` remain non-annotatable.** `_APPROVED_ANNOTATION_IMAGE_KINDS` is a closed two-element set (`src/pwa/floorplan/annotation_source.py:18`); membership is checked before any byte is read; both kinds are covered by dedicated negative test cases.

**(c) DXF SVG preview stays `other`.** `src/pwa/intake.py:186`, asserted in `tests/integration/test_plan001_intake.py`. This matters because an SVG promoted to an annotatable kind would put an XML parser on the trusted path. It was not promoted.

**(d) A `floorplan_page` whose bytes are not PNG is rejected.** `_APPROVED_FORMATS_BY_KIND["floorplan_page"] == {"PNG"}`, checked against `image.format` after `Image.open`, with `image.load()` forcing a real decode. The negative case is tested with JPEG bytes carrying a `floorplan_page` label — i.e. the test forges the manifest, which is exactly the adversary the check exists for. Note the asymmetry is deliberate and correct: `floorplan` still admits JPEG (a user upload legitimately may be), but `floorplan_page` is a *derived* artifact the system itself produced as PNG, so anything else in that slot is a forgery signal.

**(e) The documented residual trust boundary is not widened further.** The boundary the amendment documents is: manifest `kind` is authoritative and unauthenticated, so an attacker who can write the source manifest can relabel an entry. What this round adds to that attacker's reach is bounded by (d) — they can only get a **PNG that is already in the inventory and whose content hash matches** to be annotated. They cannot introduce new bytes (`content_hash` is still verified, §6), cannot reach a non-PNG through the `floorplan_page` door, and cannot reach any kind outside the two-element allowlist.

Two further containment facts I verified rather than assumed, because both would have widened the boundary quietly:

- The source preflight at `src/pwa/floorplan/builder.py:638-646` is **unchanged**. It still requires exactly one `kind == "floorplan"` entry and still rejects duplicate inventory paths. Adding N `floorplan_page` entries does not perturb the unique-floorplan identity check, because that check filters on `kind == "floorplan"` and `floorplan_page` is a distinct token — not a prefix match, not a `startswith`. Had that filter been written loosely, a two-page PDF would have broken source identity for every run. It is written tightly.
- A manifest that declares 1.0.0 but contains a `floorplan_page` entry is rejected as an invalid source contract before the parser ever looks at kinds, because validation dispatches on the declared version and frozen 1.0.0's enum has no such token. The attacker cannot smuggle the new kind into an old-declared manifest.

**Ruling: no security regression. The blast radius of a forged manifest is unchanged in kind and bounded in degree exactly as the amendment documents.**

---

## 5. Error classification

| Condition | Required code | Actual | Anchor |
|---|---|---|---|
| Reference not in source inventory | `PARSE_SOURCE_UNSUPPORTED` | ✅ | `src/pwa/floorplan/annotation_source.py:72-76` |
| Inventory kind not allowlisted | `PARSE_SOURCE_UNSUPPORTED` | ✅ | `:78-83` |
| Decoded format wrong for kind | `PARSE_SOURCE_UNSUPPORTED` | ✅ | `:104-108` |
| Bytes do not decode at all | `PARSE_SOURCE_UNSUPPORTED` | ✅ | `:112-116` |
| Content hash disagreement | `PARSE_SOURCE_HASH_MISMATCH` | ✅ unchanged | `:95-98` |
| Over the raster byte bound | `PARSE_RESOURCE_LIMIT` | ✅ unchanged | `:87-93` |

**The two codes cannot collapse.** They are raised from disjoint branches with no shared exception path: the hash branch is a plain `!=` comparison outside the decode `try`, and the decode `try` re-raises `FloorplanError` untouched (`except FloorplanError: raise` precedes the broad clause) so a hash error can never be caught and relabelled as unsupported. The ordering — kind gate, then byte bound, then hash, then decode — means a wrong-kind file with a bad hash reports *unsupported*, which is the correct precedence: the kind violation is the more specific and more security-relevant fact.

`contracts/error_codes.md` is byte-identical to its pinned digest. No new token was introduced; `PARSE_SOURCE_UNSUPPORTED` already existed in the vocabulary and this round only widened which conditions map to it. That is the cheapest possible form of this change and the right one.

---

## 6. R-1

**Closed.** `src/pwa/floorplan/cli.py:20-36`: the residual-state diagnostic `print(..., file=sys.stderr)` now sits **inside** the `try`, ahead of `except Exception: return 2`. A failing stderr write therefore yields exit 2 instead of an uncaught traceback.

The obvious objection to this fix is that moving a write inside a broad `except` could mask a *different* exit code — if the residual path could ever produce exit 1 or 3, a stderr failure would silently rewrite it to 2. It cannot: `residual_state` is only ever populated by `_staged_operational_result` (`src/pwa/floorplan/builder.py:441-459`), which hardcodes `cli_exit = 2`. The exit code the fix can mask is the exit code it returns. The fix is sound.

**The test patches the right thing.** `tests/integration/test_plan002_cli.py::test_main_returns_2_when_residual_diagnostic_stderr_write_raises_oserror` monkeypatches `pwa.floorplan.cli.sys.stderr` with a `RaisingStderr` whose `write` raises `OSError`, and asserts `exit_code == 2`. It does **not** patch `print`. That distinction is the whole point of the test — patching `print` would prove only that the call is inside a `try`, whereas patching the stream exercises the actual failure mode (a closed pipe, a full disk, a detached console) through the real `print` machinery. I checked for a `print` patch specifically and there is none.

---

## 7. Ruling on F-NA6-1 (defect in the APPROVED TEXT)

**The orchestrator is right.** AC 2's clause

> Every historical 1.0.0 fixture validates unchanged under its declared version and under 1.1.0.

is unsatisfiable in the second half, and unsatisfiable *by construction*, not by implementation choice. Every schema in this system pins its own `schema_version` as a `const`. A document declaring `"schema_version": "1.0.0"` therefore fails 1.1.0's const on its first keyword, forever, regardless of payload. No implementation could satisfy the clause as literally written without abandoning the const-pinning that makes exact-version dispatch trustworthy — and that pinning is load-bearing for the security property in §4 (it is what stops a `floorplan_page` entry from being smuggled into a 1.0.0-declared manifest).

**The implementer's relabel-then-validate interpretation is the correct one.** The clause is evidently reaching for *payload forward-compatibility*: the shape of an old manifest is still legal under the new schema, so nothing about the old artifact's structure was outlawed. Relabelling the envelope and validating is exactly how you test that proposition when the envelope carries a version const. `tests/unit/test_contract_versions.py:109-114` does it in both steps — declared-version validation first, then relabelled validation — which keeps the two distinct properties distinct rather than conflating them. I would have written the same test, and I can construct no alternative reading of the clause that is both satisfiable and meaningful.

**The proposed repair is adequate.** The orchestrator's replacement —

> Every historical 1.0.0 fixture continues to validate unchanged under its declared version, and its payload shape is valid under 1.1.0 when relabelled to that version. A document declaring `schema_version: "1.0.0"` is not expected to validate against the 1.1.0 schema, whose `schema_version` const forbids it by construction.

— states the satisfiable property, states the non-property explicitly so a future literal reader is not misled, and gives the reason. It changes no code and no test; the existing test already proves exactly what the repaired sentence claims.

**One suggested addition, non-blocking.** The repair speaks of "fixtures". The population that actually matters for the additivity claim is the *committed artifacts* — the three `runs/*/project/project_manifest.json` files, which are real historical outputs rather than test fixtures. I would extend the first sentence to "Every historical 1.0.0 fixture **and every committed 1.0.0 run artifact**…". Without it, the AC constrains only the fixture and leaves the real artifacts uncovered by the letter of the criterion, even though they are in fact covered in practice.

**Procedurally the orchestrator was also right not to apply it.** The amendment cleared a cross-provider gate; the repair must clear the same gate. My ruling is: the repair is correct, adopt it (with or without my addition), and route it through the same approval path. It is a wording fix to a criterion, and it changes nothing about whether NA-6 is acceptable — which is why F-NA6-1 does not block this verdict.

---

## 8. F-NA6B-1 — my own finding, also against plan text, not code

**Finding (text defect, needs the same gate).** The amendment authorised edits to exactly two clauses of PLAN-002. Those two are correct. But three *other* statements in the same document describe the manifest and bundle versions, were not in the amendment's scope, and are now false:

- `docs/plans/PLAN-002-floorplan-parsing.md:34` — "bounded update to future intake manifests from contracts bundle 1.0.0 to 1.1.0 after D-012 approval"
- `docs/plans/PLAN-002-floorplan-parsing.md:90` — "…declaring bundle 1.1.0; it never rewrites the source run. Future intake runs declare 1.1.0 after approval."
- `docs/plans/PLAN-002-floorplan-parsing.md:102` — in the D-013 tree: `project/project_manifest.json      # new schema 1.0 artifact, bundle 1.1`

Intake and the builder now write manifest 1.1.0 / bundle 1.2.0. All three lines say otherwise.

**This is not an implementation defect, and I want to be precise about that.** The implementer was *forbidden* to touch clauses the amendment did not name; editing these three would itself have been scope creep and I would be reporting it as a finding in the opposite direction. The correct behaviour was to leave them and let the reviewer raise it. That is what happened. The defect is that the amendment's scope was drawn one clause too narrowly.

**Why it matters enough to record.** §6 and the code now agree (§10), but the document as a whole does not agree with itself. `tests/unit/test_plan002_contract_text.py` pins the two corrected clauses, so the *correct* text is now protected while the stale text sits unprotected three sections earlier — which is the configuration most likely to mislead a future reader who greps for "bundle" and finds line 34 first.

**Recommended disposition:** a follow-up text-only amendment updating these three lines to 1.1.0 / 1.2.0, through the same gate, bundled with the F-NA6-1 repair. No code changes. Not a blocker for GC3-8.

---

## 9. Regression hunt

Everything the mandate named, plus the paths I judged most likely to break silently.

| Surface | Method | Result |
|---|---|---|
| Golden canonical projection hash | `tests/golden/` contains no `project_manifest` reference; nothing in the geometry, normalization or projection path is touched by this diff | **No change possible from this round.** Orchestrator separately reports the hash still `sha256:e5041ddc…b7e77e` |
| Overlay bytes | `src/pwa/floorplan/overlay.py` is not in the diff; the sanitized re-encode pins JPEG q95 / PNG compress_level 6; the new gc3_8 test asserts byte-identical overlays across two runs | **Unchanged; determinism additionally re-asserted** |
| `limits_snapshot()` / `config.py` | digest comparison — byte-identical | **No new key** |
| Dependencies | `pyproject.toml`, `uv.lock` — byte-identical | **None added** |
| `contracts/error_codes.md` | byte-identical | **Unchanged** |
| Source preflight | read `src/pwa/floorplan/builder.py:596-665` | **Unchanged**; unique-`floorplan` and unique-path checks intact (§4) |
| Can `parse_run()` now raise on a new path? | traced every new raise | **No** — detail below |

**On `parse_run()` raising.** This is the regression that would matter most, because an escaping exception turns a classified CLI 2 into a traceback. Every new `FloorplanError` is raised inside the block guarded at `src/pwa/floorplan/builder.py:1063`, where `except FloorplanError` routes to `_staged_operational_result(finding=exc.finding)` → `cli_exit = 2`. I also traced the one non-`FloorplanError` that the new `image.load()` call can produce: Pillow's `DecompressionBombError` derives from `Exception`, not from `OSError`/`ValueError`, so it is *not* caught by the narrow clause in `annotation_source.py` — but it **is** caught by the broad clause at `src/pwa/floorplan/builder.py:1104-1111`, which lists `DecompressionBombError` and `DecompressionBombWarning` explicitly. So it degrades to a generic operational CLI 2 rather than escaping. No new escape path exists.

**Observation (non-blocking, not a finding).** That broad clause covers `OSError, ValueError, UnicodeDecodeError, JSONDecodeError, DecompressionBomb{Error,Warning}` but **not `KeyError`**. The new code introduces one dictionary indexed by a value validated against a different collection:

```python
if inventory_kind not in _APPROVED_ANNOTATION_IMAGE_KINDS: raise ...
approved_formats = _APPROVED_FORMATS_BY_KIND[inventory_kind]
```

Today the two collections have identical membership, so the `KeyError` is unreachable. It becomes reachable the moment someone adds a token to the allowlist and forgets the format map — and it would escape as a traceback rather than a classified failure. Cheapest durable fix if it is ever touched: `_APPROVED_ANNOTATION_IMAGE_KINDS = frozenset(_APPROVED_FORMATS_BY_KIND)`, which makes the divergence structurally impossible. I am not asking for it in this round; it is not a defect against the approved spec and the code is correct as written.

---

## 10. Evidence integrity and scope

**Nothing under `evidence/` was rewritten.** `git show --stat 1f18fac` shows the NA-6 commit **adds** two evidence files (the implementation report and the orchestrator verification) and modifies none. The only modification to a pre-existing evidence file anywhere in the branch is NA-7's own commit `761a6ab`, which **appends** 46 lines to `ac13-provenance-enumeration-draft-20260811.md` after line 96, under an explicit in-file note that it was "appended rather than folded in, because this file is committed evidence". That is the correct handling of an immutable-by-convention file and it is out of NA-6's scope anyway.

**PLAN-002 edits are confined to the clauses the amendment names.** The diffstat shows `docs/plans/PLAN-002-floorplan-parsing.md | 30 ++-`, and the changed regions are line 119 and lines 203-227 — the manifest sentence and the §6 replacement. No other clause was edited, including the three stale ones in §8, which the implementer correctly left alone. **No scope creep.**

The full diffstat is 15 files, +919/−35: five source/schema files, seven test files, one plan file, two new evidence files. Every file in it is accounted for by the amendment. Nothing unexplained.

---

## 11. Can GC3-8 be marked CLOSED?

**Yes.** All four amendments are implemented as approved, all nine ACs are MET, the change is additive on all three tests, the security properties hold, the error vocabulary is intact and unwidened, and R-1 is closed with a test that exercises the real failure mode.

**Do PLAN-002 §6 and the code agree?** **Yes, for §6 specifically.** §6 has promised annotation of a selected intake-generated PDF page since the plan was approved, and until this round the parser had no path to it — `floorplan_page` did not exist as a kind, so a page render could not be an annotation source. It can now, and the negative paths are classified rather than collapsed into an unlabelled operational failure. Lines 203-227 describe what `src/pwa/floorplan/annotation_source.py` and `src/pwa/intake.py` actually do.

**Two carried items, neither blocking:**
- **F-NA6-1** — approved-text repair for AC 2. Adopt via the same gate. My addition in §7 is optional.
- **F-NA6B-1** — three stale statements at `docs/plans/PLAN-002-floorplan-parsing.md:34,90,102`. Text-only follow-up, same gate. Best bundled with F-NA6-1 into one small text amendment.

Both are defects in *text that already passed a gate*, which is why neither can be fixed by the implementer and neither reduces this verdict. **GC3-8: CLOSE.** The plan document's internal consistency is a separate, open, text-only item.

---

## 12. CANNOT_VERIFY, with the commands I would have run

I executed no code. These are the items whose verification requires execution, each with the exact command. Where the orchestrator reports having run the equivalent, I note it as corroboration I did not produce and did not rely on.

| Item | Command I would have run | Corroboration |
|---|---|---|
| Full suite green, added-test count | `.venv/Scripts/python.exe -m pytest -q` | Orchestrator: 369 passed, exit 0, baseline 356 |
| AC 2 against the real committed artifacts | `PYTHONPATH=src .venv/Scripts/python.exe -c "…load each runs/*/project/project_manifest.json, validate_artifact under declared version and after relabel to 1.1.0…"` — attempted, **permission denied**, never executed | Orchestrator: all three `declared_ok=True`, `as_1.1.0=False` |
| AC 4/5/6 end-to-end behaviour | `.venv/Scripts/python.exe -m pytest -q tests/integration/test_plan002_gc3_8.py tests/integration/test_plan001_intake.py` | Orchestrator: 6/6, 6/6, 5/5 |
| R-1 runtime behaviour | `.venv/Scripts/python.exe -m pytest -q tests/integration/test_plan002_cli.py -k residual_diagnostic` | Orchestrator: 1/1 |
| Golden hash unchanged | `.venv/Scripts/python.exe -m pytest -q tests/golden` | Orchestrator: hash still `sha256:e5041ddc…b7e77e` |

Static substitutes were used throughout: for AC 2 I read the three committed manifests directly and reasoned against the frozen schema's `schema_version` const and `kind` enum; for the boundaries I compared digests; for the behavioural ACs I read the assertions and confirmed the producer code can satisfy them only in the intended way.

---

## 13. Audit list — every Bash command I ran

All reads. None touched the index, HEAD, the working tree, or any file. Listed in execution order; #17 was rejected by the permission layer and never ran.

1. `ls contracts/ && ls schemas/ && ls schemas/project_manifest/v1/`
2. `grep -rn "1\.1\.0" contracts/README.md schemas/README.md` ; `grep -rn "contracts_bundle\|bundle" contracts/README.md schemas/README.md`
3. `grep -rn "CONTRACTS_BUNDLE_VERSION\|contracts_bundle_version" --include=*.py --include=*.md --include=*.yaml --include=*.json src/ docs/ contracts/ schemas/ tests/`
4. `grep -n "FloorplanError\|except \|def parse_run\|def _failed\|source_inventory\|_annotation_source\|extract_with_image_snapshot" src/pwa/floorplan/builder.py`
5. `grep -rln "runs/RUN-\|REPO_ROOT / \"runs\"" tests/` ; `ls runs/`
6. `sha256sum schemas/project_manifest/v1/project_manifest-1.0.0.schema.json schemas/project_manifest/v1/project_manifest-1.1.0.schema.json contracts/error_codes.md pyproject.toml uv.lock src/pwa/floorplan/config.py`
7. `git status --porcelain && git log --oneline -3 && git diff --stat main...HEAD`
8. `grep -rn '"1\.0\.0"\|"1\.1\.0"\|"1\.2\.0"' src/`
9. `ls .venv/Scripts/python.exe` ; `ls runs/RUN-20260806-140000-demo1/project/`
10. `sed -n '300,345p' src/pwa/floorplan/builder.py` ; `grep -n "_source_binding" -A 40 src/pwa/floorplan/builder.py`
11. `sed -n '95,140p' tests/integration/test_plan002_parse_run.py`
12. `grep -n "1\.0\.0\|1\.1\.0\|1\.2\.0\|bundle" docs/plans/PLAN-002-floorplan-parsing.md`
13. `head -c 900 runs/RUN-20260806-140000-demo1/project/project_manifest.json` ; `head -c 900 runs/RUN-20260806-060723-42cc1f60/project/project_manifest.json`
14. `grep -n "^## \|^### " docs/plans/PLAN-002-floorplan-parsing.md`
15. `git show --stat --oneline 1f18fac | cat` ; `git show --stat --oneline 761a6ab | cat`
16. `grep -rn '\["kind"\]\|"kind"\|kind ==' src/ --include=*.py` ; `ls tests/golden/` ; `grep -rln "project_manifest" tests/golden/`
17. **REJECTED, never executed:** `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -B -c "…validate the three committed run manifests…"`
18. `grep -n "source_sha256\|metadata\|href\|data:\|_MEDIA_TYPES" src/pwa/floorplan/overlay.py` ; `grep -n "_MEDIA_TYPES" -A 5 src/pwa/floorplan/builder.py`

Two `git` commands appear (#7, #15). Both are read-only reporting commands — `status --porcelain`, `log --oneline`, `diff --stat`, `show --stat` — with no writing subcommand, no checkout, no index operation.

---

## 14. Summary

**ACCEPT.** The implementation matches the approved amendment on all four parts plus R-1, all nine acceptance criteria are MET, and I found no defect in the code. The change is genuinely additive: the frozen 1.0.0 schema is byte-identical to its pinned digest, the delta to 1.1.0 is exactly the three authorised differences and that property is machine-checked, and every committed artifact still validates under the version it declares. The security allowlist is enforced before any byte is read, `floorplan_page` has exactly one producer and it is the PDF page-render path, and a forged `floorplan_page` carrying non-PNG bytes is rejected. The two source error codes remain disjoint and `contracts/error_codes.md` is unchanged.

Two findings, both against **text that already passed a gate** and therefore neither fixable by the implementer nor blocking: **F-NA6-1** (I agree with the orchestrator; the relabel-then-validate reading is correct; the proposed repair is adequate, optionally extended to cover committed run artifacts) and **F-NA6B-1** (three stale bundle/version statements at `docs/plans/PLAN-002-floorplan-parsing.md:34,90,102`). Both should go through the same cross-provider gate as one small text-only amendment. One non-blocking observation: `KeyError` is absent from the broad except tuple in `parse_run()`, currently unreachable.

**GC3-8 can be marked CLOSED.** PLAN-002 §6 and the code agree. The plan document's internal consistency is a separate open item.
