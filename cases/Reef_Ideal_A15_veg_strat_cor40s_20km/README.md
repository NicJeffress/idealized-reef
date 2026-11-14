# Reef_Ideal_A15_veg_strat_cor40s_20km: stratified A15 canopy case, 40 S rotation, domain extended to 20 km offshore

f = -9.3745e-5 s-1 (40 S, exaggerated), as `Reef_Ideal_A15_veg_strat_cor40s`.

The grid is extended offshore with `tools/reef/extend_a15_grid.py` (2026-11-13, author: "lets do flat at
400m ... Lets fire off a 20km run with f=0 and 40 deg S"): every row of the 5 km grid kept, 86 rows added
beyond it, so the north boundary is at 19.87 km (203 x 212 rho points). Row spacing 80 m at 5 km, growing
1 % per row to 120 m by 10 km (the part looked at), then 4 % per row to 400 m (a buffer, from about 15.6 km).
The 1:10 fore-reef slope stops at 400 m (5.04 km) and the bottom is flat beyond; barotropic Courant 0.81 as
before (deeper would need a shorter fast step). Interior nudging band `USER(3)` 4000 m instead of 1000 m, so
it still spans about 10 rows of the 400 m spacing. Stratification as before (N² 1e-4, 28 C at the surface,
`tools/stratification/make_strat_init.py`). Why: the stratified surface jet reached the 5 km boundary within
about 12 h at both f = 0 and 40°S. Runs use the image built from
`Reef_Ideal_A15_veg_strat_cor40s`; the run spec copies this folder's grid, initial and SWAN files over the
image's.

Made with

    ~/venv/bin/python -I tools/reef/extend_a15_grid.py cases/Reef_Ideal_A15_veg_strat_cor40s cases/Reef_Ideal_A15_veg_strat_cor40s_20km --nudge-band 4000
    C=cases/Reef_Ideal_A15_veg_strat_cor40s_20km; ~/venv/bin/python -I tools/stratification/make_strat_init.py 1e-4 --case $C --base $C/init_reef.nc -o $C/init_strat.nc --t-surface 28 && mv $C/init_strat.nc $C/init_reef.nc

The rest of this file is the parent case's README (its grid sizes are the 5 km grid's).

---

# Reef_Ideal_A15_veg_strat_cor40s: stratified A15 canopy case with exaggerated rotation (40 S)

`Reef_Ideal_A15_veg_strat` (density 1 m-2 canopy, constant N^2 = 1e-4 s^-2: 28 C at the
surface, linear to about 5 C at 400 m, uniform salinity; a rough warm-season profile for
a tropical South Pacific reef; north boundary nudged toward the initial state) with a uniform Coriolis
parameter at 40 deg S, more than twice that at 17.5 deg S (to make the pass jet bend inside the
domain for the particle-tracking figure; no reef sits this far south):

    f = 2 x 7.2921e-5 x sin(-40 deg) = -9.3745e-5 s-1   (inertial period 18.6 h)

**Only the grid file differs from `Reef_Ideal_A15_veg_strat`** (the `f` variable). Made with

    ~/venv/bin/python -I tools/reef/set_coriolis.py cases/Reef_Ideal_A15_veg_strat cases/Reef_Ideal_A15_veg_strat_cor40s --lat -40

The image is built from this folder (the stratified header and analytical files);
f is read from the grid at run time. First run: `a15scor40s168`, 7 days on Spot in 6 h
segments, 15 min 3-D history from hour 24.

The rest of this file is `Reef_Ideal_A15_veg_strat`'s README.

---

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
>
> **Spectral Stokes drift updated every 120 s since 2026-11-06** (`STOKES_INTERVAL`, `STOKES_NCPL` 5, coawst-cloud
> `roms-stokes-interval`; 2.2x faster, tested on density 1; needs an image built after this date to take effect).


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
[`docs/Reef_Ideal_A15_veg_strat.md`](../../docs/Reef_Ideal_A15_veg_strat.md), "Known results"):

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
