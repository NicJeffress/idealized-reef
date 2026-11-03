# The `GLS_Kmin` floor sets the lagoon's mixing at rest

- **Date:** 2026-11-03
- **Status:** done: the 1e-3 m²/s backreef diffusivity at rest is the GLS
  minimum-TKE floor; `GLS_Kmin` 1e-8 removes it

## Question / why

At rest (no waves, no tide) the stratified A15 case showed a vertical
diffusivity of about 1e-3 m²/s over the 2 m backreef, which erased the
stratification there within hours. The phase 1 runs showed it is not the
canopy turbulence (identical with `VEG_TURB` off) and that the TKE sits at the
floor `GLS_Kmin` (7.6e-6 m²/s², ROMS's k-epsilon default). Does a lower
floor remove it?

## What was run

Reef_Ideal_A15_veg_strat with the defaults of 2026-11-02 (AB3-AM4, implicit
stress and canopy drag, triads), at rest (tide 0, Hs 0.001 m), N² 1e-4,
24 h: `GLS_Kmin` 7.6e-6 (k-rest-76) and 1e-8 (k-rest-8).

## Results

Medians at mid-depth after 24 h:

| Zone | AKt, Kmin 7.6e-6 | AKt, Kmin 1e-8 | top-bottom temperature, 7.6e-6 / 1e-8 |
|---|---|---|---|
| lagoon and backreef (0.5-3 m) | 7.4e-4 m²/s | 5.1e-6 m²/s | 0.000 / 0.034 C |
| fore reef (3-20 m) | 5.1e-5 m²/s | 5.1e-6 m²/s | 0.29 / 0.49 C |
| offshore (> 20 m) | 4.7e-5 m²/s | 5.1e-6 m²/s | 8.31 / 8.37 C |

TKE is at the floor everywhere in both runs (7.6e-6 and 1e-8). With the
lower floor the diffusivity drops to ROMS's background value (`AKT_BAK`
5e-6) in every zone, 150x lower in the lagoon, and the lagoon keeps part of
its stratification; with the default floor it is mixed out.

Why the lagoon is hit hardest: the diffusivity at the floor scales with
sqrt(Kmin) times the turbulent length scale; offshore, stratification limits
the length scale (Galperin), in the unstratified shallow lagoon nothing does,
so the same floor gives 15x more mixing there.

## Decision / outcome

Proposed: `GLS_Kmin` 1e-8 for the stratified and heated A15 cases, once a
72 h heated run with it is stable (ROMS users report k-epsilon being less
forgiving at low floors; the 24 h forced stratified run with 1e-8 was stable,
reef-flat temperature range -66 %). The floor is a modelling choice that
decides how much a calm lagoon can stratify; record it in any methods
section.

## Details and links

- [Results summary](../results/README.md),
  [phase 0-2 results](2026-11-02_options-campaign-results-p0-p2.md) (p1s-kmin, p1s-rest)
- Cost: 2 runs x ~0.4 h of c2d-standard-16 Spot, about $0.20.
