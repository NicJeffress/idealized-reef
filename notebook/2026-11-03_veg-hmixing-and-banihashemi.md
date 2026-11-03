# Why `VEG_HMIXING` and `UV_BANIHASHEMI` did not compile

- **Date:** 2026-11-03
- **Status:** explained. `UV_BANIHASHEMI`: our misconfiguration, it compiles.
  `VEG_HMIXING`: COAWST dropped its only routine in v3.6; restoring it needs a
  port and fixes (planned as a coawst-cloud patch)

## Question / why

Both options failed to build in the options campaign
([phases 1-2 setup](2026-11-02_options-campaign-phases1-2.md)). The author
asked why, what `vegetation_hmixing.F` did, and whether anything else does it
now.

## `UV_BANIHASHEMI`: two alternatives switched on together

`UV_KIRBY` and `UV_BANIHASHEMI` are alternative definitions of the current
that ROMS sends to SWAN (a depth-weighted current after Kirby and Chen, or a
wavenumber-dependent one after Banihashemi et al.). Both declare the
averaged-output arrays `avguWav`/`avgvWav`, with different shapes, in
`mod_average.F`. The A15 cases define `UV_KIRBY`; adding `+UV_BANIHASHEMI`
switched on both, hence "Component 'avguwav' already declared". Built as
`-UV_KIRBY +UV_BANIHASHEMI` it compiles (2026-11-03). Not a COAWST bug; the
member can be run.

## `VEG_HMIXING`: the routine was dropped in COAWST v3.6

What it did (COAWST v3.4, `ROMS/Nonlinear/Vegetation/vegetation_hmixing.F`,
157 lines; the canopy-edge viscosity of the COAWST vegetation module,
Beudin et al. 2017): an extra horizontal viscosity where the plant density
changes sideways, at the edges of canopy patches,

    visc_veg = VEGHMIXCOEF * Lveg * |grad(plant density)| / (largest density)

per vegetation type and level (`Lveg` the effective blade length), added to
ROMS's horizontal viscosity in `hmixing.F` (3-D) and in the barotropic step
(2-D). The idea: shear layers at canopy edges generate eddies that a
hydrostatic model with coarse cells does not resolve.

History: the file is in the v3.4 tag and in the 2019 commit before v3.6; it
is gone in the "Update to COAWST v3.6" commit (2020-05-18), while v3.6's
`hmixing.F` still calls `vegetation_hmixing_cal`. The public repository brings
in each version as one bulk commit, and neither the commit messages nor the
v3.9 user manual mention the option, so there is no stated reason. Everything
else is still in v3.9: the `VEG_HMIXING` switch (it turns on `VISC_3DCOEF` in
`globaldefs.h`), the `VEGHMIXCOEF` input in `vegetation.in` and its reader,
the arrays `visc2d_r_veg`/`visc3d_r_veg` (allocated), and the two calls. Only
the routine that fills the arrays is missing, so the option has not compiled
since v3.6.

Nothing else does it: ROMS's horizontal viscosity (`VISC2`, now 0) is
uniform, the third-order upstream advection adds numerical diffusion where
gradients are sharp but not in proportion to canopy edges, and `VEG_TURB`
acts only on the vertical turbulence (k and epsilon in each column).

Porting the v3.4 routine needs more than a copy: it uses v3.4 names (`pdens`
for the density index, module `mod_vegetation`); its "largest density
gradient" loop takes the largest density instead (and not over the whole
domain); and it divides by that value, so a bare reef (density 0
everywhere) divides by zero.

## Decision / outcome

Banihashemi: can be tested as `-UV_KIRBY +UV_BANIHASHEMI`. Canopy-edge
viscosity: a coawst-cloud patch restoring the routine with those fixes and a
before/after test on the patchy canopy, if the author wants the option.
