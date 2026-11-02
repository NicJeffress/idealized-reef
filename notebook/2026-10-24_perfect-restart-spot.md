# PERFECT_RESTART with waves, for Spot VMs

- **Date:** 2026-10-24
- **Status:** restart patches done and tested on the idealized reef; Batch segment runner written, **not yet tested**; stratified case needs a author decision

## Question / why

The author wants to try Spot VMs (about 70-75 % cheaper) and asked to check
that PERFECT_RESTART works with all current physics, on the idealized
domain, so a preempted run can continue where it stopped.

## What was run

- `tests/restart_test.sh` (new): 60 min straight against 30 min + restart
  + 30 min, control VM, 6 ROMS + 2 SWAN; `tests/restart_check.py`
  compares every output record after the restart. Every-step history
  around the restart to find the first differing field. No Batch cost.
- Cases: Reef_Ideal_A15_veg (vegetation, VEG_TURB, spectral Stokes, SSW
  BBL, GLS), _veg_strat (N^2 1e-4, RadNud + nudging band), _veg_therm
  (solar heating at 11:00, SST feedback, far-field files), _veg_therm with
  `STEP2D_FB_AB3_AM4`.

## Results

As shipped a restarted run drifted: currents 2.4 cm/s off 30 min after the
restart, SWAN without plants at the restart record. Causes, and fixes:

| Cause | Fix |
|---|---|
| SWAN's periodic restart file is rounded text, and only the spectra; after a hotstart SWAN zeroes dissipation, so ROMS got other wave fields | coawst-cloud's `swan-exact-restart`: binary file with spectra and `COMPDA` before and after the coupling exchange, restored after the hotstart |
| SWAN reads `RESTART` after `COMPUTE` only at the end of the run (our case files) | run scripts put it before `COMPUTE` |
| ROMS uses the wave geopotential `zetat` one step late; not in the restart file | `roms-restart-wec.patch`: saved and read |
| ROMS's volume fluxes of a step are computed before the coupling exchange, the restart file after it | `Huon`, `Hvom` saved and reused in the first step (with halo exchange) |

| Case (max difference 30 min after the restart) | currents | other |
|---|---|---|
| A15_veg | 2e-10 m/s | SWAN output bit-identical |
| A15_veg_therm | 6e-9 m/s | temp 2e-6 C, Hs 1e-7 m |
| A15_veg_therm, AB3-AM4 | 5e-8 m/s | temp 2e-6 C, Hs 1e-7 m |
| A15_veg_strat | 9e-5 m/s (averages) | temp 1e-3 C, see below |

- First restarted step bit-identical in veg and therm; round-off starts
  in step 2-3 (veg interior, therm at the periodic seam columns). Two
  straight runs are bit-identical, so a small source remains, not traced
  (stopped at the author's request; far below physical relevance).
- Stratified case: our `ana_tobc.h` / `ana_tclima.h` copy the "initial
  state" as the north-boundary nudging reference on their first call,
  so after a restart the reference is the restart-time state. With a
  restart every few hours this nudges toward a drifting state.

Also written (not yet run): `run_member.sh` segment mode
(`restart_segment_hours`), `"spot": true` in `make_ensemble.py` (Spot VMs,
retry on preemption code 50001), `tools/merge_segments.py`,
`tests/segment_test.sh` (local run with a simulated preemption).

## Decision / outcome

Restarts are usable for the veg and thermal cases, including AB3-AM4.
Images need rebuilding to get the patches (none pushed yet).

## Open questions

- Stratified case: give the boundary/climatology reference as files from
  the initial state (like the thermal case's far-field files), or keep it
  analytic and avoid restarts for it? (author)
- Run `tests/segment_test.sh`, then a tiny Spot Batch job (confirms Spot
  uses the normal CPU quota; `PREEMPTIBLE_CPUS` is 0).
- The remaining round-off difference (optional).
- SWAN restart files are twice the spectra (A15: 145 MB per SWAN process);
  the second spectra copy could be dropped.

## Details and links

- coawst-cloud's patch documents `roms-restart-wec` and `swan-exact-restart`
- `batch/README.md`, Restartable members
- Entry Cost audit
