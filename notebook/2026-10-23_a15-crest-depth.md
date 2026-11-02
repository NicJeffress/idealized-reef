# The A15 crest depth, read from the grid file

- **Date:** 2026-10-23
- **Status:** done (documentation corrected)

## Question / why

While writing fuller documentation of the cases, A15's grid file was read
directly (`h`, `mask_rho`, `y_rho` of `roms_grid_default_1.nc`, identical to the
v3.7 original) to check the case description, which had come partly from a
coarse depth profile.

## What was run

No model runs.

## Results

- **The A15 crest is 0.50 m deep (rows 31-34, y = 940-1000 m)**, not 0.63 m at
  about 600 m as the first case notes and the vegetation case notes said.
- At low tide (0.15 m) the crest has 0.35 m of water, so the 0.4 m test canopy
  of `Reef_Ideal_A15_veg` reaches the surface there: the situation handled by
  `veg3_emergent_cd` (coawst-cloud's `swan-vegetation-fixes`), not a
  "submerged" canopy as had been written.
- Model setup behind the timings, for reference: A15 203 x 111 points, 10
  levels, DT 6 s, NDTFAST 24; SWAN on the same grid, 72 directions, 21
  frequencies, 120 s step; MCT exchange every 600 s (100 ROMS and 5 SWAN steps
  per exchange).

## Decision / outcome

Case descriptions corrected and dated.

## Open questions

- "20 frequencies" in some notes means 20 intervals (21 frequencies).

## Details and links

- [docs/Reef_Ideal_A15.md](../docs/Reef_Ideal_A15.md), [docs/Reef_Ideal_A15_veg.md](../docs/Reef_Ideal_A15_veg.md)
