משה — Write, Bash ו‑Task כולם מושבתים בסשן הזה, אז לא נוצר קובץ תוכנית; המפרט עצמו הוא התוצר והוא כאן במלואו. שום קובץ לא נערך, שום התקנה/רשת/מזהה/בדיקה לא רצו.

---

# PLAN-002RF WP0-FX1 — Hardest-Clean-Raster Fixture: Spatial/Geometry Design Specification

**Mode:** read-only design. No edit, no install, no network, no recognizer, no product route, no test, no GPU/cloud.

---

## 0. Context and honest scoping

### 0.1 The governing charter is not in this repository

`PLAN-002RF`, `PLAN-002R`, `WP0`, `WP0-FX1` and `FX1` appear **nowhere** in the working tree. `docs/plans/` holds only PLAN-000/001/002; a repo-wide grep for those tokens returns one incidental hit inside an SVG. Memory records a PLAN-002R remediation spec having been drafted, but it is not on disk here, and with `Bash`/`Task` disabled I could not reach other branches.

So this design is written against (a) the brief's constraints and (b) boundaries that **are** approved and readable here: PLAN-002 §3/§12/§13, ADR-0003, ADR-0004, ADR-0005, the on-disk schemas, and the canonical spatial brief `evidence/PLAN-002/design/post-approval-spatial-brief-2026-08-09.md`. **Nothing below is represented as approved text.** This is the single largest limitation.

### 0.2 Why FX1 needs to exist

`tools/make_floorplan_fixtures.py:16-84` builds the current Layer A fixture: one axis-aligned 8 m × 6 m rectangle, one dividing wall, two doors, two windows — and a PNG that is `Image.new("RGB", (2000, 1800), "white")`, i.e. **a blank canvas**. In Part 1 the raster path is driven entirely by a hand-authored `floorplan_annotation`, so nothing was ever drawn. The visual gate was then rejected. WP0-FX1 is the artifact that must exist before anything can be measured: a project-owned raster whose truth is frozen *before* any recognizer exists.

### 0.3 Skills inspected (read from `~/.claude/skills/`)

| Skill | Verdict |
|---|---|
| `svg-art-skill` | **Rejected.** Decorative/generative SVG wrappers (grids, fractals, spirals). No geometric-truth semantics; also wrong output format. |
| `algorithmic-art` | **Rejected.** "Philosophy → p5.js" built on *seeded randomness* — directly opposed to a determinism-first fixture. |
| `threejs-geometry` | **Rejected.** 3D `BufferGeometry`/WebGL. Wrong dimensionality and runtime. |
| `sympy` | **Rejected.** Exact symbolic arithmetic would genuinely help the arc, but SymPy is not in the locked dependency set (`pyproject.toml:6-12`) and PLAN-002 §3 forbids new dependencies. Its *idea* is honoured by §5.3's frozen-literal rule instead. |
| `canvas-design`, `excalidraw`, `networkx`, `qa-harness`, `data-structure-protocol` | **Rejected.** Design aesthetics, diagram authoring, graph library, browser screenshots, codebase graphs. None touches deterministic raster fixture geometry. |
| `verification-before-completion` | **Used (method).** "Evidence before claims" is why §11 makes every invariant a build-time assertion and §14 forbids accuracy claims. |
| `python-testing-patterns` | **Used (light).** Confirmed the generated-fixture idiom in `tests/conftest.py:39-42` / `src/pwa/fixtures.py` — fixtures are generated, not committed as opaque blobs. |

**No spatial-geometry, floorplan, CAD, rasterization or ground-truth skill exists in the installed catalogue.** Every geometric rule here is authored directly against the repository. This independently reproduces the finding already recorded at `post-approval-spatial-brief-2026-08-09.md:8`.

### 0.4 The four roles, kept apart

This is the load-bearing structural decision. Four artifacts, four jobs, **one direction of flow**.

```
  (1) SOURCE GEOMETRY  ──derives──▶ (2) RASTER RENDERING
   fx1-source-geometry.json           fx1.png (+ pixel buffer)
   authored integers, mm, y-up        pixels only; carries NO truth
   the only artifact containing
   a free human decision
        │
        └────derives──────────────▶ (3) FROZEN TRUTH
                                      fx1-truth.json
                                      mm + px + topology + IDs
                                      frozen BEFORE any recognition
                                             │
                                             └──▶ (4) ANCHOR MANIFEST
                                                    fx1-anchors.json
                                                    authoritative scale statement
```

- **(1)** authored; the origin of everything.
- **(2)** a pure function of (1). It is evidence of nothing — it is the thing to be recognised later. It never feeds back.
- **(3)** a pure function of (1) — **not** of (2), and never of a recognizer.
- **(4)** the scale statement, split out because scale is the one quantity a consumer may trust without trusting the rest of the truth.

**No arrow ever points left.**

---

## 1. Canvas and raster settings

```json
{
  "canvas": {
    "width_px": 2400, "height_px": 2000,
    "mode": "L", "bit_depth": 8, "background_value": 255,
    "total_pixels": 4800000,
    "envelope_class": "clean_plan",
    "png_encoder": { "format": "PNG", "optimize": false, "compress_level": 6,
                     "pnginfo": null, "exif": null, "icc_profile": null }
  },
  "value_palette": { "background": 255, "wall": 0, "opening_motif": 0, "anchor": 64, "clutter": 128 },
  "stroke_widths_px": { "wall": 3, "opening_motif": 2, "anchor": 2, "clutter": 1 }
}
```

**Grayscale `"L"`, not RGB.** One channel removes colour-management and channel-order drift, and the four distinct values let a checker separate the four layers by luminance alone. 4,800,000 px is ~4.8 % of `MAX_SOURCE_PIXELS` (1e8) and the file is orders of magnitude under `MAX_SOURCE_RASTER_BYTES` (50 MiB), so FX1 cannot trip a Part 1 resource limit.

**Metadata empty by construction** — pre-satisfies PLAN-002 §12's no-EXIF rule and the GC-7 sanitisation concern without needing a sanitisation pass at all.

**"Clean-plan envelope" — explicit definition.** FX1 is a clean CAD-style export, *deliberately* free of: sensor/scan noise, JPEG artefacts, skew, rotation, perspective, shadows, paper texture, colour bleed, banding, dither, antialiasing, and any resampling. Those degradations are a later, harder fixture (§14).

### 1.1 Rasterization rule — project-owned, not Pillow's line algorithm

Pillow's `ImageDraw.line(width>1)` join/cap behaviour is not contractually stable across versions, and `pyproject.toml:8` pins only `pillow>=10.0`. Relying on it makes "deterministic" a hope.

**Rule.** The pixel buffer is a specified mathematical function of the source geometry. For a stroke with centreline segment `S` and width `w` px, pixel `(i, j)` takes that stroke's value iff

```
dist( pixel_centre(i,j), S ) <= w / 2 ,   pixel_centre(i,j) = (i + 0.5, j + 0.5)
```

`dist` = point-to-**closed-segment** Euclidean distance, `float64`, comparison `<=`. Square caps are *not* used; caps are round by this definition, which is exactly why consecutive segments join seamlessly with **no join rule at all**.

Implementation: NumPy over each primitive's integer bbox inflated by `ceil(w/2)+1`. Pillow is used **only** to encode the finished array (`Image.fromarray(arr, mode="L")`), never to decide a pixel.

**Ambiguity guard (I7).** For every primitive and every pixel centre in its bbox, assert `abs(dist − w/2) > 1e-9`. No pixel ever sits a rounding hair from the threshold, so `<=` cannot flip on a different libm. If it fires, the **build fails** rather than emitting an ambiguous raster.

No antialiasing, no alpha, no blending. Later layers overwrite outright.

---

## 2. Coordinate systems

Three spaces. Every number declares its space in its field name.

| Space | Units | Origin | Y | Used by |
|---|---|---|---|---|
| **Source** | integer mm (`_mm`) | canvas bottom-left | **up** | (1), (3) |
| **Metric** | metres (`_m`) | same | up | (3), (4) |
| **Pixel** | px (`_px`) | canvas top-left | **down** | (2), (3), (4) |

```
MM_PER_PX = 5          SCALE_M_PER_PX = 0.005          H_PX = 2000

x_px = X_mm / 5                    X_mm = x_px * 5
y_px = 2000 - (Y_mm / 5)           Y_mm = (2000 - y_px) * 5
```

**The `H_PX` (not `H_PX − 1`) flip is inherited deliberately.** It is the convention already in force: `post-approval-spatial-brief-2026-08-09.md:266` gives `Y_raw = (height_px − y_px) * s`, and the existing fixture's `(200,1400) → (1.0,2.0)` round trip confirms it. It is a *boundary* convention, not a pixel-centre convention. "Correcting" it here would silently desynchronise FX1 from everything else, so it is kept and flagged. Consequence: `Y_mm = 0` maps to `y_px = 2000`, one row past the last valid row (1999). §3's margins keep all geometry far from that edge; I8 enforces it.

`MM_PER_PX = 5` is *why* the fixture is authored in millimetres: **every authored coordinate is a multiple of 5 mm, so it lands on an exact integer pixel with no rounding anywhere.** Authoring in metres and dividing to get pixels is what produced the 0.1 mm one-quantum defect recorded at `evidence/PLAN-002/visual-gate/na4-na5-record-20260811.md:44-55`. That mistake is designed out.

---

## 3. Source geometry — exact primitives with IDs and coordinates

Integer millimetres, y-up. **Normative.** IDs are authored strings, not content hashes (§9.1).

```json
{
  "doc": "fx1-source-geometry", "version": "1.0.0",
  "units": "mm", "y_axis": "up", "mm_per_px": 5, "canvas_px": [2400, 2000],
  "datum_note": "Source origin coincides with the canvas bottom-left corner boundary.",

  "wall_axes": [
    { "id": "W-S",    "kind": "segment", "a_mm": [1000,1500], "b_mm": [9000,1500], "role": "exterior" },
    { "id": "W-E-A",  "kind": "segment", "a_mm": [9000,1500], "b_mm": [9000,1750], "role": "exterior" },
    { "id": "W-APSE", "kind": "arc",     "role": "exterior",
      "centre_mm": [9000,3250], "radius_mm": 1500,
      "start_deg": -90.0, "end_deg": 90.0, "sweep": "ccw" },
    { "id": "W-E-B",  "kind": "segment", "a_mm": [9000,4750], "b_mm": [9000,5000], "role": "exterior" },
    { "id": "W-E-C",  "kind": "segment", "a_mm": [9000,5000], "b_mm": [9000,8500], "role": "exterior" },
    { "id": "W-N",    "kind": "segment", "a_mm": [3400,8500], "b_mm": [9000,8500], "role": "exterior" },
    { "id": "W-DIAG", "kind": "segment", "a_mm": [1000,6700], "b_mm": [3400,8500], "role": "exterior" },
    { "id": "W-W",    "kind": "segment", "a_mm": [1000,1500], "b_mm": [1000,6700], "role": "exterior" },
    { "id": "W-PV",   "kind": "segment", "a_mm": [4000,1500], "b_mm": [4000,8500], "role": "partition" },
    { "id": "W-PH",   "kind": "segment", "a_mm": [4000,5000], "b_mm": [9000,5000], "role": "partition" }
  ]
}
```

Pixel projection (all exact integers):

| Wall | `a_px` → `b_px` |
|---|---|
| `W-S` | (200,1700) → (1800,1700) |
| `W-E-A` | (1800,1700) → (1800,1650) |
| `W-APSE` | centre (1800,1350), R = 300 px |
| `W-E-B` | (1800,1050) → (1800,1000) |
| `W-E-C` | (1800,1000) → (1800,300) |
| `W-N` | (680,300) → (1800,300) |
| `W-DIAG` | (200,660) → (680,300) |
| `W-W` | (200,1700) → (200,660) |
| `W-PV` | (800,1700) → (800,300) |
| `W-PH` | (800,1000) → (1800,1000) |

What this buys, against the brief:

- **Straight walls** — eight axis-aligned segments.
- **Bounded circular-arc wall** — `W-APSE`, a semicircular apse, R = 1500 mm, bulging east. Bounded: finite radius, finite sweep, both endpoints coincident with straight-wall endpoints.
- **Diagonal geometry** — `W-DIAG`, Δ = (2400, 1800) mm. **Slope 3/4, not 45°.** A 45° diagonal is symmetric and hides sign and axis-swap bugs; a 3-4-5 diagonal does not, *and* it has exact integer length 3000 mm with exact rational unit direction `(0.8, 0.6)` — which is what makes the opening hosted on it land on exact integer pixels (§4.2).
- **Explicit rooms/topology** — three rooms, one closed outer loop, two partitions (§7).

Envelope: 8.0 m × 7.0 m of wall centrelines inside a 12.0 m × 10.0 m canvas. Margins: 1.0 m west, 1.5 m south, 1.5 m north, 3.0 m east (the apse consumes 1.5 m of the east margin, leaving 1.5 m clear). Those margins exist to hold the anchors (§6) outside the plan.

---

## 4. Openings — typed motifs, three host geometries

```json
{
  "openings": [
    { "id": "O-D1", "type": "door", "host_id": "W-S", "host_kind": "segment",
      "centre_mm": [2500,1500], "width_mm": 900,
      "span_a_mm": [2050,1500], "span_b_mm": [2950,1500],
      "span_a_px": [410,1700],  "span_b_px": [590,1700],
      "hinge_at": "span_a", "swing_side": "interior", "connects": ["R-HALL","EXTERIOR"] },

    { "id": "O-D2", "type": "door", "host_id": "W-PH", "host_kind": "segment",
      "centre_mm": [7000,5000], "width_mm": 900,
      "span_a_mm": [6550,5000], "span_b_mm": [7450,5000],
      "span_a_px": [1310,1000], "span_b_px": [1490,1000],
      "hinge_at": "span_b", "swing_side": "north", "connects": ["R-NE","R-SE"] },

    { "id": "O-P1", "type": "passage", "host_id": "W-PV", "host_kind": "segment",
      "centre_mm": [4000,6800], "width_mm": 1500,
      "span_a_mm": [4000,6050], "span_b_mm": [4000,7550],
      "span_a_px": [800,790],   "span_b_px": [800,490],
      "connects": ["R-HALL","R-NE"] },

    { "id": "O-W1", "type": "window", "host_id": "W-N", "host_kind": "segment",
      "centre_mm": [6000,8500], "width_mm": 1200,
      "span_a_mm": [5400,8500], "span_b_mm": [6600,8500],
      "span_a_px": [1080,300],  "span_b_px": [1320,300],
      "connects": ["R-NE","EXTERIOR"] },

    { "id": "O-W2", "type": "window", "host_id": "W-APSE", "host_kind": "arc",
      "centre_deg": 0.0, "half_angle_deg": 22.5, "start_deg": -22.5, "end_deg": 22.5,
      "tessellation_vertices": [12, 20],
      "width_basis": "arc_length",
      "connects": ["R-SE","EXTERIOR"],
      "derived": ["span_a_mm","span_b_mm","span_a_px","span_b_px","chord_mm","arc_length_mm"] },

    { "id": "O-W3", "type": "window", "host_id": "W-DIAG", "host_kind": "segment_diagonal",
      "centre_mm": [2200,7600], "width_mm": 1200,
      "span_a_mm": [1720,7240], "span_b_mm": [2680,7960],
      "span_a_px": [344,552],   "span_b_px": [536,408],
      "connects": ["R-HALL","EXTERIOR"] }
  ]
}
```

Three types × three host geometries (axis-aligned / diagonal / curved). That product is the hard part of "hardest".

### 4.1 The three motifs

Every motif is a *gap plus decoration*. **The gap is produced by splitting the wall polyline before drawing — never by erasing drawn pixels.** Erasure is order-dependent and would make the raster a function of draw order rather than of geometry.

| Type | Gap | Jamb ticks | Content inside the gap |
|---|---|---|---|
| `passage` | yes | 2 | **nothing** |
| `window` | yes | 2 | **two** glazing lines parallel to the host, offset ±40 mm perpendicular |
| `door` | yes | 2 | **one** leaf line (perpendicular, length = `width_mm`) + **one** quarter-circle swing arc, centre at the hinge jamb, radius = `width_mm` |

Jamb tick: perpendicular to the host at each span endpoint, total length 100 mm (20 px), centred on the host axis. All opening elements at stroke 2 px, value 0.

Types are separable by *stroke count inside the gap* — 0 / 2 / 2 — with the door distinguished by its arc. No text, no symbol font, no glyph anywhere.

**"Perpendicular" per host kind:** `segment` and `segment_diagonal` → the host's unit normal; `arc` → the **radial** direction at that angle. Glazing on `W-APSE` is therefore two concentric arcs at R = 1460 and R = 1540 mm over the same angular span, tessellated by the §5 rule.

### 4.2 `O-W3` is exactly integral, and that is the point

`W-DIAG` unit direction = `(2400,1800)/3000 = (0.8, 0.6)` — exact in decimal. Half-width 600 mm → offsets `(±480, ±360)` mm → span endpoints `(1720,7240)` and `(2680,7960)` mm → pixels `(344,552)` and `(536,408)`. **All integers.** A diagonally-hosted opening with zero rounding is a strictly stronger fixture than an approximated one.

### 4.3 `O-W2` boundaries coincide with tessellation vertices

`W-APSE` sweeps 180° in `N_APSE = 32` steps (§5) → step exactly `5.625°`. `O-W2` spans `[−22.5°, +22.5°]`, i.e. vertex indices **12 through 20**. The arc wall therefore splits at real vertices; no segment is ever cut mid-way.

**Design constraint, stated so it cannot be violated later:** *every opening boundary on an arc host must land on a tessellation vertex.* Mid-segment splitting is deliberately not specified — it would add a second, subtler rounding rule for no gain.

---

## 5. Arc parameters and tessellation rule

### 5.1 The rule

```
Given radius R (mm) and total sweep Θ (rad):
  N_min = smallest integer N >= 2 with sagitta(N) <= 0.5 px,
          sagitta(N) = R * (1 - cos(Θ / (2N)))  mm, compared as sagitta / MM_PER_PX px
  N     = smallest power of two >= N_min
Vertices: P_k = centre + R * (cos(θ0 + k*Θ/N), sin(θ0 + k*Θ/N)),  k = 0..N
```

Powers of two so that any future halving of an arc still lands on existing vertices.

### 5.2 The two instantiations, frozen

| Arc | R (mm) | Sweep | `N_min` | **N (frozen)** | Step | Sagitta |
|---|---|---|---|---|---|---|
| `W-APSE` | 1500 | 180° | 28 | **32** | 5.625° | ≈ 0.36 px |
| door swing (`O-D1`, `O-D2`) | 900 | 90° | 11 | **16** | 5.625° | ≈ 0.15 px |

Both sagittas sit well under the 0.5 px bound, so the choice is not boundary-sensitive. Sagitta figures are indicative; the ≤ 0.5 px *inequality* is what the builder asserts (I9).

### 5.3 Arc-derived values are frozen literals, not recomputed values

`cos`/`sin` come from platform libm and may differ by 1 ULP between machines. Bit-exact cross-platform trigonometry is not something to rely on.

**Rule.** Every arc-derived non-integer quantity — tessellation vertices, `O-W2` span endpoints, chord and arc lengths, apse polygon area — is **computed once by the builder and written into the frozen truth as a literal**. On every later build the value is *recomputed and compared* against the literal with tolerance `1e-6 mm`; a mismatch **fails the build**. The literal is the authority; recomputation is verification.

This is also why §4 authors `O-W2` by **angle** (`half_angle_deg: 22.5`) rather than by chord length: the authored value stays an exact decimal, and the irrational part is confined to derived, frozen fields.

**Digits I deliberately did not compute here.** `O-W2` span endpoints, chord and arc length; the 33 apse vertices; the 17 vertices of each door swing; the apse polygon area. They are marked `derived` and given as formulas, **not digits**, because hand-computed digits presented as normative is exactly the class of error §5.3 exists to prevent. Every *authored* integer above is normative and hand-checkable.

---

## 6. Scale anchors — three, non-collinear, spatially distributed

An anchor is a **drawn** feature whose real-world length is declared out-of-band in the anchor manifest. **There is no printed number anywhere in the image** — which is what makes "no OCR" structurally true rather than merely intended: there is nothing to read.

Each anchor is a baseline segment with a perpendicular end tick (200 mm / 40 px, centred) at each end, value 64, stroke 2 px, entirely in the canvas margins and outside the plan.

```json
{
  "anchors": [
    { "id": "A-S", "orientation": "horizontal",
      "a_mm": [1500,750],  "b_mm": [6500,750],
      "a_px": [300,1850],  "b_px": [1300,1850],
      "real_length_mm": 5000, "real_length_m": 5.0,
      "span_px": 1000.0, "derived_m_per_px": 0.005,
      "provenance": "authored_source_geometry:fx1-source-geometry#anchors[0]",
      "placement": "south margin, 150 px below W-S" },

    { "id": "A-W", "orientation": "vertical",
      "a_mm": [500,2000],  "b_mm": [500,8000],
      "a_px": [100,1600],  "b_px": [100,400],
      "real_length_mm": 6000, "real_length_m": 6.0,
      "span_px": 1200.0, "derived_m_per_px": 0.005,
      "provenance": "authored_source_geometry:fx1-source-geometry#anchors[1]",
      "placement": "west margin, 100 px left of W-W" },

    { "id": "A-D", "orientation": "diagonal_3_4_5",
      "a_mm": [10500,5500], "b_mm": [11700,7100],
      "delta_mm": [1200,1600],
      "a_px": [2100,900],   "b_px": [2340,580],
      "delta_px": [240,-320],
      "real_length_mm": 2000, "real_length_m": 2.0,
      "span_px": 400.0, "derived_m_per_px": 0.005,
      "provenance": "authored_source_geometry:fx1-source-geometry#anchors[2]",
      "placement": "east margin, north of the apse's Y-range" }
  ]
}
```

### 6.1 `A-D` placement — the constraints that bind

Three earlier placements were rejected, and a reader who later needs to move an anchor needs to know why:

1. **North margin** — only 1500 mm tall (`Y ∈ (8500, 10000)`); a 3-4-5 diagonal with usable length does not fit.
2. **Δ = (3200, 400)** — slope 1:8, not a 3-4-5 triangle, so the length is irrational and the derived `m/px` is not exact.
3. **East margin at `X ∈ [10600, 11800]`** — right-edge clearance 39 px, one pixel short of I8's 40 px floor.

Final: Δ = (1200, 1600) mm is a 3-4-5 triangle scaled ×400 → hypotenuse **exactly 2000 mm**; in pixels Δ = (240, −320), span **exactly 400 px**; `2.0 m / 400 px = 0.005` exactly. Placed at `Y ∈ [5500, 7100]`, well north of the apse's `Y ∈ [1750, 4750]`, so the nearest structure is `W-E-C` at `x_px 1800` — 300 px away. Right-edge clearance 59 px.

### 6.2 Why these three

- **Non-collinear** — directions `(1,0)`, `(0,1)`, `(3,4)`. All three pairwise cross products non-zero; no line contains all three midpoints.
- **Spatially distributed** — south, west and east margins; three different sides.
- **Isotropy evidence** — `A-D` is the one that proves the scale is the same along a non-axis direction. Two axis-aligned anchors alone cannot distinguish uniform scale from anisotropic scale.
- **Exactness** — all three have integer-pixel endpoints and derive `0.005 m/px` **exactly**. I6 requires exact equality, not tolerance.

### 6.3 Hash-binding strategy

```json
{
  "binding": {
    "source_sha256":   "sha256:<canonical hash of fx1-source-geometry.json>",
    "pixels_sha256":   "sha256:<hash of the canonical pixel-buffer byte stream>",
    "truth_sha256":    "sha256:<canonical hash of fx1-truth.json>",
    "png_file_sha256": "sha256:<sha256_file(fx1.png)>",
    "chain": "source -> {raster, truth} -> anchors -> manifest",
    "recognizer_inputs": []
  }
}
```

- `source_sha256` / `truth_sha256` / the anchors' own hash use the repository's existing normative algorithm, `compute_content_hash` (`src/pwa/contracts.py:22-31`): canonical JSON with `ensure_ascii=False, separators=(",",":"), sort_keys=True`, SHA-256, `sha256:` prefix, over the document with its own `content_hash` removed.
- `png_file_sha256` uses `pwa.files.sha256_file` (`src/pwa/files.py:19-24`).
- **`pixels_sha256` is the binding invariant, not the PNG hash.** SHA-256 over `header || arr.tobytes()`, where `header = b"FX1|L|8|2400|2000|C\n"` (C-contiguous, row-major). Mode and dimensions live *inside* the hash so two different rasters cannot collide by reshaping.
- **PNG file-byte identity is explicitly NOT claimed** across Pillow/zlib versions. Pixel-buffer identity **is** claimed, and is what every invariant and every future comparison uses.
- `recognizer_inputs: []` is an asserted literal (I13). Any future attempt to feed recognizer output into the truth must **delete an assertion**, visibly, in a diff.

**Freeze procedure.** All four documents plus the PNG are written with exclusive-create (`write_json_exclusive`, `src/pwa/files.py:48-55`, which already refuses to overwrite), then committed in one commit; the manifest records that SHA as `frozen_at_commit`. After the freeze commit the builder's only legal mode is `--verify`. **Regeneration in place is not a supported operation.**

---

## 7. Rooms, topology and clutter

### 7.1 Room polygons

Source mm, y-up, **CCW**, first vertex lexicographically smallest — matching the canonical-polygon rule already in force (spatial brief §4.4).

```json
{
  "rooms": [
    { "id": "R-HALL", "name_free": null,
      "polygon_mm": [[1000,1500],[4000,1500],[4000,8500],[3400,8500],[1000,6700]],
      "polygon_px": [[200,1700],[800,1700],[800,300],[680,300],[200,660]],
      "vertex_count": 5, "has_diagonal_edge": true, "has_arc_edge": false,
      "area_mm2": 18840000 },

    { "id": "R-NE", "name_free": null,
      "polygon_mm": [[4000,5000],[9000,5000],[9000,8500],[4000,8500]],
      "polygon_px": [[800,1000],[1800,1000],[1800,300],[800,300]],
      "vertex_count": 4, "has_diagonal_edge": false, "has_arc_edge": false,
      "area_mm2": 17500000 },

    { "id": "R-SE", "name_free": null,
      "polygon_mm": [[4000,1500],[9000,1500],[9000,1750],
                     "<W-APSE tessellation vertices k=0..32>",
                     [9000,4750],[9000,5000],[4000,5000]],
      "vertex_count": 39, "has_diagonal_edge": false, "has_arc_edge": true,
      "area_mm2_rect_part": 17500000,
      "area_mm2_apse_analytic": "derived: pi*R^2/2, R=1500",
      "area_mm2_polygon": "derived: shoelace over the tessellated ring (STRICTLY LESS than analytic)" }
  ]
}
```

Shoelace verification of the two integral rooms (hand-computed, indicative; the builder recomputes and freezes): `R-HALL` → +37,680,000 / 2 = **18,840,000 mm²**, positive ⇒ CCW; `R-NE` → +35,000,000 / 2 = **17,500,000 mm²**, positive ⇒ CCW.

`R-SE` is the hard one on purpose: it contains the apse as an **open alcove**, not a separate room, so its ring mixes straight edges with 32 tessellation chords. Truth records **both** the analytic apse area and the tessellated-polygon area, and names the polygon area as the one a consumer is scored against. Reporting only one would be a quiet lie about which number is authoritative.

`name_free: null` everywhere — room names would be text, text implies OCR, OCR is forbidden.

### 7.2 Topology

```json
{
  "topology": {
    "rooms": ["R-HALL","R-NE","R-SE"], "exterior": "EXTERIOR",
    "adjacency": [
      { "a": "R-HALL", "b": "R-NE",     "shared_wall": ["W-PV"],                 "openings": ["O-P1"] },
      { "a": "R-NE",   "b": "R-SE",     "shared_wall": ["W-PH"],                 "openings": ["O-D2"] },
      { "a": "R-HALL", "b": "R-SE",     "shared_wall": ["W-PV"],                 "openings": [] },
      { "a": "R-HALL", "b": "EXTERIOR", "shared_wall": ["W-S","W-W","W-DIAG"],   "openings": ["O-D1","O-W3"] },
      { "a": "R-NE",   "b": "EXTERIOR", "shared_wall": ["W-N","W-E-C"],          "openings": ["O-W1"] },
      { "a": "R-SE",   "b": "EXTERIOR", "shared_wall": ["W-E-A","W-APSE","W-E-B"],"openings": ["O-W2"] }
    ],
    "note": "R-HALL and R-SE share a wall with NO opening: adjacency-without-connection is represented explicitly, not by omission."
  }
}
```

That third row is the one that matters. A topology format that can only list *connections* cannot distinguish "not adjacent" from "adjacent but sealed", and a fixture that never exercises the difference will not catch a consumer that conflates them.

**Scope note:** `floorplan_parse` 1.1.0 has exactly one relational field, `openings[].wall_id`, and no adjacency graph at all (spatial brief §6.2). This topology block lives **only** in the FX1 truth document; it is not a claim that any Part 1 product emits it.

### 7.3 Clutter — bounded, non-text, adversarial by family

Nine items, four families, each confusable with **exactly one** structural class, so a later consumer must discriminate rather than pattern-match.

```json
{
  "clutter": {
    "count": 9, "value": 128, "stroke_px": 1, "min_clearance_mm": 150,
    "families": {
      "rect":      "closed rectangle - confusable with a room boundary",
      "circle":    "closed circle (tessellated, N=16) - confusable with the arc wall",
      "long_line": "long straight segment - confusable with a wall",
      "tick_run":  "short parallel segments - confusable with an opening's jamb ticks"
    },
    "items": [
      { "id": "C-1", "family": "rect",      "room": "R-HALL", "rect_mm": [1300,2600,2300,3400] },
      { "id": "C-2", "family": "rect",      "room": "R-NE",   "rect_mm": [4600,5600,6200,6800] },
      { "id": "C-3", "family": "circle",    "room": "R-NE",   "centre_mm": [7600,7000], "radius_mm": 600, "n_seg": 16 },
      { "id": "C-4", "family": "long_line", "room": "R-SE",   "a_mm": [4400,2200], "b_mm": [8400,2200] },
      { "id": "C-5", "family": "long_line", "room": "R-HALL", "a_mm": [1400,5000], "b_mm": [3600,5000],
        "adversarial_note": "COLLINEAR with W-PH (Y=5000) but disjoint from it; nearest approach 400 mm to W-PH's endpoint" },
      { "id": "C-6", "family": "tick_run",  "room": "R-HALL", "origin_mm": [1300,4000], "dir": "x", "pitch_mm": 300, "n": 5, "tick_mm": 800 },
      { "id": "C-7", "family": "tick_run",  "room": "R-SE",   "origin_mm": [4600,3400], "dir": "x", "pitch_mm": 300, "n": 5, "tick_mm": 600 },
      { "id": "C-8", "family": "rect",      "room": "R-SE",   "rect_mm": [7000,3600,8600,4400] },
      { "id": "C-9", "family": "circle",    "room": "R-SE",   "centre_mm": [6000,2800], "radius_mm": 400, "n_seg": 16 }
    ]
  }
}
```

`min_clearance_mm: 150` (30 px) from **any** wall axis, opening motif (including door swing arcs) or anchor, enforced by I5. The binding cases, checked by hand: `C-1` clears `O-D1`'s swing arc by ~200–235 mm (the arc's apex is at Y = 2400, `C-1` starts at Y = 2600); `C-2` clears `O-D2`'s swing arc by 350 mm. Everything else clears by ≥ 400 mm.

`C-5` is the deliberately nasty one: a segment **collinear with a real wall but disjoint from it**. Any consumer that merges collinear segments without checking the gap will get it wrong.

**Bounded means bounded:** exactly 9 items, exactly 4 families, all inside room interiors, all at value 128 / stroke 1 px — separable from structure by luminance alone if a consumer wants to cheat. That is fine: FX1's job is to *have* a frozen truth, not to be unsolvable.

---

## 8. Rendering order and style

Later layers overwrite earlier ones. No blending, no erase, no XOR.

| # | Layer | Value | Stroke | Contents |
|---|---|---|---|---|
| 0 | `background` | 255 | — | full-canvas fill |
| 1 | `clutter` | 128 | 1 px | the 9 items of §7.3 |
| 2 | `anchors` | 64 | 2 px | 3 baselines + 6 end ticks |
| 3 | `openings` | 0 | 2 px | jamb ticks, glazing lines, door leaves, swing arcs |
| 4 | `walls` | 0 | 3 px | wall axes **already split** at every opening span |

Within each layer, primitives are drawn in the explicit list order of §3/§4/§7 — never in dict-iteration order, never sorted at runtime.

**Layer 4 last** guarantees a wall is never occluded. **Wall splitting happens in geometry, before rasterization**: each wall axis is reduced to the sub-segments outside every opening span on it, and only those are drawn. Nothing is ever painted and then removed.

Style: **single-line centreline walls**, no double-line wall thickness — because the repository's whole geometry model is centreline-based (`RawWall.start/end`, `src/pwa/floorplan/types.py:22-27`), and a double-line rendering would make the raster disagree with the truth about what a wall *is*. Wall thickness is explicitly out of scope (PLAN-002 §3).

---

## 9. Independent-truth derivation rules

The truth document is a **pure function of the source geometry**, mechanically specified so a reviewer can re-derive it by hand from §3/§4/§7 without running anything.

| Truth field | From | Rule |
|---|---|---|
| `walls[].a_mm/b_mm` | source | verbatim copy |
| `walls[].a_px/b_px` | source | `x_px = X_mm/5`, `y_px = 2000 − Y_mm/5`; must be integral (I1) |
| `walls[].length_mm` | source | `hypot`; exact integer for all axis-aligned walls and for `W-DIAG` (3000) |
| `walls[].drawn_subsegments` | source + openings | wall axis minus every opening span on it |
| `arc.vertices_mm[k]` | source | §5.1 formula; **frozen literal**, re-verified at 1e-6 mm |
| `arc.vertices_px[k]` | `vertices_mm` | mapping above; **non-integral, frozen literal** |
| `openings[].span_*` | source | verbatim for segment hosts; frozen literal for `O-W2` |
| `openings[].width_m` | source | `width_mm / 1000`; for `O-W2` both `chord_mm` and `arc_length_mm` are given, and `width_basis` names which is authoritative |
| `openings[].host_kind` | source | `segment` \| `segment_diagonal` \| `arc` |
| `rooms[].polygon_mm` | source | authored ring; for `R-SE` the arc span is spliced in as vertices `k=0..32` |
| `rooms[].area_mm2` | polygon | shoelace over the ring **as recorded**; for `R-SE` the analytic apse area is given *additionally*, never instead |
| `topology.adjacency` | source | rooms sharing a wall axis, plus openings whose `connects` names both |
| `content_key` per entity | truth | identity string in the repository's format (§9.1) |
| every `*_sha256` | §6.3 | canonical hashing |

### 9.1 `content_key` — a bridge, not an ID

FX1 entity IDs are **authored strings** (`W-DIAG`, `R-SE`, `O-W2`). Content-addressed IDs are the parser's job, not the fixture's, and a hash is unreadable in a failing test.

Each truth entity additionally carries a `content_key`: the identity string in the repository's existing format (spatial brief §4.5) — `wall|<sx>|<sy>|<ex>|<ey>`, `room|<v0x>|<v0y>|…`, `opening|<type>|<wall_key>|<cx>|<cy>|<width>`, with `key(d) = "0.0000" if d == 0 else f"{d:.4f}"`.

This makes a future FX1-vs-parser comparison mechanical **without** FX1 pre-committing to the parser's anchoring convention. FX1 does **not** apply the parser's wall-endpoint anchor translation; it records raw metric values and states that the anchor transform is the consumer's step.

### 9.2 What the truth must never contain

- Any value from a recognizer, parser, detector, OCR engine or model — now or later.
- Any value read back from the raster. Truth flows source → truth; the raster is a sibling, not a parent.
- Any `floorplan_parse` or `floorplan_annotation` envelope. **FX1 truth is a fixture-local document and deliberately is neither** — and it *cannot* be: both schemas type `openings[].type` as `{"enum": ["door","window"]}` (`floorplan_annotation-1.0.0.schema.json:88`, `floorplan_parse-1.1.0.schema.json:187`), so `passage` is unrepresentable; and neither schema has any arc primitive at all. Forcing FX1 through them would need either a schema change (out of scope, §14) or a lossy encoding that destroys the exact features FX1 exists to carry.
- Any free text, room name, label or dimension string.

---

## 10. Artifacts, layout and rights

Proposed layout (PLAN-002RF's own is unreadable here):

```
tools/make_fx1_fixture.py                  # builder; --out, --verify
tests/fixtures/floorplan/fx1/
    fx1-source-geometry.json               # (1) authored
    fx1.png                                # (2) raster
    fx1-truth.json                         # (3) frozen truth
    fx1-anchors.json                       # (4) anchor manifest
    fx1-manifest.json                      # hashes, rights, provenance, frozen_at_commit
    NOTICE-fx1.md                          # rights statement
evidence/PLAN-002RF/WP0-FX1/build-record.md
```

`tests/fixtures/` is the established fixture root (`tests/fixtures/contracts/examples.json`); `tools/make_*.py --out` is the established generator idiom (`tools/make_floorplan_fixtures.py:87-92`, `tools/make_tiny_scene.py`).

```json
{
  "rights": {
    "origin": "project_owned_generated",
    "third_party_bytes": 0, "third_party_assets": [],
    "network_acquisition": "none", "vendored_from": null,
    "license": "same as repository",
    "attribution_required": false, "share_alike": false,
    "sensitive_content": false, "layer_b_attestation_required": false
  }
}
```

Every pixel is a function of integers written by this project. No downloaded image, no CAD template, no clip-art, no font (there is no text), no dataset. Therefore:

- **ADR-0003's vendoring obligations do not attach.** That ADR governs the Apache-2.0 PanoWorld demo subset and mandates a pinned commit SHA, `fixture-metadata.json`, `NOTICE` and an upstream licence copy. FX1 vendors nothing — and `NOTICE-fx1.md` exists to say so *affirmatively*, rather than leaving a reader to infer it from absence.
- **PLAN-002 §13's Layer B rights/sensitivity attestation does not apply** — that covers private real plans. FX1 is Layer A: synthetic, tracked, project-created.
- **PLAN-002 §13's "explicit project-generated provenance notice (not a claim that the repository has a root distribution license)"** is honoured verbatim: `NOTICE-fx1.md` states project authorship of this fixture and makes no claim about repository-wide licensing, which stays open under D-010.
- **LOCAL-ONLY:** the builder performs no network I/O, reads nothing outside its own constants, and writes only under `--out`.

---

## 11. Invariants — each asserted at build time, each a function of (1)/(2)/(3) only

A violated invariant **fails the build**. None requires a recognizer.

| # | Invariant |
|---|---|
| **I1** | Every authored coordinate in §3/§4/§6/§7 is an integer multiple of 5 mm, hence maps to an exact integer pixel. Arc-derived vertices are the sole, declared exception. |
| **I2** | Every opening span lies strictly inside its host with ≥ 200 mm of host remaining beyond each jamb. (Tightest actual: `O-P1`, 950 mm.) |
| **I3** | The exterior wall loop is closed and connected; no two wall axes overlap collinearly; every wall endpoint is shared with another wall or is an arc endpoint. |
| **I4** | Every room ring is simple (no self-intersection, no repeated vertex), CCW by shoelace, non-zero area; rooms are pairwise interior-disjoint. |
| **I5** | Every clutter item clears every wall axis, opening motif (**including swing arcs**) and anchor by ≥ 150 mm, and lies inside its declared room. |
| **I6** | ≥ 2 anchors (FX1 ships 3); at least one pair has non-zero direction cross product; **every** anchor's `real_length_m / span_px` equals `0.005` **exactly** — not within tolerance. |
| **I7** | No pixel centre lies within `1e-9` px of any stroke's `w/2` threshold (§1.1). |
| **I8** | All drawn geometry lies within `[0,2400) × [0,2000)` px with ≥ 40 px clearance from every canvas edge. |
| **I9** | Every arc's sagitta ≤ 0.5 px at its frozen `N`. |
| **I10** | The renderer exposes **no text primitive**. Structural, not a scan: `ImageDraw.text`, `ImageFont` and any glyph source are absent from the builder. |
| **I11** | Rebuild determinism: a second build into a fresh directory reproduces `pixels_sha256`, `source_sha256`, `truth_sha256` and the anchors hash exactly. |
| **I12** | Arc-derived frozen literals re-verify within `1e-6 mm` (§5.3). |
| **I13** | `recognizer_inputs == []`, and no truth field's provenance names a parser, detector or model. |
| **I14** | The raster contains **only** `{0, 64, 128, 255}`, and all four are non-empty. |

I14 is cheap and catches a whole class of silent failure — a mis-ordered layer, a wrong mode, or an accidental antialiasing pass all show up immediately as a fifth value.

---

## 12. Deterministic replay and hash requirements

- **No entropy.** No `random`, `time`, `uuid`, `os.urandom`, `datetime.now`, hostname, path or environment value reaches output. `PYTHONHASHSEED` is irrelevant: no `set`/`dict` iteration order reaches output — every ordering is an explicit list.
- **Float discipline.** All authored arithmetic is integer. `float64` appears only in (a) the rasterizer's distance test, guarded by I7, and (b) arc trigonometry, neutralised by the frozen literals of §5.3.
- **`--verify` mode.** Rebuilds into a temp directory, recomputes all hashes, compares against `fx1-manifest.json`, re-checks I1–I14, exits non-zero on any mismatch. The only supported post-freeze operation.
- **Byte-level output conventions**, matching the repo: JSON via `write_json_exclusive` (`indent=2`, `ensure_ascii=False`, LF, one trailing newline, insertion order preserved); `sort_keys=True` used *only* inside `compute_content_hash`'s ephemeral hashing serialization, never on disk.
- **PNG file bytes are not a determinism claim** (§6.3). `pixels_sha256` is.
- **Freeze ordering, which is the whole point.** `fx1-truth.json` is written and hashed in the same build as the raster, before any recognition exists anywhere in the project, and the manifest records `frozen_at_commit`. Any later change to truth is therefore a visible history event, not a silent re-derivation.

---

## 13. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Pillow/zlib drift changes PNG bytes. | Bind on `pixels_sha256`, not file hash; state the non-claim explicitly (§6.3). |
| R2 | Pillow line/join behaviour changes and moves pixels. | Don't use it — project-owned rasterizer (§1.1); Pillow encodes only. |
| R3 | libm `cos`/`sin` differ by 1 ULP across platforms, shifting arc vertices. | Frozen literals + 1e-6 mm re-verification (§5.3, I12). |
| R4 | A pixel centre sits exactly on a stroke boundary and flips between builds. | I7 guard; build fails rather than emitting ambiguity. |
| R5 | Someone routes FX1 through the annotation adapter "because it's a raster". | Structurally blocked — `passage` and arcs are unrepresentable in both schemas (§9.2). Restate in `NOTICE-fx1.md`. |
| R6 | Truth quietly regenerated from a future recognizer, destroying independence. | One-way chain; `recognizer_inputs: []` as an asserted literal (I13); exclusive-create writes; `frozen_at_commit`. |
| R7 | Authoring in metres reintroduces the 0.1 mm one-quantum defect already seen in this project. | Integer millimetres throughout, `MM_PER_PX = 5`, I1. |
| R8 | Scope creep into WP1 (scoring, harness, metrics). | §14 non-goals; FX1 ships **no comparison code**. |
| R9 | The apse polygon area quoted as if exact. | Both areas recorded; the tessellated one is named as the polygon truth (§7.1). |
| R10 | The `H_PX` vs `H_PX − 1` flip is "corrected" by a later contributor. | Documented as inherited and deliberate (§2), with the existing round trip cited. |
| R11 | PLAN-002RF's real charter differs from this design. | Stated up front (§0.1); this is a proposal against readable boundaries, not a restatement of approved text. |
| R12 | Anchors mistaken for structure by a consumer. | Distinct value 64, placed outside the plan envelope, enumerated in the anchor manifest. |

---

## 14. Negative space — what WP0-FX1 is not

**Not built here:**
- No OCR, no text, no glyph, no font, no label, no printed dimension — anywhere.
- No recognizer, detector, model, VLM, learned parser, or inference of any kind.
- No changes to `src/pwa/floorplan/**`, any schema, `contracts/`, or `pyproject.toml`.
- No `floorplan_parse` / `floorplan_annotation` document. FX1 is not a product input (§9.2).
- No DXF. FX1 is a raster fixture; a CAD twin is a separate decision.
- No scoring, matching, metric, tolerance tuning or evaluation harness — **that is WP1**.
- No degraded-raster variants (noise, skew, JPEG, scan artefacts). FX1 is the *clean* fixture.
- No third-party asset, download, vendoring, network, GPU, cloud or new dependency.
- No test execution, install, or product route in this design turn.

**Not claimed here:**
- **No accuracy, recall, precision, yield or difficulty claim of any kind.** FX1 has never been shown to any recognizer. "Hardest" describes the *geometric content* — arc host, diagonal host, three opening types, mixed-primitive room ring, adversarial clutter — and says nothing about how any system performs on it. PLAN-002 §13 rules that a fixture without labelled ground truth is a smoke test, not accuracy evidence; the converse holds here — FX1 *has* ground truth and still makes no accuracy claim, because no measurement has occurred.
- Not a claim that the truth is complete beyond FX1's own enumerated entities.
- Not a claim that PNG bytes are reproducible across environments (§6.3).
- Not a claim that any of this is approved.

---

## 15. Verification, for whoever implements this later (not run now)

1. `python tools/make_fx1_fixture.py --out <tmp>` → exit 0; 5 files + NOTICE.
2. `--verify` → exit 0, with I1–I14 reported **individually**, not as one aggregate boolean.
3. Build twice into fresh directories; assert `pixels_sha256` and all three document hashes are equal (I11).
4. Open `fx1.png` and confirm by eye: three rooms, one apse, one 3-4-5 diagonal, six openings in three visually distinct motifs, nine grey clutter items, three dark-grey anchors in the margins, **no text anywhere**.
5. `set(numpy.unique(arr)) == {0, 64, 128, 255}` (I14).
6. Re-derive by hand from §3/§4 alone the pixel endpoints of `O-W3` — `(344,552)` and `(536,408)` — and confirm they match `fx1-truth.json`. One wrong number anywhere in the chain fails this.
7. Confirm `fx1-truth.json` carries no `schema_id` of `floorplan_parse`/`floorplan_annotation`, and that `recognizer_inputs` is `[]`.

---

## Evidence block

| Field | Value |
|---|---|
| **Requested model alias** | first-party Anthropic Claude Code, **Opus**, effort **MAX**, no fallback authorized |
| **Actual model ID (authoritative runtime metadata)** | **Not available to me in this session.** The harness gives me the model only as prose context ("powered by the model named Opus 5 … exact model ID is `claude-opus-5`"), which per your brief is *not authoritative*. I have no tool that reads authoritative runtime JSON: `Bash`, `Task` and `Write` are all disabled here, so I could not read the session transcript or any runtime-metadata file. **Runtime capture must be done externally.** |
| **Session ID** | `c0d9917d-ce87-4f1c-9f92-e58d3c72c28a` — from the `SessionStart` hook JSON in this session's context. Transcript: `<home>/.claude/projects/D----------------------------PanoWorld-Automation--worktrees-t-c6b406c5/c0d9917d-ce87-4f1c-9f92-e58d3c72c28a.jsonl` (path prefix redacted per PLAN-002 §12). |
| **Effort** | Requested MAX. **Not independently verifiable by me** — no exposed runtime field reports effort. |
| **Fallback** | **No fallback invoked to my knowledge**, but I cannot prove that negative from inside the session, for the same reason the model ID is unverifiable. |
| **Provider separation** | Author: Anthropic. Per PLAN-002 §17 and `PROJECT-STATE.yaml.delegated_authority`, this design requires an **independent OpenAI reviewer** before it becomes implementable. |

### Limitations

1. **PLAN-002RF / WP0-FX1 charter unread** — not in the tree; `Bash`/`Task` disabled so other branches were unreachable. Designed against readable approved boundaries plus your brief. **Largest limitation.**
2. **Self-identification is not authoritative** — stated per the brief; runtime JSON to be captured separately.
3. **No file was written.** `Write` is disabled in this session, so the plan file could not be created; this response is the entire deliverable.
4. **No execution of any kind** — no build, render, hash or test. Every hash above is a placeholder for the builder to fill.
5. **Arc-derived digits deliberately withheld** — `O-W2` span endpoints, the 33 apse vertices, the door-swing vertices and the apse polygon area are given as *formulas*, not digits, precisely because hand-computed digits presented as normative is the failure mode §5.3 exists to prevent. All authored integers are normative and hand-checkable.
6. **Areas and clearances are hand-arithmetic** — `R-HALL` 18,840,000 mm², `R-NE` 17,500,000 mm², and the §7.3 clearance checks were computed by hand and are indicative; the builder recomputes and freezes.
7. **Invariants I1–I14 are specified, not verified** — no code was run.
8. **No skill covered this domain** — nine inspected and rejected as inapplicable, two used for method only. All geometry here is authored directly.
