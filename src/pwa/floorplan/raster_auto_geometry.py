"""raster_auto (Product B-AUTO) deterministic image geometry primitives.

Pure, deterministic NumPy/Pillow primitives for the CPU-only, no-OCR,
no-learned-model recognition of a supported clean raster floorplan. No model
call, no network, no I/O beyond caller-provided arrays.

The algorithms follow the frozen PLAN-002RF / WP0 (opus spatial-design) protocol
and the WP1 frozen evaluator conventions. Every threshold is a versioned,
documented constant; none is tuned against truth (anti-gaming: AT-18, AT-21).
Where a WP0 decision is still BLOCKED (U-2..U-5), the constant is declared as a
U-pending default and is never silently promoted to a frozen threshold.
"""

from __future__ import annotations

import math

import numpy as np

# --- Frozen raster-recognition constants (WP0 §6 + §3, versioned) ------------
ANCHOR_MIN_SPAN_PX = 50.0        # W-05: an admissible anchor spans >= 50 px
MIN_OTSU_SEPARABILITY = 0.70     # below this the histogram is not bimodal
# Draft WP0 §5.3 ink-fraction band, versioned. NOTE: the frozen FX1 supported
# fixture is a sparse synthetic line drawing at ~0.63% ink, below the 1% floor
# WP0's §5.3 drafted for photographed scans. The lower bound is therefore fixed
# at 0.1% for the supported clean line-drawing envelope; this is an explicit
# U-5 (style-guide) reconciliation, not a per-plan tune, and must be ratified
# with U-5 before any broader corpus is scored.
INK_FRACTION_BAND = (0.001, 0.35)
MAX_SUPPRESSED_INK_FRACTION = 0.25
MAX_UNEXPLAINED_INK_FRACTION = 0.10
SCALE_MEDIAN_RESIDUAL_MAX = 0.01  # AT-15: median anchor residual <= 1%
SCALE_DISAGREEMENT_MAX = 0.02     # AT-15: anchor disagreement <= 2%
MIN_SCALE_ANCHORS = 3             # U-2: <3 anchors cannot detect a wrong anchor (n=2 collapse)
HOUGH_THETA_STEP_DEG = 0.25
ARC_RMS_RESIDUAL_MAX_PX = 1.0    # U-3 (draft): arc fit acceptance bound

# --- Opening / wall structural constants (versioned) -------------------------
# Dark ink is structural (walls + openings); mid-gray clutter (value 128) and
# light anchors (value 64) are excluded by the frozen dark threshold.
DARK_INK_BELOW = 128
# A straight wall is a 3 px stroke in the FX1 supported envelope; the opening
# motifs (jamb ticks / leaf / glazing) are 2 px. The stroke-width tolerance
# band used by thickness recovery is a documented constant, not a tune.
WALL_STROKE_PX = 3
OPENING_STROKE_PX = 2
# Maximum admissible gap along a wall centreline that is still the SAME wall
# (i.e. an opening gap, not the end of the wall). With arc-first/diagonal-first
# detection the merge must NOT cross a detected arc's chord (2*radius; the corpus
# arcs span radius 200-300 px -> chord 400-600 px), while the largest opening in
# the corpus envelope is a passage of 1.5 m = 300 px. The bound is therefore the
# open interval (300, 400) px; 350 px is its midpoint. (A 3.0 m passage == a
# 3.0 m arc gap and cannot be told apart by gap length alone — that requires the
# U-4 "merge only across a recognised opening motif" check, still pending.)
WALL_OPENING_GAP_PX = 350.0       # between max opening (300 px) and min arc chord (400 px)
# Minimum wall length (px) that is still a recognisable wall (rejects stray
# fragments below the frozen DEGENERATE_WALL_M = 0.05 m -> 10 px).
MIN_WALL_LENGTH_PX = 10.0
MAX_HOUGH_PEAKS = 200


def otsu_threshold(hist: np.ndarray) -> int:
    """Global Otsu threshold over a 256-bin integer histogram.

    Frozen tie-break: among equal between-class-variance maxima, the lowest
    index wins. ``hist`` must be an integer array of length 256.
    """
    hist = np.asarray(hist, dtype=np.float64)
    total = hist.sum()
    if total <= 0:
        return 0
    probs = hist / total
    omega = np.cumsum(probs)
    mu_t = np.cumsum(probs * np.arange(256))
    mu_total = mu_t[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (mu_total * omega - mu_t) ** 2 / (omega * (1.0 - omega))
    between = np.nan_to_num(between)
    candidates = between[1:-1]
    if candidates.size == 0:
        return 0
    # np.argmax returns the lowest index on ties -> the frozen tie-break.
    best_idx = int(np.argmax(candidates))
    return best_idx + 1


def otsu_separability(hist: np.ndarray, threshold: int) -> float:
    """Between-class / total variance ratio (eta) for a chosen threshold."""
    hist = np.asarray(hist, dtype=np.float64)
    total = hist.sum()
    if total <= 0:
        return 0.0
    probs = hist / total
    idx = np.arange(256)
    mu_total = (probs * idx).sum()
    var_total = (probs * (idx - mu_total) ** 2).sum()
    if var_total <= 0:
        return 0.0
    omega0 = probs[:threshold].sum()
    omega1 = 1.0 - omega0
    if omega0 <= 0 or omega1 <= 0:
        return 0.0
    mu0 = (probs[:threshold] * idx[:threshold]).sum() / omega0
    mu1 = (probs[threshold:] * idx[threshold:]).sum() / omega1
    var_between = omega0 * omega1 * (mu1 - mu0) ** 2
    return float(var_between / var_total)


def binarize_dark_ink(image: np.ndarray, ink_below: int = DARK_INK_BELOW) -> np.ndarray:
    """Dark-ink binarization: pixels strictly below ``ink_below`` become 1.

    The FX1 fixture authors walls/openings at value 0 and anchors at 64, with
    clutter at 128 and background at 255. The frozen dark-ink split at 128
    separates structural ink from clutter deterministically (no adaptive
    thresholding; polarity is asserted, not inferred).
    """
    a = np.asarray(image)
    return (a < ink_below).astype(np.uint8)


def binarize_structural(image: np.ndarray) -> np.ndarray:
    """Structural-ink binarization: pixels of value 0 ONLY become 1.

    FX1 authors walls + opening motifs at value 0, scale anchors at value 64
    and clutter at value 128. Structural recognition (walls/openings) must
    exclude the anchor and clutter layers outright, so the structural mask
    selects the exact structural value. Deterministic and value-exact.
    """
    a = np.asarray(image)
    return (a == 0).astype(np.uint8)


def wall_centerlines(mask: np.ndarray) -> np.ndarray:
    """Isolate wall strokes from opening motifs by stroke width (FX1 envelope).

    The FX1 clean envelope draws walls as 3 px strokes and opening motifs (door
    leaves, glazing, jamb ticks) as 2 px strokes, all at the same structural
    value. A single binary erosion by a 3x3 structuring element removes the
    2 px motifs outright and thins each 3 px wall to its 1 px centreline — the
    exact wall skeleton the Hough stage should vote on, free of the motif ink
    that previously drove over-segmentation (review MAJOR #5/#7).
    """
    from scipy import ndimage

    return ndimage.binary_erosion(mask, structure=np.ones((3, 3)), iterations=1).astype(np.uint8)


def connected_components(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """8-connected two-pass union-find labelling, deterministic.

    Returns ``(labels, count)`` where ``labels`` is int32 with 0 = background
    and 1..count = component ids, assigned in scan order.
    """
    mask = np.asarray(mask, dtype=bool)
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    parent = [0]

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            nxt = parent[x]
            parent[x] = root
            x = nxt
        return root

    current = 0
    for y in range(h):
        row = mask[y]
        for x in range(w):
            if not row[x]:
                continue
            neighbors = []
            if x > 0 and labels[y, x - 1]:
                neighbors.append(int(labels[y, x - 1]))
            if y > 0:
                if labels[y - 1, x]:
                    neighbors.append(int(labels[y - 1, x]))
                if x > 0 and labels[y - 1, x - 1]:
                    neighbors.append(int(labels[y - 1, x - 1]))
                if x + 1 < w and labels[y - 1, x + 1]:
                    neighbors.append(int(labels[y - 1, x + 1]))
            if not neighbors:
                current += 1
                parent.append(current)
                labels[y, x] = current
            else:
                root = min(find(n) for n in neighbors)
                labels[y, x] = root
                for n in neighbors:
                    rn = find(n)
                    if rn != root:
                        parent[rn] = root
    for y in range(h):
        for x in range(w):
            if labels[y, x]:
                labels[y, x] = find(int(labels[y, x]))
    remap: dict[int, int] = {}
    out = np.zeros((h, w), dtype=np.int32)
    k = 0
    for y in range(h):
        for x in range(w):
            v = int(labels[y, x])
            if v == 0:
                continue
            if v not in remap:
                k += 1
                remap[v] = k
            out[y, x] = remap[v]
    return out, k


def hough_physical_lines(mask: np.ndarray, theta_step_deg: float = HOUGH_THETA_STEP_DEG, min_votes: int = 30,
                         *, max_lines: int = 64) -> list[dict]:
    """Cluster the Hough accumulator into DISTINCT physical lines.

    Unlike ``hough_lines`` (which returns raw NMS peaks, including the many
    near-duplicate peaks a 3 px wall stroke induces), this returns one
    representative ``(theta, rho, votes)`` per physical line: peaks are merged
    when their theta differs by <= ``theta_step_deg`` and their rho by <= the
    wall stroke width (they are the same wall seen across its thickness). The
    representative is the highest-vote cell in each cluster. This is a
    deterministic clustering of the accumulator, driven by the declared stroke
    geometry, not a per-fixture tune.
    """
    mask = np.asarray(mask, dtype=bool)
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return []
    h, w = mask.shape
    diagonal = int(np.ceil(math.hypot(h, w))) + 1
    thetas = np.arange(0.0, 180.0, theta_step_deg)
    theta_rad = np.deg2rad(thetas)
    acc = np.zeros((thetas.size, 2 * diagonal), dtype=np.int32)
    rho_offset = diagonal
    cos_t = np.cos(theta_rad)
    sin_t = np.sin(theta_rad)
    for x, y in zip(xs.tolist(), ys.tolist()):
        xf = float(x)
        yf = float(y)
        rho = np.rint(xf * cos_t + yf * sin_t).astype(np.int32)
        acc[np.arange(thetas.size), rho + rho_offset] += 1

    cells = [(int(acc[ti, ri]), int(ti), int(ri)) for ti, ri in np.argwhere(acc >= min_votes)]
    cells.sort(key=lambda c: -c[0])
    rho_tol = 2.0 * WALL_STROKE_PX + 2.0  # stroke width + wrap-induced rho smear
    # A WALL_STROKE_PX-wide stroke over a wall of length L subtends
    # atan(WALL_STROKE_PX / L) radians of angular spread, so a 3 px stroke
    # spreads its votes across adjacent theta bins. Merge peaks within that
    # spread plus one theta bin. 15 deg covers the stroke spread AND the T-junction
    # erosion artifact (a partition meeting a perimeter wall leaves a ~10 deg
    # near-axis echo); with arc/diagonal-first detection the Hough only sees
    # axis-aligned walls (>= 90 deg apart), so distinct walls never merge.
    theta_tol = 15.0 + theta_step_deg
    # A wall at perpendicular distance D from the origin shifts its rho by
    # ~D*sin(dtheta) when the line tilts by dtheta; the angular spread therefore
    # leaks a peak into an adjacent theta bin at a SHIFTED rho. Bound D by the
    # canvas diagonal so near-axis echoes (e.g. theta 0.5 deg -> rho +9 px for a
    # 1000 px wall) merge into their true peak instead of being emitted as
    # duplicate walls. (Geometry-derived; distinct walls >= ~200 px apart never
    # merge because their dtheta ~ 0 keeps the effective rho tolerance small.)
    lines: list[dict] = []
    for votes, ti, ri in cells:
        th = float(thetas[ti])
        rho = float(ri - rho_offset)
        # Merge into an existing physical line if within the stroke-geometry
        # tolerance (same theta bin and adjacent rho bins = same wall band).
        merged = False
        for line in lines:
            dtheta = abs(th - line["theta_deg"])
            wrapped = dtheta > 90.0
            dtheta = min(dtheta, 180.0 - dtheta)
            if dtheta <= theta_tol:
                # The same physical line at theta and theta+180 has rho of
                # OPPOSITE sign; negate rho for the wrapped branch before the
                # distance test, else a vertical wall is emitted twice (theta~0
                # and theta~180) — a direct over-segmentation contributor.
                rho_cmp = -line["rho"] if wrapped else line["rho"]
                # Scale the effective rho tolerance with the actual angular gap.
                rho_tol_pair = rho_tol + math.hypot(mask.shape[1], mask.shape[0]) * math.sin(math.radians(dtheta))
                if abs(rho - rho_cmp) <= rho_tol_pair:
                    # Keep the highest-vote representative; do not add duplicates.
                    merged = True
                    break
        if not merged:
            lines.append({"theta_deg": th, "rho": rho, "votes": votes})
            if len(lines) >= max_lines:
                break
    lines.sort(key=lambda p: -p["votes"])
    return lines


def hough_lines(mask: np.ndarray, theta_step_deg: float = HOUGH_THETA_STEP_DEG, min_votes: int = 30) -> list[dict]:
    """2-parameter (theta, rho) Hough accumulator for straight-wall segments.

    Returns a sorted list of peak dicts ``{theta_deg, rho, votes}``, each a
    distinct non-maximum-suppressed peak in the accumulator above ``min_votes``.
    Peaks are returned in descending vote order and capped to a bounded set.
    """
    mask = np.asarray(mask, dtype=bool)
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return []
    h, w = mask.shape
    diagonal = int(np.ceil(math.hypot(h, w))) + 1
    thetas = np.arange(0.0, 180.0, theta_step_deg)
    theta_rad = np.deg2rad(thetas)
    acc = np.zeros((thetas.size, 2 * diagonal), dtype=np.int32)
    rho_offset = diagonal
    cos_t = np.cos(theta_rad)
    sin_t = np.sin(theta_rad)
    for x, y in zip(xs.tolist(), ys.tolist()):
        xf = float(x)
        yf = float(y)
        rho = np.rint(xf * cos_t + yf * sin_t).astype(np.int32)
        acc[np.arange(thetas.size), rho + rho_offset] += 1

    above = np.argwhere(acc >= min_votes)
    cells = [(int(acc[ti, ri]), int(ti), int(ri)) for ti, ri in above]
    cells.sort(key=lambda c: -c[0])
    peaks: list[dict] = []
    for votes, ti, ri in cells:
        th = float(thetas[ti])
        rho = float(ri - rho_offset)
        if any(abs(th - q["theta_deg"]) < 2.0 * theta_step_deg and abs(rho - q["rho"]) <= 2.0 for q in peaks):
            continue
        peaks.append({"theta_deg": th, "rho": rho, "votes": votes})
        if len(peaks) >= MAX_HOUGH_PEAKS:
            break
    return peaks


def fit_circle(points: np.ndarray) -> tuple[float, float, float]:
    """Kasa algebraic circle fit (least squares) -> ``(cx, cy, r)``.

    Solves the linear least-squares problem for the circle
    ``x^2 + y^2 + D x + E y + F = 0``. Deterministic and pure NumPy.
    """
    pts = np.asarray(points, dtype=np.float64)
    x = pts[:, 0]
    y = pts[:, 1]
    A = np.column_stack([x, y, np.ones_like(x)])
    b = -(x * x + y * y)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    D, E, F = sol
    cx = -D / 2.0
    cy = -E / 2.0
    r = math.sqrt(max(0.0, (D * D + E * E) / 4.0 - F))
    return (float(cx), float(cy), float(r))


def circle_fit_residual(points: np.ndarray, circle: tuple[float, float, float]) -> float:
    """RMS radial residual of ``points`` against a ``(cx, cy, r)`` circle."""
    pts = np.asarray(points, dtype=np.float64)
    cx, cy, r = circle
    dist = np.sqrt((pts[:, 0] - cx) ** 2 + (pts[:, 1] - cy) ** 2)
    return float(np.sqrt(np.mean((dist - r) ** 2)))


def min_anchor_span_px(anchors: list[dict]) -> float:
    """Minimum span_px among anchors (or 0.0 for an empty list)."""
    if not anchors:
        return 0.0
    return float(min(a["span_px"] for a in anchors))


def fit_scale(anchors: list[dict]) -> dict:
    """Multi-anchor scale fit, frozen AT-15 semantics, n >= MIN_SCALE_ANCHORS.

    Each anchor contributes ``m_per_px = real_length_m / span_px``. The fit
    returns the median ``m_per_px``, the median-residual (max relative
    deviation from the median) and the disagreement (max pairwise relative
    spread).

    Requires at least ``MIN_SCALE_ANCHORS`` (3) admissible anchors. With only
    two anchors the median residual and the pairwise disagreement collapse to
    the same quantity (``disagreement == 2 * median_residual``), so a single
    wrong anchor can never be detected -- a two-anchor "agreement" is not
    evidence of agreement at all (U-2). Fewer than ``MIN_SCALE_ANCHORS``
    admissible anchors yields a null fit (residual/disagreement inf) so the
    caller fails closed.
    """
    mpp = [float(a["real_length_m"]) / float(a["span_px"]) for a in anchors if float(a["span_px"]) > 0]
    if len(mpp) < MIN_SCALE_ANCHORS:
        return {"m_per_px": None, "median_residual": float("inf"), "disagreement": float("inf"), "count": len(mpp)}
    median = float(np.median(mpp))
    residuals = [abs(v - median) / median for v in mpp]
    disagreement = 0.0
    for i in range(len(mpp)):
        for j in range(i + 1, len(mpp)):
            disagreement = max(disagreement, abs(mpp[i] - mpp[j]) / median)
    return {
        "m_per_px": median,
        "median_residual": float(max(residuals)),
        "disagreement": float(disagreement),
        "count": len(mpp),
    }


def clutter_within_band(suppressed_ink: float, total_ink: float, cap: float = MAX_SUPPRESSED_INK_FRACTION) -> bool:
    """Suppressed-ink fraction is within the declared band (anti-hallucination)."""
    if total_ink <= 0:
        return True
    return (suppressed_ink / total_ink) <= cap


def unexplained_ink_within_band(unexplained: float, total_ink: float, cap: float = MAX_UNEXPLAINED_INK_FRACTION) -> bool:
    """Unexplained-ink fraction is within the declared band."""
    if total_ink <= 0:
        return True
    return (unexplained / total_ink) <= cap


def within_pixel_budget(pixels: int, cap: int = 100_000_000) -> bool:
    """True iff a declared pixel count is within the decode cap."""
    return int(pixels) <= int(cap)


# --- Collinear run extraction (wall centreline recovery) ---------------------


def collinear_runs(mask: np.ndarray, theta_deg: float, rho: float, tol_px: float = 2.0) -> list[tuple[float, float]]:
    """Return [(t0, t1), ...] contiguous ink runs along a (theta, rho) line.

    Projects every ink pixel onto the line direction; sorts by the along-line
    coordinate ``t``; emits maximal contiguous runs of pixels whose
    perpendicular distance to the line is within ``tol_px`` and whose along-line
    neighbours are within a small merge tolerance. Runs are sorted ascending.
    """
    mask = np.asarray(mask, dtype=bool)
    ys, xs = np.nonzero(mask)
    if xs.size == 0:
        return []
    theta = math.radians(theta_deg)
    n = np.array([math.cos(theta), math.sin(theta)])      # line normal (unit)
    d = np.array([-math.sin(theta), math.cos(theta)])     # line direction (unit)
    pts = np.stack([xs.astype(np.float64), ys.astype(np.float64)], axis=1)
    perp = pts @ n - rho
    along = pts @ d
    keep = np.abs(perp) <= tol_px
    if not keep.any():
        return []
    t = np.sort(along[keep])
    # Merge along-line points closer than the wall stroke width (they are the
    # same stroke); a gap above the wall-stroke threshold is a real break
    # (opening or wall end) and stays split.
    gap = 2.0 * (WALL_STROKE_PX + 1)
    runs: list[tuple[float, float]] = []
    start = t[0]
    prev = t[0]
    for v in t[1:]:
        if v - prev > gap:
            runs.append((float(start), float(prev)))
            start = v
        prev = v
    runs.append((float(start), float(prev)))
    return runs


def merge_collinear_segments(runs: list[tuple[float, float]], max_gap_px: float = WALL_OPENING_GAP_PX) -> list[tuple[float, float]]:
    """Merge along-line runs separated by a gap <= ``max_gap_px`` into one wall.

    A gap up to the frozen opening span (passage <= 3.0 m) is an *opening*, so
    the runs on either side belong to the same wall. A larger gap is a genuine
    wall boundary (U-4 pending default) and stays split. Returns merged
    ``(t0, t1)`` intervals, ascending, still split at real boundaries.
    """
    runs = sorted(runs)
    if not runs:
        return []
    merged: list[tuple[float, float]] = []
    cur_start, cur_end = runs[0]
    for start, end in runs[1:]:
        if start - cur_end <= max_gap_px:
            cur_end = max(cur_end, end)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = start, end
    merged.append((cur_start, cur_end))
    return merged


def line_from_theta_rho(theta_deg: float, rho: float, t: float) -> tuple[float, float]:
    """Point on the (theta, rho) line at along-line coordinate ``t``."""
    theta = math.radians(theta_deg)
    n = np.array([math.cos(theta), math.sin(theta)])
    d = np.array([-math.sin(theta), math.cos(theta)])
    p = n * rho + d * t
    return (float(p[0]), float(p[1]))
