# Vegetation drag crashed with periodic boundaries (`wrk` bounds)

- **Date:** 2026-10-21 (suspected from the code 2026-10-20, confirmed 2026-10-21)
- **Status:** done; `drag_work_array` in coawst-cloud's `roms-vegetation`, in every image

## Question / why

The author remembered a "vegetation periodic BC bug" from older COAWST
versions, and coral canopy drag through the vegetation package is a
project decision. Does vegetation work with A15's east-west periodic
boundaries?

## What was run

- Code reading of `ROMS/Nonlinear/Vegetation/vegetation_drag.F` (same in
  v3.7, v3.8.1 and v3.9).
- `cases/Reef_Ideal_A15_veg`: A15 with a constant submerged canopy
  everywhere (author's test, 2026-10-20): density 4 m-2, diameter 0.5 m,
  height 0.4 m (lambda_f 0.8), Cd 1; `VEGETATION`, `VEG_DRAG`, `VEG_TURB`,
  `VEG_SWAN_COUPLING` on.

## Results

- The work array `wrk` was declared with tile-private bounds
  `IminS:ImaxS` (tile -3 ... +3) but exchanged by `exchange_r2d_tile` and
  `mp_exchange2d` with the halo bounds `LBi:UBi`. With A15 (periodic,
  MPDATA, 3 ghost points) `LBi` = -3 but `IminS` = -2, so the exchange
  wrote past the end of the array.
- The constant-vegetation test aborted on the first ROMS step with
  `munmap_chunk(): invalid pointer` in `mp_exchange2d` called from
  `vegetation_drag_tile`.
- Fix: declare `wrk(LBi:UBi,LBj:UBj)`; every use lies within those bounds.

## Decision / outcome

`drag_work_array` in coawst-cloud's `roms-vegetation`, applied in every build.
Likely the bug the author remembered.

## Open questions

- The tiling test planned with it (1x1 vs 2x1 vs 1x2 tiles) was covered
  later: the coupled periodic vegetation runs have a clean seam, and in
  the 2026-10-22 spatial vegetation tests 2x3 tiles differ from 1x6 at
  rounding level, as without plants.
- PERFECT_RESTART with vegetation (COAWST issue #266) is still untested.

## Details and links

- coawst-cloud's patch documents, roms-vegetation.patch
- [docs, Code issues](../docs/Reef_Ideal_A15.md)
- [`docs/Reef_Ideal_A15_veg.md`](../docs/Reef_Ideal_A15_veg.md)
- Next: [cylinder convention](2026-10-21_vegetation-cylinder-convention.md)
