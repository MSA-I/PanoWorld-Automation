# PLAN-002RF / WP0 — CPU-only hardest-clean-raster feasibility gate: design memo

**Status: DESIGN ONLY. Nothing here is authorized to run.** This memo specifies a protocol for a
separately authorized WP0 spike; it does not report spike results, and it makes no accuracy claim.

---

## Context

PLAN-002RF §8 puts one stop-go condition on WP0: produce the *hardest-clean-raster protocol* and
**"stop if route to targets within 60 s / soft 1.5 GiB is implausible."** F-8 records that the
CPU-only Pillow/NumPy option is "CONDITIONALLY ACCEPT… capability remains speculative", and §1 says
plainly that "CPU-only Pillow/NumPy feasibility is unknown until a separately authorized WP0 spike."

The repository holds exactly one rights-cleared raster (`samples/Sample_Floorplan.jpg`, public
domain, 842 × 569, SHA-256 `917a5753…df08`). The only geometry that exists over it is the NA-5
hand-authored annotation, which its own record disclaims: *"This is not accuracy evidence… Room
areas are plausible, not correct."*

This memo answers what that single sample can and cannot decide, and specifies the protocol so the
answer is produced by measurement rather than by assumption.

**Headline finding, stated up front:** this sample **cannot** prove Product B-AUTO feasibility. It
is not merely a small sample — by the approved support classifier in packet §3 it is an
**unsupported** input (no authoritative scale anchors), so its correct pipeline outcome is a
**refusal**. Any run that emits geometry from it is a CRITICAL failure, not a success. What the
sample *can* do is prove the refusal path, the determinism contract, the containment controls, and —
through a resource ladder — bound the plausibility of the 60 s / 1.5 GiB target.

---

## 1. Provider / model / session evidence

| Field | Value | How verified |
|---|---|---|
| Requested provider | Anthropic first-party Claude Code | brief |
| Requested model | `opus`, exact runtime ID to be reported | brief |
| **Actual model (self-reported)** | **Opus 5, model ID `claude-opus-5`** | system environment block of this session |
| Actual provider | Anthropic first-party Claude Code CLI on Windows 10 Pro 19045 | session environment |
| **Session ID** | **`6a2a726e-170e-47fb-938f-f4dcc7f4e747`** | `SessionStart` hook payload |
| Transcript | `C:\Users\art1\.claude\projects\D----------------------------PanoWorld-Automation--worktrees-t-d025498b\6a2a726e-170e-47fb-938f-f4dcc7f4e747.jsonl` | `SessionStart` hook payload |
| Permission mode | `plan` | `UserPromptSubmit` hook payload (`"permission_mode":"plan"`) |
| Requested effort | MAX (`--effort max`), normalized scale of `docs/06` | brief |
| **Actual effort — UNVERIFIABLE** | no in-session channel exposes the effort/thinking parameter to me | see caveat below |
| Fallback | none requested; **none occurred** | no provider substitution in this session |
| Runtime / token / cost | **not available to me in-session** | must be taken from the caller's run report |
| Build / region / retention / training policy | **unknown** | not exposed |

**Effort caveat (do not paper over this).** `docs/06` §"שדות חובה ב-run report/state" requires both
the normalized and the provider-side effort value to be recorded. I can attest to the *requested*
value only. The actual `--effort` argument is set outside my context and is not readable from
inside the session, so the WP0 evidence bundle must take `EFFORT_PROVIDER_VALUE` from the launching
process (the Hermes/orchestrator invocation record), not from this memo. Reporting it here on my own
authority would be fabricated provenance.

**Routing conformance.** `docs/06` maps *Floorplan Parsing → CV/Spatial Architect → Opus 5 / EXTRA,
reviewer OpenAI GPT-5.6 / EXTRA*. This engagement is staffed at Opus 5 / MAX, i.e. **stricter than
policy**, which §"סטטוס וסמכות" permits ("תוכנית ספציפית רשאית להחמיר"). Per §"Cross-provider
review" and rule 6 ("אותו agent/model אינו גם המחבר היחיד וגם המאשר הסופי"), **this memo requires an
OpenAI-side independent review before it may be used to close U-8.** I am the author; I am not the
approver.

---

## 2. Skills — what was searched, found, and applied

Searched the installed skill set (2,356 skills under `C:\Users\art1\.claude\skills`) for
geometry / computer-vision / evaluation / threat-modeling matches. Four were loaded and applied.

| Skill | Loaded | Substantively applicable? | Effect on this memo |
|---|---|---|---|
| `computer-vision-expert` | yes | **No** | Content is entirely learned-model CV: YOLO26, SAM 3, VLMs, Depth Anything V2, ONNX/TensorRT edge deployment. Every technique it recommends is explicitly **prohibited** by packet §2.2 (no OCR, learned models, weights, training, GPU). Contributed nothing usable; recorded so its citation is not mistaken for methodological support. |
| `advanced-evaluation` | yes | **No** | Content is LLM-as-a-Judge: direct scoring, pairwise comparison, position/length/verbosity bias, rubric generation. The PLAN-002RF evaluator is a deterministic geometric matcher with adjudicated human truth — no judge model, no rubric. Not applicable. |
| `threat-modeling-expert` | yes | **Yes** | Applied its 8-step method (scope/trust boundaries → DFD → assets and entry points → STRIDE per component → attack trees → scoring → mitigations → **residual risks**) to §7 below. The explicit "document residual risks" step is what produces the honest Windows-RSS residual rather than hiding it. |
| `performance-profiling` | yes | **No** | Content is web performance: Lighthouse, Core Web Vitals (LCP/INP/CLS), bundle analysis, DevTools. Nothing about process working set, `tracemalloc` domain coverage, or native-allocator accounting. Its one transferable line — *"Measure, analyze, optimize — in that order"* — is already the WP0 premise. |

**Not available (searched, absent).** There is **no** computational-geometry, raster-vectorization,
classical-CV, Hough/morphology, planar-topology, NumPy, or Pillow skill installed. `threejs-geometry`
is WebGL scene geometry; `vector-database-engineer` / `vector-index-tuning` are embedding indexes.
The core technical content of this memo therefore rests on first-principles analysis of the
repository artifacts, not on a skill.

**Provenance note for the register.** Packet §12.2 records that the earlier "critical geometry memo"
and the "independent review" each applied `computer-vision-expert` (and the review also
`advanced-evaluation`, `threat-modeling-expert`). On inspection two of those three are substantively
inapplicable to a no-ML, no-OCR, deterministic geometry problem. The skill citations in §12.2 should
therefore **not** be read as evidence of domain-specific methodological support. This is a factual
observation about the record, not a challenge to those memos' conclusions.

---

## 3. Assumptions (each one falsifiable, each one named)

| # | Assumption | Basis | If false |
|---|---|---|---|
| A-1 | Packet bytes at SHA-256 `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7` are the controlling scope. | **Verified by me this session**: `sha256sum` over the file returns exactly that digest. | whole memo is scoped to the wrong baseline |
| A-2 | Locked dependency set is Python 3.11 + `numpy==2.4.6`, `pillow==12.3.0`, `ezdxf==1.4.4`, `pypdfium2==5.12.1`, `jsonschema==4.26.0`. | `uv.lock` read directly; `pyproject.toml` pins `requires-python = "==3.11.*"`. Note packet §12.1 says `pypdfium2` "lock currently" — it does not state a version; the lock says **5.12.1**. | version-pinned determinism claims void |
| A-3 | No new dependency may be installed for WP0. | packet §2.2, §12.1, brief | protocol must be redesigned; `psutil` would be the obvious ask |
| A-4 | The named local workstation is the one in `docs/02`: Windows 10 Pro 22H2 build 19045, Intel i7-9800X (8C/16T), 47.7 GB RAM, disk D with ~617 GB free. | `docs/02` §"מפרט שנבדק בפועל" | every runtime number is unanchored; WP0 §8 "target workstation" output unmet |
| A-5 | The NA-5 annotation is **not** truth and may not be used as truth, as a tuning target, or as a sanity check that influences any threshold. | `evidence/PLAN-002/visual-gate/na4-na5-record-20260811.md` §"What is NOT claimed"; packet AT-21 | evaluation becomes self-scoring; B is non-evaluable per AT-21 |
| A-6 | "Two machine-readable scale anchors" (packet §3, B source row) is a **precondition for support**, evaluated before geometry, not an output of geometry. | packet §3 Scale row: conventional-size assumptions and absent anchors are fail-closed | the scale/thickness circularity in §5.6 becomes unresolvable |
| A-7 | The WP0 spike may synthesize derived images (resized, degraded, corrupted, adversarial) **from the one existing sample**, locally, with no acquisition and no network. | zero-cost, no rights change, single source family; AT-20 requires derivatives stay in one split | the resource ladder is impossible and U-10 cannot be evidenced at all |
| A-8 | GPU/H200/cloud/network/spend/G7/G8/PLAN-003/activation are all out of bounds for WP0. | packet §10 hard boundary; brief | — |

---

## 4. What this sample can and cannot validly measure

### 4.1 The sample is out of the supported B envelope

Packet §3, **Scale** row — supported: *"B at least two authoritative anchors"*; unsupported and
mandatory fail-closed: *"conventional-size assumptions; one unreliable anchor; fabricated plausible
scale; absent/contradictory anchors."*

`samples/README.md`: *"There is no scale bar, so `scale_m_per_px` has to come from a known real
dimension or from the project manifest."* No project manifest supplies one.

The NA-5 record's four "anchors" are two interior door gaps measured against **an assumed 0.81 m
leaf** and two wall bands measured against **an assumed 24 cm exterior / 12.5 cm partition**. Those
are conventional-size assumptions by definition — the exact category §3 fails closed.

**Therefore the sample is supported-style but unsupported-scale.** Under the approved classifier it
is not an R0 clean-supported family; it belongs with the R3 refusal families. The "hardest clean
raster" fixture that WP0 §8 asks for **does not currently exist in the repository.**

### 4.2 Re-derivation: the sample fails AT-15 three independent ways

Recomputed from the numbers the NA-5 record itself states (37 px and 39 px against 0.81 m; 11 px
against 0.24 m; 6 px against 0.125 m). This is arithmetic over committed evidence — no fixture was
run.

| Anchor | m/px | residual vs median | ±0.5 px localisation error |
|---|---:|---:|---:|
| door gap, 37 px | 0.0218919 | **+2.66 %** | ±1.35 % |
| door gap, 39 px | 0.0207692 | **−2.61 %** | ±1.28 % |
| exterior band, 11 px | 0.0218182 | **+2.28 %** | ±4.5 % |
| partition band, 6 px | 0.0208333 | **−2.31 %** | **±8.3 %** |
| **median** | **0.0213258** (matches the recorded 0.0213) | — | — |

1. **AT-15 median residual ≤ 1 %** — every single anchor residual is ≥ 2.28 %. Median absolute
   residual ≈ **2.4 %, i.e. 2.4× the gate.** Fails.
2. **AT-15 disagreement ≤ 2 %** — max pairwise spread is (0.0218919 − 0.0207692) / 0.0213258 =
   **5.26 %, i.e. 2.6× the gate.** Fails, *before* the grid question is even raised.
3. **The rejected alternative** (dotted background read as a 50 cm construction grid) gives
   0.025 m/px — **≈ 17 % away, 8.7× the gate.** Under §3 that is "contradictory anchors" → fail
   closed. Fails.

**A structural consequence worth carrying into U-2:** at ±0.5 px endpoint localisation, a ≤ 1 %
median-residual gate requires an anchor spanning **≥ 50 px**; at a more realistic ±1 px, **≥ 100 px**.
The 6 px partition band carries ±8.3 % intrinsic error and can never be admissible. Anchors must
therefore have a declared **minimum pixel span**, not just a declared count.

### 4.3 Statistical reach of n = 1

| Approved gate | Requires | Reachable at n = 1 |
|---|---|---|
| AT-07 B clean yield ≥ 95 % | R0 = 30, ≥ 29 emit | **No** — denominator absent |
| AT-08 supported-scan yield ≥ 85 % | R1+R2 = 25, ≥ 22 emit | **No** |
| AT-09/10 wall P/R ≥ 0.995 macro, ≥ 0.980 per plan | adjudicated truth, slices | **No** — no truth (A-5) |
| AT-11/12 opening P/R | adjudicated truth | **No** |
| AT-13 zero critical FP + exact `3/n` bound | n frozen families | **No** — 3/1 = **300 %**, a vacuous bound |
| AT-14 tolerance boundary fixtures | below/at/above fixtures | Partially — synthetic boundary fixtures are constructible, but they test the *matcher*, not the *recognizer* |
| AT-15 scale | ≥ 2 authoritative anchors | **No** — and fails three ways (§4.2) |
| AT-16 topology | truth adjacency graph | **No** |
| AT-17 unsupported deterministic refusal | R3 + regressions | **Yes, partially** — this sample *is* an unsupported-scale input |
| AT-18 automatic-only execution | no interaction/edit/tuning | **Yes** |
| AT-19 deterministic replay | two clean runs, pinned env | **Yes** |
| AT-24 security/resource controls | adversarial matrix | **Yes**, on locally synthesized adversaries |
| AT-25 local-only boundary | full audit | **Yes** |

Five AT rows are reachable; twelve are not. WP0 must score **only** the reachable five and must
record the other twelve as NOT EVALUABLE — not as "pending", not as "provisionally passing".

### 4.4 Resource reach

- Sample is 479,098 px (0.479 MP) and 235,297 bytes.
- `src/pwa/floorplan/config.py:18` `MAX_SOURCE_PIXELS = 100_000_000` → the sample is **208.7× below**
  the pixel cap. `MAX_SOURCE_RASTER_BYTES = 50 MiB` → **222.8× below** the byte cap.
- A single native-resolution run therefore bounds **nothing** about worst-case time or memory. The
  resource question can only be approached by a **scaling ladder** plus a fitted complexity curve,
  with the extrapolation's admissibility itself gated (W-12 below).

**Two cap arithmetic findings for U-10, derivable now without running anything:**

- The proposed 32,768 px max side and the existing 100 MP decode cap interact: 100 MP / 32,768 =
  3,052, so a 32,768 px side is reachable only at aspect ratio ≥ 10.7 : 1. The **binding** cap is
  100 MP (max square side 10,000 px). U-10 should be restated so the two caps are not read as
  independent.
- At the 100 MP cap, one full-frame buffer costs: `uint8` 95.4 MiB, `float32` 381 MiB, `float64`
  763 MiB. Against a 1.5 GiB soft target that permits roughly **one** live `float64` full-frame
  array (47 % of budget), **three** `float32`, or **fifteen** `uint8` — and a `RGB→L` decode alone
  already costs ≈ 381 MiB (24 %). U-10 is therefore better expressed as a **static buffer budget**
  (max concurrent full-frame buffers × declared dtype) than as a single aggregate number, because
  the aggregate number is unenforceable at design review while the buffer budget is checkable by
  reading the code.

---

## 5. Protocol

Two tracks, run in one authorized spike. **Track C's expected outcome is a refusal.**

### 5.0 Preconditions (all must hold before any byte of the sample is decoded)

- Fresh interpreter, `PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`,
  `OPENBLAS_NUM_THREADS=1`, `PYTHONUTF8=1` (Hebrew repo path — see `pyproject.toml:20-25`).
- `environment.json` written **first**, containing: OS build, CPU model, physical RAM, Python
  version and build, `numpy.__version__`, `numpy.show_config()` digest, `PIL.__version__`, and
  **`PIL.features.pilinfo()` including the libjpeg / zlib / libpng versions and SIMD flags** — see
  the JPEG determinism hazard in §5.2.
- Working directory outside the repo; **no `runs/` directory in the tree is written** (the NA-4/NA-5
  precedent).
- Manifest read and hash-checked before the image is opened.

### 5.1 S0 — Intake and containment (fail-closed, before allocation)

| Step | Rule | Refusal condition |
|---|---|---|
| path | resolve; reject symlink, NTFS **junction**, and any reparse point via `os.lstat().st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT` (a plain `Path.is_symlink()` misses junctions on Windows); assert containment inside the declared root after resolution | `PATH_OUTSIDE_ROOT`, `PATH_REPARSE_POINT` |
| ADS / UNC / long path | reject `:` alternate-data-stream syntax, `\\?\`, `\\host\share`, and paths > 260 chars unless long-path-aware | `PATH_UNSUPPORTED_FORM` |
| bytes | `stat().st_size ≤ MAX_SOURCE_RASTER_BYTES` (reuse `config.py:17`) | `PARSE_RESOURCE_LIMIT` |
| hash | SHA-256 of source bytes **must equal** manifest `rights.source_sha256` | `SOURCE_HASH_MISMATCH` |
| bomb guard | set `Image.MAX_IMAGE_PIXELS = MAX_SOURCE_PIXELS` **and** `warnings.simplefilter("error", Image.DecompressionBombWarning)` before `Image.open` — Pillow's default trips at 89.5 MP as a *warning* and only errors at 2×; leaving the default silently accepts 89.5–100 MP with a warning and rejects at a different point than the contract says | `PARSE_RESOURCE_LIMIT` |
| header-only probe | `Image.open()` is lazy: read `.size`, `.mode`, `.format`, `n_frames` and decide **before** `.load()`. Declared-dimension rejection must happen with zero pixel allocation | `PARSE_RESOURCE_LIMIT` |
| format allow-list | `format ∈ {JPEG, PNG}` by **content sniff**, not extension; `n_frames == 1`; `mode ∈ {L, RGB, RGBA, P}`. Reject CMYK, LAB, `I;16`, animated | `RASTER_UNSUPPORTED_FORMAT` |
| metadata | EXIF, ICC, XMP, and PNG ancillary chunks are read for the **audit record only** and never propagate to any emitted artifact. This directly addresses the open finding in `samples/README.md` that the raster overlay embeds source bytes verbatim, carrying this file's 7 EXIF tags into `parse/overlay.svg` | W-15 |

### 5.2 S1 — Canonical decode

- `P` → `RGB` with declared palette handling; `RGBA` → composite over **declared opaque white** via
  `Image.alpha_composite` (undeclared alpha handling is a silent nondeterminism source);
  `RGB → L` via Pillow's ITU-R 601-2 luma with its integer rounding.
- Emit `grayscale_sha256` over the raw `uint8` buffer.

**Named residual determinism hazard — JPEG IDCT.** libjpeg-turbo selects among SSE2/AVX2 IDCT paths
at runtime; different builds or CPUs can differ by ±1 LSB on some coefficients. AT-19 already
distinguishes *same-environment byte identity* (satisfiable) from *cross-environment normalized
pixels* (the reason the distinction exists). WP0 must (a) record `pilinfo()`, (b) prove
same-environment byte identity, and (c) declare cross-environment identity **out of scope until
U-11 fixes the normalized-pixel contract**. Do not claim cross-machine byte determinism for a JPEG
source.

### 5.3 S2 — Binarization

Global Otsu over the 256-bin histogram — pure integer/NumPy, no filters, deterministic.

| Parameter | Value | Why frozen |
|---|---|---|
| `BINARIZE_METHOD` | `otsu_global_v1` | versioned per packet §12.1 "algorithms/config to be versioned" |
| `OTSU_TIE_BREAK` | `lowest_index` among maxima of between-class variance | unspecified tie-breaks are a classic replay-breaker |
| `MIN_OTSU_SEPARABILITY` | η = σ²_B/σ²_T ≥ 0.70 | below this the histogram is not bimodal → refuse rather than binarize noise |
| `INK_POLARITY` | `dark_is_ink`, asserted | polarity inference is a guess |
| `INK_FRACTION_BAND` | [0.01, 0.35] | outside → refuse |

No adaptive/local thresholding in WP0: it adds unproven parameters and its own scale dependence.

### 5.4 S3 — Clutter suppression (connected components)

8-connected two-pass union–find labelling in NumPy. This is the **expected runtime bottleneck** and
is the primary thing the ladder must measure.

- Suppress components by bounding-box size, fill ratio, and aspect within declared bands. **No OCR** —
  text is suppressed as small dense blobs, never read.
- Every suppression is counted. `MAX_SUPPRESSED_INK_FRACTION = 0.25`; above it → refuse
  (`RASTER_CLUTTER_EXCEEDS_ENVELOPE`). Rationale: this sample carries furniture, stair treads, a
  compass rose, room labels and German CAD annotations (`BRH 87.50`, `16 Stg 17.5/22.7`), and the
  suppressor cannot distinguish a dropped glyph from a dropped short wall stub. An uncapped
  suppressor silently manufactures a clean plan.

### 5.5 S4 — Scale (**the structural blocker**)

**Rule for WP0: anchors are read from the per-plan manifest only.** `len(scale_anchors) < 2` →
refuse `SCALE_ANCHORS_INSUFFICIENT`. Never derive from conventional sizes. For this sample
(`scale_anchors: []`) the outcome is a refusal, deterministically.

**New conflict C-1 — escalate to Moshe, do not resolve here.** The approved B envelope requires "at
least two **machine-readable** scale anchors", but the approved technology envelope bans OCR and
learned models (§2.2). The two admissible anchor classes in a raster — a scale bar with a numeric
label, and a dimension line with a numeric label — both require **reading digits**. Within the
Pillow/NumPy no-OCR envelope there is therefore **no mechanism by which Product B-AUTO can obtain an
authoritative scale anchor from a raster at all.** The candidate resolutions are mutually exclusive
and all have costs:

| Option | Mechanism | Cost / objection |
|---|---|---|
| C-1a | human supplies per-plan `scale_anchors` out-of-band | §1 says humans "cannot … complete" product output; supplying the scale looks like completing it. Needs an explicit Moshe ruling, not an agent's reading. |
| C-1b | restrict B to inputs carrying machine-readable physical density (PNG `pHYs`, JPEG JFIF density, rendered-PDF page geometry) plus a declared print scale | deterministic and no-OCR, but narrows the envelope and still needs the drawing scale from somewhere |
| C-1c | non-OCR scale-bar *geometry* detector | measures the bar's pixel length but cannot read its value → still OCR. **Not viable.** |
| C-1d | admit OCR | contradicts §2.2. Requires reopening the technology envelope. |

**C-1b is the only option that is internally consistent with the packet as approved.** It is not
mine to choose. U-2 cannot be closed while C-1 is open.

### 5.6 S5–S7 — Recognition stages (cost-measured, accuracy NOT claimed)

**S5 straight walls.** No Hough in Pillow/NumPy; implement as a NumPy (θ, ρ) accumulator,
`HOUGH_THETA_STEP_DEG = 0.25` over [0, 180) = 720 bins, ρ at 1 px. At the 100 MP cap the accumulator
is 720 × 28,284 × int32 ≈ **77.7 MiB** — comfortable. Runtime is the problem: cost scales as
*ink-pixel count × θ bins*, and at 100 MP with 5 % ink that is ≈ 3.6 × 10⁹ element-operations, which
on the `docs/02` workstation plausibly lands in the tens of seconds against a 60 s whole-run cap.

**Protocol consequence:** the ladder must vary **ink-pixel count**, not only resolution. A ladder
that only upsamples holds the ink fraction roughly constant and will under-predict the worst case.

**S5b arcs.** A 3-parameter (cx, cy, r) Hough is memory-infeasible at the cap. Use contour following
plus a closed-form algebraic circle fit (Kåsa/Pratt, pure NumPy least squares) with an RMS residual
test. Bounds `ARC_MIN_RADIUS_PX`, `ARC_MAX_RADIUS_PX`, `ARC_MIN_SWEEP_DEG`, `ARC_MAX_RMS_RESIDUAL_PX`
are **U-3** and are not proposed here.

**S6 thickness — the circularity, stated explicitly.** Paired-edge thickness bands are declared in
metres, which needs scale; the only historic scale evidence on this sample was derived *from* wall
thicknesses. NA-5 broke the loop with an assumption. **Product B must not.** Thickness stays in
pixels until scale is independently fixed; if scale refuses, thickness is unresolvable, centreline
emission is impossible, and the run fails closed. This is the mechanism by which the whole B path is
gated on C-1.

**S7 topology.** Reuse, do not reimplement: `QUANTUM_M` (`config.py:5`), the face/adjacency and
leak/dangling validators in `src/pwa/floorplan/builder.py`, and the finding codes in
`src/pwa/floorplan/findings.py`.

**Anti-hallucination control.** Ink not explained by an accepted primitive above
`MAX_UNEXPLAINED_INK_FRACTION = 0.10` → refuse. This is what prevents a partially-understood drawing
from being emitted as a confident plan.

### 5.7 S8 — Emit or refuse

Emission requires *every* stage to have succeeded. **Proposed refusal-condition names in this memo
(`RASTER_LOW_CONTRAST`, `SCALE_ANCHORS_INSUFFICIENT`, `RASTER_CLUTTER_EXCEEDS_ENVELOPE`,
`RASTER_UNEXPLAINED_INK`, `RASTER_UNSUPPORTED_FORMAT`, `PATH_REPARSE_POINT`, …) are drafts, not
adopted codes.** F-15 requires append-only new blocking codes via ADR and U-9 owns the exact shapes.
WP0 supplies the *list of conditions that must be encodable*; WP2 assigns the codes.

### 5.8 Instrumentation — and a defect in the current harness

**`tracemalloc` is the wrong instrument here.** It traces allocations that go through Python's
`PyMem_*` domains. Pillow's decoder buffers and much of NumPy's array memory are allocated by C code
through the system allocator and are **not** counted. The packet §9 target is an *observed
working-set* figure, so the peak must come from the OS.

The untracked `tools/wp0_cpu_feasibility.py:82-96` measures peak with `tracemalloc` and compares it
against `SOFT_MEMORY_LIMIT_BYTES = 1_610_612_736`. That comparison can pass while the true working
set is several times larger. It must be replaced, not tuned.

**Correct method, no new dependency:**

- `ctypes` → `K32GetProcessMemoryInfo` (psapi) → `PROCESS_MEMORY_COUNTERS.PeakWorkingSetSize`, and
  `GetProcessMemoryInfoEx` → `PrivateUsage` for commit. Pure stdlib; satisfies A-3.
- Run the stages in a **child worker** and sample its working set from the parent at ≥ 10 Hz,
  mirroring the existing `src/pwa/floorplan/dxf_source.py` / `dxf_worker.py` subprocess pattern. This
  gives a real peak *and* gives the killability AT-24 requires.
- Time: `time.perf_counter_ns()` per stage, plus `time.process_time()` to separate CPU from wall.
  Report per-stage median and max over replays.
- **Cap conflict to reconcile in U-10:** the existing worker cap is `PARSER_TIMEOUT_S = 30`
  (`config.py:21`); the packet proposes a 60 s whole-run cap. Two different numbers currently govern
  overlapping scopes.

### 5.9 Determinism / replay proof

AT-19 requires two clean runs. WP0 requires **more** (strengthening is permitted; weakening is not):

| Replay | Varies | Must be identical |
|---|---|---|
| R1–R3 | nothing (3 runs, fresh interpreter each) | every per-stage hash and the canonical JSON, byte for byte |
| R4 | `PYTHONHASHSEED` = 1 | identical → proves no set/dict iteration order leaks into output |
| R5 | different CWD, different TEMP, different user-profile-relative path | identical → proves no absolute path, username, or timestamp is in canonical bytes (packet §9) |
| R6 | wall-clock separated by ≥ 1 h | identical → proves no timestamp leakage |

Any single mismatch is STOP, not "flaky".

### 5.10 Adversarial / refusal matrix

All synthesized locally from the one sample. Zero acquisition, zero network, zero spend.

| ID | Input | Required behaviour |
|---|---|---|
| A1 | JPEG truncated at 50 % | decode error → refuse; **no partial emit** |
| A2 | copy retaining all 7 EXIF tags | zero EXIF bytes in any artifact |
| A3 | highly-compressible PNG declaring > 100 MP | rejected at header, **zero pixels allocated** |
| A4 | CMYK / 16-bit / animated GIF / SVG renamed `.png` | refused by content sniff, not extension |
| A5 | symlink and NTFS **junction** pointing outside root | refused |
| A6 | `..` traversal, ADS `file.jpg:evil`, UNC, > 260-char path | refused |
| A7 | skew +4.9° and +5.1° | 5.1° refused on envelope; 4.9° not refused *for skew* |
| A8 | γ-compressed to 10 % dynamic range | `MIN_OTSU_SEPARABILITY` refusal |
| A9 | crop of the dotted background grid only | zero walls; **grid must never be promoted to walls** |
| A10 | crop of furniture symbols only | zero walls, zero openings, refuse via unexplained-ink |
| A11 | **manifest with two anchors disagreeing by 17 %** (the real 0.0213 vs 0.025 case) | refuse on AT-15 disagreement — the sample's own ambiguity becomes the test |
| A12 | kill during atomic finalization | no partial artifact, no orphaned lock, no corrupt output |
| A13 | ladder rung engineered to exceed 60 s | clean timeout refusal, verified process-tree kill, no orphan |

### 5.11 Resource ladder (Track R)

≥ 5 rungs spanning ≥ 16× in pixel count **and** an independent ink-fraction sweep (§5.6). Fit
log–log per stage; report the exponent and R². Extrapolate to the 100 MP cap. The extrapolation is
**inadmissible** unless W-12 passes.

---

## 6. Threshold table

These are **WP0-local gates**. They are additional to, and do not replace, weaken, or reinterpret,
any AT-01…AT-26 threshold.

| ID | Gate | Threshold | Failure action |
|---|---|---|---|
| W-01 | source hash | exact match to manifest | **STOP** |
| W-02 | rights | `approved` + public-domain recorded | **STOP** |
| W-03 | format/mode allow-list | JPEG/PNG, 1 frame, mode ∈ {L,RGB,RGBA,P} | refuse |
| W-04 | pre-allocation guards | bytes ≤ 50 MiB, declared px ≤ 100 MP, bomb warning→error, header-only decision | refuse |
| W-05 | support classifier | ≥ 2 manifest anchors, each spanning ≥ 50 px | refuse — **expected for this sample** |
| W-06 | independent truth present | `truth.independent == true` and a path | accuracy **NOT SCORED**; never "provisionally passed" |
| W-07 | determinism R1–R3 | 3/3 byte-identical | **STOP** |
| W-08 | invariance R4–R6 | identical under hashseed/CWD/TEMP/time | **STOP** |
| W-09 | native-resolution peak working set and wall time | reported, no pass/fail at n = 1 | informational only |
| W-10 | peak working set extrapolated to 100 MP | ≤ **0.75 GiB** (half of the 1.5 GiB soft target — headroom for the ×2 uncertainty of a 208× extrapolation) | PARTIAL |
| W-11 | wall time extrapolated to 100 MP | ≤ **30 s** (half of 60 s, same reasoning) | PARTIAL |
| W-12 | extrapolation admissibility | ≥ 5 rungs, ≥ 16× pixel span, ink sweep run, log–log R² ≥ 0.98 | W-10/W-11 become **inadmissible**, not "passed" |
| W-13 | network | zero sockets opened during the run | **STOP + incident** |
| W-14 | process control | no child beyond the declared worker; tree kill verified ≤ 5 s; zero orphans | **STOP** |
| W-15 | disclosure | zero EXIF/ICC/absolute path/username/hostname/PID/timestamp bytes in any emitted artifact | **STOP** |
| W-16 | adversarial matrix | 13/13 of §5.10 behave as required | **STOP** |
| W-17 | **outcome inversion** | this sample **must REFUSE**. An emit is a **CRITICAL** finding | **STOP + incident** |

**W-10/W-11 headroom, justified rather than asserted:** the extrapolation spans 208× in pixel count
from a single family. A 2× safety factor is the minimum defensible margin, and even that is a
judgement call, not a measurement. If Moshe prefers, the alternative is to reject extrapolation
entirely and hold U-10 blocked until a real large fixture exists — which is the more conservative
reading of §3's fail-closed posture.

### Decision rule

Evaluated conjunctively after both tracks complete:

- **GO** — *"CPU-only route to the resource targets is plausible; proceed to WP1 corpus lock."*
  Requires **all** of W-01…W-08 and W-13…W-17 pass, **and** W-10/W-11/W-12 pass, **and** C-1 has an
  explicit Moshe ruling. GO carries **no accuracy meaning whatsoever.**
- **PARTIAL** — W-01…W-08 and W-13…W-17 pass, but W-10/W-11/W-12 fail or are inadmissible, or C-1
  is unresolved. Return to Moshe with named options only: lower the pixel cap; raise the memory
  cap; narrow the support envelope; or take the §2.3 Option 2A A-only planning fallback. **Never**
  add manual operation, never weaken a gate, never install a dependency to rescue it.
- **STOP** — any of W-01, W-02, W-07, W-08, W-13, W-14, W-15, W-16, W-17 fails; or the harness emits
  geometry for this sample; or any accuracy figure is produced from it.

**Standing verdict, independent of the above:** *Product B-AUTO **accuracy** feasibility is
**NOT EVALUABLE** at WP0.* It is neither GO nor STOP — it is outside WP0's evidentiary reach and
belongs to WP1 (corpus + truth) and WP4. WP0 must say so in those words.

---

## 7. Security and resource risks (STRIDE, per `threat-modeling-expert`)

Trust boundary: untrusted image bytes and an untrusted manifest cross into a local CPU worker that
writes to a local evidence directory. Entry points: file path, image bytes, manifest JSON. Assets:
repository integrity, private evidence, the workstation itself, and the truthfulness of the record.

| STRIDE | Threat | Control | Residual |
|---|---|---|---|
| **S**poofing | manifest declares a hash for a different file | W-01 hash-before-decode | low |
| **T**ampering | derived ladder images silently substituted for the source family | every rung's SHA-256 recorded and bound to the parent hash | low |
| **R**epudiation | run cannot be reproduced or attributed | `environment.json` + R1–R6 + hash-bound records | JPEG IDCT cross-environment variance (§5.2) — **named, accepted, U-11** |
| **I**nfo disclosure | EXIF/ICC/paths/username leak into committed evidence | W-15 byte scan; metadata never propagates; **this is a live open finding today** (`samples/README.md`) | low once W-15 enforced |
| **D**enial of service | decompression bomb; pathological ink fraction driving S5 past the cap | header-only rejection; `MAX_IMAGE_PIXELS` + warning→error; ink-fraction band; 60 s cap; tree kill | **Windows has no portable hard RSS sandbox** — packet §9 already accepts this; the soft target is *observed*, not *enforced* |
| **E**levation | symlink/junction/reparse escape; ADS; UNC | §5.1 path rules incl. `FILE_ATTRIBUTE_REPARSE_POINT` | low |

**Attack tree, "false plan accepted as real"** — the highest-value attack because it corrupts the
record rather than the machine:
`root: emit plausible-but-wrong geometry`
→ `(a) supply a manifest with fabricated anchors` — blocked by W-05 span rule + A11 disagreement test;
→ `(b) supply an input whose clutter suppressor drops real walls` — blocked by `MAX_SUPPRESSED_INK_FRACTION`;
→ `(c) supply an input where unexplained ink is ignored` — blocked by `MAX_UNEXPLAINED_INK_FRACTION`;
→ `(d) tune thresholds until this sample emits` — **blocked only by governance**, see U-6 below. This
is the branch with no technical control, and it is the one most likely to be taken by a
well-intentioned implementer under schedule pressure.

**Resource risks specific to this design:** the S3 union–find pass and the S5 accumulator are the two
stages that can breach both caps; the ladder must report them separately so a failure names a stage
rather than the pipeline. The `tracemalloc` instrumentation defect (§5.8) is itself a security-of-
evidence risk: it produces a number that *looks* like a passing memory measurement and is not one.

---

## 8. U-1 … U-15 recommendations

Legend — **RECOMMEND**: WP0 evidence supports a resolution. **BLOCKED (+support)**: the decision
stays blocked, but WP0 evidence supports a named constraint that any resolution must satisfy.
**BLOCKED**: no WP0 evidence bears on it.

| ID | Verdict | WP0-supported content | Missing evidence | Owner |
|---|---|---|---|---|
| U-1 chain partial credit | **BLOCKED** | none | adjudicated truth + frozen matcher (WP1) | Moshe + Evaluation Reviewer |
| U-2 scale fit / disagreement | **BLOCKED (+support)** | Anchors must carry a **minimum pixel span ≥ 50 px** (≥ 100 px at ±1 px localisation), derived in §4.2 — a 6 px band carries ±8.3 % intrinsic error and can never meet a 1 % gate. Draft, non-binding: disagreement = `max pairwise |sᵢ−sⱼ| / median(s)`. **Blocked above all by new conflict C-1** (§5.5): no no-OCR mechanism to obtain a raster anchor exists. | Moshe's C-1 ruling; anchor-bearing corpus | Moshe + Geometry/Evaluation Reviewer |
| U-3 arc bounds | **BLOCKED (+support)** | Method constraint only: 3-parameter circle Hough is memory-infeasible at the 100 MP cap; use algebraic circle fit + RMS residual. No numeric bounds proposed. | arc-bearing raster families | Moshe + Geometry Reviewer |
| U-4 clustering/merge/T-split bounds | **BLOCKED (+support)** | Instrumentation requirement: every merge/split/snap/dedup must be logged as a counted, reversible edit-op with a declared budget, and exceeding the budget must refuse. Numbers unproposed — you cannot know whether a merge changed semantics without truth. | truth + semantic-change fixtures | Moshe + Contract/Geometry Reviewer |
| U-5 symbol/style guide + support classifier | **BLOCKED (+support)** | Architecture only: the classifier must decide support **before** any geometry stage, on declared features, with its decision hash-bound. **WP0 evidence argues against resolving U-5 now** — calibrating on n = 1 overfits to this exact German-CAD/American-label style and is precisely the gaming §5 anti-gaming rules exist to prevent. | ≥ 60 raster families across strata | Moshe + Evaluation Owner |
| U-6 role names / overlap matrix | **BLOCKED (+support)** | Adopt the packet's strict separation **and add**: *the party that authored or executed the feasibility harness may not sign its WP0 disposition.* Supported by direct WP0 evidence — the NA-4/NA-5 record shows one orchestrator authoring the geometry, running the parse, and disposing the gate; and §9 below records harness code authored and executed in this same worktree during this session. Attack-tree branch (d) has no technical control, only this one. | named individuals | Moshe + Governance Approver |
| U-7 corpus rights / zero-spend | **BLOCKED (+support)** | Factual finding for the register: **exactly one** rights-cleared raster exists today. The "incremental infrastructure USD 0" line in §8 therefore has **no evidentiary basis** for a 100-family corpus, and should not be restated until it does. | source/licence manifest for ~100 families | Moshe + Rights Owner |
| U-8 CPU spike protocol + stop thresholds | **RECOMMEND** | **This memo is the candidate resolution**: §5 protocol, §6 thresholds W-01…W-17, and the GO/PARTIAL/STOP rule, including the standing "accuracy NOT EVALUABLE" verdict. | cross-provider independent review (`docs/06` rule 6 — I am the author, not the approver) | Moshe + OpenAI-side reviewer |
| U-9 schema/catalog/code versions | **BLOCKED (+support)** | WP0 supplies the **list of refusal conditions that must be encodable** (§5.7). The names used here are drafts and must not be adopted as codes — F-15 requires append-only codes via ADR. | ADR-0006 + contract review | Contract Reviewer / ADR |
| U-10 32,768 px / 60 s / 1.5 GiB | **BLOCKED (+support)** | Three supported items: (i) the **named workstation can be fixed now** from `docs/02` (i7-9800X 8C/16T, 47.7 GB, Win10 19045) — a WP0 §8 required output that needs no new evidence; (ii) the binding cap is **100 MP**, not 32,768 px (§4.4), and U-10 should be restated so the caps are not read as independent; (iii) restate the memory target as a **static buffer budget** (max concurrent full-frame buffers × dtype), because the aggregate number is unenforceable at review while the buffer budget is checkable. Also: `PARSER_TIMEOUT_S = 30` conflicts with the proposed 60 s. | measured ladder (W-10/11/12) | Moshe + Security/Performance Reviewer |
| U-11 renderer/font/CVD/normalized pixels | **BLOCKED (+support)** | `environment.json` must record `PIL.features.pilinfo()` incl. libjpeg/zlib versions and SIMD flags: JPEG IDCT variance is a real cross-environment hazard for the normalized-pixel contract (§5.2). | pinned renderer/font decisions | QA / Security / Reproducibility Reviewers |
| U-12 labour/cost cap | **BLOCKED** | none | Moshe's cap decision | Moshe |
| U-13 CAD refusal cases + passage minima | **BLOCKED** | none — CAD/Product A, outside WP0's raster scope | corpus decision | Moshe + Corpus/Evaluation/Geometry Reviewers |
| U-14 confidence calibration / G1 | **BLOCKED (+support)** | `LOW_CONFIDENCE_THRESHOLD = 0.5` is a **live constant today** at `src/pwa/floorplan/config.py:8`. Any U-14 resolution must state whether it is retained, and F-22's "diagnostic only, never overrides" must be enforced by a test asserting the constant does not gate emission. | calibration semantics / ADR | Moshe + Contract/Evaluation Reviewers |
| U-15 durable Git anchor | **BLOCKED (+support)** | I verified the packet digest this session: `sha256sum` returns `95c4cfd8…422f7`, matching the approved value, while `.hermes/` remains untracked. Record that verification (digest + verifier + session ID + timestamp) in the WP0 evidence bundle so a later anchor can prove the bytes were unchanged in the interim. No commit is authorized here. | commit + SHA link | governance owner + Moshe |

**Summary: 1 RECOMMEND (U-8), 9 BLOCKED-with-supported-constraints, 5 BLOCKED outright, plus one new
escalation (C-1) and one new classification finding (C-2, §4.1: the sample is not an R0 family).**

---

## 9. Boundary audit

### What I did

Read-only, entirely local. 8 file reads (`Read`), 3 content searches (`Grep`), 4 shell commands
(`sha256sum` on the packet; three directory listings incl. one over the skills directory).
4 skills loaded. No subagents, no workflows, no MCP calls.

**One file written: this memo**, at `C:\Users\art1\.claude\plans\wp0-anthropic-opus-starry-glacier.md`
— the harness-designated plan artifact, **outside the repository**. **Zero repository files created,
modified, or deleted.**

### What I did not do

Did not open, decode, or process `samples/Sample_Floorplan.jpg`. Did not execute
`tools/wp0_cpu_feasibility.py`. Did not run `pytest` or any test. Did not install, add, upgrade, or
resolve any dependency. Did not make a network request of any kind (no `WebFetch`, no `WebSearch`, no
MCP fetch). Did not acquire data. Did not commit, stage, branch, merge, or push. Did not spend.
Did not touch GPU, H200, cloud, or any remote execution. Did not touch G7/G8, PLAN-003, or
`scene_geometry`. Did not activate any product route. Did not start implementation.

### What I did not do that the brief forbade weakening

Did not weaken, reinterpret, or restate any AT-01…AT-26 threshold — §6 adds WP0-local gates only.
Did not invent labels or ground truth. Did not treat the NA-5 annotation as truth (A-5). Did not
substitute manual operation anywhere in the protocol. Did not propose a fallback, a dependency, or a
human rescue for any failure path.

### Observed, not authored — flagged for governance

`git status` shows three untracked paths, none created by me:

| Path | Size | mtime |
|---|---|---|
| `tools/wp0_cpu_feasibility.py` | 5,173 B | 2026-08-12 11:13 |
| `tests/unit/test_wp0_cpu_feasibility.py` | 2,131 B | 2026-08-12 11:11 |
| `evidence/PLAN-002RF/WP0/{fixture-manifest.json, opus-spatial-design-prompt.md, opus-spatial-design-raw.json (0 B), opus-spatial-design-stderr.log (0 B)}` | — | 11:08–11:14 |

`tools/__pycache__/wp0_cpu_feasibility.cpython-311.pyc` (11:13) and
`tests/unit/__pycache__/test_wp0_cpu_feasibility.cpython-311-pytest-9.0.2.pyc` (11:14) both exist,
which means **the harness module was imported and its test executed under pytest during this session
window** — i.e. the raster fixture has already been opened and processed by another party. Stated as
fact, neutrally: I make no claim about whether that was authorized. Whether writing and running a
WP0 harness falls inside "WP0 decisions/ADR/feasibility design" or trips the packet §10 "no
implementation" boundary is Moshe's call, not mine. It is recorded here because a boundary audit that
omitted it would be incomplete, and because of U-6: **the party that wrote and ran that harness
cannot also sign the WP0 disposition.**

Two substantive defects in that harness, if it is carried forward:

1. **`tracemalloc` cannot measure the working set** (§5.8). Its memory assertion can pass while the
   real peak is several times larger. Replace with `K32GetProcessMemoryInfo.PeakWorkingSetSize`
   sampled from a parent process.
2. **`FIND_EDGES` + `count_nonzero` is not the Product B pipeline.** Its runtime and memory numbers
   bound a 3×3 convolution and two reductions — not connected-component labelling or a Hough
   accumulator, which are the stages that will actually breach the caps. Numbers from it must not be
   presented as feasibility evidence for the 60 s / 1.5 GiB target.

What it gets **right**, and should be kept: hash-before-processing, refusal on missing independent
truth, refusal on `len(scale_anchors) < 2`, `path_recorded: False`, and the explicit
`accuracy_note` declining to score. That is the correct fail-closed posture.

---

## 10. Direct answer: can this single sample prove Product B feasibility?

**No.** Not partially, not provisionally, not "subject to confirmation."

1. **It is not a supported input.** By packet §3 it has no authoritative scale anchors, so its
   correct outcome is a refusal. An unsupported input cannot demonstrate a supported-path capability.
2. **It fails the scale gate three independent ways** (§4.2): every anchor residual ≥ 2.28 % against
   a ≤ 1 % gate; internal spread 5.26 % against a ≤ 2 % gate; the rejected grid hypothesis 17 % away.
   And the 6 px partition anchor carries ±8.3 % intrinsic quantisation error — it is not an anchor at
   all.
3. **There is no truth to score against.** The only geometry over it was authored by the party that
   would be scored, and its own record disclaims it. Using it violates AT-21 and F-7.
4. **n = 1 makes the statistics vacuous.** The rule-of-three bound at n = 1 is 300 %. AT-07 needs
   29/30. Neither is approachable.
5. **It is 208× below the pixel cap**, so it bounds nothing about the resource targets on its own.

What it **can** do, and what WP0 should therefore ask of it: prove that the refusal path fires
deterministically and for the right reason; prove byte-identical replay under the pinned
environment; prove the containment and disclosure controls hold against a locally-synthesized
adversarial matrix; and — via the scaling ladder with a fitted, admissibility-gated extrapolation —
support or refute the *plausibility* of the 60 s / 1.5 GiB targets, which is exactly and only what
packet §8 asks WP0 to decide.

The most likely way this goes wrong is not a failed measurement. It is a successful-looking one: a
harness that emits geometry for this sample, reports a `tracemalloc` figure under 1.5 GiB, and is
read as evidence that CPU-only B-AUTO works. **W-17 exists to make that outcome a CRITICAL finding
rather than a green light.**

---

## 11. Verification (how a reviewer checks this memo without running anything)

| Claim | Check |
|---|---|
| packet hash | `sha256sum ".hermes/plans/2026-08-11_220700-plan-002rf-final-remediation-approval-packet.md"` → `95c4cfd8…422f7` |
| locked versions | `uv.lock` lines 53–54, 102–103, 129–130, 197–198, 246–247 |
| caps and constants | `src/pwa/floorplan/config.py:5,8,17,18,21`; `src/pwa/intake.py:21` |
| sample facts | `samples/README.md` (842 × 569, 235,297 B, 7 EXIF tags, "no scale bar") |
| anchor arithmetic (§4.2) | recompute 0.81/37, 0.81/39, 0.24/11, 0.125/6 from the four measurements stated in `evidence/PLAN-002/visual-gate/na4-na5-record-20260811.md` §"Scale, and why it is defensible" |
| "not truth" | same file, §"What is NOT claimed" |
| workstation | `docs/02-היתכנות-על-המחשב-הנוכחי-ולוחות-זמנים.md` §"מפרט שנבדק בפועל" |
| routing / cross-provider requirement | `docs/06-מדיניות-ניתוב-מודלים-ומאמץ.md` rule 6, §"Cross-provider review" |
| harness defects (§9) | `tools/wp0_cpu_feasibility.py:82-96` (tracemalloc), `:28-49` (FIND_EDGES probe) |
| boundary | `git status --short` — three untracked paths, none authored by me; no tracked file modified |

**Before U-8 may close:** an OpenAI-side independent review of this exact memo, per `docs/06` rule 6
and §"Cross-provider review". I am the author and cannot be the approver.
