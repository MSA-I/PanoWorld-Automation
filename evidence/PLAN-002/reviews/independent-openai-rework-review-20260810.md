<!-- Independent cross-provider review of the PLAN-002 rework.
     PROVIDER: openai | MODEL_ID_EXACT: gpt-5.6-sol | EFFORT: EXTRA / xhigh
     Route: OmniRoute local gateway (codex/gpt-5.6-sol-xhigh), streaming.
     Reviewer had no filesystem or tool access; the review package (spec, full
     floorplan package source, contracts.py, rework report, tracked diff and six
     test files) was supplied inline by the orchestrator.
     NOTE: the first response was truncated by the output-token limit mid-item-5
     of the final gate-conditions list. The completed list was recovered in a
     bounded follow-up request and is appended below under 'Recovered tail'. -->
# VERDICT: `NEEDS_REWORK`

The two original proof-of-concepts are addressed, but the rework is not ready for the human approval gate. There is a new **CRITICAL arbitrary-write containment defect** through `--parse-run-id`, the rewritten source containment still does not satisfy the reparse-point requirement, and several contract/traceability defects remain.

The most serious current issue is that an absolute or traversing `parse_run_id` controls both staging and final filesystem locations without validation.

---

## 1. Per-finding verification

### CRITICAL findings

| Finding | Status | Verification |
|---|---|---|
| **C-1 code/security: absolute `source_run` containing `..`** | **PARTIALLY_CLOSED** | The exact attack is closed by `runs.py::resolve_contained_run()`: `if any(part == ".." for part in candidate.parts): raise ValueError(...)`, and containment is then checked with `resolved.relative_to(runs_root)`. However, AC-17 is still not fully met because both the root and candidate are resolved **before** reparse-point checks: `runs_root = Path(runs_root).resolve(strict=True)` and `resolved = candidate.resolve(strict=False)`. This erases traversed symlinks/junctions before `is_link_or_reparse(cursor)` sees them. Example: `runs/alias` is a junction to `runs/actual`; `--source-run runs/alias/RUN-1` resolves to `runs/actual/RUN-1`, and the code checks `actual`, not `alias`, so the junction is accepted despite the explicit requirement to reject it. A `runs_root` that is itself a junction is likewise never checked. |
| **C-1 spatial: duplicate openings** | **CLOSED** | `validate.py::validate()` now uses `seen_openings` and keys it as `key = (opening.type, opening.wall_id, opening.center, opening.width_m)`, emitting `PARSE_DUPLICATE_ENTITY` on reuse. That is the same tuple encoded by `normalize.py::_opening_identity()`: kind, wall ID, center and width. Two coincident doors therefore cannot remain finding-free or G1-eligible. |

### Code/security MAJOR findings

| Finding | Status | Verification |
|---|---|---|
| **M-1: manifest paths and ancestor reparse points** | **PARTIALLY_CLOSED** | Inventory paths now pass through `runs.py::resolve_contained_relpath()`, and absolute paths and raw `..` components are rejected. However, `joined.resolve(strict=False)` resolves away in-root symlinks/junctions before the ancestor walk, so a contained reparse point is accepted if its target remains under the root. In addition, `builder.py::parse_run()` reads `project_manifest.json` and `input_quality_report.json` directly with `manifest_path.read_text(...)` and `quality_path.read_text(...)`; their `project` ancestor and artifact leaves are not passed through `resolve_contained_relpath()`. A manifest symlink to a valid JSON document outside the source run is therefore read before any rejection. The implementation of `pwa.files.is_link_or_reparse` and `copy_immutable` was not supplied, so their internal behavior cannot be verified. |
| **M-2: unknown manifest units caused a second exception** | **CLOSED** | `_failed_scale_artifacts()` now makes `normalization_block` optional. For DXF with manifest units `"unknown"`, `resolved_source_unit_scale_m` is `None` and normalization is omitted rather than fabricating a value or raising. The originating `PARSE_UNITS_MISMATCH` can therefore finalize as CLI 3. |
| **M-3: missing/malformed source manifest escaped `parse_run()` and leaked a path** | **CLOSED** for the reported cases | `builder.py::parse_run()` wraps both reads and JSON decoding in `except (OSError, json.JSONDecodeError)` and returns a generic CLI-2 diagnostic without inserting the exception text or path. There are still other uncaught preflight inputs, discussed below, but the two reported missing/malformed-manifest cases are fixed. |
| **M-4: failed artifacts falsely bound a nonexistent overlay** | **CLOSED** | `_failed_scale_artifacts()` builds `failed_payload` with only units, scale, rooms, walls and openings; it adds normalization conditionally but never adds `"overlay"`. Its parse report instead records `{"overlay_omitted_reason": ...}`. There is no all-zero overlay hash or false path in these omitted-overlay outcomes. |
| **M-5: timeout killed only the direct child** | **CLOSED**, with portability caveat | POSIX starts the worker with `start_new_session=True` and kills `os.killpg(os.getpgid(proc.pid), SIGKILL)`. Windows starts a new process group and invokes `taskkill /PID <pid> /T /F`, falling back to direct `proc.kill()` only if `taskkill` returns nonzero. I do not see a normal POSIX PID-reuse problem: the unreaped child retains its PID until `proc.wait()`. The Windows path depends on the external OS utility `taskkill`, and the supplied test mocks that invocation rather than killing a real descendant, but the implementation does address the original direct-child-only defect. |
| **M-6: 1 MiB log cap truncated legal worker JSON** | **PARTIALLY_CLOSED** | `_run_worker()` no longer uses `MAX_WORKER_STDIO_BYTES` for `worker-output.json`; it uses `MAX_DXF_BYTES`. That fixes the cited approximately 1.2 MiB result. But `_bounded_text()` silently truncates anything over 50 MiB, after which `json.loads()` reports malformed JSON. A valid, ג‰₪50 MiB R12 DXF with exactly 200,000 minimal entities on a long unknown layer can produce more than 50 MiB of repeated finding JSON while remaining at the accepted entity limit (`len(modelspace) > MAX_DXF_ENTITIES`, not `>=`). The result becomes operational CLI 2 instead of the required warning/partial or resource-limit domain outcome. A separate, explicitly sized result-channel bound or streaming protocol is needed. |
| **M-7: security-sensitive DXF kinds on unknown layers became warnings** | **CLOSED** | `dxf_worker.py::_scan_layout()` checks `kind in _SECURITY_UNSUPPORTED_KINDS` before `layer not in _KNOWN_LAYERS`. The set includes `ARC`, `SPLINE`, `INSERT`, `IMAGE`, and `OLE2FRAME`; these therefore produce `PARSE_UNSUPPORTED_FEATURE` regardless of layer. |
| **M-8: duplicate-schema test did not reach duplicate branches** | **CANNOT_VERIFY** | Production branches are present in `contracts.py::load_schema_catalog()`: `if key in out: raise ValueError("Duplicate schema version pair...")` and `if schema["$id"] in ids_seen: raise ValueError("Duplicate schema $id...")`. However, `tests/unit/test_contract_versions.py`, containing the claimed corrected tests, was not supplied. A passing aggregate test count does not prove those tests construct fixtures that reach the intended branches. |
| **M-9: AC-3 had zero assertions** | **CANNOT_VERIFY** | The claimed replacement test is in `tests/integration/test_plan002_failure_matrix.py`, which was not supplied. The shown implementation appears read-only toward the source run during ordinary execution, but M-9 was specifically a test-evidence defect, so the actual assertions are required to close it. |
| **M-10: private paths/user name in tracked evidence** | **CLOSED** based on stipulated evidence | The orchestrator independently verified that no path or OS-user-name leak remains. Evidence files were not supplied for independent inspection, but this was explicitly given as a fact not requiring reconfirmation. |

### Spatial MAJOR findings

| Finding | Status | Verification |
|---|---|---|
| **M-2: opening matching checked only the center, not the line** | **PARTIALLY_CLOSED** | DXF spans are now normalized into `NormOpening.span_m`, and both `normalize.py::_span_collinear_with_wall()` and `validate.py::_span_collinear_with_wall()` require each endpoint to be within `OPENING_OFFSET_M` of the wallג€™s infinite line. This closes the reported 0.9 m, 45-degree example. It does not impose a meaningful angular bound for short openings: a 0.04 m segment perpendicular to the wall, centered on it, with endpoints at ֲ±0.02 m passes both endpoint checks and can produce a complete result. Width also remains the raw span length rather than wall projection; the deferral rationale is not generally valid, as detailed below. |
| **M-3: non-adjacent collinear overlap and T-touch were missed** | **CLOSED** | `_validate_room()` now calls `seg_intersects_non_adjacent()`, which explicitly handles collinear overlap and all four endpoint-on-segment cases. Adjacent edge pairs are skipped before this predicate, so ordinary adjacent polygon edges do not become false positives. A single shared endpoint between non-adjacent edges is not flagged by the collinear-overlap branch, but such geometry repeats a polygon vertex and is rejected earlier by `len(set(points)) != len(points)`. |
| **M-4: DXF source layer was derived from detections; rooms/doors empty** | **PARTIALLY_CLOSED** | `builder.py::_source_binding()` now builds source primitives from `raw.walls`, `raw.rooms`, and raw opening spans, independently of normalized provenance. `overlay.py::_dxf_svg()` also emits detected rooms, doors and windows. However, bounds are still derived only from source primitives: `xs = [...] for primitive in primitives` and likewise for `ys`. A disagreeing detection outside source bounds can be clipped and invisible. The supplied test itself renders a detected endpoint at x=8200 into a viewBox only 4400 units wide. Thus the source/detection comparison remains only partially falsifiable visually. |
| **M-5: JPEG embedded as `data:image/png`** | **CLOSED** | `builder.py::_source_binding()` derives PILג€™s decoded format through `_MEDIA_TYPES = {"PNG": ..., "JPEG": ...}` and passes `media_type`; `_raster_svg()` emits `href="data:{media_type};base64,..."`. |

---

## 2. Blocking regressions and newly identified defects

### CRITICAL ג€” `parse_run_id` permits arbitrary staging writes outside `runs_root`

**File/function:** `src/pwa/floorplan/builder.py::parse_run()`

Quoted code:

```python
final_run = runs_root / parse_run_id
staging_run = runs_root / ".staging" / parse_run_id
...
staging_run.mkdir(parents=True, exist_ok=False)
...
copy_source_inventory(source_run, staging_run, source_manifest)
```

There is no run-ID validation or destination containment check.

**Concrete failure scenario:**

- `runs_root=/srv/pwa/runs`
- valid source run and annotation
- `parse_run_id=/tmp/pwa-write`

Because joining a `Path` with an absolute component discards the prefix, both `final_run` and `staging_run` become `/tmp/pwa-write`. The parser creates that directory and copies source inventory and audit artifacts there before `_artifact()` has an opportunity to reject the invalid run ID. A generic exception then writes `parse/parse-report.json` there as well.

A relative value such as `../../outside` can similarly escape. This is an arbitrary new-directory write and source-data copy outside the configured run boundary.

**Required fix:** validate the raw ID against the approved run-ID grammar before constructing any path, reject separators/anchors/drive components, and independently prove both staging and final destinations are contained below `runs_root`.

---

### MAJOR ג€” Annotation integrity and lineage are not verified or recorded

**Files/functions:**  
`src/pwa/floorplan/annotation_source.py::AnnotationSource.extract()`  
`src/pwa/floorplan/builder.py::parse_run()`

Annotation validation is only schema validation:

```python
errors = validate_artifact(document)
```

There is no:

```python
document["content_hash"] == compute_content_hash(document)
```

The generated `floorplan_parse` inputs contain only the derived manifest and quality report:

```python
inputs=[
    {"artifact_id": derived_manifest["artifact_id"], ...},
    {"artifact_id": derived_quality["artifact_id"], ...},
],
```

The annotation artifact ID/hash is omitted, despite D-013 explicitly requiring that additional binding.

**Concrete failure scenario:**

1. Create a valid annotation artifact and compute its hash.
2. Change a wall or opening coordinate without updating `content_hash`.
3. Supply it to `parse_run()`.

The changed geometry is accepted because the hash is never recomputed, and the completed parse artifact contains no input binding identifying which annotation produced it. The shown tests even construct annotations with an all-zero content hash.

This breaks immutable lineage and AC-13.

---

### MAJOR ג€” Copied inventory is not rehashed after copying

**Files/functions:**  
`src/pwa/floorplan/builder.py::parse_run()`  
`src/pwa/floorplan/runs.py::copy_source_inventory()`

The source is hashed during preflight:

```python
if sha256_file(input_path) != item["sha256"]:
    ...
```

It is later copied:

```python
copy_immutable(source_item, destination_item)
```

No destination hash is recomputed before the derived manifest is finalized.

**Concrete failure scenario:**

- The source style file passes the preflight hash.
- A concurrent process changes it before `copy_source_inventory()`.
- The modified style bytes are copied.
- Parsing the unchanged floorplan succeeds.
- The derived manifest retains the old style hash and the run finalizes `complete`.

The finalized derived inventory is therefore not actually bound to its manifest, contrary to D-013ג€™s ג€reverified hashesג€ requirement.

---

### MAJOR ג€” Annotation may bind to a style image instead of the floorplan

**File/function:** `src/pwa/floorplan/annotation_source.py::AnnotationSource.extract()`

Quoted code:

```python
if source_inventory is not None and image_ref not in source_inventory:
    raise ValueError(...)
```

Membership and hash are checked, but inventory `kind` is not.

**Concrete failure scenario:**

- Source inventory contains:
  - `floor.png`, kind `floorplan`
  - `style.jpg`, kind `style_reference`
- Both are 2000ֳ—1800.
- Annotation names `style.jpg` as `source_image_ref` with its correct hash and dimensions.

The parser accepts the style image, applies the floorplanג€™s manifest scale, embeds it in the overlay, and can return `complete`. Section 6 permits only the floorplan raster or an explicitly selected PDF page derivative.

---

### MAJOR ג€” Additional invalid preflight inputs still escape `parse_run()`

**File/function:** `src/pwa/floorplan/builder.py::parse_run()`

Quoted code:

```python
if validate_artifact(source_manifest) or validate_artifact(source_quality):
```

`validate_artifact()` raises for a document with no string schema ID/version or an unknown schema/version; that call is outside an exception handler.

Likewise:

```python
if Path(annotation).stat().st_size > MAX_ANNOTATION_BYTES:
```

is outside the main staging `try`.

**Concrete failure scenarios:**

1. `project_manifest.json` contains valid JSON `{}`.  
   `validate_artifact({})` raises `ValueError` out of `parse_run()` instead of returning `ParseRunResult(cli_exit=2)`.

2. `--annotation /private/missing.json`.  
   `accepts()` succeeds based on `.json`, then `stat()` raises `FileNotFoundError` out of `parse_run()`.

`cli.main()` suppresses these through its broad defense-in-depth catch, but the reported requirement and M-3 were specifically that `parse_run()` classify reachable failures rather than raise.

---

### MAJOR ג€” Unsupported DXF semantics can be hidden by cardinality failure

**Files/functions:**  
`src/pwa/floorplan/dxf_worker.py::_scan_layout()`  
`src/pwa/floorplan/builder.py::_prevalidate_raw()`

Unsupported entities are accumulated in `raw.errors`, but `_prevalidate_raw(raw)` runs before those findings are combined:

```python
_prevalidate_raw(raw)
...
findings = sort_findings([*raw.errors, *validate(geometry), *raw.unmapped])
```

**Concrete failure scenario:**

- DXF contains one valid closed `PWA-ROOM`.
- Its only wall-like entity is an `ARC` on `PWA-WALL`.

The worker records `PARSE_UNSUPPORTED_FEATURE` and emits zero walls. `_prevalidate_raw()` immediately raises `PARSE_EMPTY_GEOMETRY`; the exception path discards `raw.errors`. The finalized diagnostic set reports only empty geometry rather than the unsupported ARC, violating the required disposition and finding precedence.

---

### MAJOR ג€” DXF overlay rendering is unusable for supported metre-unit DXFs

**File/function:** `src/pwa/floorplan/overlay.py::_dxf_svg()`

Newly rendered openings use a fixed source-coordinate radius:

```python
f'<circle ... r="20" .../>'
```

ID and confidence labels have no explicit scale-dependent font size.

**Concrete failure scenario:**

- Valid `$INSUNITS=6` DXF.
- Source bounds are an 8 m ֳ— 6 m room.
- ViewBox is approximately 8.8 ֳ— 6.8 source units.
- Every door/window is rendered with a 20 m radius circle, and default text sizing is also enormous relative to the viewBox.

The opening and label layers obscure or clip most of the plan, so AC-14 is not satisfied for one of the three explicitly supported unit systems. Existing tests exercise millimetres only.

The bounds also exclude detected geometry, so substantial source/detection disagreement can be clipped.

---

### MAJOR ג€” JPEG EXIF/private metadata is copied into the SVG overlay

**Files/functions:**  
`src/pwa/floorplan/builder.py::_source_binding()`  
`src/pwa/floorplan/overlay.py::_raster_svg()`

Quoted code:

```python
"image_bytes": source_path.read_bytes(),
```

and:

```python
image_b64 = base64.b64encode(image_bytes).decode("ascii")
```

**Concrete failure scenario:**

A valid JPEG floorplan contains EXIF GPS coordinates and `Artist=Alice`. The complete original JPEG byte stream is embedded in `parse/overlay.svg`, preserving that metadata. This violates section 12ג€™s prohibition on EXIF/private source data in artifacts/evidence. Correcting the MIME type makes the JPEG path render correctly but does not sanitize or reject EXIF.

Because the overlay contract also requires binding to the verified raster, the project must explicitly decide whether to reject metadata-bearing raster input or embed a deterministic sanitized representation while separately binding the original hash.

---

### MAJOR ג€” Overlay output is not created exclusively and can follow a staging symlink

**File/function:** `src/pwa/floorplan/builder.py::parse_run()`

Quoted code:

```python
overlay_path.parent.mkdir(parents=True, exist_ok=True)
overlay_path.write_bytes(overlay_bytes)
```

Unlike JSON outputs, this is neither exclusive nor no-follow.

**Concrete failure scenario:**

After the predictable staging directory is created, another local process creates:

```text
runs/.staging/<id>/parse/overlay.svg -> /tmp/victim
```

`write_bytes()` follows the symlink and truncates `/tmp/victim`. The finalized run can also contain a symlink rather than the claimed immutable overlay. This violates the exclusive-write and reparse-point requirements.

---

## 3. Requested edge-case assessment

### Containment: UNC, drive-relative paths, case, and junctions

- **Absolute and relative raw `..`:** rejected.
- **UNC paths:** no lexical bypass is apparent under Windows `Path` semantics; an outside share should fail `relative_to()`.
- **Case differences:** Windows path comparison is case-insensitive, so ordinary case variation should not bypass containment.
- **Drive-relative paths such as `C:foo`:** they are not absolute. Depending on the runs-root drive they are joined/resolved and then physically containment-checked. I do not see a demonstrated escape without `..`, but accepting drive-relative syntax is unnecessarily ambiguous and should be rejected explicitly.
- **Candidate junction/symlink:** not correctly rejected if its resolved target remains under the root, because resolution occurs before the lexical ancestor walk.
- **`runs_root` itself a junction:** not rejected; `resolve(strict=True)` erases it before any `is_link_or_reparse()` call.
- **Manifest and quality artifact ancestors:** not checked through the containment helper before reading.
- **Destination paths:** completely bypassed through unsanitized `parse_run_id`.

The correct pattern is to inspect the original lexical chain with `lstat`/reparse checksג€”including the configured rootג€”before or while resolving each component, and then independently confirm the resolved final target remains contained.

### Process-tree kill

The normal supported paths are reasonable:

- POSIX: dedicated session/process group plus `killpg`.
- Windows: `taskkill /T /F`.

I did not construct a normal PID-reuse case on POSIX because the child remains unreaped until `proc.wait()`. The Windows implementation retains the `Popen` process handle, which also reduces reuse concerns.

Residual concerns:

- The Windows implementation relies on an external executable rather than a pure stdlib mechanism.
- If `taskkill` returns nonzero, the fallback kills only the direct process, so descendants may survive.
- If invoking `taskkill` itself raises, there is no exception fallback inside `_kill_process_tree()`.

Given that the worker code shown does not spawn children, these are residual portability/defense-depth concerns rather than a demonstrated current production failure.

### `seg_intersects_non_adjacent()` false positives

I found no adjacent-edge false positive in the new room self-intersection path. `_validate_room()` excludes both consecutive pairs and the first/last pair before invoking the full predicate. Non-adjacent T-touches are correctly invalid under AC-9. Collinear contact at only a shared endpoint is not reported by `_collinear_segments_overlap()`, but repeated non-adjacent vertices are rejected earlier.

### Overlay determinism and active content

The generated SVG remains deterministic in the code shown:

- no timestamp;
- deterministic geometry/source iteration for a fixed source;
- fixed numeric formatting;
- metadata JSON uses sorted keys;
- labels are XML-escaped.

I found no external URL, script, `foreignObject`, or active-content insertion. The blockers are instead clipping/scaling, original raster metadata leakage, and nonexclusive output writing.

---

## 4. Deferred `width_m` sub-clause

The implementerג€™s calculation is approximately correct **only for the stated 0.9 m opening**.

Let:

- raw opening length be \(L\);
- endpoint signed distances from the wall be \(d_1,d_2\);
- tolerance be \(\delta=0.02\) m.

The perpendicular component between endpoints is bounded by:

\[
|\Delta_\perp| = |d_2-d_1| \le 2\delta = 0.04
\]

The maximum angle is therefore:

\[
\theta_{\max}=\arcsin(0.04/L)
\]

For \(L=0.9\) m:

\[
\theta_{\max}\approx 2.547^\circ
\]

and the wall-projected span is:

\[
P=\sqrt{0.9^2-0.04^2}\approx 0.8991107\text{ m}
\]

The raw/projected difference is about 0.000889 m, or approximately **0.099%**. Thus ג€about 2.5 degreesג€ and ג€about 0.1 percentג€ are reasonable for that exact length.

The broader conclusion is wrong.

### Very short opening

For \(L=0.05\) m:

\[
P=\sqrt{0.05^2-0.04^2}=0.03\text{ m}
\]

Raw length is 0.05 m while projected length is 0.03 m: a 66.7% excess relative to the projection.

For \(L=0.04\) m, a perpendicular span centered on the wall with endpoints at ֲ±0.02 m passes the current endpoint checks, while its wall projection is zero. Therefore the new gate does not generally bound angular deviation.

### It can flip a pass/fail invariant even for a 0.9 m opening

Use:

- wall `(0,0)` to `(5,0)`;
- opening center `(0.4497,0)`;
- opening vector with projected length approximately `0.8991107` and perpendicular change `0.04`;
- endpoints therefore have y offsets `-0.02` and `+0.02`.

The projected half-span is about `0.449555`, so its left projected endpoint is still inside the wall by about `0.000145` m. But validation uses raw `width_m / 2 = 0.45` and requires:

```python
t >= 0.45 - QUANTUM_M  # 0.4499
```

Since `t=0.4497`, the code reports `PARSE_OPENING_WIDTH_EXCEEDS_WALL`, although the projected opening fits. The raw/projected difference exceeds the 0.0001 m slack sufficiently to change the result.

### Conclusion on deferral

The deferral is not justified by the stated numerical bound. At minimum the implementation needs either:

1. projected width after successful wall resolution; or
2. an explicit angular/projection-ratio invariant plus a minimum opening span.

Because width affects canonical geometry and stable IDs, changing this likely falls under PLAN-002 section 20ג€™s retained Geometry/Contract human gate. It should be escalated to Moshe rather than accepted on the current rationale.

---

## 5. Additional INFO-level observations

These are not independently demonstrated blockers under a concrete ordinary input, but merit follow-up:

1. **Hash-ID collisions are not detected.**  
   The implementation detects duplicate geometry but not two distinct identity tuples producing the same 12-hex ID. I do not have a concrete SHA-256-prefix collision pair, so this is `INFO`, not a falsifiable defect.

2. **Worker log files are capped only when read.**  
   `stdout` and `stderr` are ordinary temporary files; `_bounded_text()` limits later reads but not worker writes. Thus they are not actually ג€capped temporary filesג€ as section 12 states. I cannot show from the supplied code that a particular DXF makes the trusted worker emit more than the cap, so this remains `INFO`.

3. **Some required test/evidence files are absent.**  
   I cannot verify M-8 or M-9 without:
   - `tests/unit/test_contract_versions.py`;
   - `tests/integration/test_plan002_failure_matrix.py`.

4. **Shared filesystem helpers were not supplied.**  
   `src/pwa/files.py` is needed to assess the exact behavior of `copy_immutable()` and `is_link_or_reparse()`. The call-order containment defects above remain valid regardless, but helper-internal protections cannot be credited or challenged without that file.

---

## Required gate conditions before approval

At minimum:

1. Validate and contain `parse_run_id` before any filesystem operation.
2. Rework path checking so lexical reparse pointsג€”including `runs_root` itselfג€”are not erased by `resolve()` before inspection.
3. Apply reparse/containment checks to source manifest and quality artifact paths before reading.
4. Recompute annotation `content_hash` and bind its artifact ID/hash into parse outputs.
5. Restrict annotation image binding to the approved floorplan/PDF-page

---

## Recovered tail - Required gate conditions before approval (complete)

1. Validate and contain `parse_run_id` before any filesystem operation; this is a bounded code fix.

2. Rework path checking so lexical reparse pointsג€”including `runs_root` itselfג€”are not erased by `resolve()` before inspection; this is a bounded code fix.

3. Apply reparse and containment checks to source-manifest and quality-artifact paths before reading them; this is a bounded code fix.

4. Recompute the annotation `content_hash` and bind its artifact ID and hash into parse outputs; this is a bounded code fix.

5. Restrict annotation image binding to approved floorplan or PDF-page source artifacts, rejecting missing, ambiguous, cross-run, or unsupported bindings; this is a bounded code fix.

6. Resolve opening-fit semantics by using projected width after successful wall resolution or by adopting an explicit projection-ratio and minimum-span invariant; this touches PLAN-002 section 20ג€™s retained Geometry/Contract human gate and requires Mosheג€™s explicit approval before implementation.
