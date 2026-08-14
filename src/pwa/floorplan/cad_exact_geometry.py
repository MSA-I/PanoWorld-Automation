"""Deterministic cad_exact arc/bulge geometry primitives (PLAN-002RF WP3).

Pure, side-effect-free geometry for Product A (`cad_exact`): bounded circular
arcs and LWPOLYLINE bulges, their sagitta/tessellation rules, and the bulge
<-> sweep sign convention. Everything here is frozen to the FX1 truth
(`fx1-truth.json`) and the WP1 frozen evaluator constants
(`SAGITTA_MAX_PX`, bulge > 0 == counter-clockwise sweep).

No recognizer, no I/O, no model call. Routes remain default-off.
"""

from __future__ import annotations

import math

# Frozen convention (WP2 recognition.arc_invariants): bulge > 0 -> ccw sweep.
_CCW = 1.0
_CW = -1.0


def bulge_magnitude(sweep_rad: float) -> float:
    """CAD bulge magnitude: bulge = tan(theta / 4) for swept angle theta.

    ``sweep_rad`` must be in (0, 2*pi); the magnitude is always positive here
    (sign is added separately by ``bulge_for_sweep``).
    """
    theta = float(sweep_rad)
    if not 0.0 < theta < 2.0 * math.pi:
        raise ValueError("sweep angle must be in (0, 2*pi)")
    return math.tan(theta / 4.0)


def bulge_for_sweep(sweep: str, angle_rad: float | None = None, *, theta_rad: float | None = None) -> float:
    """Return a signed bulge consistent with the frozen ccw>0 convention.

    ``sweep`` is ``"ccw"`` or ``"cw"``. The swept angle is taken from
    ``theta_rad`` when given, otherwise ``angle_rad``.
    """
    theta = theta_rad if theta_rad is not None else angle_rad
    if theta is None:
        raise ValueError("a swept angle is required")
    magnitude = bulge_magnitude(float(theta))
    return magnitude if sweep == "ccw" else -magnitude


def sweep_from_bulge(bulge: float) -> float:
    """Return the (positive) swept angle implied by a bulge magnitude.

    ``theta = 4 * atan(|bulge|)``. The sign of ``bulge`` is ignored here;
    callers that need direction use ``bulge_for_sweep`` / ``sweep_from_endpoints``.
    """
    return 4.0 * math.atan(abs(float(bulge)))


def sagitta_px(radius_mm: float, sweep_rad: float, n_segments: int, mm_per_px: float) -> float:
    """Sagitta of a chord segment in pixels.

    ``sagitta = R * (1 - cos(theta / (2*N)))``, converted to px via
    ``mm_per_px`` (FX1 uses 5 mm/px).
    """
    r = float(radius_mm)
    segment = float(sweep_rad) / (2.0 * int(n_segments))
    return r * (1.0 - math.cos(segment)) / float(mm_per_px)


def min_segments_for_sagitta(
    radius_mm: float,
    sweep_rad: float,
    max_sagitta_px: float,
    mm_per_px: float,
) -> int:
    """Smallest power-of-two N >= 2 with sagitta(N) <= max_sagitta_px.

    ``N_min`` is the smallest integer N >= 2 with sagitta <= bound; the result
    is the smallest power of two >= N_min (FX1 §5.1), so any halving of an arc
    still lands on existing vertices.
    """
    bound = float(max_sagitta_px)
    n = 2
    while True:
        if sagitta_px(radius_mm, sweep_rad, n, mm_per_px) <= bound:
            return _next_power_of_two(n)
        n += 1


def _next_power_of_two(n: int) -> int:
    result = 1
    while result < n:
        result *= 2
    return result


def sweep_from_endpoints(start_deg: float, end_deg: float, direction: str) -> tuple[str, float]:
    """Return (sweep, angle_rad) for an arc authored by start/end angle.

    ``direction`` is ``"ccw"`` or ``"cw"``. A ccw arc from ``start_deg`` to
    ``end_deg`` sweeps ``(end - start) mod 360`` degrees; a cw arc sweeps the
    complementary direction. Both are mapped to a positive angle in (0, 2*pi].
    """
    start = float(start_deg) % 360.0
    end = float(end_deg) % 360.0
    delta = (end - start) % 360.0
    if direction == "ccw":
        degrees = delta
    elif direction == "cw":
        degrees = (360.0 - delta) % 360.0
    else:
        raise ValueError("direction must be 'ccw' or 'cw'")
    if degrees == 0.0:
        degrees = 360.0
    return direction, math.radians(degrees)


def is_bounded_circular_arc(radius: float, start_deg: float, end_deg: float) -> bool:
    """A bounded arc has finite positive radius and finite sweep endpoints."""
    try:
        r = float(radius)
        s = float(start_deg)
        e = float(end_deg)
    except (TypeError, ValueError):
        return False
    return math.isfinite(r) and r > 0.0 and math.isfinite(s) and math.isfinite(e)


def tessellate_arc(
    center: tuple[float, float],
    radius_mm: float,
    start_deg: float,
    end_deg: float,
    sweep: str,
    n_segments: int,
) -> list[tuple[float, float]]:
    """Tessellate a bounded circular arc into ``n_segments + 1`` vertices.

    Vertices P_k = center + R*(cos(theta0 + k*theta/N), sin(...)), k=0..N, with
    theta advancing ccw for ``sweep == "ccw"`` and cw otherwise. Angles use the
    y-up, degrees-from-positive-x model of FX1 (start_deg=-90 points down,
    +90 points up). Deterministic: identical inputs → identical outputs.
    """
    cx, cy = float(center[0]), float(center[1])
    r = float(radius_mm)
    n = int(n_segments)
    if n < 2:
        raise ValueError("n_segments must be >= 2")
    _, theta = sweep_from_endpoints(start_deg, end_deg, sweep)
    sign = 1.0 if sweep == "ccw" else -1.0
    step = sign * theta / n
    vertices: list[tuple[float, float]] = []
    for k in range(n + 1):
        angle = math.radians(float(start_deg)) + k * step
        vertices.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return vertices
