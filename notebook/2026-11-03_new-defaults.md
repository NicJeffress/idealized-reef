# New A15 defaults: the roller and the breaking-zone grid

- **Date:** 2026-11-03
- **Status:** adopted (the author's decisions); CTHETA and vertical-resolution tests running
- **Builds:** coawst-cloud `3227cce` (roller sub-steps and roller restart);
  image `v3.9-cc3227cce-reef_a15_veg-def1103b` for the canopy case

## Question / why

After the roller checks ([roller](2026-11-03_roller-checks.md)) and the grid
tests ([grid](2026-11-03_grid-10m.md)), the author reviewed the open
modelling choices and made these defaults.

## What changed

- **Reniers roller on** in every A15 case: `ROLLER_RENIERS`, `WEC_ALPHA`
  0.5. It shifts breaking momentum onto the crest and reef flat (set-up
  +25 %, crest transport +15 % on the 20 m grid, more on the refined grid)
  and makes the answer less grid-sensitive. It needs the coawst-cloud fixes
  `roms-roller-substeps` (stable at DT 6 s) and `roms-restart-roller` (exact
  restarts), so only images built from coawst-cloud `3227cce` on.
- **Breaking-zone grid** replaces the 20 m grid in `Reef_Ideal_A15`,
  `_bulk`, `_veg`, `_veg_strat` and `_veg_therm`: 203 x 126 rho points, the
  rows between 850 and 1150 m from the shore (crest, breaking zone, top of
  the fore reef) split to 10 m across the shore, DT 6 s kept (barotropic
  Courant 0.81). It recovers the uniform 10 m answer (set-up and pass
  transport exactly, jets within 1-2 %) for +16 % cost instead of 8x.
  Made with `tools/reef/refine_a15_grid.py --band 850 1150 --factor 2`,
  which now also interpolates non-uniform initial fields and regenerates
  the bare cases' SWAN plant files; the stratified and thermal initial
  temperatures were rewritten exactly on the new grid with
  `tools/stratification/make_strat_init.py` (N² 1e-4). The new
  `Reef_Ideal_A15_veg` is byte-identical to the grid tested on 2026-11-03.
  The 20 m cases remain in the git history. Analyses that pick regions by
  row number must map them by distance from the shore instead.
- **Bed roughness and canopy**: the options note had "bed roughness or
  canopy drag, never both". The author's view: usually one or the other,
  but a suggestion, not a rule (a reef can be a rough bed and a canopy at
  once). The canopy cases keep both (`grain_diameter` 0.12 m, z0 1 cm, and
  the canopy). In the 8 h density-1 canopy run, bottom friction took 36 %
  of SWAN's wave dissipation over the reef, the canopy 27 % and breaking
  37 %.
- `UV_BANIHASHEMI` had already been tested (within 0.5 % of `UV_KIRBY`,
  [entry](2026-11-03_veg-hmixing-and-banihashemi.md)); the options note
  still listed it as "to test" and now records the result.

## Tests started with the new defaults

- **SWAN limiters** (band grid, roller, 24 h; done: no effect, [entry](2026-11-03_swan-limiters.md)): current settings,
  `NUM CTHETA 0.9`, `NUM CTHETA 0.9 CSIGMA 0.9`, `NUM DIRIMPL 1`.
- **Vertical resolution** (band grid, roller, 24 h): N 10, 15 and 20 at
  DT 6 s, and N 20 at DT 3 s (the crest layers are 2.5 cm at N 20).
- **Wave streaming** (`BOTTOM_STREAMING`, `VEG_STREAMING`): bottom friction
  and the canopy remove 63 % of the wave energy on the reef, but only the
  breaking part reaches the mean flow without these options. Their code
  needs fixes first (coawst-cloud `roms-veg-streaming-fixes`, being tested).

## Decision / outcome

Adopted: roller, band grid, roughness as a suggestion, and `GLS_Kmin` 1e-8
(1e-8 and 1e-10 agree to three digits; [72 h runs](2026-11-03_kmin-heated-72h.md)).
Noted for later: `UV_BANIHASHEMI` may replace `UV_KIRBY`; check whether it is
needed on every new domain (sheared currents with waves spanning kD ~ 1).

## Details and links

- [Results summary](../results/README.md)
- Cost of the two Batch tests: about $1.
