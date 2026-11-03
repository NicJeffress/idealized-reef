# Reef_Ideal_A15_bulk: A15 with bulk Stokes drift

Folder: [`cases/Reef_Ideal_A15_bulk`](../cases/Reef_Ideal_A15_bulk).
Application flag `REEF_IDEAL_A15`. Identical to
[Reef_Ideal_A15](Reef_Ideal_A15.md) except one line in the header:

```c
#define BULK_STOKES   /* Stokes drift from Hwave, Lwave, Dwave (as in v3.7), not the SWAN spectrum */
```

## Why it exists

COAWST v3.7, which the original A15 runs used, computed the Stokes drift from
bulk wave parameters (height, wavelength, direction: a monochromatic profile).
COAWST v3.9 by default sums it over SWAN's frequency bins (spectral Stokes
drift), which gives a more realistic vertical profile but costs more. This
variant compares the two, in cost and in Stokes profiles.

## Known results

([notebook](../notebook/2026-10-21_spectral-stokes-fixes-speedup.md))

- 1 h, 6 ROMS + 2 SWAN on 8 vCPUs: ROMS's WEC kernel took 386 CPU-s with
  spectral Stokes drift and 26 CPU-s with bulk; wall time 149 s in both,
  because at that split ROMS and SWAN are balanced and with bulk ROMS just waits
  for SWAN.
- coawst-cloud's `roms-wec-stokes-fast` cuts the spectral cost to 217 CPU-s
  (same physics, about 3x fewer SINH/COSH/EXP calls), and
  `roms-wec-stokes-fixes` corrects index errors in the spectral code.
- The author chose the spectral Stokes drift for the A15 family; this case stays
  as the comparison.

## Caveats

- **SWAN is not periodic in this folder.** Its `swan.in` keeps A15's original
  (v3.7) wave boundaries: waves enter on the north edge and on the offshore
  half of the east and west edges (rows 72-125 of the breaking-zone grid),
  without `REPEATING`. With non-periodic SWAN, A15's periodic ROMS seam gets
  mismatched wave forcing (a 58 mm/s jump in the alongshore current in a 3 h
  test). For a like-for-like comparison with A15, copy
  `cases/Reef_Ideal_A15/swan.in` into this folder.
- Otherwise the case follows every A15 default of 2026-11-03 (breaking-zone
  grid, 15 levels, roller, bottom streaming, `TKE_WAVEDISS`, `BKD` breaking,
  34 frequencies, `GLS_Kmin` 1e-8); none of the campaign's tests was run
  with the bulk Stokes drift.
- No comparison of the Stokes profiles themselves is recorded yet.
