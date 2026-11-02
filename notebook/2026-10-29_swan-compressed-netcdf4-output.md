# Compressed NetCDF-4 output for SWAN (swan-netcdf4-compression)

- **Date:** 2026-10-29
- **Status:** implemented and tested locally; now coawst-cloud's `swan-netcdf4-compression`

## Question / why

ROMS writes compressed NetCDF-4 by default since 2026-10-29 (build option
`OUTPUT_OPTIONS="+OUT_NETCDF4 +DEFLATE"`; [entry on compressed ROMS output](2026-10-29_compressed-netcdf4-output.md)). SWAN's
`.nc` output (`BLOCK`, `TABLE`, `SPECOUT`) is written by separate code
(`agioncmd.ftn90`) and was still classic and uncompressed. Author: "see about
getting swan netcdf to have the same compression".

## What was done

- The SWAN change (now coawst-cloud's `swan-netcdf4-compression`):
  `agioncmd.ftn90` now includes `swancpp.h` (ROMS's `cppdefs.h` and the case
  header), so ROMS's two options reach SWAN's NetCDF writer too:
  - `OUT_NETCDF4`: files created as NetCDF-4/HDF5 (`NF90_NETCDF4`) instead of
    classic 64-bit offset;
  - `DEFLATE` as well: every multi-dimensional variable gets shuffle + deflate
    level 1 (`nf90_def_var_deflate(ncid, varid, 1, 1, 1)`), the same call as
    ROMS's `def_var.F`. That covers 16 `nf90_def_var` calls: `BLOCK`/`TABLE`
    quantities, curvilinear x/y and the `SPECOUT` spectral variables. 1-D axes
    and `time` are left uncompressed. Chunks are the library default: one
    record of the whole field.
  - With `OUTPUT_OPTIONS=""` the files stay classic.
- Checked the preprocessed source (cpp with the A15 header, as the COAWST
  makefile runs it). Without the options the code is the old code plus an
  empty `agnc_compress` routine and 16 calls to it. With them, only the create
  mode and the deflate call change. None of the ~45 macros in the header
  rewrites SWAN code (the only hit was the option names in a comment, now
  reworded).
- Local test on the control VM (c3d-standard-4; another session's container
  was running at the same time, load ~5): two A15 vegetation images, both
  with the default `OUTPUT_OPTIONS` (ROMS compressed), built from the patch
  before (`coawst:a15veg_swan_classic`) and after (`coawst:a15veg_swan_nc4`)
  the change. `tests/a15_periodic_test.sh per 0` with `CASE_DIR=Reef_Ideal_A15_veg
  MINUTES=30 OUTDT=2 NOCN=2 TI=1 TJ=2 NWAV=2` (2 ROMS + 2 SWAN processes;
  SWAN collects output on one process). Through `SWANSED` it also wrote a
  `TABLE` `.nc` and a point `SPECOUT` `.nc` (3 points) and a 4 x 4 `FRAME`
  `SPECOUT` `.nc`, so every SWAN NetCDF writer ran: 36 `BLOCK` files
  (7 of them every 2 min, 16 records; the rest at the end) plus 3 point files.
  Runs alternated: classic, compressed, classic, compressed.
- The patch was reworded afterwards (comment only, same compiled code); the
  images were built from the version before that.
- Scripts (scratch, not in the repo): an every-variable bit comparison of all
  `.nc` files of two run folders, and a write benchmark repeating SWAN's
  pattern (open the file, write one record, close, at every output time) in
  Python netCDF4 on the same data.

## Results

| | classic | compressed | ratio |
|---|---|---|---|
| all SWAN `.nc` files (39) | 20.2 MB | 5.0 MB | 4.0x smaller |
| `hsign.nc` / `dir.nc` / `vel.nc` (16 records) | 1.62 / 1.62 / 3.05 MB | 0.64 / 0.53 / 1.28 MB | 2.5 / 3.0 / 2.4x |
| `depth.nc`, `nplants.nc`, `cddragveg.nc` (16 records) | 1.62 MB each | 0.26 / 0.04 / 0.04 MB | 6-46x (smooth or constant fields) |
| one-record budget terms (`dissip`, `propxy`, ...) | 0.27 MB each | 0.03-0.10 MB | 3-9x |
| `p1_table.nc` (3 points x 16 records) | 6 kB | 30 kB | larger: HDF5 files are at least ~20 kB |
| values | | | bit-identical in every variable of every file (39 files, 380 variables, ROMS history included) |
| SWAN's file writes (benchmark, 7 files x 16 records) | 0.52 ms per write | 1.37 ms per write | +0.1 s over the whole run (0.04 %) |
| wall time, 30 min simulated (busy VM) | 241, 233 s | 268, 238 s | within the run-to-run noise |
| Python, read 5 fields x 16 records (cached) | 5 ms | 24 ms | 4-5x slower decoding, milliseconds |

- The compressed runs were also bit-identical to each other and to a
  first run made while the classic image was building.
- SWAN's output costs almost nothing either way. Each write compresses one
  111 x 202 field (under 1 ms), so the effect on run time cannot be measured
  next to the run-to-run noise (+5 s and +27 s in the two pairs, on a VM
  shared with another job).
- `ncdump`, Python netCDF4/xarray and MATLAB read NetCDF-4 files. SWAN's own
  restart files (`RESTART ... UNFormatted`) are binary and unaffected.

## Decision / outcome

Implemented as asked. It follows the existing default `OUTPUT_OPTIONS`, so new
images write compressed SWAN files with no new switch; `OUTPUT_OPTIONS=""`
gives classic files for both models. Images built before this change write
classic SWAN files.

## Open questions

- `SPECOUT` on a whole grid (`COMPGRID`, the 2-D "map" layout of the spectral
  file) was not run: the file would be large. It uses the same
  `agnc_compress` call as the tested point layout.
- Chunking is the library default (one record of the whole field). SWAN
  writes each record in 256 x 256 or 128 x 128 blocks. On a grid larger than
  that, each block write rewrites the record's chunk, which HDF5's chunk
  cache handles. This was not timed on a large grid.

## Details and links

- coawst-cloud's patch document `swan-netcdf4-compression`
- ROMS side: the 2026-10-29 notebook entry on compressed NetCDF-4 ROMS output
