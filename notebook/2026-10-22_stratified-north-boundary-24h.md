# Stratified A15 over 24 h: which north open boundary

- **Date:** 2026-10-22 (runs); default chosen by the author 2026-10-23
- **Status:** decision (author): RadNud plus the interior nudging band

## Question / why

A 24 h run at N^2 = 1e-4 with A15's zero-gradient north boundary showed
errors growing near the boundary. Which open-boundary treatment keeps a
stratified run clean for a day or more?

## What was run

Batch, 24 h, A15's waves and tide, N^2 = 1e-4, DT 6 s unless stated:
- `strat-24h` (image `sha256:24d30199...`, c2d-standard-16, 10 + 6):
  forced, and at rest (no tide, Hs 1 mm).
- `strat-obc-24h` (image `sha256:9bac8cf1...`, c2d-standard-8, 6 + 2):
  Rad; RadNud; band with zero-gradient; RadNud + band; zero-gradient at
  DT 3 s. `strat-radsponge-24h` (same image, c2d-16, 10 + 6): Rad + band,
  and RadNud + band as control.
- RadNud: exterior = initial stratification at rest, outflow 1 day,
  inflow 0.1 day (`OBCFAC` 10). Band: 1 km wide, 1 h at the boundary.
  Cost: not recorded.

## Results

| At 24 h | zero-gradient (6 s / 3 s) | Rad | RadNud | band only | RadNud + band |
|---|---|---|---|---|---|
| north boundary \|v\|, \|u\| (cm/s) | 5.8, 8.3, growing | 0.56, 0.31 | 0.51, 0.21 | 0.55, 0.17 | 0.52, 0.16 |
| rows 100-110: max \|T - initial\| (C) | 2.11 / 2.08 | 0.15 | 0.08 | 0.45 (boundary row only) | 0.03 |
| domain-mean T drift (C) | +0.40 / +0.39 | +0.055 | +0.058 | +0.001 | +0.013 |

- Over the reef zero-gradient differs from the others by up to 1.2 C,
  1.6 cm/s and 3 cm of Hs; the treatments differ from each other by at
  most 0.09 C, 2 mm/s and 7 mm.
- Zero-gradient drifts the same at DT 3 s and stays clean at rest: a
  boundary effect driven by the tide. It copies the next row level by
  level, but the bottom still slopes (391 -> 400 m), so the bottom
  boundary cell starts 0.45 C too warm.
- Rad + band: rows 110/109/105 within 0.007/0.007/0.011 C of the initial
  file (RadNud + band 0.011/0.018/0.020); the c2d-16 control is
  bit-identical to the c2d-8 run.

## Decision / outcome

> **North open boundary of the stratified and thermal cases: RadNud plus
> the interior nudging band is the default** (author, 2026-10-23). Nudging
> (toward a reference state) and the sponge (extra viscosity/diffusivity
> only) are different things; keep the sponge off. (the project conventions)

Early commits call the band a "nudging sponge"; renamed in `3d38700`.

## Open questions

- Rad + band is equivalent over 24 h; RadNud anchors the boundary to the
  initial profile, which may matter in week-long runs (untested). The
  sponge was only tested in the 3 h screening.

## Details and links

- [docs, Constant stratification](../docs/Reef_Ideal_A15_veg_strat.md) ("Over 24 h the north boundary matters"); [Case README](../docs/Reef_Ideal_A15_veg_strat.md); switches set by `tests/north_obc.sh`
