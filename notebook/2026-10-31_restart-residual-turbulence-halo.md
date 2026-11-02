# Restart residual traced: tke/gls ghost columns empty after a restart

- **Date:** 2026-10-31
- **Status:** done in coawst-cloud (`b03ddd0`, `roms-restart-wec`: `turbulence_halo`)

## Question / why

The base A15 case restarted (30 + 30 min vs 60 min straight) to 1.8e-7 m/s,
not round-off, while the canopy variant reached 1.2e-10. Author: "Trace the
residual first", before the improvements tier.

## What was done

- Debug build (A15, fixes + the two borrowed SWAN improvements + a print patch
  in `gls_prestep_tile`): tke/gls at both time levels, W, W_stokes, Huon, Hvom,
  Hz on row j = 33 at the seam columns, at 600 and 606 s after the restart
  and at the same times straight. One Batch run (1 ROMS tile).
- At the first step everything was identical except the outer periodic ghost
  columns i = -2, -1, 203, 204 (Lm = 201) of tke and gls: GLS_Kmin 7.6e-6 and
  GLS_Pmin 1e-12 instead of about 1.6e-4 / 8e-5. One step later columns
  -1 ... 1 and 200 ... 202 differed at relative 2e-7.
- Cause: `ini_fields.F` refills the halos of every field a perfect restart
  restores (u, v, t, ubar, vbar, ru, rv, rubar, ...) except tke and gls; the
  restart file holds i = 0 ... 202 only. The first step's horizontal advection
  of tke/gls reads two columns out.
- Fix: new change `turbulence_halo` in roms-restart-wec.patch: at the end of
  `ini_fields`, under PERFECT_RESTART with GLS_MIXING or MY25_MIXING,
  exchange_w3d_tile on tke and gls (3 levels) for periodic domains and
  mp_exchange4d for tiles. Not wave-specific: any periodic GLS/MY25 restart.
- coawst-cloud's restart test updated (its variants: `veg` = Reef_Ideal_A15_veg,
  `river` = Reef_Ideal_A15 with a test river, `noriver` = bare A15): every
  variant must reach < 1e-8 m/s.

## Results

60 min straight vs 30 + 30, compared at 60 min, ROMS 1x6 + 2 SWAN, Batch:

| Variant | before patch | after (with turbulence_halo) |
|---|---|---|
| veg | 2.7e-5 m/s | 1.2e-10 m/s, SWAN bit-identical |
| river | 2.1e-2 m/s | 1.9e-9 m/s, Hs last bit |
| noriver | 2.1e-2 m/s | 5.8e-11 m/s (was 1.8e-7), SWAN bit-identical |

- Remaining differences are last-bit flips of the float32 history (river:
  u -0.0301691350 vs -0.0301691368 at one point, float32 step 1.86e-9).
- Correction: the bare case is 2.1e-2 m/s off before the patch with or without
  the river, so the 2 cm/s comes from the missing wave state, amplified by the
  bare crest flow, not from the river. The document said otherwise; fixed.
- Cost: 7 Batch c2d-standard-8 Spot VMs, about 10-12 min each: about $0.20
  (estimate).

## Problems on the way

- Scratch COAWST copy was partial (no ROMS/Modules); regenerated the patch from
  the pinned tarball (pre-patch tree vs patched tree, `diff -ruN`).
- Applying all 2-improvements alphabetically fails (swan-closed-ring needs
  swan-periodic-curvilinear first); the A15 series order applies cleanly.

## Decisions / next

- `turbulence_halo` is part of coawst-cloud's `roms-restart-wec`. The error
  shows with the periodic direction in one tile (A15 1x6); runs split over
  several tiles in x seem to get the periodic halo filled by the parallel read.
  Images built before the change lack it; rebuild before relying on exact
  restarts with another tiling.
