# Lab notebook

A dated record of every experiment, test and finding on the idealized cases,
one Markdown file per entry, in plain language with numbers and units. The
case pages in [`docs/`](../docs) hold the current description of each case; the
notebook says what was done when, why, what came out and what was decided.

The entries up to 2026-11-02 were rewritten for this repository from the
author's working notebook, keeping the numbers, tables and conclusions as
recorded. Some entries name scripts, ensemble specs and container images from
the author's working repository (`tests/...`, `batch/ensemble/...`,
`make_ensemble.py`, image digests); those are not part of this repository and
are kept as a record of what ran. Patches are named as in **coawst-cloud**
(e.g. `roms-vegetation`, `swan-periodic-fixes`), with the name of the single
change in brackets where a patch holds several (e.g. `tau_veg_units`).

**Every new experiment gets an entry** (see "How to add an entry" below). The
options test campaign (phases 0-2) gets one entry per phase.

## Index (newest first)

| Date | Entry | Case | Result in one line |
|---|---|---|---|
| 2026-11-02 | [Options campaign, phases 0-2: results](2026-11-02_options-campaign-results-p0-p2.md) | A15_veg, _strat, bare and patchy | Constant canopy damps the reef 95 % (noise floor ~1e-5); breaking spreads set-up -24 to +108 %; AB3-AM4 identical and 18 % faster; implicit canopy drag within 2.5 % and 37 % faster; 36 directions -10 %; roller blew up; rest diffusivity = GLS floor, not VEG_TURB |
| 2026-11-02 | [SWAN skips triads in the first iteration](2026-11-02_swan-triads-skipped-first-iteration.md) | A15_veg | With currents and one iteration per step, `TRIAD` is never computed (p1-notriad bit-identical); two iterations: breaking dissipation -73 %, set-up -41 % |
| 2026-11-02 | [OMEGA_IMPLICIT on the pass-jet runaway](2026-11-02_options-p2-omega-diag.md) | A15 thin-crest (thin_steep) | 2 m sea from t = 0: blow-up at 37.2 min, 35.3 min with `OMEGA_IMPLICIT`; the runaway is horizontal (cross-shore Courant ~0.75 at onset); DT 3 s clean with or without it (identical): option stays off; ~$0.06 |
| 2026-11-02 | [Options campaign, phases 1-2: setup](2026-11-02_options-campaign-phases1-2.md) | A15_veg, _strat, _therm | 26 members (breaking, triads, whitecapping, TKE_WAVEDISS, roller, Canuto, GLS_Kmin, NONLIN_EOS, bottom stress, implicit canopy drag) submitted; `VEG_HMIXING` and `UV_BANIHASHEMI` do not compile in v3.9 |
| 2026-11-02 | [Options campaign, phase 0: setup](2026-11-02_options-campaign-phase0.md) | A15_veg, A15_veg_10m | 15 members of 24 h (DT, NDTFAST, SWAN step and iterations, coupling, spectral resolution, tiling, 10 m grid, AB3-AM4, splines, VISC2) submitted; results pending |
| 2026-11-02 | [Bottom-stress schemes on thin crests](2026-11-02_a15-thin-crest-bottom-stress.md) | A15 thin-crest variants | Implicit stress = uncapped explicit (1 %), converged in DT; the `LIMIT_BSTRESS` cap gives 40-75 % faster crest flow and a DT-dependent set-up; no blow-up on any crest; ~$0.60 |
| 2026-10-31 | [Circle_Island restart residual: DSTART](2026-10-31_circle-island-restart-dstart.md) | Circle_Island | Restart residual 4.5e-5 = step-counter overflow (calendar-dated initial file with DSTART 0); DSTART 730119 -> 1e-11, SWAN bit-identical |
| 2026-10-31 | [Circle_Island and swan-closed-ring](2026-10-31_circle-island-swan-closed-ring.md) | Circle_Island | New 216 x 80 O-grid case; coupler map exact with 1-3 SWAN processes, layouts identical, seam move within SWAN's iteration error; restart_record bug found and fixed |
| 2026-10-31 | [Restart residual: turbulence_halo](2026-10-31_restart-residual-turbulence-halo.md) | A15 | Base A15 restart residual 1.8e-7 m/s traced to empty tke/gls ghost columns; fixed, 5.8e-11 |
| 2026-10-29 | [SWAN compressed NetCDF-4](2026-10-29_swan-compressed-netcdf4-output.md) | A15_veg | SWAN `.nc` files 4.0x smaller, values bit-identical, run time unchanged within noise |
| 2026-10-29 | [ROMS compressed NetCDF-4](2026-10-29_compressed-netcdf4-output.md) | A15_veg | History/averages/diagnostics 2.0-2.9x smaller, identical values; about 1 % run time at hourly output; made the default |
| 2026-10-27 | [Restartable segments, first Spot job](2026-10-27_spot-segments-first-batch.md) | A15_veg | Kill-and-resume matches the straight run to 2e-10 m/s; two Spot members in 3 segments each, bit-identical; about $0.10 |
| 2026-10-27 | [Implicit vegetation drag](2026-10-27_implicit-vegetation-drag.md) | A15_veg (patchy) | `VEG_DRAG_IMPLICIT`: patchy canopy runs 6 h at DT 6 s (explicit blew up at 42 min), within ~1 cm/s of explicit DT 3 s, 1.65x faster |
| 2026-10-27 | [Implicit bottom stress](2026-10-27_implicit-bottom-stress.md) | A15 | `BSTRESS_IMPLICIT`: split version not converged; drag inside the tridiagonal solve plus a fix for opposing near-bed flow: converged, within 2.5 % of explicit |
| 2026-10-24 | [WET_DRY Stokes fix as default patch](2026-10-24_wet-dry-stokes-patch-default.md) | A15 | A15 with `WET_DRY`: 0.24 m/s off the run without it after 1 h, 6e-5 m/s patched; other builds bit-identical |
| 2026-10-24 | [PERFECT_RESTART with waves](2026-10-24_perfect-restart-spot.md) | A15_veg, _strat, _therm | Restarted runs drifted 2.4 cm/s; with the restart fixes they match to round-off; strat case nudging reference resets at a restart |
| 2026-10-24 | [AB3-AM4 barotropic kernel](2026-10-24_ab3-am4-barotropic-kernel.md) | A15_veg | `STEP2D_FB_AB3_AM4` made usable; within 0.34 mm/s of LF-AM3; patchy canopy at DT 3 s 40 % faster |
| 2026-10-23 | [Thermal A15, 3 days](2026-10-23_thermal-forcing-3day.md) | A15_veg_therm | A wave-driven overturning imports heat; Rad drifts +0.35 C in 3 days, RadNud + nudging band +0.004 C; band chosen as default |
| 2026-10-23 | [Thermal forcing, 6 h tests](2026-10-23_thermal-forcing-6h.md) | A15_veg_therm | Diurnal heating and far-field column; budgets close; backreef surface 28.0 -> 30.2 C in 6 h |
| 2026-10-23 | [A15 crest depth](2026-10-23_a15-crest-depth.md) | A15 | Crest is 0.50 m deep at 940-1000 m (not 0.63 m at 600 m); the 0.4 m canopy reaches the surface at low tide |
| 2026-10-22 | [Stratified A15, north boundary over 24 h](2026-10-22_stratified-north-boundary-24h.md) | A15_veg_strat | Zero-gradient drifts +0.40 C; RadNud + interior nudging band 0.03 C near the boundary; chosen as default |
| 2026-10-22 | [Spatially varying canopy](2026-10-22_spatial-vegetation-patterns.md) | A15_veg | Patterns tool; `VEGETATION 3` = `VEGETATION 1` for a constant canopy; patchy blows up at DT 6 s (explicit drag), runs at 3 s |
| 2026-10-22 | [Constant stratification, Courant limit](2026-10-22_constant-stratification-courant.md) | A15_veg_strat | Internal-wave Courant number must stay below about 0.4-0.5; N² 1e-4 runs at DT 6 s, 3e-4 needs 3 s |
| 2026-10-21 | [Coral elements are cylinders](2026-10-21_vegetation-cylinder-convention.md) | A15_veg | thickness = pi/4 x diameter; thickness = diameter filled the bed and blew up `VEG_TURB` |
| 2026-10-21 | [tau_veg units](2026-10-21_veg-turb-tau-veg-units.md) | A15_veg | tau_veg was 1.6-3x too long; fixed: canopy eddy viscosity -7 % |
| 2026-10-21 | [tau_free never used](2026-10-21_veg-turb-tau-free.md) | A15_veg | Restoring it: canopy TKE -42 %, eddy viscosity -65 %; kept as shipped (author's decision, to revisit) |
| 2026-10-21 | [Vegetation crash with periodic boundaries](2026-10-21_vegetation-periodic-crash-fix.md) | A15_veg | Work array exchanged with wrong bounds: heap corruption on the first step; fixed |
| 2026-10-21 | [SWAN plant input grids](2026-10-21_swan-plant-input-grid-bug.md) | A15 | Plant height/diameter/thickness read on the wrong input grids (start-up crash); fixed |
| 2026-10-21 | [A15 24 h on Batch](2026-10-21_a15-periodic-batch-24h.md) | A15 | 68 s wall per simulated hour, seam clean all day, bit-identical across CPUs; 2.85 GB output per day; ~$0.50 |
| 2026-10-21 | [A15 benchmark](2026-10-21_a15-split-tiling-benchmarks.md) | A15 | c2d-standard-16 with 10 ROMS + 6 SWAN best (139 s per 2 h); C2D 25-30 % faster than C3D |
| 2026-10-21 | [Coupled periodic A15](2026-10-21_a15-coupled-periodic-test.md) | A15 | Periodic SWAN: seam current jump 2 mm/s against 58 mm/s with non-periodic SWAN; Stokes coupling bug fixed |
| 2026-10-21 | [Periodic curvilinear SWAN](2026-10-21_swan-periodic-curvilinear-grids.md) | Swan_Periodic_Test | SWAN periodic on stretched curvilinear grids; seam within 1.3e-4 m on A15's grid |
| 2026-10-21 | [Periodic SWAN, regular grids](2026-10-21_swan-periodic-regular-grids.md) | Swan_Periodic_Test | Periodic SWAN works once patched (x-strips crashed, COMPGRID frame wrong); non-periodic boundaries change crest Hs by up to 1.2 m |
| 2026-10-21 | [Spectral Stokes drift](2026-10-21_spectral-stokes-fixes-speedup.md) | A15, A15_bulk | Keep spectral Stokes; index errors fixed; 3x fewer transcendental calls |
| 2026-10-20 | [Port to COAWST v3.9](2026-10-20_reef-a15-port-to-v39.md) | A15 | Ported as-is; ROMS is the bottleneck (WEC kernel 46 %) |
| 2026-10-20 | [Ensemble design decisions](2026-10-20_reef-ensemble-design-decisions.md) | A15 | Goals and first decisions: periodic, canopy drag for coral, roughness approaches never mixed, SWAN on the ROMS grid |

## How to add an entry

1. After each experiment or test, create `notebook/YYYY-MM-DD_short-slug.md`,
   dated when the work was done. About 20-60 lines.
2. Use the template below. Give numbers with units, the case and any changes
   to it, the build options (coawst-cloud commit, `CPP_OPTIONS`), machine type
   and ROMS + SWAN process split, run length and cost. Quote the author's
   decisions as written. Write "not recorded" rather than guessing.
3. Link with relative paths (`../docs/<Case>.md`, `../tools/...`).
4. Figures: embed every figure looked at to reach the result. Commit the PNG to
   `figures/` (about 100-400 KB, dpi 100-120) and embed it under `## Figures`
   with `![what it shows](../figures/name.png)` and a short caption saying what
   each panel shows and which script made it.
5. Add a row at the top of the index table above.
6. Keep entries to the idealized cases in this repository.

Template:

```markdown
# <Title: what was tested or found>

- **Date:** YYYY-MM-DD
- **Status:** done / pending / decision (author) / superseded

## Question / why

What was asked or noticed, and who asked (if recorded).

## What was run

Case and changes, build (coawst-cloud commit, CPP_OPTIONS), machine type,
ROMS + SWAN split, run length, cost (or "not recorded").

## Results

The key numbers, with units (a small table is fine).

## Figures

![What the figure shows](../figures/<name>.png)

Script that made it; what each panel shows.

## Decision / outcome

> Quote of the author's decision.

## Open questions

What is still unknown or not done.

## Details and links

- [docs/<Case>.md](../docs/<Case>.md)
```
