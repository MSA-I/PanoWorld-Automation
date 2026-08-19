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

    # Arc-first + diagonal-first: detect the circular arc AND the 3-4-5 diagonal
    # from the STRUCTURAL mask (pre-erosion, where they are clean strokes), remove
    # them, then erode + recover the remaining axis-aligned walls so Hough does
    # not chord/staircase-fragment the curved and diagonal walls.
    arc = _detect_arc_from_structural(ink)
    ink_segments = ink
    if arc is not None:
        ink_segments = ink_segments & (1 - _paint_arc_ring(ink.shape, arc["center_px"], arc["radius_px"]))
    # Diagonal detection runs AFTER arc removal so the arc's chord/tangent pixels
    # cannot be mistaken for a non-axis straight wall.
    diag = _detect_diagonal_from_structural(ink_segments)
    if diag is not None:
        ink_segments = ink_segments & (1 - _paint_line_band(ink.shape, diag["theta_deg"], diag["rho"]))
    wall_ink = G.wall_centerlines(ink_segments)   # 1 px wall skeleton, opening motifs removed
    segment_walls = _recover_segment_walls(wall_ink, thickness_ink=ink_segments)
    arc_walls = _arc_wall_from_detection(arc, len(segment_walls)) if arc is not None else []
    diag_walls = _diagonal_wall_from_detection(diag, len(segment_walls) + len(arc_walls)) if diag is not None else []
    walls = segment_walls + arc_walls + diag_walls

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

    # --- topology / face derivation (pixel space) --------------------------
    rooms = _derive_rooms(walls, mm_per_px)

    # --- scale conversion to mm (FX1 truth space) --------------------------
    _finalize_units(walls, rooms, openings, mm_per_px, h)

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
    """Read authoritative scale anchors for ``path`` from the per-plan manifest.

    The manifest is the SIBLING of the raster with the same stem and the
    ``-scale-anchors.json`` suffix (``fx1-scale-anchors.json`` for the FX1
    fixture, ``fxx-scale-anchors.json`` for a corpus fixture). This is the
    no-OCR envelope (C-1/W-05): scale is read from the hash-bound manifest, never
    from digits in the image. Returns a list of ``{span_px, real_length_m}``
    records. The manifest binds each anchor's real length to its expected pixel
    span and is hash-bound to the raster. A raster whose SHA-256 does not match
    the manifest's ``raster_sha256`` yields no anchors (fail-closed: scale never
    resolves for an unbound raster), and any other raster has no manifest -> no
    anchors.
    """
    import hashlib
    import json

    manifest_path = path.with_name(path.stem + "-scale-anchors.json")
    if not manifest_path.is_file():
        return []
    try:
        doc = json.loads(manifest_path.read_text(encoding="utf-8"))
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
    best = None  # (inlier_count, cx, cy, r)
    # Subsample the point cloud for the per-iteration inlier count (the full
    # count is only done once on the winning candidate), keeping the RANSAC
    # cheap while preserving the deterministic winner.
    pts_sub = pts[::4]
    for _ in range(20000):
        idx = rng.randint(0, n, 3)  # O(3), duplicates rejected by the spread check
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
        dists = np.hypot(pts_sub[:, 0] - cx, pts_sub[:, 1] - cy)
        cnt = int((np.abs(dists - r) <= 3.0).sum())  # structural arc is a 3px stroke
        if cnt >= 75 and (best is None or cnt > best[0]):  # 300 / 4 (subsample)
            best = (cnt, cx, cy, r)
    if best is None:
        return None
    _, cx, cy, r = best
    dists = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
    inl = np.abs(dists - r) <= 3.0
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


def _line_from_points(p0: np.ndarray, p1: np.ndarray) -> tuple[float, float] | None:
    """Return (theta_deg, rho) of the line through two points (Hough convention)."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    length = math.hypot(dx, dy)
    if length < 1.0:
        return None
    nx, ny = -dy / length, dx / length  # normal = direction rotated +90deg
    theta = math.degrees(math.atan2(ny, nx)) % 180.0
    rho = p0[0] * math.cos(math.radians(theta)) + p0[1] * math.sin(math.radians(theta))
    return theta, rho


def _detect_diagonal_from_structural(structural: np.ndarray) -> dict | None:
    """Detect a NON-axis straight wall (the 3-4-5 diagonal) from the STRUCTURAL mask.

    Hough chord-fragments a 3-4-5 diagonal because its rasterization is a
    staircase whose axis-aligned steps vote as near-axis lines. Here the diagonal
    is fit directly (deterministic RANSAC 2-point line fit, fixed seed), rejecting
    axis-aligned fits, then removed before erosion. Returns
    ``{theta_deg, rho, start_px, end_px}`` or None.
    """
    import numpy as np

    ys, xs = np.nonzero(structural)
    pts = np.column_stack([xs, ys]).astype(np.float64)
    n = pts.shape[0]
    if n < 200:
        return None
    rng = np.random.RandomState(20260818)  # fixed seed -> deterministic
    best = None  # (inlier_count, theta, rho, inlier_bool)
    for _ in range(5000):
        i0, i1 = rng.randint(0, n, 2)  # O(2), duplicates rejected by the spread check
        p0, p1 = pts[i0], pts[i1]
        if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) < 60.0:
            continue
        line = _line_from_points(p0, p1)
        if line is None:
            continue
        theta, rho = line
        # Reject axis-aligned fits: the diagonal is the only non-axis wall in the
        # clean envelope. |sin(2*dir)| ~ 0 for 0/90/180deg, ~1 for 45deg.
        dir_deg = (theta + 90.0) % 180.0
        if abs(math.sin(math.radians(2.0 * dir_deg))) < 0.5:
            continue
        dist = np.abs(pts[:, 0] * math.cos(math.radians(theta)) + pts[:, 1] * math.sin(math.radians(theta)) - rho)
        inl = dist <= 3.0  # structural stroke is 3px
        cnt = int(inl.sum())
        if cnt >= 300 and (best is None or cnt > best[0]):
            best = (cnt, theta, rho, inl)
    if best is None:
        return None
    _, theta, rho, inl = best
    inl_pts = pts[inl]
    # Endpoints from the inliers' projection onto the line direction.
    ux = math.cos(math.radians(theta + 90.0))
    uy = math.sin(math.radians(theta + 90.0))
    t = inl_pts[:, 0] * ux + inl_pts[:, 1] * uy
    t0, t1 = float(t.min()), float(t.max())
    start_px = [t0 * ux + rho * math.cos(math.radians(theta)), t0 * uy + rho * math.sin(math.radians(theta))]
    end_px = [t1 * ux + rho * math.cos(math.radians(theta)), t1 * uy + rho * math.sin(math.radians(theta))]
    return {"theta_deg": theta, "rho": rho, "start_px": start_px, "end_px": end_px}


def _paint_line_band(shape: tuple[int, int], theta_deg: float, rho: float, width_px: int = 4) -> np.ndarray:
    """Boolean mask of a band (width) around a (theta, rho) line."""
    import numpy as np

    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist = xx * math.cos(math.radians(theta_deg)) + yy * math.sin(math.radians(theta_deg)) - rho
    return (np.abs(dist) <= width_px).astype(np.uint8)


def _diagonal_wall_from_detection(diag: dict, index: int) -> list[dict]:
    """Convert a detected diagonal into the segment wall dict shape."""
    return [{
        "index": index,
        "source_ref": "raster:diagonal#0",
        "kind": "segment",
        "start_px": diag["start_px"],
        "end_px": diag["end_px"],
        "thickness_px": 3.0,
        "orientation_deg": diag["theta_deg"] + 90.0,
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
    """Detect openings (gaps + motif) along a straight wall centreline.

    A door is a gap whose JAMB carries a perpendicular leaf stroke (the leaf is
    authored at the opening's start jamb, not the gap centre); a window has no
    gap but carries a parallel glazing stroke offset ~4 px off the centreline; a
    passage is a bare empty gap. Deterministic; type comes from the motif.
    """
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

    openings: list[dict] = []
    N = int(length)

    # 1. Gaps (doors + passages): empty runs along the centreline.
    t = np.arange(0, N, 1.0)
    cx = x0 + ux * t
    cy = y0 + uy * t
    empty = np.zeros(N, dtype=bool)
    for i in range(N):
        xi = int(round(cx[i]))
        yi = int(round(cy[i]))
        if 0 <= xi < w and 0 <= yi < h:
            empty[i] = ink[yi, xi] == 0
        else:
            empty[i] = True
    gap_floor = 1.5 * G.WALL_STROKE_PX
    gap_ceil = G.WALL_OPENING_GAP_PX
    for (gi0, gi1) in _empty_runs(~empty, gap_floor, gap_ceil):
        # Classify: leaf at a jamb -> door, else passage.
        motif = "passage"
        for jamb_i in (gi0, gi1):
            jx = x0 + ux * jamb_i
            jy = y0 + uy * jamb_i
            if _leaf_present(ink, jx, jy, nx, ny):
                motif = "door"
                break
        tc = (gi0 + gi1) / 2.0
        openings.append({
            "source_ref": wall["source_ref"] + f":opening#{len(openings)}",
            "kind": motif,
            "center_px": [float(x0 + ux * tc), float(y0 + uy * tc)],
            "width_px": float(gi1 - gi0),
            "wall_id": wall["index"],
        })

    # 2. Windows (glazing): no gap, but a parallel stroke offset off-centreline.
    #    Emitted only for centreline positions with the offset stroke, grouped.
    win_runs = _glazing_runs(ink, x0, y0, ux, uy, N, h, w)
    for (wi0, wi1) in win_runs:
        tc = (wi0 + wi1) / 2.0
        openings.append({
            "source_ref": wall["source_ref"] + f":opening#{len(openings)}",
            "kind": "window",
            "center_px": [float(x0 + ux * tc), float(y0 + uy * tc)],
            "width_px": float(wi1 - wi0),
            "wall_id": wall["index"],
        })
    return openings


def _leaf_present(ink: np.ndarray, cx: float, cy: float, nx: float, ny: float) -> bool:
    """True if a perpendicular leaf stroke (>= 100 px) starts near (cx, cy)."""
    h, w = ink.shape
    for direction in (1.0, -1.0):
        run = 0
        for k in range(1, 190):  # leaf is 180 px long
            px = int(round(cx + nx * direction * k))
            py = int(round(cy + ny * direction * k))
            if 0 <= px < w and 0 <= py < h and ink[py, px]:
                run += 1
            else:
                break
        if run >= 100:
            return True
    return False


def _glazing_runs(ink, x0, y0, ux, uy, N, h, w) -> list[tuple[int, int]]:
    """Return [(i0, i1), ...] centreline index runs where the glazing offset stroke
    (the second parallel line at a ~4 px diagonal offset) is present."""
    runs = []
    i = 0
    while i < N:
        xi = int(round(x0 + ux * i))
        yi = int(round(y0 + uy * i))
        hit = _glazing_at(ink, xi, yi, h, w)
        if hit:
            j = i
            while j < N and _glazing_at(ink, int(round(x0 + ux * j)), int(round(y0 + uy * j)), h, w):
                j += 1
            if j - i >= 10:  # a window spans >= ~50 mm
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def _glazing_at(ink, xi, yi, h, w) -> bool:
    """True if there is ink at the glazing's fixed (+4,+4) render offset.

    The window's second glazing line is authored at exactly (x+4, y+4); scanning
    the other diagonal offsets also catches the diagonal-staircase wall's own
    steps (which span ~all offsets), over-detecting the window across the whole
    wall. The single fixed offset is provable and staircase-robust.
    """
    px, py = xi + 4, yi + 4
    return 0 <= px < w and 0 <= py < h and ink[py, px]


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


def _arc_wall_opening(ink: np.ndarray, wall: dict) -> dict | None:
    """Detect an arc-hosted window (two concentric glazing arcs) — if present.

    The arc window is authored as TWO concentric arcs at radius r and r-8 (the
    glazing), spanning a sub-range of the host arc. Scan the host arc's angular
    span for the inner glazing arc; the contiguous hit run is the window. Returns
    None when no distinct inner arc is provable (never fabricate an arc opening).
    """
    arc = wall.get("arc_px")
    if not arc:
        return None
    cx, cy = arc["center"]
    r = arc["radius_px"]
    start = arc["start_deg"]
    end = arc["end_deg"]
    sweep = (end - start) % 360.0
    if sweep < 10.0:
        return None
    h, w = ink.shape
    N = max(int(sweep), 2)
    hits: list[int] = []
    for i in range(N + 1):
        ang = math.radians(start + sweep * i / N)
        # inner glazing arc at radius r-8 (the second concentric stroke)
        px = int(round(cx + (r - 8.0) * math.cos(ang)))
        py = int(round(cy + (r - 8.0) * math.sin(ang)))
        if 0 <= px < w and 0 <= py < h and ink[py, px]:
            hits.append(i)
    if len(hits) < 5:
        return None
    i0, i1 = min(hits), max(hits)
    # A glazing arc spanning essentially the whole host arc is not a window.
    if (i1 - i0) >= N - 2:
        return None
    ang_c = math.radians(start + sweep * (i0 + i1) / 2.0 / N)
    span_deg = sweep * (i1 - i0) / N
    return {
        "source_ref": wall["source_ref"] + ":opening#0",
        "kind": "window",
        "center_px": [cx + r * math.cos(ang_c), cy + r * math.sin(ang_c)],
        "width_px": r * math.radians(span_deg),
        "wall_id": wall["index"],
        "arc_span_deg": [start + sweep * i0 / N, start + sweep * i1 / N],
    }


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
        if wall.get("kind") == "circular_arc" and wall.get("arc_px"):
            # A circular_arc wall is a curved ring, not a chord: paint the full
            # ring band (wall stroke) so the apse is attributed, not left as
            # unexplained ink (which would falsely fail-closed every arc plan).
            arc = wall["arc_px"]
            _paint_arc_band(coverage, arc["center"], arc["radius_px"],
                            arc["start_deg"], arc["end_deg"], radius=4)
            continue
        a = wall.get("start_px")
        b = wall.get("end_px")
        if a is None or b is None:
            continue
        _paint(coverage, a, b, radius=4)
    for opening in openings:
        # An arc-hosted window also carries an inner concentric glazing arc at
        # radius-8 across its angular span; attribute that ink too.
        span = opening.get("arc_span_deg")
        if span is not None and opening.get("kind") == "window":
            wl = next((x for x in walls if x.get("index") == opening.get("wall_id")), None)
            if wl and wl.get("arc_px"):
                arc = wl["arc_px"]
                _paint_arc_band(coverage, arc["center"], arc["radius_px"] - 8.0,
                                span[0], span[1], radius=4)
            continue
        c = opening.get("center_px")
        if c is None:
            continue
        _paint_disc(coverage, c, radius=12)
    return int((ink & (1 - coverage)).sum())


def _paint_arc_band(coverage, center, radius_px, start_deg, end_deg, radius: int) -> None:
    """Paint an annular band of the arc ring (radius +/- ``radius``) over an angular span."""
    import numpy as np

    h, w = coverage.shape
    cx, cy = center[0], center[1]
    sweep = (end_deg - start_deg) % 360.0
    if sweep < 1.0:
        sweep = 360.0
    # Sample densely enough to paint every pixel of the curved stroke: one
    # angular step per ~1 px of arc length (a stroke is 1 px thick along the
    # arc), otherwise adjacent radial columns leave gaps and the ring reads as
    # unexplained ink even though it IS attributed to the recovered arc wall.
    arc_len_px = abs(radius_px) * math.radians(sweep)
    steps = max(int(arc_len_px), 16)
    for i in range(steps + 1):
        ang = math.radians(start_deg + sweep * i / steps)
        ca, sa = math.cos(ang), math.sin(ang)
        # sample the band around the ring point
        for dr in range(-radius, radius + 1):
            px = int(round(cx + (radius_px + dr) * ca))
            py = int(round(cy + (radius_px + dr) * sa))
            if 0 <= px < w and 0 <= py < h:
                coverage[py, px] = 1


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
    """Derive room faces from the recovered wall centrelines (planar half-edge walk).

    Snap wall endpoints to junctions (within a stroke tolerance), build a planar
    half-edge graph (the arc is approximated by its chord), and walk faces. The
    outer boundary face is dropped by its (large, clockwise) signed area; the
    remaining bounded faces are the rooms. Deterministic; returns [] when scale
    is unresolved or the graph has no bounded face (fail-closed).
    """
    if mm_per_px is None:
        return []
    import numpy as np
    from collections import defaultdict

    # 1. Collect edges (segments + arc chords).
    edges: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for w in walls:
        sp, ep = w.get("start_px"), w.get("end_px")
        if sp is None or ep is None:
            continue
        edges.append(((float(sp[0]), float(sp[1])), (float(ep[0]), float(ep[1]))))
    if len(edges) < 3:
        return []

    # 1b. Split edges at T-junctions (a wall endpoint meeting another wall's
    # interior) so the planar graph is closed; endpoint-to-endpoint joins are
    # left to the snapping step below. TOL also snaps the diagonal's RANSAC-fit
    # endpoints onto their host walls (~7 px fit error, above the old 6 px).
    TOL = 10.0
    split_points: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for i, (p, q) in enumerate(edges):
        qp = (q[0] - p[0], q[1] - p[1])
        L2 = qp[0] * qp[0] + qp[1] * qp[1]
        if L2 < 1e-9:
            continue
        for j, (r, s) in enumerate(edges):
            if i == j:
                continue
            for pt in (r, s):
                t = ((pt[0] - p[0]) * qp[0] + (pt[1] - p[1]) * qp[1]) / L2
                if t < 0.03 or t > 0.97:
                    continue  # near an endpoint; snapping handles it
                proj = (p[0] + t * qp[0], p[1] + t * qp[1])
                if math.hypot(pt[0] - proj[0], pt[1] - proj[1]) < TOL:
                    split_points[i].append(proj)
    if split_points:
        split_edges = []
        for i, (p, q) in enumerate(edges):
            pts = [p] + sorted(
                split_points[i],
                key=lambda z: (z[0] - p[0]) * (q[0] - p[0]) + (z[1] - p[1]) * (q[1] - p[1]),
            ) + [q]
            for a, b in zip(pts, pts[1:]):
                if a != b:
                    split_edges.append((a, b))
        edges = split_edges

    # 2. Snap endpoints to junctions (union-find clustering within TOL).
    pts_arr = np.array([p for e in edges for p in e], dtype=np.float64)
    n = len(pts_arr)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            if math.hypot(pts_arr[i, 0] - pts_arr[j, 0], pts_arr[i, 1] - pts_arr[j, 1]) < TOL:
                union(i, j)
    clusters: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)
    centroid: dict[int, tuple[float, float]] = {}
    for rep, idxs in clusters.items():
        centroid[rep] = (float(pts_arr[idxs, 0].mean()), float(pts_arr[idxs, 1].mean()))

    snapped: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for k, e in enumerate(edges):
        p = centroid[find(2 * k)]
        q = centroid[find(2 * k + 1)]
        if p != q:
            snapped.append((p, q))
    if len(snapped) < 3:
        return []

    # 3. Half-edge adjacency: junction -> sorted (angle, to) outgoing edges.
    out: dict[tuple[float, float], list[tuple[float, tuple[float, float]]]] = defaultdict(list)
    for (p, q) in snapped:
        out[p].append((math.atan2(q[1] - p[1], q[0] - p[0]), q))
        out[q].append((math.atan2(p[1] - q[1], p[0] - q[0]), p))
    for j in out:
        out[j].sort(key=lambda x: x[0])

    # 4. Walk faces via the half-edge "next" rule (next CCW of the reverse edge).
    used: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    faces: list[list[tuple[float, float]]] = []
    for u, nbrs in out.items():
        for (_, v) in nbrs:
            if (u, v) in used:
                continue
            face = [u, v]
            used.add((u, v))
            cur = (u, v)
            while True:
                cu, cv = cur
                rev_ang = math.atan2(cu[1] - cv[1], cu[0] - cv[0])
                # next edge: smallest CLOCKWISE angle from the reverse edge (the
                # face is traced on the left); skip the reverse half-edge itself
                cand = out[cv]
                best = None
                for (ang, to) in cand:
                    diff = (rev_ang - ang) % (2.0 * math.pi)
                    if diff < 1e-6:
                        diff = 2.0 * math.pi  # the reverse half-edge, never take it
                    if best is None or diff < best[0]:
                        best = (diff, to)
                nxt = best[1]
                nhe = (cv, nxt)
                if nhe in used or nxt == face[0]:
                    if nxt == face[0]:
                        faces.append(face)
                    break
                used.add(nhe)
                face.append(nxt)
                cur = (cv, nxt)

    # 5. Keep bounded faces (positive shoelace area in y-down image space).
    rooms: list[dict] = []
    for face in faces:
        if len(face) < 3:
            continue
        area = 0.0
        for i in range(len(face)):
            x1, y1 = face[i]
            x2, y2 = face[(i + 1) % len(face)]
            area += x1 * y2 - x2 * y1
        area *= 0.5
        if area < 60.0:  # drop the outer face (negative) and tiny slivers
            continue
        rooms.append({
            "id": f"R-{len(rooms)}",
            "area_px": float(area),
            "points": [[float(x), float(y)] for x, y in face],
        })
    return rooms


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

    # Rooms are derived in pixel space (points + area_px); convert them to the
    # same mm truth space as walls/openings so the contract layer can divide by
    # 1000 uniformly. This closes the room-channel gap: without it the rooms
    # carried no ``polygon`` and were silently dropped by the emitter.
    for i, room in enumerate(rooms):
        pts = room.get("points")
        if mm_per_px is not None and pts is not None:
            room["polygon"] = [[_mm(p[0], mm_per_px), _mm(height_px - p[1], mm_per_px)] for p in pts]
            # area_m2 from the shoelace area on the mm polygon (py is flipped,
            # but the absolute signed area is invariant).
            area_mm2 = 0.0
            n = len(room["polygon"])
            for k in range(n):
                x1, y1 = room["polygon"][k]
                x2, y2 = room["polygon"][(k + 1) % n]
                area_mm2 += x1 * y2 - x2 * y1
            room["area_m2"] = abs(area_mm2) * 0.5 / 1_000_000.0
        else:
            room["polygon"] = None
            room["area_m2"] = None
        room["index"] = i
        room["source_ref"] = f"raster:face#{i}"


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
