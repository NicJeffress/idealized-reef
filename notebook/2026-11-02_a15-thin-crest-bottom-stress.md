# Bottom-stress schemes on thin reef crests (A15 variants)

- **Date:** 2026-11-02
- **Status:** done: 25 runs in three rounds (about $0.60 in total); the
  implicit stress equals the full explicit stress and is converged in DT; the
  cap (`LIMIT_BSTRESS`) is the scheme that changes the answer and depends on DT

## Question / why

Author: "can you do some debugging using the idealized domain into why implicit
bottom stress isn't recommended?" coawst-cloud's document of
`roms-bstress-implicit` (`BSTRESS_IMPLICIT`) then said "not recommended", based
on failures on a realistic grid with a 0.30 m crest and steep flanks (rx0 0.40),
where the capped explicit stress failed too. Can a thin, steep crest on A15
reproduce a failure, and which scheme gives the right answer? These were also
the first runs with images built by coawst-cloud.

## What was run

Reef_Ideal_A15 (crest 0.50 m over rows 31-34, 20 m rows, 10 levels, Hs 1 m /
Tp 10 s from the north, tide 0.15 m / 12 h, z0 0.01 m through `SSW_BBL`, DT 6 s,
NDTFAST 24, LF-AM3) with three grid variants written by
[`tools/reef/make_thin_crest.py`](../docs/Reef_Ideal_A15_thin_crest.md) (ROMS grid +
SWAN bathymetry; only the reef columns change, the pass is untouched):

| grid | crest | flanks (rx0) | isolates |
|---|---|---|---|
| default_1 | 0.50 m, 4 rows | 0.34 | A15 as used so far |
| thin_smooth | 0.30 m, 4 rows | rows 29-39 eased, <= 0.32 | depth alone |
| thin_steep | 0.30 m, 2 rows, 0.71 m either side | 0.41 | a narrow two-row crest |
| steep_050 | 0.50 m, 2 rows, 1.19 m either side | 0.41 | steepness alone |

Bottom layer on the 0.30 m crest: 3 cm at rest, 5.6-5.9 cm at the end of the
run (3 h; near low tide the layer is 1.5 cm). Three images from coawst-cloud
(`build.sh --case .../Reef_Ideal_A15_thin --app REEF_IDEAL_A15`, all with
`-SPLINES_VVISC`, which the option needs): `cap` (+LIMIT_BSTRESS), `nocap` (the
explicit stress as COAWST ships it), `imp` (+BSTRESS_IMPLICIT). Runs: 3 h (low
tide at 3 h), ROMS 1x6 + 2 SWAN, Spot c2d-standard-8, history every 10 min.
Wall 453-470 s each. Cost of round 1 about $0.25. Scripts: coawst-cloud
`tests/experimental/roms-bstress-implicit/` (`thin_crest.sh`,
`thin_crest_summary.py`, `cap_stats.py`).

## Results, round 1 (3 h, DT 6 s)

All 12 runs finished; no NaN, no blow-up. At 3 h:

| grid | scheme | fastest 3-D current (m/s) | max vertical Courant | crest depth-mean v (m/s) | lagoon set-up (mm) |
|---|---|---|---|---|---|
| default_1 | cap | 1.14 | 0.54 | -0.58 | 53.5 |
| default_1 | nocap | 1.01 | 0.46 | -0.50 | 42.0 |
| default_1 | imp | 1.00 | 0.44 | -0.50 | 41.4 |
| thin_smooth | cap | 1.48 | 1.56 | -0.98 | 32.4 |
| thin_smooth | nocap | 0.95 | 0.76 | -0.56 | 16.1 |
| thin_smooth | imp | 0.94 | 0.75 | -0.56 | 16.0 |
| thin_steep | cap | 1.17 | 2.03 | -1.12 | 43.3 |
| thin_steep | nocap | 0.91 | 1.21 | -0.79 | 26.1 |
| thin_steep | imp | 0.92 | 1.21 | -0.79 | 26.2 |
| steep_050 | cap | 1.11 | 0.77 | -0.56 | 51.3 |
| steep_050 | nocap | 1.06 | 0.65 | -0.53 | 46.3 |
| steep_050 | imp | 1.05 | 0.66 | -0.52 | 45.6 |

(The fastest current is in the surface layer over the pass or the crest; crest
v is `vbar` on row 32 over the reef columns, negative = into the lagoon;
set-up = mean zeta rows 5-25 minus rows 95-105.)

- **Implicit = uncapped explicit.** On every grid they agree to 1 % in the
  crest current and 1 mm in the set-up (99.9th percentile of the bottom stress
  within 1-2 %). The option changes nothing but the time discretization.
- **The cap is the outlier.** With `LIMIT_BSTRESS` the crest flow is 15 %
  faster on the 0.50 m crest and 40-75 % faster on the 0.30 m crests
  (thin_smooth: 0.98 against 0.56 m/s), the set-up 25-100 % higher. The cap
  binds at 51-67 % of the crest cells (stability number
  S = tau DT / (Hz_1 |u_1|) at 0.74-0.75) and halves the effective drag: on
  thin_steep the median crest stress is 1.75 N/m2 at a bottom-layer speed of
  0.32 m/s with the cap, 2.12 N/m2 at 0.24 m/s without it (tau/|u_1|^2 17
  against 36 kg/m3).
- **The explicit stress is stable far beyond the cap's criterion.** Without the
  cap the crest runs at S median 1.4-1.9, 90th percentile 2.9-6.3, largest
  7-11, for 3 h without trouble: the vertical viscosity (GLS) ties the thin
  bottom layer to the layers above within a step. `LIMIT_BSTRESS` (and
  `WET_DRY`, which carries it in COAWST) is far more conservative than needed.
- **No blow-up.** Neither the 0.30 m crest, nor rx0 0.41 flanks, nor both
  together blow up on A15 with any scheme, through low tide (0.15 m of water
  over the crest). The largest vertical Courant number, 2.0, is in the capped
  run; the full-friction runs stay at 1.2.

## Round 2 (thin_steep, 7 runs, about $0.15)

| run | result | crest v at 3 h | set-up |
|---|---|---|---|
| nocap, DT 3 s (NDTFAST 12) | finished | -0.792 | 26.2 mm |
| imp, DT 3 s | finished | -0.788 | 26.2 mm |
| cap + `STEP2D_FB_AB3_AM4` | finished | -1.118 | 43.3 mm |
| imp + `STEP2D_FB_AB3_AM4` | finished | -0.786 | 26.2 mm |
| cap, Hs 2 m from t = 0 (no ramp) | blow-up 34.6 min | | |
| nocap, Hs 2 m from t = 0 | blow-up 37.1 min | | |
| imp, Hs 2 m from t = 0 | blow-up 36.3 min | | |

- **Converged.** Halving DT changes the implicit and the uncapped explicit
  crest current by 0.3-0.5 % and the set-up by 0.1 mm. The stability number of
  the uncapped explicit stress at DT 3 s is still above the cap's limit at 65 %
  of the crest cells (median 0.93, largest 4.4), and the run is clean.
- **The barotropic kernel is irrelevant:** AB3-AM4 reproduces LF-AM3 to the
  last digit shown for both schemes.
- **A 2 m sea switched on at t = 0** (SWAN `CONSTANT PAR 2.0 10.0`, no ramp)
  blows up with all three schemes within three minutes of each other. The
  runaway is not on the crest: it is the jet through the pass (i 101, rows
  45-52, 14-25 m deep) at mid-depth (k 6-8), speeds rising 3 -> 30 m/s over
  eight steps with the cross-shore Courant number above 1 and the vertical one
  1.3-5. The bottom stress plays no part.

## Round 3: Hs ramped to 2 m (thin_steep, 6 runs, about $0.15)

Images rebuilt with `wavebc_north_2m.txt` (TPAR: 0.125 m at 0 h, 2 m at 1 h,
then constant), 3 h, DT 6 and 3 s:

| scheme | DT | result | fastest current | max vertical Courant | crest v | set-up (mm) |
|---|---|---|---|---|---|---|
| cap | 6 s | finished | 2.19 | 1.68 | -1.215 | 178.6 |
| cap | 3 s | finished | 1.89 | 0.66 | -1.104 | 151.1 |
| nocap | 6 s | finished | 1.81 | 1.21 | -1.051 | 139.6 |
| nocap | 3 s | finished | 1.81 | 0.61 | -1.052 | 139.6 |
| imp | 6 s | finished | 1.81 | 1.20 | -1.043 | 139.7 |
| imp | 3 s | finished | 1.81 | 0.61 | -1.044 | 139.7 |

- With the ramp every run survives 2 m seas through low tide, so the round-2
  blow-ups were the forcing shock, not the crest.
- **The cap makes the answer depend on the time step.** Its limit is
  0.75 Hz_1 |u_1| / DT, so halving DT doubles the allowed stress: the capped
  set-up drops from 179 to 151 mm (-15 %) and the crest flow from 1.22 to
  1.10 m/s, converging towards the uncapped answer (140 mm, 1.05 m/s) from
  above. The implicit and the uncapped explicit runs change by 0.1 % between
  the two steps and agree with each other to 0.8 % (bottom stress 99.9th
  percentile 16.9 N/m2 in all four).
- The remaining difference between implicit and uncapped explicit (0.8 % at
  2 m, 0.5 % at 1 m) is the stress's time level (implicit: the new velocity;
  explicit: the old one), the same order as the DT sensitivity of either.

## Decision / outcome

The "not recommended" verdict in coawst-cloud's patch document was corrected:
the option is the full bottom stress taken stably; it reproduces the uncapped
explicit stress wherever that stress is stable and replaces the cap where it is
not. A15 keeps the explicit, uncapped stress.

## Open questions

- A failure like the realistic grid's (a surface-layer runaway at crest ends)
  is not reproduced on A15: 10 m rows and crest segments ending in channels are
  the remaining differences.

## Details and links

- [docs/Reef_Ideal_A15_thin_crest.md](../docs/Reef_Ideal_A15_thin_crest.md)
- [2026-10-27 implicit bottom stress](2026-10-27_implicit-bottom-stress.md)
- coawst-cloud's patch document `roms-bstress-implicit`
