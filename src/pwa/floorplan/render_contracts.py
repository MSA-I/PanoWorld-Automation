"""Renderer / font / CVD / legibility contract checkers (PLAN-002RF packet §7, WP5).

Pure, deterministic, side-effect-free functions implementing the frozen evidence
legibility contract so that a renderer (when one is pinned — U-11 is still
BLOCKED) can prove its output meets the required thresholds without a human
eyeball. These are the *contract* layer only; no renderer is selected here and
no output is produced by this module.

Frozen thresholds (packet §7, line 118):

  - body text >= 12 CSS px; legend text >= 14 CSS px;
  - text contrast >= 4.5:1; geometry contrast >= 3:1;
  - accepted-stroke contrast >= 3:1 under declared protanopia /
    deuteranopia / tritanopia severity-1.0 simulation.

The CVD simulation uses the standard Machado (2010) severity-1.0 matrix for the
three deficiencies. It is deterministic and versioned; U-11 (pinned
renderer/font and normalized-pixel contract) remains BLOCKED, so this module is
the *measurable criteria* the future renderer must pass, not the renderer itself.
"""

from __future__ import annotations

# --- Frozen legibility thresholds (packet §7) ---------------------------------
TEXT_MIN_CSS_PX = 12.0
LEGEND_MIN_CSS_PX = 14.0
TEXT_CONTRAST_MIN = 4.5
GEOMETRY_CONTRAST_MIN = 3.0

_CVD_KIND = ("protanopia", "deuteranopia", "tritanopia")

# Machado et al. (2010) simulation matrices, severity 1.0, sRGB-linear domain.
# The matrix maps an sRGB-linear vector to the simulated LMS response. Values
# are the published severity-1.0 coefficients (rounded, deterministic).
_MACHADO_1_0: dict[str, tuple[tuple[float, float, float], ...]] = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanopia": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}


def _srgb_to_linear(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(c: float) -> float:
    c = max(0.0, min(1.0, c))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055
    return round(v * 255.0)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    lin = [_srgb_to_linear(float(ch)) for ch in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """WCAG contrast ratio between two sRGB colours (1.0 .. 21.0)."""
    l1 = _relative_luminance(fg)
    l2 = _relative_luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def meets_text_contrast(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> bool:
    return contrast_ratio(fg, bg) >= TEXT_CONTRAST_MIN


def meets_geometry_contrast(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> bool:
    return contrast_ratio(fg, bg) >= GEOMETRY_CONTRAST_MIN


def meets_font_size(size_css_px: float, *, kind: str) -> bool:
    """True iff ``size_css_px`` meets the frozen minimum for ``kind``."""
    minimum = LEGEND_MIN_CSS_PX if kind == "legend" else TEXT_MIN_CSS_PX
    return float(size_css_px) >= minimum


def simulate_cvd(rgb: tuple[int, int, int], deficiency: str) -> tuple[int, int, int]:
    """Simulate the given CVD deficiency at severity 1.0, deterministically."""
    if deficiency not in _CVD_KIND:
        raise ValueError(f"unknown CVD deficiency {deficiency!r}")
    matrix = _MACHADO_1_0[deficiency]
    lin = [_srgb_to_linear(float(ch)) for ch in rgb]
    out = [matrix[i][0] * lin[0] + matrix[i][1] * lin[1] + matrix[i][2] * lin[2]
           for i in range(3)]
    return tuple(_linear_to_srgb(c) for c in out)  # type: ignore[return-value]


def meets_geometry_contrast_under_cvd(
    fg: tuple[int, int, int], bg: tuple[int, int, int], deficiency: str
) -> bool:
    """Geometric-contrast check re-run under a declared CVD deficiency."""
    sim_fg = simulate_cvd(fg, deficiency)
    sim_bg = simulate_cvd(bg, deficiency)
    return meets_geometry_contrast(sim_fg, sim_bg)
