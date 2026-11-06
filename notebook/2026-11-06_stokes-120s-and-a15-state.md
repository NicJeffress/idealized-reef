# Stokes drift every 120 s adopted; where the A15 default stands

- **Date:** 2026-11-06
- **Status:** decision recorded in the case folders. No image has been built with it and no run has used it through the case header yet
- **Build:** none new. The evidence is from images built with `+STOKES_INTERVAL` on the command line, coawst-cloud `ca5316d` plus `roms-stokes-interval`

## Question / why

The author, on the choice of Stokes update interval: "Adopt 120 s". The reasons are in [Making A15 faster](2026-11-05_speed-stokes-and-machines.md). This entry records the change, what it hasn't been checked on, and the state of the other decisions on the default case.

## What changed

- `#define STOKES_INTERVAL` in the header and `STOKES_NCPL == 5` in `ocean.in` of `Reef_Ideal_A15`, `Reef_Ideal_A15_veg`, `Reef_Ideal_A15_veg_strat` and `Reef_Ideal_A15_veg_therm`.
- At DT 2.5 s and a 600 s exchange, that is an update every 48 steps, 120 s. A 6 h restart segment is a multiple of it, as the option needs.
- **Not changed:** `Reef_Ideal_A15_bulk`, because `BULK_STOKES` is cheap already and the option doesn't touch it. The islands, which keep their own settings. coawst-cloud's own default stays off: the option is in its series and only a case that defines it uses it.
- **Takes effect at the next image build.** Existing images ignore the new keyword and still update every step, so runs from them aren't affected.

## Evidence, and what it doesn't cover

| Density 1, 24 h, hours 12-24, against every step | At 120 s |
|---|---|
| Wall time per simulated hour (10 ROMS + 6 SWAN) | 127 s against 280 s |
| Set-up | -0.003 % |
| Crest and pass transport | under 0.001 %, -0.002 % |
| Peak Cw | -0.3 % |
| Budget by zone | unchanged to three decimals |
| Restart | bit-identical at `STOKES_NCPL` 1, from the second record after it; 120 s not run separately |

- **Past about 3 km the first day's tide means do move:** offshore-going transport departs by about 1 % at 3.5-4 km and 4 % at 4.9 km. That is no larger than the same flow reaches by chance within two more days ([72 h twin](2026-11-05_speed-stokes-and-machines.md)).
- **Tested on density 1 only.** Not run with the option: bare reef, patchy canopy, stratified, thermal. The bare reef has the fastest flow and the patchy canopy the highest peak Cw, so those are the two most worth running. The patch's limit also still stands: a larger tide over very shallow water changes the layers more between updates, so repeat the accuracy test before using it there.
- **The header route hasn't been compiled.** The tests set the option with `CPP_OPTIONS`. It should act the same from the header, but the first build should confirm it: the log must print `stokes_ncpl` as 5.

## Where the A15 default stands

| Question | State | Basis |
|---|---|---|
| Stokes update | **Decided: 120 s** (this entry) | [Making A15 faster](2026-11-05_speed-stokes-and-machines.md) |
| Canopy | **Decided:** density 1, everywhere | [Default check](2026-11-04_default-check.md) |
| Time step | **Decided:** DT 2.5 s, `NDTFAST` 10 | [All defaults](2026-11-04_all-defaults.md) |
| Grid | Author leaning to keep it ("maybe we just keep the grid how it is"); no smaller A15 being built | [Default check](2026-11-04_default-check.md), [jet and 10 m limit](2026-11-04_jet-and-10m-limit.md) |
| Run length | **Open.** I recommend 24 h, averaged over hours 12-24, for reef and lagoon flow. Stratified set-up is 0.8 % low on day 1, and about 3.5 days removes that | [Seven days](2026-11-05_seven-day-run.md), [bare and patchy](2026-11-05_settling-bare-patchy.md), [stratified](2026-11-06_seven-day-stratified.md) |
| Machine and split | **Open.** I recommend `c2d-standard-8` with 5 + 3 for ensembles ($0.14 per 24 h, 7.5 members per hour on 100 vCPUs); `c2d-standard-16` with 10 + 6 is $0.17 and 6.1 members per hour | [Making A15 faster](2026-11-05_speed-stokes-and-machines.md) |
| Breaking force shape and `KWD` | Stock kept; no explicit decision by the author | [Force shapes](2026-11-04_force-shapes-and-budget.md) |

What the runs so far don't support at any tested length: individual offshore snapshots past 2-4 km after about three days, stratified `AKv` in the lagoon and at the crest front, temperature, and flow past 1.2 km under stratification.

## Decision / outcome

120 s is the A15 default from the next image. Next step, when the author wants it: build the image and run 24 h on the bare and patchy reefs at `STOKES_NCPL` 5, against the `settle3d` members' first day at every step, checking Cu, Cv and Cw in the logs.

## Details and links

- Patch: coawst-cloud `3-experimental/roms-stokes-interval`
- Movies of the seven-day default run: `gs://coawst-runs-nj/movies/a15_spinup7d_whole.mp4`, `a15_spinup7d_reef1500m.mp4`
- Cost: no runs for this entry
