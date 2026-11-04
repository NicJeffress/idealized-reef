# The default A15 canopy case at DT 2.5 s: Courant numbers, full-day budget, canopy extent

- **Date:** 2026-11-04
- **Status:** default check passed; **canopy extent still the author's call**; grid checks still running (5 m band
  blew up at DT 2.5 s, rerun at DT 1.25 s; uniform 10 m running)
- **Build:** coawst-cloud `ca5316d`, case commit `26e6fb7`, `c2d-standard-16` Spot, 10 ROMS (1 x 10) + 6 SWAN

## Question / why

The defaults were settled one at a time, and the canopy cases had not yet run at DT 2.5 s. Do Cu, Cv and Cw stay below 1? With
`roms-diag-implicit-drag`, how does the whole-day budget divide bed stress and canopy drag? And does the canopy belong everywhere
or only on the reef? The author's ensembles will "vary all kinds of veg properties", so the default has to be locked first.

## What was run

`Reef_Ideal_A15_veg` as it stands, density 1 (`def1104-check`), and the same with density 1 only on the reef, meaning backreef, crest and fore reef
up to 20 m deep; lagoon, pass and deep water bare, 35 % of the wet cells (`def1104-reef`). 24 h, statistics over hours 12-24.
[`tools/reef/courant_from_log.py`](../tools/reef/courant_from_log.py), [`tools/reef/momentum_budget.py`](../tools/reef/momentum_budget.py),
`tests/options_compare.py --lagoon 5 25 --offshore 110 120 --flat 20 34 --crest-row 38 --forereef 45 60`.

## Results: Courant numbers and DT

| | Default, DT 2.5 s | DT 3 s (`a-dt3`) | Reef-only canopy |
|---|---|---|---|
| peak Cu | 0.018 | 0.022 | 0.018 |
| peak Cv | 0.169 | 0.203 | 0.187 |
| peak Cw | 0.16 (hour 1.8, top layer, row 43) | 0.19 | 0.16 |
| fastest current | 0.75 m/s | 0.75 m/s | 0.81 m/s |
| wall s per simulated hour | 280 | 239 | 272 |

All three Courant numbers fall by exactly the ratio of the steps, so on density 1 they are physical, unlike the low-tide peak on the smooth reef.

DT 3 s and DT 2.5 s agree on density 1: set-up, its range, transports, jets and Hs within 0.02 %, flushing time 0.1 %. Sea level differs by
under 8 micrometres rms all day. The only difference that grows is in `vbar` far offshore, 3.9-4.9 km from shore over 280-380 m of water
above the pass (max 7 cm/s, largest-row rms 1 cm/s at hour 24): the plume there diverges chaotically and does not touch the reef statistics.
DT 2.5 s costs 1.17x DT 3 s here. It is needed for the smooth end of the range, not for density 1.

## Results: the budget

Depth-integrated, hours 12-24, reef columns, m³/s² per metre alongshore. Lagoon-ward forces are negative. The residual is 1e-10 in every
zone, and 1e-7 of the largest term at every grid point, every hour of the day, in `ubar`, `vbar`, `u` and `v`, so each term is now measured rather than left over.

| Zone (m from shore) | Breaking + roller | Streaming | Pressure | Bed stress | Canopy drag | Advection + VF |
|---|---|---|---|---|---|---|
| lagoon, 0-920 | 0.000 | -0.012 | -0.068 | +0.033 | +0.088 | -0.039 |
| back of crest, 920-1000 | -0.041 | -0.063 | -0.309 | +0.089 | +0.322 | +0.001 |
| crest front, 1000-1050 | -0.535 | -0.336 | +0.731 | +0.082 | +0.047 | +0.010 |
| top of fore reef, 1050-1150 | -0.021 | -0.250 | +0.160 | +0.098 | +0.010 | +0.004 |
| slope, 1150-1500 | 0.000 | -0.011 | +0.001 | +0.006 | +0.003 | +0.001 |
| **all, 0-1500** | **-0.597** | **-0.672** | **+0.515** | **+0.308** | **+0.469** | **-0.023** |
| share of the force | 47 % | 53 % | 41 % | 24 % | 37 % | -2 % |

- **Over the whole reef, 41 % of the force goes into the pressure gradient, 37 % into canopy drag and 24 % into bed stress.** Set-up isn't the whole of it:
  61 % goes to drag, 60 / 40 canopy to bed.
- **The force and the drag are in different places.** Waves push hardest on the crest front (0.87 of 1.27), where pressure takes 84 % of it.
  Sea level there climbs from -13 mm to +78 mm (hour 12-24 mean, against offshore). That head then drives the flow down the back of the crest, where
  sea level falls to +33 mm and **69 % of all canopy drag acts in 80 m**. The lagoon sits at +26 mm.
- **Streaming matters most in front of breaking.** It is nearly all of the force on the top of the fore reef, 0.25 of 0.27, opposed by pressure and bed stress.
- **The two pressure parts nearly cancel on the fore reef.** Sea-level slope and the quasi-static wave term are -0.48 and +0.58 on the top of the fore reef, -0.23 and +0.23 on the slope: this is
  set-down under shoaling waves. On the crest front the sea-level part is +0.86 of the +0.73, so the set-up there is real sea-level slope.
- The old leftover budget at DT 3 s had drag +0.80 and pressure +0.51, so measuring it changed the split, not the size.

## Results: canopy extent

| Metric | Everywhere | Reef only |
|---|---|---|
| set-up | 25.7 mm | **-21.9 %** |
| set-up range | 19.1 mm | -17.3 % |
| crest transport | 720 m³/s | +2.8 % |
| pass transport | 814 m³/s | +3.0 % |
| crest jet p99 / max | 0.256 / 0.331 m/s | +4.7 / +0.2 % |
| pass jet p99 / max | 0.482 / 0.568 m/s | +8.9 / +9.9 % |
| surface/mean speed, crest / fore reef | 1.11 / 1.00 | -0.1 / +12.5 % |
| Hs crest / reef flat | 0.198 / 0.198 m | +0.3 / +3.8 % |
| dissipation across the reef | 1588 W/m | +0.3 % |
| flushing time | 65.8 h | -3.9 % |
| canopy drag / bed stress, 0-1500 m | 0.469 / 0.308 | 0.502 / 0.317 |

**The difference is the way out.** Sea level on the crest is the same in both (77.6 against 77.3 mm, at 1005 m). The lagoon is 5.7 mm lower with a bare lagoon and pass, and
that same offset carries along the pass (24.7 against 19.3 mm at 420 m). The crest flow changes by only 3 %, so what the canopy in the pass and lagoon does is add head loss on the
return route. Waves hardly notice: canopy over deep water does nothing to them.

For a canopy axis this matters: with canopy everywhere, changing density also changes the drag on the exit route, so 22 % of the set-up at density 1 is not a reef-canopy effect.

## Results: the grid checks (in progress)

The question is whether the band grid is converged with today's defaults; until now it had only been compared with a uniform 10 m grid on older settings.

**5 m rows (1018 m from shore) at DT 2.5 s blew up** at hour 1.77: Cw 0.10 at 0.67 h, 3.41 at 0.83 h, then 4-5, in the top layer at rows 60-62 (h 0.7-0.9 m); Cv only reached about
0.1 until the end (7.4, 20.8 m/s). Cost $0.03. Rerunning at DT 1.25 s, `NDTFAST` 10.

**Hypothesis, not yet tested:** stability depends on DT over the row spacing in the breaking zone. Density 1 at 10 m is noisy at DT 6 s (ratio 0.6); 5 m at DT 2.5 s blows up (0.5); the
smooth bare reef has Cw 1.39 at 10 m and DT 3 s (0.3), 0.61 at DT 2.5 s (0.25). The speed this implies, about 3 m/s, is close to sqrt(gD) at D of about 1 m. The rerun is the test.

## Decision / outcome

The default check passes. No change made. **The extent is the author's call:** *(recommendation, not yet decided)* reef only, because plants don't grow on 300 m of water, a scoured pass and a deep lagoon
are the less likely places for them, and a canopy axis then varies the reef alone.

## Open questions

- Canopy extent.
- Grid: the two runs above.
- Is 22 % of set-up to a canopy on the return route a sign that pass and lagoon drag should be an axis of its own?
- 7-day spin-up: every number here is hours 12-24 of the first day.
- Why the fore-reef surface/mean speed moves +12.5 % with canopy extent while the crest does not. Not investigated.

## Details and links

- [All defaults](2026-11-04_all-defaults.md), [force shapes and budget](2026-11-04_force-shapes-and-budget.md), [results summary](../results/README.md)
- Figure: [canopy extent](../figures/2026-11-04_canopy-extent.png), `tests/options_compare.py --png`.
- Cost: `def1104-check` $0.33, `def1104-reef` $0.32 (1.8-1.9 h at $0.17 per hour Spot), `grid-b5` $0.03.
