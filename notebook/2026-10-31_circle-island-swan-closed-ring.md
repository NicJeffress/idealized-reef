# Circle_Island: a circular-island O-grid to test swan-closed-ring

- **Date:** 2026-10-31
- **Status:** done; a restart residual left open here was traced the same day
  to the case's DSTART ([next entry](2026-10-31_circle-island-restart-dstart.md))

## Question / why

Author: "Yes, build it": a circular-island O-grid case, to test coawst-cloud's
`swan-closed-ring` (the coupler map on grids that close round an island), the
last improvement without an idealized test.

## What was done

- New case `Circle_Island` (all files from `make_case.py`): round island
  600 m, lagoon 3 m, reef crest 0.8 m at 1150 m, fore reef to 47 m at 5.8 km;
  log-polar O-grid 216 x 80 (6 columns per SWAN direction bin, square cells
  17.5-169 m); A15 physics, `CURVGRID`, f = 0, DT 4 s, NDTFAST 10; waves Hs 1 m
  Tp 10 s from the north, or (`$INWARD` lines in `swan.in`) aimed inward all
  round; a copy of the grid with the seam moved 54 columns.
- coawst-cloud test `tests/improvements/swan-closed-ring`: 12 runs of 1 h on
  Cloud Batch (c2d-standard-8 Spot), `before` on the control VM.

## Results

| Check | Result |
|---|---|
| before the patch | SWAN stops: "REPeating curvilinear grid: no period found" |
| coupler, SWAN -> ROMS | Hwave = SWAN Hs exactly, also ROMS columns 0 and Lm+1, every output, 1/2/3 SWAN processes |
| coupler, ROMS -> SWAN | water level = zeta of the previous exchange within 1.1e-4 m (one ring off would be 2.3e-2) |
| layouts (6x1+2, 1x6+1, 2x2+3) | identical |
| seam moved 90 deg | 0.3 mm zeta, 6 mm Hs, 2 cm/s radial current, on the crest beside the seams; 3-6x smaller with 5 SWAN iterations per step; 1 vs 5 iterations itself changes results 3.5x more (SWAN sweeps start at the seam) |
| waves from all sides | Hs repeats every 10 deg within 0.55 %, no worse at the seam; the two boundary-row points beside the seam 2.2 cm low (segment ends) |
| A15 before/after | bit-identical (154 variables) |
| restart 30+30 vs 60 | open: 4.5e-5 relative (traced in the next entry) |

## Problems on the way

- **restart_record (a real bug in coawst-cloud's `roms-restart-wec`)**: the case
  writes a restart record every 10 min, and ROMS stopped at the third record
  (NetCDF error on `Huon`). Under PERFECT_RESTART the restart grids hold a
  time-level dimension before the record dimension; the patch used the wrong
  ones, so `zetat`/`Huon`/`Hvom` had no record dimension. Fixed. Segmented runs
  (one restart record per segment) never met it; a straight run with a restart
  record every hour and `LcycleRST F` would have stopped at hour 3. Restart test
  rerun on A15 variants: PASS.
- The grid generator first put u/psi coordinates one column off; ROMS does not
  use them here; other inputs bit-identical after the fix.
- Cost: about 25 Batch runs of 2-10 min on c2d-standard-8 Spot: about $0.40
  (estimate).

## Decision / outcome

`swan-closed-ring` works on a closed O-grid; Circle_Island kept as a case.

## Details and links

- [docs/Circle_Island.md](../docs/Circle_Island.md)
- coawst-cloud's patch document `swan-closed-ring`
