# Spatially varying vegetation (coral canopy)

`make_veg_init.py` writes plant fields (density, diameter, height,
thickness) into the ROMS initial file of `cases/Reef_Ideal_A15_veg`
from a small JSON pattern: where the reef has plants, where it is bare,
and how much is there. ROMS reads the fields from the initial file and
sends them to SWAN at every coupling exchange (`VEG_SWAN_COUPLING`), so
one file sets the canopy for both models. The case's `swan.in` uses
`VEGETATION 3` (SWAN takes density, height and diameter at each point from
ROMS) rather than `VEGETATION 1` (one height and diameter for the whole grid).

```
python3 -I tools/vegetation/make_veg_init.py tools/vegetation/patterns/patchy.json \
    -o init_reef.nc --png patchy.png
```

It prints, per reef zone, the area, the share of each plant class and
the mean frontal area, and with `--png` draws a map. Examples in
`patterns/`: `const.json` (the case's constant canopy), `zones.json`
(amount by zone), `patchy.json` (random patches).

## Pattern format

```json
{
  "description": "free text, shown in the summary and the map",
  "classes": {
    "sparse": {"density": 1, "diameter": 0.5, "height": 0.4},
    "dense":  {"density": 4, "diameter": 0.5, "height": 0.4}
  },
  "zones": {"crest_depth": 1.0},
  "layers": [
    {"where": ["forereef", "crest"], "class": "dense"},
    {"where": "backreef",
     "patches": {"size_m": 150, "seed": 1, "cover": {"dense": 0.3, "sparse": 0.3}}},
    {"where": {"zone": "reef", "x_m": [-500, 500]}, "class": "bare"}
  ]
}
```

- **classes**: plant types by density n (m-2), diameter D (m) and
  height h (m). The amount of canopy is usually described by the
  frontal area per bed area lambda_f = n D h (the drag) and the bed
  coverage pi D^2 n / 4. **Thickness is not given: plants are
  cylinders, thickness = pi/4 x D** (project convention; ROMS uses
  D x thickness as each plant's footprint). `bare` always exists (no
  plants: all four fields 0). The script stops if pi D^2 n / 4 >= 1 (no
  gap between plants, ROMS's `VEG_TURB` would divide by zero) and warns
  above 0.8.
- **layers** are applied in order; a later layer overwrites an earlier
  one. Everything starts bare. A layer sets one `class` everywhere in
  its `where`, or draws `patches` there.
- **where**: a zone name, a list of zone names, or an object whose
  conditions must all hold: `zone`, `x_m` [x0, x1] (alongshore, metres,
  grid coordinates; a range may run past the periodic seam at
  x = +-3.0 km), `y_m` [y0, y1] (cross-shore), `depth_m` [h0, h1].
- **zones** come from the bathymetry (thresholds in `"zones"`, defaults
  in brackets). The crest line is the middle of the shallowest band in
  each column; the reef's typical profile is the median depth of each
  grid row.
  - `pass`: more than `pass_excess` [1 m] deeper than the typical profile
  - `crest`: depth <= `crest_depth` [1 m]
  - `forereef`: seaward of the crest line, depth <= `forereef_depth`
    [20 m]; `deep` beyond
  - `backreef`: landward of the crest line, depth <= `backreef_depth`
    [5 m]; `lagoon` beyond
  - groups: `reef` = backreef + crest + forereef, `all` = every wet cell

  For A15 that gives lagoon 301 ha, backreef 216 ha, crest 68 ha,
  forereef 123 ha, pass 23 ha (maps: `--png`).
- **patches**: a smooth random field (Gaussian-filtered noise, built in
  metres on a uniform grid that is exactly periodic alongshore, so
  patches wrap across the seam and do not depend on the stretched ROMS
  spacing), thresholded so that each class in `cover` gets that share of
  the layer's area (area-weighted). The highest values get the first
  class, the next ones the second, so a second class rings the first,
  like the sparse fringe of a dense patch; the rest of the area gets
  `rest` (default `bare`). `size_m` is the rough patch diameter
  (smoothing sigma = size_m / 3); the summary reports the mean
  equivalent diameter of the patches it made (150 m in `patchy.json`
  gives 160 m dense patches). The same `seed` gives the same field.

## What the file contains

The initial file is a copy of the case's `init_reef.nc` with new
`plant_density`, `plant_diameter`, `plant_height`, `plant_thickness`,
plus `veg_class` and `reef_zone` maps (codes with `flag_meanings`; ROMS
ignores them, analysis can use them) and the pattern as the global
attribute `vegetation_pattern`. The domain is EW periodic: fields are
built on the interior columns 1..Lm and copied to the ghost columns
(0 = Lm, Lm+1 = 1), because ROMS reads the ghost columns from the file
and sends columns 0..Lm to SWAN. Land cells are bare.

## In ensembles

Each ensemble member gets its own initial file: run the script once per member
with that member's pattern (patterns are small JSON files, easy to template:
e.g. a different `seed` or `density` per member) and give each run its file as
`ININAME`.

## Bare cells and patch edges in the models

Checked in the source (2026-10-22): zero density gives zero drag and
zero turbulence source in ROMS (`VEG_TURB`'s gap between plants is
capped at 1e11 m, so no division by zero), and zero dissipation in
SWAN's `SVEG_COAWST` (all its divisions are guarded). At a patch edge
ROMS averages the drag of the two cells onto the face between them, so
a bare cell next to a patch gets a little TKE from the plant work on its
faces but no matching dissipation source (its gap is the 1e11 m cap):
the edge is half a cell wide, as for any field on the C grid.

## Plants reaching the surface

At low tide the A15 crest (0.50 m deep) has about 0.35 m of water, less
than the 0.4 m plant height in the examples. ROMS then applies the drag
over the whole water column. SWAN's `SVEG_COAWST` used Cd = 1.95 there
whatever the drag method (and nothing when depth equals height);
coawst-cloud's `swan-vegetation-fixes` makes it use the `VEGETATION 3` drag method (method 1:
Cd = 1, as ROMS's `CD_VEG`), so the canopy dissipates waves the same
way it did with `VEGETATION 1`. The summary reports how much of the
vegetated area reaches the surface at the lowest tide (h - 0.17 m).

## Time step: the vegetation drag is explicit

ROMS steps the vegetation drag explicitly, so a canopy limits the time
step: the number 2 alpha |U| DT (alpha = 0.5 Cd D n; 1 m-1 for the dense
example class) must stay near or below about 1. Uniform or zoned
canopies slow the flow and run at A15's DT 6 s; patchy canopies funnel
fast flow from bare gaps into dense patches, and `patchy.json` blew up at
6 s after 42 min but ran at 3 s. The drag stays explicit by default; the
build option `VEG_DRAG_IMPLICIT` (coawst-cloud's `roms-veg-implicit`) takes it
implicitly and runs the patchy pattern at 6 s (see
`docs/Reef_Ideal_A15_veg.md`).
