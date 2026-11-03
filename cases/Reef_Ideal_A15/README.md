# Reef_Ideal_A15 on COAWST v3.9

> **Grid and roller since 2026-11-03 (author's decisions).** The default grid is
> the breaking-zone grid: 203 x 126 rho points, the rows between 850 and 1150 m
> from the shore (crest, breaking zone, top of the fore reef) split in two (10 m
> across the shore, 20 m elsewhere), DT 6 s kept (barotropic Courant 0.81).
> Made from the 20 m grid (203 x 111, this folder before 2026-11-03 in git) with
> `tools/reef/refine_a15_grid.py --band 850 1150 --factor 2`; it recovers the
> uniform 10 m answer at +16 % cost (notebook 2026-11-03_grid-10m). Row numbers
> quoted below refer to the 20 m grid. The Reniers roller is on
> (`ROLLER_RENIERS`, `WEC_ALPHA` 0.5; notebook 2026-11-03_roller-checks). Also since
> 2026-11-03: 15 vertical levels (was 10), `GLS_Kmin` 1e-8 and SWAN `BKD` breaking.


The user's idealized reef case, ported from COAWST v3.7 (originals in
`reference/Reef_Ideal_A15_v3.7/`, uploaded to
`gs://coawst-runs-nj/incoming/Reef_Ideal_A15/`). Domain and physics are
summarized in `docs/case_design.md`.

Build: `docker build --build-arg COAWST_APPLICATION=REEF_IDEAL_A15
--build-arg CASE_DIR=Projects/Reef_Ideal_A15 -t coawst:reef_a15 .`
The .in files name each other without paths, so the model runs inside the
case directory (`"run_in_case_dir": true` in an ensemble spec). ROMS and
SWAN write NetCDF under `output/`.

## Changes from the v3.7 files

- `reef_ideal_a15.h`: unchanged. (`MCT_INTERP_OC2WV` and `WEC_MELLOR` no
  longer exist in v3.9; both were `#undef` anyway.)
- `ocean.in`: A15's values; `VARNAME` points to the image's
  `ROMS/External/varinfo.yaml` (v3.9 uses YAML, not varinfo.dat);
  `VEGNAM` renamed `VEGNAME`; keys new in v3.9 appended at the end with the
  values of the v3.9 Inlet_test template (NXTR, NDEFXTR, BOT_ALBEDO,
  Lnodal, NSLICE, Z_SLICE, INP_LIB, OUT_LIB, PIO_*, ExtractFlag, GRXNAME,
  XTRNAME). Unused v3.7 keys (SSS_MISMATCH_THRESHOLD, TNUDG_SSS) left in;
  ROMS ignores them.
- `coupling.in`: the v3.9 template (adds the WRF-Hydro keys, drops the
  v3.7 weight-file keys) with A15's settings: 600 s exchanges, swan.in and
  ocean.in, 8 ROMS + 4 SWAN processes (run scripts override these).
- `swan.in`: all BLOCK output `.mat` -> `.nc` (project rule: NetCDF
  output). Physics unchanged.
- `ana_fsobc.h`: v3.9's stock file plus an `REEF_IDEAL_A15` branch with
  A15's tide (zeta_north = -0.15 sin(2 pi t / 12 h)).
- `ana_m2obc.h`: dropped; v3.9's default sets all boundary values to
  zero, which is what A15's version did.
- Interpolation weights (`scrip_reef_grid_default_1.nc`) dropped: the SWAN
  grid is the ROMS rho grid (coordinates identical), so v3.9 needs none.
- Data files copied unchanged: `roms_grid_default_1.nc`, `init_reef.nc`,
  `swan_coord_default_1.grd`, `swan_bathy_default_1.bot`, vegetation
  `.bot` files, `wavebc_*.txt`, `vegetation.in` (vegetation is off in the
  header).

## Periodic SWAN (2026-10-21)

ROMS is east-west periodic (`LBC ... Per`), and since 2026-10-21 so is SWAN
by default (SWAN patch items 13-15, `patches/README.md`). Compared with
A15's original `swan.in`:

    COORDINATES CARTESIAN REPEATING
    BOUNDPAR2 SEGMENT IJ 0 110 201 110 VARIABLE FILE 0 'wavebc_north.txt'
    (BOUNDPAR3 and BOUNDPAR4, the east and west boundaries, commented out)

`wavebc_east.txt` and `wavebc_west.txt` are kept but unused. For the
original non-periodic setup, undo these three changes (as
`tests/a15_periodic_test.sh ref` does). Image: registry tag
`v3.9-26e6fb7-reef_a15-per` (also `reef_a15`), digest
`sha256:85dede9b83cb582d4bdf95e8511e75a514032899510f07480d3b3384e4194458`;
it reproduces the test runs below bit for bit.

`CGRID CURVILINEAR 202 110` and the coordinate file stay: with REPEATING
the grid has 202 columns per period, and the file's 203rd column is column
1 shifted by the period (6061 m). The coupler passes ROMS columns 0..201,
so SWAN's period is one 40 m column longer than ROMS's 6021 m (ROMS column
201 appears twice in SWAN); harmless with the seam in the alongshore-
uniform part of the reef (the two copies differed by < 0.1 mm in Hs).

Coupled test, 3 h on the control VM, image with items 13-15
(`tests/a15_periodic_check.py`; figure `docs/a15_periodic_coupled.png`):

| | periodic, A15 waves | periodic, waves from 20 deg | A15 as is (non-periodic SWAN) |
|---|---|---|---|
| finished (wall time) | yes (26 min; shared the CPU with an image build) | yes, 7.7 min | yes, 7.4 min |
| Hs jump across the seam (SWAN / ROMS) | 0.02 / 0.02 mm | 0.08 / 0.13 mm | - / 0.03 mm |
| ubar jump across ROMS's seam | 2.2 mm/s | 2.1 mm/s | **58 mm/s** |
| largest neighbour jump, uniform reef (ubar) | 2.1 mm/s | 5.6 mm/s | 2.1 mm/s |
| ROMS Hwave = SWAN Hs | yes (< 0.1 mm) | yes | no: 0.27 m at the edges |

With non-periodic SWAN, crest Hs near the side boundaries differed by up to
0.32 m from the periodic run even at normal incidence, and ROMS's periodic
seam got mismatched forcing (the 58 mm/s jump in alongshore current).
