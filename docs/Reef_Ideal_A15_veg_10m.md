# Reef_Ideal_A15_veg_10m: the vegetated case at 10 m (generated)

The grid-convergence twin of [Reef_Ideal_A15_veg](Reef_Ideal_A15_veg.md): every
cell split into 2 x 2, so 10 m cells over the reef and the pass. It is
generated, not stored (the folder is 47 MB):

```bash
python3 -I tools/reef/refine_a15_grid.py cases/Reef_Ideal_A15_veg cases/Reef_Ideal_A15_veg_10m
coawst-cloud/build/coawst/build.sh --case cases/Reef_Ideal_A15_veg_10m --app REEF_IDEAL_A15
```

The script is deterministic: a regenerated folder is bit-identical to the one
used in the options campaign (checked 2026-11-02).

![20 m and 10 m grids near the pass](../figures/a15_refined_10m.png)

## What the script changes

[`tools/reef/refine_a15_grid.py`](../tools/reef/refine_a15_grid.py) copies the
case folder and replaces:

| File | Change |
|---|---|
| `roms_grid_default_1.nc` | 404 x 220 rho points (`Lm` 402, `Mm` 218); x, y and h interpolated linearly in index space (the reef profile keeps its shape, crest still 0.50 m), pm and pn scaled by 2, masks by nearest cell, f, xl, el kept |
| `init_reef.nc` | rewritten at rest on the new grid with the same constant temperature, salinity, bed and plant fields (A15's initial file is uniform in every field) |
| `swan_coord_default_1.grd`, `swan_bathy_default_1.bot` | on the new grid, same layout |
| `swan.in` | `CGRID` / `INPGRID` dimensions and the boundary segments |
| `ocean.in` | `Lm`, `Mm`; `DT` 3 s (halved), `NDTFAST` 12 (halved, so the barotropic step stays 0.25 s; see the caveat), `NTIMES` 28800 (same 24 h); output intervals scaled to stay hourly |

The SWAN time step, the coupling interval and the wave boundary files are
unchanged. Any other factor: `--factor N`.

## Purpose and status

Member `p0-grid10` of the options test campaign, phase 0: does the lagoon
set-up, the crest jet and the pass flow at 20 m change when the grid is halved?
About 8x the cost of the 20 m case per simulated day (4x the cells, half the
time step). Results: to be added in [`results/`](../results).

## Caveats

- **Barotropic Courant number.** The script halves `NDTFAST` together with
  `DT`, so the fast step stays 0.25 s while the cells halve:
  `tools/cfl_check.py` gives a barotropic Courant number of 1.61 (deepest
  water at the north boundary, 10 m pass columns), against 0.81 at 20 m and a
  limit of about 0.9 for LF-AM3. Keeping `NDTFAST` at 24 (fast step 0.125 s)
  brings it back to about 0.8. (The script's docstring says `NDTFAST` is kept;
  the code halves it.) Not yet checked against a run.
- The SWAN seam period of the refined grid is the interpolated ghost-column
  distance, 20 m shorter than the original file's period (which is itself
  40 m longer than ROMS's); the seam effect is below 1e-3 m either way.
- Refinement interpolates the 20 m bathymetry; it adds resolution, not new
  topographic detail.
