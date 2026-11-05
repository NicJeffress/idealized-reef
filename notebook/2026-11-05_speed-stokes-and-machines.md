# Making A15 faster: Stokes drift updates, machines and process split

- **Date:** 2026-11-05
- **Status:** result; the Stokes option works and is off by default until the author decides. Twin test on the offshore flow: running
- **Build:** coawst-cloud `ca5316d` (`a544f70f`, `def1104-check`); `ca5316d` plus `roms-stokes-interval` (`f0bfd5c`) with `+STOKES_INTERVAL` (`e01ef5a1`). `Reef_Ideal_A15_veg`, density 1, DT 2.5 s, N 15, 34 frequencies, 72 directions

## Question / why

The author: "can we do anything to speed these runs up? How do they scale onto bigger machienes?" and, on Stokes drift: tie the update "to the coupline interval (or some multiple shorter than the coupling interval)?"

## Where the time goes

ROMS, 6 h of `spinup7d`, 10 ROMS + 6 SWAN: WEC kernel 60 %, GLS 10 %, barotropic kernel 6 %, canopy 4 %, time-averaged output 4 %. MPI halo exchanges are 23 %, counted inside those.

We use `SPECTRUM_STOKES`. ROMS redoes the sum over the 34 frequency bins in every layer and column on every baroclinic step, 240 times per SWAN exchange at DT 2.5 s, on the same spectrum.

## The option

`roms-stokes-interval`: `STOKES_NCPL` in `ocean.in` is the number of updates per wave-to-ocean exchange (0 every step, 1 at the exchange, 5 every 120 s, 20 every 30 s). Only the spectral sum is held. `W_stokes` and `ubar_stokes`, `vbar_stokes` are still computed every step from the current depths, so the 2-D and 3-D Stokes transports stay consistent.

## Results: accuracy and speed

24 h (`stokes-int`), against every step (`def1104-check`), hours 12-24:

| | Every step | 600 s | 120 s | 30 s |
|---|---|---|---|---|
| wall s per simulated hour | 280 | 135 | 127 | 144 |
| WEC kernel, share of ROMS time | 59 % | 11 % | 13 % | 19 % |
| set-up, 25.69 mm | | -0.03 % | -0.003 % | -0.001 % |
| set-up range, 19.08 mm | | -0.4 % | -0.01 % | -0.01 % |
| crest transport, 720 m³/s | | +0.01 % | under 0.001 % | under 0.001 % |
| pass transport, 814 m³/s | | -0.01 % | -0.002 % | under 0.001 % |
| surface/mean speed, fore reef | | +2.1 % | -0.02 % | +0.09 % |
| Hs crest | | under 0.03 % | under 0.01 % | under 0.01 % |
| peak Cw, 0.160 | | -1.1 % | -0.3 % | -0.1 % |

- Wall times are from separate VMs; a few percent is noise, since 120 s can't really be cheaper than 600 s.
- The budget by zone is unchanged to three decimals at all three intervals (the 0-1500 m canopy term at 600 s moves in the fourth) and closes to about 1e-10.
- Tide-mean TKE and `AKv`, point by point where they exceed 10 % of the zone's largest, rms and largest change. At 120 s: TKE at most 0.01 % rms and `AKv` 0.02 % rms on the reef and in the lagoon, largest `AKv` change 2.2 % at the crest front. At 600 s: rms 0.12 % at most, largest 8.5 %.
- Stokes velocity on the reef and in the lagoon: under 0.2 % rms even at 600 s, so the change in depth between updates doesn't matter here.
- **Control:** `STOKES_NCPL` 0 for 2 h, all 62 history and 83 diagnostic fields bit-identical to the build without the patch (`stokes-ctl`).
- **Restart:** `STOKES_NCPL` 1, 8 h with a restart at 4 h, bit-identical to the straight run from hour 5 in every field (`stokes-rst`). The first record after the restart differs only in the same output-only fields and diagnostics as without the patch.

## Results: machines and split

2 simulated hours from rest, one run each, wall time including start-up; 24 h runs are a little quicker per hour, since start-up counts for less (127-135 s against 147 s). The price is us-west4 Spot ($0.174/h for `c2d-standard-16`; 8 and 32 scaled from it, 56 estimated), and cost is per 24 h simulated.

| Machine | ROMS + SWAN | Stokes every step | Stokes every 120 s |
|---|---|---|---|
| `c2d-standard-8` | 6 + 2 | 948 s | 667 s |
| `c2d-standard-8` | 5 + 3 | 1056 s | **476 s** |
| `c2d-standard-16` | 9 + 7 | | 306 s |
| `c2d-standard-16` | 10 + 6 | 642 s | **294 s** |
| `c2d-standard-16` | 12 + 4 | **565 s** | 362 s |
| `c2d-standard-32` | 20 + 12 | 333 s | **179 s** |
| `c2d-standard-32` | 24 + 8 | **293 s** | |
| `c2d-standard-56` | 36 + 20 | 213 s | |
| `c2d-standard-56` | 40 + 16 | **209 s** | |

- **The best split depends on the Stokes setting.** Every step: ROMS is the bottleneck, so 12 + 4 beats 10 + 6 by 12 %. Every 120 s: SWAN limits, and 10 + 6 beats 12 + 4 by 19 %, and on 8 vCPUs 5 + 3 beats 6 + 2 by 29 %. 10 + 6 remains right if the option is adopted.
- With Stokes at 120 s, per 24 h at the best split in each row:

| Machine | Best split | Wall, 2 h test | Cost per 24 h | Members per hour, 100 vCPUs (one region) |
|---|---|---|---|---|
| `c2d-standard-8` | 5 + 3 | 476 s | $0.14 | 7.5 (12 VMs) |
| `c2d-standard-16` | 10 + 6 | 294 s | $0.17 | 6.1 (6 VMs) |
| `c2d-standard-32` | 20 + 12 | 179 s | $0.21 | 5.0 (3 VMs) |

## Results: the offshore flow

Beyond 2 km the flow differs from the every-step run by 7-30 % rms at all three intervals, and hardly shrinks with the interval (`u` 30 % at 600 s, 16 % at 30 s). A tiny perturbation test is running to see whether that is chaos; see below when it's in.

## Decision / outcome

No default changed. **For the author to decide:** adopt `STOKES_NCPL` 5 (120 s, SWAN's own step) in the A15 cases. Then 10 + 6 on `c2d-standard-16`, or 5 + 3 on `c2d-standard-8` for ensembles: smaller machines are cheaper per member and get through more members under the 100 vCPU limit per region.

## Open questions

- Tested on one case. Before using it on a bigger tide or shallower water: repeat the accuracy test, since the layers change more between updates. On bare and patchy reefs, too.
- The split was tested with `STOKES_NCPL` 5 on the 2 h benchmark only.

## Details and links

- Patch: coawst-cloud `3-experimental/roms-stokes-interval`
- Specs: `batch/ensemble/bench/a15def-*`, `a15stk-*`, `batch/ensemble/tests/stokes-int`, `stokes-ctl`, `stokes-rst`, `twin24h`
- Cost: `a15def` about $0.60, `a15stk` about $0.30, Stokes tests about $0.60
