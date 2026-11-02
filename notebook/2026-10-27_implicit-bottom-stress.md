# Implicit bottom stress (BSTRESS_IMPLICIT) on A15

- **Date:** 2026-10-27, later sections 2026-10-28
- **Status:** done: the final version matches the converged explicit answer on
  A15. (Only the A15 parts of this work are recorded here; the option was also
  exercised on a realistic reef grid that is not part of this repository.)

## Question / why

Author's question: is the bottom stress implicit too? It is not: ROMS applies
it explicitly (`pre_step3d.F` bottom flux, `rhs3d.F` barotropic forcing). The
optional cap `LIMIT_BSTRESS`, |tau_b| <= 0.75 Hz_1 |u_1| / DT, keeps it stable
but weakens friction where it binds, which on shallow crest jets can be most of
the jet. The author asked for an implicit version, tested on A15 first.

## What was run

- The patch (now coawst-cloud's `roms-bstress-implicit`, option
  `BSTRESS_IMPLICIT`, `SSW_BBL` only), in successive versions below.
- A15 bare (no canopy), 6 h runs on Cloud Batch at DT 6, 3 and 1.5 s; with
  and without the option; images `+VEG_DRAG_IMPLICIT +BSTRESS_IMPLICIT`
  (`sha256:0c8f9767...`), explicit `-SPLINES_VVISC` (`sha256:3d44316e...`),
  `+BSTRESS_IMPLICIT -SPLINES_VVISC` (`sha256:81593d5d...`), final
  `sha256:531a9b96...`.

## Results

**First version** (kbu = |bustr|/|u_1|): on A15 bare it differed from the
explicit (uncapped) run by up to 25-29 cm/s, 6 cm zeta, 45 cm Hs, since
|bustr|/|u_1| is unbounded where u_1 alone is near zero. Fixed:
kbu = Tauc/|U_1| (quadratic drag along the bottom-layer flow). Both implicit
options then ran 6 h at DT 6 s (bare and patchy).

An explicit reference at DT 1 s (NDTFAST 4) failed: surface-layer currents grew
to 4.7 m/s and blew up (probably too few fast steps per slow step for the
barotropic averaging).

**Split version** (backward-Euler drag after the vertical viscosity solve).
A15 bare, 6 h, RMS difference of depth-averaged current (u, v): explicit DT 3 s
vs DT 6 s 5.5 / 4.6 %; explicit DT 3 s vs implicit DT 6 s 25 / 15 %; vs implicit
DT 3 s 18 / 11 %; implicit DT 3 s vs DT 6 s 24 / 17 %. Not trustworthy: it does
not converge towards the explicit solution and depends strongly on DT. Likely
cause: for a stiff drag in one thin bottom layer coupled to the layer above by
viscosity, that operator splitting gives a DT-dependent balance (the canopy
drag, spread over many layers, agreed to 1-2 %).

**Coupled version** (as UCLA ROMS, `IMPLCT_NO_SLIP_BTTM_BC`): dt kbu on the
bottom cell's diagonal of ROMS's tridiagonal vertical-viscosity solve, so
`BSTRESS_IMPLICIT` needs `SPLINES_VVISC` off. A15 bare, 6 h, RMS diff / RMS
speed (u, v): explicit DT 3 vs 6 s 6.8 / 7.7 %; implicit DT 3 vs 6 s 14.3 /
11.1 %; explicit vs implicit at DT 3 s 18.6 / 16.5 %. Pointwise RMS of a 6 h
eddying flow also measures drift, so this was not conclusive; the implicit
run's mean current was about 8 % weaker (4.8 against 5.2 cm/s).

**Convergence resolved: barotropic sign error under the undertow
(2026-10-28).** Integral metrics instead of pointwise RMS (lagoon set-up =
lagoon minus offshore sea level, cm; flow across the crest row j 33):

| run | set-up 1 h | 3 h | 6 h | lagoon current h 3-6 |
|---|---|---|---|---|
| explicit DT 6 / 3 / 1.5 s | 4.56 | 4.13 | 4.04-4.07 | 12.85 cm/s |
| implicit, first barotropic coefficient, DT 6 / 3 s | 4.06 / 3.82 | 3.58 / 3.41 | 3.40 / 3.23 | 12.2 / 12.1 |
| implicit with explicit remainder, DT 6 / 3 s | 4.47 / 4.45 | 4.06 / 4.05 | 3.94 / 3.92 | 12.66 / 12.64 |

- The explicit integrals are converged in DT (6, 3, 1.5 s identical) although
  the explicit drag's stability number on the crest is 1.15 (median) at
  DT 6 s; the large pointwise differences were eddies drifting apart.
- On the crest the schemes were identical (velocity profiles level by level);
  the old implicit run's whole lagoon sat 0.7 cm low.
- Cause: near-bed flow opposes the depth mean at about 7-9 % of faces, along the
  crest's seaward edge (row 35: undertow under the onshore mean). The first
  barotropic coefficient fell back to drag on ubar there, pushing the mean flow
  offshore where the real stress pushes it onshore. Fixed: implicit part
  c2b*ubar only where u_1 and ubar agree, plus the explicit remainder
  bustr - c2b*ubar, so the barotropic mode feels exactly bustr at the start of
  each step.
- The fixed implicit version is converged (DT 6 vs 3 s: 0.02 cm) and within
  about 0.1 cm (2.5 %) of explicit.

## Decision / outcome

The fixed version (drag inside the tridiagonal solve, explicit remainder for
opposing flows) matches the converged explicit answer on A15. It stays a build
option; A15 runs without it (explicit, uncapped stress). Follow-up on thinner
crests: [2026-11-02 entry](2026-11-02_a15-thin-crest-bottom-stress.md).

## Open questions

- A converged reference on a thin crest (done 2026-11-02).

## Details and links

- coawst-cloud's patch document `roms-bstress-implicit`
- [docs/Reef_Ideal_A15_thin_crest.md](../docs/Reef_Ideal_A15_thin_crest.md)
