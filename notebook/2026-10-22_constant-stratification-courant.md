# Constant stratification in A15: the internal-wave Courant limit

- **Date:** 2026-10-22
- **Status:** done

## Question / why

The author's request: a version of the model initialised with constant
stratification, tried with reasonable and extreme values. A15 itself
froze temperature and salinity (`TS_FIXED`, 18 C and 35).

## What was run

- `cases/Reef_Ideal_A15_veg_strat`: the vegetation case with T/S evolving,
  run-time tide (`USER(1:2)`), north-boundary options (all off here).
- `tools/stratification/make_strat_init.py`: with A15's linear equation of
  state (R0 1027, Tcoef 1.7e-4 /C) constant N^2 is a linear temperature
  profile; N^2 = 1e-4 s^-2 is 28 C at the surface to 5.4 C at 400 m.
- `tools/cfl_check.py` (Courant numbers before a run); `tests/strat_tests.sh`
  (3 h each, A15's waves and tide, control VM), `tests/strat_check.py`.
  Case image `v3.9-26e6fb7-reef_a15_veg_strat` (`sha256:24d30199...`).

## Results

Internal-wave Courant number (maxima at the 400 m deep north boundary in
the 20 m pass columns; barotropic 0.81 everywhere, limit about 0.9):

| N^2 (s^-2) | DT 6 s | DT 3 s | Outcome |
|---|---|---|---|
| 0 | 0 | - | clean; matches the TS_FIXED case to rounding (u 2e-6 m/s) |
| 1e-5 | 0.12 | - | clean |
| 1e-4 | 0.39 | 0.20 | clean at 6 s for 3 h |
| 3e-4 | 0.68 | 0.34 | 6 s blew up at 34 min (also without tide and waves); 3 s clean |
| 1e-3 | 1.24 | 0.62 | 6 s blew up at 4.5 min; 3 s ran but the deep north became garbage |
| 3e-3 | 2.15 | 1.08 | 6 s blew up at 1.6 min |

- Did not fix it (N^2 3e-4, DT 6 s): Rad, RadNud, a nudging band or both
  (blow-up delayed to 37-47 min); a viscous sponge (failed at 17 min).
  `OMEGA_IMPLICIT` ran 3 h with a wrong solution (5 m/s and 15 C errors
  at the boundary): it turns a crash into a silent bad run.
- At rest with N^2 = 1e-4 the pressure-gradient error over A15's slopes
  stays below 0.4 cm/s over 24 h.
- Above about 1.3e-4 over 400 m the "temperatures" leave the seawater
  range (only a density proxy with the linear equation of state).

## Decision / outcome

Keep the internal-wave Courant number below about 0.4-0.5; use DT 3 s for N^2 = 3e-4. Not recommended: `OMEGA_IMPLICIT`.

## Open questions

- On the 2 m backreef the vertical diffusivity at rest is about 1e-3 m2/s
  (background elsewhere 5e-5): stratification on the reef flat erodes
  within hours without forcing; cause not traced.

## Details and links

- [docs, Constant stratification](../docs/Reef_Ideal_A15_veg_strat.md); [case README](../docs/Reef_Ideal_A15_veg_strat.md); Next: [north boundary over 24 h](2026-10-22_stratified-north-boundary-24h.md)
