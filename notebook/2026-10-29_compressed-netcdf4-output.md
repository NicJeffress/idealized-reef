# Compressed NetCDF-4 output from ROMS (OUT_NETCDF4 + DEFLATE)

- **Date:** 2026-10-29
- **Status:** tested; made the default by the author (2026-10-29)

## Question / why

Author: "can you test if we can start outputting in compressed netcdf4? does
that have any runtime or analysis speed costs?" (data transfer between cloud
regions was about 8 % of the bill).

## What was run

- ROMS writes NetCDF-4/HDF5 when built with `OUT_NETCDF4` and compresses each
  variable with `DEFLATE` (shuffle on, deflate level 1, the fastest; chunks of
  one record). The build already links NetCDF-4/HDF5, so it is a build option:
  `CPP_OPTIONS="... +OUT_NETCDF4 +DEFLATE"`. Output is still written serially
  by ROMS's rank 0.
- A15 vegetation, 30 min on the control VM (2 ROMS + 2 SWAN), history,
  averages and diagnostics every 2 min (a deliberately heavy output load).
- (A larger realistic case was tested the same way; not recorded here.)

## Results

| | classic | compressed | ratio |
|---|---|---|---|
| A15 history / averages / diagnostics | 335 / 294 / 514 MB | 117 / 118 / 257 MB | 2.9 / 2.5 / 2.0x smaller |
| values | | | identical in every variable (473) |
| ROMS time writing output, A15 (2-min output) | 2-3 % | 11 % | |

- At usual output settings (history hourly) the extra writing time is about
  1 % of a run.
- Smaller files cut bucket storage, inter-region transfer and download time by
  about the same factor.
- Readers: Python netCDF4/xarray, MATLAB's netCDF functions, ncdump and
  NetCDF-Fortran programs all read NetCDF-4.

## Decision / outcome

> **ROMS output is compressed NetCDF-4 by default** (author, 2026-10-29:
> "Yes, default"): `OUTPUT_OPTIONS="+OUT_NETCDF4 +DEFLATE"`, lossless;
> `OUTPUT_OPTIONS=""` for classic files.

SWAN's NetCDF output followed the same day:
[SWAN compression](2026-10-29_swan-compressed-netcdf4-output.md).

## Details and links

- coawst-cloud's build documentation (output format)
