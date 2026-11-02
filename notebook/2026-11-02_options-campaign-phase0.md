# Options test campaign, phase 0: setup and submission

- **Date:** 2026-11-02 (evening)
- **Status:** done except p0-grid10; results in
  [the phases 0-2 results entry](2026-11-02_options-campaign-results-p0-p2.md)

## Question / why

The options test campaign settles the physics and numerics choices for the A15
cases in phases. Phase 0 measures the baseline's own noise on the vegetated
A15 case: how much do the metrics move when only the numerics change (DT,
NDTFAST, SWAN step and iterations, coupling interval, spectral resolution,
tiling, grid, the AB3-AM4 kernel, the spline operators, `VISC2`)? Later
candidates are then judged against that convergence envelope. The author asked
for the A15 results to be written up for this repository.

## What was run

- Baseline: `Reef_Ideal_A15_veg` (constant canopy) as in the case folder:
  `VISC2` 0, DT 6 s, NDTFAST 24, MPDATA, GLS k-epsilon (`KANTHA_CLAYSON`,
  `RI_SPLINES`), `SSW_BBL` explicit and uncapped, `WEC_VF`, `WDISS_WAVEMOD`,
  `UV_KIRBY`, spectral Stokes; SWAN `GEN3`, `FRICTION MADSEN 0.3`, `OFF QUAD`,
  `BREAKING CON 1.0 0.73`, `TRIAD`, `PROP BSBT`, `CIRCLE 72 0.04 1.0 20`,
  dt 120 s; coupling 600 s. Hs 1 m, Tp 10 s, 0.15 m tide. 24 h; metrics over
  hours 12-24 (the second tidal cycle).
- Members (one change each):

  | Member | Change from baseline | Decides |
  |---|---|---|
  | p0-base | none | the reference |
  | p0-dt3 | `DT` 3, `NDTFAST` 12, `NTIMES` doubled | the convergence noise floor |
  | p0-ndt20, p0-ndt30 | `NDTFAST` 20 (barotropic Courant about 0.97; may fail) and 30 | the usable NDTFAST range at DT 6 s |
  | p0-swan60 | SWAN `COMPUTE ... 60 SEC` | SWAN time-step convergence |
  | p0-swanit2 | `NUM STOPC 0.005 0.01 0.005 99.5 NONSTAT 2` | SWAN iteration convergence |
  | p0-cpl300 | `TI_WAV2OCN`, `TI_OCN2WAV` 300 | coupling-interval convergence |
  | p0-msc34 | `CIRCLE 72 0.04 1.0 34` | frequency resolution with triads |
  | p0-dir36 | `CIRCLE 36` | coarser directional resolution |
  | p0-tile | `NtileI` 2, `NtileJ` 5 | tiling noise (expected rounding level) |
  | p0-grid10 | the 10 m grid ([Reef_Ideal_A15_veg_10m](../docs/Reef_Ideal_A15_veg_10m.md)), DT 3 s | grid convergence at 20 m |
  | p0-ab3am4 | image with `+STEP2D_FB_AB3_AM4`, `NDTFAST` 24 | whether A15 switches barotropic kernels |
  | p0-splvv | image with `-SPLINES_VVISC` | the vertical viscous operator alone |
  | p0-splvd | image with `-SPLINES_VDIFF` | the vertical diffusive operator alone |
  | p0-visc001 | `VISC2` 0.001 | confirms the change to 0 is invisible |

- Metrics, computed by one comparison script for every member: lagoon set-up
  (rows 5-25 minus the offshore band; mean and range), cross-crest (row 33) and
  pass transport, crest and pass jet (99th percentile and maximum of
  depth-averaged speed), surface-to-depth-mean speed ratio on crest and
  forereef, Hs on the crest and reef flat, SWAN surface dissipation across the
  reef, lagoon flushing time, Courant numbers and the fastest current from the
  log, wall time per simulated hour. The script was checked on the thin-crest
  runs of the same day (implicit vs uncapped explicit: 1 % in every flow
  metric; capped: 10-25 %).
- Images built with coawst-cloud (`9d93a75`, `VISC2` 0, compressed output):
  base, `-ab3am4`, `-nosplvv`, `-nosplvd`, `_10m`. One Batch job per image;
  24 h, c2d-standard-16 Spot, 10 + 6 processes, 4 h restart segments, up to six
  members in parallel. Expected cost of phase 0 about $1.50.

## Results

Pending.

## Decision / outcome

Pending. Decision rule: anything within the p0-dt3 envelope counts as
converged; a later candidate that moves a metric by less than that envelope is
reported as "no effect". If p0-ab3am4 is within the envelope, AB3-AM4 becomes
the A15 default.

## Open questions

- p0-ndt20 may fail (barotropic Courant about 0.97): a failure is a result.
- p0-grid10 is about 8x the baseline cost per simulated day (4x cells, DT
  halved).

## Update, 2026-11-02 20:10: p0-grid10 rerun

The first p0-grid10 run blew up within its first minute of wall time
(`Blowing-up`, ROMS main3d). Its hand-written `ocean.in` had `NDTFAST` 12
at DT 3 s: a 0.25 s fast step on 10 m cells, barotropic Courant number about
1.6 against a limit of about 0.9. The refinement script itself keeps
`NDTFAST` (fast step halves with DT, Courant number stays about 0.8); only
the member's template was wrong. Rerun as `options-p0-grid10b` with
`NDTFAST` 24. The failure is not a grid-convergence result.

Also: the single-member jobs were moved out of the first region (its disk
quota, 500 GB, held five 100 GB boot disks) to other regions with 50 GB
disks, so the 15 members run side by side.

## Details and links

- [results/README.md](../results/README.md)
- [docs/Reef_Ideal_A15_veg.md](../docs/Reef_Ideal_A15_veg.md)
- [2026-11-02 thin-crest entry](2026-11-02_a15-thin-crest-bottom-stress.md)
