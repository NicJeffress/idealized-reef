# Results: what the options campaign has shown so far

A running summary of what the options test campaign (November 2026) has
taught us about the physics and the numerics of the idealized reef cases,
kept up to date as runs finish. The numbers come from the notebook entries
linked in each section, where the full tables, figures and run details are.
Percentages are differences between 24 h runs, over hours 12-24 (the second
tidal cycle), unless stated.

**Last updated:** 2026-11-03 01:00 UTC.

Entries: [results p0-p2](../notebook/2026-11-02_options-campaign-results-p0-p2.md),
[triads-on](../notebook/2026-11-02_options-triads-on.md),
[SWAN triads](../notebook/2026-11-02_swan-triads-skipped-first-iteration.md),
[OMEGA_IMPLICIT](../notebook/2026-11-02_options-p2-omega-diag.md),
[island first runs](../notebook/2026-11-02_island-a15-first-runs.md),
[phases 1-2 setup](../notebook/2026-11-02_options-campaign-phases1-2.md),
[thin crests](../notebook/2026-11-02_a15-thin-crest-bottom-stress.md).

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
2. **The canopy controls the reef's circulation.** A dense canopy (4 plants
   per m², 0.5 m diameter, 0.4 m tall) everywhere cuts the lagoon set-up by
   94 % and the crest transport by 85 % against the bare reef (3.9 against
   62 mm, 203 against 1396 m³/s; crest jet 0.10 against 0.83 m/s; all with
   triads); a patchy canopy (30 % dense, 30 % sparse) sits in between.
3. **Once the triads act, the time stepping and SWAN settings are well
   converged, but the 20 m grid is not:** halving the grid spacing lowers the
   crest transport by 18 % and the set-up by 15 % (dense canopy, triads off;
   being repeated with triads). The other physics choices (triads, canopy,
   breaking) still move the answer more.

## Physics

| Question | Answer | Size of the effect | Entry |
|---|---|---|---|
| Triads (`TRIAD`) | first-order; must be on, with the SWAN fix | set-up x5.6 (canopy), +46 % (bare) | triads-on |
| Wave breaking formulation, with triads | `BREAKING CON 1.0 0.73`, `CON 1.0 0.80` and `BKD` agree; `TG` (Thornton-Guza) is the outlier | CON 0.80 / BKD: set-up -4 / +6 %, crest transport -5 / +8 %; TG: set-up +12 %, forereef shear +145 %, breaking dissipation +45 % | triads-on |
| ... without triads (for the record) | the spread looked huge | set-up -24 % to +108 %: an artefact of the missing triads | results p0-p2 |
| Turbulence from breaking (`TKE_WAVEDISS + ZOS_HSIG`) | stable; small on the reef, but it increases the forereef shear, the opposite of what was expected; not adopted (tested with triads off) | crest transport -8 %, crest jet -17 to -20 %, forereef surface/mean speed +23 to +42 % | results p0-p2 |
| Whitecapping on opposing currents (`WCAP AB ... CURRENT`) | no effect on A15 | < 1 % | results p0-p2 |
| Wave roller (`ROLLER_RENIERS`, `WEC_ALPHA` 0.5) | blew up at 23 min on the reef flat (0.3 -> 27 m/s in two steps); not usable as is | - | results p0-p2 |
| Wave-number-dependent current to SWAN (`UV_BANIHASHEMI`) | compiles as `-UV_KIRBY +UV_BANIHASHEMI` (the two are alternatives; our build had both); not yet run | - | VEG_HMIXING entry |
| Canopy-edge viscosity (`VEG_HMIXING`) | does not compile since COAWST v3.6, which dropped its routine (`vegetation_hmixing.F`) but kept everything else; nothing replaces it | - | VEG_HMIXING entry |
| Mixing at rest (the unexplained 1e-3 m²/s on the backreef) | the GLS minimum-TKE floor (`GLS_Kmin` 7.6e-6), not the canopy turbulence: identical with `VEG_TURB` off | lagoon diffusivity 7.4e-4 m²/s, TKE at the floor everywhere | results p0-p2 |
| Lower TKE floor (`GLS_Kmin` 1e-8) | offshore diffusivity 10x lower; the reef-flat temperature range drops | reef-flat SST range -66 % (stratified, 24 h) | results p0-p2 |
| Stability functions (`CANUTO_A` instead of Kantha-Clayson) | small on the flow, noticeable on the temperature | SST range +29 %, flow within 4 % | results p0-p2 |
| Nonlinear equation of state (`NONLIN_EOS`), heated reef, 72 h | no new pressure-gradient error at rest; no effect when heated | < 0.5 % everywhere, reef-flat temperature included | results p0-p2 |
| Heated reef (1000 W/m² peak, balanced over the day) | the reef-flat surface temperature swings 2.6 C a day | - | results p0-p2 |
| Bottom stress: implicit (`BSTRESS_IMPLICIT`) vs explicit | the same on the bare reef; **now the default** | 0-3 % (forereef shear ratio -6 % with triads, -17 % without) | results p0-p2, new-defaults check |
| Bottom-stress cap (`LIMIT_BSTRESS`) | changes the answer and depends on DT; do not use without a DT check | set-up +15 %, crest jet +13 % (bare reef) | results p0-p2, thin crests |
| Round island with passes (Island_A15) | wave-driven island-lagoon circulation: inflow over the windward reef, outflow through every pass, the leeward one most; the windward pass drains too | ~1150 m³/s in over the reef; 2 passes: 590 (windward) and 704 m³/s (leeward) out | island first runs |

## Numerics

| Question | Answer | Size | Entry |
|---|---|---|---|
| Time step DT 6 vs 3 s (bare reef, triads on: a flow that moves) | converged | <= 1.6 % (forereef shear 3.4 %) | triads-on |
| ... on the dense canopy | converged, but only because the canopy damps the flow | ~1e-5 | results p0-p2 |
| NDTFAST 20 or 30 instead of 24 | no effect | ~1e-5 | results p0-p2 |
| AB3-AM4 barotropic kernel (`STEP2D_FB_AB3_AM4`) | as accurate as LF-AM3, faster; **now the default** | within the noise; wall time -18 to -19 % | triads-on |
| SWAN iterations per step (with the fix) | one is enough | 1, 2, 5 iterations within 0.6 % (canopy), 2 % (bare) | triads-on |
| SWAN time step 60 vs 120 s | no effect (tested with triads off) | ~1e-5 | results p0-p2 |
| Directions (`CIRCLE 36` vs 72) | matters | set-up -11 %, crest transport -10 %, breaking dissipation -19 % (triads off) | results p0-p2 |
| Frequencies (34 vs 20) | small | +3 to +5 % (with triads) | triads-on |
| Coupling interval | must be a multiple of both models' time steps: 300 s with SWAN at 120 s was silently ignored (COAWST kept 600 s); 240 s still to test | - | results p0-p2 |
| Tiling (2 x 5 vs 1 x 10) | rounding level | 1e-7 | results p0-p2 |
| `VISC2` 0.001 vs 0 | invisible; 0 is the default | ~1e-5 | results p0-p2 |
| Vertical viscous operator (`SPLINES_VVISC` off) | small; needs to be off for the implicit schemes | crest surface/mean speed +11 % (canopy) | results p0-p2 |
| Vertical diffusive operator (`SPLINES_VDIFF` off) | untestable on a case with T and S fixed (bit-identical); to test on the stratified case | - | results p0-p2 |
| Explicit canopy drag at DT 6 s | fails once triads act, even on the uniform canopy (fore-reef bed, 2 alpha \|U\| DT ~ 6) | 6 of 8 runs blew up | triads-on |
| Implicit canopy drag (`VEG_DRAG_IMPLICIT`) | as accurate as explicit at DT 3 s, stable at DT 6 s; **now the default** | within 2.5 % (patchy canopy); 37 % faster | results p0-p2 |
| `OMEGA_IMPLICIT` (implicit vertical advection) on a crest-jet blow-up | no help: the runaway is horizontal; a shorter DT is what saves the run | blows up 1.9 min sooner | OMEGA_IMPLICIT |
| 10 m grid instead of 20 m (dense canopy, triads off, old defaults) | **not converged at 20 m**: the largest numerical effect found; to be repeated on the density-1 canopy with triads and the new defaults | set-up -15 %, crest transport -18 %, pass transport -10 %, crest jet p99 +15 %, forereef shear ratio +22 %, Hs crest +4 %; 8x the cost | results p0-p2 |

## Problems found in the code along the way

| Problem | Status |
|---|---|
| SWAN never computed `TRIAD` in coupled runs (first-iteration guard with currents) | fixed: coawst-cloud `swan-triads-nonstationary` |
| ROMS never wrote the quicksave file's 3-D `u`, `v` (standard NetCDF writer) | fixed: coawst-cloud `roms-quicksave-uv` (already fixed in upstream ROMS) |
| `VEG_HMIXING`: COAWST v3.6 dropped its routine and kept the rest | explained ([entry](../notebook/2026-11-03_veg-hmixing-and-banihashemi.md)); a port is possible |
| A coupling interval that is not a multiple of both models' steps is silently replaced (300 s ran as 600 s) | noted; check the coupler log (`CplInt` and `Steps`) |
| `UV_BANIHASHEMI` "did not compile" | our configuration: it replaces `UV_KIRBY`, it cannot be added to it |

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

## Running now (submitted 2026-11-03 00:27 UTC)

- **A realistic canopy for the tests** (author's suggestion): density 1 per m²
  everywhere (frontal area 0.2, 20 % of the bed covered, against 0.8 and 79 %
  for the dense canopy), new defaults, triads on: baseline, DT 3 s, no
  triads, gamma 0.80, `BKD`, `TG`, `TKE_WAVEDISS`, explicit canopy drag.
- **The `GLS_Kmin` floor at rest**: stratified case, 7.6e-6 against 1e-8.

## Still open

- The 10 m grid with triads and the new defaults on the density-1 canopy.
- Coupling interval 240 s; `TKE_WAVEDISS`, the roller and the breaking
  formulations on the stratified and heated cases with triads on; a rest run
  with `GLS_Kmin` 1e-8; `SPLINES_VDIFF` on the stratified case.
- Infragravity waves: none of the runs has them; a standalone SWAN `SURFBEAT`
  estimate of their energy on the reef flat is the planned first step.
