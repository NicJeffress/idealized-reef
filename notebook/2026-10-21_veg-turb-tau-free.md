# VEG_TURB never uses the free-turbulence time scale (tau_free)

- **Date:** 2026-10-21
- **Status:** decision (author): keep as shipped; to revisit

## Question / why

The published canopy turbulence model uses tau_eff = min(tau_free,
tau_veg) with tau_free = k/epsilon. In COAWST v3.9's `vegetation_turb.F`,
`inverse_dissip = MAX(1/dissip, max_eps)` with `max_eps` = 1e14, so
tau_free >= k x 1e14 s and tau_eff = tau_veg always. Is that intended, and
how much does it matter?

## What was run

- COAWST history: v3.2-v3.7 had `1/MAX(dissip, eps)` (eps 1e-12); commit
  `866892c` (2023-03-29, "final update to v3.7") turned it into the MAX
  form. Same in v3.8, v3.8.1, v3.9 and ROMS's own `vegetation_turb.F`
  (2025). No discussion found in the COAWST or ROMS issues or ROMS pull
  request #24.
- `tests/veg_timescales.py` on the 3 h periodic A15 vegetation run.
- 3 h runs restoring tau_free (control VM), compared with
  `tests/veg_compare.py`.

## Results

- Inside the canopy tau_free has a median of 44 s (15-290 s) and tau_veg
  105 s (62-1140 s): tau_free is the shorter one at 96 % of canopy points.
- The 2023 edit switched tau_free off twice: besides MAX for MIN, it reused
  `cff2` (the exponent of the epsilon formula) for the tau_veg term, so
  epsilon underflows to 0 from the second point of each tile.
- `MIN(1/dissip, max_eps)` alone: no change in the canopy (ratios 1.00),
  except up to 0.5 mm/s at the first point of each tile.
- MIN plus a separate variable (tau_free really restored, as in v3.2-v3.7
  and the papers): canopy TKE median -42 %, epsilon +21 %, eddy viscosity
  -65 %; above the canopy unchanged; currents change by up to 2.0 cm/s
  (3-D) and 1.1 cm/s (depth-averaged) against largest currents of
  6-8 cm/s; Hs by up to 3 mm.

## Decision / outcome

> **VEG_TURB: keep tau_free off, as shipped in COAWST v3.9** (author,
> 2026-10-21): the vegetation's epsilon source uses only the canopy time
> scale tau_veg (set by the gap between plants L), on the argument that
> canopy turbulence decays at canopy length scales. To revisit
> eventually. (the project conventions)

## Open questions

- Revisit, e.g. with observations of in-canopy turbulence or mixing on
  reefs. The repair is two lines (written down in coawst-cloud's patch documents).
- Test runs were kept for the revisit (not part of this repository).

## Details and links

- coawst-cloud's patch documents, roms-vegetation.patch ("Looked into, not changed")
- [docs, Goal](../docs/Reef_Ideal_A15.md) (decision)
- Related: [tau_veg units](2026-10-21_veg-turb-tau-veg-units.md)
