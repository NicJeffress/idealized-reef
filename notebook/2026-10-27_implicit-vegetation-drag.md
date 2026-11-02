# Implicit vegetation drag (VEG_DRAG_IMPLICIT)

- **Date:** 2026-10-27
- **Status:** done on A15

## Question / why

The explicit canopy drag 0.5 Cd D n |U| U blows up when 2 alpha |U| DT is well
above 1 (alpha = 0.5 Cd D n = 1 m-1 for the dense class): on A15 the patchy
canopy at DT 6 s (blow-up at 42 min, [2026-10-22 entry](2026-10-22_spatial-vegetation-patterns.md)),
and, with fast flow from bare crest gaps into dense patches, a number near 10
on a realistic reef grid. The author asked for an implicit drag (step3d_uv plus
the barotropic drag at every fast step), tested on A15 patchy first.

## What was run

- coawst-cloud's `roms-veg-implicit` (cpp option `VEG_DRAG_IMPLICIT`;
  details in its patch document): drag coefficients
  stored by vegetation_drag.F, drag out of rhs3d.F, backward Euler in
  step3d_uv.F after the vertical viscosity and in both barotropic kernels
  (LF-AM3: first/predictor/corrector; AB3-AM4) at every fast step, with a
  barotropic coefficient that keeps the canopy flow profile.
- A15 image `coawst:reef_a15_veg_vegimp` (`sha256:bedfc482...`,
  `+VEG_DRAG_IMPLICIT`); Batch `a15-vegimp-6h` (patchy DT 6 s, patchy
  DT 3 s, constant DT 6 s) and the explicit reference `a15-vegexp-6h`
  (patchy DT 3 s, constant DT 6 s; image `sha256:f9884cb4...`), 6 h each,
  Spot c2d-standard-16 in us-east4.

## Results

- Patchy at DT 6 s ran 6 h with the implicit drag (explicit: blow-up at
  42 min). Wall 398 s against 658 s for the explicit drag at its stable
  DT 3 s (1.65x faster).
- Differences at 6 h (depth-averaged currents): patchy DT 3 s implicit vs
  explicit, 99.9 % of cells within 0.6-0.7 cm/s, RMS 1-2 % of RMS speed;
  implicit DT 6 s vs explicit DT 3 s, within 1.0-1.3 cm/s, 2-4 %, largest
  2.3 cm/s and Hs 4 cm; constant canopy within 0.3-0.8 cm/s (8-10 % of very
  weak flow, at a reef-flank spot). Canopy TKE/eps/AKv medians unchanged
  (ratio 1.00-1.02); 90th percentile of the TKE ratio 1.13-1.48.
- Tables: coawst-cloud's patch document `roms-veg-implicit`.
- Note: COAWST's ROMS also has an implicit vertical advection
  (`OMEGA_IMPLICIT`); it was tested on A15 on 2026-10-22 and gave wrong
  solutions ([2026-10-22 entry](2026-10-22_constant-stratification-courant.md)),
  so it is not a fix for these blow-ups.
- Cost: about $0.20 (5 x ~8-11 min of c2d-standard-16 Spot in us-east4).

## Decision / outcome

> **VEG_DRAG: explicit by default; `VEG_DRAG_IMPLICIT` for patchy or dense
> canopies** (author: explicit 2026-10-22; implicit option implemented on the
> author's request 2026-10-27, build arg `CPP_OPTIONS="+VEG_DRAG_IMPLICIT"`).

## Open questions

- A build without the option is unchanged by construction; not checked by
  compiling twice.
- Whether the dense-canopy and A15 default runs should move to the
  implicit drag too (they are stable explicitly).

## Details and links

- coawst-cloud's patch document `roms-veg-implicit`
- [docs/Reef_Ideal_A15_veg.md, explicit vegetation drag](../docs/Reef_Ideal_A15_veg.md)
