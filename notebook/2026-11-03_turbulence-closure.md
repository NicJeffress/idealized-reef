# Turbulence closure on the heated reef: k-epsilon, k-omega, gen; `SPLINES_VDIFF`

- **Date:** 2026-11-03
- **Status:** done; k-epsilon kept (proposed; the author's decision); `SPLINES_VDIFF` is inert here
- **Builds:** coawst-cloud `fa37747` series; `Reef_Ideal_A15_veg_therm` with the defaults of
  2026-11-03 evening (breaking-zone grid, roller, 15 levels, `GLS_Kmin` 1e-8, BKD), 24 h;
  `VEG_TURB` off in the closure members (its canopy source is a k-epsilon source)

## Question / why

The options campaign had compared two stability functions (Kantha-Clayson and
Canuto-A) on an unheated case; the author asked whether other GLS closures
(k-omega, the generic "gen" model) should be tried, and where the closure
matters. `VEG_TURB` adds the plant work to the length-scale equation as an
epsilon source, valid only for k-epsilon, so every closure member ran with it
off; one member with it on gives the reference.

## What was run

Heated case (shortwave peak 1000 W/m², tide 0.15 m, waves, density-1 canopy),
24 h, metrics over hours 12-24:

| Member | closure (`GLS_P`, `M`, `N`) | stability functions | `VEG_TURB` |
|---|---|---|---|
| ke-KC | k-epsilon (3, 1.5, -1) | Kantha-Clayson | off |
| ke-Canuto | k-epsilon | Canuto-A | off |
| kw-Canuto | k-omega (-1, 0.5, -1) | Canuto-A | off |
| gen-Canuto | gen (2, 1, -0.67) | Canuto-A | off |
| ke-KC + VEG_TURB | k-epsilon | Kantha-Clayson | on (today's default) |

Coefficients from ROMS's table in `ocean.in`; `GLS_Kmin` 1e-8 for all. Plus the
stratified case with and without `SPLINES_VDIFF`.

## Results

Flow and surface temperature (`tests/options_compare.py`, differences to ke-KC):

| Metric | ke-KC | ke-Canuto | kw-Canuto | gen-Canuto | ke-KC + VEG_TURB |
|---|---|---|---|---|---|
| set-up | 1.94 mm | +1.2 % | +6.5 % | -4.5 % | +0.8 % |
| crest transport | 144 m³/s | +1.2 % | +1.7 % | +5.0 % | -3.7 % |
| crest jet p99 | 0.054 m/s | +1.1 % | +3.0 % | +5.5 % | -3.2 % |
| surface / mean speed, crest | 1.29 | +3.4 % | +2.3 % | +9.7 % | -8.2 % |
| reef-flat SST mean | 28.16 C | +0.0 % | -0.5 % | -0.0 % | -0.0 % |
| reef-flat SST range | 1.49 C | +0.7 % | **-12.7 %** | -4.8 % | +0.8 % |

Mixing and stratification by distance from shore:

| Zone | metric | ke-KC | ke-Canuto | kw-Canuto | gen-Canuto | ke-KC + VEG_TURB |
|---|---|---|---|---|---|---|
| lagoon (0-850 m) | AKt median | 1.6e-3 | 1.3e-3 | **6.9e-6** | 6.8e-4 | 1.7e-3 |
| | top-bottom T mean / max | 0.50 / 1.49 C | 0.49 / 1.54 | 0.13 / 1.78 | 0.49 / 1.48 | 0.50 / 1.53 |
| reef flat, crest | AKt median | 3.4e-3 | 3.1e-3 | 2.2e-3 | 2.0e-3 | **5.5e-3** |
| top of fore reef | AKt median | 2.3e-3 | 1.7e-3 | 3.4e-4 | 1.4e-3 | 2.9e-3 |
| slope, offshore | AKt median | 5.1e-6 (= `AKT_BAK`) in all | | | | |

- **k-epsilon with Canuto-A or Kantha-Clayson: the same reef.** Mixing differs by
  10-30 %, the flow and the temperatures by 1-3 %. (The earlier "+29 % SST range"
  with Canuto-A was on the unheated stratified case, where that range is tiny.)
- **gen** mixes less in the lagoon and on the reef (2-2.4x lower AKt) and moves the
  flow by up to 5 % (crest transport) and the crest shear by 10 %; temperatures
  within 5 %.
- **k-omega** departs strongly in the lagoon: the diffusivity falls to the
  background (7e-6 against 1.6e-3 m²/s), yet the mean top-bottom temperature
  difference is smaller (0.13 against 0.50 C) while its maximum is larger. The two
  do not fit a simple picture (it may mix in bursts, e.g. by night convection); it
  needs a closer look before k-omega results could be trusted.
- **`VEG_TURB` on** (the default) raises the reef-flat and crest diffusivity by 60 %
  and makes the crest flow 8 % less surface-intensified; the flow changes by 2-4 %.
- **`SPLINES_VDIFF` does nothing here**: the stratified runs with and without it
  are bit-identical. In `step3d_t.F` the spline reconstruction is used only for
  tracers that are not advected with MPDATA; with MPDATA (all A15 tracers) the
  vertical diffusion is the standard implicit solve either way.

## What it means

On the forced, heated reef the closure is a 5-10 % effect at most among k-epsilon,
its stability functions and gen; the canopy turbulence (`VEG_TURB`) is as large.
Nothing argues for leaving k-epsilon, so `VEG_TURB` needs no port to other closures.
k-omega would need investigation first.

## Decision / outcome

Proposed: keep k-epsilon with Kantha-Clayson and `VEG_TURB` on (no patch needed);
gen as a sensitivity member if the closure becomes an ensemble axis. `SPLINES_VDIFF`:
irrelevant with MPDATA (kept as is). The author's decision.

## Details and links

- [Results summary](../results/README.md), [GLS_Kmin](2026-11-03_kmin-heated-72h.md)
- Cost: 7 runs of about 55 min, about $1.
