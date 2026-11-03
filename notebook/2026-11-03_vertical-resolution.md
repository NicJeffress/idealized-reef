# Vertical resolution: N 10, 15 and 20 levels

- **Date:** 2026-11-03
- **Status:** done; N 10 is not converged; the choice of N is the author's decision
- **Builds:** coawst-cloud `3227cce`, image `v3.9-cc3227cce-reef_a15_veg-def1103b`:
  `Reef_Ideal_A15_veg` on the breaking-zone grid, Reniers roller (`WEC_ALPHA` 0.5),
  density-1 canopy, `GLS_Kmin` 7.6e-6 and `BREAKING CON 1.0 0.73` (as the other
  campaign members), 24 h

## Question / why

Every A15 run so far had 10 levels (`Vtransform` 2, `Vstretching` 4, theta_s 3,
theta_b 2, Tcline 20 m), which on the 0.5 m crest gives 5 cm layers. The
options note had kept N 10 because 20 levels made an earlier implicit-stress
case fail on a much rougher grid, and the vertical structure of the crest jet
and the canopy layer had never been checked against N.

## What was run

N 10, 15 and 20 at DT 6 s, and N 20 at DT 3 s (the crest layers are 2.5 cm at
N 20). Initial files with the new number of levels from
`tools/reef/set_nlevels.py` (the canopy case is at rest and uniform); everything
else identical. Metrics over hours 12-24 with `tests/options_compare.py`, regions
mapped to the band grid; CSV and cross-reef profiles next to this entry.

## Results

| Metric | N 10 | N 15 | N 20 | N 20, DT 3 s |
|---|---|---|---|---|
| set-up | 14.18 mm | -7.2 % | -10.3 % | -11.7 % |
| crest transport | 521 m³/s | +2.1 % | +3.4 % | +3.4 % |
| pass transport | 618 m³/s | +1.8 % | +2.9 % | +2.9 % |
| crest jet p99 / max | 0.195 / 0.264 m/s | +2.1 / +2.8 % | +1.9 / +12.1 % | +3.7 / +3.0 % |
| pass jet p99 / max | 0.337 / 0.404 m/s | +5.5 / +6.6 % | +9.1 / +10.5 % | +8.8 / +10.6 % |
| surface / mean speed, fore reef | 1.074 | -6.3 % | -5.8 % | +1.2 % |
| Hs crest / reef flat, breaking dissipation | | within 0.3 % | within 0.3 % | within 0.3 % |
| largest vertical Courant number | 0.23 | 0.50 | **5.5** | 0.27 |
| fastest current | 0.53 m/s | 0.56 | **0.99** | 0.58 |
| wall s per simulated hour | 115 | 122 (+7 %) | 156 (+36 %) | 314 (2.7x) |

- **N 10 is not converged.** With more levels the lagoon set-up falls (-7 %
  at N 15, -10 to -12 % at N 20) while the flow over the crest and through
  the pass rises (+2 to +3 %; the pass jet +9 to +11 %). The waves are
  untouched (Hs and breaking dissipation within 0.3 %): the difference is in
  how the ocean model distributes the wave forcing and the bottom and canopy
  drag over depth, where the crest has only 5 cm layers at N 10.
- **It converges:** 10 to 15 changes the set-up by 7 %, 15 to 20 by another
  3-4 %; N 15 captures about two thirds of the change.
- **N 20 at DT 6 s is not robust.** Around low tide (hours 13-14.5) the top
  layer on the crest rows (2.5 cm thick) reached a vertical Courant number of
  5.5 and a spike of 0.99 m/s; the run did not blow up, but its crest-jet
  maximum and fore-reef shear are off. At DT 3 s the same grid stays at 0.27.
  N 15 at DT 6 s is clean (0.50).

## What it means

The vertical grid is a real numerical choice for A15: the set-up depends on it
by about 10 %, as much as the horizontal grid did before the breaking-zone
refinement. N 15 at DT 6 s takes most of the way for 7 % more cost; N 20 needs
DT 3 s (2.7x the cost of N 10) for the last 4 %.

## Decision / outcome

Open (the author's decision): N 15 at DT 6 s as the new default, N 20 at DT 3 s,
or N 10 with the difference stated.

## Details and links

- [Results summary](../results/README.md), [new defaults](2026-11-03_new-defaults.md)
- Cost: 4 runs, about $0.9.
