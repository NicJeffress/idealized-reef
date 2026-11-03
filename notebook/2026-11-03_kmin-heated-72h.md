# GLS_Kmin and background mixing in the heated case, 72 h

- **Date:** 2026-11-03
- **Status:** done; `GLS_Kmin` 1e-8 adopted as the A15 default (the author, 2026-11-03)
- **Builds:** coawst-cloud `61f8cea`, Reef_Ideal_A15_veg_therm with the defaults
  of 2026-11-03 (30-degree spread, 34 frequencies, `TKE_WAVEDISS`, triads)

## Question / why

At rest, the GLS minimum TKE (`GLS_Kmin`) sets the lagoon's mixing: the
suggested k-epsilon value 7.6e-6 m²/s² gives 7.4e-4 m²/s there, 1e-8 gives the
background value ([at rest](2026-11-03_gls-kmin-at-rest.md),
[docs/gls_kmin.md](../docs/gls_kmin.md)). Two things were left: whether a low
floor runs stably for days with heating, waves and tide (forum users worried
about divisions by a tiny TKE), and how much it changes a heated reef, where
the flow makes its own turbulence. And once the floor is low, the background
coefficients `AKT_BAK` and `AKV_BAK` take over the quiet-water mixing, so
their sensitivity was checked in the same setting.

## What was run

Heated case (shortwave peak 1000 W/m², tide 0.15 m, waves, the case's dense canopy, density 4 m⁻²),
72 h in 4 h restart segments on Spot VMs, five members:

| Member | `GLS_Kmin` | `AKT_BAK` | `AKV_BAK` |
|---|---|---|---|
| k76 | 7.6e-6 (the current default) | 5e-6 | 5e-5 |
| k8 | 1e-8 | 5e-6 | 5e-5 |
| k10 | 1e-10 | 5e-6 | 5e-5 |
| akt1 | 1e-8 | **1e-6** | 5e-5 |
| akv5 | 1e-8 | 5e-6 | **5e-6** |

Statistics from the hourly history: depth zones lagoon and back reef
(0.5-3 m), fore reef (3-20 m), offshore (deeper than 20 m); the third day
unless noted. Script `reduce.py` (zone means and medians of every record);
table in the CSV next to this entry.

## Results

**All five ran 72 h without trouble**, including 1e-10.

| Day 3 | k76 | k8 | k10 | akt1 | akv5 |
|---|---|---|---|---|---|
| lagoon AKt (median) | 5.3e-3 m²/s | 5.4e-3 | 5.4e-3 | 5.4e-3 | 5.4e-3 |
| lagoon top-bottom T, mean / max | 0.110 / 1.24 C | 0.114 / 1.33 | 0.114 / 1.34 | 0.118 / 1.38 | 0.114 / 1.31 |
| lagoon surface T daily range | 1.92 C | 1.94 | 1.93 | 1.94 | 1.91 |
| fore reef AKt (median) | 9.0e-4 | 9.4e-4 | 9.5e-4 | 9.3e-4 | 1.1e-3 |
| fore reef top-bottom T, mean | 0.391 C | 0.410 | 0.409 | 0.423 | 0.394 |
| fore reef surface T daily range | 1.05 C | 1.11 | 1.11 | 1.14 | 1.07 |
| offshore AKt (median) | **4.7e-5** | **5.1e-6** | **5.0e-6** | **1.1e-6** | 5.1e-6 |
| offshore top-bottom T, mean | 4.81 C | 4.81 | 4.81 | 4.81 | 4.81 |
| warmest water anywhere | 29.57 C | 29.58 | 29.60 | 29.58 | 29.51 |

- **On the reef, the floor hardly matters when the reef is forced and
  heated.** The lagoon's mixing (5e-3 m²/s) is made by the waves, the tide
  and the canopy, 1000 times the floor's contribution, and its daily
  temperature cycle (1.9 C) is the same within 1 %. A lower floor lets the
  water stratify a little more at the warmest hour (top-bottom maximum
  +7 % in the lagoon, mean +5 % on the fore reef).
- **Offshore, below the mixed layer, the floor is the mixing**: 4.7e-5 m²/s
  with 7.6e-6, against 5e-6 (exactly `AKT_BAK`) with 1e-8 or 1e-10, as at rest
  and as the 0.05 Kmin/N rule predicts. In 72 h this changes nothing visible:
  diffusing across a 20 m thermocline at 5e-5 m²/s takes
  (20 m)²/5e-5 m²/s, about 90 days. It matters for runs of weeks or more.
- **1e-8 and 1e-10 agree to three digits** everywhere: below 1e-8 the floor's
  share is negligible and `AKT_BAK` is the mixing.
- **`AKT_BAK` 1e-6 instead of 5e-6** sets the offshore diffusivity to 1.1e-6
  (the floor contributes nearly nothing) and adds 3 % to the stratification
  on the reef. **`AKV_BAK` 5e-6 instead of 5e-5** raises the fore-reef
  diffusivity 16 % (less background friction, more shear, more turbulence)
  and changes the temperatures by 1-4 %.
- An earlier 24 h result, "`GLS_Kmin` 1e-8 cuts the reef-flat temperature
  range by 66 %" ([results p0-p2](2026-11-02_options-campaign-results-p0-p2.md)),
  was on the stratified case without heating, where that range is only
  0.045 C: 66 % of almost nothing. With heating the range is 1.9 C and the
  floor moves it by less than 1 %.

## What it means

- A low floor is safe: 72 h of waves, tide and strong heating at 1e-8 and
  1e-10 ran as smoothly as the default.
- On the reef the choice is not important while the reef is forced; it
  decides the mixing only where the water is quiet: offshore below the mixed
  layer, and a calm lagoon at slack water ([at rest](2026-11-03_gls-kmin-at-rest.md)).
  With a floor of 1e-8 or less, that quiet-water mixing is `AKT_BAK`, an
  explicit and reportable number, instead of a hidden side effect of the
  floor (0.05 Kmin/N, varying with the stratification).

## Decision / outcome

Recommendation: **`GLS_Kmin` 1e-8 in every A15 case** (1e-10 gives the same
answer; 1e-8 is the value ROMS's own input file suggests for the generic
closure and keeps the TKE further from zero), keeping `AKT_BAK` 5e-6 and
`AKV_BAK` 5e-5, which now set the quiet-water mixing and should be reported
with it. **Adopted by the author on 2026-11-03** (1e-8 rather than 1e-10).

## Details and links

- [docs/gls_kmin.md](../docs/gls_kmin.md) (updated with these runs),
  [results summary](../results/README.md)
- Cost: 5 runs of about 2.2 h on c2d-standard-16 Spot, about $2.5.
