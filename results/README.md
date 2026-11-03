# Results: what the options campaign has shown so far

A running summary of what the options test campaign (November 2026) has
taught us about the physics and the numerics of the idealized reef cases,
kept up to date as runs finish. The numbers come from the notebook entries
linked in each section, where the full tables, figures and run details are.
Percentages are differences between 24 h runs, over hours 12-24 (the second
tidal cycle), unless stated.

**Last updated:** 2026-11-03 04:40 UTC.

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
| Triads (`TRIAD`) | first-order; must be on, with the SWAN fix | without them: set-up -82 % (dense canopy), -61 % (density-1 canopy), -32 % (bare) | triads-on, density-1 |
| Wave breaking formulation, with triads | CON 0.73 and CON 0.80 agree within 1 % on the realistic canopy; `BKD` gives 7-11 % more set-up, crest transport and crest jet; `TG` (Thornton-Guza) leaves the flow within 3 % but changes the fore-reef shear, crest Hs and flushing | density-1 canopy: BKD set-up +8 %, crest jet +11 %; TG forereef shear +62 %, Hs crest -18 %, flushing +33 % (dense canopy: similar spread) | density-1, triads-on |
| ... without triads (for the record) | the spread looked huge | set-up -24 % to +108 %: an artefact of the missing triads | results p0-p2 |
| Turbulence from breaking (`TKE_WAVEDISS + ZOS_HSIG`) | **with triads it behaves as expected**: less surface-intensified fore-reef flow and a slower crest jet; **adopted 2026-11-03** (author). (With triads off it had increased the fore-reef shear: an artefact of the missing triads) | density-1 canopy: forereef surface/mean speed -32 %, crest jet -17 %, set-up -9 %, crest transport -5 % | density-1 |
| Whitecapping on opposing currents (`WCAP AB ... CURRENT`) | no effect on A15 | < 1 % | results p0-p2 |
| Wave roller (`ROLLER_RENIERS`) | blew up at DT 6 s: COAWST advects the roller with one explicit step per DT (Courant 1.1-1.6 on the crest); **fixed** with sub-steps (coawst-cloud `roms-roller-substeps`): DT 6 s now equals DT 3 s within 0.1 %. A sizeable term: more set-up and transport | `WEC_ALPHA` 0.5: set-up +25 %, crest transport +16 %, jets +10 %, forereef surface/mean +32 % (density-1 canopy) | roller entry |
| Wave-number-dependent current to SWAN (`UV_BANIHASHEMI`) | compiles as `-UV_KIRBY +UV_BANIHASHEMI` (the two are alternatives; our build had both); not yet run | - | VEG_HMIXING entry |
| Canopy-edge viscosity (`VEG_HMIXING`) | does not compile since COAWST v3.6, which dropped its routine (`vegetation_hmixing.F`) but kept everything else; nothing replaces it | - | VEG_HMIXING entry |
| Mixing at rest (the unexplained 1e-3 m²/s on the backreef) | **the GLS minimum-TKE floor** (`GLS_Kmin` 7.6e-6), not the canopy turbulence (identical with `VEG_TURB` off); `GLS_Kmin` 1e-8 removes it | lagoon diffusivity at rest 7.4e-4 -> 5.1e-6 m²/s (150x); the calm lagoon keeps its stratification | results p0-p2, Kmin at rest |
| Lower TKE floor (`GLS_Kmin` 1e-8; see [docs/gls_kmin.md](../docs/gls_kmin.md)) | diffusivity falls to ROMS's background everywhere at rest; proposed for stratified and heated runs after a 72 h heated check | reef-flat SST range -66 % (stratified, forced, 24 h) | results p0-p2, Kmin at rest |
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
| Directions (36 / 72 / 144) | **converged at 72 with the 30-degree spread** (within 1 % of 144; 36 within 3 %). With the old 4-degree swell they converged slowly (the bins did not resolve the spread) | 30 deg: 36 -3 %, 144 +1 % (set-up); 4 deg: 36 -16 %, 144 +5 % | spread-30, spectral resolution |
| Frequencies (20 / 34 / 48) | converged by 34; 20 is about 3 % low; **34 adopted 2026-11-03** | 34 vs 20: set-up +3 %, crest transport +1.5 %; 48 = 34 within 0.4 % | spectral resolution |
| Coupling interval | must be a multiple of both models' time steps: 300 s with SWAN at 120 s was silently ignored (COAWST kept 600 s); 240 s still to test | - | results p0-p2 |
| Tiling (2 x 5 vs 1 x 10) | rounding level | 1e-7 | results p0-p2 |
| `VISC2` 0.001 vs 0 | invisible; 0 is the default | ~1e-5 | results p0-p2 |
| Vertical viscous operator (`SPLINES_VVISC` off) | small; needs to be off for the implicit schemes | crest surface/mean speed +11 % (canopy) | results p0-p2 |
| Vertical diffusive operator (`SPLINES_VDIFF` off) | untestable on a case with T and S fixed (bit-identical); to test on the stratified case | - | results p0-p2 |
| Explicit canopy drag at DT 6 s | fails once triads act on the dense canopy (fore-reef bed, 2 alpha \|U\| DT ~ 6); fine on the density-1 canopy (within 3 % of implicit) | dense: 6 of 8 runs blew up | triads-on, density-1 |
| Implicit canopy drag (`VEG_DRAG_IMPLICIT`) | as accurate as explicit at DT 3 s, stable at DT 6 s; **now the default** | within 2.5 % (patchy canopy); 37 % faster | results p0-p2 |
| `OMEGA_IMPLICIT` (implicit vertical advection) on a crest-jet blow-up | no help: the runaway is horizontal; a shorter DT is what saves the run | blows up 1.9 min sooner | OMEGA_IMPLICIT |
| 10 m grid instead of 20 m | **not converged at 20 m**, the same in two regimes: the breaking zone (1010-1060 m from shore, 2-3 cells at 20 m) is under-resolved; dissipation is the same, the momentum transfer is not. Proposed: refine across the shore over that zone only (~+20 % cost instead of 8x) | set-up -16 % (both regimes), crest transport -11 % (density 1, triads) / -18 % (dense, no triads), dissipation +0.2 % | grid-10m |

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

## Problems found in the code along the way

| Problem | Status |
|---|---|
| SWAN never computed `TRIAD` in coupled runs (first-iteration guard with currents) | fixed: coawst-cloud `swan-triads-nonstationary` |
| The Reniers roller took one explicit step per DT (`numits=1`; 30 commented out): unstable at DT 6 s on a reef crest | fixed: coawst-cloud `roms-roller-substeps` |
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

## Still open

- A grid refined across the shore over the breaking zone only (proposed).
- Coupling interval 240 s; `TKE_WAVEDISS`, the roller and the breaking
  formulations on the stratified and heated cases with triads on; a 72 h
  heated run with `GLS_Kmin` 1e-8; `SPLINES_VDIFF` on the stratified case.
- Infragravity waves: none of the runs has them; a standalone SWAN `SURFBEAT`
  estimate of their energy on the reef flat is the planned first step.
