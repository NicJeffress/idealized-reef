# Tools

Python scripts (numpy, scipy, netCDF4, matplotlib) that make variants of the
cases. Run them from the repository root with `python3 -I`.

| Script | What it does |
|---|---|
| [`vegetation/make_veg_init.py`](vegetation/README.md) | writes spatially varying canopy fields (density, diameter, height, thickness = pi/4 x diameter) into a copy of an A15 initial file from a JSON pattern; examples in `vegetation/patterns/` |
| `stratification/make_strat_init.py` | writes a constant N² (optionally below a mixed layer) into an initial file, with the case's linear equation of state; prints the internal-wave Courant number |
| `thermal/far_field.py` | the 1-D far-field ocean column of `Reef_Ideal_A15_veg_therm`; writes the climatology and boundary files each thermal run needs |
| `cfl_check.py` | barotropic and internal-wave Courant numbers of a case before a run (and the advective ones from run logs) |
| `fb_stability.py` | linear stability limit of the AB3-AM4 barotropic kernel (0.890) |
| `reef/refine_a15_grid.py` | refines an A15 case folder by an integer factor (makes `Reef_Ideal_A15_veg_10m`) |
| `reef/make_thin_crest.py` | adds the thin-crest grid variants to a copy of an A15 case |

Circle_Island's generator lives in its case folder
(`cases/Circle_Island/make_case.py`), as do the Swan_Periodic_Test input
scripts. The figures are made by `figures/make_figures.py`.
