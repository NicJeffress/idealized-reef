# Reef_Ideal_A15_veg_strat: A15 with vegetation and constant stratification

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


Same as `cases/Reef_Ideal_A15_veg` (constant canopy, periodic ROMS and
SWAN, `VEGETATION 3`), plus (user's request, 2026-10-22):

- **Temperature and salinity evolve**: `TS_FIXED` is off in the header
  (A15 froze them at 18 C and 35). Tracer advection is MPDATA as before;
  no horizontal tracer diffusion; vertical mixing from GLS. Wind, surface
  heat and salt fluxes and shortwave are zero (ROMS's analytical
  defaults), so temperature changes only by advection, mixing and the
  open north boundary.
- **Initial constant stratification**: `init_reef.nc` holds N^2 =
  1e-4 s^-2 (temperature 28 C at the surface to 5.4 C at 400 m, salinity
  35), written by `tools/stratification/make_strat_init.py`. A15 uses
  ROMS's **linear** equation of state (`NONLIN_EOS` is not defined;
  R0 1027, Tcoef 1.7e-4 /C in `ocean.in`), so a constant N^2 is a linear
  temperature profile, N^2 = g (R0/rho0) Tcoef dT/dz, and temperature
  acts only through density. Other N^2: run the tool and pass the file
  (tests: `INIT=` in `tests/a15_periodic_test.sh`; ensembles: a member
  file `init_reef.nc`).
- **Tide set at run time**: `ana_fsobc.h` takes the amplitude (m) and
  period (h) of the northern-boundary tide from `USER(1)` and `USER(2)`
  in `ocean.in` (A15's 0.15 m and 12 h by default); amplitude 0 turns
  it off. So one image serves every tide.
- History output also has the density anomaly (`rho`).
- **North-boundary options for stratified runs**, switched in `ocean.in`.
  **Default since 2026-10-23 (user's choice): RadNud plus the interior
  nudging band** (`OBCFAC` 10: inflow 0.1 day, outflow 1 day; sponge
  off). A15's zero-gradient (`Gra`, all switches off) is what the N^2
  tests below used (`tests/strat_tests.sh` still sets it). The options
  need the image built with this header, `v3.9-26e6fb7-reef_a15_veg_strat-obc`
  (sha256:9bac8cf1...; with all of them off it gives results
  bit-identical to the plain `...-reef_a15_veg_strat` image, tested). Its
  copy of `ocean.in` predates the switch and has `Gra`; Batch members
  bring their own `ocean.in` and the test scripts set every switch
  (`tests/north_obc.sh`), so runs never use that copy as is. The
  options: nudged radiation (`RadNud` for
  `LBC(isUvel/isVvel/isTvar)` north; exterior state = the initial
  stratification at rest, from the case's `ana_tobc.h` and ROMS's
  `ana_m3obc.h`); an interior nudging band (`Lm3CLM`, `LtracerCLM`,
  `LnudgeM3CLM`, `LnudgeTCLM` = T; relaxes tracers to the initial state
  (copied at the first call of `ana_tclima.h` / `ana_tobc.h`: after a
  restart that is the restart-time state, so restarted or segmented runs
  nudge toward a drifting state; notebook 2026-10-24, perfect restart)
  and 3-D velocity to rest in a band `USER(3)` m wide, time scale
  `USER(4)` h at the boundary; `ana_tclima.h`, `ana_m3clima.h`,
  `ana_nudgcoef.h`); a viscous/diffusive sponge (`LuvSponge`,
  `LtracerSponge` = T; `USER(5)` m2/s at the boundary, `ana_sponge.h`;
  the grid file's `visc_factor`/`diff_factor` are not used: they sit on
  A15's former east/west walls, which are now the periodic seam).
  `USER = 0.15 12 1000 1 10` (tide amplitude m, period h, band width m,
  nudging time scale h, sponge viscosity m2/s).

Build: `docker build --build-arg COAWST_APPLICATION=REEF_IDEAL_A15
--build-arg CASE_DIR=Projects/Reef_Ideal_A15_veg_strat -t
coawst:reef_a15_veg_strat .`

Limits to keep in mind (details and test results in
`docs/case_design.md`, "Constant stratification"):

- **The internal-wave Courant number limits DT.** The baroclinic step is
  explicit; the first-mode speed is about N H / pi, largest where the
  water is deepest (400 m at the north boundary), and the pass columns
  are 20 m wide. `tools/cfl_check.py` prints the number before a run
  (and the barotropic one, 0.81 here, limit about 0.9 for LF-AM3): 0.39
  for N^2 = 1e-4 at DT 6 s, 0.68 for 3e-4, 1.24 for 1e-3. In the tests,
  runs needed it below about 0.4-0.5 (it adds to advection); 0.68 blew up
  after 34 min even without tide and waves, 1.24 within minutes; DT 3 s
  fixed 3e-4 (0.34). Radiation and sponges at the north boundary only
  delayed those blow-ups by minutes.
- Over 400 m a constant N^2 above about 1.3e-4 needs temperatures outside
  the seawater range (e.g. 2-228 C for 1e-3). With the linear equation of
  state that is harmless (temperature is only a density proxy), but such
  runs are numerical stress tests, not oceans. Stronger stratification
  near the reef with realistic temperatures would need a profile that is
  not constant (e.g. a surface layer over a uniform deep layer).
- The vegetation drag is explicit too (see `cases/Reef_Ideal_A15_veg`).
