# Reef_Ideal_A15_veg: A15 with constant submerged vegetation

> **Grid and roller since 2026-11-03 (author's decisions).** The default grid is
> the breaking-zone grid: 203 x 126 rho points, the rows between 850 and 1150 m
> from the shore (crest, breaking zone, top of the fore reef) split in two (10 m
> across the shore, 20 m elsewhere), DT 6 s kept (barotropic Courant 0.81).
> Made from the 20 m grid (203 x 111, this folder before 2026-11-03 in git) with
> `tools/reef/refine_a15_grid.py --band 850 1150 --factor 2`; it recovers the
> uniform 10 m answer at +16 % cost (notebook 2026-11-03_grid-10m). Row numbers
> quoted below refer to the 20 m grid. The Reniers roller is on
> (`ROLLER_RENIERS`, `WEC_ALPHA` 0.5; notebook 2026-11-03_roller-checks). Also since
> 2026-11-03: 15 vertical levels (was 10), `GLS_Kmin` 1e-8, SWAN `BKD` breaking and wave
> streaming (`BOTTOM_STREAMING`; `VEG_STREAMING` with the canopy).


> **Vegetation elements are cylinders: `plant_thickness = (pi/4) x
> plant_diameter`** (user's convention, 2026-10-21). ROMS uses diameter x
> thickness as each plant's footprint; for cylinders that must be pi D^2/4.
> See "Periodic SWAN and an open problem with the canopy" below.

Same as `cases/Reef_Ideal_A15` (application REEF_IDEAL_A15, so the A15
tide branch applies), plus canopy drag everywhere (user's test, 2026-10-20):

- Header: VEGETATION, VEG_DRAG, VEG_TURB, VEG_SWAN_COUPLING on (VEG_FLEX,
  VEG_STREAMING off).
- `init_reef.nc`: plant_density 4 m-2, plant_diameter 0.5 m, plant_height
  0.4 m everywhere (frontal area per bed area lambda_f = 4 x 0.5 x 0.4 =
  0.8); plant_thickness = (pi/4) x 0.5 = 0.3927 m (cylinders, bed
  coverage pi D^2 n / 4 = 0.785). It was 0.5 m until 2026-10-21, which
  made D t n = 1 and ROMS blow up. The reef crest is 0.50 m deep
  (rows 31-34 of the grid), 0.35 m at low tide (0.15 m tide), so the
  0.4 m canopy reaches the surface on the crest around low tide (ROMS
  then applies the drag over the whole water column; SWAN needed patch
  item 16 for it); the user's first idea, 0.5 m, would reach the
  surface there at mean sea level. (Corrected 2026-10-23: this note
  said 0.63 m deep and a submerged canopy, from a coarse depth profile.)
- `swan.in`: `VEGETATION 3 0.4 0.5 1 1` since 2026-10-22 (Mendez &
  Losada in COAWST's `SVEG_COAWST`: density, height, diameter and
  thickness at each point come from ROMS's plant fields via the coupler,
  so they may vary in space; the last value is the drag method, 1 = Cd
  1.0 = CD_VEG in vegetation.in; the height/diameter/stems given are not
  used). Before: `VEGETATION 1 0.4 0.5 1 1.0` (height and diameter fixed
  by the command, only the density from ROMS). With the constant canopy
  both give the same result to single-precision rounding (tested
  2026-10-22, below). `INPGRID NPLANTS` stays (it switches on the
  spatial density); the .bot vegetation files and the NPHT/NPDA/NPTK
  grids are gone (as in COAWST's Veg_test).
- Spatially varying canopies (presence/absence, amount by zone, random
  patches): `tools/vegetation/make_veg_init.py` writes them into a copy
  of `init_reef.nc`; see `tools/vegetation/README.md` and "Spatially
  varying vegetation" below. The `init_reef.nc` here keeps the constant
  canopy.

Build: `docker build --build-arg COAWST_APPLICATION=REEF_IDEAL_A15
--build-arg CASE_DIR=Projects/Reef_Ideal_A15_veg -t coawst:reef_a15_veg .`

## Periodic SWAN and an open problem with the canopy (2026-10-21)

`swan.in` is periodic as in `cases/Reef_Ideal_A15` (`REPEATING`, north
boundary `IJ 0 110 201 110`, east/west boundaries commented out). Image
`coawst:reef_a15_veg_per` (local), SWAN patch items 1-15.

**With thickness 0.5 m (= diameter) the canopy made ROMS blow up, periodic
SWAN or not; thickness is now (pi/4) x diameter.**
`VEG_TURB` (Uittenbogaard 2003, as in Beudin et al. 2017 and Table 1 of
Kalra et al. 2017, GMD 10:4511) uses the eddy size between plants
L = c_l ((1 - b t n)/n)^(1/2), with b = diameter, t = thickness,
n = density. Here b t n = 0.5 x 0.5 x 4 = 1, so L = 0, the vegetation
dissipation time scale tau_veg = (L^2/(c_k^2 P_veg))^(1/3) = 0 and the
source c_2 P_veg / tau_eff added to epsilon is infinite. The infinities
show up at ROMS's periodic seam (sea level dip, doubled cross-shore
current at column 201) and the run blows up after 1 h 44 min. Kalra et
al. used seagrass with b t n below 0.0025. Plant thickness enters only
this term (drag and SWAN use diameter, density and height).

Tested with thickness 0.39 m (pi/4 x diameter: b t = the area of a 0.5 m
cylinder, solid fraction 0.785), given as an override
(`tests/a15_periodic_test.sh` with `init_reef.nc` mounted): 3 h coupled
runs complete, seam clean in both models (sea level < 0.001 mm, currents
like neighbouring columns), ROMS gets exactly SWAN's Hs and the plant
density SWAN gets equals ROMS's. With non-periodic SWAN ROMS's alongshore
current jumps 11 mm/s at its seam. Choice of canopy parameters and of a
code safeguard: see below.

**Since 2026-10-21 (`patches/roms-vegetation.patch` items 2-3):** ROMS
stops on the first step with a message if diameter x thickness x density
>= 1 anywhere (tested: the old 0.5 m canopy stops after 2 s), and the
barotropic vegetation drag on v uses the right depth average. Rebuilt
image `coawst:reef_a15_veg_per` (local; case init with thickness
pi/4 x 0.5 m): 3 h coupled runs with A15's waves and with waves from
20 deg complete with a clean periodic seam in both models (sea level
< 0.001 mm, currents like neighbouring columns); with non-periodic SWAN
ROMS's alongshore current jumps 11 mm/s at its seam.

Since 2026-10-21 (item 4) tau_veg uses the plant work per unit mass, as
published; before, it was 1.6-3 times too long here. Effect in the 3 h
periodic run (canopy medians): TKE -3 %, epsilon +2 %, eddy viscosity -7 %
(-14 % at the 10th percentile); currents change by at most 4 mm/s, Hs by
under 0.5 mm (canopy currents are weak here, about 2 cm/s).

**Kept as shipped (user's decision, 2026-10-21; to revisit eventually):**
`vegetation_turb.F` never uses the
free-turbulence time scale (`inverse_dissip = MAX(1/dissip, max_eps)`, so
tau_eff = tau_veg always); `MIN(1/dissip, max_eps)` and the pre-2023
`1/MAX(dissip, eps)` would behave the same here (GLS keeps epsilon >=
1e-12). History and details in `patches/README.md` (roms-vegetation.patch);
`tests/veg_timescales.py` compares the time scales in a run. Tested: the
2023 edit also reuses `cff2` (the epsilon exponent) for tau_veg, so MIN
alone changes nothing; MIN plus a separate variable restores tau_free and
lowers canopy TKE by 42 % and eddy viscosity by 65 % (medians), currents
by up to 2 cm/s (`tests/veg_compare.py`).

## Spatially varying vegetation (2026-10-22)

`swan.in` now uses `VEGETATION 3`, so SWAN takes density, height and
diameter at each point from ROMS (above). Patterns are written into a
copy of `init_reef.nc` by `tools/vegetation/make_veg_init.py`; tests in
`tests/veg_spatial_tests.sh` / `tests/veg_spatial_check.py`, results and
figure in `docs/case_design.md` ("Spatially varying vegetation"). In
short: constant canopy, bare reef and the zones pattern run cleanly at
DT 6 s (zones also 24 h on Batch); the patchy pattern blows up at DT 6 s
after 42 min because ROMS's vegetation drag is explicit, and runs at
DT 3 s (`DT=3` in `tests/a15_periodic_test.sh`; in ocean.in set
`DT == 3.0d0`, `NDTFAST == 12` and halve the output intervals in steps).
Kept explicit by the user's decision (2026-10-22).

Image: `us-central1-docker.pkg.dev/coawst-runs/coawst/coawst:reef_a15_veg`
(= `v3.9-26e6fb7-reef_a15_veg-dicd`, sha256:dd15f392..., SWAN items
1-17, `VEGETATION 3`). The earlier push `v3.9-26e6fb7-reef_a15_veg`
(sha256:7a437bc7..., items 1-16) gives the same model results (only the
DICD output differs); `batch/ensemble/tests/veg-spatial-24h` ran on it.
