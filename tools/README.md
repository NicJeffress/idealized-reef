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
| `reef/extend_a15_grid.py` | extends an A15 case offshore: rows added beyond the north boundary with gentle stretching, bottom flat at `--depth` (400 m); makes the `*_20km` cases |
| `reef/extract_jet_fields.py` | streams a segmented run's history files from the bucket and keeps top-layer and depth-mean fields at every record plus full-depth sections at 2.5, 5, 10 and 15 km (0.8 GB instead of 19 GB) |
| `reef/jet_head.py` | surface jet head against time: farthest point above 0.05 / 0.02 m/s connected to the pass (periodic), and the nudging band it is measured against |
| `reef/jet_core_path.py` | time-mean path and speed of the surface jet core by distance from shore, for extracted or full history files |
| `reef/make_thin_crest.py` | adds the thin-crest grid variants to a copy of an A15 case |
| `reef/set_coriolis.py` | copies a case folder and sets a uniform Coriolis parameter f = 2 Omega sin(lat) in its grid (`--lat -17.5`); makes the `*_cor*` cases |
| `reef/jet_bend.py` | follows the pass jet record by record (connected depth-mean Lagrangian speed above a threshold): head position, bearing, north-boundary contact, periodic wrap |
| `reef/track_particles.py` | seeds particles (lagoon, back reef edge to edge, or the whole domain) and runs ROMSPath (coawst-cloud image) on a merged history file, in parallel chunks |

Circle_Island's generator lives in its case folder
(`cases/Circle_Island/make_case.py`), as do the Swan_Periodic_Test input
scripts. The figures are made by `figures/make_figures.py`; the README particle figure and GIF by `figures/make_profile_figure.py`, the 40°S jet comparison by `figures/jet_compare.py`, the 20 km domain figures by `figures/jet_20km.py`, and the side-by-side particle GIF and movie of several runs by `figures/make_compare_gif.py`.
