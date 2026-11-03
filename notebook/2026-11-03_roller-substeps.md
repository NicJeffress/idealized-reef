# The wave roller blew up at DT 6 s: a missing sub-step, now fixed

- **Date:** 2026-11-03
- **Status:** fixed (coawst-cloud `roms-roller-substeps`); the roller raises the
  set-up 25 % on the density-1 canopy
- **Builds:** coawst-cloud `d0db509` without and with `roms-roller-substeps`,
  case defaults of 2026-11-02, `+ROLLER_RENIERS`

## Question / why

`ROLLER_RENIERS` (surface roller of breaking waves, Reniers et al. 2004;
`WEC_ALPHA` is the share of the breaking dissipation that feeds the roller)
blew up at 23 min in phase 1 ([results p0-p2](2026-11-02_options-campaign-results-p0-p2.md)).
The author asked to dig into it.

## What was run

Density-1 canopy, triads on, defaults of 2026-11-02, 24 h, unsegmented (the
roller has not been through the restart tests): `WEC_ALPHA` 0.5 at DT 6 and
3 s and 0.2 at DT 6 s, first with COAWST's roller, then with the fix.

## Results

**Unpatched:** both DT 6 s runs blew up (WEC_ALPHA 0.5 at 21.8 min, 0.2 at
22.9 min), each at the surface at the inner edge of the crest beside the pass
(columns 119-124, rows 30-31), the vertical Courant number rising from about
0.5 to 25 in four steps. At DT 3 s the same run finished the day. A smaller
roller did not help, a smaller time step did.

**Cause** (`ROMS/Nonlinear/WEC/wec_roller.F`): the roller area is advected
with an explicit upwind step at the current plus the wave celerity. The loop
count is set by `numits=1` (the line above, `numits=30`, is commented out),
so it takes one step per baroclinic DT. With a wave celerity of 3-6 m/s on the
crest (1-3 m of water) and 20 m cells, the Courant number is 1.1-1.6 at DT 6 s
(unstable) and 0.55-0.8 at DT 3 s (stable).

**Fix:** the routine now computes the largest outflow Courant number of the
roller's upwind step over the domain and takes as many sub-steps as keep it
at or below 0.9.

| Run (density-1 canopy) | set-up | crest transport | crest jet max | surface/mean forereef | wall s per sim h |
|---|---|---|---|---|---|
| unpatched, DT 3 s, WEC_ALPHA 0.5 (values) | 22.8 mm | 653 m³/s | 0.33 m/s | 3.44 | 110 |
| patched, DT 6 s, 0.5 | +0.1 % | +0.1 % | -3.7 % | -0.4 % | **61** |
| patched, DT 3 s, 0.5 | 0.0 % | 0.0 % | -3.9 % | -0.7 % | 107 |
| patched, DT 6 s, 0.2 | -12 % | -8.1 % | -7.7 % | -23 % | 60 |
| no roller (density-1 baseline) | -20 % | -14 % | -10 % | -24 % | 69 |

## What it means

- The patched roller runs at DT 6 s and gives the converged DT 3 s answer
  (within 0.1 % on set-up and transports), at almost half the cost.
- **The roller is a sizeable term on this reef:** with `WEC_ALPHA` 0.5 the
  lagoon set-up is 25 % higher than without it, the crest transport 16 %,
  the jets 10-11 %, and the fore-reef flow more surface-intensified (+32 %).
  That is the expected physics: the roller stores part of the breaking
  energy and releases its momentum further shoreward, onto the reef flat.
  `WEC_ALPHA` 0.2 sits in between.

## Decision / outcome

The fix goes into coawst-cloud with a local before/after test. Whether the
roller (and which `WEC_ALPHA`) belongs in the A15 defaults is the author's
call; before that, its restart should be tested (`PERFECT_RESTART` with
`ROLLER_RENIERS` has not been checked).

## Details and links

- [Results summary](../results/README.md)
- Cost: 6 runs, about $1.
