# Spectral Stokes drift: keep it, fix it, make it 3x cheaper

- **Date:** 2026-10-21
- **Status:** done, default patches

## Question / why

The A15 port showed ROMS spending 46 % of its time in the WEC kernel,
mostly the spectral Stokes drift (`SPECTRUM_STOKES`, v3.9's default with
SWAN; v3.7, which the author's old runs used, had only bulk Stokes drift).
Keep spectral or go back to bulk? And can it be made cheaper?

## What was run

- `cases/Reef_Ideal_A15_bulk`: A15 with `BULK_STOKES` (as v3.7), to
  compare cost.
- 1 h runs, 6 ROMS (1x6) + 2 SWAN on the control VM (8 vCPUs), spectral
  versus bulk, then with the patches.
- Code reading of `wec_stokes.F` against its own comments, the v loop and
  the git history (introduced in COAWST commit `c6c108b`, February 2023;
  no GitHub issue found).

## Results

- ROMS WEC kernel: 386 CPU-s spectral, 26 CPU-s bulk; wall time 149 s in
  both, because at this split ROMS and SWAN are balanced and with bulk
  ROMS just waits for SWAN.
- Fixes (`roms-wec-stokes-fixes.patch`): the u-point high-frequency tail
  averaged the wavenumber over the v-point neighbours (effect on A15 after
  1 h: up to 1.6e-6 m/s, max u_stokes 0.06 m/s); the u loop summed bins up
  to kD 200 instead of 36 (bins beyond add about e^-36); an unused SINH
  per bin.
- Speed-up (`roms-wec-stokes-fast.patch`, same physics, about 3x fewer
  SINH/COSH/EXP calls): WEC kernel 386 -> 217 CPU-s; largest relative
  difference 5e-7 after 1 h (float32 output resolution).

## Decision / outcome

> **Decided (author, 2026-10-21): keep the spectral Stokes drift** (v3.9
> default `SPECTRUM_STOKES`, summed over the 21 SWAN frequency bins) for a
> realistic vertical profile, rather than `BULK_STOKES`.

> **Decided (author, 2026-10-21): fix the spectral Stokes bugs and use the
> speed-up by default.**

## Open questions

- Speed-ups only show in wall time with a process split that gives SWAN
  more processes (ROMS was the bottleneck; SWAN then is).
- Recomputing Stokes drift only after each exchange: open (changes
  results slightly).
- `Reef_Ideal_A15_bulk` is still non-periodic and needs a rebuild with the
  newer patches.
- Report upstream (GitHub issue): open.

## Details and links

- coawst-cloud's patch documents, Stokes patches
- [docs, Performance notes](../docs/Reef_Ideal_A15.md); [`docs/Reef_Ideal_A15_bulk.md`](../docs/Reef_Ideal_A15_bulk.md)
