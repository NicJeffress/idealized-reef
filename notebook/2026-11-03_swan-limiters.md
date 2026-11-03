# SWAN's refraction and frequency-shift limiters (`CTHETA`, `CSIGMA`, `DIRIMPL`)

- **Date:** 2026-11-03
- **Status:** done; no change to the defaults
- **Builds:** image of the band-grid roller run (coawst-cloud `61f8cea`, `+ROLLER_RENIERS`),
  `Reef_Ideal_A15_veg` on the breaking-zone grid, density-1 canopy, `WEC_ALPHA` 0.5,
  24 h, DT 6 s; the defaults of 2026-11-03

## Question / why

SWAN's technical manual warns that refraction over coarse, steep bathymetry
in nonstationary runs can turn wave energy through spuriously large angles
per step, and offers a limiter on the refraction (`NUM CTHETA`, a CFL limit on
the turning rate) and on the frequency shift by currents (`CSIGMA`); with
strong currents it also recommends fully upwind directional differencing
(`NUM DIRIMPL 1` instead of the default 0.5). The A15 fore reef is steep (1:5)
and the crest jet is strong, so the options note listed them as "to test".

## What was run

Four members, otherwise identical: the current settings; `NUM CTHETA 0.9`;
`NUM CTHETA 0.9 CSIGMA 0.9`; `NUM DIRIMPL 1`. SWAN echoed each command in its
print file. Metrics over hours 12-24 (`tests/options_compare.py` with the
regions mapped to the band grid: lagoon rows 5-25, offshore 110-120, reef flat
20-34, crest v-row 38, fore reef 45-60); CSV next to this entry. Directional
noise: the second difference of SWAN's mean direction across the crest,
breaking zone and top of the fore reef, last 12 h.

## Results

| Metric | current | `CTHETA 0.9` | `+ CSIGMA 0.9` | `DIRIMPL 1` |
|---|---|---|---|---|
| set-up | 14.18 mm | +0.0 % | +0.0 % | -0.1 % |
| crest / pass transport | 521 / 618 m³/s | +0.0 / +0.0 % | same | +0.0 / -0.1 % |
| crest jet p99 / max | 0.195 / 0.264 m/s | +0.0 / +0.2 % | same | -0.9 / -1.0 % |
| Hs crest / reef flat | 0.199 / 0.192 m | -0.1 / +0.7 % | same | +0.0 / -0.4 % |
| breaking dissipation across the reef | 1706 W/m | -0.0 % | same | +0.1 % |
| direction 2nd difference p99, alongshore / cross-shore | 3.7 / 10.0 deg | 3.4 / 10.0 | - | 3.7 / 8.8 |
| wall s per sim h | 119 | 119 | 121 | 118 |

- The current-settings member reproduces the band-grid roller run of the
  same day exactly (set-up 14.18 mm): the runs are reproducible.
- **`CTHETA 0.9` changes nothing that matters** (everything within 0.7 %):
  the refraction turning rate on the A15 grid stays below the limit almost
  everywhere, and the direction field is no noisier without it.
- **`CSIGMA 0.9` never acts**: the results are identical to `CTHETA` alone
  to every printed digit. The frequency shift by A15's currents (at most
  0.5 m/s) is far below its limit.
- **`DIRIMPL 1`** (more upwind, more numerical diffusion in direction)
  smooths the cross-shore direction field slightly and moves the jets by
  1 %, within the noise of every other numerical choice.

## What it means

On the idealized reef SWAN's directional numerics are not a source of error:
the defaults are converged with respect to these limiters. Where currents are
much stronger (a pass with a 1-2 m/s ebb jet against swell) the frequency
shift and the refraction by currents grow, so the result does not carry over
to such a site without its own check.

## Decision / outcome

Keep the defaults (no limiter, `DIRIMPL` 0.5) for A15.

## Details and links

- [Results summary](../results/README.md), [new defaults](2026-11-03_new-defaults.md)
- Cost: 4 runs of about 50 min on c2d-standard-16 Spot, about $0.4.
