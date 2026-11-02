# VEG_TURB: the canopy time scale tau_veg had the wrong units (tau_veg_units)

- **Date:** 2026-10-21
- **Status:** done; `tau_veg_units` in coawst-cloud's `roms-vegetation`

## Question / why

While tracing the `VEG_TURB` blow-up (cylinder entry), the canopy
turbulence code was read line by line against the papers that describe it
(Uittenbogaard 2003; Beudin et al. 2017; Kalra et al. 2017).

## What was run

- Code reading of `ROMS/Nonlinear/Vegetation/vegetation_turb.F` back to
  COAWST v3.4.
- `tests/veg_timescales.py`: tau_free = k/epsilon and tau_veg (published
  form and as coded) inside the canopy, from a ROMS history file.
- 3 h periodic A15 vegetation run with the fix against the old code
  (tau_free off in both), on the control VM; `tests/veg_compare.py`.

## Results

- The plant work `tke_loc_veg` is built from a drag that includes the
  layer thickness Hz, so it is work integrated over the cell (m3/s3).
  That is right for ROMS's Hz-weighted TKE and epsilon updates, but
  tau_veg = (L^2/(c_k^2 P_veg))^(1/3) needs work per unit mass (m2/s3).
  As coded, tau_veg was Hz^(-1/3) times the published value: 1.6-3 times
  too long in A15's 4-26 cm canopy layers, since the original
  implementation (v3.4 checked). The vegetation dissipation source was
  therefore too weak.
- Fix: tau_veg uses the work divided by the w-cell thickness
  0.5 (Hz(k) + Hz(k+1)), the weight `gls_corstep` uses; the TKE and
  epsilon sources are unchanged.
- Effect in the 3 h run (canopy medians): TKE -3 %, epsilon +2 %, eddy
  viscosity -7 % (-14 % at the 10th percentile); currents change by at
  most 4 mm/s, Hs by under 0.5 mm (canopy currents about 2 cm/s).
- The rebuilt image's binary is identical to the tested one.

## Decision / outcome

Kept (`tau_veg_units`). The project conventions: "tau_veg itself has the units fix".

## Open questions

- Not reported upstream.

## Details and links

- coawst-cloud's patch document `roms-vegetation` (`tau_veg_units`)
- [`docs/Reef_Ideal_A15_veg.md`](../docs/Reef_Ideal_A15_veg.md)
- Related: [tau_free](2026-10-21_veg-turb-tau-free.md), [cylinder convention](2026-10-21_vegetation-cylinder-convention.md)
