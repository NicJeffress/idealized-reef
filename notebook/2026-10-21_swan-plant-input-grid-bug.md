# SWAN read plant properties on the wrong input grids (plant_input_grids)

- **Date:** 2026-10-21
- **Status:** done; the change `plant_input_grids` in coawst-cloud's `swan-vegetation-fixes`

## Question / why

In the A15 benchmark on c3d-standard-16, the 12 ROMS + 4 SWAN member
crashed at SWAN start-up (once in 7 Batch runs; not reproducible on the
control VM). Why?

## What was run

- Code reading of `SWAN/src/swanmain.ftn` and `swanpre1.ftn`.
- Valgrind on a short A15 run, before and after the fix (local images
  `coawst:reef_a15_before10_vg`, `coawst:reef_a15_vg`).
- Source check of how ROMS's plant fields reach SWAN in coupled runs.

## Results

- `INPGRID`/`READINP` register plant height, diameter and thickness as
  input grids 18, 19, 20, but `SWRBC` interpolated them on grids 16, 17,
  18 (SWAN 41.51's sea-swell inputs, undefined here): garbage plant values
  or a segfault in `SVALQI`/`EQREAL`. `INPGRID NPHT` also set the wrong
  flag (`VARNPL` instead of `VARNPH`).
- Valgrind: 4 reports of `SVALQI` branching on uninitialised values
  before the fix, none after; the 41 unrelated reports unchanged.
- Who is affected: in coupled runs with `VEG_SWAN_COUPLING` the coupler
  overwrites SWAN's plant arrays with ROMS's fields at every exchange,
  starting before the first wave step, so the wrong values never reached
  a coupled wave computation; the risk was the start-up crash. Standalone
  SWAN, or coupled without `VEG_SWAN_COUPLING`, used wrong values
  throughout.
- Coupled `swan.in` still needs `INPGRID NPLANTS` (no `READINP`): it
  switches on the spatial density; without it SWAN uses `nstems`
  everywhere.

## Decision / outcome

Fixed; image `v3.9-26e6fb7-reef_a15` (`sha256:3b7e0961...`) pushed; the
12 + 4 split reran cleanly.

## Open questions

- In SWAN 41.51 grid 18 is also the sea-swell direction grid: a case
  using both would collide (not changed).
- A author comment on COAWST issue #211 (odd results with
  `VEG_SWAN_COUPLING`) may be related. Not reported upstream.

## Details and links

- coawst-cloud's patch document `swan-vegetation-fixes` (`plant_input_grids`)
- [docs, Code issues](../docs/Reef_Ideal_A15.md) ("How ROMS plant fields reach SWAN")
