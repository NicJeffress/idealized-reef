# Circle_Island restart residual traced to DSTART (a case setting)

- **Date:** 2026-10-31
- **Status:** done; Circle_Island restarts to 1e-11 (SWAN Hs bit-identical)

## Question / why

Author: "Yes, trace it" (the 4.5e-5 restart residual left open on the new
circular-island O-grid case).

## How it was traced

1. Restart file as a full-state dump: straight run writing a restart record at
   step 451 (30:04), restarted run every step (Batch). Interior `rv` (the step's
   right-hand side, both levels) identical; `v` after one step off by a
   zero-mean shear (-2.1 mm/s bottom, +3.7 top) at the crest.
2. ROMS momentum diagnostics per step: `v_wbrk`, `v_vvisc` differ; misleading,
   since the 3-D diagnostics also carry previous steps' terms, which a restart
   does not restore.
3. Ruled out: tiling, `CURVGRID`, roughness and water level sent to SWAN at the
   restart, wave fields (identical through step 1), bottom stress, AKv,
   kstp/Zt_avg1, the SSW_BBL lagged bed fields, `OMEGA_IMPLICIT` (not defined).
4. Debug build printing every input of `pre_step3d`/`step3d_uv` at the crest:
   the restarted run's step counter started at 1 (`ntstart = ntfirst = 1`).

## Cause and fix

- Circle_Island's initial file says "seconds since 2000-01-01", but its
  `ocean.in` came from A15 with `DSTART = 0`. With `TIME_REF` 0 the model time is
  about 6.3e10 s, so (time - DSTART)/DT + 1, about 1.6e10, overflows ROMS's
  4-byte step counter, which ends at 1. A perfect restart sets ntfirst = 1
  expecting the counter to continue, so the restarted run cold-started its 3-D
  time stepping (Euler, then AB2, instead of AB3 with the restored history).
  Visible only where the forcing had just changed (crest after the wave update).
- The A15 cases are consistent (plain "days" and DSTART 0).
- Fix: Circle_Island `ocean.in` `DSTART = 730119.0d0`. Restart 30+30 vs 60:
  max 1e-11 relative, zeta/ubar/vbar/AKv/tke/SWAN Hs bit-identical. A fresh run
  is bit-identical with or without the fix, so all other swan-closed-ring
  results stand.
- Cost: about 9 Batch runs of 2-5 min (c2d-standard-8 Spot): about $0.15
  (estimate).

## Decision / outcome

Fixed in the case. A guard followed in coawst-cloud (`roms-restart-step-count`):
a restart whose step number cannot fit the counter now stops with a message
instead of silently cold-starting.

## Details and links

- [docs/Circle_Island.md](../docs/Circle_Island.md) (Start date)
