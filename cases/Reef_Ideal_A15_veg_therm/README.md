# Reef_Ideal_A15_veg_therm: A15 with vegetation, stratification and thermal forcing

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
> streaming (`BOTTOM_STREAMING`; `VEG_STREAMING` with the canopy). **DT 2.5 s, `NDTFAST` 10
> since 2026-11-04** (to stay below the CFL limits at every canopy density and bed roughness; with streaming at 15 levels DT 6 s was unsafe, and DT 3 s reached a vertical Courant number of 1.39 on a smooth bare reef).
>
> **Spectral Stokes drift updated every 120 s since 2026-11-06** (`STOKES_INTERVAL`, `STOKES_NCPL` 5, coawst-cloud
> `roms-stokes-interval`; 2.2x faster, tested on density 1; needs an image built after this date to take effect).


Same as `cases/Reef_Ideal_A15_veg_strat` (constant canopy, periodic ROMS
and SWAN, temperature and salinity evolving, run-time tide), plus (user's
request and choices, 2026-10-23):

- **Surface heat flux** from the case's `ana_srflux.h` and `ana_stflux.h`:
  a clear-sky diurnal shortwave entering the water, `USER(6)` W/m2 at
  noon as a half sine over a `USER(8)` h day centred on noon (`USER(9)` =
  hour of day at model time 0), and a constant non-solar flux `USER(7)`
  W/m2 (longwave + latent + sensible; negative = cooling). Defaults: 1000
  W/m2, 12 h, start at midnight, -318.31 W/m2, which balances the
  shortwave over a day (net zero). `SOLAR_SOURCE` spreads the shortwave
  over depth (Paulson & Simpson, Jerlov `WTYPE` 1 = clear water); light
  reaching the bed heats the bottom cell (ROMS's default; `BOTTOM_ALBEDO`
  is not used yet: it would send the absorbed part into the seabed and
  lose it).
- **Thermal expansion** `TCOEF = 3.2e-4` /C, seawater at 28 C and salinity
  35 (TEOS-10; A15 had 1.7e-4). ROMS's linear equation of state stays.
  `init_reef.nc`: N^2 = 1e-4 s^-2 with this TCOEF (28 C at the surface to
  16 C at 400 m), constant canopy.
- **North boundary**, switched in `ocean.in`:
  - `RadNud` plus the interior nudging band toward the **far-field
    ocean** (the default since 2026-10-23, user's choice after the 3-day
    test; `Lm3CLM`, `LtracerCLM`, `LnudgeM3CLM`, `LnudgeTCLM` = T,
    `OBCFAC` 10): `tools/thermal/far_field.py` integrates a 1-D water
    column with the same surface heating, light absorption and equation
    of state (background diffusivity plus convective adjustment instead
    of GLS) and writes `ocean_clm.nc` (temp/salt for the band) and
    `ocean_bndry.nc` (temp_north/salt_north) into the run directory. 3-D
    velocity is relaxed toward rest. Band width `USER(3)` m, time scale
    `USER(4)` h at the boundary.
  - `Rad` for 3-D velocity and tracers, with the four switches F and
    `OBCFAC` 1: no exterior state. ROMS's radiation keeps the boundary
    value unchanged while a signal travels into the domain, and the
    boundary row does not receive the surface heat flux itself. With
    the waves this lets heat pile up in the domain (+0.35 C domain mean
    in 3 days, `docs/case_design.md`).

  **Every run with the default needs the far-field files**, made for
  that run's `ocean.in` (forcing, `TCOEF`, `USER`, run length from
  `NTIMES` x `DT`) and initial file: `far_field.py --ocean-in ocean.in
  --init init_reef.nc -o .`, or a `generate` step in the ensemble spec
  (as in `batch/ensemble/tests/therm-3d/spec.json`). Without them ROMS
  stops at startup. The image
  `v3.9-26e6fb7-reef_a15_veg_therm` (sha256:0eac0912...) was built
  before the switch and holds the old `ocean.in` (Rad); runs never use
  it as is (Batch members bring their own `ocean.in`,
  `tests/therm_tests.sh` sets the boundary explicitly), and the next
  rebuild picks up the new one. The compiled model is the same.
- History output adds the surface net heat flux (`shflux`) and the
  shortwave (`swrad`).

`USER` order: tide amplitude (m), tide period (h), band width (m),
nudging time scale (h), sponge viscosity (m2/s), peak shortwave (W/m2),
non-solar flux (W/m2), day length (h), hour at time 0.

Build: `docker build --build-arg COAWST_APPLICATION=REEF_IDEAL_A15
--build-arg CASE_DIR=Projects/Reef_Ideal_A15_veg_therm -t
coawst:reef_a15_veg_therm .`

Limits from the stratified case still apply (internal-wave Courant
number below about 0.4-0.5, `tools/cfl_check.py`; the vegetation drag is
explicit).
