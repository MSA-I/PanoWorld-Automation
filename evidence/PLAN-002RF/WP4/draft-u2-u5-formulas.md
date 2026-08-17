# DRAFT — WP4 blocker formulas for U-2 / U-3 / U-4 / U-5

Status: **DRAFT for Moshe + reviewers.** NOT an approved decision, NOT an ADR,
NOT a change to any frozen constant or contract. Nothing here is normative until
it survives the U-6 role-separation gate and is recorded append-only under U-9.

Purpose: turn each BLOCKED decision into an *exact formula + threshold* proposal,
and say explicitly which parts are derivable from the FX1 fixture today and which
parts still require below/at/above fixtures (and therefore stay BLOCKED).

Controlling packet: `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`.

---

## U-2 — Scale: the exact fit + agreement formula

### 2.0 Scale-source ladder (Moshe decision, 2026-08-17)

Moshe directed that scale be derived the way AutoCAD's SCALE→Reference works:
pick a *known* length in the drawing, measure it in pixels, and set
`scale = known_length / measured_pixels`. This is adopted as a **priority
ladder of scale sources**, highest first:

1. **Dimension lines in the plan** — detect a dimension annotation
   geometrically (extension lines + tick/arrow marks + the measured segment),
   then combine it with a real length that comes from the *user or a manifest*.
2. **Synthetic anchors** — the FX1 margin baselines are exactly a dimension
   line without the printed number; this is a special case of source 1.
3. **User-provided wall thickness** — when the plan has no usable dimension
   lines, the future system asks the user for the interior AND exterior wall
   thickness; the engine detects ≥3 walls, measures each thickness in px, and
   computes `s_i = thickness_m / thickness_px` per wall.
4. **None of the above** → `SCALE_ANCHORS_INSUFFICIENT`, refuse (never guess).

Two rules are load-bearing and unchanged by this ladder:

- **No OCR, ever.** Reading the *printed digits* (e.g. "70", "10 cm") off a
  dimension is OCR and remains forbidden (C-1 / W-05). The *real length* always
  comes from the user or a manifest — exactly as AutoCAD's Reference option does
  (the human types the real distance; the software only measures pixels). Only
  the *geometry* of the dimension line is detected from the image.
- **Every source still goes through the n≥3 + non-collinearity fit (§2.2–§2.5).**
  A single wall-thickness reading is one ruler and would re-open the n=1/n=2
  hole — so the thickness fallback measures ≥3 walls of mixed orientations and
  still refuses on disagreement. Wall thickness is additionally caveated:
  single-line plans draw no thickness, and even double-line plans may draw it
  symbolically, so a thickness-derived scale is lower-confidence and must be
  flagged as such (it is a *fallback*, not a primary anchor).

### 2.1 Per-anchor scale

For anchor `i` with declared real length `L_i [m]` and measured pixel span
`S_i [px]`:

```
s_i = L_i / S_i        # m/px
```

An anchor is admissible only if `S_i >= ANCHOR_MIN_SPAN_PX` (50 px, frozen W-05).
Sub-threshold spans are rejected *before* the fit — a short anchor is a noisy
ratio, not a disagreement to be averaged away.

### 2.2 Combined scale (robust estimator)

```
s* = median(s_i)                                  # primary
w* = sum(L_i) / sum(S_i)                          # length-weighted total
```

`s*` is the answer the engine uses. `w*` is a cross-check: because every FX1
anchor is exact, `s* == w* == 0.005`. In general the median is robust to one
gross outlier while the weighted total is physically the "total length / total
span". The two are *required to agree* (see 2.4), which catches an outlier the
median would otherwise silently absorb.

### 2.3 Agreement metrics (exact)

```
r_i        = |s_i - s*| / s*          # per-anchor relative residual
median_residual = max(r_i)            # frozen AT-15: <= 1%  (SCALE_MEDIAN_RESIDUAL_MAX)
disagreement    = max_{i<j} |s_i - s_j| / s*   # frozen AT-15: <= 2% (SCALE_DISAGREEMENT_MAX)
```

### 2.4 Why n >= 3 is required (the n=2 collapse)

For `n = 2`, `s* = (s1 + s2)/2` and therefore

```
median_residual = |s1 - s2| / (s1 + s2)
disagreement    = 2 * median_residual
```

The two thresholds are **the same test**: `residual <= 1%` ⟺ `disagreement <= 2%`.
With two anchors there is no way to detect that *one* of them is wrong — any two
ratios always "agree" by construction of the median. This is a correctness bug in
the current `fit_scale`, not just a cosmetic redundancy.

**Proposal:** scale resolution requires `n >= 3` admissible anchors. `n == 2`
(or `n == 1`) → `SCALE_ANCHORS_INSUFFICIENT`, fail-closed. This is already what
FX1 supplies (three anchors) and is the structural reason three were authored.

### 2.5 Isotropy requirement (non-collinear anchors)

Two axis-aligned anchors cannot distinguish uniform scale from anisotropic scale
(a scan stretched along one axis). The fixture's own rationale (§6.2 of the
spatial design) is that `A-D` (3-4-5 diagonal) exists precisely to prove isotropy.

**Proposal:** at least two anchors must have non-parallel directions (cross
product of their unit direction vectors non-zero beyond a tolerance), and the
anchor set must be non-collinear. A plan whose anchors are all parallel →
`SCALE_ANCHORS_INSUFFICIENT` (anisotropy cannot be excluded, fail-closed).
Directions are derived from the anchor endpoints (`a_px`/`b_px`), which the
current `_load_authoritative_anchors` drops — it must be carried forward.

### 2.6 Refusal (never guess)

If any of 2.1–2.5 fails, the engine refuses with a scale finding and emits an
empty payload. There is no "closest guess" fallback. The scale is only ever
resolved from *authoritative* anchors (manifest, hash-bound to the raster), never
from OCR digits (C-1/W-05).

### 2.7 Derivability now vs blocked

- **Derivable now** (from FX1): the exact `s_i` formula, median + weighted-total
  cross-check, the residual/disagreement formulas, the n≥3 rule, and the
  non-collinearity rule. All three FX1 anchors give `0.005` exactly, so I6
  (exact equality) is satisfied and the disagreement is 0.
- **Blocked**: the *product-side anchor discovery* (detecting the baseline + end
  ticks in a real raster and measuring `S_i`) is not implemented and needs its
  own below/at/above fixtures; the numeric disagreement thresholds (1%/2%) are
  inherited from AT-15 and remain draft until adjudicated labeler truth exists.
  The *refusal* path is implementable now; the *acceptance* of a real-world
  (non-hash-bound) scan is not.

---

## U-3 — Circular-arc bounds: radius / sweep / sampling

### 3.1 Fit + acceptance (already drafted in code)

```
circle = Kasa algebraic least-squares fit over the arc's ink points   # (cx, cy, r)
RMS    = sqrt( mean( (|p - c| - r)^2 ) )          # radial residual
accept iff RMS <= ARC_RMS_RESIDUAL_MAX_PX (1.0, U-3 draft)
```

Kåsa fit is linear, deterministic, and closed-form — appropriate here because the
sampled points are the contour itself (not a noisy scan). The RMS residual is the
acceptance gate: a true circular arc yields a sub-pixel residual; a clutter circle
or a straight line fails it.

### 3.2 Radius bounds (express in metres, after scale)

Raw-pixel radius is meaningless until scale resolves, so the bound must be
physical:

```
r_min_m  = DEGENERATE_WALL_M           # 0.05 m — below this a "wall arc" is a point
r_max_m  = (draft) some architectural cap, e.g. 50 m, OR
           canvas diagonal in metres if smaller
guard    = r_min_px <= r_px <= r_max_px   evaluated AFTER scale resolution
```

The current code uses `r < 10 or r > max(w, h)` px — a placeholder that is
*not* scale-aware and is therefore wrong for any non-FX1 scale. The correct
bound is physical and scale-derived.

### 3.3 Sweep bounds

```
sweep_min = (draft) tie to sagitta: if the chord sagitta over the detected
            angular span < epsilon, the feature is a straight line, not an arc
sweep_max = refuse full circle: sweep >= 360° - epsilon  → refuse
            (a closed ring is a clutter circle — C-3/C-9 — never a wall)
```

The fixture verifies sweep ∈ {90° (door swing), 180° (apse)}. Those are the only
two values with independent truth. Any claim about arcs outside {90°, 180°} is
**not** verified and stays BLOCKED.

### 3.4 Sampling / tessellation rule (already frozen, reuse it)

The representation rule is frozen in the spatial design §5.1 and
`cad_exact_geometry.py`:

```
N_min = smallest N >= 2 with sagitta(N) = R * (1 - cos(Θ / 2N)) <= 0.5 px
N     = smallest power of two >= N_min
```

Detection *samples* the contour pixels directly; the sagitta rule governs how the
recovered arc is *re-emitted*. Do not invent a second sampling rule.

### 3.5 Derivability now vs blocked

- **Derivable now**: the fit (Kåsa + RMS), the physical-unit radius guard, the
  refuse-full-circle rule, and the "sweep-min ties to sagitta" rule.
- **Blocked**: the numeric `r_min/r_max/sweep_min/sweep_max` bounds and the RMS
  acceptance threshold cannot be set from one image with exactly one true arc
  (R = 300 px, sweep 180°). They need below/at/above arc fixtures (e.g. R at
  10 px / 300 px / canvas-diagonal; sweep at 1° / 90° / 180° / 359°) with
  independent truth. No fixture ⇒ bounds stay BLOCKED; the engine must refuse
  any arc whose bounds it cannot verify rather than accept it on the draft 1 px.

---

## U-4 — Line-merge / over-segmentation bounds

### 4.1 The root cause (why "merge by gap" hallucinates)

The 70-fragment failure is not a pure threshold problem. Three distinct things are
conflated in the current recovery:

1. **Stroke thickness** — a 3 px stroke votes into 2–3 adjacent (θ, ρ) bins; this
   is *one* wall, split by binning.
2. **Opening motifs** — a wall is split in geometry at every opening, and the
   motif strokes (door leaf, glazing, jamb ticks) are themselves ink *inside* the
   gap, so the gap is never "empty". Merging by gap length alone therefore either
   fails to rejoin (motif ink hides the gap) or fabricates a wall across clutter.
3. **Angular bleed** — the 3-4-5 diagonal's Hough peak spreads across adjacent
   angular bins.

### 4.2 Collinearity (same physical line)

```
same line  iff  |Δθ| <= θ_tol   AND   |Δρ| <= ρ_tol
θ_tol = θ_step + 1.0          # stroke angular spread + bin
ρ_tol = WALL_STROKE_PX + 1.0  # stroke band
```

This is already in `hough_physical_lines` and is the correct *binning* level:
it collapses a thick stroke's duplicate bins into one physical line. Keep it.

### 4.3 Gap-merge rule (the change that matters)

Merge two collinear runs `A` and `B` (A ends before B starts) **iff** the
intervening gap `g = B.start - A.end` satisfies:

```
0 <= g <= WALL_OPENING_GAP_PX            # 3.0 m / 5 mm-per-px + margin = 620 px
AND the gap is a RECOGNIZED opening      # contains a typed motif (jamb ticks + leaf/glazing/nothing)
```

The second clause is load-bearing: a wall is split *only* at openings, so two
fragments of one wall are separated *only* by an opening motif — never by bare
empty space. This is exactly what makes `C-5` (a clutter segment collinear with
`W-PH` but disjoint from it) safe: `C-5` is value-128 clutter, never enters the
structural mask, and even if it did, the gap to `W-PH` is unannotated ⇒ no merge.

**Never merge across an unannotated gap.** That single rule eliminates the
"invented line" failure class regardless of the numeric gap bound.

### 4.4 Fragment length floor

```
fragment is a wall candidate iff length_px >= MIN_WALL_LENGTH_PX  # 0.05 m / 5 mm-per-px = 10 px
```

Applied *after* merge (a fragment may be short on its own but part of a merged
wall). Stray sub-threshold fragments are refused as over-segmentation evidence,
not silently promoted.

### 4.5 Merge provenance — every merge documented and reversible

Each merge emits a provenance record, not just a merged segment:

```
{
  "wall_id": ..., "kind": "merged_segment",
  "fragments": [ {id, t0, t1}, ... ],        # the pieces, ascending
  "gaps":     [ {from, to, px, classified_opening: true/false} ],
  "reason": "opening-gap-merge | stroke-thickness-merge",
  "reversible": true
}
```

The emitted wall is the merged result; the provenance list lets any reviewer or
consumer **undo** the merge and inspect the raw fragments. This is the U-4
"must be documented and reversible" requirement made concrete — it is a data
shape, implementable now with no fixtures.

### 4.6 Derivability now vs blocked

- **Derivable now**: the collinearity test, the "merge only across a recognized
  opening" rule, the fragment-length floor, and the merge-provenance record.
- **Blocked**: the *numeric* gap bound (`WALL_OPENING_GAP_PX`) is pinned to the
  frozen `PASSAGE_SPAN_MAX_M = 3.0 m` — correct for the clean envelope, but any
  claim that the same bound holds for other styles is unverified. Below/at/above
  gap fixtures (opening gap vs. wall end vs. `C-5`-style disjoint collinear) with
  independent topology truth are still required before the bound is frozen for a
  broader corpus. The 70-fragment FX1 case is a *finding*, not a fixture.

---

## U-5 — Style guide: this is a corpus problem, not a formula problem

### 5.1 What is and is not a formula

U-5 is the one decision with **no closed-form answer**. The blocker is
over-fitting to a single drawing; the only fix is a predeclared corpus with
independent truth across ≥60 drawings spanning distinct styles. What *can* be
predeclared now is the *shape* of the guide and the refusal envelope.

### 5.2 Supported slices — predeclared, additive

Each slice is either SUPPORTED (engine must emit) or REFUSED (engine must
fail-closed, not guess). Proposed minimal matrix:

| Slice | FX1 | Status | Min output |
|---|---|---|---|
| single-line centreline walls (clean) | yes | supported | walls + rooms + openings |
| double-line walls (paired edges → centreline) | no | supported later | walls (thickness recovered) |
| hatched / poché walls | no | refuse until fixture | — |
| text / room labels | no | refuse (no OCR) | — |
| furniture | no | refuse (clutter, value≠structural) | — |
| stairs | no | refuse until fixture | — |
| door swings / arcs | yes | supported | typed door |
| diagonal / non-axis walls | yes | supported | walls + openings |

The minimum the engine must always recognize is: **walls (segments + bounded
arcs), rooms (closed faces), and typed openings (door / window / passage)** —
and it must *refuse* (empty payload + finding) when it cannot reach a clean plan
rather than emit a partial one.

### 5.3 The 60-example corpus matrix (the actual U-5 deliverable)

No formula unblocks U-5; the deliverable is a predeclared matrix of source
families with independent truth, frozen *before* recognition. Structure:

```
per family: style slice, count, variation axis (rotation/scale/line weight/deg),
            independent labeler + adjudicator truth (AT-21)
total >= 60 drawings across >= N distinct slices
```

Each family needs below/at/above coverage for whatever threshold it exercises
(e.g. line weight just-under/at/over the stroke band; skew just-under/at/over the
orientation tolerance). This is the same "no tuning against truth" discipline
(AT-18/AT-21) applied at corpus scale.

### 5.4 Derivability now vs blocked

- **Derivable now**: the slice taxonomy, the minimum-recognition contract, the
  refusal envelope, and the corpus-matrix structure.
- **Blocked**: U-5 itself. With one drawing there is no way to know whether the
  engine recognizes "floorplans" or "this one floorplan". It stays BLOCKED until
  the corpus exists and is scored. The current `INK_FRACTION_BAND` lower bound
  (0.001, reconciled for the sparse FX1 line drawing) is explicitly flagged in
  code as a U-5 ratification item — it must be ratified, not silently kept.

---

## Conjunctive position

U-2 and U-4 have **formula-level answers derivable now** (n≥3 scale with median +
weighted cross-check and non-collinearity; merge-only-across-recognized-openings
with reversible provenance). U-3 has a **formula skeleton** whose numeric bounds
need arc fixtures. U-5 has **no formula** and is a corpus deliverable.

The one concrete correctness fix available today is the n=2 scale collapse in
`fit_scale` (§2.4): as written, a two-anchor scale can never fail its own
disagreement test. Requiring n≥3 closes that hole and is already satisfied by
FX1. **Implemented 2026-08-17** (`MIN_SCALE_ANCHORS = 3`; `fit_scale` returns a
null fit below n=3) and test-locked (TDD RED→GREEN, 3 scale tests; full suite
520 passed, same pre-existing exclusions/warnings). This is still a DRAFT change
for the U-2 gate: per U-6 it must survive a separate independent reviewer, and
per U-9 the constant is recorded append-only. It is NOT an approved decision and
NOT a weakened threshold — it tightens a refusal (two anchors now fail closed).
