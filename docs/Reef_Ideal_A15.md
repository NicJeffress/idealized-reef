# Reef_Ideal_A15: idealized fringing reef with a pass

The base case of the family. Folder: [`cases/Reef_Ideal_A15`](../cases/Reef_Ideal_A15).
Application flag `REEF_IDEAL_A15` (all A15 variants use the same flag; the
header in each folder decides the physics).

![Bathymetry](../figures/a15_bathymetry.png)

## Geometry and bathymetry

An alongshore-uniform fringing reef, 6 km long and periodic east-west, cut by
one pass at x = 0. From the coast (south) to the open ocean (north):

| Zone | Cross-shore position (y) | Depth |
|---|---|---|
| land | southern grid row (y = 0) | masked |
| lagoon | 0 to about 0.4 km | 10 m |
| backreef (reef flat) | about 0.5 to 0.9 km | shoaling to about 2 m |
| reef crest | rows 31-34, y = 940-1000 m | 0.50 m |
| forereef | from the crest seaward, slope 1:10 | 7.8 m at 1.1 km, 30 m at 1.35 km, ... |
| open ocean | to the north boundary at y = 5.04 km | 400 m |

The pass is 10 m deep (the lagoon depth) through the crest and backreef, about
380 m wide at crest level (columns 92-110, x = -180 to +180 m) and narrowing to
100 m at its bottom. Seaward of the crest it joins the forereef.

![Cross-reef profile and grid spacing](../figures/a15_profile.png)

The grid and initial file come from the author's COAWST v3.7 project
(`reference/Reef_Ideal_A15_v3.7/Make_grid_Reef_Ideal_A14.m`,
`Make_init_Reef_Ideal_A15.m`) and are unchanged.

## Grid

- ROMS: 203 x 111 rho points (`Lm` 201, `Mm` 109), 10 terrain-following levels
  (`Vtransform` 2, `Vstretching` 4, `THETA_S` 3, `THETA_B` 2, `TCLINE` 20 m).
- Stretched in both directions: dx 20 m at the pass to 40 m at the periodic
  seam (x = ±3 km); dy about 50 m at the coast, 20 m at the crest, 80 m
  offshore. The grid is rectilinear (no `CURVGRID`); the Coriolis parameter in
  the grid file is 0 (`UV_COR` is compiled but has no effect).
- SWAN runs on the same points as ROMS (`CGRID CURVILINEAR 202 110` with A15's
  coordinate file), so no interpolation between the models.

## Physics (header `reef_ideal_a15.h`)

| Process | Option | Notes |
|---|---|---|
| waves on currents | `WEC_VF` (vortex force), `WDISS_WAVEMOD` (breaking dissipation from SWAN), `UV_KIRBY` | spectral Stokes drift (COAWST v3.9's default, summed over SWAN's frequencies); the variant `_bulk` uses bulk Stokes drift |
| bottom stress | `SSW_BBL` with `SSW_CALC_ZNOT`, `SSW_LOGINT`, `SSW_LOGINT_WBL` | wave-current bottom boundary layer; grain diameter 0.12 m in the initial file, `Zob` 0.01 m; implicit since 2026-11-02 (`BSTRESS_IMPLICIT`, coawst-cloud `roms-bstress-implicit`; before: explicit and uncapped, which it equals within 0-3 %), no `LIMIT_BSTRESS` |
| vertical mixing | `GLS_MIXING`, `KANTHA_CLAYSON`, `RI_SPLINES`, `N2S2_HORAVG` | k-epsilon parameters (`GLS_P` 3, `GLS_M` 1.5, `GLS_N` -1) |
| vertical operators | `SPLINES_VDIFF`; `SPLINES_VVISC` off since 2026-11-02 | the implicit bottom stress and canopy drag need the tridiagonal viscous solve |
| momentum advection | `UV_ADV` (3rd-order upstream horizontal, 4th-order centred vertical) | |
| horizontal viscosity | `UV_VIS2`, `VISC_GRID`, `MIX_S_UV`, `VISC2 = 0` | the upstream scheme supplies the lateral viscosity |
| pressure gradient | `DJ_GRADPS` | |
| tracers | `SALINITY`, `TS_FIXED` (T 18 C, S 35), MPDATA advection | the strat and thermal variants let T and S evolve |
| barotropic kernel | AB3-AM4 (`STEP2D_FB_AB3_AM4`, coawst-cloud `roms-step2d-fb`) since 2026-11-02 | within the noise floor of LF-AM3 (ROMS's default) and 19 % faster; before: LF-AM3 |
| vegetation | `#undef VEGETATION` | vegetation input files are present but unused; see `_veg` |
| restarts | `PERFECT_RESTART` | |
| output | `AVERAGES`, `DIAGNOSTICS_UV` | |

Time stepping: `DT` 6 s, `NDTFAST` 24 (barotropic Courant number 0.81; the
AB3-AM4 limit is 0.890, LF-AM3's about 0.9). `NTIMES` 14400 = 24 h.

SWAN (`swan.in`): nonstationary, 72 directions, 21 frequencies 0.04-1.0 Hz,
time step 120 s; `GEN3`, `FRICTION MADSEN 0.3`, `BREAKING CON 1.0 0.73`,
`TRIAD`, `OFF QUAD`, `PROP BSBT`; `COORDINATES CARTESIAN REPEATING` (periodic
in x, like ROMS). Coupling every 600 s through MCT (`coupling.in`), so 100
ROMS steps and 5 SWAN steps per exchange.

## Forcing and boundaries

- **Waves:** JONSWAP (gamma 3.3), Hs ramped from 0.125 m to 1.0 m over the
  first 30 min, Tp 10 s, from the north, 4 degree directional spread, on the
  north boundary only (`wavebc_north.txt`, TPAR format). `wavebc_east.txt` and
  `wavebc_west.txt` are left from the non-periodic v3.7 setup and unused.
- **Tide:** zeta at the north boundary = -0.15 sin(2 pi t / 12 h)
  (`ana_fsobc.h`, `REEF_IDEAL_A15` branch). The flow settles into a repeating
  12 h cycle by about hour 12.
- **ROMS boundaries:** east-west periodic; south closed; north: Chapman (sea
  level), Shchepetkin (2-D momentum), zero gradient (3-D momentum, tracers,
  TKE). No wind, no surface heat or salt flux.
- **SWAN boundaries:** periodic in x; waves enter along the north edge
  (`BOUNDPAR2 SEGMENT IJ 0 110 201 110`).

## Outputs

ROMS writes history, averages, diagnostics and restart files hourly
(`NHIS`, `NAVG`, `NDIA`, `NRST` = 600 steps) under `output/`; history includes
the WEC stresses, Stokes drift and wave fields. SWAN writes `BLOCK 'COMPGRID'`
NetCDF fields (Hs, direction, periods, dissipation terms, radiation stress,
...) at the end of the run and a restart file hourly. As configured, a
simulated day makes about 2.85 GB (restart 1.24 GB, diagnostics 0.82 GB,
history 0.51 GB, averages 0.47 GB) in classic NetCDF; compressed NetCDF-4
output is about 3x smaller.

## Known results

- **Port from v3.7 to v3.9** ([notebook](../notebook/2026-10-20_reef-a15-port-to-v39.md)).
  ROMS is the bottleneck, not SWAN; most ROMS time is the WEC kernel
  (spectral Stokes drift recomputed every step). v3.9's spectral Stokes drift
  is a physics difference from the v3.7 runs (bulk Stokes).
- **Periodic SWAN** ([notebook](../notebook/2026-10-21_a15-coupled-periodic-test.md)).
  With non-periodic SWAN, ROMS's periodic seam received mismatched wave forcing:
  a 58 mm/s jump in the alongshore depth-mean current at the seam and up to
  0.32 m different crest Hs near the sides. With periodic SWAN the seam is
  clean (Hs jump 0.02 mm, current jump 2 mm/s, like neighbouring columns).
  SWAN's period is one 40 m column longer than ROMS's (the coupler passes ROMS
  columns 0..201); harmless here (< 0.1 mm in Hs).
- **24 h on Cloud Batch** ([notebook](../notebook/2026-10-21_a15-periodic-batch-24h.md)):
  no NaN, seam clean all day (zeta within 6e-6 m), Hs up to 1.8 m over the pass,
  pass jet 0.88 m/s, tide range -0.17 to +0.20 m.
- **Speed** ([notebook](../notebook/2026-10-21_a15-split-tiling-benchmarks.md)):
  best on c2d-standard-16 with 10 ROMS (tiles 1 x 10) + 6 SWAN processes,
  68 s wall per simulated hour (a week in about 3.2 h). C2D machines were
  25-30 % faster than C3D. 1 x N tilings give bit-identical results across
  tilings; results are bit-identical across CPU types (EPYC 7B13 vs 9B14).
- **Exact restarts** ([notebook](../notebook/2026-10-24_perfect-restart-spot.md),
  [turbulence halo](../notebook/2026-10-31_restart-residual-turbulence-halo.md)):
  with coawst-cloud's `roms-restart-wec` and `swan-exact-restart`, a run
  stopped and restarted continues as the uninterrupted one to round-off
  (base A15: 5.8e-11 m/s), which allows cheap interruptible (Spot) machines.
- **AB3-AM4 barotropic kernel** (`STEP2D_FB_AB3_AM4`, coawst-cloud
  `roms-step2d-fb`): in 1 h tests as close as LF-AM3 to a 4x-smaller-step
  reference, 2-D kernel 2.4-2.6x less CPU; wall time 4-5 % less with 6 + 2
  processes because SWAN then sets the pace
  ([notebook](../notebook/2026-10-24_ab3-am4-barotropic-kernel.md)).
- **Bottom stress** on the default and thinner crests: the uncapped explicit
  stress, the implicit stress (`BSTRESS_IMPLICIT`) and DT 3 s agree; the
  `LIMIT_BSTRESS` cap changes the answer and depends on DT. See
  [thin-crest variants](Reef_Ideal_A15_thin_crest.md).
- **Grid convergence and other numerics:** the options test campaign, phase 0
  (DT, NDTFAST, SWAN step and iterations, coupling interval, spectral
  resolution, tiling, the 10 m grid), results to come in [`results/`](../results).

## Caveats

- `UV_COR` is defined but f = 0 in the grid file: no rotation.
- The original v3.7 project's numbers in some old notes (crest 0.63 m at
  600 m) came from a coarse profile; the grid's crest is 0.50 m at 940-1000 m
  ([notebook](../notebook/2026-10-23_a15-crest-depth.md)).
- SWAN's directional spreading at the boundary is narrow (4 degrees), as in the
  v3.7 project.
- With varying alongshore spacing (20-40 m), SWAN's Hs varies by about 0.1-0.2 %
  along an alongshore-uniform crest (finer mesh, higher Hs), periodic or not
  ([Swan_Periodic_Test](Swan_Periodic_Test.md)).
- `ocean.in` sets `NtileI 4 x NtileJ 2` and `coupling.in` 8 ROMS + 4 SWAN; set
  your own layout (both files) for your machine.
- `VARNAME` in `ocean.in` points to `/opt/coawst/ROMS/External/varinfo.yaml`
  (the path inside coawst-cloud images); change it for other builds.
