# Reef ensemble design: goals and first decisions

- **Date:** 2026-10-20
- **Status:** decisions recorded; several items still open

## Question / why

The author's plan (2026-10-20): an "encyclopedia" of how reef structure,
forcing and roughness affect reef dynamics, from idealized ROMS + SWAN
runs, possibly with offline particle tracking (ROMSPath) for larval
dispersion, comparing dispersion and other metrics across runs. Starting
point: the author's COAWST v3.7 project `Reef_Ideal_A15` (uploaded to

## What was run

Nothing; a design discussion recorded in the case pages in `docs/`.

## Results

Planned variations:
- Structure: forereef slope; crest, backreef and lagoon heights and
  widths; left-right crest height asymmetry.
- Forcing: wave height and period, stratification, tides, winds, thermal
  forcing.
- Roughness: homogeneous, only on forereef, crest or backreef, patchiness,
  `Zob` versus frontal area `lambda_f`.

## Decision / outcome

Recorded as decided by the author (the case pages in `docs/`):
- East-west periodic boundary conditions.
- The vegetation package for coral form drag.
- "Roughness: two separate approaches, never mixed": (a) bottom shear
  via `Zob` only, with SWAN given the matching Madsen roughness; (b)
  frontal area `lambda_f` only (ROMS canopy drag), with SWAN dissipating
  the same canopy (`VEG_SWAN_COUPLING`).
- "SWAN on the same grid as ROMS (no SCRIP interpolation)."
- Stratification and thermal forcing: both, at a later stage.

## Open questions

- Crest asymmetry with periodicity (proposed layout: half pass | west
  crest | pass | east crest | half pass): to think through.
- Run length, ROMSPath output interval, whether larvae feel Stokes drift.
- Output volume: hourly 3-D fields for a week are about 1 GB per run;
  15-min about 4 GB (about 400 GB for 100 runs).
- Structure variations need a Python grid generator (port of
  `Make_grid_Reef_Ideal_A14.m`): not built.
- PERFECT_RESTART: the author suspects a bug; a restart test is still to do.

## Details and links

- [docs, Goal](../docs/Reef_Ideal_A15.md) and [Decisions and answers](../docs/Reef_Ideal_A15.md)
- [What each variation needs](../docs/Reef_Ideal_A15.md), [Proposed order](../docs/Reef_Ideal_A15.md)
- Original v3.7 files: [`reference/Reef_Ideal_A15_v3.7/`](../reference/Reef_Ideal_A15_v3.7/)
