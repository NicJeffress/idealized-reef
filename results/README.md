# Results: what the options campaign has shown so far

A running summary of what the options test campaign (November 2026) has
taught us about the physics and the numerics of the idealized reef cases,
kept up to date as runs finish. The numbers come from the notebook entries
linked in each section, where the full tables, figures and run details are.
Percentages are differences between 24 h runs, over hours 12-24 (the second
tidal cycle), unless stated.

**Last updated:** 2026-11-12.

Entries: [Coriolis and particles](../notebook/2026-11-12_coriolis-and-particles.md),
[seven-day stratified run](../notebook/2026-11-06_seven-day-stratified.md),
[making A15 faster](../notebook/2026-11-05_speed-stokes-and-machines.md),
[seven-day run](../notebook/2026-11-05_seven-day-run.md),
[default check](../notebook/2026-11-04_default-check.md),
[all defaults](../notebook/2026-11-04_all-defaults.md),
[force shapes and budget](../notebook/2026-11-04_force-shapes-and-budget.md),
[results p0-p2](../notebook/2026-11-02_options-campaign-results-p0-p2.md),
[triads-on](../notebook/2026-11-02_options-triads-on.md),
[SWAN triads](../notebook/2026-11-02_swan-triads-skipped-first-iteration.md),
[OMEGA_IMPLICIT](../notebook/2026-11-02_options-p2-omega-diag.md),
[island first runs](../notebook/2026-11-02_island-a15-first-runs.md),
[phases 1-2 setup](../notebook/2026-11-02_options-campaign-phases1-2.md),
[thin crests](../notebook/2026-11-02_a15-thin-crest-bottom-stress.md).

**Correction, 2026-11-04:** every "flushing time" here and in entries before this date is about 8x too long, and its relative changes don't carry over: `tests/options_compare.py` divided the lagoon volume by what is nearly only the Stokes transport. The density-1 default's 65.8 h is really 7.9 h. Fixed; [default check](../notebook/2026-11-04_default-check.md).

## The headline

1. **SWAN's triads were never computed in coupled runs, and they matter more
   than anything else we tested.** SWAN skipped the triad source term in the
   first iteration of each time step whenever there are currents, and a
   coupled run does one iteration per step. Fixed in coawst-cloud
   (`swan-triads-nonstationary`). With triads acting:
   - dense canopy everywhere: lagoon set-up **5.6x** (3.9 against 0.7 mm),
     transport over the crest **3.3x**, Hs on the crest **+86 %**;
   - bare reef: set-up **+46 %** (62 against 42 mm), crest transport +24 %,
     crest and pass jets +13 to +21 %.

   The likely mechanism on the canopy: triads move wave energy to higher
   frequencies, whose orbital motion reaches the bed less, so the canopy
   dissipates less of it and more reaches the crest and breaks there.
2. **The canopy controls the reef's circulation.** A realistic canopy
   (density 1 per m², frontal area 0.2) gives a set-up of 18 mm and a crest
   jet of 0.29 m/s, between the bare reef (62 mm, 0.83 m/s) and the dense
   test canopy. A dense canopy (4 plants
   per m², 0.5 m diameter, 0.4 m tall) everywhere cuts the lagoon set-up by
   94 % and the crest transport by 85 % against the bare reef (3.9 against
   62 mm, 203 against 1396 m³/s; crest jet 0.10 against 0.83 m/s; all with
   triads); a patchy canopy (30 % dense, 30 % sparse) sits in between.
3. **Once the triads act, the time stepping and SWAN settings are well
   converged, but the 20 m grid is not:** halving the grid spacing lowers the
   set-up by 16 % and the crest transport by 11-18 %, because the narrow
   breaking zone at the top of the fore reef is only two or three 20 m cells
   wide. The other physics choices (triads, canopy,
   breaking) still move the answer more.

## Physics

| Question | Answer | Size of the effect | Entry |
|---|---|---|---|
| Turbulence closure on the heated reef (k-epsilon KC / Canuto-A, gen, k-omega) | **k-epsilon is fine**: Canuto-A within 1-3 %; gen within 5 % (crest shear 10 %); k-omega odd in the lagoon (AKt at the background, weaker mean stratification), needs a look; `VEG_TURB` itself 2-8 % | 5-10 % | closure entry (dense canopy); **k-epsilon, Kantha-Clayson, `VEG_TURB` on adopted** |
| Wave streaming: the wave momentum lost to bottom friction (`BOTTOM_STREAMING`) | **first-order**: bottom alone set-up +57 %, crest transport +22 %; **bottom + canopy (`VEG_STREAMING`) set-up +95 %, crest +32 %, pass +29 %, jets +27-35 %**; stable at DT 6 s (= DT 3 s), no cost | without them 60 % of the dissipated wave momentum pushes no water | wave-streaming entry; **adopted** |
| Triads (`TRIAD`) | first-order; must be on, with the SWAN fix | without them: set-up -82 % (dense canopy), -61 % (density-1 canopy), -32 % (bare) | triads-on, density-1 |
| Wave breaking formulation, with triads | CON 0.73 and CON 0.80 agree within 1 % on the realistic canopy; `BKD` gives 7-11 % more set-up, crest transport and crest jet; `TG` (Thornton-Guza) leaves the flow within 3 % but changes the fore-reef shear, crest Hs and flushing | density-1 canopy: BKD set-up +8 %, crest jet +11 %; TG forereef shear +62 %, Hs crest -18 %, flushing +33 % (dense canopy: similar spread) | density-1, triads-on |
| ... without triads (for the record) | the spread looked huge | set-up -24 % to +108 %: an artefact of the missing triads | results p0-p2 |
| Turbulence from breaking (`TKE_WAVEDISS + ZOS_HSIG`) | **with triads it behaves as expected**: less surface-intensified fore-reef flow and a slower crest jet; **adopted 2026-11-03** (author). (With triads off it had increased the fore-reef shear: an artefact of the missing triads) | density-1 canopy: forereef surface/mean speed -32 %, crest jet -17 %, set-up -9 %, crest transport -5 % | density-1 |
| Whitecapping on opposing currents (`WCAP AB ... CURRENT`) | no effect on A15 | < 1 % | results p0-p2 |
| Wave roller (`ROLLER_RENIERS`) | blew up at DT 6 s: COAWST advects the roller with one explicit step per DT (Courant 1.1-1.6 on the crest); **fixed** with sub-steps (coawst-cloud `roms-roller-substeps`): DT 6 s now equals DT 3 s within 0.1 %. **Real physics, linear in `WEC_ALPHA`**: its effect grows on the refined breaking-zone grid, and with it the grid sensitivity drops; restarts to round-off with `roms-restart-roller`. Recommended on, `WEC_ALPHA` 0.5, with 0.25/1.0 as a sensitivity pair (author's decision) | `WEC_ALPHA` 0.25/0.5/1.0: set-up +12/+25/+50 %, crest transport +8/+15/+30 %; band grid 0.5: set-up +32 %, crest +19 % | roller entry; roller checks |
| Wave-number-dependent current to SWAN (`UV_BANIHASHEMI` instead of `UV_KIRBY`) | **no practical difference**: keep `UV_KIRBY` (the two are alternatives; the first build had both, which does not compile) | within 0.5 % (forereef shear ratio +5 %), wall time +5 % | VEG_HMIXING entry; run 2026-11-03 |
| Canopy-edge viscosity (`VEG_HMIXING`) | does not compile since COAWST v3.6, which dropped its routine (`vegetation_hmixing.F`) but kept everything else; nothing replaces it | - | VEG_HMIXING entry |
| Mixing at rest (the unexplained 1e-3 m²/s on the backreef) | **the GLS minimum-TKE floor** (`GLS_Kmin` 7.6e-6), not the canopy turbulence (identical with `VEG_TURB` off); `GLS_Kmin` 1e-8 removes it | lagoon diffusivity at rest 7.4e-4 -> 5.1e-6 m²/s (150x); the calm lagoon keeps its stratification | results p0-p2, Kmin at rest |
| Lower TKE floor (`GLS_Kmin` 1e-8; see [docs/gls_kmin.md](../docs/gls_kmin.md)) | diffusivity falls to the background (`AKT_BAK`) wherever the water is quiet; **stable in 72 h heated runs** (1e-10 too, same answer). On the forced, heated reef it changes temperatures by a few percent at most; offshore below the mixed layer it cuts the diffusivity tenfold (matters over weeks). **Recommended for every A15 case** (author's decision), with `AKT_BAK` 5e-6 and `AKV_BAK` 5e-5 reported as the quiet-water mixing | heated 72 h: lagoon daily range 1.92 -> 1.94 C, fore-reef stratification +5 %, offshore AKt 4.7e-5 -> 5.1e-6 m²/s; AKV_BAK 5e-6: fore-reef AKt +16 % | Kmin at rest; Kmin heated 72 h |
| Stability functions (`CANUTO_A` instead of Kantha-Clayson) | small on the flow, noticeable on the temperature | SST range +29 %, flow within 4 % | results p0-p2 |
| Nonlinear equation of state (`NONLIN_EOS`), heated reef, 72 h | no new pressure-gradient error at rest; no effect when heated | < 0.5 % everywhere, reef-flat temperature included | results p0-p2 |
| Heated reef (1000 W/m² peak, balanced over the day) | the reef-flat surface temperature swings 2.6 C a day | - | results p0-p2 |
| Bottom stress: implicit (`BSTRESS_IMPLICIT`) vs explicit | the same on the bare reef; **now the default** | 0-3 % (forereef shear ratio -6 % with triads, -17 % without) | results p0-p2, new-defaults check |
| Bottom-stress cap (`LIMIT_BSTRESS`) | changes the answer and depends on DT; do not use without a DT check | set-up +15 %, crest jet +13 % (bare reef) | results p0-p2, thin crests |
| Momentum budget, density 1 (measured, closes to 1e-7) | of the wave force (47 % breaking and roller, 53 % streaming), pressure takes 41 %, canopy drag 37 %, bed stress 24 %. The force acts on the crest front, where pressure takes 84 % of it; 69 % of the canopy drag acts in the 80 m behind it | sea level -13 to +78 mm across the crest front, +33 mm behind, +26 mm in the lagoon | default check |
| Canopy on the reef only instead of everywhere (density 1) | the difference is the way out: crest sea level the same, lagoon lower, the head loss through the lagoon and pass gone | set-up -22 %, range -17 %, transports +3 %, pass jet +9 %, Hs crest +0.3 % | default check |
| How far the pass jet goes (default, 24 h) | **no natural end in the domain**: reaches the 5 km boundary by about hour 18; offshore-going transport grows to 5x the pass outflow; 40 m wide at 1.75-2.5 km on both grids. Boundary feedback on the reef not yet known | 0.42 m/s at 1.2 km, 0.27 at 2 km, 0.04 at 4 km | jet and 10 m limit |
| Round island with passes (Island_A15) | wave-driven island-lagoon circulation: inflow over the windward reef, outflow through every pass, the leeward one most; the windward pass drains too | ~1150 m³/s in over the reef; 2 passes: 590 (windward) and 704 m³/s (leeward) out | island first runs |

## Numerics

| Question | Answer | Size | Entry |
|---|---|---|---|
| Bare reef on the breaking-zone grid at DT 6 s | **blows up** (58 min, top of the fore reef: cross-shore Courant 1 on the 10 m rows; the flow is 3-4x faster without the canopy) | runs at DT 3 s | limiters entry (bare update) |
| `SPLINES_VDIFF` | **inert with MPDATA tracers** (bit-identical): the spline vertical diffusion is used only for non-MPDATA tracers | - | closure entry |
| Vertical resolution (N 10 / 15 / 20) | **N 10 not converged**: set-up -7 % at N 15, -10 to -12 % at N 20; crest and pass flow +2 to +3 %, pass jet +9 %; N 20 needs DT 3 s; N 15 at DT 6 s clean | 10 % in set-up; cost +7 % (N 15), 2.7x (N 20, DT 3 s) | vertical-resolution entry; **N 15 adopted** |
| SWAN refraction / frequency-shift limiters (`CTHETA`, `CSIGMA`), upwind direction (`DIRIMPL 1`) | **not needed on A15**: defaults converged | `CTHETA` 0.9 within 0.7 % (bare reef: 0.8 %); `CSIGMA` never acts; `DIRIMPL` 1 within 1 % | limiters entry |
| **Time step, all defaults (`BKD`, streaming, N 15)** | **DT 2.5 s, `NDTFAST` 10 adopted**: every Courant number below 1 across the roughness and canopy range. DT 6 s stable on density 1 but Cw above 1 on 96 % of steps (peak 2.65, numerical: DT 3 s cuts it 13x); DT 3 s still Cw 1.39 at low tide on a smooth bare reef; DT 2.5 s 0.61 | DT 3 s vs DT 6 s, density 1: set-up +4.4 %, crest transport +3.0 %, range +8.0 %. Cost: DT 3 s 1.84x DT 6 s, DT 2.5 s 1.22x DT 3 s | all defaults |
| The default at DT 2.5 s, density 1 | **all below 1**: Cu 0.018, Cv 0.17, Cw 0.16. Same answer as DT 3 s; DT 2.5 s is for the smooth end of the range | within 0.02 %, sea level 8 micrometres rms; 1.17x cost | default check |
| Band grid with today's defaults against the rest of the domain refined 2x (density 1) | **the band grid is good**: sea level within 0.2 mm along the reef | set-up +0.5 %, transports within 0.6 %, jets within 1.5 %, Hs -2.2 to -2.5 %; 3.88x cost | default check |
| 5 m rows in the breaking zone | **blows up at DT 2.5 s** (hour 1.8, Cw 3-5 in the top layer), clean at DT 1.25 s. **The 10 m band is within 4 % of it.** A finer grid needs its own DT check; stability may depend on DT over the row spacing (not separated from a plain DT limit) | set-up -3.9 %, transports -2 to -3 %, Hs crest -3 %, jets within 2.3 %; 2.48x cost | default check |
| Vertical levels with streaming on | **N 15 converged**: N 20 within 2.8 % in set-up, 1 % in transports, 4 % in pass jet and fore-reef shear | 1.33x cost | force shapes |
| Vertical shape of the breaking force | **matters little for bulk flow**: Kumar et al. 2012's form within 0.7 %, uniform -4.7 % in set-up; fore-reef shear is sensitive (-5.4 %, +43 %). Stock COAWST's length is D/2 pi (a_b about 0.29-0.45 against Uchiyama's best 0.1-0.2) | under 5 % | force shapes |
| Vertical shape of the bottom streaming force (`KWD` cap) | **matters little**: cap 200 -1.8 %, cap 5 +6.1 % in set-up; no paper has a cap like 20 | transports within 1.3 % | force shapes |
| `BKD` breaker index, frozen in every non-stationary run once accuracy reaches 95 % | **harmless on A15**: never frozen within 2e-6 mm of set-up; where kD < 1 it depends only on the bed slope. Recheck on other domains | none | all defaults |
| Time step DT 6 vs 3 s (bare reef, triads on: a flow that moves) | converged | <= 1.6 % (forereef shear 3.4 %) | triads-on |
| ... on the dense canopy | converged, but only because the canopy damps the flow | ~1e-5 | results p0-p2 |
| NDTFAST 20 or 30 instead of 24 | no effect | ~1e-5 | results p0-p2 |
| AB3-AM4 barotropic kernel (`STEP2D_FB_AB3_AM4`) | as accurate as LF-AM3, faster; **now the default** | within the noise; wall time -18 to -19 % | triads-on |
| SWAN iterations per step (with the fix) | one is enough | 1, 2, 5 iterations within 0.6 % (canopy), 2 % (bare) | triads-on |
| SWAN time step 60 vs 120 s | no effect (tested with triads off) | ~1e-5 | results p0-p2 |
| Directions (36 / 72 / 144) | **converged at 72 with the 30-degree spread** (within 1 % of 144; 36 within 3 %). With the old 4-degree swell they converged slowly (the bins did not resolve the spread) | 30 deg: 36 -3 %, 144 +1 % (set-up); 4 deg: 36 -16 %, 144 +5 % | spread-30, spectral resolution |
| Frequencies (20 / 34 / 48) | converged by 34; 20 is about 3 % low; **34 adopted 2026-11-03** | 34 vs 20: set-up +3 %, crest transport +1.5 %; 48 = 34 within 0.4 % | spectral resolution |
| Coupling interval | **600 s is converged**: 240 s (2 SWAN steps, 40 ROMS steps; checked in the coupler log) changes nothing beyond 0.1 % (set-up range 0.8 %). The interval must be a multiple of both models' time steps: 300 s with SWAN at 120 s was silently replaced by 600 s | 240 vs 600 s: <= 0.1 % | results p0-p2; 240 s run 2026-11-03 |
| Tiling (2 x 5 vs 1 x 10) | rounding level | 1e-7 | results p0-p2 |
| `VISC2` 0.001 vs 0 | invisible; 0 is the default | ~1e-5 | results p0-p2 |
| Vertical viscous operator (`SPLINES_VVISC` off) | small; needs to be off for the implicit schemes | crest surface/mean speed +11 % (canopy) | results p0-p2 |
| Vertical diffusive operator (`SPLINES_VDIFF` off) | untestable on a case with T and S fixed (bit-identical); to test on the stratified case | - | results p0-p2 |
| Explicit canopy drag at DT 6 s | fails once triads act on the dense canopy (fore-reef bed, 2 alpha \|U\| DT ~ 6); fine on the density-1 canopy (within 3 % of implicit) | dense: 6 of 8 runs blew up | triads-on, density-1 |
| Implicit canopy drag (`VEG_DRAG_IMPLICIT`) | as accurate as explicit at DT 3 s, stable at DT 6 s; **now the default** | within 2.5 % (patchy canopy); 37 % faster | results p0-p2 |
| `OMEGA_IMPLICIT` (implicit vertical advection) on a crest-jet blow-up | no help: the runaway is horizontal; a shorter DT is what saves the run | blows up 1.9 min sooner | OMEGA_IMPLICIT |
| 10 m grid instead of 20 m | **not converged at 20 m**: the breaking zone (2-3 cells at 20 m) is under-resolved. **Refining only that zone across the shore** (10 m rows from 850 to 1150 m) recovers the uniform 10 m answer at +16 % cost (instead of 8x) | 20 m vs 10 m: set-up -16 %, crest transport -11 %; band grid = 10 m for set-up, pass transport and jets | grid-10m |

## Rotation (2026-11-12)

Every A15 grid had f = 0 until now. With uniform f at 17.5°S (tropical South Pacific) or 40°S, the reef and lagoon don't change: transports within 0.5 %, set-up within 0.2 %, waves the same; only the fore-reef shear grows (surface to depth-mean speed +21-25 %). Offshore everything changes: the pass jet turns left (southern hemisphere). At 17.5°S it bends about 13° and still runs most of the way across the 5 km domain; at 40°S it hooks 3.5 km out and feeds one clockwise eddy per pass, which never reaches the boundary. Particles released over the whole back reef at 40°S leave within about 2 days, and from day 4 a few percent come back over the crest from the eddy. With stratification (N² 1e-4) the jet stays a surface jet that runs straight offshore into the north boundary. [Entry](../notebook/2026-11-12_coriolis-and-particles.md).

## How long a run has to be (2026-11-05)

Seven days of the default canopy case (density 1, unstratified, steady waves): **the reef and lagoon settle within the first tide.** Hours 12-24 against hours 156-168: set-up +0.05 %, crest and pass transport +0.04 and +0.03 %, Hs crest +0.01 %, and every budget term within 0.1 % of the largest. TKE and `AKv` on the reef and in the lagoon settle just as fast (rms under 0.15 % in every layer); past the crest `AKv` doesn't (1150-2000 m 13 % low on day 1, 3.8-5 km 86 % low). Offshore of about 2.5 km the slow recirculation keeps growing all week (offshore-going transport at 4 km +50 %), and the jet spreads along the 5 km boundary, so the outer 1.5 km depends on that boundary; none of it reaches the reef. Restarted segments are bit-identical to an uninterrupted run; only the first hourly diagnostic record after a restart is off (`*_accel` mainly). Not yet shown for stratified or heated cases, or for residence time. [Entry](../notebook/2026-11-05_seven-day-run.md).

**Bare and patchy reefs settle the same way.** Hours 12-24 against 60-72: set-up +0.02 and +0.07 %, transports within 0.05 %, budget within 0.12 %, and TKE and `AKv` under 1 % rms on the reef and in the lagoon. Peak Cw 0.44 and 0.67. Offshore-going transport agrees to about 2 km and not past 2.5 km. Past the crest the faster reefs are unsteady (bare TKE 35 % rms at 1.5-2 km), and that doesn't fade with time. So 24 h members, averaged over hours 12-24, hold for the reef and lagoon across this range; hours 0-12 are about 5-6 % low. [Entry](../notebook/2026-11-05_settling-bare-patchy.md).

**Stratified, seven days ([entry](../notebook/2026-11-06_seven-day-stratified.md)):** reef and lagoon flow settle much as without stratification. Hours 12-24 against 156-168: transports +0.04 %, budget terms above 0.02 out to 1150 m within 0.6 %, TKE within 1.6 % rms, peak Cw 0.16. Set-up is 0.8 % low on day 1 and settled to about 0.2 % by about hour 72, so 24 h members still hold, and about 3.5 days removes that offset. What doesn't settle in a week: `AKv` in the lagoon (22 % rms on day 1, still 20 % on day 3) and at the crest front, the flow past 1.2 km (offshore-going transport at 2 km doubles around hours 48-72, then swings by about 10 %), and temperature. With no surface fluxes, the lagoon cools 0.18 °C from day 1 to day 7, and the domain warms 0.027 °C per day because Stokes drift brings in warm surface water and the return flow takes out cooler water. Deep-water `AKv` is 0.4 % of the unstratified value.

## Speed (2026-11-05)

ROMS spent 59 % of its time in the WEC kernel, nearly all re-summing the spectral Stokes drift every step on an unchanged spectrum. `roms-stokes-interval` (A15 default since 2026-11-06, off elsewhere) updates it `STOKES_NCPL` times per wave exchange: at 120 s, 2.2x faster, set-up within 0.003 %, transports within 0.002 %, budget unchanged, restarts exact at a 600 s update (120 s not run separately). **The offshore flow isn't repeatable past the first day or so:** 1e-6 m of noise at the start, run 72 h, makes 4-5 km snapshots as different as the run's own one tide apart (60-70 %) by about hour 34, and 2-4 km by about hours 60-72. Tide-mean transport then differs by chance by up to 14 % at 4.5-4.9 km, 2.6 % at 4 km, 0.6 % at 3 km, 0.13 % at 2 km. It reaches the reef from hours 26-30 and levels off by about hour 48, at a **chance level of about 0.03 % of set-up and 0.01 % of transports** in tide means. A tiny seed gives these times; larger ones are quicker. At 120 s the first day's tide-mean transport departs by 1 % at 3.5-4 km and 4 % at 4.9 km, against under 0.13 % at 30 s, but that's no larger than chance reaches within two more days, so 120 s (`STOKES_NCPL` 5) is enough; 30 s is about 13 % slower. With it on, 10 + 6 stays the best split on `c2d-standard-16`; `c2d-standard-8` with 5 + 3 is cheapest per member ($0.14 per simulated day). [Entry](../notebook/2026-11-05_speed-stokes-and-machines.md).

## Changes adopted on 2026-11-06 (author's decision)

- **Spectral Stokes drift updated every 120 s, not every step** (`STOKES_INTERVAL`, `STOKES_NCPL` 5), in `Reef_Ideal_A15`, `_veg`, `_veg_strat` and `_veg_therm`, from the next image. 2.2x faster on density 1, where set-up stays within 0.003 % and transports within 0.002 %. Not yet run on bare, patchy, stratified or thermal. [Entry](../notebook/2026-11-06_stokes-120s-and-a15-state.md).

## Changes adopted on 2026-11-04 (author's decisions)

- **DT 2.5 s, `NDTFAST` 10 in every A15 case**, to stay below the CFL limits; DT 6 s then DT 3 s were not enough.
- **Canopy stays over the whole domain, density 1** (reef only would lower set-up 22 %, through head loss on the way out).
- Momentum budgets close (`roms-diag-implicit-drag`); restarts with `BKD` exact (`swan-bkd-exact-restart`).

## Changes adopted on 2026-11-03 (author's decisions)

- `TKE_WAVEDISS` + `ZOS_HSIG` in every A15 case.
- 34 SWAN frequencies instead of 20 (converged; 20 was about 3 % low).
- A 30 degree directional spread for the incoming waves (all A15 cases and the
  islands); the 4 degree spread of the v3.7 project was narrower than SWAN's
  direction bins, which made the answer depend on the number of directions.
  With it, 72 directions is converged (144 within 1 %).
- The new baseline (density-1 canopy): set-up 12.5 mm, crest transport
  465 m³/s, crest jet 0.24 m/s; about a third less set-up than with the old
  4-degree swell. Runs take 60 % longer with 34 frequencies.
- Later the same day: the **Reniers roller** on (`WEC_ALPHA` 0.5) and the
  **breaking-zone grid** (rows 850-1150 m from shore at 10 m, 203 x 126) as
  the default grid of every A15 case; bed roughness under a canopy is allowed
  (one or the other is a suggestion, not a rule), `GLS_Kmin` 1e-8 (the
  quiet-water mixing is then `AKT_BAK` 5e-6 / `AKV_BAK` 5e-5, kept deliberately), and SWAN's `BKD` breaking
  (Salmon et al. 2015; 7-11 % more set-up and crest transport than `CON 0.73`),
  15 vertical levels, and wave streaming from bottom friction and the canopy
  (`BOTTOM_STREAMING`, `VEG_STREAMING`; set-up +95 %)
  ([new defaults](../notebook/2026-11-03_new-defaults.md)). SWAN's refraction
  limiters changed nothing (within 1 %); N 10 levels was not converged (set-up
  -7 % at N 15, -10 to -12 % at N 20): **N 15 adopted** (DT 6 s); wave streaming is
  being tested.

## Problems found in the code along the way

| Problem | Status |
|---|---|
| With `TS_FIXED`, ROMS computed the depth-averaged densities of the barotropic pressure gradient once, at start-up: a restarted run used those of the restart time (3.7e-7 m/s off after 4 h) | fixed: coawst-cloud `roms-ts-fixed-density` (restarts bit-identical) |
| SWAN never computed `TRIAD` in coupled runs (first-iteration guard with currents) | fixed: coawst-cloud `swan-triads-nonstationary` |
| The Reniers roller took one explicit step per DT (`numits=1`; 30 commented out): unstable at DT 6 s on a reef crest | fixed: coawst-cloud `roms-roller-substeps` |
| The Reniers roller area `rollA` was not in the restart file: each restarted segment began with no roller (1.4e-4 m/s off after 4 h) | fixed: coawst-cloud `roms-restart-roller` stores `rollA` and `Dissip_roller` and does not step the roller twice in the first restarted step (A15 test: 6.4e-4 m/s before, 5.8e-11 after, round-off) |
| ROMS never wrote the quicksave file's 3-D `u`, `v` (standard NetCDF writer) | fixed: coawst-cloud `roms-quicksave-uv` (already fixed in upstream ROMS) |
| `VEG_HMIXING`: COAWST v3.6 dropped its routine and kept the rest | explained ([entry](../notebook/2026-11-03_veg-hmixing-and-banihashemi.md)); a port is possible |
| A coupling interval that is not a multiple of both models' steps is silently replaced (300 s ran as 600 s) | noted; check the coupler log (`CplInt` and `Steps`) |
| `UV_BANIHASHEMI` "did not compile" | our configuration: it replaces `UV_KIRBY`, it cannot be added to it |
| `BKD`'s one-way switch `MODGAM` was not in the restart file: restarted runs recomputed the breaker index once (1e-7 m/s after an hour, 5e-5 m/s later) | fixed: coawst-cloud `swan-bkd-exact-restart`, bit-identical over three segments |
| With implicit bottom stress and canopy drag, `*_bstr` held only the explicit remainder and the canopy drag was missing or mixed into `*_vvis`; `*_fveg` never written | fixed: coawst-cloud `roms-diag-implicit-drag`, 2-D and 3-D budgets close to 1e-7 of the largest term; solution bit-identical |

## Defaults adopted on 2026-11-02 (author's decision), checked

In every A15 case: the AB3-AM4 barotropic kernel, the implicit bottom
stress, `SPLINES_VVISC` off; in the canopy cases also the implicit canopy
drag. Images must be built with coawst-cloud `2d5672c` or later so that
`TRIAD` acts.

Check runs, 24 h with triads
([entry](../notebook/2026-11-03_a15-new-defaults-check.md)): on the bare reef
the new defaults agree with the old settings within 0-3 % (set-up +1.3 %,
crest transport +0.4 %, jets up to +3.3 %; the set-up's tidal range and the
forereef shear ratio -6 %); on the constant canopy within 2.3 % except the
mean set-up (-6.7 %, from the implicit bottom stress). The patchy canopy and
the stratified case run stably at DT 6 s. **Every A15 run is about 20 %
cheaper** (65-75 instead of 81-84 s of wall time per simulated hour).

## Still open

- **Run length and machine for ensemble members:** the author's call. Recommended: 24 h averaged over hours 12-24, on `c2d-standard-8` with 5 + 3. [State of the default](../notebook/2026-11-06_stokes-120s-and-a15-state.md).
- `STOKES_NCPL` 5 on the bare reef, patchy canopy, stratified and thermal cases: not run yet.
- **Is the size of the streaming force right?** It is 53 % of the wave force on density 1 and now the main unverified piece: the total
  follows Luhar et al. 2010 and Beudin et al. 2017, its vertical shape is our choice, and Beudin says it is unverified. At density 1, A/S is below
  Luhar's limit of 1 everywhere on the reef.
- Grid checks so far are on density 1 with a canopy uniform alongshore: repeat on the bare or smooth end, or with patches, if those become ensemble cases.
- Before a bed-roughness axis: `FRICTION MADSEN` per member, since SWAN uses the larger of it and the coupled KN (the cases hold 0.3).
- Later, once the physics and numerics are settled: the list of ensemble axes
  (bed roughness, canopy parameters, `BKD` parameters, `WEC_ALPHA`, `SZ_ALPHA`,
  `ZOS_HSIG_ALPHA`, ...) and lagoon residence time with ROMSPath.
- `TKE_WAVEDISS`, the roller and the breaking
  formulations on the stratified and heated cases with triads on; (`SPLINES_VDIFF`: inert with MPDATA.)
- `UV_BANIHASHEMI` instead of `UV_KIRBY`: no difference on A15 (within 0.5 %); to
  reconsider, and check on every new domain with sheared currents (a pass jet,
  a wind-driven surface current) and waves spanning kD ~ 1.
- Infragravity waves: none of the runs has them; a standalone SWAN `SURFBEAT`
  estimate of their energy on the reef flat is the planned first step.
