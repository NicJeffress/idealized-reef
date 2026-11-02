# Options test campaign, phases 1 and 2: setup and submission

- **Date:** 2026-11-02 (evening)
- **Status:** done except the thermal members; results in
  [the phases 0-2 results entry](2026-11-02_options-campaign-results-p0-p2.md)
- **Builds:** coawst-cloud `9d93a75`; one image per cpp option

## Question / why

Phase 1 tests the physics that drives the reef (wave breaking, triads,
whitecapping on currents, wave-breaking turbulence, the roller, stability
functions, the equation of state) on the vegetated, stratified and heated A15
cases; phase 2 tests the bottom-stress and canopy-drag numerics. Each candidate
is judged against the phase 0 noise floor (the DT 3 s run). Phases 1 and 2 were
started in parallel with phase 0 to save wall time; the decisions wait for the
phase 0 envelope.

## What was run

All 24 h, c2d-standard-16 Spot, 10 ROMS + 6 SWAN processes, 4 h restart
segments, unless stated. Baseline as in phase 0 (DT 6 s, NDTFAST 24, SWAN
`BREAKING CON 1.0 0.73`, `TRIAD`, `GEN3` Komen whitecapping).

| Job (image) | Case | Members: change |
|---|---|---|
| options-p1a (base) | A15_veg | p1-g080 `BREAKING CON 1.0 0.80`; p1-bkd `BREAKING BKD 1.0 0.54 7.59 -8.06 8.09`; p1-tg `BREAKING TG 1.0 0.42 4.0`; p1-notriad no `TRIAD`; p1-abcur `WCAP AB 5.0e-5 1.75e-3 CURRENT` |
| options-p1a-tkew (`+TKE_WAVEDISS +ZOS_HSIG`) | A15_veg | p1-tkew; p1-tkew-g080 (with gamma 0.80) |
| options-p1a-roller (`+ROLLER_RENIERS`) | A15_veg | p1-roller, `WEC_ALPHA` 0.5; one unsegmented run (the roller has not been through the restart tests) |
| options-p1s (base strat) | A15_veg_strat | p1s-base; p1s-bkd; p1s-kmin `GLS_Kmin` 1e-8; p1s-rest (no tide, Hs 0.001 m) |
| options-p1s-tkew | A15_veg_strat | p1s-tkew |
| options-p1s-novt (`-VEG_TURB`) | A15_veg_strat | p1s-vegturb-off, at rest (against p1s-rest: the backreef diffusivity of 1e-3 m2/s at rest) |
| options-p1s-canuto (`+CANUTO_A -KANTHA_CLAYSON`) | A15_veg_strat | p1s-canuto |
| options-p1t (base therm) | A15_veg_therm | p1t-base, 72 h; p1t-rest, 24 h, no tide, no waves, no heat flux |
| options-p1t-tkew | A15_veg_therm | p1t-tkew, 72 h |
| options-p1t-nleos (`+NONLIN_EOS`) | A15_veg_therm | p1t-nleos, 72 h; p1t-nleos-rest, 24 h at rest (pressure-gradient check against p1t-rest; the 72 h run counts only if the rest run is as clean as the linear one) |
| options-p2 (base) | A15_veg | p2-bare-exp, bare reef (canopy code compiled, density 0); p2-patchy-exp3, patchy canopy at DT 3 s |
| options-p2-bsimp (`+BSTRESS_IMPLICIT -SPLINES_VVISC`) | A15_veg | p2-bare-imp |
| options-p2-limbs (`+LIMIT_BSTRESS`) | A15_veg | p2-bare-cap |
| options-p2-vegimp (`+VEG_DRAG_IMPLICIT -SPLINES_VVISC`) | A15_veg | p2-patchy-imp6, p2-const-imp6 (DT 6 s) |

The thermal members make their far-field column (`tools/thermal/far_field.py`)
for their own forcing and run length. The far-field column uses the linear
equation of state, so the nudging band of p1t-nleos relaxes toward a column
computed with the linear one (small, but a difference).

## Not run: two options that do not compile in COAWST v3.9

- **`VEG_HMIXING`** (planned p2-hmix, edge viscosity at canopy patches):
  `hmixing.F` and `step2d_LF_AM3.h` use the module `vegetation_hmixing_mod`,
  which no source file in v3.9 defines. The build stops at `hmixing.o`.
- **`UV_BANIHASHEMI`** (planned p1-bani, wave-number-dependent current to
  SWAN): `mod_average.F` declares `avguwav` and `avgvwav` twice with this
  case's options (`Component 'avguwav' already declared`, rank mismatches).

Both are upstream bugs; candidates for coawst-cloud patches if either option is
wanted.

## Results

Pending.

## Decision / outcome

Pending (decision rules: breaking becomes an ensemble axis if the three
formulations spread set-up or crest transport by more than about 10 %;
`TKE_WAVEDISS + ZOS_HSIG` adopted if stable and less crest shear; implicit
canopy drag adopted if within the phase 0 noise of explicit DT 3 s).

## Details and links

- [Phase 0 entry](2026-11-02_options-campaign-phase0.md)
- [Implicit vegetation drag](2026-10-27_implicit-vegetation-drag.md),
  [thin-crest bottom stress](2026-11-02_a15-thin-crest-bottom-stress.md)
