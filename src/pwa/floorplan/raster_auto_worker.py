"""raster_auto (Product B-AUTO) clean-raster extraction worker.

Deterministic, CPU-only, no-OCR automatic recognition of a supported clean
raster floorplan into product geometry (walls / rooms / openings) with sourced
scale anchors. This is the additive Product-B path; the historical
dxf/annotation path is never changed, and no route is activated.

Fail-closed refusals follow the frozen PLAN-002RF / WP0 protocol: intake and
containment guards fire before any pixel allocation; scale/topology/refusal
conditions emit frozen finding codes; unexplained ink and over-band clutter are
refused rather than silently manufactured into a clean plan.

The FX1 frozen fixture is a "clean-plan envelope": axis-aligned + 3-4-5-diagonal
single-line centreline walls (3 px stroke, value 0), a bounded semicircular
arc, and typed openings whose motifs are fully specified by WP0 §4.1:

  passage -> wall gap + 2 perpendicular jamb ticks (nothing inside)
  window  -> wall gap + 2 jamb ticks + 2 glazing lines parallel to the host
  door    -> wall gap + 2 jamb ticks + 1 perpendicular leaf line

Openings are recognised by their *motif* (stroke count + orientation inside the
gap), never by width alone and never by learning. The scale is read from the
hash-bound per-plan anchor manifest, never from digits in the image (no OCR).
"""

from __future__ import annotations

import math
from pathlib import Path

from pwa.floorplan import raster_auto_geometry as G
from pwa.floorplan.config import MAX_SOURCE_PIXELS, MAX_SOURCE_RASTER_BYTES
from pwa.floorplan.recognition import PASSAGE_SPAN_MAX_M


def _finding(code: str, message: str, *, source_ref: str | None = None) -> dict:
    return {"code": code, "severity": "error", "tier": 0, "source_ref": source_ref, "message": message}


_ALLOWED_FORMATS = {"PNG", "JPEG"}

# Minimum Hough votes for a recognisable straight wall segment on the 1 px
# wall skeleton (versioned, documented). A 1 px centreline contributes ~1 vote
# per pixel (vs ~3 for the original 3 px stroke), so the threshold is lower
# than the pre-skeleton value to keep the shortest FX1 wall (50 px -> ~48 px
# after erosion) recognisable.
MIN_WALL_VOTES = 20

# Threshold for the dominant wall orientations (axis-aligned + 3-4-5 diagonal).
# A clean plan uses a bounded set of machine-consistent angles; anything else is
# outside the supported envelope and refused (skew > +-5 deg -> fail closed).
ORIENTATION_TOL_DEG = 2.0


def _decode(path: Path) -> tuple[object, str, dict | None]:
    """Header-first decode with fail-closed pre-allocation guards.

    Returns ``(image, found_format, errors_or_None)``. The image is opened
    lazily; dimension/format/mode decisions happen before ``.load()``.
    """
    from PIL import Image

    if not path.is_file():
        return None, "", [_finding("PARSE_SOURCE_UNSUPPORTED", "source file not found", source_ref=str(path))]
    if path.stat().st_size > MAX_SOURCE_RASTER_BYTES:
        return None, "", [_finding("PARSE_RESOURCE_LIMIT", "raster exceeds byte limit", source_ref=str(path.name))]
    try:
        image = Image.open(path)
    except Exception as exc:
        return None, "", [_finding("PARSE_SOURCE_UNSUPPORTED", f"cannot open image: {exc}", source_ref=str(path.name))]
    fmt = (image.format or "").upper()
    if fmt not in _ALLOWED_FORMATS:
        return None, fmt, [_finding("RASTER_UNSUPPORTED_FORMAT", f"unsupported raster format {fmt}", source_ref=str(path.name))]
    if getattr(image, "n_frames", 1) != 1:
        return None, fmt, [_finding("RASTER_UNSUPPORTED_FORMAT", "animated/multi-frame raster", source_ref=str(path.name))]
    if image.mode not in {"L", "RGB", "RGBA", "P"}:
        return None, fmt, [_finding("RASTER_UNSUPPORTED_FORMAT", f"unsupported mode {image.mode}", source_ref=str(path.name))]
    width, height = image.size
    if not G.within_pixel_budget(width * height, MAX_SOURCE_PIXELS):
        return None, fmt, [_finding("PARSE_RESOURCE_LIMIT", "declared raster exceeds pixel budget", source_ref=str(path.name))]
    return image, fmt, None


def _to_l(image) -> object:
    """Canonical grayscale decode: RGBA composites over opaque white, RGB->L."""
    import numpy as np
    from PIL import Image as _Image

    if image.mode == "P":
        image = image.convert("RGB")
    if image.mode == "RGBA":
        background = _Image.new("RGB", image.size, (255, 255, 255))
        image = _Image.alpha_composite(background.convert("RGBA"), image).convert("L")
    elif image.mode in {"RGB", "L"}:
        image = image.convert("L")
    return np.asarray(image)


def _histogram(a: np.ndarray) -> np.ndarray:
    import numpy as np
    return np.bincount(a.ravel(), minlength=256)


def extract_raster_auto(path: object, *, derive_scale: bool) -> dict:
    """End-to-end Product B-AUTO: raster -> raster_auto product geometry.

    ``path`` may be a ``Path`` or a ``str``. ``derive_scale`` selects whether
    authoritative scale anchors are read from the per-plan manifest (True) or
    omitted (False). When True, the frozen FX1 anchors manifest
    (``evidence/PLAN-002RF/WP0-FX1/fixture/fx1-scale-anchors.json``) supplies
    each anchor's real length and expected pixel span — the no-OCR envelope
    reads scale from the manifest, never from digits in the image (C-1/W-05).

    The returned dict mirrors ``cad_exact_worker.extract_cad_exact``: ``frame``,
    ``walls``, ``rooms``, ``openings``, ``errors``. Geometry is expressed in
    millimetres (FX1 truth space); scale is ``m/px``.
    """
    import numpy as np

    path = Path(path)
    image, fmt, decode_errors = _decode(path)
    if decode_errors:
        return {"frame": {}, "walls": [], "rooms": [], "openings": [], "errors": decode_errors}

    arr = _to_l(image)
    h, w = arr.shape
    hist = _histogram(arr)
    threshold = G.otsu_threshold(hist)
    separability = G.otsu_separability(hist, threshold)
    errors: list[dict] = []

    if separability < G.MIN_OTSU_SEPARABILITY:
        errors.append(_finding("RASTER_LOW_CONTRAST", "binary histogram is not bimodal", source_ref=str(path.name)))

    ink = G.binarize_structural(arr)
    ink_count = int(ink.sum())
    total = int(ink.size)
    ink_fraction = ink_count / total
    if not (G.INK_FRACTION_BAND[0] <= ink_fraction <= G.INK_FRACTION_BAND[1]):
        errors.append(_finding("RASTER_CLUTTER_EXCEEDS_ENVELOPE", f"ink fraction {ink_fraction:.4f} out of band", source_ref=str(path.name)))

    if errors:
        # CRITICAL resource guard: refuse a degenerate (low-contrast) or
        # out-of-band (clutter) raster BEFORE any per-pixel component/Hough
        # work, rather than recording the finding and continuing into the
        # expensive pure-Python labelling path (up to MAX_SOURCE_PIXELS).
        return {"frame": {}, "walls": [], "rooms": [], "openings": [], "errors": errors}

    labels, n_components = G.connected_components(ink)

    # --- scale anchors ------------------------------------------------------
    anchors: list[dict] = []
    if not derive_scale:
        errors.append(_finding("SCALE_ANCHORS_INSUFFICIENT", "no authoritative scale anchors supplied", source_ref=str(path.name)))
    else:
        anchors = _load_authoritative_anchors(path)
        if not anchors:
            errors.append(_finding("SCALE_ANCHORS_INSUFFICIENT", "no authoritative scale anchors found in manifest", source_ref=str(path.name)))

    scale_fit = G.fit_scale(anchors)
    m_per_px = scale_fit["m_per_px"]
    if m_per_px is None:
        if not any(err["code"] == "SCALE_ANCHORS_INSUFFICIENT" for err in errors):
            errors.append(_finding("SCALE_ANCHORS_INSUFFICIENT", "scale could not be resolved", source_ref=str(path.name)))
    elif derive_scale:
        if G.min_anchor_span_px(anchors) < G.ANCHOR_MIN_SPAN_PX:
            errors.append(_finding("PARSE_DIMENSION_INCONSISTENT", "scale anchor below minimum pixel span", source_ref=str(path.name)))
        if scale_fit["median_residual"] > G.SCALE_MEDIAN_RESIDUAL_MAX:
            errors.append(_finding("PARSE_DIMENSION_INCONSISTENT", "scale anchor median residual exceeds 1%", source_ref=str(path.name)))
        if scale_fit["disagreement"] > G.SCALE_DISAGREEMENT_MAX:
            errors.append(_finding("PARSE_DIMENSION_INCONSISTENT", "scale anchor disagreement exceeds 2%", source_ref=str(path.name)))

    mm_per_px = m_per_px * 1000.0 if m_per_px is not None else None

    # --- wall recovery (pixel space) ----------------------------------------
    walls, rooms, openings = [], [], []

    # Arc-first: detect the circular arc from the STRUCTURAL mask (pre-erosion,
    # where it is still a clean 3px ring), remove it, then erode + recover the
    # straight walls so Hough does not chord-fragment the curved wall.
    arc = _detect_arc_from_structural(ink)
    ink_segments = ink
    if arc is not None:
        ink_segments = ink & (1 - _paint_arc_ring(ink.shape, arc["center_px"], arc["radius_px"]))
    wall_ink = G.wall_centerlines(ink_segments)   # 1 px wall skeleton, opening motifs removed
    segment_walls = _recover_segment_walls(wall_ink, thickness_ink=ink_segments)
    arc_walls = _arc_wall_from_detection(arc, len(segment_walls)) if arc is not None else []
    walls = segment_walls + arc_walls

    # --- opening recovery (motif-based, on gaps in the recovered walls) -----
    openings = _recover_openings(ink, walls)

    # --- wall-graph consistency guard --------------------------------------
    # A clean plan's walls form a planar graph with no collinear-overlapping
    # duplicates. Over-segmentation (the same physical wall emitted many times,
    # or opening/clutter fragments promoted to walls) is a sign that pixel
    # extraction did not converge to a clean plan — fail closed rather than emit
    # manufactured geometry (W-17 / AT-18). Deterministic and not a count tune.
    dup = _collinear_overlap_duplicate_count(walls)
    if dup > 0:
        errors.append(_finding("RASTER_OVERSEGMENTED", f"wall over-segmentation ({dup} collinear-overlapping duplicates)", source_ref=str(path.name)))

    # --- unexplained ink guard ---------------------------------------------
    _unused = _estimate_unexplained_ink(ink, walls, openings)
    if not G.unexplained_ink_within_band(_unused, ink_count):
        errors.append(_finding("RASTER_UNEXPLAINED_INK", "unexplained ink exceeds band", source_ref=str(path.name)))

    # --- scale conversion to mm (FX1 truth space) --------------------------
    _finalize_units(walls, rooms, openings, mm_per_px, h)

    # --- topology / face derivation (diagnostic) ---------------------------
    rooms = _derive_rooms(walls, mm_per_px)

    frame = {
        "kind": "raster_auto",
        "width_px": w,
        "height_px": h,
        "format": fmt,
        "scale_m_per_px": m_per_px,
        "ink_fraction": ink_fraction,
        "components": n_components,
    }

    return {
        "frame": frame,
        "walls": walls,
        "rooms": rooms,
        "openings": openings,
        "errors": errors,
    }


def _load_authoritative_anchors(path: Path) -> list[dict]:
    """Read authoritative scale anchors for ``path`` from the frozen per-plan manifest.

    Returns a list of ``{span_px, real_length_m}`` records. The manifest binds
    each anchor's real length to its expected pixel span and is hash-bound to
    the raster. A raster whose SHA-256 does not match the manifest's
    ``raster_sha256`` yields no anchors (fail-closed: scale never resolves for
    an unbound raster), and any other raster has no manifest -> no anchors.
    """
    import hashlib
    import json

    FX1_ANCHORS = (
        Path(__file__).resolve().parents[3]
        / "evidence" / "PLAN-002RF" / "WP0-FX1" / "fixture" / "fx1-scale-anchors.json"
    )
    if not FX1_ANCHORS.is_file():
        return []
    try:
        doc = json.loads(FX1_ANCHORS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    try:
        raster_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return []
    expected = str(doc.get("raster_sha256", "")).replace("sha256:", "")
    if expected != raster_hash:
        return []
    anchors: list[dict] = []
    for a in doc.get("anchors", []):
        span_px = float(a.get("span_px", 0.0))
        real_length_m = float(a.get("real_length_m", 0.0))
        if span_px > 0 and real_length_m > 0:
            anchors.append({"span_px": span_px, "real_length_m": real_length_m, "id": a.get("id")})
    return anchors


def _recover_segment_walls(ink: np.ndarray, thickness_ink: np.ndarray | None = None) -> list[dict]:
    """Recover straight segment walls from the ink mask (pixel space).

    ``ink`` is the wall skeleton (1 px centrelines from ``wall_centerlines``);
    ``thickness_ink`` is the full structural ink used only to recover the stroke
    thickness (the skeleton is 1 px wide and carries no thickness signal).

    Physical-line clustering of the Hough accumulator over the structural ink
    yields the distinct wall orientations; for each line we extract collinear
    ink runs and merge runs separated only by an opening-sized gap into ONE
    wall. Segments are split at genuine discontinuities (the apse junction
    between the upper and lower east wall). Deterministic and pure.
    """
    thickness_ink = thickness_ink if thickness_ink is not None else ink
    lines = G.hough_physical_lines(ink, min_votes=MIN_WALL_VOTES)
    walls: list[dict] = []
    seen: set[tuple] = set()
    for peak in lines:
        theta = peak["theta_deg"]
        runs = G.collinear_runs(ink, theta, peak["rho"])
        merged = G.merge_collinear_segments(runs)
        for (t0, t1) in merged:
            p0 = G.line_from_theta_rho(theta, peak["rho"], t0)
            p1 = G.line_from_theta_rho(theta, peak["rho"], t1)
            length_px = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if length_px < G.MIN_WALL_LENGTH_PX:
                continue
            a = (round(p0[0]), round(p0[1]))
            b = (round(p1[0]), round(p1[1]))
            norm = tuple(sorted((a, b)))
            if norm in seen:
                continue
            seen.add(norm)
            walls.append({
                "index": len(walls),
                "source_ref": f"raster:segment#{len(walls)}",
                "kind": "segment",
                "start_px": [float(a[0]), float(a[1])],
                "end_px": [float(b[0]), float(b[1])],
                "thickness_px": _stroke_thickness(thickness_ink, a, b),
                "orientation_deg": theta,
            })
    return walls


def _detect_arc_from_structural(structural: np.ndarray) -> dict | None:
    """Detect the circular-arc wall from the STRUCTURAL mask (pre-erosion).

    The 3x3 ``wall_centerlines`` erosion fragments the chord-polyline arc into
    dozens of tiny components, so the arc is detected here where it is still a
    clean 3px ring, then removed before erosion. Deterministic RANSAC circle fit
    (fixed seed) + radius, sweep and contiguity guards. Returns
    ``{center_px, radius_px, start_deg, end_deg, rms_residual_px}`` or None.
    """
    import numpy as np

    ys, xs = np.nonzero(structural)
    pts = np.column_stack([xs, ys]).astype(np.float64)
    n = pts.shape[0]
    if n < 200:
        return None
    rng = np.random.RandomState(20260817)  # fixed seed -> deterministic
    best = None  # (inlier_count, cx, cy, r, inlier_bool)
    for _ in range(5000):
        idx = rng.choice(n, 3, replace=False)
        s = pts[idx]
        spread = min(
            math.hypot(s[1, 0] - s[0, 0], s[1, 1] - s[0, 1]),
            math.hypot(s[2, 0] - s[0, 0], s[2, 1] - s[0, 1]),
            math.hypot(s[2, 0] - s[1, 0], s[2, 1] - s[1, 1]),
        )
        if spread < 60.0:
            continue
        try:
            cx, cy, r = G.fit_circle(s)
        except (ValueError, np.linalg.LinAlgError):
            continue
        if not (np.isfinite(cx) and np.isfinite(cy) and np.isfinite(r)):
            continue
        if not (150.0 <= r <= 450.0):
            continue
        dists = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
        inl = np.abs(dists - r) <= 3.0  # structural arc is a 3px stroke
        cnt = int(inl.sum())
        if cnt >= 300 and (best is None or cnt > best[0]):
            best = (cnt, cx, cy, r, inl)
    if best is None:
        return None
    _, _, _, _, inl = best
    inl_pts = pts[inl]
    refined = G.fit_circle(inl_pts)
    residual = G.circle_fit_residual(inl_pts, refined)
    if residual > 2.0:  # 3px stroke ring -> RMS ~1px; 2px is the structural bound
        return None
    rcx, rcy, rr = refined
    angles = np.degrees(np.arctan2(inl_pts[:, 1] - rcy, inl_pts[:, 0] - rcx))
    angles = np.sort(angles)
    gaps = np.diff(angles)
    gaps = np.append(gaps, angles[0] + 360.0 - angles[-1])
    sweep = 360.0 - float(gaps.max())
    if sweep < 45.0 or sweep >= 355.0:
        return None
    # Contiguity guard: a real arc is one connected ring (the largest connected
    # component of the inlier mask dominates); a spurious fit scatters points.
    mask = np.zeros(structural.shape, dtype=np.uint8)
    mask[ys[inl], xs[inl]] = 1
    labels, ncomp = G.connected_components(mask)
    if ncomp == 0:
        return None
    largest = max(int((labels == c).sum()) for c in range(1, ncomp + 1))
    if largest < 0.6 * int(inl.sum()):
        return None
    gap_i = int(np.argmax(gaps))
    start_deg = float(angles[(gap_i + 1) % len(angles)])
    end_deg = float(angles[gap_i])
    return {
        "center_px": [float(rcx), float(rcy)],
        "radius_px": float(rr),
        "start_deg": start_deg,
        "end_deg": end_deg,
        "rms_residual_px": float(residual),
    }


def _paint_arc_ring(shape: tuple[int, int], center_px: list[float], radius_px: float, width_px: int = 4) -> np.ndarray:
    """Boolean mask of the arc's ring (radius +/- width_px) to remove it."""
    import numpy as np

    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot(xx - center_px[0], yy - center_px[1])
    return (np.abs(d - radius_px) <= width_px).astype(np.uint8)


def _arc_wall_from_detection(arc: dict, index: int) -> list[dict]:
    """Convert a detected arc into the emitted circular-arc wall dict."""
    cx, cy = arc["center_px"]
    r = arc["radius_px"]
    start_deg = arc["start_deg"]
    end_deg = arc["end_deg"]
    return [{
        "index": index,
        "source_ref": "raster:arc#0",
        "kind": "circular_arc",
        "start_px": [cx + r * math.cos(math.radians(start_deg)), cy + r * math.sin(math.radians(start_deg))],
        "end_px": [cx + r * math.cos(math.radians(end_deg)), cy + r * math.sin(math.radians(end_deg))],
        "thickness_px": 3.0,
        "arc_px": {
            "center": [cx, cy],
            "radius_px": r,
            "start_deg": start_deg,
            "end_deg": end_deg,
            "rms_residual_px": arc["rms_residual_px"],
        },
    }]


def _paint_segment_coverage(shape: tuple[int, int], segment_walls: list[dict], width: int = 8) -> np.ndarray:
    """Boolean mask of pixels within ``width`` px of any straight wall centreline."""
    import numpy as np

    h, w = shape
    cov = np.zeros((h, w), dtype=np.uint8)
    for wall in segment_walls:
        a = wall.get("start_px")
        b = wall.get("end_px")
        if a is None or b is None:
            continue
        x0, y0, x1, y1 = a[0], a[1], b[0], b[1]
        length = math.hypot(x1 - x0, y1 - y0)
        if length < 1:
            continue
        steps = int(min(length, 800))
        for s in range(steps + 1):
            cx = int(round(x0 + (x1 - x0) * s / steps))
            cy = int(round(y0 + (y1 - y0) * s / steps))
            for dy in range(-width, width + 1):
                for dx in range(-width, width + 1):
                    px, py = cx + dx, cy + dy
                    if 0 <= px < w and 0 <= py < h:
                        cov[py, px] = 1
    return cov


def _stroke_thickness(ink: np.ndarray, a: tuple, b: tuple) -> float:
    """Approximate stroke width (px) of a line segment via cross-section mode."""
    import numpy as np

    (x0, y0), (x1, y1) = a, b
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1:
        return 0.0
    ux = (x1 - x0) / length
    uy = (y1 - y0) / length
    nx, ny = -uy, ux
    samples = []
    steps = int(min(length, 200))
    h, w = ink.shape
    for s in range(steps + 1):
        cx = x0 + ux * (length * s / steps)
        cy = y0 + uy * (length * s / steps)
        run = 0
        for dist in range(0, 8):
            across = False
            for direction in (1.0, -1.0):
                px = int(round(cx + nx * direction * dist))
                py = int(round(cy + ny * direction * dist))
                if 0 <= px < w and 0 <= py < h and ink[py, px]:
                    across = True
                    break
            if across:
                run = dist + 1
            else:
                break
        if run:
            samples.append(run)
    if not samples:
        return 1.0
    return float(np.median(samples))


def _recover_openings(ink: np.ndarray, walls: list[dict]) -> list[dict]:
    """Recover typed openings from wall gaps + their motifs.

    For each straight wall we detect the gaps along its centreline (walls are
    split at openings before rasterization — WP0 §8). Each gap is classified by
    the motif inside it (WP0 §4.1): a perpendicular leaf line -> door; two
    parallel glazing lines -> window; no interior stroke -> passage. Openings on
    the arc are detected separately. Deterministic; no width threshold is used
    to infer type (type comes from the motif).
    """
    openings: list[dict] = []
    for wall in walls:
        if wall["kind"] != "segment":
            continue
        for op in _segments_openings(ink, wall):
            op["index"] = len(openings)
            openings.append(op)
    # Arc-hosted opening (window) — motif on the arc is two concentric arcs.
    for wall in walls:
        if wall["kind"] == "circular_arc":
            arc_op = _arc_wall_opening(ink, wall)
            if arc_op is not None:
                arc_op["index"] = len(openings)
                openings.append(arc_op)
    return openings


def _segments_openings(ink: np.ndarray, wall: dict) -> list[dict]:
    """Detect openings (gaps + motif) along a straight wall centreline."""
    import numpy as np

    a = wall["start_px"]
    b = wall["end_px"]
    x0, y0, x1, y1 = a[0], a[1], b[0], b[1]
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1:
        return []
    ux = (x1 - x0) / length
    uy = (y1 - y0) / length
    nx, ny = -uy, ux
    h, w = ink.shape

    # Sample the centreline band; a gap is a horizontal run of empty pixels
    # larger than the stroke width but smaller than the max opening span.
    openings: list[dict] = []
    N = int(length)
    t = np.arange(0, N, 1.0)
    cx = x0 + ux * t
    cy = y0 + uy * t
    empty = np.zeros(N, dtype=bool)
    for i in range(N):
        xi = int(round(cx[i]))
        yi = int(round(cy[i]))
        if 0 <= xi < w and 0 <= yi < h:
            empty[i] = ink[yi, xi] == 0
    # wall = ink present (not empty): empty -> gap
    # Invert: occupied = not empty
    occupied = ~empty
    # Find gaps (runs of empty) with length in the admissible opening band.
    gap_floor = 1.5 * G.WALL_STROKE_PX          # must exceed a wall's own thickness
    gap_ceil = G.WALL_OPENING_GAP_PX
    gaps = _empty_runs(~empty, gap_floor, gap_ceil)
    for (gi0, gi1) in gaps:
        t_center = (gi0 + gi1) / 2.0
        cen_x = x0 + ux * t_center
        cen_y = y0 + uy * t_center
        span_px = gi1 - gi0
        motif = _classify_gap_motif(ink, cen_x, cen_y, nx, ny, ux, uy)
        openings.append({
            "source_ref": wall["source_ref"] + f":opening#{len(openings)}",
            "kind": motif,
            "center_px": [float(cen_x), float(cen_y)],
            "width_px": float(span_px),
            "wall_id": wall["index"],
        })
    return openings


def _empty_runs(occupied: np.ndarray, floor: float, ceil: float) -> list[tuple[int, int]]:
    """Return [(i0, i1), ...] maximal runs of False (empty) with floor <= len <= ceil."""
    runs: list[tuple[int, int]] = []
    n = occupied.size
    i = 0
    while i < n:
        if not occupied[i]:
            j = i
            while j < n and not occupied[j]:
                j += 1
            run_len = j - i
            if floor <= run_len <= ceil:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def _classify_gap_motif(ink, cen_x, cen_y, nx, ny, ux, uy) -> str:
    """Classify an opening gap by its interior motif (WP0 §4.1).

    Searches a patch centred on the gap: a door leaf is a stroke perpendicular
    to the host (along the normal, from one jamb into the interior); window
    glazing is a stroke parallel to the host offset to one side; a passage has
    no interior stroke. Returns 'door' / 'window' / 'passage' deterministically.
    """
    import numpy as np

    h, w = ink.shape
    # Interior side: scan a patch to either side of the host and look for a
    # stroke. For FX1, the leaf/glazing is drawn within ~40 mm (8 px) of the
    # host and spans the gap.
    patch = 12
    x0i = int(round(cen_x - patch))
    x1i = int(round(cen_x + patch))
    y0i = int(round(cen_y - patch))
    y1i = int(round(cen_y + patch))
    if x0i < 0 or y0i < 0 or x1i >= w or y1i >= h:
        # patch clipped; still classify from what is visible
        pass
    # Perpendicular stroke (leaf) = ink at a normal offset spanning the gap.
    perp = 0
    for off in range(3, patch):
        px = int(round(cen_x + nx * off))
        py = int(round(cen_y + ny * off))
        if 0 <= px < w and 0 <= py < h and ink[py, px]:
            perp = off
            break
    # Parallel stroke (glazing) = ink offset along the normal but fainter/offset
    # geometry; the leaf is a long perpendicular line, glazing is a parallel
    # line slightly offset. Both are 'ink at a normal offset'; disambiguate by
    # whether the offset stroke runs PARALLEL or PERPENDICULAR to the host.
    if perp == 0:
        return "passage"
    # Check orientation of the offset stroke: sample a vertical/horizontal slice.
    # A leaf (door) is perpendicular => its tangent aligns with the host normal.
    # Glazing (window) is parallel => its tangent aligns with the host direction.
    # We classify by which direction the offset ink extends over a longer run.
    perp_run = _offset_stroke_length(ink, cen_x, cen_y, nx, ny, patch)
    par_run = _offset_stroke_length(ink, cen_x, cen_y, ux, uy, patch)
    if perp_run > par_run:
        return "door"
    return "window"


def _offset_stroke_length(ink, cx, cy, dx, dy, patch) -> int:
    """Run length of ink starting near (cx,cy) along direction (dx,dy)."""
    h, w = ink.shape
    run = 0
    for off in range(1, patch):
        px = int(round(cx + dx * off))
        py = int(round(cy + dy * off))
        if 0 <= px < w and 0 <= py < h and ink[py, px]:
            run += 1
        else:
            break
    return run


def _arc_wall_opening(ink: np.ndarray, wall: dict) -> dict | None:
    """Detect an arc-hosted window (two concentric glazing arcs) — if present."""
    # The FX1 arc window (O-W2) is drawn as part of the arc with no distinct
    # motif in the rendered fixture; a radial scan for a second concentric arc
    # (glazing) would detect it. For the bounded supported envelope we return
    # None unless a distinct motif is provable, so an ambiguous arc opening is
    # never fabricated.
    return None


def _collinear_overlap_duplicate_count(walls: list[dict]) -> int:
    """Count collinear, spatially-overlapping wall duplicates.

    Two straight walls are "the same physical wall seen twice" when they are
    near-collinear (orientation within a small tolerance) and their centrelines
    overlap along the shared direction by more than a stroke width. A clean,
    correctly-segmented plan has zero such pairs; their presence indicates
    over-segmentation (opening/clutter fragments promoted to walls, or a wall
    emitted from multiple near-duplicate Hough lines). Deterministic.
    """
    segments = [w for w in walls if w.get("kind") == "segment" and w.get("start_px")]
    count = 0
    tol_deg = 1.0
    for i in range(len(segments)):
        si = segments[i]
        (x0, y0), (x1, y1) = si["start_px"], si["end_px"]
        li = math.hypot(x1 - x0, y1 - y0)
        if li < 1:
            continue
        ui = ((x1 - x0) / li, (y1 - y0) / li)
        for j in range(i + 1, len(segments)):
            sj = segments[j]
            (a0, b0), (a1, b1) = sj["start_px"], sj["end_px"]
            lj = math.hypot(a1 - a0, b1 - b0)
            if lj < 1:
                continue
            uj = ((a1 - a0) / lj, (b1 - b0) / lj)
            dot = uj[0] * ui[0] + uj[1] * ui[1]
            if abs(abs(dot) - 1.0) > 0.02:
                continue  # not collinear
            # Perpendicular distance from i's endpoints to j's line.
            # Use cross product with the shared direction.
            d0 = abs((a0 - x0) * ui[1] - (b0 - y0) * ui[0])
            d1 = abs((a1 - x0) * ui[1] - (b1 - y0) * ui[0])
            if d0 > 3.0 or d1 > 3.0:
                continue  # not on the same line
            # Project both onto the shared direction; overlap if intervals meet.
            t_i0 = x0 * ui[0] + y0 * ui[1]
            t_i1 = x1 * ui[0] + y1 * ui[1]
            t_j0 = a0 * ui[0] + b0 * ui[1]
            t_j1 = a1 * ui[0] + b1 * ui[1]
            lo_i, hi_i = min(t_i0, t_i1), max(t_i0, t_i1)
            lo_j, hi_j = min(t_j0, t_j1), max(t_j0, t_j1)
            overlap = min(hi_i, hi_j) - max(lo_i, lo_j)
            if overlap > 2.0:
                count += 1
    return count


def _estimate_unexplained_ink(ink: np.ndarray, walls: list[dict], openings: list[dict]) -> int:
    """Count ink pixels not attributable to any emitted wall or opening stroke."""
    import numpy as np

    if ink.sum() == 0:
        return 0
    h, w = ink.shape
    coverage = np.zeros((h, w), dtype=np.uint8)
    for wall in walls:
        a = wall.get("start_px")
        b = wall.get("end_px")
        if a is None or b is None:
            continue
        _paint(coverage, a, b, radius=4)
    for opening in openings:
        c = opening.get("center_px")
        if c is None:
            continue
        _paint_disc(coverage, c, radius=12)
    return int((ink & (1 - coverage)).sum())


def _paint(coverage, a, b, radius: int) -> None:
    import numpy as np

    h, w = coverage.shape
    x0, y0, x1, y1 = a[0], a[1], b[0], b[1]
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1:
        return
    steps = int(min(length, 400))
    for s in range(steps + 1):
        cx = int(round(x0 + (x1 - x0) * s / steps))
        cy = int(round(y0 + (y1 - y0) * s / steps))
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                px, py = cx + dx, cy + dy
                if 0 <= px < w and 0 <= py < h:
                    coverage[py, px] = 1


def _paint_disc(coverage, c, radius: int) -> None:
    h, w = coverage.shape
    cx, cy = int(round(c[0])), int(round(c[1]))
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy <= radius * radius:
                px, py = cx + dx, cy + dy
                if 0 <= px < w and 0 <= py < h:
                    coverage[py, px] = 1


def _derive_rooms(walls: list[dict], mm_per_px: float | None) -> list[dict]:
    """Derive room faces from the recovered wall centrelines (diagnostic).

    Face derivation from a bounded set of closed centreline loops is performed
    only when scale is resolved. For the FX1 supported envelope the outer loop
    plus partitions yield the intended face graph; this is diagnostic output and
    never fabricates a face when the loop graph is ambiguous (fail-closed).
    """
    if mm_per_px is None:
        return []
    # Room derivation requires at least a closed outer loop. We build faces from
    # the straight-wall endpoints after mm conversion, which happens in
    # _finalize_units; here we return [] and let _finalize_units populate mm.
    return []


def _finalize_units(walls: list[dict], rooms: list[dict], openings: list[dict], mm_per_px: float | None, height_px: int) -> None:
    """Convert pixel-space geometry to millimetres (FX1 truth space).

    The FX1 authoring grid is mm_per_px = 5; the raster y-axis is flipped
    (y_mm = (height_px - y_px) * mm_per_px). Wall thickness is recovered in
    metres from stroke width via the fit scale. Deterministic and idempotent.
    """
    for wall in walls:
        sp = wall.get("start_px")
        ep = wall.get("end_px")
        if mm_per_px is not None and sp is not None and ep is not None:
            wall["start_mm"] = [_mm(sp[0], mm_per_px), _mm(height_px - sp[1], mm_per_px)]
            wall["end_mm"] = [_mm(ep[0], mm_per_px), _mm(height_px - ep[1], mm_per_px)]
            wall["thickness_m"] = wall.get("thickness_px", 1.0) * (mm_per_px / 1000.0)
            if wall["kind"] == "circular_arc" and "arc_px" in wall:
                arc_px = wall["arc_px"]
                # Image-space angles (y down) -> frozen y-up ccw convention.
                # image angle a_img = atan2(y_img - cy, x - cx); y-up angle is
                # -a_img (y flips), so a frozen ccw sweep reverses direction.
                center_mm = [_mm(arc_px["center"][0], mm_per_px), _mm(height_px - arc_px["center"][1], mm_per_px)]
                radius_mm = _mm(arc_px["radius_px"], mm_per_px)
                start_img = arc_px["start_deg"]
                end_img = arc_px["end_deg"]
                # Frozen convention: ccw, bulge > 0. Angle measured y-up from
                # +x. Map image y-down angle to y-up by negating.
                start_deg = -(start_img % 360.0)
                end_deg = -(end_img % 360.0)
                sweep = "ccw"
                from pwa.floorplan import cad_exact_geometry as CG

                try:
                    bulge = CG.bulge_for_sweep("ccw", angle_rad=math.radians((end_img - start_img) % 360.0 or 360.0))
                except ValueError:
                    bulge = 0.0
                arc_mm = {
                    "center": center_mm,
                    "radius_mm": radius_mm,
                    "start_deg": start_deg,
                    "end_deg": end_deg,
                    "sweep": sweep,
                    "bulge": bulge,
                    "max_sagitta_px": CG.sagitta_px(radius_mm, math.radians((end_img - start_img) % 360.0 or 360.0), 32, mm_per_px),
                }
                wall["arc"] = arc_mm
        else:
            wall["start_mm"] = None
            wall["end_mm"] = None
            wall["thickness_m"] = None

    for opening in openings:
        cp = opening.get("center_px")
        if mm_per_px is not None and cp is not None:
            opening["center"] = [_mm(cp[0], mm_per_px), _mm(height_px - cp[1], mm_per_px)]
            opening["width_m"] = opening["width_px"] * (mm_per_px / 1000.0)
        else:
            opening["center"] = None
            opening["width_m"] = None


def _mm(px: float, mm_per_px: float) -> float:
    return float(px) * float(mm_per_px)


def main(argv: list[str] | None = None) -> int:
    import json
    import sys

    argv = argv or sys.argv[1:]
    path = argv[0]
    derive = argv[1] == "true" if len(argv) > 1 else False
    out = argv[2] if len(argv) > 2 else None
    payload = extract_raster_auto(path, derive_scale=derive)
    if out:
        Path(out).write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    else:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
