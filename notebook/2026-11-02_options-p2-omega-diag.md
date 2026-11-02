# OMEGA_IMPLICIT on the A15 pass-jet runaway (options campaign p2-omega-diag)

- **Date:** 2026-11-02
- **Status:** done: the option does not stop the runaway (it ends 1.9 min
  earlier); DT 3 s runs cleanly with or without it, with identical
  answers, so the clean DT 3 s run is the time step's doing, not the
  option's. The analysis in the options doc (section 1.2) stands.
- **Builds:** coawst-cloud `9d93a75`

## Question / why

Phase 2 of `docs/options_test_campaign.md`, member p2-omega-diag: does
`OMEGA_IMPLICIT` (adaptive implicit vertical advection) prevent the pass-jet
blow-up of the thin_steep grid under a 2 m sea switched on at t = 0
([2026-11-02_a15-thin-crest-bottom-stress.md](2026-11-02_a15-thin-crest-bottom-stress.md),
round 2)? The options doc (section 1.2, "Why `OMEGA_IMPLICIT` did not help,
from the code") predicts no: the option only relaxes the vertical Courant
limit, and the runaway is horizontal (cross-shore Courant number above 1).
Expected: the option delays the end by a few steps or lets the run continue
with a wrong jet. If it ran cleanly to 1 h with a sane jet, the analysis
would be wrong and the option would go back on the table.

## What was run

- **Case:** coawst-cloud `tests/cases/Reef_Ideal_A15` turned into
  `Reef_Ideal_A15_thin` by `tests/experimental/roms-bstress-implicit/make_thin_crest.py`,
  grid `thin_steep` (crest 0.30 m over two rows, rx0 0.41; pass untouched).
  As in the round-2 blow-up run `bsi2-nocap-thin-steep-hs2`: explicit
  uncapped bottom stress, `-SPLINES_VVISC`, LF-AM3, DT 6 s / NDTFAST 24,
  VISC2 0.001 m2/s (the coawst-cloud test case value), SWAN north boundary
  `CONSTANT PAR 2.0 10.0 0. 4.` from t = 0 (no ramp). 60 min, history every
  10 min, quicksave every minute (eastward/northward 3-D velocity, w,
  depth means).
- **Images** (built with coawst-cloud `9d93a75`, `build.sh --case
  .../Reef_Ideal_A15_thin --app REEF_IDEAL_A15`, pushed to a private
  container registry):
  - `v3.9-cc9d93a75-reef_a15_thin_steep-base` (`-SPLINES_VVISC`):
    `sha256:f284ef940e11540be7c46872cf78b9341d8b40f6729dae7155e412cba38fadd2`
  - `v3.9-cc9d93a75-reef_a15_thin_steep-omegaimp` (`-SPLINES_VVISC +OMEGA_IMPLICIT`):
    `sha256:3dc838b6846355e2a91e7481d02c17c817db08eb12a2f62a2f8c6d5ab09489b8`
- **Runs:** Batch bridge `tools/engine_tests/batch_case.sh` (as thin_crest.sh's
  runs), ROMS 1x6 + 2 SWAN, Spot c2d-standard-8, us-east1-b. Four members:
  the three of the brief plus a control the brief did not ask for (the
  baseline at DT 3 s), needed to tell the option's effect from the time
  step's. Jobs `p2-omega-base`, `p2-omega-imp`, `p2-omega-imp-dt3` (first
  pass; their quicksaves have no 3-D u, v, see below) and
  `p2-omega-base-q`, `p2-omega-imp-q`, `p2-omega-imp-dt3-q`,
  `p2-omega-base-dt3-q` (rerun with the eastward/northward quicksave
  fields; the logs are identical step for step to the first pass).
- **Reproduction check:** the baseline log matches the round-2 run
  `bsi2-nocap-thin-steep-hs2` bit for bit at every one of its 372 steps
  (energies, Courant numbers, location, speed).
- **Cost:** 7 jobs, 0.37 VM-hours at $0.158/h Spot = **about $0.06**
  (disk and IP extra, under a cent).

## Results

| run | end | max Cu / Cv / Cw, minutes 11-34 (log, max-C point) | cross-shore Courant, pass (quicksave) 30 / 34 / 35 min | fastest point at the end | pass jet at 30 min (3-D / depth mean) |
|---|---|---|---|---|---|
| baseline, DT 6 s | blow-up 37.2 min (step 372) | 0.23 / 0.40 / 1.82 | 0.59 / 0.68 / 0.73, then 1.04 (36), 1.49 (37) | 31 m/s at i 101, j 51, k 7 (pass, mid-depth) | 1.96 / 1.75 m/s |
| `OMEGA_IMPLICIT`, DT 6 s | blow-up 35.3 min (step 353) | 0.23 / 0.40 / 1.82 | 0.59 / 0.68 / 1.13 | 23 m/s at i 101, j 48, k 8 (pass, mid-depth) | 1.96 / 1.75 m/s |
| `OMEGA_IMPLICIT`, DT 3 s | ran to 60 min | 0.12 / 0.17 / 0.66 | 0.29 / 0.34 / 0.34 (max 0.34) | 2.07 m/s at i 101, j 41, k 9 (60 min) | 1.96 / 1.75 m/s |
| baseline, DT 3 s (control) | ran to 60 min | 0.12 / 0.17 / 0.66 | identical to the line above | identical | 1.96 / 1.75 m/s |

(Log columns: ROMS's per-step Courant numbers at the point where Cu + Cv +
Cw is largest; the per-minute table for every run was kept with the run output.
Cross-shore Courant: domain maximum of |v| DT / dy from the minute
quicksaves; it sits in the pass, i 100-101, j 34-44, surface layer.
Pass jet: maximum speed over i 89-113, j 25-60.)

- **The option does not stop the runaway; it brings it forward.** With
  `OMEGA_IMPLICIT` at DT 6 s the run ends 19 steps (1.9 min) earlier, at the
  same place (the pass, i 101, mid-depth k 6-8). Its first effect on the log
  is at step 103 (10.3 min, when the waves reach the crest); the flow stays
  within 0.25 mm/s of the baseline up to 30 min, so the option is barely
  active before the end. The runaway then starts at 34.7 min instead of
  35.5 min: the fastest point moves into the pass with the cross-shore
  Courant number at 0.78-0.83, and in six steps the speed goes 2.9 -> 23 m/s
  while the vertical Courant number (full w, implicit part included) goes
  0.4 -> 6.3. The quicksave at 35.0 min already has cross-shore Courant 1.13
  in the pass.
- **The runaway is horizontal, as the options doc says.** In both DT 6 s
  runs the cross-shore Courant number in the pass climbs steadily with the
  jet (0.51 at 23 min, 0.59 at 30 min, 0.68 at 34 min, pass jet
  1.72 -> 2.35 m/s) and the run fails once it reaches about 0.75-0.8; it is
  past 1 within a minute. The vertical Courant numbers above 1 before that
  (1.8 at 11 min) are at the crest, not in the pass, and did no harm.
- **DT 3 s is what saves the run.** At DT 3 s the run is clean to 1 h with
  and without the option, and the two are identical (fields within
  6e-11 m/s, zeta identical; the option never engages because Cw stays
  below 0.76). The jet is sane: at 30 min it equals the DT 6 s runs' to
  the last digit shown (1.96 m/s at the surface, 1.75 m/s depth mean;
  the 3-D fields differ by at most 3.5 cm/s), peaks at 2.36 m/s at 37 min
  and settles near 2.0 m/s (cross-shore Courant at most 0.34). So the
  brief's "runs cleanly to 1 h" case did occur at DT 3 s, but the control
  shows it says nothing for the option.
- **Quicksave finding (COAWST v3.9 bug, output only):** the 3-D `u` and
  `v` of the quicksave file (`Qout(idUvel)`, `Qout(idVvel)`) are defined
  but never written in the serial NetCDF branch of `wrt_quick.F` (only the
  PIO branch writes them), so they come out as fill values. `u_eastward`,
  `v_northward` (`idu3dE`, `idv3dN`), `w` and the 2-D fields are written.
  Not yet reported to coawst-cloud.

## Figures

![Fastest current, cross-shore Courant number in the pass and vertical
Courant number against time for the four runs](2026-11-02_options-p2-omega-diag.png)

Made by the analysis script kept with the run output.
Top: fastest current on a log scale, line from the ROMS log at every step,
dots the pass maximum from the minute quicksaves. Middle: domain maximum of
the cross-shore Courant number |v| DT / dy from the quicksaves (in the
pass). Bottom: vertical Courant number at ROMS's largest-Courant point from
the log. The two DT 3 s runs lie on top of each other; the two DT 6 s runs
are on top of each other until 34.7 min.

## Decision / outcome

The expectation of the campaign brief holds in substance: `OMEGA_IMPLICIT`
does not cure the pass-jet runaway because the runaway is driven by the
horizontal advection (cross-shore Courant number about 0.75 and rising),
and here it even fails sooner. The clean run at DT 3 s is the time step,
not the option (identical control). The options doc's verdict ("keep off")
stands; the option stays off the table. For waves switched on without a
ramp the remedies remain the ramp (round 3 of the thin-crest entry) or a
shorter DT.

## Details and links

- [Phases 1-2 setup](2026-11-02_options-campaign-phases1-2.md)
- [2026-11-02_a15-thin-crest-bottom-stress.md](2026-11-02_a15-thin-crest-bottom-stress.md)
