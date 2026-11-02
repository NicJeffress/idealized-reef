# Reef_Ideal_A15 for COAWST v3.7 (original project)

The author's original idealized-reef project for COAWST v3.7, from which every
A15 case in `cases/` derives. Kept for provenance.

| File | What |
|---|---|
| `Make_grid_Reef_Ideal_A14.m` | MATLAB generator of the ROMS grid and SWAN grid (reef geometry parameters at the top: stretching, lagoon/reef-flat/crest extents and depths, forereef slope, pass width) |
| `Make_init_Reef_Ideal_A15.m` | MATLAB generator of the initial file (rest, T 18 C, S 35, vertical grid, bed and plant fields) |
| `reef_ideal_a15.h`, `ocean.in`, `swan.in`, `coupling.in`, `vegetation.in` | v3.7 inputs (`VARNAME` path made generic) |
| `ana_fsobc.h`, `ana_m2obc.h` | analytical tide and 2-D boundary values |
| `scrip_coawst_reef_grid_default_1.in`, `wavebc_*.txt` | SCRIP input and SWAN boundary files |

Not copied here: the grid, initial and SWAN grid/bathymetry/vegetation files
(identical, bit for bit, to those in `cases/Reef_Ideal_A15/`), the 12.8 MB SCRIP
interpolation-weights file (v3.9 needs none, since SWAN runs on the ROMS grid)
and a plotting script specific to the author's other work.

Changes made in the port to v3.9 are listed in `docs/Reef_Ideal_A15.md`.
