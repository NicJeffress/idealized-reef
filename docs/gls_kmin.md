# The GLS minimum TKE (`GLS_Kmin`): what it does and what value to use

A reference note for the A15 cases (and any ROMS/COAWST run with the GLS
k-epsilon closure). Last updated 2026-11-03 (72 h heated runs added; 1e-8 adopted as the A15 default).

## In short

`GLS_Kmin` is the floor ROMS puts under the turbulent kinetic energy (TKE) of
its GLS closure. Wherever the flow produces no turbulence (calm, or strongly
stratified water), the TKE sits at that floor, and the floor alone sets the
vertical mixing: about **0.05 Kmin / N** for diffusivity and viscosity in
stratified water (N the buoyancy frequency), and more where the water is
barely stratified. ROMS's suggested k-epsilon value, **7.6e-6 m²/s²**, gives
mixing of 1e-5 to 1e-3 m²/s in quiet water, far above the background value
(`AKT_BAK`, 5e-6) and enough to erase stratification within hours in a 2 m
lagoon. Lower floors (1e-8 to 1e-10) are common elsewhere and restore the
background mixing. **The value is a modelling choice that decides how much a
calm lagoon can stratify; state it in any methods section.**

## How the floor sets the mixing

In k-epsilon the eddy diffusivity is AKt = c_mu' k² / epsilon. In stratified
water ROMS limits the turbulent length scale to the Ozmidov scale (the
Galperin limit), which bounds the dissipation from below at about
0.228 k N. With k at the floor, the diffusivity then tends to

    AKt ~ AKv ~ 0.05 Kmin / N

(M. Scully's derivation on the ROMS forum, 2011). So the minimum mixing is set
by `GLS_Kmin`, not `AKT_BAK`/`AKV_BAK` (which is why changing `AKT_BAK` "has no
effect"), and it varies with the stratification: weaker stratification, more
mixing. In nearly unstratified water the length-scale limit hardly acts and
the same floor gives much larger values.

## And `AKT_BAK`?

In the GLS closure the background coefficients are added to the turbulent
part (`gls_corstep.F`):

    Akv = Akv_bak + Sm*ql
    Akt = Akt_bak + Sh*ql

and they are kept out of the TKE budget (shear and buoyancy production use
`Akv - Akv_bak` and `Akt - Akt_bak`); at the surface boundary
`Akt = Akt_bak`. So the background is always present; whether it matters
depends on the turbulent part next to it. With the floor at 7.6e-6 the
turbulent part in quiet water is 1e-5 to 1e-3 m²/s and `AKT_BAK` (5e-6 in the
A15 cases) is a percent of the total: changing it "has no effect". With the
floor at 1e-8 or below, the turbulent part in quiet water drops to about
1e-7 m²/s and **`AKT_BAK` and `AKV_BAK` become the background mixing** (the rest
run measured 5.1e-6 m²/s, i.e. `AKT_BAK`). Lowering the floor therefore hands
the quiet-water mixing to two explicit parameters, which then need choosing:

| Parameter | A15 value | Notes |
|---|---|---|
| `AKT_BAK` | 5e-6 m²/s (T and S) | ROMS's usual default 1e-6; molecular heat diffusion 1.4e-7, salt 1e-9; the excess stands for unresolved mixing (internal waves) |
| `AKV_BAK` | 5e-5 m²/s | 10x `AKT_BAK`; sets the vertical friction of a calm lagoon at slack water once the floor is low |
| `AKK_BAK`, `AKP_BAK` | 5e-6 m²/s | background diffusion of TKE and of the length-scale variable; smooth the closure's own fields only |

## What the A15 tests measured

24 h at rest (no tide, no waves), stratified case (N² 1e-4 initially), the
defaults of 2026-11-02 ([notebook](../notebook/2026-11-03_gls-kmin-at-rest.md)):

| Zone | AKt, Kmin 7.6e-6 | AKt, Kmin 1e-8 | top-bottom temperature, 7.6e-6 / 1e-8 |
|---|---|---|---|
| lagoon and backreef (0.5-3 m) | 7.4e-4 m²/s | 5.1e-6 m²/s | 0.000 / 0.034 C |
| fore reef (3-20 m) | 5.1e-5 m²/s | 5.1e-6 m²/s | 0.29 / 0.49 C |
| offshore (> 20 m) | 4.7e-5 m²/s | 5.1e-6 m²/s | 8.31 / 8.37 C |

The offshore value checks the formula: N about 8e-3 s^-1 gives
0.05 x 7.6e-6 / 8e-3 = 4.8e-5 m²/s (measured 4.7e-5). With the lower floor the
diffusivity falls to the background value everywhere and the calm lagoon keeps
part of its stratification. With waves and tide (24 h, forced), 1e-8 ran
stably, cut the offshore diffusivity tenfold and the reef-flat daily
temperature range by 66 % (the forced shallow mixing itself is unchanged,
about 1.3e-3 m²/s, because the flow produces that turbulence). This floor is
the "unexplained 1e-3 m²/s backreef diffusivity at rest" of earlier tests: it
is identical with the canopy turbulence (`VEG_TURB`) switched off.

### Heated, forced, 72 h

Heated case (shortwave peak 1000 W/m², tide, waves, canopy), 72 h, third day
([notebook](../notebook/2026-11-03_kmin-heated-72h.md)):

| Zone | AKt, 7.6e-6 / 1e-8 / 1e-10 | top-bottom temperature, mean | surface daily range |
|---|---|---|---|
| lagoon and backreef | 5.3e-3 / 5.4e-3 / 5.4e-3 m²/s | 0.110 / 0.114 / 0.114 C | 1.92 / 1.94 / 1.93 C |
| fore reef | 9.0e-4 / 9.4e-4 / 9.5e-4 m²/s | 0.391 / 0.410 / 0.409 C | 1.05 / 1.11 / 1.11 C |
| offshore | 4.7e-5 / 5.1e-6 / 5.0e-6 m²/s | 4.81 C, all three | 0.47 C, all three |

All three ran stably. Where the flow makes turbulence (the whole reef here),
the floor changes the temperatures by a few percent at most; offshore below
the mixed layer it sets the diffusivity tenfold higher, which a 72 h run cannot
see (crossing a 20 m thermocline at 5e-5 m²/s takes about 90 days) but a run
of weeks would. 1e-8 and 1e-10 agree to three digits. With the floor at 1e-8,
`AKT_BAK` 1e-6 instead of 5e-6 sets the offshore diffusivity to 1.1e-6 m²/s and
adds 3 % to the reef's stratification; `AKV_BAK` 5e-6 instead of 5e-5 raises
the fore-reef diffusivity 16 % and moves the temperatures 1-4 %. (An earlier
"-66 % reef-flat temperature range" with 1e-8 was on the unheated stratified
case, where that range is only 0.045 C.)

## What the ROMS forum and the literature say

- **Where 7.6e-6 comes from:** the coefficient table of Warner et al. (2005,
  Ocean Modelling 8, 81-113), matched to GOTM's settings at the time. J.
  Warner (2011): "i provided sets of coefficients that seemed to represent
  values in the literature at that time"; "If you determine a set of
  coefficients that seem more applicable for your particular application,
  then please share them out." The suggestion block of `ocean.in` lists
  `GLS_Kmin` 5e-6 (k-kl), 7.6e-6 (k-epsilon, k-omega) and 1e-8 (gen).
- **M. Scully (2011)**, thread "Changing AKT_BAK values has no effect on model
  results": derived the 0.05 Kmin/N limit; ran ROMS with 1e-10 "fine", reaching
  the specified background viscosity; noted that the floor differs between
  closures (k-kl lower), so closures can look different only because their
  effective background mixing differs, which matters for fluxes across a
  pycnocline. H. Arango quoted Umlauf and Burchard's original GLS as using
  1e-9.
- **J. Pringle (2018)**, thread "excess mixing in k-epsilon GLS mixing; bug or
  misconfigured?": a stratified channel at rest lost its stratification in
  ROMS k-epsilon within 30-45 days, kept it with LMD, MY25, GOTM, and ROMS
  with 1e-10. GOTM's default has since dropped from 7.6e-6 to 1e-10. "What is
  the 'right' value of GLS_Kmin? ... it will be determined by unresolved
  sources of TKE so is application dependent" (e.g. internal-wave breaking);
  he chose 1e-10 and asked for a smaller default. Mixed-layer deepening under
  wind is insensitive to the floor, because turbulence is produced there.
- **B. Perfect (2018)**, same thread: the floor gave "extremely large
  background dissipation values" in a topographic-wake study; worried that
  very small TKE could cause numerical problems where 1/k is needed.
- **R. Harcourt (2023)**, thread "Possible Coding Error in gls_corstep.F":
  "the default suggested gls_Kmin=7.6e-6 setting ... should be either lowered
  or marked clearly ... Like for N~1e-3/s you get AKt, AKs, Akv ~ 1e-3 m^2/s".

No thread reports a run that failed at a low floor; the concern raised is
numerical (divisions by k).

## Related code issues, and COAWST v3.9's status

| Issue | Upstream ROMS (myroms, main) | COAWST v3.9 |
|---|---|---|
| Smoothed limiter on the buoyancy parameter Gh put a notch in the mixing just below its critical value (Harcourt 2018, "Equation error in GLS model coded into gls_corstep.F") | original formula | **corrected** (`MAX(0, Gh-Ghcri)`) |
| Floors applied to layer-thickness-weighted TKE during advection (Harcourt 2023) | still applied there | **applied only after the vertical solve**, to TKE itself |
| Equation (33) of Warner et al. (2005) | a misprint in the paper; the code was right (Warner, 2025) | same |

## Recommendation for the A15 cases

- **`GLS_Kmin` 1e-8** in every A15 case (adopted 2026-11-03, the author's
  decision): stable in 72 h heated runs, the same answer as 1e-10, and the
  value ROMS's input file suggests for the generic closure. The default
  7.6e-6 adds a hidden 1e-5 to 1e-3 m²/s wherever the water is quiet.
- With the floor that low, **`AKT_BAK` (5e-6) and `AKV_BAK` (5e-5) are the
  quiet-water mixing**: choose them deliberately and report them with the
  floor.
- On a forced reef the choice matters little (a few percent); it matters
  in a calm lagoon at slack water and offshore below the mixed layer, and
  more the longer the run.
- Whatever the choice, keep it the same across an ensemble and report it.

## Sources

- [Changing AKT_BAK values has no effect on model results](https://m.myroms.org/forum/viewtopic.php?p=8458) (ROMS forum, 2011)
- [excess mixing in k-epsilon GLS mixing; bug or misconfigured?](https://myroms.org/forum/viewtopic.php?p=18566) (ROMS forum, 2018)
- [Possible Coding Error in gls_corstep.F](https://m.myroms.org/forum/viewtopic.php?p=24570) (ROMS forum, 2023)
- Equation error in GLS model coded into gls_corstep.F (ROMS forum, 2018)
- [GLS coefficient table as quoted on the forum](https://m.myroms.org/forum/viewtopic.php?p=6604)
- Warner, J. C., C. R. Sherwood, H. G. Arango and R. P. Signell (2005),
  Performance of four turbulence closure models implemented using a generic
  length scale method, Ocean Modelling 8, 81-113.
