# WP4 — Moshe decision record (U-3 / U-4 / U-5 / AT-21)

- Date: 2026-08-18
- Decision maker: Moshe (owner approval)
- Scope: unblock the four WP4 BLOCKED decisions so the MAJOR rework can start.
- Choice: **Option 3 — approve all + expand the corpus to 60 now** (not 32).

## Decisions

| Decision | Disposition | Content |
|---|---|---|
| U-3 (arcs) | APPROVE skeleton; numeric bounds stay DRAFT | Kasa fit + RMS ≤ 1 px acceptance; refuse full circle (≥360°−ε); physical radius guard in metres applied after scale. Numeric `r_min/r_max/sweep_min/sweep_max` remain DRAFT pending below/at/above arc fixtures. |
| U-4 (line merge) | APPROVE | Merge two collinear runs only across a RECOGNIZED opening motif; never merge across an unannotated gap; every merge carries documented, reversible provenance. |
| U-5 (style / corpus) | APPROVE — expand to 60 now | Corpus target = **60** synthetic clean-raster fixtures (currently 32), predeclared matrix spanning distinct slices, truth frozen before recognition. |
| AT-21 (truth) | APPROVE derived-only | Synthetic truth is derived solely from source geometry and frozen before recognition; no blind dual labeling / adjudicator required for synthetic fixtures. |

## Consequence

These four decisions are registered append-only. The WP4 card `t_f2830a3e` is unblocked on the
decision layer and may proceed to the MAJOR rework (door / room / arc-hosted-opening reachability,
collinear-merge spurious walls, scale-aware thresholds, confidence + provenance). The corpus must be
expanded 32 → 60 before U-5's ≥60 requirement is met.

## Remaining still BLOCKED (unchanged by this decision)

- U-3 numeric arc bounds (r_min/r_max/sweep) — still DRAFT, need arc fixtures.
- U-6 role separation, U-9 schema/version registration, U-10 resource budget, U-11 renderer/font,
  U-12 spend, U-13 CAD refusal/passage minima, U-14 confidence calibration — unaffected here.
