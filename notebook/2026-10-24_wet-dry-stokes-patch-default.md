# WET_DRY Stokes masking fix becomes a default patch

- **Date:** 2026-10-24
- **Status:** decision (author): patched, applied in every build

## Question / why

A COAWST bug traced earlier the same day on another case (LF-AM3 with
`WET_DRY` and waves drops the Stokes transport towards -i and -j in the first
predictor sub-step of every baroclinic step) had a tested fix but no
patch. The author: "I am happy making the wetdry patch the default". The
author asked to test it on the idealized reef, to save money.

## What was run

- coawst-cloud's `roms-wetdry-stokes` (applied after `roms-limit-bstress`): in that sub-step the time-averaged mask
  itself (0 or 1) masks the Stokes transport, 3-D builds only.
- Control VM (c3d-standard-8), no Batch cost. Reef_Ideal_A15 images built
  three ways: `+LIMIT_BSTRESS` (no `WET_DRY`, reference), `+WET_DRY`
  patched, `+WET_DRY` from the previous commit (unpatched).
  `tests/a15_periodic_test.sh per 1` (periodic, 1 h, 6 ROMS + 2 SWAN,
  history every 10 min), about 150 s wall each.
- A build without `WET_DRY` with and without the patch, to check that it
  changes nothing else.

## Results

| 1 h A15 run against no `WET_DRY` | max ubar diff | max vbar diff | max sea-level diff |
|---|---|---|---|
| `WET_DRY`, unpatched | 0.22 m/s | 0.24 m/s | 12 mm |
| `WET_DRY`, patched | 6.2e-5 m/s | 1.1e-5 m/s | 3e-6 m |

- Largest currents in the run: 1.0 m/s (vbar), 0.5 m/s (ubar). Nothing
  dries (shallowest water 0.5 m, DCRIT 0.10 m). The unpatched difference
  starts at the first wave exchange (10 min) and grows to 0.2 m/s by
  40 min.
- Build without `WET_DRY`: `coawstM` bit-identical with and without the
  patch (md5 `79e978f8...`).

## Decision / outcome

Default patch (author). Changes results only for builds with `WET_DRY`,
waves and the LF-AM3 kernel; none of the current cases. No image
rebuilt or pushed.

## Open questions

- Report the bug upstream (COAWST GitHub)?

## Details and links

- coawst-cloud's patch documents, roms-wetdry-stokes.patch
- Entry WET_DRY drops part of the Stokes transport
