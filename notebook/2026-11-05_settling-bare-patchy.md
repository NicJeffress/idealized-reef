# Settling time on a bare and a patchy reef

- **Date:** 2026-11-05
- **Status:** result; no default changed. Run length stays the author's call; the stratified case is in [its own entry](2026-11-06_seven-day-stratified.md)
- **Build:** coawst-cloud `ca5316d` (`a544f70f`), `Reef_Ideal_A15_veg` with all defaults, DT 2.5 s, `NDTFAST` 10, N 15. `c2d-standard-16` Spot, 10 ROMS + 6 SWAN, 6 h segments

## Question / why

The [seven-day run](2026-11-05_seven-day-run.md) settled within the first tide, but only for uniform density 1. A canopy ensemble will span bare to patchy, with much faster currents at the bare end. Do 24 h members hold across that range? The author: "Yes, run both", then asked to include TKE: "are you looking at tke to determine spin up duration?"

## What was run

`settle3d`, 3 days each, no preemption:

- **Bare:** `bare.json`, canopy code compiled with density 0, default bed roughness (KN 0.3).
- **Patchy:** `patchy.json`, 30 % dense, 30 % sparse, 40 % bare in 150 m patches over the reef; lagoon and pass bare.

Compared hours 12-24 with hours 60-72 in each, with density 1 from the seven-day run over the same hours. Bulk numbers are tide-cycle means from 10-minute records, Eulerian plus Stokes; `tools/reef/momentum_budget.py` for the budget; TKE and `AKv` as tide means from hourly records, point by point where they exceed 10 % of the zone's largest.

## Results: reef and lagoon

| Hours 12-24 against 60-72 | Bare | Patchy | Density 1 |
|---|---|---|---|
| set-up, hours 60-72 | 84.01 mm | 32.82 mm | 25.16 mm |
| set-up change | +0.02 % | +0.07 % | +0.08 % |
| crest transport | 1804 m³/s, +0.03 % | 1105 m³/s, +0.05 % | 769 m³/s, +0.04 % |
| pass transport | 1834 m³/s, +0.03 % | 1121 m³/s, +0.05 % | 782 m³/s, +0.04 % |
| Hs crest | -0.004 % | +0.004 % | +0.009 % |
| set-up range | 12.19 mm, +2.2 % | 17.14 mm, -0.2 % | 19.38 mm, -0.1 % |
| budget, largest change of any term | 0.05 % of the largest | 0.12 % | within 0.1 % (against hours 156-168) |
| 12 h window within 0.5 % of the last, from | hour 0.7 | hour 0.7 | hour 0.7 |
| peak Cu / Cv / Cw, 3 days | 0.032 / 0.36 / 0.44 | 0.025 / 0.24 / 0.67 | 0.018 / 0.18 / 0.16 |
| fastest current | 1.56 m/s | 1.15 m/s | 0.75 m/s |

- **Bare and patchy settle within the first tide too.** No blow-ups, and every Courant number stays below 1 in all 12 segments.
- **What's left is scatter, not drift.** Over the 3 days the cycle-mean set-up wanders by 0.10 % on the bare reef and 0.22 % on the patchy reef, up and down, where density 1 falls steadily by 0.08 %. The bare reef's set-up range moves by up to 2.5 % from tide to tide.

## Results: turbulence

Tide-mean TKE / `AKv`, rms point-by-point difference, hours 12-24 against 60-72:

| From shore | Bare | Patchy | Density 1 |
|---|---|---|---|
| lagoon | 0.08 / 0.11 % | 0.13 / 0.32 % | 0.09 / 0.05 % |
| back of crest | 0.12 / 0.67 % | 0.13 / 0.15 % | 0.09 / 0.07 % |
| crest front | 0.15 / 0.83 % | 0.19 / 0.30 % | 0.13 / 0.14 % |
| 1150-1500 m | 5.9 / 15 % | 1.6 / 6.4 % | 0.27 / 1.5 % |
| 1500-2000 m | 35 / 41 % | 13 / 17 % | 1.4 / 3.9 % |
| 2-3 km | 38 / 43 % | 19 / 20 % | 4.0 / 5.9 % |

- **On the reef and in the lagoon, turbulence settles as fast as the flow,** under 1 % rms. Single points can move more where `AKv` is small: largest 32 % at the bare crest front, 21 % in the patchy lagoon.
- **Past the crest, the faster reefs are unsteady.** Hours 36-48 against 60-72 give nearly the same numbers (bare 1500-2000 m TKE 33 %, 2-3 km 38 %; patchy 11, 16 %), so this doesn't fade with time: it is variability rather than spin-up, and it grows with the speed of the jet. A single tide-mean snapshot there isn't a settled value on these reefs.
- Zone mean `AKv` at 3.8-5 km is 48 % low on the bare reef, 78 % on the patchy reef and 74 % on density 1 at hours 12-24 against 60-72, and still rising (10-23 % low at hours 36-48).

## Results: how far out it settles

Offshore-going transport, tide mean, hours 12-24 against 60-72 (`vbar` from hourly records, Eulerian):

| Line | Bare | Patchy | Density 1 |
|---|---|---|---|
| 1.2 km | +0.04 % | +0.06 % | +0.06 % |
| 1.5 km | +0.8 % | +0.17 % | +0.01 % |
| 2 km | +0.75 % | +1.4 % | -0.7 % |
| 2.5 km | -4.3 % | +11 % | -2.4 % |
| 3 km | -15 % | +22 % | -6.3 % |
| 4 km | -38 % | -30 % | -28 % |
| 4.9 km | -43 % | -71 % | -54 % |

The same picture as density 1: settled to about 2 km on every reef, not beyond 2.5 km. Past that the sign differs between reefs, so this isn't only one slow growth; the unsteadiness above is mixed in.

## Results: could a member be shorter than 24 h?

Hours 2-14 against 60-72, so a 14 h run at about 42 % less cost: bulk flow within 0.5 % (above). On the reef and in the lagoon, TKE is within 0.7 % rms, and `AKv` 0.6-1.4 % on the bare reef, 0.4-3.5 % on the patchy reef and 0.1-1.8 % on density 1 (largest single point 53 %, patchy lagoon). At 1150-1500 m, zone mean `AKv` is 10-12 % low. So a shorter run gives good bulk numbers and noticeably less settled turbulence. The budget wasn't checked for that window, and hours 12-24 are the safer choice.

## Decision / outcome

No default changed. Together with the seven-day run: **24 h members, analysed over hours 12-24, hold for the reef and lagoon across bare, patchy and density 1,** unstratified with steady waves, for flow, budget and turbulence. The first 12 h should stay out of the average, since hours 0-12 are about 5-6 % low. Nothing read past about 2 km on the bare and patchy reefs is a settled value at 24 h, and a longer run doesn't make it one on the unsteady parts. **For the author to decide** once the stratified case is in.

## Open questions

- Stratified case: `strat7d`, running.
- Smooth bare reef (KN 0.03), the fastest end, not run. Heated case, residence time and the bed roughness or canopy extremes aren't covered.
- Restart exactness wasn't compared with a straight run on these two reefs; it was on density 1 and, for shorter runs, on the bare reef ([all defaults](2026-11-04_all-defaults.md)).

## Details and links

- Spec: `batch/ensemble/tests/settle3d`
- [Seven-day run](2026-11-05_seven-day-run.md), [results summary](../results/README.md)
- Cost: bare 5.9 h, patchy 5.8 h, $2.04 in all. About 29 min per segment, faster than the 32 I had estimated
