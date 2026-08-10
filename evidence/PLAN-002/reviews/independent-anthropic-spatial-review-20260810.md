# PLAN-002 — Independent Anthropic spatial/geometry review (2026-08-10)

- Reviewer role: independent spatial/geometry reviewer under MODEL-ROUTING-v1.
- PROVIDER: anthropic · MODEL: Opus 5 · MODEL_ID_EXACT: `claude-opus-5` · EFFORT_NORMALIZED: HIGH ·
  EFFORT_PROVIDER_VALUE: session-inherited · THINKING: extended spatial/geometric reasoning.
- MODEL_REASON: coordinate transforms, normalization/identity rules, geometry invariants and
  source-aligned overlay correctness.
- FALLBACK_PROVIDER / FALLBACK_MODEL: none — block if unavailable (not exercised).
- CROSS_PROVIDER_REVIEWER: human Moshe approval.
- Working tree reviewed: `.worktrees/t_b7ade39e`, branch
  `panoworld-dev/t_b7ade39e-p1-02-floorplan-parsing`, uncommitted working-tree state.
- Mode: **read-only on source**. No implementation file was modified. Scratch probes were written to
  the session scratchpad only.

---

## 1. Skills loaded (mandatory, PLAN-002 §17)

| Skill | Loaded | Use in this review |
|---|---|---|
| `code-reviewer` | yes | severity discipline, structured finding format, production-risk framing |
| `python-patterns` | yes | Decimal/float boundary reasoning, typing and module-structure judgement |
| `threejs-geometry` | yes | geometry/winding/vertex-buffer background; only tangentially applicable (this is 2D floorplan geometry, not Three.js) |
| `debugging-strategies` | yes | hypothesis → controlled experiment → falsifiable evidence loop used for every finding below |

---

## 2. Verdict

**NEEDS_REWORK**

The core spatial mathematics is correct and, in several places, better than the plan requires: the
raster→metric transform matches §6 exactly, quantization goes through `Decimal(str(v))` before
identity hashing, the translation anchor is taken over wall endpoints only, CCW is decided by the
correct signed-area sign, the canonical rotation is a true idempotent total order, and stable IDs
survive input reordering while correctly changing when the anchor moves.

Rework is required because three things the acceptance file records as "evidenced" are not actually
enforced by the code: opening identity uniqueness (§7), opening/wall **collinearity** (§6), and the
non-adjacent segment-intersection invariant (§8.2). In addition the DXF overlay omits half of its
detections and derives its "source" layer from the detections themselves, which makes AC-14's
source-alignment claim structurally unfalsifiable for that adapter.

ESCALATE_WHEN triggers that fired: **identity-rule defect** (finding C-1) and **overlay
misalignment/omission** (finding M-4). No cross-adapter disagreement was found.

## 3. Counts

| Severity | Count |
|---|---|
| Critical | 1 |
| Major | 4 |
| Minor | 4 |
| Info | 4 |

---

## 4. Findings

### C-1 (CRITICAL) — Duplicate openings collide on `id` and produce a `complete`, G1-eligible artifact

`src/pwa/floorplan/validate.py:145-200` checks duplicate geometry for walls and rooms and for
nothing else:

```python
        key = (wall.start, wall.end)
        duplicate = key in seen_walls
        if duplicate:
            findings.append(make_finding("PARSE_DUPLICATE_ENTITY", "duplicate wall geometry", ...))
...
        duplicate = room.polygon in seen_rooms
        if duplicate:
            findings.append(make_finding("PARSE_DUPLICATE_ENTITY", "duplicate room geometry", ...))
```

The opening loop (`validate.py:181-188`) has no equivalent. `src/pwa/floorplan/normalize.py:86-90`
derives the opening id purely from content:

```python
def _opening_identity(kind, wall_id, center, width_m) -> str:
    encoded = (f"opening|{kind}|{wall_id or '__pending__'}|{key(center[0])}|{key(center[1])}|{key(width_m)}"...)
    return "o-" + hashlib.sha256(encoded).hexdigest()[:12]
```

so two coincident source openings necessarily produce the same id, with no finding.

**Concrete numeric failure scenario.** DXF with walls `(0,0)-(5,0)`, `(5,0)-(5,4)`,
`(0,4)-(5,4)`, `(0,0)-(0,4)`, one room `(0,0),(5,0),(5,4),(0,4)`, and **two identical**
`PWA-DOOR` lines `(2.05,0)-(2.95,0)` (a copy-paste duplicate, a routine CAD authoring artifact).
Measured output:

```
opening ids: ['o-0d59ba803823', 'o-0d59ba803823']
ids distinct: False
validate findings: NONE
```

Status is `complete`, CLI 0, G1-eligible. The emitted `floorplan_parse.json` contains two
`payload.openings[]` entries with the identical `id`; the 1.1.0 schema has no `uniqueItems`
constraint on ids (`schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json:180-186`), so it
validates. Any downstream 3D consumer that keys openings by `id` silently drops one of them.

This directly contradicts PLAN-002 §7 ("Collision/duplicate geometry fails; no suffix or merge") and
the AC-8 clause "duplicates fail". The failure matrix has `f-duplicate-wall` and `f-duplicate-room`
rows but no duplicate-opening row, which is why the gap was not caught.

**Suggested fix (described, not applied).** In `validate()`, add an opening pass keyed on the same
identity tuple used by `_opening_identity` — `(type, wall_id, center, width_m)` — emitting
`PARSE_DUPLICATE_ENTITY`. Separately, add a global assertion that every emitted `id` across walls,
rooms and openings is unique, failing with `PARSE_DUPLICATE_ENTITY` if not; that closes the hash
collision case as well as the duplicate-geometry case, which §7 names together.

---

### M-2 (MAJOR) — §6 collinearity is not implemented; opening→wall matching is a centre-point test

PLAN-002 §6 requires: *"Every opening line must be collinear with exactly one wall segment within
tolerance."* Neither matcher tests collinearity. `src/pwa/floorplan/normalize.py:96-118`:

```python
def _resolve_wall_id(walls, center) -> str:
    ...
        dx = cx - sx
        dy = cy - sy
        t = dx * ux + dy * uy
        distance = abs(dx * uy - dy * ux)
        if distance <= OPENING_OFFSET_M and -QUANTUM_M <= t <= length + QUANTUM_M:
            candidates.append((t, wall.id))
```

and `src/pwa/floorplan/validate.py:41-53` (`_distance_to_wall`) does the same. Both consume only
`opening.center`. The opening's span/direction is carried into provenance
(`normalize.py:234-238`, `"source_span"`) but is never used for matching or for width derivation.

**Concrete numeric failure scenario.** Wall `(0,0)-(5,0)`. `PWA-DOOR` line drawn **perpendicular**
to it: `(2.5,-0.45)-(2.5,0.45)`. The worker computes `center=(2.5,0.0)` and
`width_m = hypot(0, 0.9) = 0.9` (`dxf_worker.py:120-121`). Measured:

```
_resolve_wall_id                 -> w-aaa
validate.resolve_opening_wall    -> ('w-aaa', [])
full-pipeline validate findings  -> NONE
```

The opening is bound to the wall at confidence 1.0, status `complete`, CLI 0. A 45° door line
`(2.18,-0.32)-(2.82,0.32)` behaves identically and reports `width_m = 0.9` where the true
wall-aligned span is `0.636 m` — a 41 % width error handed to the 3D stage, with no finding.

**Suggested fix.** Reject openings whose span is absent, then require the unit direction of the span
to be parallel to the candidate wall within a documented angular/`OPENING_OFFSET_M`-derived
tolerance (e.g. `|span_dir × wall_dir| * span_length <= OPENING_OFFSET_M`), and require **both** span
endpoints — not just the centre — to be within `OPENING_OFFSET_M` of the wall line. Emit
`PARSE_UNKNOWN_WALL_REF` on zero matches and `PARSE_AMBIGUOUS_WALL_REF` on multiple, per §6.
Derive `width_m` from the span projected onto the wall direction, not from the raw span length.
Add a failure-matrix row (`f-opening-not-collinear`).

---

### M-3 (MAJOR) — Self-intersection test detects only *proper* crossings; collinear overlap and one-sided vertex-on-edge touches pass

`src/pwa/floorplan/validate.py:28-38`:

```python
def seg_proper_cross(p1, p2, q1, q2) -> bool:
    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)
```

Zero is folded into the "not greater than zero" branch, so a touching configuration is detected only
when the touching endpoint approaches from the **left** of the other edge, and a collinear overlap
(all four orientations zero) is never detected. Measured on the primitive (integer 1e-4 units):

```
collinear overlap [(0,0)-(6,0)] vs [(1,0)-(4,0)] : False
T-touch approach from LEFT  (q1 above)           : True
T-touch approach from RIGHT (q1 below)           : False
```

PLAN-002 §8.2 requires "no non-adjacent segment intersection", not "no proper crossing".

**Concrete numeric failure scenario.** Room polygon (metres)

```
(0,0) (6,0) (6,2) (3,2) (3,5) (4.5,5) (4.5,2) (0,2)
```

Edge `e2 = (6,2)→(3,2)` and edge `e6 = (4.5,2)→(0,2)` are non-adjacent and **collinearly overlap**
on `x ∈ [3, 4.5]` at `y = 2`; the endpoint `(4.5,2)` of `e5` also lies strictly inside `e2`. The
polygon is therefore not simple. Measured through `_canonical_polygon` + `_validate_room`:

```
T-touch from LEFT of edge  -> findings=NONE
```

Controls behaved correctly: a clean square → `NONE`, a classic bowtie → `PARSE_SELF_INTERSECTING_POLYGON`.
So a non-simple room is emitted with positive area, CCW winding, unique vertices and zero findings —
AC-9's "no self-intersection" clause does not hold.

**Suggested fix.** Replace `seg_proper_cross` with a full segment-intersection predicate: keep the
proper-crossing branch, and add the standard degenerate branches — `o_i == 0` combined with an
on-segment bounding-box containment test for each of the four endpoints, plus a collinear-overlap
test (all four orientations zero **and** the 1-D projections onto the shared axis overlap in more
than a point). All arithmetic is already exact integers via `_to_int`, so no tolerance is needed.
Adjacent edges must still be allowed to share exactly their common endpoint. Add failure-matrix rows
for collinear overlap and for a right-side vertex touch.

---

### M-4 (MAJOR) — DXF overlay omits rooms and doors, and its "source" layer is regenerated from the detections

`src/pwa/floorplan/overlay.py:150-151`:

```python
    lines.append('<g id="rooms"></g>')
    lines.append('<g id="doors"></g>')
```

Only windows are drawn (`overlay.py:152-160`). `src/pwa/floorplan/builder.py:259-271` builds the DXF
`source` layer as:

```python
        "primitives": [
            {"type": "line",
             "start": wall.provenance["source_start"],
             "end": wall.provenance["source_end"]}
            for wall in geometry.walls
        ],
```

i.e. the "source" polylines are re-projected from the **normalized walls' own provenance**, not from
an independent read of the accepted DXF entities. Source room LWPOLYLINEs and source door/window
LINEs never reach the overlay at all.

**Concrete failure scenario (measured on the tracked golden evidence).** For
`evidence/PLAN-002/overlays/layer-a-1-dxf.svg`, built from a fixture with 5 walls, 2 rooms, 2 doors
and 2 windows:

```
g=source     present=True  empty=False   (5 polylines — walls only)
g=walls      present=True  empty=False   (the same 5 polylines, exactly coincident)
g=rooms      present=True  empty=True    <-- 2 rooms missing
g=doors      present=True  empty=True    <-- 2 doors missing
g=windows    present=True  empty=False
```

4 of 11 detections are absent. Because `walls` is drawn from `_inverse_dxf(normalized)` and `source`
is drawn from the provenance those same normalized walls carry, the two groups are coincident by
construction: **no normalization error can ever make them disagree**, so the DXF overlay cannot
serve as the falsifiable G1 alignment evidence AC-14 claims. The DXF viewBox is also derived from
wall primitives only (`overlay.py:117-125`), so a room polygon outside the wall bounding box would be
clipped.

**Suggested fix.** Render room polygons and door markers in `_dxf_svg` (mirroring `_raster_svg`).
Populate `_source_binding` `primitives` from the raw adapter output (`raw.rooms`, `raw.openings`,
`raw.walls` source coordinates) rather than from `geometry.*.provenance`, so the source layer is an
independent projection of the accepted DXF entities. Compute the viewBox over all source primitives.

---

### M-5 (MAJOR) — Raster overlay hardcodes `data:image/png` for JPEG sources

`src/pwa/floorplan/overlay.py:72`:

```python
        f'<g id="source"><image x="0" y="0" width="{width}" height="{height}" href="data:image/png;base64,{image_b64}"/></g>',
```

`src/pwa/intake.py:17` accepts JPEG floorplans: `FLOORPLAN_SUFFIXES = {".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg"}`,
and `src/pwa/intake.py:171,193` treats `.jpg`/`.jpeg` as first-class raster floorplans with a
`m_per_px` scale, i.e. exactly the annotation-adapter path.

**Concrete failure scenario (measured).** A 40×30 JPEG floorplan with a valid annotation renders:

```
source bytes are JPEG (magic b'\xff\xd8\xff'), declared as: data:image/png;base64,/9j/4AAQSkZJRgABAQ...
declares image/png: True
```

Browsers usually sniff and recover, but strict SVG rasterizers (librsvg, resvg, Inkscape CLI,
CairoSVG) and most print/PDF pipelines honour the declared MIME type and drop the image — producing
an overlay whose entire `source` layer is blank while the file still hashes deterministically and
passes every current test. That defeats the whole point of AC-14 evidence for the JPEG case.

**Suggested fix.** Derive the MIME type from the verified image bytes (PIL already opens the file in
`_source_binding`, so `Image.format` is available) and pass it through `source_binding`; restrict it
to an allowlist of `image/png` / `image/jpeg` and fail with `PARSE_SOURCE_UNSUPPORTED` otherwise.

---

### m-6 (MINOR) — `PARSE_OPENING_OFF_WALL` returned when the declared wall is a legitimate candidate

`src/pwa/floorplan/validate.py:78-79`:

```python
        if candidates and declared_wall.id != candidates[0].id:
            return None, [make_finding("PARSE_OPENING_OFF_WALL", "opening binds a different wall")]
```

`candidates[0]` is simply the first wall in `geometry.walls` order that satisfies the proximity test;
it is not "the best" candidate.

**Concrete numeric failure scenario.** Wall A `(0,0.015)-(5,0.015)` (ordered first), wall B
`(0,0)-(5,0)`. Opening centre `(2.5, 0.0)`, width 0.9, annotation declares wall B. Distance to B is
exactly 0; distance to A is 0.015 < `OPENING_OFFSET_M` = 0.02, so both are candidates. Measured:

```
resolve_opening_wall(declared=B)    -> PARSE_OPENING_OFF_WALL "opening binds a different wall"
resolve_opening_wall(declared=None) -> PARSE_AMBIGUOUS_WALL_REF
```

The declared, perfectly-on-wall reference is rejected with an "off wall" code. Per §6/§11 the correct
outcome is either acceptance of the explicit declaration or `PARSE_AMBIGUOUS_WALL_REF`.

**Suggested fix.** When a declaration exists and the declared wall passes the distance and
half-width tests, accept it; only if *another* wall is strictly closer (or the declared wall fails)
report a code — and use `PARSE_AMBIGUOUS_WALL_REF` for the genuine tie.

---

### m-7 (MINOR) — `_resolve_wall_id` reports `PARSE_UNKNOWN_WALL_REF` for the multi-match case

`src/pwa/floorplan/normalize.py:116-117`:

```python
    if len(candidates) != 1:
        raise FloorplanError("PARSE_UNKNOWN_WALL_REF", "opening must resolve exactly one wall")
```

§6/§11 require `PARSE_AMBIGUOUS_WALL_REF` when more than one wall matches. Measured with the two
walls from m-6: `raised: FloorplanError PARSE_UNKNOWN_WALL_REF`.

Impact is currently contained: `normalize.py:213-219` catches both codes and defers to
`_PENDING_DXF_WALL_ID`, and `validate.resolve_opening_wall` re-resolves with the correct codes, so
the user-visible finding is right. It is still a latent wrong-code path and a trap for any future
caller of `_resolve_wall_id`.

**Suggested fix.** Split the branches: `PARSE_UNKNOWN_WALL_REF` for `len == 0`,
`PARSE_AMBIGUOUS_WALL_REF` for `len > 1`.

---

### m-8 (MINOR) — `MAX_COORDINATE_MAGNITUDE_M` is enforced before translation only

`src/pwa/floorplan/normalize.py:48-49` checks the bound on the pre-translation metric value;
`_normalize_point` (`normalize.py:53-54`) subtracts the anchor afterwards and never re-checks.

**Concrete numeric failure scenario.** Walls spanning `x ∈ [-99000, +99000]` m (each endpoint within
the 100 000 m cap, so accepted). Measured:

```
MAX normalized coordinate emitted: 198000.0   exceeds MAX_COORDINATE_MAGNITUDE_M: True
translation: [-99000.0, -99000.0]
```

The artifact carries coordinates at ~2× the documented bound with no `PARSE_RESOURCE_LIMIT`.

**Suggested fix.** Re-apply the magnitude check to the translated values (or to the bounding-box
extent) before ID computation.

---

### m-9 (MINOR) — `ids` and `confidence` overlay layers are always empty; `legend` is empty on the happy path

`src/pwa/floorplan/overlay.py:105-107` and `161-163` emit `<g id="ids"></g>` and
`<g id="confidence"></g>` unconditionally, for both adapters. `_legend_lines` (`overlay.py:49-57`)
populates the legend only from `raw.unmapped` source refs, so a clean parse yields
`<g id="legend"></g>`.

Measured on both tracked golden overlays: `ids` empty, `confidence` empty, `legend` empty.

§10 requires "layers **distinguish** source, walls, rooms, doors, windows, IDs, confidence and
legend". Empty placeholder groups satisfy the letter of "a layer exists" but carry no ID or
confidence information, which is precisely what a human G1 reviewer needs in order to tell a 0.6
annotated wall from a 1.0 DXF wall on the picture.

**Suggested fix.** Render entity ids as escaped `<text>` at a deterministic anchor, and encode
confidence as a deterministic per-entity attribute or a small legend swatch; make the legend
unconditional (adapter, units, scale, confidence key).

---

### i-10 (INFO) — AC-6 is structurally blind to the value of `height_px`

The transform matches §6 exactly (`normalize.py:45`), and I verified it point-by-point:

```
y_px=   0 -> 9.0000   y_px=   1 -> 8.9950   y_px= 200 -> 8.0000
y_px=1400 -> 2.0000   y_px=1799 -> 0.0050   y_px=1800 -> 0.0000
```

But because §7 then translates so the minimum **wall endpoint** is `(0,0)`, any constant offset in
the flip cancels. Measured on the real Layer A geometry:

```
height_px=1800 -> proj hash e5041ddcf05eb02d  translation=[1.0, 2.0]
height_px=1799 -> proj hash e5041ddcf05eb02d  translation=[1.0, 1.995]
height_px=1801 -> proj hash e5041ddcf05eb02d  translation=[1.0, 2.005]
height_px=5000 -> proj hash e5041ddcf05eb02d  translation=[1.0, 18.0]
height_px=   0 -> proj hash e5041ddcf05eb02d  translation=[1.0, -7.0]
```

The overlay is likewise blind, because `_inverse_raster` uses the same recorded `source_height_px`,
so forward and inverse stay mutually consistent for any value. **This is not a defect** — the code
matches the spec formula, and the invariance is arguably desirable — but the brief asked me to hunt
for a `height` vs `height-1` off-by-one, and the honest answer is that no current test could detect
one. The **sign** of the flip *is* discriminated: normalizing the real Layer A raster geometry with
`y_down=False` yields projection hash `6caa9d0a1cc74da2` ≠ `e5041ddcf05eb02d`, with doors and windows
swapping y (`door (2.5, 0.0)` → `(2.5, 6.0)`).

Suggested (evidence, not code): assert `normalization.source_height_px` equals the freshly decoded
image height in a dedicated test — that is the only place the constant is observable.

### i-11 (INFO) — The Layer A raster fixture has no source features to align with

`tools/make_floorplan_fixtures.py:18`:

```python
    Image.new("RGB", (2000, 1800), "white").save(image_path, format="PNG")
```

The embedded "source" raster is a **blank white image**. The overlay's detections land on exactly the
annotated pixel coordinates (`200,1400`, `1200,800`, …) — I verified the normalize→overlay round-trip
is bit-exact, max error `0.0` over all wall endpoints — but there is nothing drawn in the PNG for
them to align **with**. The direct answer to "does the drawn geometry land on the source features?"
is: there are no source features; the overlay merely renders. The retained human visual G1 gate is
therefore doing no real alignment work on this fixture.

Suggested (evidence, not code): render the fixture PNG with the actual wall/room/opening strokes at
the annotated pixel coordinates, so a transform regression becomes visible.

### i-12 (INFO) — The Layer A fixture never exercises quantization or oblique geometry

Every fixture coordinate is axis-aligned and an exact multiple of 0.05 m
(`tools/make_floorplan_fixtures.py:23-76`): DXF mm values `1000/2000/…/9000`, annotation px values
`200/600/700/1200/1800` at `0.005 m/px`. Both adapters therefore reach identical exact Decimals with
zero rounding, so the ROUND_HALF_EVEN path, the `-0.0 → 0.0` rule, and all non-axis-aligned
projection/collinearity maths are untouched by the cross-adapter test. They are covered only by the
separate unit rows `b-quantize-half-even`, `b-negative-zero`, `b-span-quantum`.

I confirmed the quantization contract itself is correct and adapter-agnostic:

```
Decimal(str(2.00005)) = 2.00005          -> quantize HALF_EVEN -> 2.0000   (banker's, correct)
Decimal(2.00005)      = 2.0000499999...  -> quantize HALF_EVEN -> 2.0000
raster: Decimal("400.01")  * Decimal("0.005") = 2.00005 -> 2.0000
dxf   : Decimal("2000.05") * Decimal("0.001") = 2.00005 -> 2.0000
q(-0.00005) = -0.0000  key="0.0000"  emit=0.0
```

Because both adapters go through the same exact `Decimal` arithmetic in `_to_metric`, two adapters
can diverge at a .00005 boundary only if their **exact products differ** — a fixture property, not an
implementation defect. I could not construct an implementation-level divergence.

### i-13 (INFO) — Opening confidence inherits the wall's confidence, which §9 does not define

`src/pwa/floorplan/normalize.py:265-277` sets each opening's confidence to
`wall_confidence.get(opening.wall_id, 0.6)`. §9 defines 0.9/0.6 only for "primitives tied to a
declared dimension" vs "derived only from supplied scale"; an opening whose `width_m` is *declared
directly in the annotation* arguably has its own tie. The chosen inheritance rule is defensible and
deterministic, but it is an unstated extension of the approved contract and should be written into
§9 rather than left implicit in code.

---

## 5. AC-by-AC verdict (ACs in scope)

| AC | Verdict | Reason |
|---|---|---|
| **AC-6** — both adapters emit the same canonical projection for Layer A | **VERIFIED** | Independently reproduced. I hand-entered the two fixture coordinate tables (mm/y-up and px/y-down) into `normalize()` and got `sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e` from **both** — matching the implementer's claim exactly. `canonical_projection` (`normalize.py:298-307`) genuinely returns only `units`, room polygons, wall endpoints and `[type, wall_id, center, width]`; confidence, provenance, `scale_m_per_px`, `source_units`, `y_axis` and timestamps are all excluded, and `wall_id` is itself a pure function of wall geometry. Scope caveats in §6 below and in i-10/i-12. |
| **AC-7** — adapter-specific confidence/provenance/scale correct and intentionally different | **VERIFIED** | DXF → 1.0 throughout; annotation → 0.9 for dimension-tied walls/rooms and 0.6 otherwise; `source_units` `mm` vs `px`; `y_axis` `up` vs `flipped_from_raster`; `scale_m_per_px` `None` vs `0.005`. Provenance carries `source_kind`/`source_ref`/original endpoints, polygon and span per §9. Covered by `tests/golden/test_floorplan_golden.py::test_adapter_specific_fields`. Caveat i-13. |
| **AC-8** — stable IDs across reruns/reordering; anchor rules; **duplicates fail** | **NOT_MET** | The stability half is solid and I verified it: IDs were byte-identical across 20 random reorderings of walls/rooms/openings; an addition inside the bounds preserved every wall and room ID; an addition below the minimum moved the anchor from `[1.0, 2.0]` to `[0.0, 0.0]` and changed all IDs, as §7 documents. The identity tuple serialization is unambiguous (fixed 4-decimal `key()` tokens, `\|`-separated, distinct `wall\|`/`room\|`/`opening\|` prefixes, so no two different geometries can share a byte string). But the explicit "duplicates fail" clause does **not** hold for openings — see C-1. |
| **AC-9** — every room passes uniqueness, area, winding, self-intersection | **NOT_MET** | Uniqueness (`validate.py:99-101`), positive area via exact integer shoelace (`validate.py:102-108`) and CCW (`_canonical_polygon`, correct `area < 0 → reverse` sign; verified idempotent and rotation-invariant) are all correct. The self-intersection rule is not: a demonstrably non-simple polygon with a collinear non-adjacent overlap passes with zero findings — see M-3. |
| **AC-10** — opening references exactly one wall, lies on it, fits by half-width at both ends | **WEAK_EVIDENCE** | The half-width test is correct and genuinely checks **both** ends (`validate.py:76,87`: `t < w/2 - Q or (length - t) < w/2 - Q`); measured: centered→OK, overhang-start→`PARSE_OPENING_WIDTH_EXCEEDS_WALL`, overhang-end→`PARSE_OPENING_WIDTH_EXCEEDS_WALL`, exactly-wall-length→OK (boundary accepted, per §8.7). "Exactly one wall" and "lies on it" are enforced only as centre-point proximity; the §6 collinearity clause is not met (M-2) and the declared-reference code path is wrong in a legitimate case (m-6). |
| **AC-11** — declared dimensions and source scale pass tolerance or fail with the exact code | **VERIFIED** | `validate.py:190-195` implements `max(0.02, abs(declared) * 0.01)` exactly as §8 specifies, in `Decimal`, emitting `PARSE_DIMENSION_INCONSISTENT`. Scale equality is a `Decimal(str(...))` comparison against the source manifest (`builder.py:482-486`) with `PARSE_SCALE_UNKNOWN` + CLI 3 + finalized failed diagnostic set. Failure matrix rows `f-dimension-bad`, `f-scale-unknown`, `f-scale-contradictory`, `b-dimension-exact` are present. |
| **AC-14** — source-aligned overlay shows source and detections, deterministic, XML-valid, no active/external content | **NOT_MET** | The safety and determinism half is verified: both tracked overlays parse as valid XML, are LF-only, contain no `<script>`, `foreignObject`, `xlink:href`, `<!ENTITY>`, `onload`, or any `http(s)://`/`file:` reference other than the SVG namespace, carry no timestamp, use a source-pixel `viewBox="0 0 2000 1800"` for raster and source-coordinate bounds `0 0 8800 6800` for DXF, bind the source by SHA-256 in `<metadata>`, and escape labels via `xml.sax.saxutils.escape`. The "shows source and detections" half fails: the DXF overlay omits 2 rooms and 2 doors and its source layer is derived from the detections (M-4), and the raster overlay embeds a blank image (i-11) with a hardcoded PNG MIME type that is wrong for JPEG inputs (M-5). |
| **AC-16** — warning/partial/unresolved acknowledgement cannot pass G1 | **VERIFIED (with a caveat)** | The confidence comparison is strictly `<` at all three sites (`validate.py:160,174,187`) against `LOW_CONFIDENCE_THRESHOLD = 0.5` (`config.py:8`), so exactly 0.5 is accepted, per §8. `builder.py:556-559` maps any warning → `partial` → CLI 1 and any error → `failed` → CLI 3, leaving only a finding-free run as `complete`/CLI 0/G1-eligible. Caveat: C-1 lets a genuinely invalid input reach that G1-eligible state, so the gate is sound but its input predicate is not. |

---

## 6. How strong is the cross-adapter equality claim?

**Stronger than the usual failure mode, but narrower than the acceptance file implies.**

The first thing I checked was the brief's suspicion — that `tools/make_floorplan_fixtures.py` derives
the DXF and the annotation from one shared geometry table by shared code, which would reduce AC-6 to
a tautology. **It does not.** The two fixtures are two independently written literal coordinate
tables in two different coordinate systems: the DXF is authored in millimetres, y-up
(`make_floorplan_fixtures.py:23-33`, values `1000…9000` × `2000…8000`), and the annotation is
authored in pixels, y-down, at `0.005 m/px` (`:56-76`, values `200…1800` × `200…1400`). There is no
shared constant, no shared loop and no conversion helper between them; a human transcribed the same
intended plan twice. The equality therefore does real work: it exercises the mm→m scale, the px→m
scale, the y-down→y-up flip, the wall-endpoint translation anchor, endpoint lexicographic ordering,
polygon canonicalisation and the wall-id hash, and it would fail on a scale mix-up, an endpoint
ordering bug, a polygon-rotation bug, or a **sign** error in the flip (I confirmed the last one
empirically: dropping the flip changes the hash to `6caa9d0a1cc74da2`). I also reproduced
`e5041ddc…` independently from my own transcription of both tables, so the number is real and not an
artifact of a shared helper.

What it does **not** prove is nearly as important. The fixture is a single pair of axis-aligned
rectangles whose every coordinate is an exact multiple of 0.05 m, so both adapters reach identical
exact `Decimal`s with zero rounding: the ROUND_HALF_EVEN boundary, the `-0.0 → 0.0` rule, and all
oblique-geometry maths are untouched by AC-6 (i-12). The translation anchor mathematically cancels
any constant y offset, so the `height_px` value — the single most dangerous constant in the raster
transform — is provably invisible to the projection hash for *any* value I tried, including 0 and
5000 (i-10). Openings are compared only as `[type, wall_id, center, width]`, and both adapters obtain
`width` from a declared metre value or a straight span length, so the collinearity defect (M-2) is
invisible to it. And AC-6 says nothing about *correctness* — it says the two adapters agree; both
could be wrong in the same way, since they share `normalize()` end to end and differ only in
`SourceFrame`. Layer A remains, as §13 already concedes, one synthetic plan and not accuracy
evidence. My honest summary: AC-6 as literally written is met and independently reproduced, but it
should be cited as "the two adapter front-ends feed the shared normalizer consistently on one
axis-aligned synthetic plan", not as "cross-path geometry equality is proven".

---

## 7. Empirical checks run

All probes ran read-only against the worktree using the root venv
(`.venv\Scripts\python.exe`, `PYTHONPATH` pointed at `.worktrees/t_b7ade39e/src`); scratch scripts
live in the session scratchpad and touch nothing in the repository.

**Probe 1 — forward transform vs §6, and forward∘inverse identity**

```
y_px=    0  metric_y=9.0000  spec=9.000  match=True
y_px=    1  metric_y=8.9950  spec=8.995  match=True
y_px=  200  metric_y=8.0000  spec=8.000  match=True
y_px= 1400  metric_y=2.0000  spec=2.000  match=True
y_px= 1799  metric_y=0.0050  spec=0.005  match=True
y_px= 1800  metric_y=0.0000  spec=0.000  match=True

normalization: {'quantum_m': 0.0001, 'source_units': 'px', 'source_unit_scale_m': 0.005,
 'translation_m': [1.0, 2.0], 'y_axis': 'flipped_from_raster', 'source_height_px': 1800,
 'scale_m_per_px': 0.005}
max round-trip error over wall endpoints (norm -> px -> norm): 0.0
inverse px positions: (200,1400)-(200,200) (200,1400)-(1800,1400) (200,200)-(1800,200)
                      (1200,1400)-(1200,200) (1800,1400)-(1800,200)
```

**Probe 1 (cont.) — cross-adapter hash, quantization, canonical polygon**

```
projections equal: True
raster hash: sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e
dxf    hash: sha256:e5041ddcf05eb02da0a07176d483ee4eaef311bf885204078710f07fe3b7e77e

q(2.00005)=2.0000  q(2.00015)=2.0002  q(2.00025)=2.0002  q(-2.00005)=-2.0000
q(-5e-05)=-0.0000 key=0.0000 emit=0.0     q(5e-05)=0.0000 key=0.0000 emit=0.0
Decimal(str(2.00005)) = 2.00005              -> 2.0000
Decimal(2.00005)      = 2.0000499999999998...-> 2.0000
raster 400.01*0.005 = 2.00005 -> 2.0000 ; dxf 2000.05*0.001 = 2.00005 -> 2.0000

ccw canonical == cw canonical: True   area: 16   idempotent: True
all 4 rotations map to the same canonical form: True
```

**Probe 2 — adversarial invariants**

```
clean square (control)                 -> NONE
classic bowtie (control)               -> PARSE_SELF_INTERSECTING_POLYGON
collinear-overlap polygon (M-3)        -> NONE                      <-- defect
seg_proper_cross collinear overlap     -> False                     <-- defect
seg_proper_cross T-touch from LEFT     -> True
seg_proper_cross T-touch from RIGHT    -> False                     <-- defect

perpendicular DXF door, wall (0,0)-(5,0), span (2.5,-0.45)-(2.5,0.45):
  _resolve_wall_id            -> w-aaa
  resolve_opening_wall        -> ('w-aaa', [])
  full pipeline validate      -> NONE                               <-- defect (M-2)

duplicate openings:
  opening ids  -> ['o-0d59ba803823', 'o-0d59ba803823']
  ids distinct -> False
  findings     -> NONE                                              <-- defect (C-1)

declared wall B (dist 0) vs first candidate A (dist 0.015):
  declared=B    -> PARSE_OPENING_OFF_WALL "opening binds a different wall"   <-- m-6
  declared=None -> PARSE_AMBIGUOUS_WALL_REF
_resolve_wall_id multi-match -> PARSE_UNKNOWN_WALL_REF (spec: AMBIGUOUS)     <-- m-7

half-width fit: centered OK | overhang START PARSE_OPENING_WIDTH_EXCEEDS_WALL
                | overhang END PARSE_OPENING_WIDTH_EXCEEDS_WALL | exactly wall length OK
```

**Probe 3 — y-flip discrimination and `height_px` sensitivity** (output quoted in i-10 above).

**Probe 4 — AC-8 and overlay safety**

```
IDs identical under 20 random input reorderings: True
anchor-preserving addition: wall IDs preserved True, room IDs preserved True
anchor-moving addition:     any pre-existing wall ID preserved False, translation [1.0,2.0] -> [0.0,0.0]
duplicate WALL geometry:    ids ['w-b38b...','w-8829...','w-8829...',...]
                            findings ['PARSE_AMBIGUOUS_WALL_REF','PARSE_DUPLICATE_ENTITY']

layer-a-1-raster.svg: XML-valid=True bytes=21122 LF-only=True suspicious=[]
  source F/walls F/rooms F/doors F/windows F | ids EMPTY, confidence EMPTY, legend EMPTY
layer-a-1-dxf.svg:    XML-valid=True bytes=1385  LF-only=True suspicious=[]
  source F/walls F/windows F | rooms EMPTY, doors EMPTY, ids EMPTY, confidence EMPTY, legend EMPTY
```

**Probe 5 — coordinate bound and MIME**

```
source magnitudes 99000 (<=100000, accepted)
MAX normalized coordinate emitted: 198000.0  exceeds MAX_COORDINATE_MAGNITUDE_M: True
translation: [-99000.0, -99000.0]

JPEG source bytes b'\xff\xd8\xff' declared as: data:image/png;base64,/9j/4AAQSkZJRgABAQ...
declares image/png: True
```

I did not re-run the full pytest suite (the orchestrator's 261-passed/exit-0 result is accepted and I
found no reason to challenge it); every finding above is reproducible from the probe outputs quoted.

---

## 8. Files reviewed

- `src/pwa/floorplan/normalize.py`, `validate.py`, `overlay.py`, `dxf_source.py`, `dxf_worker.py`,
  `annotation_source.py`, `config.py`, `types.py`, `builder.py` (targeted sections)
- `docs/plans/PLAN-002-floorplan-parsing.md` §6–§10, §14
- `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md`
- `evidence/PLAN-002/acceptance.md`, `implementation/ac-traceability.md`,
  `determinism/geometry-projection-hashes.json`, `failures/parse-failure-matrix.json`,
  `overlays/layer-a-1-raster.svg`, `overlays/layer-a-1-dxf.svg`
- `tools/make_floorplan_fixtures.py`, `tests/golden/test_floorplan_golden.py`
- `schemas/floorplan_parse/v1/floorplan_parse-1.1.0.schema.json`, `src/pwa/intake.py`
