# PLAN-002 Implementation Brief — for the OpenAI Codex implementer

**Author:** plan-002-spatial-architect (Anthropic / claude-opus-5 / HIGH)
**Status of this document:** read-only architectural brief. No code was written, no test was run, no file in the repo was modified.
**Authority:** PLAN-002 §1–§20 is **locked**. This brief adds no scope and changes no contract. Where the plan text admits two readings, the item is marked `AMBIGUITY` and the implementer must resolve it with Moshe/the reviewer, not silently.

> **Resolution addendum (canonical project update, 2026-08-09):** this brief preserves the architect's point-in-time observations. After it was delivered, the PLAN approval was canonicalized in the plan header, PROJECT-STATE.yaml, ADR-0004 and ADR-0005. Moshe then explicitly selected hash Option A and approved the recommended source-quality/scale semantics. PLAN-002 sections 5, 11, 14 and 20 plus ADR-0005 now supersede the open blocker/ambiguity statuses in sections 0, 7.5 and 12 below: every pre-parse source hash mismatch is CLI 2 with no finalized run; incomplete/blocked source quality is CLI 2 with no finalized run; only a complete, blocker-free source with missing/contradictory scale reaches `PARSE_SCALE_UNKNOWN`, failed diagnostics and CLI 3.

---

## 0. Context and blocker

PLAN-002 authorizes a deterministic, local, contract-first floorplan parser: a narrow DXF convention and a schema-validated manual annotation path, both projecting to one canonical metric geometry, emitting `floorplan_parse` 1.1.0 + `assumptions` 1.0.0 + a source-aligned SVG into a **new immutable derived run**. This brief converts that plan into module boundaries, exact data shapes, algorithms and a TDD order so the Codex implementer can start without re-deriving spatial decisions.

### BLOCKER — approval is not recorded in the repository

The dispatch says to treat the Moshe approval as locked. The repository does not corroborate that:

| Location | Recorded value |
|---|---|
| `docs/plans/PLAN-002-floorplan-parsing.md:4` | `Status: **REVIEW** — requires explicit Moshe approval; implementation is forbidden before approval.` |
| `PROJECT-STATE.yaml` `human_gates.plan_002_approval` | `"pending Moshe approval; independent OpenAI review APPROVE, no implementation authorized"` |
| `PROJECT-STATE.yaml` `next_actions` | `block_for_Moshe_approval_on_D_004_D_012_D_013_D_014_and_PLAN_002_scope`, `do_not_implement_floorplan_parsing_before_explicit_approval` |
| `docs/OPEN-DECISIONS.md` D-004/D-012/D-013/D-014 | all still `Decision: Moshe before PLAN-002 implementation` |
| `docs/decisions/` | ADR-0004 / ADR-0005 do not exist |

PLAN-002 §20 requires the approval to be recorded on the Kanban card **and converted into ADRs before implementation**. Producing this brief is safe (it is a document). **Codex must not begin implementation until** `PROJECT-STATE.yaml`, the plan header and ADR-0004/ADR-0005 record the approval. That is the single blocker; everything below is ready to execute the moment it clears.

---

## 1. Module boundaries

```
src/pwa/floorplan/
  __init__.py            # package marker; no logic
  config.py              # every named limit/tolerance + DXF_UNITS + limits_snapshot()
  types.py               # frozen dataclasses: Raw*/Norm*/SourceFrame/NormalizedGeometry
  findings.py            # Finding, code→(severity, tier) table, deterministic sort
  source.py              # FloorplanSource Protocol + select_source(path)
  dxf_source.py          # parent side: caps, subprocess spawn, timeout, kill, mapping
  dxf_worker.py          # `python -m pwa.floorplan.dxf_worker <in.dxf> <out.json>`
  annotation_source.py   # schema-validated annotation → RawGeometry
  normalize.py           # Decimal quantization, anchor, canonical order, stable IDs, projection
  validate.py            # geometry invariants → findings; opening↔wall resolution
  overlay.py             # deterministic SVG (raster + DXF variants)
  runs.py                # containment, verify, byte-copy, derived artifacts, staging, finalize
  builder.py             # orchestration: parse_run(...) → ParseOutcome
  cli.py                 # argparse + exit codes
tools/parse_floorplan.py         # thin shim, matches existing tools/ style
tools/make_floorplan_fixtures.py # Layer A generator (single metric source of truth)
```

**Dependency direction (enforce; no cycles):**
`config → types → findings → {source, normalize, validate, overlay} → runs → builder → cli`.
`normalize` must not import `validate`; `overlay` must not import `runs`; nothing under `floorplan/` imports `pwa.intake` or `pwa.packager`.

**Edits outside the package (§16 ownership, nothing else):**
- `src/pwa/contracts.py` — add `load_schema_catalog()`, version-aware `validator_for`/`validate_artifact`, registry from all catalog values, semver-aware latest for `load_all_schemas()`.
- `src/pwa/intake.py` — the bundle string only. Extract `CONTRACTS_BUNDLE_VERSION = "1.1.0"` as a module constant and reference it at `intake.py:218`. No other line changes.
- `src/pwa/files.py` — **read-only**. `copy_immutable`, `sha256_file`, `write_json_exclusive`, `is_link_or_reparse` are reused verbatim; do not modify them.

### 1.1 `contracts.py` changes — exact shape

```python
_SEMVER_RE = re.compile(r"-(\d+)\.(\d+)\.(\d+)\.schema\.json$")

def load_schema_catalog(schemas_dir=None) -> dict[tuple[str, str], dict]:
    """{(schema_id, schema_version): schema} for every file on disk.
    Rejects duplicate (id, version) and duplicate $id."""

def load_all_schemas(schemas_dir=None) -> dict[str, dict]:
    """Compatibility view: latest schema per schema_id, latest chosen by
    parsed (major, minor, patch) TUPLE — never by lexicographic filename."""

def build_registry(schemas=None) -> Registry:
    """Built from ALL catalog values so 1.0.0 $refs keep resolving."""

def validator_for(schema_id, schema_version=None, catalog=None) -> Draft202012Validator
def validate_artifact(doc, catalog=None) -> list
    # selects on (doc["schema_id"], doc["schema_version"]); unknown pair → KeyError
```

`schema_id` and `schema_version` are read from the file's `const` values, not from the filename — then cross-checked against the filename, and a mismatch is a hard error at load time.

---

## 2. Data shapes

### 2.1 In-memory (`types.py`, all `@dataclass(frozen=True)`, tuples not lists)

```python
class SourceFrame:            # how source coords become metres
    kind: Literal["dxf", "raster"]
    unit_scale_m: float       # metres per source coordinate unit (mm→0.001; px→scale_m_per_px)
    y_down: bool              # raster True, DXF False
    height_px: int | None     # raster only, needed for the flip
    source_units: str         # "mm"|"cm"|"m" (dxf) or "px" (raster)

class RawWall:    index:int; source_ref:str; start:tuple[float,float]; end:tuple[float,float]
class RawRoom:    index:int; source_ref:str; polygon:tuple[tuple[float,float],...]
class RawOpening: index:int; source_ref:str; kind:Literal["door","window"]
                  center:tuple[float,float]        # SOURCE units
                  width_m:float                    # ALREADY METRES in both adapters
                  span:tuple[tuple[float,float],tuple[float,float]] | None  # DXF only
                  wall_index:int | None            # annotation explicit ref; DXF None
class RawDimension: index:int; source_ref:str; a:tuple[float,float]; b:tuple[float,float]
                    declared_length_m:float
class RawGeometry: frame:SourceFrame; walls; rooms; openings; dimensions;
                   scanned_entities:int; unmapped:tuple[Finding,...]

class NormWall:    id:str; start; end; confidence:float; provenance:dict
class NormRoom:    id:str; polygon; confidence:float; provenance:dict
class NormOpening: id:str; type:str; wall_id:str; center; width_m:float;
                   confidence:float; provenance:dict
class NormalizedGeometry: units:Literal["m"]; walls; rooms; openings;
                          dimensions_m; normalization:dict; frame:SourceFrame
```

> **`width_m` asymmetry — read twice.** The DXF adapter computes `width_m = hypot(span) * unit_scale_m`. The annotation adapter reads `width_m` **verbatim** from the document — it is already metres and must **never** be multiplied by `scale_m_per_px`. This is the easiest silent AC-6 failure in the whole plan.

`source_ref` format (used in findings and provenance, and as the deterministic tiebreak in finding sort):
`dxf:modelspace/PWA-WALL#<handle>` and `annotation:walls[3]` / `annotation:openings[1]`.

### 2.2 `floorplan_annotation` 1.0.0 payload

```json
{
  "image": { "source_image_ref": "project/inputs/originals/floorplan.png",
             "sha256": "sha256:<64hex>", "width_px": 2000, "height_px": 1500 },
  "scale_m_per_px": 0.005,
  "walls":  [ { "start_px": [x, y], "end_px": [x, y] } ],
  "rooms":  [ { "polygon_px": [[x, y], ...] } ],
  "openings": [ { "type": "door", "wall_index": 0, "center_px": [x, y], "width_m": 0.9 } ],
  "declared_dimensions": [ { "a_px": [x, y], "b_px": [x, y], "length_m": 4.0 } ]
}
```

Rules baked into the schema: `additionalProperties: false` at every level; `source_image_ref` is a relative POSIX path with no `..`, no drive letter, no leading `/`; `wall_index` is `integer, minimum: 0`; `width_m`/`length_m`/`scale_m_per_px` are `exclusiveMinimum: 0`; `width_px`/`height_px` are `integer, minimum: 1`; `polygon_px` has `minItems: 3`.

> **`walls` and `rooms` must be `minItems: 0`.** The empty case is a *runtime* finding (`PARSE_EMPTY_GEOMETRY`, CLI 3). If the schema rejects it, the failure surfaces as a schema error on the operational path (CLI 2) and AC-20 fails.

### 2.3 `floorplan_parse` 1.1.0 — additive deltas only

Copy 1.0.0, bump `$id` and both `const`s, **rewrite every self-`$ref` to the 1.1.0 `$id`**, then add:

- `payload.normalization` (object, optional in schema, required at runtime):
```json
{ "quantum_m": 0.0001, "source_units": "mm", "source_unit_scale_m": 0.001,
  "translation_m": [tx, ty], "y_axis": "up" | "flipped_from_raster",
  "source_height_px": 1500, "scale_m_per_px": 0.005 }
```
- `payload.overlay` (optional in schema, required at runtime):
  `{ "path": "parse/overlay.svg", "sha256": "sha256:<64hex>" }`
- entity `provenance` (optional in schema, required at runtime), explicit per kind:
  - wall: `{source_kind, source_ref, source_start:[x,y], source_end:[x,y]}`
  - room: `{source_kind, source_ref, source_polygon:[[x,y],…]}`
  - opening: `{source_kind, source_ref, source_center:[x,y], source_span:[[x,y],[x,y]]?}`
  Each provenance object is `additionalProperties: false` with `source_kind: {enum:["dxf","annotation"]}`.

> The envelope is `additionalProperties: false` at the top level and `allOf` branches do not relax it. `normalization` and `overlay` therefore live **under `payload`**, never top-level.

### 2.4 `parse-report.json` — raw evidence, not an envelope artifact

```json
{ "report_version": 1, "parse_run_id": "...", "source_run_id": "...",
  "adapter": "dxf" | "annotation", "outcome": "complete|partial|failed", "cli_exit": 0,
  "terminal_finding": { "code": "...", "severity": "...", "source_ref": "..." } | null,
  "limits": { ...config.limits_snapshot()... },
  "metrics": { "walls": 0, "rooms": 0, "openings": 0, "source_entities_scanned": 0 },
  "findings": [ { "code", "severity", "tier", "source_ref", "message" } ],
  "overlay": { "path": "...", "sha256": "..." } | { "overlay_omitted_reason": "..." },
  "canonical_projection_sha256": "sha256:<64hex>" }
```
No timestamp, no duration, no absolute path, no stack trace. It is byte-deterministic and asserted as such.

---

## 3. Normalization — the exact algorithm

Do **all** of steps 1–5 in `Decimal`. Convert to `float` only at the emit boundary. Float subtraction after quantization reintroduces ~1e-17 dust and destabilizes stable IDs.

```
q(v)  = Decimal(str(v)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
emit(d) = 0.0 if d == 0 else float(d)          # kills -0.0
key(d)  = "0.0000" if d == 0 else f"{d:.4f}"   # ID/ordering text form
```

1. **To metres.** DXF: `X = x_u * unit_scale_m`, `Y = y_u * unit_scale_m`.
   Raster: `X = x_px * s`, `Y = (height_px - y_px) * s`.
   Reject NaN/inf/non-finite, non-2D, `|value| > MAX_COORDINATE_MAGNITUDE_M` → `PARSE_RESOURCE_LIMIT`; negative/zero widths → `PARSE_RESOURCE_LIMIT`.
2. **Quantize** every coordinate with `q`.
3. **Anchor.** `tx = min(x of every WALL endpoint)`, `ty = min(y of every WALL endpoint)`, computed **per axis independently, over walls only**. Rooms and openings do not move the anchor.
4. **Translate.** `v' = q(v - anchor)` (still Decimal; re-quantize defensively).
5. **Wall endpoints** are ordered so `start <= end` lexicographically by `(x, y)`.
6. **Room polygon**, in this order and no other:
   a. drop a trailing vertex equal to the first;
   b. reject consecutive duplicates and any repeated vertex → `PARSE_OPEN_POLYGON` / `PARSE_SELF_INTERSECTING_POLYGON` per §8;
   c. shoelace signed area; `< 0` → reverse to CCW; `== 0` → error;
   d. **then** rotate so the lexicographically smallest vertex is first; on ties pick the lexicographically smallest full rotated tuple.
   Reversing after rotating gives a different canonical form — order (c) before (d) is load-bearing.
7. **Stable IDs**, walls → rooms → openings (openings need `wall_id`):
```
wall_key    = "wall|"    + "|".join(key(sx), key(sy), key(ex), key(ey))
room_key    = "room|"    + "|".join(key(v) for each vertex coord in canonical order)
opening_key = "opening|" + "|".join(type, wall_id, key(cx), key(cy), key(width_m))
id = {"w","r","o"}[kind] + "-" + sha256(key.encode("utf-8")).hexdigest()[:12]
```
   A repeated key is `PARSE_DUPLICATE_ENTITY` (error). Never suffix, never merge.
8. **Canonical order** sorts by the full geometry tuple (not by the ID hash).

### 3.1 Canonical projection (AC-6)

```python
{ "units": "m",
  "rooms":    [[[x, y], ...] for each room in canonical order],
  "walls":    [[[sx, sy], [ex, ey]] for each wall],
  "openings": [[type, wall_id, [cx, cy], width_m] for each opening] }
```
Excludes `created_at`, confidence, provenance, source scale, overlay, normalization. Hash it with `compute_content_hash`-style canonical JSON into `evidence/PLAN-002/determinism/geometry-projection-hashes.json`.

### 3.2 Fixture numerics — the AC-6 landmine

`tools/make_floorplan_fixtures.py` must hold **one metric model** and derive DXF and PNG+annotation from it, with numbers chosen so both paths land on exact 1e-4 multiples with no rounding:

- DXF authored in **integer millimetres** → `x_mm * 0.001` is exact to 1e-3.
- Raster authored with **integer pixels** and `scale_m_per_px = 0.005` → `px * 0.005` is exact to 5e-3; pick `height_px` so `(height_px - y_px) * 0.005` reproduces the same metric y.
- Opening widths are authored in metres; the DXF span length must be the same value expressed in mm.

If the fixture is authored the other way round (metres first, pixels by division) AC-6 fails by exactly one quantum and the cause is very hard to see.

---

## 4. Geometry invariants (`validate.py`)

**Work in exact integers.** Every normalized coordinate is a multiple of 1e-4, so multiply by 10 000 into `int` for all orientation/intersection/containment predicates. Cross products are then exact and no epsilon is needed. Reserve float only for lengths, distances and tolerance comparisons.

| # | Invariant | Code (severity) |
|---|---|---|
| 1 | pre-normalization: ≥1 wall and ≥1 room, **before any `min()`** | `PARSE_EMPTY_GEOMETRY` (error) |
| 1b | post-normalization: ≥1 non-degenerate wall and ≥1 positive-area room | `PARSE_EMPTY_GEOMETRY` (error) |
| 2 | wall length `hypot < DEGENERATE_WALL_M` (0.05 m) | `PARSE_DEGENERATE_WALL` (error) |
| 3 | duplicate identity tuple, any kind | `PARSE_DUPLICATE_ENTITY` (error) |
| 4 | DXF `LWPOLYLINE.closed` must be true | `PARSE_OPEN_POLYGON` (error) |
| 5 | ≥3 unique vertices, positive area, CCW, no non-adjacent segment intersection | `PARSE_SELF_INTERSECTING_POLYGON` (error) |
| 6 | opening matches exactly one wall | 0 → `PARSE_UNKNOWN_WALL_REF`, >1 → `PARSE_AMBIGUOUS_WALL_REF` |
| 7 | perpendicular distance ≤ `OPENING_OFFSET_M` and projection `t ∈ [0, L]` | `PARSE_OPENING_OFF_WALL` |
| 8 | `t >= width_m/2 - QUANTUM_M` **and** `(L - t) >= width_m/2 - QUANTUM_M` | `PARSE_OPENING_WIDTH_EXCEEDS_WALL` |
| 9 | `abs(measured - declared) > max(0.02, abs(declared)*0.01)` | `PARSE_DIMENSION_INCONSISTENT` |
| 10 | annotation scale == manifest `payload.scale.m_per_px` (compare `Decimal(str(...))`, not floats) | `PARSE_SCALE_UNKNOWN` / `PARSE_UNITS_MISMATCH` per §6 |
| 11 | limits checked **before** any O(n²) loop | `PARSE_RESOURCE_LIMIT` |

**Opening↔wall resolution lives in exactly one function**, used by both adapters, operating on normalized metric geometry:

```python
def resolve_opening_wall(walls, center, declared_wall_id: str | None) -> tuple[str | None, list[Finding]]
```
DXF passes `declared_wall_id=None` (geometric match). Annotation passes the id resolved from `wall_index`. In both paths the geometric match is computed and must be unique; if the annotation's explicit reference disagrees with the unique geometric match → `PARSE_OPENING_OFF_WALL`. Duplicating this logic per adapter is how the two paths silently diverge.

Boundary semantics: `t == width_m/2` exactly **passes** (§8.7 says "at least"). `confidence == 0.5` **passes**; only `< 0.5` is low. Both need a dedicated fixture.

Room-overlap area is explicitly **not** an invariant in Part 1; obvious boundary intersections are `PARSE_ROOM_BOUNDARY_UNMATCHED` (warning) only.

**Finding order** is `(tier, code, source_ref)` with tiers: 0 containment/size/hash/schema, 1 units/unsupported source semantics, 2 normalization, 3 geometry invariants, 4 warnings. Put the tier in the `findings.py` table next to the severity so it cannot drift.

**Self-intersection cost.** Pairwise is O(n²); at `MAX_POLYGON_VERTICES = 10_000` that is 10⁸ pairs. Check the vertex cap first, and leave a `# ponytail: O(n²) segment test; Bentley–Ottmann if a real plan ever approaches the vertex cap` comment naming the ceiling. Layer A polygons are ~4–8 vertices.

---

## 5. DXF adapter and the subprocess boundary

**Parent (`dxf_source.py`):**
1. `stat().st_size > MAX_DXF_BYTES` → `PARSE_RESOURCE_LIMIT`, **before** spawning.
2. `subprocess.Popen([sys.executable, "-m", "pwa.floorplan.dxf_worker", src, out_json])` with
   `stdin=DEVNULL`, `stdout=<tempfile>`, `stderr=<tempfile>` — **never `PIPE`** (a chatty worker deadlocks the parent).
   Env is minimal and explicit: `PYTHONPATH` → `src` only, `PYTHONNOUSERSITE=1`, no inherited extras.
   POSIX: `start_new_session=True` + `os.killpg` on timeout. Windows: `CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW` + `proc.kill()`.
3. `proc.wait(timeout=PARSER_TIMEOUT_S)`; on `TimeoutExpired` kill, wait again, emit `PARSE_TIMEOUT`.
4. Read stdio tempfiles with a hard `MAX_WORKER_STDIO_BYTES` truncation; never surface raw tracebacks or absolute paths into artifacts.
5. Strictly validate the worker's JSON shape before touching it. Treat it as untrusted input even though we spawned it.

**Windows residual, state it in the ADR rather than hiding it:** stdlib has no job-object tree kill. The guarantee is `proc.kill()` **plus** the worker's enforced no-children invariant (the worker never spawns; assert it and test it). Say this plainly; do not claim tree termination on Windows.

**Worker (`dxf_worker.py`):** `recover.readfile` + reject `auditor.has_errors` (matches `intake._read_dxf` behaviour, and intake already guaranteed the file audits clean); then `len(msp) > MAX_DXF_ENTITIES` → `PARSE_RESOURCE_LIMIT` (post-load protection — say so, do not call it pre-parse protection). Iterate modelspace only. Never touch `doc.blocks` resolution, never resolve XREF/IMAGE/OLE. Emit plain JSON. No pickle, no eval.

**Mapping** (case-sensitive exact ASCII layer match):

| Layer | Entity | Meaning |
|---|---|---|
| `PWA-WALL` | `LINE` | wall centerline |
| `PWA-ROOM` | closed `LWPOLYLINE`, ≥3 unique vertices, every bulge exactly 0 | room polygon |
| `PWA-DOOR` | `LINE` | door span → midpoint = center, length = width |
| `PWA-WINDOW` | `LINE` | window span |

`$INSUNITS` must be 4/5/6 (mm/cm/m) **and** equal the verified manifest `payload.units`; otherwise `PARSE_UNITS_MISMATCH`. Intake's user-supplied units never override contradictory DXF metadata at parse time. Define `DXF_UNITS = {4:"mm",5:"cm",6:"m"}` in `floorplan/config.py`; do **not** import the private `pwa.intake._DXF_UNITS`.

Disposition is exactly PLAN-002 §6's table: unknown layer → `PARSE_UNMAPPED_SOURCE_ENTITY` (warn, recorded then ignored); wrong entity kind on a `PWA-*` layer, anything on `PWA-DIM`, `ARC`/`SPLINE`/`INSERT`/`IMAGE`/XREF/OLE, nonzero bulge, nonzero Z/elevation, any paperspace entity or any additional non-empty layout → `PARSE_UNSUPPORTED_FEATURE` (error), **after** finishing the bounded scan so the report is complete.

---

## 6. Overlay transforms

**Compute every coordinate in Python and emit literal numbers. Do not use SVG `transform` attributes for the flip** — renderer-independent, auditable, and it keeps determinism a property of one number formatter.

One formatter, used for every emitted number:
```python
def fmt(v: float) -> str:   # 3 decimals, trailing zeros stripped, "-0" → "0"
```

**Raster overlay:**
- `viewBox="0 0 W H"`, `width=W height=H` from dimensions **decoded fresh from the verified image bytes** (never from manifest `details`).
- `<image x="0" y="0" width="W" height="H" href="data:image/png;base64,…"/>` — `href` only, no `xlink`.
- Order of guards: raster bytes ≤ `MAX_SOURCE_RASTER_BYTES`, `W*H` ≤ `MAX_SOURCE_PIXELS`, **then** base64 (which inflates 4/3), then final SVG ≤ `MAX_OVERLAY_BYTES`.
- Detections mapped back with the exact recorded inverse:
  `x_px = (X_m - tx) / s`, `y_px = height_px - (Y_m - ty) / s`. SVG y is already down, so no further flip.

**DXF overlay:**
- bbox over accepted source primitives in source units, padded by a named constant (`OVERLAY_MARGIN_FRACTION = 0.05`).
- `svg_x = x_u - minX`, `svg_y = maxY - y_u`; `viewBox="0 0 (maxX-minX) (maxY-minY)"`.
- Normalized detections come back via `x_u = (X_m - tx) / k`, `y_u = (Y_m - ty) / k`, then into svg coords.

**Both:** groups `source`, `walls`, `rooms`, `doors`, `windows`, `ids`, `confidence`, `legend`, in that order, entities inside each group in canonical order. `<metadata>` carries canonical JSON with `source_sha256`, `parse_run_id`, `quantum_m` and the full `normalization` block. No timestamp. No script, no `foreignObject`, no external URL, no filesystem href. Escape every text node with `xml.sax.saxutils.escape` and every attribute with `quoteattr`. Prefer keeping source layer names **out** of the legend entirely; if any appear, they are hostile input and must be escaped (Layer A has a hostile-label fixture for this).
Written with `open("x", encoding="utf-8", newline="\n")`, one trailing LF, no trailing whitespace.

**Quantization is lossy — the inverse is exact only to `QUANTUM_M / s` pixels.** Do not assert `inverse(forward(p)) == p`; assert it is within that bound. It is still byte-deterministic, which is what AC-14 requires.

---

## 7. Derived-run lifecycle and failure semantics

### 7.1 Containment (AC-17)

```
root = Path(runs_root).resolve(strict=True)
```
Then walk the **unresolved** candidate path component by component from `root` downward, `lstat`-ing each with `pwa.files.is_link_or_reparse`, and reject on the first link/reparse point. `Path.resolve()` alone silently *follows* a symlink and would hide exactly the attack this check exists for. Reject `..`, absolute/drive-qualified inputs, and `cand == root`. Repeat the per-component check for every file before it is opened or copied.

### 7.2 Strict write order

Build everything in memory, validate everything, then write, then finalize:

1. preflight: containment; source `project_manifest.json` + `input_quality_report.json` load, schema-valid at their declared versions, `content_hash` recomputes;
2. source report is `complete` with `blockers == []` (precondition — see AMBIGUITY-2);
3. `prepare_staging` — reject if `runs/<id>` or `runs/.staging/<id>` exists;
4. byte-copy **every** entry of the source inventory with `copy_immutable` to the same run-relative path, plus the two source artifacts as `project/source-*.json`; each returned hash must equal the manifest's;
5. build + validate the derived `project_manifest` (bundle `1.1.0`, parse-run id, new artifact id, reverified inventory, envelope `inputs[]` → source manifest + source report artifact ids/hashes) and the derived `input_quality_report`;
6. adapter `extract` → `prevalidate_cardinality` → `normalize` → `validate`;
7. **render overlay, hash it** — this must precede step 8, because `payload.overlay.sha256` feeds `floorplan_parse`'s `content_hash`. The SVG must never contain the parse hash (cycle);
8. build + validate `floorplan_parse` 1.1.0, `assumptions` 1.0.0 (`payload.stage = "parsing"`), `parse-report.json`;
9. write all files with `write_json_exclusive` / exclusive `"x"` opens;
10. close every handle, then `os.replace(staging, final)`.

Any exception before step 10 → operational failure, staging retained, CLI 2.

### 7.3 Outcome matrix (locked, §11)

| Outcome | Finalized artifacts | Overlay | Status | CLI |
|---|---|---|---|---|
| no findings | derived manifest + derived report + parse + assumptions + parse-report | required | `complete` | 0 |
| warnings / low confidence only | same set | required | `partial` | 1 |
| any error finding, source reached the parser | same set, `floorplan_parse.status = failed` | required only if normalized geometry exists **and** render stays within `MAX_OVERLAY_BYTES`; otherwise `parse-report.overlay_omitted_reason` | `failed` | 3 |
| usage / containment / invalid source contract / staging IO / any unexpected exception before a valid diagnostic set | **none finalized**, bounded staging may remain | not required | — | 2 |

`PARSE_RESOURCE_LIMIT` / `PARSE_TIMEOUT` **after** a validated preflight are failed-domain (CLI 3) and finalize without overlay when rendering is impossible. Failure to serialize or validate the diagnostic set is operational (CLI 2). Every retry needs a new parse-run id; stale staging is reported and never auto-deleted or resumed.

**Envelope status/errors coupling:** the envelope requires a non-empty `errors[]` whenever `status` is `partial` or `failed`. Map findings into `errors[]` as `{code, message, path?}` with `code` matching `^[A-Z][A-Z0-9_]*$` (the `PARSE_*` vocabulary already does) and messages free of absolute paths and stack traces. A `partial` artifact with an empty `errors[]` is schema-rejected — that would flip a legitimate CLI 1 into CLI 2.

### 7.4 Windows specifics

- `os.replace` on a directory fails with `PermissionError` if **any** handle inside is still open. Close everything (including PIL images and the worker's tempfiles) before finalize.
- Directory `fsync` is not available on Windows. Match PLAN-001: file-level `fsync` (already inside `copy_immutable`) and no directory fsync. Do not add one and do not silently swallow its failure elsewhere.
- Same-volume rename only; `runs/.staging` and `runs/` are already siblings.

### 7.5 Two ambiguities to resolve before coding — do not decide silently

- **AMBIGUITY-1 — `PARSE_SOURCE_HASH_MISMATCH` exit code.** §12/AC-17 says hash mismatch "fails before parsing"; §11 lists it as an error finding (→ `failed`, CLI 3). Recommended split, subject to confirmation: a mismatch on a *copied inventory item* under a schema-valid source bundle is failed-domain (CLI 3, exact code, full diagnostic set); a mismatch or schema failure on the *source manifest/report itself* is operational (CLI 2) because no trustworthy derived manifest can be built.
- **AMBIGUITY-2 — source report not `complete` / non-empty blockers vs `PARSE_SCALE_UNKNOWN`.** Recommended: source report incomplete or with blockers → invalid source contract → CLI 2; a schema-valid, `complete` source whose manifest has `scale.known == false` or null `m_per_px` on a path that needs it → `PARSE_SCALE_UNKNOWN`, CLI 3.

Both readings satisfy the plan text; picking silently makes AC-20's decision-table test unfalsifiable.

---

## 8. Confidence, assumptions, G1

Deterministic, never estimated: accepted DXF primitive `1.0`; annotated primitive tied to a declared dimension `0.9`; annotated primitive from supplied scale only `0.6`. Part 1 has **no** parser default that alters geometry, so `assumptions.payload.entries` records only source/scale provenance with `requires_human_ack: false`; any future default must ship with `requires_human_ack: true`.

`any(entity.confidence < 0.5)` → `PARSE_LOW_CONFIDENCE` warning → `partial` → G1 blocked. Any unresolved `requires_human_ack: true` also blocks G1. Because `assumptions` 1.0.0 has no resolution field, acknowledgement is only ever expressed as corrected input plus a **fresh** derived run; never mutate an existing artifact.

---

## 9. TDD vertical-slice order

Follow PLAN-002 §15 exactly. Per slice: red test first, minimum code to green, then the next slice.

| # | Slice | First failing test |
|---|---|---|
| 1 | exact-version schemas + derived-run lifecycle (red) | `tests/unit/test_contract_versions.py` — 1.0.0 doc validates against 1.0.0, 1.1.0 against 1.1.0, a 1.1.0 doc mislabeled 1.0.0 is rejected, duplicate `(id, version)` or `$id` is rejected; `tests/integration/test_plan002_parse_run.py::test_staging_left_on_operational_failure` |
| 2 | catalog implementation | all of slice 1 green **and** the whole existing suite still green (AC-2) |
| 3 | fixtures + annotation validation | `tests/unit/test_floorplan_sources.py` annotation-schema cases; `test_schemas_roundtrip` inventory now 14 from the catalog |
| 4 | normalization + stable IDs | `tests/unit/test_floorplan_normalize.py` — quantization boundaries, `-0.0`, anchor-only-from-walls, reorder-stability, anchor-moving addition changes IDs (documented), duplicates fail |
| 5 | invariant validator | `tests/unit/test_floorplan_validate.py` — every error code + both warnings, plus `t == width/2` and `confidence == 0.5` boundaries |
| 6 | overlay | `tests/unit/test_floorplan_overlay.py` — byte-identical across runs, XML-valid, no script/external ref, hostile label escaped, inverse within `QUANTUM_M/s` |
| 7 | DXF + annotation adapters | `tests/golden/test_floorplan_golden.py::test_canonical_projection_matches_across_adapters` (**AC-6, the keystone**) |
| 8 | CLI + finalization + failure matrix | `tests/integration/test_plan002_failures.py` — exact `(code, severity, artifact status, CLI exit)` per row |
| 9 | full regression, cross-provider review, handoff | full pytest + `git diff --check` + evidence + `HANDOFF-PLAN-002-to-PLAN-003-001.md` |

Slice 2 is the AC-2 gate: if any pre-existing test goes red there, stop and fix the catalog rather than editing the historical test.

---

## 10. Highest-risk pitfalls, ranked

1. **`validate_artifact` must select from the catalog by `(schema_id, schema_version)`.** If it keeps using the latest-only view, every existing `floorplan_parse` 1.0.0 example fails the 1.1.0 `schema_version` `const` and AC-2 breaks on the first commit. `tests/conftest.py::make_envelope` hardcodes `"1.0.0"`, so this fires immediately in `test_schemas_roundtrip.py`.
2. **"Latest" must be a parsed semver tuple, not a filename sort.** `load_all_schemas` currently relies on `sorted(rglob(...))`; `1.10.0` sorts before `1.2.0`.
3. **Registry from all catalog values.** 1.0.0's `$ref`s are absolute to its own `$id`; and every self-`$ref` copied into 1.1.0 must be rewritten to the 1.1.0 `$id` or it silently resolves against the 1.0.0 document.
4. **Layer A fixture numerics** must be exactly representable at 1e-4 in both paths (§3.2), or AC-6 fails by one quantum with a near-invisible cause.
5. **`width_m` is already metres in the annotation path.** Never scale it.
6. **Do normalization in `Decimal` end to end.** Float subtraction after quantization reintroduces dust and destabilizes IDs.
7. **Normalize `-0.0` to `0.0` before formatting.** `f"{-0.0:.4f}"` is `"-0.0000"` → a different ID for the same point.
8. **Use exact integer predicates** (coordinates × 10 000) for orientation, intersection and containment. No epsilons in combinatorial geometry.
9. **Render and hash the overlay before computing `floorplan_parse.content_hash`**, and never put the parse hash inside the SVG.
10. **`floorplan_annotation` must allow empty `walls`/`rooms`** so `PARSE_EMPTY_GEOMETRY` reaches CLI 3 instead of being masked as a schema error on CLI 2.
11. **Containment must `lstat`-walk the unresolved path.** `resolve()` follows the symlink you are trying to detect.
12. **Subprocess stdio via tempfiles, never `PIPE`.** And be honest about the Windows tree-kill limitation.
13. **`os.replace` on a directory fails on Windows with any open handle.** Close PIL images and worker tempfiles first; no directory fsync on Windows.
14. **No timestamps or durations** in `parse-report.json` or the SVG — they destroy byte determinism (AC-14).
15. **CCW correction strictly before lexicographic rotation.**
16. **Walls get IDs before openings** (`wall_id` is inside the opening identity tuple).
17. **`normalization` and `overlay` live under `payload`** — the envelope is `additionalProperties: false` and `allOf` does not relax it.
18. **Update both inventories:** `test_schemas_roundtrip.py::test_all_13_artifact_schemas_present` (13 → catalog-derived 14, rename it) and the "Current schemas" paragraph in `schemas/README.md`.
19. **`partial`/`failed` require a non-empty `errors[]`** or the envelope rejects the artifact and a CLI 1 becomes a CLI 2.
20. **The anchor is min over wall endpoints only.** Test that a room extending past the walls does not move IDs, and that a *wall* extending the minimum bounds does (AC-8, documented and expected).

---

## 11. Verification (no execution performed in this session)

Once approval is recorded, from the worktree with the root interpreter and inherited `PYTHONPATH` cleared:

```
python -m pytest -q                                  # full suite, AC-21
python -m pytest tests/golden/test_floorplan_golden.py -q   # AC-6 keystone
python tools/parse_floorplan.py --runs-root runs --source-run runs/<intake-id> --parse-run-id <new-id> --annotation <path>
git diff --check                                     # AC-21
git diff -- pyproject.toml uv.lock                   # must be empty, AC-22
```

Success evidence lands under `evidence/PLAN-002/**` per §15. No `uv sync`, no install, no network, no GPU, no G7/G8.

---

## 12. Agent update fields

```
name: plan-002-implementation-brief-spatial-architect
role: Bounded post-approval spatial architect — implementation brief for the Codex implementer
plan_id: PLAN-002
provider: anthropic
requested_model: "claude-opus-5"
actual_model_id: "claude-opus-5"
normalized_effort: HIGH
provider_effort: high
fallback: "none"
model_reason: "spatial geometry, coordinate transforms, invariants, and overlay design"
reviewer_model: "OpenAI approved Codex"
cross_provider_review: "yes"
status: DONE (brief delivered; implementation NOT started and NOT authorized)
boundary_respected: "read-only — no edit/write to repo files, no tests run, no network, no install, no commit/merge/push; Part 1 local only; no H200/GPU/G7/G8"
blockers:
  - id: BLOCK-PLAN-002-APPROVAL
    summary: "PLAN-002 approval is not recorded in the repo: plan header says REVIEW, PROJECT-STATE human_gates.plan_002_approval says pending, D-004/D-012/D-013/D-014 remain open, ADR-0004/ADR-0005 do not exist. §20 requires Kanban approval + ADRs before implementation."
    owner: Moshe
    status: OPEN
  - id: AMBIGUITY-1
    summary: "PARSE_SOURCE_HASH_MISMATCH — CLI 2 vs CLI 3 split (brief §7.5)"
    owner: implementer + reviewer
    status: OPEN
  - id: AMBIGUITY-2
    summary: "Incomplete source quality report vs PARSE_SCALE_UNKNOWN routing (brief §7.5)"
    owner: implementer + reviewer
    status: OPEN
```
