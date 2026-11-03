# Wave streaming: the wave momentum lost to bottom friction and the canopy

- **Date:** 2026-11-03
- **Status:** done; **both adopted in the A15 defaults** (the author, 2026-11-03)
- **Builds:** coawst-cloud `ae2da7f` (`roms-veg-streaming-fixes`), `+BOTTOM_STREAMING`
  (and `+VEG_STREAMING`); `Reef_Ideal_A15_veg`, breaking-zone grid, roller, density-1
  canopy, 10 levels, `GLS_Kmin` 7.6e-6, `BREAKING CON 1.0 0.73` (as the baseline member
  of the vertical-resolution test, which is the comparison), 24 h

## Question / why

In the vortex-force formulation (`WEC_VF`), the momentum the waves lose reaches the
mean flow only through explicit force terms, one per way of losing it: breaking
(always on), bottom friction (`BOTTOM_STREAMING`) and plants (`VEG_STREAMING`). The
options note had both streaming options off as "second-order". On the density-1
canopy reef SWAN's dissipation is about 40 % breaking, 34 % bottom friction and
26 % canopy, so without them about 60 % of the wave momentum lost pushed no water.
Where (alongshore mean, end of the baseline run; W per metre of reef):

| zone | depth | Hs | near-bed orbital velocity | friction | breaking | canopy |
|---|---|---|---|---|---|---|
| lagoon, back reef (0-950 m from shore) | 1.4-6.6 m | 0.11-0.14 m | 0.04-0.13 m/s | 83 | 5 | 34 |
| crest (950-1050 m) | 0.55 m | 0.37 m | 0.44 m/s | 741 | 1545 | 476 |
| top of the fore reef (1050-1150 m) | 6.3 m | 0.95 m | 0.36 m/s | 520 | 94 | 542 |
| fore-reef slope, offshore | 23-110 m | 0.9-1.0 m | <= 0.13 m/s | 63 | 0 | 38 |

The friction is not the result of an extreme roughness: SWAN's Madsen et al. (1988)
friction factor is capped at 0.3, and on the crest it is about 0.25-0.3 (orbital
excursion 0.5-0.6 m against KN 0.3 m), a moderate value for a reef (field reefs
reach and exceed it; Lowe et al. 2005 found about 0.28 on Kaneohe, where friction
rivalled breaking). The friction is large because the near-bed orbital velocity is
0.36-0.44 m/s over the 0.5 m crest and the top of the fore reef. (An earlier split of
the same budget by depth called the 3-20 m zone "fore reef": in A15 that depth range
is mostly the 10 m deep lagoon.) The author's view was that the streaming terms
should be on.

## Code fixes first

The canopy force was broken in COAWST v3.9 (coawst-cloud `roms-veg-streaming-fixes`):
it replaced the bottom force instead of adding to it, its depth integral scaled with
the canopy height in metres, it used the previous step's canopy fraction, it had no
ghost points (`Dissip_veg` was never exchanged), and under `PERFECT_RESTART` its
restart variable was defined without the record dimension (a run stopped at the
fourth restart record). After the fix the depth-integrated force equals
(Dissip_fric + Dissip_veg) k/sigma to 3.5e-4 (0.29 of it before). The bottom force
itself was right.

## Results: bottom streaming

| Metric | none | bottom, DT 6 s | bottom, DT 3 s |
|---|---|---|---|
| set-up | 14.18 mm | **+57 %** | +57 % |
| set-up range | 13.48 mm | +32 % | +32 % |
| crest transport | 521 m³/s | **+22 %** | +22 % |
| pass transport | 618 m³/s | +19 % | +20 % |
| crest jet p99 / max | 0.195 / 0.264 m/s | +17 / +13 % | +17 / +13 % |
| pass jet p99 / max | 0.337 / 0.404 m/s | +22 / +21 % | +22 / +21 % |
| surface / mean speed, crest / fore reef | 1.13 / 1.07 | -2 / -5 % | -2 / -4 % |
| Hs crest / reef flat | 0.199 / 0.192 m | +3.7 / +3.4 % | same |
| breaking dissipation across the reef | 1706 W/m | -1.4 % | -1.4 % |
| lagoon flushing time | 64 h | -4.6 % | -4.5 % |
| wall s per simulated hour | 115 | 116 | 184 |

- **First-order.** Giving the water the momentum the waves lose to bottom friction
  raises the lagoon set-up by more than half and the flow over the crest and
  through the pass by a fifth. It acts near the bed on the fore reef and the crest,
  where breaking adds nothing below the top layers: the near-surface share of the
  flow falls slightly (surface/mean speed -2 to -5 %).
- **Numerically clean**: DT 6 s and DT 3 s agree to 0.1 %; stable on the A15
  defaults (implicit bottom stress and canopy drag), where the explicit-drag test
  case of the coawst-cloud fix blew up; cost +1.5 %.
- The waves themselves change little (Hs +3.7 % from the deeper water over the crest).

## Results: bottom and canopy streaming

Same runs plus `VEG_STREAMING` (coawst-cloud `4abff12`, after the restart-file fix):

| Metric | none | bottom | bottom + canopy, DT 6 s | bottom + canopy, DT 3 s |
|---|---|---|---|---|
| set-up | 14.18 mm | +57 % | **+95 %** | +95 % |
| set-up range | 13.48 mm | +32 % | +56 % | +56 % |
| crest transport | 521 m³/s | +22 % | **+32 %** | +33 % |
| pass transport | 618 m³/s | +19 % | +29 % | +29 % |
| crest jet p99 / max | 0.195 / 0.264 m/s | +17 / +13 % | +27 / +21 % | +27 / +21 % |
| pass jet p99 / max | 0.337 / 0.404 m/s | +22 / +21 % | +35 / +33 % | +35 / +33 % |
| surface / mean speed, crest / fore reef | 1.13 / 1.07 | -2 / -5 % | -3 / +7 % | -3 / +10 % |
| Hs crest / reef flat | 0.199 / 0.192 m | +4 / +3 % | +6 / +6 % | same |
| lagoon flushing time | 64 h | -5 % | -8.5 % | -8 % |
| wall s per simulated hour | 115 | 116 | 116 | 178 |

- **The canopy part adds about as much again**: with both forces the lagoon
  set-up nearly doubles and the crest and pass transports rise by about 30 %.
- Again stable and converged in time (DT 6 s = DT 3 s within 0.1 %), at no cost.
- Together the two streaming forces give the mean flow the momentum of the
  60 % of the wave dissipation that is not breaking; on this reef that is the
  difference between a set-up of 14 and of 28 mm.

## What it means

Without `BOTTOM_STREAMING`, the model leaves out a forcing as large as a third of the
breaking forcing on this reef; on a rough reef the set-up and the cross-reef transport
are underestimated by tens of percent. The force is proportional to SWAN's
bottom-friction dissipation, so the bed roughness (`grain_diameter` 0.12 m, SWAN KN
0.3 m) now sets the flow directly as well as the wave height: it moves up the list of
ensemble axes.

The same holds for the canopy: its streaming force is proportional to the canopy's
wave dissipation, so the canopy parameters set the flow through it too.

## Decision / outcome

**Adopted** (the author, 2026-11-03): `BOTTOM_STREAMING` in every A15 case and
`VEG_STREAMING` in the canopy cases; images from coawst-cloud `4abff12` on.

## Details and links

- coawst-cloud: `roms-veg-streaming-fixes` (patch, document, test)
- [Vertical resolution](2026-11-03_vertical-resolution.md) (the baseline member),
  [results summary](../results/README.md)
- Cost: bottom pair about $0.35, bottom + canopy pair about $0.35 (plus a failed first try, $0.1).
