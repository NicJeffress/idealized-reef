# Reef_Ideal_A15_bulk

> **Grid and roller since 2026-11-03 (author's decisions).** The default grid is
> the breaking-zone grid: 203 x 126 rho points, the rows between 850 and 1150 m
> from the shore (crest, breaking zone, top of the fore reef) split in two (10 m
> across the shore, 20 m elsewhere), barotropic Courant 0.81.
> Made from the 20 m grid (203 x 111, this folder before 2026-11-03 in git) with
> `tools/reef/refine_a15_grid.py --band 850 1150 --factor 2`; it recovers the
> uniform 10 m answer at +16 % cost (notebook 2026-11-03_grid-10m). Row numbers
> quoted below refer to the 20 m grid. The Reniers roller is on
> (`ROLLER_RENIERS`, `WEC_ALPHA` 0.5; notebook 2026-11-03_roller-checks). Also since
> 2026-11-03: 15 vertical levels (was 10), `GLS_Kmin` 1e-8, SWAN `BKD` breaking and wave
> streaming (`BOTTOM_STREAMING`; `VEG_STREAMING` with the canopy). **DT 3 s, `NDTFAST` 12
> since 2026-11-04** (to stay below the CFL limits; DT 6 s was unsafe with streaming at 15 levels).


Experiment: A15 with `#define BULK_STOKES` (bulk Stokes drift from Hwave,
Lwave, Dwave, as COAWST v3.7 did) instead of v3.9's default spectral Stokes
drift, to compare cost and Stokes profiles. Otherwise identical to
`cases/Reef_Ideal_A15`.
