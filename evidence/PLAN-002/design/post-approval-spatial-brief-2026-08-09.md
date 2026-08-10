# PLAN-002 — Canonical Post-Approval Spatial & Geometry Design Brief

**Replaces:** `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md`
**Target path:** `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md` (same path; this document supersedes it in full)
**Audience:** the OpenAI Codex implementer, then the Anthropic code/spatial reviewer.
**Date:** 2026-08-09. **Baseline commit:** `a047b7c` ("PLAN-002: approve bounded floorplan parsing plan").

**Skills invoked before authoring (per PLAN-002 §17 dispatch rule):** `architecture` (decision framing, dependency-direction and simplicity checks), `test-driven-development` (red-first slice ordering, "watch it fail" gating, anti-mock rules for the fixture suite), `threat-modeling-expert` (trust boundaries for the derived-run copy path, the DXF subprocess boundary and the SVG embedding path). No spatial-geometry-specific or JSON-Schema-specific skill exists in the installed catalogue; the geometry, schema-evolution and determinism content below is authored directly against PLAN-002, ADR-0004/ADR-0005 and the on-disk schemas, and is stated as verifiable rules rather than as skill output.

---

## 0. Authority, status and scope statement

| Item | Value |
|---|---|
| PLAN-002 status | `PLANNED` — explicitly approved by Moshe on 2026-08-09 on Kanban `t_b7ade39e`, including the later AC-20 source-hash Option A and source-quality/scale clarifications |
| ADR-0004 | ACCEPTED — parser baseline, DXF convention, dual-adapter projection, mandatory overlay, Layer B rules |
| ADR-0005 | ACCEPTED — 1.1.0 additive contract + exact-version catalog, immutable derived runs, fail-closed G1, `parse-report.json` as raw evidence, hash Option A, source-quality/scale routing |
| This document | Design only. The Claude architecture subprocess was repository-read-only: it wrote only its local Claude plan output and two temporary local calculation scripts (deleted before exit). No product implementation was performed, no package was installed, no web search occurred, and no project runtime/cloud/remote/GPU/H200 resource was contacted. The operator subsequently copied the accepted design to this canonical repository path. |

**Explicit scope statement.** This design **adds no contract and no scope**. It introduces no schema field, no error code, no CLI flag, no gate and no artifact beyond those already authorized by PLAN-002 §§5–13 and ADR-0004/ADR-0005. Everything below is either (a) a verbatim restatement of an approved rule, or (b) a *design-level* specification of an algorithm, predicate, constant, module name or fixture value that the approved plan leaves to the implementer. Category (b) items are marked **[DESIGN]** where a reader could otherwise mistake them for contract text.

**Supersession of the earlier draft.** The previous brief was written before the approval was canonicalized. Its §0 `BLOCKER — approval is not recorded in the repository` is **closed**: the plan header, `PROJECT-STATE.yaml`, ADR-0004 and ADR-0005 now record the approval. Its `AMBIGUITY-1` and `AMBIGUITY-2` (§7.5, §12) are **closed by Moshe's explicit decisions** and are resolved in §8 below; the draft's recommended CLI 2 / CLI 3 *split* for inventory hash mismatch is **rejected** in favour of approved Option A (uniform CLI 2). The draft's raster inverse-transform formulas carried a sign error and are corrected in §4.6. All other technical content of the draft that survives review is carried forward here.

**Deferred, not designed here:** G7/G8, H200/GPU, cloud, remote execution, spending, production raster parsing, OCR, learned parsers, curves/blocks/xrefs, robust room-overlap area, wall thickness, room names, DWG entity parsing.

---

## 1. Module boundaries and dependency direction

```text
src/pwa/floorplan/
  __init__.py            # package marker; no logic
  config.py              # every named limit/tolerance, DXF_UNITS, limits_snapshot()
  types.py               # frozen dataclasses: SourceFrame, Raw*, Norm*, NormalizedGeometry
  findings.py            # Finding, code -> (severity, tier) table, dedupe + deterministic sort
  source.py              # FloorplanSource Protocol + select_source(...)
  dxf_source.py          # parent side: byte cap, subprocess spawn/timeout/kill, entity mapping
  dxf_worker.py          # `python -m pwa.floorplan.dxf_worker <in.dxf> <out.json>`
  annotation_source.py   # schema-validated annotation -> RawGeometry
  normalize.py           # Decimal quantization, anchor, canonical order, stable IDs, projection
  validate.py            # geometry invariants -> findings; single opening<->wall resolver
  overlay.py             # deterministic SVG (raster + DXF variants)
  runs.py                # containment, hash verification, byte-copy, derived artifacts, staging, finalize
  builder.py             # orchestration: parse_run(...) -> ParseOutcome
  cli.py                 # argparse + exit-code mapping
tools/parse_floorplan.py         # thin shim, matches existing tools/ style
tools/make_floorplan_fixtures.py # Layer A generator; single metric source of truth
```

**Dependency direction — acyclic, enforced by a unit test that imports each module in isolation:**

```text
config -> types -> findings -> { source, normalize, validate, overlay } -> runs -> builder -> cli
```

Hard rules:

- `normalize` must not import `validate`; `validate` imports `normalize` only for shared key/format helpers.
- `overlay` must not import `runs` or `builder`.
- Nothing under `src/pwa/floorplan/` imports `pwa.intake` or `pwa.packager`.
- `pwa.files` is imported read-only and **unmodified** — `is_link_or_reparse`, `sha256_file`, `copy_immutable`, `write_json_exclusive` are reused verbatim (`src/pwa/files.py:11,19,27,45`).
- `dxf_worker` imports only `config`, the stdlib and `ezdxf`. It must not import `runs`, `builder` or `pwa.contracts`.

### 1.1 Edits outside the package (PLAN-002 §16 ownership only)

`src/pwa/contracts.py` — additive, preserving the existing public names:

```python
_SEMVER_RE = re.compile(r"-(\d+)\.(\d+)\.(\d+)\.schema\.json$")

def load_schema_catalog(schemas_dir=None) -> dict[tuple[str, str], dict]:
    """{(schema_id, schema_version): schema} for every *.schema.json on disk.
    schema_id/schema_version are read from the document's `const` values and
    cross-checked against the filename; a mismatch is a hard load-time error.
    Duplicate (schema_id, schema_version) or duplicate `$id` is a hard error."""

def load_all_schemas(schemas_dir=None) -> dict[str, dict]:
    """Compatibility view: latest schema per schema_id, latest chosen by the
    parsed (major, minor, patch) TUPLE, never by lexicographic filename."""

def build_registry(catalog=None) -> Registry:
    """Built from ALL catalog values so 1.0.0 `$ref`s keep resolving."""

def validator_for(schema_id, schema_version=None, catalog=None) -> Draft202012Validator
def validate_artifact(doc, catalog=None) -> list
    # selects on (doc["schema_id"], doc["schema_version"]); unknown pair -> KeyError
```

`src/pwa/intake.py` — bundle string only: extract `CONTRACTS_BUNDLE_VERSION = "1.1.0"` as a module constant and reference it at the single existing literal site. No other line changes.

---

## 2. Parsing stages and the strict derived-run write/finalization sequence

Stages are a straight line; each stage's output is the next stage's only input.

```text
S0 preflight        -> S1 staging  -> S2 inventory copy -> S3 derived envelopes
S4 extract          -> S5 prevalidate cardinality -> S6 normalize -> S7 validate
S8 render overlay   -> S9 build+validate artifacts  -> S10 write -> S11 finalize
```

**Strict order (each numbered step must complete before the next begins):**

1. **S0 preflight — before any directory is created.**
   1.1 usage/argument validation (`--runs-root`, `--source-run`, `--parse-run-id`, optional `--annotation`);
   1.2 containment: resolve `runs_root` strictly, then walk the *unresolved* candidate path component by component from `runs_root` downward, `lstat`-ing each with `pwa.files.is_link_or_reparse`; reject on the first link/reparse point, reject `..`, absolute/drive-qualified inputs and `candidate == runs_root`;
   1.3 `runs/<parse-run-id>` and `runs/.staging/<parse-run-id>` must not exist;
   1.4 load source `project/project_manifest.json` and `project/input_quality_report.json`; each must be schema-valid **at its declared version** and its `content_hash` must recompute via `pwa.contracts.compute_content_hash`;
   1.5 source quality must be `status == "complete"` with `payload.blockers == []`;
   1.6 re-hash **every** entry of the source manifest `payload.inputs[]` in place and compare to the recorded `sha256`;
   1.7 select the adapter and confirm it accepts the designated source.
   **Any failure in S0 is operational: CLI 2, nothing finalized, nothing staged.**
2. **S1 staging** — `runs/.staging/<parse-run-id>/` created exclusively (`mkdir` without `exist_ok`).
3. **S2 inventory copy** — byte-copy with `copy_immutable` (which fsyncs and re-hashes): every source manifest inventory entry to the identical run-relative path, plus `project/source-manifest.json` and `project/source-quality-report.json` as byte copies of the two source audit artifacts. Each returned digest must equal the recorded one. A mismatch here is still **operational (CLI 2)** under approved Option A.
4. **S3 derived envelopes** — build and validate in memory: derived `project_manifest` 1.0.0 (parse-run ID, new artifact ID, `contracts_bundle_version = "1.1.0"`, full re-verified inventory, `inputs[]` binding to the source manifest and source quality-report artifact IDs/hashes, goal/units/scale copied semantically) and derived `input_quality_report` 1.0.0.
5. **S4 extract** — `FloorplanSource.extract(path, limits) -> RawGeometry`. Adapter-specific source coordinates retained.
6. **S5 prevalidate cardinality** — `prevalidate_cardinality(raw)` requires ≥1 wall and ≥1 room **before any `min()` or normalization arithmetic**; otherwise `PARSE_EMPTY_GEOMETRY`.
7. **S6 normalize** — §4.
8. **S7 validate** — §5–§6; produces the full deduplicated, sorted finding list; the outcome (`complete` / `partial` / `failed`) is now known.
9. **S8 render overlay and hash it** — must precede S9, because `payload.overlay.sha256` is an input to `floorplan_parse.content_hash`. The SVG must never contain the parse hash (cycle).
10. **S9 build + validate artifacts** — `floorplan_parse` 1.1.0, `assumptions` 1.0.0 (`payload.stage = "parsing"`), and the raw `parse-report.json`. Every envelope artifact must be schema-valid and its `content_hash` must recompute.
11. **S10 write** — `write_json_exclusive` for JSON; exclusive `open("x", encoding="utf-8", newline="\n")` for the SVG. Nothing is written before S9 succeeds for the whole set.
12. **S11 finalize** — close every handle (including PIL image objects and worker stdio temp files), then same-volume `os.replace(staging, final)`.

Any exception between S1 and S11 is **operational**: staging is retained (never auto-deleted, never resumed), the CLI emits a bounded, path-sanitized JSON diagnostic on stdout, best-effort writes `runs/.staging/<id>/parse-report.json`, and exits **2**. Every retry requires a **new** parse-run ID.

---

## 3. Exact data model

### 3.1 In-memory types (`types.py`, all `@dataclass(frozen=True)`, tuples not lists)

```python
class SourceFrame:                 # how source coordinates become metres
    kind: Literal["dxf", "raster"]
    unit_scale_m: float            # metres per source coordinate unit (mm -> 0.001; px -> scale_m_per_px)
    y_down: bool                   # raster True, DXF False
    height_px: int | None          # raster only; required for the flip
    source_units: str              # "mm" | "cm" | "m" (dxf) or "px" (raster)

class RawWall:      index: int; source_ref: str; start: tuple[float, float]; end: tuple[float, float]
class RawRoom:      index: int; source_ref: str; polygon: tuple[tuple[float, float], ...]
class RawOpening:   index: int; source_ref: str; kind: Literal["door", "window"]
                    center: tuple[float, float]                                 # SOURCE units
                    width_m: float                                              # ALREADY METRES in both adapters
                    span: tuple[tuple[float, float], tuple[float, float]] | None  # DXF only
                    wall_index: int | None                                      # annotation only; DXF None
class RawDimension: index: int; source_ref: str; a: tuple[float, float]; b: tuple[float, float]
                    declared_length_m: float
class RawGeometry:  frame: SourceFrame; walls; rooms; openings; dimensions
                    scanned_entities: int; unmapped: tuple[Finding, ...]

class NormWall:     id: str; start; end; confidence: float; provenance: dict
class NormRoom:     id: str; polygon; confidence: float; provenance: dict
class NormOpening:  id: str; type: str; wall_id: str; center; width_m: float
                    confidence: float; provenance: dict
class NormalizedGeometry: units: Literal["m"]; walls; rooms; openings
                          dimensions_m; normalization: dict; frame: SourceFrame
```

> **`width_m` asymmetry — the single easiest silent AC-6 failure.** The DXF adapter computes `width_m = hypot(span) * unit_scale_m`. The annotation adapter reads `width_m` **verbatim** from the validated document — it is already metres and must **never** be multiplied by `scale_m_per_px`.

**`source_ref` grammar [DESIGN]** — used in findings, provenance and as the deterministic sort tiebreak:

```text
dxf:modelspace/<LAYER>#<handle>        e.g. dxf:modelspace/PWA-WALL#1F3
annotation:<array>[<index>]            e.g. annotation:walls[3], annotation:openings[1]
```

### 3.2 `floorplan_annotation` 1.0.0 payload

```json
{
  "image": {
    "source_image_ref": "project/inputs/originals/floorplan.png",
    "sha256": "sha256:<64hex>",
    "width_px": 2000,
    "height_px": 1800
  },
  "scale_m_per_px": 0.005,
  "walls":    [ { "start_px": [200, 1400], "end_px": [200, 200] } ],
  "rooms":    [ { "polygon_px": [[200, 1400], [1200, 1400], [1200, 200], [200, 200]] } ],
  "openings": [ { "type": "door", "wall_index": 1, "center_px": [700, 1400], "width_m": 0.9 } ],
  "declared_dimensions": [ { "a_px": [200, 1400], "b_px": [1800, 1400], "length_m": 8.0 } ]
}
```

Schema rules: `additionalProperties: false` at every level; `source_image_ref` is a relative POSIX path with no `..`, no drive letter, no leading `/`; `wall_index` is `integer, minimum: 0`; `width_m` / `length_m` / `scale_m_per_px` are `exclusiveMinimum: 0`; `width_px` / `height_px` are `integer, minimum: 1`; `polygon_px` has `minItems: 3`.

> **`walls` and `rooms` must be `minItems: 0`.** The empty case is a *runtime* finding (`PARSE_EMPTY_GEOMETRY`, CLI 3). If the schema rejects it, the failure surfaces as a schema error on the operational path (CLI 2) and AC-20 fails.

### 3.3 `floorplan_parse` 1.1.0 — additive deltas only

Copy 1.0.0, bump `$id` and both `const` values, **rewrite every self-`$ref` to the 1.1.0 `$id`** (otherwise the copies silently resolve against the 1.0.0 document), then add:

- `payload.normalization` — object, optional in schema, **required at PLAN-002 runtime**:

```json
{ "quantum_m": 0.0001, "source_units": "mm", "source_unit_scale_m": 0.001,
  "translation_m": [1.0, 2.0], "y_axis": "up",
  "source_height_px": null, "scale_m_per_px": null }
```

  `y_axis` is `"up"` (DXF) or `"flipped_from_raster"` (annotation). `source_height_px` and `scale_m_per_px` are non-null only for the raster path.

- `payload.overlay` — optional in schema, required at runtime: `{ "path": "parse/overlay.svg", "sha256": "sha256:<64hex>" }`.
- entity `provenance` — optional in schema, required at runtime, `additionalProperties: false`, `source_kind: {"enum": ["dxf", "annotation"]}`:
  - wall: `{source_kind, source_ref, source_start: [x, y], source_end: [x, y]}`
  - room: `{source_kind, source_ref, source_polygon: [[x, y], ...]}`
  - opening: `{source_kind, source_ref, source_center: [x, y], source_span: [[x, y], [x, y]] | absent}`

  `source_*` coordinates are the **untransformed source-space** values (mm for DXF, px for raster), so the source ↔ metric mapping is auditable from the artifact alone.

> The envelope is `additionalProperties: false` at the top level and the `allOf` branch does not relax it. `normalization` and `overlay` therefore live **under `payload`**, never at top level.

### 3.4 `parse-report.json` — raw evidence, not an envelope artifact

```json
{ "report_version": 1, "parse_run_id": "...", "source_run_id": "...",
  "adapter": "dxf" | "annotation", "outcome": "complete|partial|failed|operational_failure",
  "cli_exit": 0,
  "terminal_finding": { "code": "...", "severity": "...", "source_ref": "..." } | null,
  "limits": { "...config.limits_snapshot()..." },
  "metrics": { "walls": 0, "rooms": 0, "openings": 0, "dimensions": 0, "source_entities_scanned": 0 },
  "findings": [ { "code": "...", "severity": "...", "tier": 0, "source_ref": "...", "message": "..." } ],
  "overlay": { "path": "parse/overlay.svg", "sha256": "sha256:<64hex>" }
            | { "overlay_omitted_reason": "..." },
  "canonical_projection_sha256": "sha256:<64hex>" | null }
```

No timestamp, no duration, no absolute path, no stack trace, no user name. Byte-deterministic and asserted as such.

### 3.5 Canonical projection (AC-6)

```python
{ "units": "m",
  "rooms":    [ [[x, y], ...] for each room in canonical order ],
  "walls":    [ [[sx, sy], [ex, ey]] for each wall in canonical order ],
  "openings": [ [type, wall_id, [cx, cy], width_m] for each opening in canonical order ] }
```

Excludes `created_at`, confidence, provenance, source scale, overlay and normalization. It is hashed with the same canonical serialization used by `compute_content_hash` (`json.dumps(..., ensure_ascii=False, separators=(",", ":"), sort_keys=True)`, SHA-256, `sha256:` prefix) into `evidence/PLAN-002/determinism/geometry-projection-hashes.json`.

---

## 4. Coordinate transforms, units, quantization, anchor, canonical forms, stable IDs

All of §4.1–§4.5 is performed in `Decimal`. Convert to `float` only at the emit boundary; float subtraction after quantization reintroduces ~1e-17 dust and destabilizes IDs.

```python
q(v)    = Decimal(str(v)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
emit(d) = 0.0 if d == 0 else float(d)          # kills -0.0 in JSON
key(d)  = "0.0000" if d == 0 else f"{d:.4f}"   # identity/ordering text form
```

`emit` and `key` both test `d == 0`, which is `True` for `Decimal("-0.0000")`; that is what normalizes `-0` to `0` for both JSON output and identity keys. `f"{Decimal('-0.0000'):.4f}"` would otherwise be `"-0.0000"` and produce a different ID for the same point.

### 4.1 Source → metres (forward)

| Source | X | Y |
|---|---|---|
| DXF (y-up, native) | `X_raw = x_u * unit_scale_m` | `Y_raw = y_u * unit_scale_m` |
| Raster (y-down) | `X_raw = x_px * s` | `Y_raw = (height_px - y_px) * s` |

`unit_scale_m` is `0.001` (mm), `0.01` (cm) or `1.0` (m) from `$INSUNITS ∈ {4, 5, 6}`; `s = scale_m_per_px`. `height_px` is decoded **fresh from the verified image bytes**, never read from manifest `details`.

Rejections at this stage: NaN, ±inf, non-finite, non-2D, `|value| > MAX_COORDINATE_MAGNITUDE_M`, `width_m <= 0` → `PARSE_RESOURCE_LIMIT`.

### 4.2 Quantization

Every coordinate, and every width and declared length, is quantized with `q` to `1e-4 m` using banker's rounding (`ROUND_HALF_EVEN`).

### 4.3 Anchor and translation

```text
tx = min(x over WALL endpoints only)
ty = min(y over WALL endpoints only)     # per axis, independently
v' = q(v - anchor)                       # re-quantize defensively, still Decimal
```

Rooms, openings and dimensions never move the anchor. `translation_m = [emit(-tx), emit(-ty)]`? **No** — `translation_m` records the *applied translation vector*, i.e. `[emit(tx), emit(ty)]` is the source-space anchor expressed in metres, and the applied transform is "subtract `translation_m`". Recorded as `translation_m: [tx, ty]` with the documented meaning `X_norm = X_raw - translation_m[0]`, `Y_norm = Y_raw - translation_m[1]`. **[DESIGN]** — this fixes the sign convention once so the inverse in §4.6 and the overlay in §11 cannot drift.

### 4.4 Canonical forms

- **Walls:** endpoints ordered so `start <= end` lexicographically by `(x, y)`.
- **Room polygons**, in this order and no other:
  1. drop a trailing vertex equal to the first;
  2. reject consecutive duplicates and any repeated vertex (§5);
  3. shoelace signed area: `< 0` → reverse to CCW; `== 0` → error;
  4. **then** rotate so the lexicographically smallest vertex is first; ties broken by the lexicographically smallest full rotated tuple.
  Reversing after rotating yields a different canonical form — step 3 before step 4 is load-bearing.
- **Canonical entity order** sorts by the complete geometry tuple, never by the ID hash and never by centroid:
  - walls: `(sx, sy, ex, ey)`
  - rooms: the full flattened vertex tuple of the canonical polygon
  - openings: `(cx, cy, width_m, type, wall_id)` **[DESIGN]** — geometry first, with `type` and `wall_id` as a total-order tiebreak. (The projection *element* remains `[type, wall_id, [cx, cy], width_m]` per §3.5; the ordering key and the element serialization are deliberately different things.)

### 4.5 Stable IDs

Computed walls → rooms → openings, in that order, because `wall_id` is inside the opening identity tuple.

```text
wall_key    = "wall|"    + "|".join(key(sx), key(sy), key(ex), key(ey))
room_key    = "room|"    + "|".join(key(c) for each coordinate of each vertex, in canonical order)
opening_key = "opening|" + "|".join(type, wall_id, key(cx), key(cy), key(width_m))

id = {"wall": "w", "room": "r", "opening": "o"}[kind] + "-" + sha256(key.encode("utf-8")).hexdigest()[:12]
```

The `w-` / `r-` / `o-` prefix is **[DESIGN]**; the schema types IDs as opaque `minLength: 1` strings, so the prefix adds no contract. A repeated key is `PARSE_DUPLICATE_ENTITY` (error) — never suffix, never merge.

IDs are stable across reruns and across input reordering. An addition that does **not** move the wall-derived anchor preserves every existing ID. An addition that moves the anchor changes every ID; that is expected, tested and documented (AC-8, §12.3).

### 4.6 Inverses (used only by the overlay)

```text
DXF:     x_u  = (X_norm + tx) / unit_scale_m
         y_u  = (Y_norm + ty) / unit_scale_m
Raster:  x_px = (X_norm + tx) / s
         y_px = height_px - (Y_norm + ty) / s
```

These are the corrected forms; the earlier draft's `(X_m - tx)` is wrong given the forward "subtract the anchor" convention. Worked check against the Layer A fixture (§12): `X_norm = 0, tx = 1.0, s = 0.005` → `x_px = 200` ✓; `Y_norm = 0, ty = 2.0, height_px = 1800` → `y_px = 1800 - 400 = 1400` ✓.

**Quantization is lossy.** The inverse is exact only to `QUANTUM_M / s` pixels (0.02 px at `s = 0.005`) or `QUANTUM_M / unit_scale_m` source units (0.1 mm at mm). Do **not** assert `inverse(forward(p)) == p`; assert it is within that bound. Byte determinism of the overlay is unaffected and is what AC-14 requires.

---

## 5. Polygon and room topology

**Work in exact integers.** Every normalized coordinate is an exact multiple of `1e-4`; multiply by `10_000` into `int` for every orientation, intersection and containment predicate. Cross products are then exact and no epsilon is needed. Reserve `float` for lengths, distances and tolerance comparisons only.

```python
def orient(a, b, c) -> int:   # sign of (b-a) x (c-a), exact ints
def seg_proper_cross(p1, p2, q1, q2) -> bool:
    """True iff the open segments cross at exactly one point interior to both.
    Collinear overlap, shared endpoints and touching are NOT proper crossings."""
```

### 5.1 Predicates and degeneracy

| # | Predicate | Outcome |
|---|---|---|
| P1 | polygon has ≥ 3 vertices after dropping a trailing duplicate-of-first | else `PARSE_OPEN_POLYGON` (error) |
| P2 | no two consecutive vertices equal; no vertex repeated anywhere in the ring | consecutive duplicate → `PARSE_OPEN_POLYGON`; non-consecutive repeat → `PARSE_SELF_INTERSECTING_POLYGON` (both error) |
| P3 | shoelace signed area `!= 0` | else `PARSE_SELF_INTERSECTING_POLYGON` (error) — a zero-area ring is degenerate, not "open" |
| P4 | no proper crossing between any pair of **non-adjacent** edges of the same ring | else `PARSE_SELF_INTERSECTING_POLYGON` (error) |
| P5 | winding | negative area is silently corrected to CCW during normalization (§4.4); it is not a finding |
| P6 | DXF only: `LWPOLYLINE.closed is True` | else `PARSE_OPEN_POLYGON` (error). Annotation polygons are closed by contract representation but still run P1–P4 |

Adjacent edges (sharing a vertex) are excluded from P4 because they always touch at that vertex. Edge `i` and edge `i+1 mod n` are adjacent; for `n == 3` every pair is adjacent, so P4 is vacuous and P3 carries the check.

### 5.2 Boundary warnings and the explicit Part 1 overlap limitation

`PARSE_ROOM_BOUNDARY_UNMATCHED` (**warning**) is emitted **[DESIGN predicate]** when any edge of room *A* properly crosses (`seg_proper_cross`) any edge of a different room *B*. Shared collinear edges, shared vertices and pure touching do **not** warn — two rooms sharing a party wall are the normal case and must stay silent.

Emission is deduplicated to at most one finding per unordered room pair, with `source_ref` set to the lexicographically smaller room's `source_ref`, so the finding list is order-independent.

**Part 1 limitation, stated plainly:** room *area* overlap is **not** an acceptance invariant. The locked dependency set contains no robust arbitrary-polygon intersection implementation, and Part 1 will not hand-roll one. Two rooms may overlap in area and still produce `complete` output as long as no boundary edges properly cross (e.g. one room fully containing another). This is a known, accepted gap with a documented upgrade path (a polygon-clipping dependency or an exact-integer sweep, both requiring a new approved decision).

### 5.3 Cost ceiling

Pairwise edge testing is O(n²); at `MAX_POLYGON_VERTICES = 10_000` that is 10⁸ pairs. The vertex cap is checked **before** the loop. Layer A polygons are 4 vertices. Leave the ceiling named in code:

```python
# ponytail: O(n^2) segment test; Bentley-Ottmann if a real plan ever approaches MAX_POLYGON_VERTICES
```

---

## 6. Openings, wall binding, adjacency semantics

### 6.1 Single resolver, both adapters

Duplicating opening↔wall logic per adapter is exactly how the two paths silently diverge and AC-6 fails. There is **one** function, operating on *normalized metric* geometry:

```python
def resolve_opening_wall(walls, center, width_m, declared_wall_id: str | None
                        ) -> tuple[str | None, list[Finding]]
```

Algorithm:

1. For each wall, compute the perpendicular distance `d` from `center` to the **infinite line** through the wall, and the projection parameter `t` (arc length from `start` along the wall direction).
2. A wall is a *candidate* iff `d <= OPENING_OFFSET_M` **and** `-QUANTUM_M <= t <= L + QUANTUM_M`, where `L` is the wall length.
3. Zero candidates → `PARSE_UNKNOWN_WALL_REF` (error). More than one candidate → `PARSE_AMBIGUOUS_WALL_REF` (error). The candidate list is evaluated in canonical wall order so the reported `source_ref` is deterministic.
4. Exactly one candidate `W`:
   - **DXF** passes `declared_wall_id=None` — `W` is the binding.
   - **Annotation** passes the ID resolved from `wall_index`. If `declared_wall_id != W.id` → `PARSE_OPENING_OFF_WALL` (error). If `wall_index` is out of range → `PARSE_UNKNOWN_WALL_REF` (error).
5. Span fit: `t >= width_m/2 - QUANTUM_M` **and** `(L - t) >= width_m/2 - QUANTUM_M`; else `PARSE_OPENING_WIDTH_EXCEEDS_WALL` (error).
6. Off-wall check within the segment: if `d > OPENING_OFFSET_M` for the declared wall → `PARSE_OPENING_OFF_WALL` (error).

For the DXF adapter, the plan's collinearity requirement ("every opening line must be collinear with exactly one wall segment within tolerance") is enforced **additionally** on the raw span before normalization: both span endpoints must satisfy step 2 against the same single wall.

### 6.2 What adjacency is and is not represented in Part 1

`floorplan_parse` 1.1.0 has exactly one relational field: `openings[].wall_id`. That is a **opening → wall** reference and nothing else.

- There is **no** `rooms[].adjacent_rooms`, no `walls[].rooms`, no `openings[].from_room` / `to_room`, and no adjacency graph anywhere in the approved schema. **None will be invented.**
- Room-to-room adjacency, door connectivity graphs, and "which room is on which side of a wall" are **not emitted in Part 1** and are **deferred**. They are derivable downstream from the emitted walls, rooms and openings, but PLAN-002 makes no such claim and ships no such field.
- Consequently, an opening does not carry any information about the rooms it connects, and no test may assert one.

Any future adjacency output is a new contract and a new PLAN with explicit Moshe approval.

---

## 7. Centralized tolerances, limits and boundary semantics

Everything below lives in `src/pwa/floorplan/config.py` as module-level constants, is returned by `limits_snapshot()`, and appears verbatim in `parse-report.json["limits"]`. No numeric literal from this table may appear anywhere else in the package.

| Constant | Value | Comparison | Boundary semantics |
|---|---|---|---|
| `QUANTUM_M` | `1e-4` | quantization step | exact; `ROUND_HALF_EVEN` |
| `DEGENERATE_WALL_M` | `0.05` | `length < DEGENERATE_WALL_M` → error | **exclusive**: exactly `0.0500` passes; `0.0499` fails |
| `OPENING_OFFSET_M` | `0.02` | `d <= OPENING_OFFSET_M` → on wall | **inclusive**: exactly `0.0200` passes; `0.0201` fails |
| span fit | — | `t >= width_m/2 - QUANTUM_M` and `(L - t) >= width_m/2 - QUANTUM_M` | **inclusive with one quantum of slack**: `t = width/2` passes; `t = width/2 - QUANTUM_M` passes; `t = width/2 - 2*QUANTUM_M` fails |
| `DIMENSION_TOL(d)` | `max(0.02, abs(d) * 0.01)` | `abs(measured - declared) > tol` → error | **exclusive fail**: exactly `tol` passes |
| `LOW_CONFIDENCE_THRESHOLD` | `0.5` | `confidence < 0.5` → low | **exclusive**: exactly `0.5` is accepted |
| `MAX_DXF_BYTES` | `50 MiB` | `st_size > MAX` → error, before spawn | exclusive |
| `MAX_DXF_ENTITIES` | `200_000` | `len(msp) > MAX` → error, post-load | exclusive |
| `MAX_ANNOTATION_BYTES` | `5 MiB` | `> MAX` → error, before JSON parse | exclusive |
| `MAX_WALLS` / `MAX_ROOMS` / `MAX_OPENINGS` | `20_000` / `5_000` / `20_000` | `count > MAX` → error, before O(n²) | exclusive |
| `MAX_POLYGON_VERTICES` | `10_000` | `> MAX` → error, before self-intersection loop | exclusive |
| `MAX_COORDINATE_MAGNITUDE_M` | `100_000` | `abs(v) > MAX` → error | exclusive |
| `MAX_SOURCE_RASTER_BYTES` | `50 MiB` | `> MAX` → error, before decode | exclusive |
| `MAX_SOURCE_PIXELS` | `100_000_000` | `W * H > MAX` → error, before decode | exclusive |
| `MAX_OVERLAY_BYTES` | `70 MiB` | `> MAX` → overlay omitted | exclusive |
| `MAX_WORKER_STDIO_BYTES` | `1 MiB` | truncation cap | inclusive read, then truncate |
| `PARSER_TIMEOUT_S` | `30` | `proc.wait(timeout=...)` | `TimeoutExpired` → `PARSE_TIMEOUT` |
| `DXF_UNITS` | `{4: "mm", 5: "cm", 6: "m"}` | membership | any other `$INSUNITS` → `PARSE_UNITS_MISMATCH` |
| `OVERLAY_MARGIN_FRACTION` **[DESIGN]** | `0.05` | DXF overlay bbox padding | `margin_u = OVERLAY_MARGIN_FRACTION * max(bbox_w, bbox_h)` |
| `DIMENSION_TIE_M` **[DESIGN]** | `= QUANTUM_M` | confidence tie predicate (§9.1) | inclusive |

Resource limits are checked **before** the expensive loop they protect, in this order: byte size → decoded pixel count → entity/vertex counts → O(n²) geometry.

Do not import `pwa.intake._DXF_UNITS`; `config.DXF_UNITS` is the parse-time source of truth (intake's user-supplied units never silently override contradictory DXF metadata at parse time).

---

## 8. Malformed/unsupported input, finding ordering, outcome matrix, AC-20

### 8.1 Finding model and deterministic ordering

`findings.py` holds one table mapping each code to `(severity, tier)` so severity and tier cannot drift apart:

| Tier | Meaning | Codes |
|---|---|---|
| 0 | containment / size / hash / schema | `PARSE_SOURCE_UNSUPPORTED`, `PARSE_SOURCE_HASH_MISMATCH`, `PARSE_RESOURCE_LIMIT`, `PARSE_TIMEOUT` |
| 1 | units / unsupported source semantics | `PARSE_UNITS_MISMATCH`, `PARSE_UNSUPPORTED_FEATURE`, `PARSE_SCALE_UNKNOWN` |
| 2 | normalization | `PARSE_EMPTY_GEOMETRY`, `PARSE_DUPLICATE_ENTITY` |
| 3 | geometry invariants | `PARSE_OPEN_POLYGON`, `PARSE_SELF_INTERSECTING_POLYGON`, `PARSE_DEGENERATE_WALL`, `PARSE_UNKNOWN_WALL_REF`, `PARSE_AMBIGUOUS_WALL_REF`, `PARSE_OPENING_OFF_WALL`, `PARSE_OPENING_WIDTH_EXCEEDS_WALL`, `PARSE_DIMENSION_INCONSISTENT` |
| 4 | warnings | `PARSE_LOW_CONFIDENCE`, `PARSE_UNMAPPED_SOURCE_ENTITY`, `PARSE_ROOM_BOUNDARY_UNMATCHED` |

Findings are **deduplicated** on `(code, source_ref, message)` and then sorted by `(tier, code, source_ref, message)` with plain ASCII string comparison; a `None` `source_ref` sorts as `""`. This is a total order, so the emitted list is byte-identical across runs and across input reordering.

`terminal_finding` = the first finding in sorted order whose severity is `error`, else `null`.

Outcome derivation: any error → `failed`; else any warning → `partial`; else `complete`.

Envelope mapping: findings become `errors[]` entries `{code, message, path?}`. `code` already matches `^[A-Z][A-Z0-9_]*$`. **A `partial` or `failed` envelope with an empty `errors[]` is schema-rejected**, which would flip a legitimate CLI 1 into CLI 2 — assert non-emptiness before validation. Messages contain no absolute path, no stack trace, no user name, no source file name.

### 8.2 Malformed / unsupported input behaviour

| Situation | Handling |
|---|---|
| file not accepted by any adapter (e.g. `.dwg`, `.tif`, or `--annotation` absent and the floorplan is not DXF) | `PARSE_SOURCE_UNSUPPORTED`, operational, **CLI 2** |
| annotation JSON fails `floorplan_annotation` 1.0.0 schema validation | operational, **CLI 2** — the annotation is a contract input, validated before any field is used |
| DXF entity on an unknown layer | `PARSE_UNMAPPED_SOURCE_ENTITY` (warn); entity recorded then ignored; scan continues |
| `TEXT`/`MTEXT` or wrong entity kind on a known `PWA-*` layer | `PARSE_UNSUPPORTED_FEATURE` (error); **finish the bounded scan**, then fail |
| any entity on reserved `PWA-DIM` | `PARSE_UNSUPPORTED_FEATURE` (error); finish scan, then fail |
| `IMAGE` / XREF / OLE / `INSERT` / `ARC` / `SPLINE` / nonzero bulge / nonzero Z or elevation | `PARSE_UNSUPPORTED_FEATURE` (error); **external data is never resolved**; finish scan, then fail |
| any paperspace entity, or any additional active/non-empty layout | `PARSE_UNSUPPORTED_FEATURE` (error) |
| `$INSUNITS ∉ {4,5,6}` or `DXF_UNITS[$INSUNITS] != manifest payload.units` (including `units == "unknown"`) | `PARSE_UNITS_MISMATCH` (error) |
| manifest `scale.known == false`; or annotation path and `scale.m_per_px` is null/absent; or annotation `scale_m_per_px != manifest scale.m_per_px` (compared as `Decimal(str(...))`, never as floats) | `PARSE_SCALE_UNKNOWN` (error) |
| worker JSON output malformed | treated as untrusted input; strict shape validation; failure is operational, **CLI 2** |

### 8.3 Outcome / artifact / exit-code matrix (locked, PLAN-002 §11)

| Outcome | Finalized artifacts | `floorplan_parse.status` | Overlay | CLI |
|---|---|---|---|---|
| no findings | derived manifest + derived quality report + parse + assumptions + parse-report | `complete` | required | **0** |
| warnings / low confidence only, usable geometry | same set | `partial` | required | **1** |
| any error finding, schema-valid source reached the parser | same set | `failed` | required **only if** normalized geometry exists and the render stays within `MAX_OVERLAY_BYTES`; otherwise `parse-report.overlay_omitted_reason` | **3** |
| usage / containment / invalid source contract / any hash mismatch / staging create-write-fsync-rename failure / unexpected exception before a valid diagnostic set | **none finalized**; bounded staging may remain | — | not produced | **2** |

A "valid diagnostic set" means every **envelope** artifact above is schema-valid and its hash recomputes. `parse-report.json` is deterministic JSON with a tested internal shape and names the terminal finding, but is not claimed to be schema-valid and is not in the schema catalog. `PARSE_RESOURCE_LIMIT` / `PARSE_TIMEOUT` **after** a validated preflight are failed-domain (CLI 3) and finalize without an overlay when rendering is impossible. Failure to serialize or validate the diagnostic set is operational (CLI 2).

### 8.4 Approved AC-20 semantics — hash Option A, source quality, scale

These three rows are the closure of the earlier draft's `AMBIGUITY-1` and `AMBIGUITY-2`. **The draft's recommended CLI 2 / CLI 3 split for inventory-item hash mismatch is rejected.**

| Case | Code | Outcome | Finalized derived run | CLI |
|---|---|---|---|---|
| **Any** pre-parse hash mismatch — source manifest, source quality report, **or any source inventory item** | `PARSE_SOURCE_HASH_MISMATCH` | operational | **none** | **2** |
| Source quality report not `status == "complete"`, or `payload.blockers != []` | (invalid source contract; reported in the staging/stdout diagnostic) | operational | **none** | **2** |
| Schema-valid, `complete`, blocker-free source that then exposes missing or contradictory scale | `PARSE_SCALE_UNKNOWN` | failed domain parse | derived manifest + derived quality report + `floorplan_parse(status="failed")` + assumptions + parse-report | **3** |

Design consequence to state in the ADR-facing evidence: because Option A routes every hash mismatch to CLI 2, `PARSE_SOURCE_HASH_MISMATCH` **never appears in a finalized envelope artifact**. It appears only in the stdout diagnostic and, when staging already exists, in the retained `runs/.staging/<id>/parse-report.json`. Tests must assert exactly that — asserting a finalized artifact carrying this code would be wrong.

---

## 9. Confidence, provenance, assumptions and determinism requirements

### 9.1 Confidence (deterministic, never estimated)

| Source | Value |
|---|---|
| accepted DXF primitive | `1.0` |
| manually annotated primitive tied to a declared dimension | `0.9` |
| manually annotated primitive derived only from the supplied scale | `0.6` |

**"Tied to a declared dimension" — exact predicate [DESIGN]:** an annotation-derived entity is dimension-tied iff there exists a `declared_dimensions[]` entry that **passes** `DIMENSION_TOL` and whose two normalized endpoints both coincide, within `DIMENSION_TIE_M`, with two vertices of that entity's normalized geometry — wall endpoints for walls, polygon vertices for rooms. An opening inherits the tie state of its bound wall. Everything else is `0.6`. This predicate selects among the three **approved** values; it introduces no new value and no new field.

`any(entity.confidence < LOW_CONFIDENCE_THRESHOLD)` → `PARSE_LOW_CONFIDENCE` (warning) → `partial` → G1 blocked (D-014). Note that in Part 1 no adapter can emit a confidence below `0.5`, so this warning is unreachable from any Layer A *source* fixture and is tested at unit level on a constructed `NormalizedGeometry`. State this honestly rather than fabricating an unreachable fixture.

### 9.2 Provenance and assumptions

Provenance is required at runtime on **every** emitted entity (§3.3). Text entities are not emitted in Part 1.

`assumptions` 1.0.0, `payload.stage = "parsing"`, `entries[]` with `requires_human_ack: false` — Part 1 has **no** parser default that alters geometry:

| Path | key | value | reason | source |
|---|---|---|---|---|
| both | `source_adapter` | `"dxf"` / `"annotation"` | which adapter produced the geometry | `inference` |
| both | `normalization_anchor_m` | `"[1.0, 2.0]"` | translation applied so the minimum wall endpoint is (0,0) | `inference` |
| DXF | `dxf_units` | `"mm"` | `$INSUNITS=4`, cross-checked against the verified manifest units | `user` |
| annotation | `scale_m_per_px` | `"0.005"` | taken from the verified source manifest and the validated annotation | `user` |
| annotation | `raster_y_axis` | `"flipped_from_raster"` | source pixels are y-down; metric output is y-up | `inference` |

Any future approved default that alters geometry must ship with `requires_human_ack: true`. Because `assumptions` 1.0.0 has no resolution field, acknowledgement is expressed **only** as corrected input plus a fresh derived run; a finalized artifact is never mutated.

### 9.3 Determinism requirements — exact scope

| Object | Determinism claim | How |
|---|---|---|
| stable IDs | identical for identical normalized geometry, across reruns, machines and input orderings | Decimal end-to-end; `key()` text form; `-0` normalized; §4.5 |
| canonical projection | byte-identical JSON and identical SHA-256 for both adapters on Layer A | §3.5; `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False` |
| `parse-report.json` | byte-identical for identical inputs | no timestamp, no duration, no absolute path; sorted findings; `limits_snapshot()` emitted with sorted keys |
| `overlay.svg` | byte-identical for identical `(source bytes, adapter input bytes)` | one number formatter, literal coordinates, fixed group order, no timestamp, no run ID in the SVG (§11) |
| `floorplan_parse.json` / `assumptions.json` | deterministic **modulo** `created_at`, `artifact_id`, `run_id` and the `inputs[]` hashes that depend on them | golden comparison strips exactly those fields and compares the remainder plus the canonical projection hash |

JSON on disk: `write_json_exclusive` → `indent=2`, `ensure_ascii=False`, LF newlines, one trailing newline, **insertion order preserved** (`sort_keys` applies only to the ephemeral hashing serialization in `compute_content_hash`). Map insertion order is load-bearing and must be constructed deterministically in code.

---

## 10. (reserved — merged into §9.3)

---

## 11. Overlay: source-aligned transforms, security, ordering, omission

Compute every coordinate in Python and emit literal numbers. **Do not use SVG `transform` attributes for the flip** — literal numbers are renderer-independent, auditable, and keep determinism a property of one formatter.

```python
def fmt(v: float) -> str:
    """3 decimals, trailing zeros stripped, '-0' -> '0'. The only number
    formatter in overlay.py."""
```

### 11.1 Raster overlay (annotation path)

- `viewBox="0 0 W H"`, `width="W" height="H"` from dimensions **decoded fresh from the verified image bytes**.
- `<image x="0" y="0" width="W" height="H" href="data:image/png;base64,..."/>` — `href` only, no `xlink:href`.
- Guard order: raster bytes ≤ `MAX_SOURCE_RASTER_BYTES` → `W*H` ≤ `MAX_SOURCE_PIXELS` → base64 (inflates 4/3) → final SVG ≤ `MAX_OVERLAY_BYTES`.
- Detections mapped back with the §4.6 inverse: `x_px = (X + tx)/s`, `y_px = height_px - (Y + ty)/s`. SVG y is already down, so **no further flip**.

### 11.2 DXF overlay

- bbox over accepted source primitives in **source units**; `margin_u = OVERLAY_MARGIN_FRACTION * max(bbox_w, bbox_h)`.
- `viewBox="0 0 (bbox_w + 2*margin) (bbox_h + 2*margin)"`.
- `svg_x = x_u - (minX_u - margin)`; `svg_y = (maxY_u + margin) - y_u`.
- Normalized detections return to source units via §4.6, then into SVG coordinates.

### 11.3 Common rules

- Group order, fixed: `source`, `walls`, `rooms`, `doors`, `windows`, `ids`, `confidence`, `legend`. Entities inside each group in canonical order (§4.4).
- `<metadata>` carries canonical JSON with exactly `{"source_sha256", "adapter", "quantum_m", "normalization"}`. **[DESIGN]** the parse-run ID is deliberately *excluded* so overlay bytes depend only on geometry and source; the parse artifact already binds the overlay by path + SHA-256.
- **Security:** no `<script>`, no `foreignObject`, no external URL, no `xlink`, no filesystem `href`, no `<use>` of external documents, no DOCTYPE, no entity declarations. Every text node escaped with `xml.sax.saxutils.escape`, every attribute with `quoteattr`. Prefer keeping source layer names **out** of the legend entirely; where any untrusted string does appear it is escaped (Layer A carries a hostile-label fixture).
- No timestamp, no duration, no absolute path, no user name.
- Written with `open("x", encoding="utf-8", newline="\n")`, one trailing LF, no trailing whitespace.

### 11.4 Omission rules

The overlay is **required** for `complete` and `partial`. It is required for `failed` **only if** normalized geometry exists and the render stays within `MAX_OVERLAY_BYTES`. Otherwise `parse-report.json` records `overlay_omitted_reason` with one of: `"no_normalized_geometry"`, `"overlay_exceeds_max_bytes"`, `"source_raster_exceeds_limits"`. It is never produced for operational failures.

---

## 12. Layer A fixtures — exact mappings

`tools/make_floorplan_fixtures.py` holds **one metric model** and derives the DXF and the PNG + annotation from it. Numbers are chosen so both paths land on exact `1e-4` multiples with **no rounding**: DXF is authored in **integer millimetres**; the raster is authored in **integer pixels** with `scale_m_per_px = 0.005` (`px * 0.005` is exact at `5e-3`). Authoring the other way round (metres first, pixels by division) fails AC-6 by exactly one quantum with a near-invisible cause.

### 12.1 Fixture `layer-a-1` — the canonical rectangle plan

An 8 m × 6 m rectangle divided by one interior wall at x = 5 m into two rooms, with two doors and two windows.

**Canonical normalized metric geometry (metres, y-up, anchored at (0,0)):**

| Wall | normalized `start` → `end` | expected ID |
|---|---|---|
| west | `(0, 0) → (0, 6)` | `w-b38b11821642` |
| south | `(0, 0) → (8, 0)` | `w-8829e7c2d2cc` |
| north | `(0, 6) → (8, 6)` | `w-0df3b64861a5` |
| mid | `(5, 0) → (5, 6)` | `w-6e35a882252a` |
| east | `(8, 0) → (8, 6)` | `w-5e931339aa8f` |

Listed in canonical wall order `(sx, sy, ex, ey)`.

| Room | canonical polygon (CCW, rotated to lexicographically smallest vertex) | expected ID |
|---|---|---|
| A (left) | `(0,0), (5,0), (5,6), (0,6)` | `r-ab354c288e8a` |
| B (right) | `(5,0), (8,0), (8,6), (5,6)` | `r-bea085b2f952` |

| Opening | type | bound wall | center | `width_m` | expected ID |
|---|---|---|---|---|---|
| N1 | window | north `w-0df3b64861a5` | `(2.0, 6.0)` | `1.2` | `o-13a46a7d32db` |
| D1 | door | south `w-8829e7c2d2cc` | `(2.5, 0.0)` | `0.9` | `o-9585ee57fe3e` |
| D2 | door | mid `w-6e35a882252a` | `(5.0, 3.0)` | `0.9` | `o-3a101c4fd203` |
| N2 | window | east `w-5e931339aa8f` | `(8.0, 4.5)` | `1.2` | `o-378d46ae40f1` |

Listed in canonical opening order `(cx, cy, width_m, type, wall_id)`.

**Exact identity serializations** (the strings hashed; SHA-256, first 12 hex, prefixed):

```text
wall|0.0000|0.0000|0.0000|6.0000                                  -> w-b38b11821642
wall|0.0000|0.0000|8.0000|0.0000                                  -> w-8829e7c2d2cc
wall|0.0000|6.0000|8.0000|6.0000                                  -> w-0df3b64861a5
wall|5.0000|0.0000|5.0000|6.0000                                  -> w-6e35a882252a
wall|8.0000|0.0000|8.0000|6.0000                                  -> w-5e931339aa8f
room|0.0000|0.0000|5.0000|0.0000|5.0000|6.0000|0.0000|6.0000      -> r-ab354c288e8a
room|5.0000|0.0000|8.0000|0.0000|8.0000|6.0000|5.0000|6.0000      -> r-bea085b2f952
opening|window|w-0df3b64861a5|2.0000|6.0000|1.2000               -> o-13a46a7d32db
opening|door|w-8829e7c2d2cc|2.5000|0.0000|0.9000                 -> o-9585ee57fe3e
opening|door|w-6e35a882252a|5.0000|3.0000|0.9000                 -> o-3a101c4fd203
opening|window|w-5e931339aa8f|8.0000|4.5000|1.2000               -> o-378d46ae40f1
```

**Expected canonical projection** (§3.5), byte-exact:

```json
{"openings":[["window","w-0df3b64861a5",[2.0,6.0],1.2],["door","w-8829e7c2d2cc",[2.5,0.0],0.9],["door","w-6e35a882252a",[5.0,3.0],0.9],["window","w-5e931339aa8f",[8.0,4.5],1.2]],"rooms":[[[0.0,0.0],[5.0,0.0],[5.0,6.0],[0.0,6.0]],[[5.0,0.0],[8.0,0.0],[8.0,6.0],[5.0,6.0]]],"units":"m","walls":[[[0.0,0.0],[0.0,6.0]],[[0.0,0.0],[8.0,0.0]],[[0.0,6.0],[8.0,6.0]],[[5.0,0.0],[5.0,6.0]],[[8.0,0.0],[8.0,6.0]]]}
```

```text
canonical_projection_sha256 = sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e
```

All hashes above were computed in a local Python shell using exactly the algorithm in §4.5 / §3.5 and independently recomputed by the operator after the architecture session; they are asserted values, not placeholders. **Both adapters must produce this identical projection and this identical hash — that is AC-6.**

#### DXF source (`layer-a-1.dxf`)

`$INSUNITS = 4` (mm); manifest `payload.units = "mm"`, `payload.scale = {"known": true}`. Modelspace only, Z = 0, no paperspace entity, no additional layout. Source coordinates are the metric model × 1000 mm plus an offset of `(+1000, +2000)` mm, so the normalization anchor is non-trivial: `tx = 1.0 m`, `ty = 2.0 m`.

| Layer | Entity | Source coordinates (mm) |
|---|---|---|
| `PWA-WALL` | `LINE` | `(1000,2000) → (9000,2000)` (south) |
| `PWA-WALL` | `LINE` | `(9000,2000) → (9000,8000)` (east) |
| `PWA-WALL` | `LINE` | `(1000,8000) → (9000,8000)` (north) |
| `PWA-WALL` | `LINE` | `(1000,2000) → (1000,8000)` (west) |
| `PWA-WALL` | `LINE` | `(6000,2000) → (6000,8000)` (mid) |
| `PWA-ROOM` | closed `LWPOLYLINE`, all bulges 0 | `(1000,2000),(6000,2000),(6000,8000),(1000,8000)` (room A) |
| `PWA-ROOM` | closed `LWPOLYLINE`, all bulges 0 | `(6000,2000),(9000,2000),(9000,8000),(6000,8000)` (room B) |
| `PWA-DOOR` | `LINE` | `(3050,2000) → (3950,2000)` → center `(3500,2000)`, width `900 mm` (D1) |
| `PWA-DOOR` | `LINE` | `(6000,4550) → (6000,5450)` → center `(6000,5000)`, width `900 mm` (D2) |
| `PWA-WINDOW` | `LINE` | `(2400,8000) → (3600,8000)` → center `(3000,8000)`, width `1200 mm` (N1) |
| `PWA-WINDOW` | `LINE` | `(9000,5900) → (9000,7100)` → center `(9000,6500)`, width `1200 mm` (N2) |

`normalization` block: `{"quantum_m":0.0001,"source_units":"mm","source_unit_scale_m":0.001,"translation_m":[1.0,2.0],"y_axis":"up","source_height_px":null,"scale_m_per_px":null}`; `payload.scale_m_per_px = null`.

Confidence: **every** entity `1.0`. `dimensions_m` is empty (the DXF convention has no dimension entity; `PWA-DIM` is reserved and forbidden). Provenance `source_kind = "dxf"`, `source_ref = dxf:modelspace/<LAYER>#<handle>`, `source_start/source_end/source_polygon/source_center/source_span` in **millimetres** exactly as tabulated.

Expected outcome: **`complete`, CLI 0, overlay present, G1-eligible.**

#### Raster source (`layer-a-1.png` + `layer-a-1.annotation.json`)

Image `2000 × 1800 px`, `scale_m_per_px = 0.005`; manifest `payload.units = "m"`, `payload.scale = {"known": true, "m_per_px": 0.005}`. Forward transform `X = x_px*0.005`, `Y = (1800 - y_px)*0.005`, anchor `tx = 1.0`, `ty = 2.0` — identical to the DXF path by construction.

| Corner (metric) | pixel |
|---|---|
| `(0,0)` | `(200, 1400)` |
| `(8,0)` | `(1800, 1400)` |
| `(8,6)` | `(1800, 200)` |
| `(0,6)` | `(200, 200)` |
| `(5,0)` | `(1200, 1400)` |
| `(5,6)` | `(1200, 200)` |

```json
{
  "image": { "source_image_ref": "project/inputs/originals/layer-a-1.png",
             "sha256": "sha256:<computed by the fixture generator>",
             "width_px": 2000, "height_px": 1800 },
  "scale_m_per_px": 0.005,
  "walls": [
    { "start_px": [200,1400],  "end_px": [1800,1400] },
    { "start_px": [1800,1400], "end_px": [1800,200]  },
    { "start_px": [200,200],   "end_px": [1800,200]  },
    { "start_px": [200,1400],  "end_px": [200,200]   },
    { "start_px": [1200,1400], "end_px": [1200,200]  }
  ],
  "rooms": [
    { "polygon_px": [[200,1400],[1200,1400],[1200,200],[200,200]] },
    { "polygon_px": [[1200,1400],[1800,1400],[1800,200],[1200,200]] }
  ],
  "openings": [
    { "type": "door",   "wall_index": 0, "center_px": [700,1400], "width_m": 0.9 },
    { "type": "door",   "wall_index": 4, "center_px": [1200,800], "width_m": 0.9 },
    { "type": "window", "wall_index": 2, "center_px": [600,200],  "width_m": 1.2 },
    { "type": "window", "wall_index": 1, "center_px": [1800,500], "width_m": 1.2 }
  ],
  "declared_dimensions": [
    { "a_px": [200,1400], "b_px": [1800,1400], "length_m": 8.0 },
    { "a_px": [200,1400], "b_px": [200,200],   "length_m": 6.0 }
  ]
}
```

Note the annotation array order is deliberately **not** canonical order — that is what makes the fixture prove ID stability under input reordering (AC-8).

`normalization` block: `{"quantum_m":0.0001,"source_units":"px","source_unit_scale_m":0.005,"translation_m":[1.0,2.0],"y_axis":"flipped_from_raster","source_height_px":1800,"scale_m_per_px":0.005}`; `payload.scale_m_per_px = 0.005`.

**Expected confidences (AC-7 — intentionally different from DXF):** dimension 1 endpoints normalize to `(0,0)` and `(8,0)` = the south wall's endpoints; dimension 2 endpoints normalize to `(0,0)` and `(0,6)` = the west wall's endpoints. Both dimensions pass `DIMENSION_TOL` (measured 8.0 and 6.0 exactly).

| Entity | confidence | why |
|---|---|---|
| south `w-8829e7c2d2cc` | `0.9` | tied to declared dimension 1 |
| west `w-b38b11821642` | `0.9` | tied to declared dimension 2 |
| north `w-0df3b64861a5`, mid `w-6e35a882252a`, east `w-5e931339aa8f` | `0.6` | scale only |
| room A `r-ab354c288e8a`, room B `r-bea085b2f952` | `0.6` | no dimension matches two of their vertices |
| D1 `o-9585ee57fe3e` | `0.9` | inherits the south wall |
| N1 `o-13a46a7d32db`, D2 `o-3a101c4fd203`, N2 `o-378d46ae40f1` | `0.6` | inherit `0.6` walls |

Minimum confidence is `0.6 >= 0.5`, so **no** `PARSE_LOW_CONFIDENCE`. Expected outcome: **`complete`, CLI 0, overlay present, G1-eligible.**

Provenance `source_kind = "annotation"`, `source_ref = annotation:walls[i]` / `annotation:rooms[i]` / `annotation:openings[i]`, `source_*` coordinates in **pixels** exactly as authored.

#### Overlay coordinate examples

Raster overlay: `viewBox="0 0 2000 1800"`, embedded PNG at `(0,0,2000,1800)`.

| Normalized | inverse | SVG coordinate |
|---|---|---|
| west wall `(0,0)→(0,6)` | `x=(0+1.0)/0.005`, `y=1800-(0+2.0)/0.005` | `200,1400 → 200,200` |
| D1 center `(2.5,0)` | `x=(2.5+1.0)/0.005`, `y=1800-(0+2.0)/0.005` | `700,1400` |
| N2 center `(8,4.5)` | `x=(8+1.0)/0.005`, `y=1800-(4.5+2.0)/0.005` | `1800,500` |

DXF overlay: bbox `x ∈ [1000, 9000]`, `y ∈ [2000, 8000]` mm → `bbox_w=8000`, `bbox_h=6000`, `margin = 0.05 * 8000 = 400` → `viewBox="0 0 8800 6800"`; `svg_x = x_u - 600`, `svg_y = 8400 - y_u`.

| Normalized | source (mm) | SVG coordinate |
|---|---|---|
| west wall `(0,0)→(0,6)` | `(1000,2000) → (1000,8000)` | `400,6400 → 400,400` |
| D1 center `(2.5,0)` | `(3500,2000)` | `2900,6400` |
| N2 center `(8,4.5)` | `(9000,6500)` | `8400,1900` |

Both overlays are byte-deterministic and are tracked under `evidence/PLAN-002/overlays/layer-a-1-dxf.svg` and `layer-a-1-raster.svg`.

### 12.2 Fixture `layer-a-1r` — reordered input, identical output (AC-8)

The same annotation with `walls`, `rooms`, `openings` and `declared_dimensions` arrays shuffled. Expected: **every** ID, the canonical projection and its SHA-256 are byte-identical to `layer-a-1`. Only `provenance.source_ref` indices differ.

### 12.3 Fixture `layer-a-2` — an addition that moves the anchor (AC-8, documented ID change)

`layer-a-1` DXF plus one extra `PWA-WALL` `LINE` at `(0,2000) → (0,8000)` mm (metric `(-1,0) → (-1,6)` before anchoring). `tx` moves from `1.0` to `0.0`, so **every** normalized x shifts by `+1` and **every** ID changes:

| Entity | `layer-a-2` normalized | expected ID |
|---|---|---|
| new wall | `(0,0) → (0,6)` | `w-b38b11821642` |
| west | `(1,0) → (1,6)` | `w-7b555eb3e572` |
| south | `(1,0) → (9,0)` | `w-4d4e1fd95001` |
| north | `(1,6) → (9,6)` | `w-27fa6c02f942` |
| mid | `(6,0) → (6,6)` | `w-ff541ff1603d` |
| east | `(9,0) → (9,6)` | `w-ac11489133c8` |
| room A | `(1,0),(6,0),(6,6),(1,6)` | `r-ad41ae5dd009` |
| room B | `(6,0),(9,0),(9,6),(6,6)` | `r-505dcdfeef3b` |
| N1 | window, `w-27fa6c02f942`, `(3,6)`, `1.2` | `o-d3668641a7e3` |
| D1 | door, `w-4d4e1fd95001`, `(3.5,0)`, `0.9` | `o-5ebc547d438d` |
| D2 | door, `w-ff541ff1603d`, `(6,3)`, `0.9` | `o-da9fe0362785` |
| N2 | window, `w-ac11489133c8`, `(9,4.5)`, `1.2` | `o-a46bb7f6f9d3` |

> **Assert this explicitly:** the *newly added* wall receives ID `w-b38b11821642`, which was `layer-a-1`'s **west** wall ID, because after re-anchoring its geometry tuple is exactly the one the west wall previously occupied. That is correct content-addressed behaviour — IDs address geometry, not entities — and the test must assert it rather than treat it as a collision. `PARSE_DUPLICATE_ENTITY` fires only on a repeat **within the same run**.

Expected outcome: `complete`, CLI 0. Also assert the `layer-a-2` walls do not degenerate the opening bindings (all four openings still resolve to exactly one wall).

### 12.4 Fixture `layer-a-3` — an addition that does not move the anchor (AC-8)

`layer-a-1` plus one extra room whose polygon lies **below and left of** the walls: `(-1,-1), (2,-1), (2,0), (-1,0)`. Because the anchor is computed over **wall endpoints only**, `tx`/`ty` are unchanged and every `layer-a-1` ID is preserved. The new room's ID is `r-36a3ec269e03` (identity string `room|-1.0000|-1.0000|2.0000|-1.0000|2.0000|0.0000|-1.0000|0.0000`). Its top edge is collinear with the south wall / room A's bottom edge, which is a shared-boundary touch and therefore **must not** emit `PARSE_ROOM_BOUNDARY_UNMATCHED`. Expected outcome: `complete`, CLI 0.

### 12.5 Adapter-equality test (AC-6 keystone)

```python
def test_canonical_projection_matches_across_adapters():
    dxf  = parse_layer_a_via_dxf()
    ann  = parse_layer_a_via_annotation()
    assert canonical_projection(dxf) == canonical_projection(ann)
    assert projection_sha(dxf) == "sha256:e5041ddc...e77e"
    assert projection_sha(ann) == "sha256:e5041ddc...e77e"
    # and the fields that must intentionally differ
    assert {w.confidence for w in dxf.walls} == {1.0}
    assert {w.confidence for w in ann.walls} == {0.6, 0.9}
    assert dxf.normalization["source_units"] == "mm"
    assert ann.normalization["source_units"] == "px"
```

---

## 13. Failure fixtures — code, severity, outcome, overlay, artifacts, CLI

Legend for **Finalized set**: **D** = derived manifest + derived quality report + `floorplan_parse` + `assumptions` + `parse-report`; **none** = nothing finalized (bounded staging may remain).

### 13.1 Operational / preflight (CLI 2, nothing finalized)

| Fixture | Trigger | Code | Sev | Outcome | Overlay | Finalized | CLI |
|---|---|---|---|---|---|---|---|
| `f-usage-missing-arg` | `--parse-run-id` absent | (usage) | — | operational | no | none | 2 |
| `f-traversal` | `--source-run runs/../outside` | (containment) | — | operational | no | none | 2 |
| `f-ancestor-reparse` | a junction in the ancestor chain under `runs_root` | (containment) | — | operational | no | none | 2 |
| `f-existing-final` | `runs/<parse-run-id>` already exists | (lifecycle) | — | operational | no | none | 2 |
| `f-existing-staging` | `runs/.staging/<parse-run-id>` already exists | (lifecycle) | — | operational | no | none | 2 |
| `f-hash-manifest` | source `project_manifest.json` byte-edited | `PARSE_SOURCE_HASH_MISMATCH` | error | operational | no | none | **2** |
| `f-hash-quality` | source `input_quality_report.json` byte-edited | `PARSE_SOURCE_HASH_MISMATCH` | error | operational | no | none | **2** |
| `f-hash-inventory` | one inventory PNG byte-edited (**Option A**) | `PARSE_SOURCE_HASH_MISMATCH` | error | operational | no | none | **2** |
| `f-quality-partial` | source quality `status="partial"` | (invalid source contract) | — | operational | no | none | **2** |
| `f-quality-blockers` | source quality `complete` but `blockers=["x"]` | (invalid source contract) | — | operational | no | none | **2** |
| `f-source-unsupported` | floorplan is `.dwg`; no adapter accepts | `PARSE_SOURCE_UNSUPPORTED` | error | operational | no | none | 2 |
| `f-annotation-schema` | annotation violates `floorplan_annotation` 1.0.0 | (schema) | — | operational | no | none | 2 |
| `f-annotation-oversize` | annotation > `MAX_ANNOTATION_BYTES` | `PARSE_RESOURCE_LIMIT` | error | operational | no | none | 2 |
| `f-dxf-oversize` | DXF > `MAX_DXF_BYTES`, checked before spawn | `PARSE_RESOURCE_LIMIT` | error | operational | no | none | 2 |
| `f-worker-garbage` | worker emits malformed JSON | (untrusted output) | — | operational | no | none | 2 |

`f-hash-inventory` asserts the Option-A consequence directly: **no** finalized run, **no** envelope artifact carrying `PARSE_SOURCE_HASH_MISMATCH`, and the code present only in the stdout diagnostic and the retained staging `parse-report.json`.

### 13.2 Failed domain parse (CLI 3, full diagnostic set finalized, `status="failed"`)

| Fixture | Trigger | Code | Sev | Overlay | Finalized | CLI |
|---|---|---|---|---|---|---|
| `f-scale-unknown` | complete/blocker-free source, `scale.known=false` | `PARSE_SCALE_UNKNOWN` | error | omitted (`no_normalized_geometry`) | D | **3** |
| `f-scale-contradictory` | annotation `scale_m_per_px=0.004` vs manifest `0.005` | `PARSE_SCALE_UNKNOWN` | error | omitted | D | 3 |
| `f-units-mismatch` | `$INSUNITS=4` (mm), manifest `units="m"` | `PARSE_UNITS_MISMATCH` | error | omitted | D | 3 |
| `f-units-unknown` | `$INSUNITS=0`; or manifest `units="unknown"` | `PARSE_UNITS_MISMATCH` | error | omitted | D | 3 |
| `f-unsupported-arc` | `ARC` on `PWA-WALL` | `PARSE_UNSUPPORTED_FEATURE` | error | present (other geometry normalizes) | D | 3 |
| `f-unsupported-bulge` | `LWPOLYLINE` on `PWA-ROOM` with one bulge `0.1` | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-unsupported-z` | `LINE` on `PWA-WALL` with `z=1.0` | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-unsupported-insert` | `INSERT` in modelspace | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-unsupported-xref` | XREF definition + `IMAGE` entity | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-unsupported-paperspace` | one entity in paperspace | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-unsupported-layout` | a second non-empty layout | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-unsupported-text` | `MTEXT` on `PWA-ROOM` | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-unsupported-dim` | `LINE` on reserved `PWA-DIM` | `PARSE_UNSUPPORTED_FEATURE` | error | present | D | 3 |
| `f-empty-walls` | annotation `walls: []` | `PARSE_EMPTY_GEOMETRY` | error | omitted | D | 3 |
| `f-empty-rooms` | annotation `rooms: []` | `PARSE_EMPTY_GEOMETRY` | error | omitted | D | 3 |
| `f-empty-after-norm` | one wall of length `0.01`, one zero-area room | `PARSE_EMPTY_GEOMETRY` + `PARSE_DEGENERATE_WALL` | error | present | D | 3 |
| `f-open-polygon` | DXF `LWPOLYLINE.closed = False` | `PARSE_OPEN_POLYGON` | error | present | D | 3 |
| `f-open-polygon-dup` | annotation polygon with consecutive duplicate vertices | `PARSE_OPEN_POLYGON` | error | present | D | 3 |
| `f-self-intersect` | bowtie polygon `(0,0),(5,6),(5,0),(0,6)` | `PARSE_SELF_INTERSECTING_POLYGON` | error | present | D | 3 |
| `f-zero-area` | collinear polygon `(0,0),(2,0),(4,0)` | `PARSE_SELF_INTERSECTING_POLYGON` | error | present | D | 3 |
| `f-degenerate-wall` | wall length `0.0499` | `PARSE_DEGENERATE_WALL` | error | present | D | 3 |
| `f-duplicate-wall` | two walls with identical normalized endpoints | `PARSE_DUPLICATE_ENTITY` | error | present | D | 3 |
| `f-duplicate-room` | two identical room polygons | `PARSE_DUPLICATE_ENTITY` | error | present | D | 3 |
| `f-unknown-wall-ref` | door 3 m away from every wall | `PARSE_UNKNOWN_WALL_REF` | error | present | D | 3 |
| `f-unknown-wall-index` | annotation `wall_index: 99` | `PARSE_UNKNOWN_WALL_REF` | error | present | D | 3 |
| `f-ambiguous-wall-ref` | two coincident collinear walls; door on both | `PARSE_AMBIGUOUS_WALL_REF` | error | present | D | 3 |
| `f-opening-off-wall` | door offset `0.0201` from the wall line | `PARSE_OPENING_OFF_WALL` | error | present | D | 3 |
| `f-opening-wrong-ref` | annotation `wall_index` names a wall other than the unique geometric match | `PARSE_OPENING_OFF_WALL` | error | present | D | 3 |
| `f-opening-overhang` | door width `0.9`, `t = 0.4498` from the wall end | `PARSE_OPENING_WIDTH_EXCEEDS_WALL` | error | present | D | 3 |
| `f-dimension-bad` | declared `8.0`, measured `8.0801` (tol `0.08`) | `PARSE_DIMENSION_INCONSISTENT` | error | present | D | 3 |
| `f-limit-walls` | `MAX_WALLS + 1` walls | `PARSE_RESOURCE_LIMIT` | error | omitted | D | 3 |
| `f-limit-vertices` | polygon with `MAX_POLYGON_VERTICES + 1` vertices | `PARSE_RESOURCE_LIMIT` | error | omitted | D | 3 |
| `f-limit-coordinate` | wall endpoint at `1e6 m` | `PARSE_RESOURCE_LIMIT` | error | omitted | D | 3 |
| `f-limit-entities` | DXF with `MAX_DXF_ENTITIES + 1` entities (post-load) | `PARSE_RESOURCE_LIMIT` | error | omitted | D | 3 |
| `f-timeout` | worker stub that sleeps past `PARSER_TIMEOUT_S` | `PARSE_TIMEOUT` | error | omitted | D | 3 |
| `f-overlay-too-big` | valid geometry, raster render exceeding `MAX_OVERLAY_BYTES` | `PARSE_RESOURCE_LIMIT` | error | omitted (`overlay_exceeds_max_bytes`) | D | 3 |

### 13.3 Warnings → `partial` (CLI 1, full set finalized, `status="partial"`, overlay required)

| Fixture | Trigger | Code | Sev | CLI |
|---|---|---|---|---|
| `f-unmapped-layer` | `LINE` on layer `NOTES` | `PARSE_UNMAPPED_SOURCE_ENTITY` | warn | **1** |
| `f-room-boundary-cross` | extra room `(4,1),(9,1),(9,5),(4,5)`; its top edge properly crosses the mid wall's room edge at `(5,5)` | `PARSE_ROOM_BOUNDARY_UNMATCHED` | warn | **1** |
| `f-low-confidence` | unit-level constructed `NormalizedGeometry` with one entity at `0.4999` (unreachable from any Part 1 source fixture — §9.1) | `PARSE_LOW_CONFIDENCE` | warn | **1** |
| `f-hostile-label` | DXF layer name `NOTES<script>alert(1)</script>` on an ignored entity | `PARSE_UNMAPPED_SOURCE_ENTITY` | warn | **1** — plus assert the overlay contains no `<script` and the label is escaped |

### 13.4 Tolerance boundary fixtures (must pass, `complete`, CLI 0)

| Fixture | Value | Boundary asserted |
|---|---|---|
| `b-wall-exact` | wall length exactly `0.0500` | `DEGENERATE_WALL_M` is exclusive |
| `b-offset-exact` | opening perpendicular distance exactly `0.0200` | `OPENING_OFFSET_M` is inclusive |
| `b-span-exact` | door width `0.9`, `t` exactly `0.4500` from the end | span fit inclusive at `width/2` |
| `b-span-quantum` | `t` exactly `0.4499` | inclusive with one quantum of slack |
| `b-dimension-exact` | declared `8.0`, measured `8.08` | `DIMENSION_TOL` fails only when strictly exceeded |
| `b-confidence-half` | constructed entity confidence exactly `0.5` | `LOW_CONFIDENCE_THRESHOLD` is exclusive |
| `b-quantize-half-even` | source values `0.00005` and `0.00015` | `ROUND_HALF_EVEN` → `0.0000` and `0.0002` |
| `b-negative-zero` | source value `-0.00001` | quantizes to `-0.0000`, emits `0.0` and keys `"0.0000"` |

---

## 14. TDD slices and the AC-1..AC-23 traceability matrix

### 14.1 Slices (red test first; watch it fail for the right reason; minimum code to green; then refactor)

| # | Slice | First failing test |
|---|---|---|
| 1 | exact-version schemas + derived-run lifecycle (red) | `tests/unit/test_contract_versions.py` — 1.0.0 validates against 1.0.0, 1.1.0 against 1.1.0, a 1.1.0 document mislabeled `1.0.0` is rejected, duplicate `(schema_id, schema_version)` or duplicate `$id` is rejected; `tests/integration/test_plan002_parse_run.py::test_staging_left_on_operational_failure` |
| 2 | catalog implementation | slice 1 green **and** the entire pre-existing suite still green (AC-2 gate) |
| 3 | fixtures + annotation validation | `tests/unit/test_floorplan_sources.py` annotation-schema cases; `test_schemas_roundtrip` inventory becomes catalog-derived 14 |
| 4 | normalization + stable IDs | `tests/unit/test_floorplan_normalize.py` — the §12.1 identity strings and IDs, quantization boundaries, `-0`, walls-only anchor, reorder stability, `layer-a-2` anchor-move, duplicates fail |
| 5 | invariant validator | `tests/unit/test_floorplan_validate.py` — every error code, both reachable warnings, and every §13.4 boundary |
| 6 | overlay | `tests/unit/test_floorplan_overlay.py` — byte-identical across runs, XML-valid, no script/external/`xlink`/DOCTYPE, hostile label escaped, inverse within `QUANTUM_M/s` |
| 7 | DXF + annotation adapters | `tests/golden/test_floorplan_golden.py::test_canonical_projection_matches_across_adapters` (**AC-6 keystone**) |
| 8 | CLI + finalization + failure matrix | `tests/integration/test_plan002_failures.py` — exact `(code, severity, finalized artifact set, status, CLI exit)` per §13 row |
| 9 | full regression, cross-provider review, handoff | full pytest + `git diff --check` + evidence + `HANDOFF-PLAN-002-to-PLAN-003-001.md` |

Slice 2 is the AC-2 gate: if any pre-existing test goes red there, fix the catalog — never edit the historical test.

### 14.2 Traceability matrix

| AC | Modules | Tests | Fixtures | Expected evidence |
|---|---|---|---|---|
| AC-1 | `contracts.py` | `test_contract_versions.py` | existing 1.0.0 examples + new 1.1.0 example | `evidence/PLAN-002/test-results/RUN-*/junit.xml` |
| AC-2 | `contracts.py`, `intake.py` | full pre-existing suite, `test_schemas_roundtrip.py` | `tests/fixtures/contracts/examples.json` | `summary.md` showing zero regressions |
| AC-3 | `runs.py` | `test_plan002_parse_run.py`, `test_plan002_failures.py` | every §13 fixture | pre/post source-run hash table in `acceptance.md` |
| AC-4 | `runs.py` | `test_plan002_parse_run.py` | `f-existing-final`, `f-existing-staging` | `failures/parse-failure-matrix.json` |
| AC-5 | `runs.py`, `builder.py` | `test_plan002_parse_run.py::test_staging_left_on_operational_failure` | `f-hash-inventory`, `f-worker-garbage` | staging listing in `acceptance.md` |
| AC-6 | `normalize.py`, both adapters | `test_floorplan_golden.py::test_canonical_projection_matches_across_adapters` | `layer-a-1` DXF + raster | `determinism/geometry-projection-hashes.json` containing `sha256:e5041ddc…e77e` twice |
| AC-7 | both adapters, `normalize.py` | `test_floorplan_golden.py::test_adapter_specific_fields` | `layer-a-1` | `parse/layer-a-1-dxf.json`, `parse/layer-a-1-raster.json` |
| AC-8 | `normalize.py` | `test_floorplan_normalize.py` | `layer-a-1`, `layer-a-1r`, `layer-a-2`, `layer-a-3`, `f-duplicate-*` | ID tables in `acceptance.md` matching §12.1/§12.3/§12.4 |
| AC-9 | `validate.py` | `test_floorplan_validate.py` | `f-open-polygon*`, `f-self-intersect`, `f-zero-area` | `failures/parse-failure-matrix.json` |
| AC-10 | `validate.py::resolve_opening_wall` | `test_floorplan_validate.py` | `f-unknown-wall-*`, `f-ambiguous-wall-ref`, `f-opening-*`, `b-span-*` | same |
| AC-11 | `validate.py`, `config.py` | `test_floorplan_validate.py` | `f-dimension-bad`, `b-dimension-exact`, `f-scale-*` | same |
| AC-12 | `dxf_source.py`, `dxf_worker.py` | `test_floorplan_sources.py` | every `f-unsupported-*`, `f-unmapped-layer` | same |
| AC-13 | `builder.py`, `runs.py` | `test_plan002_parse_run.py` | `layer-a-1` both paths | `parse/layer-a-*.json` with full provenance |
| AC-14 | `overlay.py` | `test_floorplan_overlay.py` | `layer-a-1` both paths | `overlays/layer-a-1-*.svg` + repeat-run byte equality log |
| AC-15 | `overlay.py`, evidence policy | `test_floorplan_overlay.py::test_hostile_label_escaped` | `f-hostile-label` | escaped-output assertion; `real-plan-redacted.json` contains no path/name |
| AC-16 | `builder.py`, `cli.py` | `test_plan002_failures.py` | `f-unmapped-layer`, `f-low-confidence` | CLI 1 rows in `parse-failure-matrix.json` |
| AC-17 | `runs.py` | `test_plan002_failures.py` | `f-traversal`, `f-ancestor-reparse`, `f-hash-*` | CLI 2 rows, no finalized run |
| AC-18 | `config.py`, `dxf_source.py`, `validate.py` | `test_floorplan_sources.py`, `test_plan002_failures.py` | `f-*-oversize`, `f-limit-*`, `f-timeout` | same |
| AC-19 | `dxf_worker.py` | `test_floorplan_sources.py::test_external_refs_never_opened` | `f-unsupported-xref` | assertion that no external path is opened (patched `open`) |
| AC-20 | `cli.py`, `builder.py` | `test_plan002_failures.py` | **all** of §13.1/§13.2/§13.3/§13.4 | `failures/parse-failure-matrix.json` — one row per fixture with `(code, severity, finalized set, status, cli_exit)` |
| AC-21 | — | full suite | — | `command.log`, `junit.xml`, `coverage.xml`, `git diff --check` output |
| AC-22 | — | `test_plan002_parse_run.py::test_dependencies_unchanged` | — | `git diff -- pyproject.toml uv.lock` empty |
| AC-23 | — | review checklist | — | `acceptance.md` statement: no network, install, GPU, H200, remote or cloud action; G7/G8 deferred |

---

## 15. Windows / process / containment pitfalls and verification commands

1. **`os.replace` on a directory fails on Windows with `PermissionError` if any handle inside is open.** Close every file object, every PIL image and both worker stdio temp files before finalize.
2. **No directory `fsync` on Windows.** Match PLAN-001: file-level `fsync` only (already inside `copy_immutable`). Do not add a directory fsync and do not silently swallow one elsewhere.
3. **Same-volume rename only.** `runs/.staging` and `runs/` are already siblings; keep them so.
4. **Containment must `lstat`-walk the *unresolved* path.** `Path.resolve()` follows the very symlink the check exists to detect. Re-run the per-component check for every file immediately before it is opened or copied.
5. **Subprocess stdio via temp files, never `PIPE`.** A chatty worker deadlocks the parent. `stdin=DEVNULL`; `stdout`/`stderr` to capped temp files; truncate reads at `MAX_WORKER_STDIO_BYTES`.
6. **Windows has no stdlib job-object tree kill.** POSIX: `start_new_session=True` + `os.killpg`. Windows: `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW` + `proc.kill()`, backed by the worker's enforced **no-children** invariant (asserted and tested). Do **not** claim tree termination on Windows; ADR-0005 already records the residual.
7. **No portable hard RSS limit on Windows.** Byte/pixel/entity/vertex/count/time/output caps bound normal work; a hard-memory sandbox stays deferred, not falsely claimed.
8. **Hebrew + space in the repository path.** Always quote absolute paths; use `-LiteralPath` in PowerShell; never build long nested-quoting one-liners around the path — write a `.ps1`/`.mjs`/`.py` file and run it. Python file I/O must be explicit UTF-8.
9. **Never write to `/tmp`.** It does not exist on this machine. Temp files go under the session scratchpad or a project-local `.tmp/`.
10. **Do not chain commands of different permission levels with `&&`.** Run `python -m pytest` separately from any `git` command.
11. **`git status` before committing** to catch shell-quoting junk files (`$p`, `{`, `0)`); delete any that appear.
12. **Worker env is minimal and explicit:** `PYTHONPATH` → `src` only, `PYTHONNOUSERSITE=1`, no inherited extras.

**Verification commands** (from the worktree, root interpreter, inherited `PYTHONPATH` cleared; no `uv sync`, no install, no network):

```bash
python -m pytest -q                                          # AC-21 full suite
python -m pytest tests/unit/test_contract_versions.py -q     # AC-1
python -m pytest tests/unit/test_floorplan_normalize.py -q   # AC-8
python -m pytest tests/unit/test_floorplan_validate.py -q    # AC-9..AC-11
python -m pytest tests/unit/test_floorplan_overlay.py -q     # AC-14, AC-15
python -m pytest tests/golden/test_floorplan_golden.py -q    # AC-6 keystone, AC-7
python -m pytest tests/integration/test_plan002_failures.py -q  # AC-20
python tools/make_floorplan_fixtures.py --out tests/golden/floorplan
python tools/parse_floorplan.py --runs-root runs --source-run runs/<intake-id> \
       --parse-run-id <new-id> --annotation <relative-annotation-path>
git diff --check                                             # AC-21
git diff -- pyproject.toml uv.lock                           # must be empty, AC-22
```

Evidence lands under `evidence/PLAN-002/**` per PLAN-002 §15.

---

## 16. Routing metadata

```yaml
name: plan-002-canonical-spatial-design-brief
role: Bounded post-approval spatial/geometry architect — canonical implementation design for PLAN-002
plan_id: PLAN-002
baseline_commit: a047b7c
provider: anthropic
requested_model: "claude-opus-5"
actual_model_id: "claude-opus-5"
effort_normalized: HIGH
effort_provider_value: high
thinking: extended spatial/contract reasoning
fallback_provider: none
fallback_model: none
model_reason: >
  Coordinate normalization and inverse transforms, quantization/identity rules,
  polygon and opening-binding invariants, source-aligned overlay design, and the
  derived-run failure matrix — all requiring exact, non-approximate spatial reasoning
  against a locked contract.
escalate_when: >
  Any contract mutation, run-lifecycle ambiguity, new dependency, network/GPU need,
  or any change to the coordinate transform, quantization/identity rules, DXF convention,
  overlay contract, G1 eligibility or AC-20 semantics.
dispatch_max_turns_requested: 18
runtime_num_turns_reported: 27
runtime_assistant_messages_observed: 36
runtime_duration_ms: 951913
runtime_input_tokens: 2196
runtime_output_tokens: 79910
runtime_cache_read_input_tokens: 1160140
runtime_cache_creation_input_tokens: 392370
runtime_web_search_requests: 0
session_id: "4a3791b1-9344-4730-a5b9-be18f7e4796e"
provider_route: firstParty
dispatch_allowed_tools_requested: [Read, Glob, Grep, Skill]
runtime_tool_calls_observed:
  Skill: 3
  Read: 11
  Bash: 6
  Write: 1
  ToolSearch: 1
runtime_tool_scope_note: >
  Claude plan mode supplied Bash, Write and ToolSearch despite the requested allow-list.
  Transcript inspection confirmed the Bash calls were local repository reads, local Python
  hash calculations, and cleanup; Write produced the Claude plan output. No web search or
  network tool call occurred, and no repository product/design file was changed by Claude.
cross_provider_handoff:
  implementer: { provider: openai, model: "runtime-selected per MODEL-ROUTING-v1; record actual", effort_normalized: HIGH }
  code_spatial_reviewer: { provider: anthropic, model: "claude-opus-5", effort_normalized: HIGH }
  rule: >
    If the implementer falls back to Anthropic, the reviewer must switch to OpenAI or the
    gate blocks. No same-provider silent substitution. Provider/model/effort/runtime metadata
    must come from runtime metadata, never from model self-description.
status: DONE (design delivered; implementation NOT started in this session)
boundary_respected: >
  Repository-read-only Claude subprocess — no product implementation, test run, install,
  network, commit/merge/push, H200/GPU/project cloud or remote runtime action. Claude wrote
  its local plan output and two temporary local calculation scripts that were removed;
  the operator copied the reviewed plan to this canonical evidence path. G7/G8 remain deferred.
skills_invoked: [architecture, test-driven-development, threat-modeling-expert]
open_blockers: []
```

`--max-turns 18` was present in the dispatch command, while the Claude result envelope reported
`num_turns: 27` and the transcript contains 36 assistant-message records. These counters have
different/undocumented accounting semantics in the CLI, so this brief records all three values
without claiming strict equality. The session was still bounded by one completed invocation
(951,913 ms), exited successfully, used only `claude-opus-5`, and had no fallback.

---

## 17. Approval analysis

**Does this design introduce any new contract, scope change, or critical Geometry/Visual gate? — No.**

Checked item by item against PLAN-002 §20's fail-closed gate list:

| Gate-triggering item | Changed here? |
|---|---|
| normalized coordinate transform | **No.** §4.1 restates the approved DXF y-up / raster `metric_y = (height_px - y_px) * scale` forms verbatim. §4.6 states their inverses and fixes a sign error present only in the superseded draft, not in the PLAN. |
| quantization / identity rules | **No.** `1e-4`, `Decimal(str(v)).quantize(..., ROUND_HALF_EVEN)`, `-0 → 0`, walls-only anchor, lexicographic endpoint order, CCW + lexicographic rotation, SHA-256 first-12-hex — all as approved. The `w-`/`r-`/`o-` prefix and the exact key delimiter are serialization detail inside an opaque `minLength: 1` string. |
| exact DXF convention | **No.** Layer/entity table, `$INSUNITS ∈ {4,5,6}`, case-sensitive ASCII matching, disposition table and paperspace/layout rules are reproduced unchanged. |
| overlay alignment / security contract | **No.** Source-aligned, self-contained, no script/external/`foreignObject`, escaped labels, deterministic ordering, size caps. Excluding the parse-run ID from `<metadata>` makes the overlay *more* deterministic and adds no capability. |
| G1 eligibility | **No.** Only `complete` with no error finding, no low-confidence finding and no unresolved `requires_human_ack` is G1-eligible; correction is a fresh derived run. |
| source-hash / source-quality / scale outcome semantics (AC-20) | **No.** Option A applied uniformly: every pre-parse mismatch → `PARSE_SOURCE_HASH_MISMATCH`, CLI 2, no finalized run; incomplete/blocked quality → CLI 2, no finalized run; complete + blocker-free + missing/contradictory scale → `PARSE_SCALE_UNKNOWN`, failed diagnostic set, CLI 3. |
| new schema field / error code / artifact / CLI flag | **No.** None added. Room-to-room adjacency is explicitly **not** emitted and no adjacency field is invented (§6.2). |

The **[DESIGN]** items — `source_ref` grammar, opening ordering key, the room-boundary proper-crossing predicate, the dimension-tie predicate for selecting among the three approved confidence values, `OVERLAY_MARGIN_FRACTION`, `DIMENSION_TIE_M`, the ID prefix, the `translation_m` sign convention and the module/file layout — are implementation specifications inside spaces the approved plan left to the implementer. None of them alters an approved value, adds a field, or relaxes a gate.

**Conclusion: no additional Moshe approval is required for this design document itself.** It is implementation-ready under the existing PLAN-002 approval.

**Retained gates remain fail-closed and unchanged:**

- the **first implementation-generated Layer A source-aligned overlay** must still be presented to Moshe at the critical **Visual/Geometry evidence** gate before it can be treated as accepted G1 evidence or handed to PLAN-003;
- any Layer B use still requires Moshe's rights/non-sensitivity attestation, and Layer B overlays stay private and untracked;
- any future change to the coordinate transform, quantization/identity rules, DXF convention, overlay contract, G1 eligibility or AC-20 semantics is a critical **Geometry/Contract** gate requiring a revised PLAN and explicit approval;
- G7/G8, H200/GPU, cloud, remote execution and spending remain **DEFERRED TO PART 2** and are not approvable through PLAN-002.
