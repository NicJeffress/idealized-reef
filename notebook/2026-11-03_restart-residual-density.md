# The 3.7e-7 m/s restart residual: densities frozen at the start time

- **Date:** 2026-11-03
- **Status:** traced and fixed (coawst-cloud `roms-ts-fixed-density`, `423a20f`); restarts bit-identical
- **Builds:** coawst-cloud series of `3227cce` plus a debug patch (checksums,
  [`rst-trace.patch`](patches/rst-trace.patch)); the A15
  canopy case of 2026-11-02/03 (20 m grid, `TS_FIXED`)

## Question / why

After the roller restart fix, a segmented 24 h canopy run was still 3.7e-7 m/s
off the straight one four hours after its restart, where every earlier restart
test had reached round-off or better. The author asked to trace it.

## What was done

1. **Bisection by option**: a one-step test (straight run to step 301 against a
   restart at step 300 plus one step) with each of the new defaults removed in
   turn (`STEP2D_FB_AB3_AM4`, `BSTRESS_IMPLICIT`, `VEG_DRAG_IMPLICIT`,
   `TKE_WAVEDISS`), and with 4 x 2 tiles: every variant still differed after
   one step, at 1e-16 relative, so no single option was the cause.
2. **Checksum trace**: a debug build that writes a bit-exact checksum of about
   60 arrays after each phase of the step, after every barotropic fast step and
   during the initialization, for 100 steps after the restart, in both runs.

## Results

- The restart file and its reading are exact. (The masked boundary row of `u`
  comes back as +0 where the straight run held -0: equal numbers, different bits.)
- After the 3-D right-hand side, every forcing, flux and turbulence field matched;
  the first difference appeared inside the first barotropic fast step, in
  **`rhoA` and `rhoS`**, the depth averages of the density used by the barotropic
  pressure gradient, and these differed from the start of the step.
- Cause: with `TS_FIXED`, `main3d.F` skips `rho_eos` every step, so these fields
  (and the density and buoyancy frequency) are computed once at initialization,
  from the layer depths of that moment. The straight run had them from t = 0;
  the restarted run from the restart time, with another free surface. With the
  uniform density of the canopy case this is a last-bit difference, which grows
  to 3.7e-7 m/s in four hours. The stratified and thermal cases call `rho_eos`
  every step and were not affected.
- (On the way: the AB3-AM4 kernel's fourth time level is not in the restart
  file, but it is not read before it is written, so it does not matter.)
- **Fix** `roms-ts-fixed-density`: `rho_eos` every step with `TS_FIXED` too. The
  restarted run is then bit-identical from its first barotropic step through
  step 405 (a wave exchange included). coawst-cloud test: 60 min straight against
  30 + 30 min, double-precision restart records: before, `u` differs at 443 050
  points; after, `u`, `v`, `ubar`, `vbar`, `zeta` bit-identical; builds without
  `TS_FIXED` unchanged.

## What it means

Segmented (Spot) runs of the A15 canopy and bare cases restart exactly with images
built from coawst-cloud `423a20f` on. The fix changes `TS_FIXED` results only at
round-off.

## Details and links

- coawst-cloud: `roms-ts-fixed-density` (patch, document and test).
- [Roller restarts](2026-11-03_roller-checks.md), [results summary](../results/README.md)
