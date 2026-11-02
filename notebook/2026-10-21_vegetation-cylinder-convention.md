# Coral elements are cylinders: plant_thickness = (pi/4) x diameter

- **Date:** 2026-10-21
- **Status:** decision (author); ROMS safeguard `zero_gap_stop` (and `v_drag_depth`) in coawst-cloud's `roms-vegetation`

## Question / why

The vegetation case with periodic SWAN (constant canopy: diameter 0.5 m,
thickness 0.5 m, 4 m-2, height 0.4 m) blew up after 1 h 44 min, with
periodic or non-periodic SWAN. Why?

## What was run

`tests/a15_periodic_test.sh` with `CASE_DIR=Reef_Ideal_A15_veg`, 3 h
coupled runs on the control VM (A15 waves and 20 deg waves), first with
thickness 0.5 m, then with 0.39 m given as an override; then with the
rebuilt image (`zero_gap_stop`, `v_drag_depth`). No cloud cost.

## Results

- `VEG_TURB` (Uittenbogaard 2003, as in Beudin et al. 2017 and Kalra et
  al. 2017) uses the gap between plants L = c_l ((1 - D t n)/n)^(1/2).
  With D t n = 0.5 x 0.5 x 4 = 1, L = 0, the canopy time scale is 0 and
  the dissipation source added to epsilon is infinite. The infinities
  showed at ROMS's periodic seam (sea-level dip, doubled cross-shore
  current at column 201). Kalra et al. used seagrass with D t n below
  0.0025.
- With thickness 0.39 m (pi/4 x 0.5 m: D t equals a 0.5 m cylinder's
  cross-section, solid fraction 0.785) the 3 h coupled periodic runs are
  clean: seam sea level < 0.001 mm, ROMS gets exactly SWAN's Hs and SWAN
  gets ROMS's plant density. Non-periodic SWAN: 11 mm/s jump in ROMS's
  alongshore current at its seam.
- `zero_gap_stop`: ROMS now stops on the first step with a message if D t n >= 1
  anywhere (the old canopy stops after 2 s). `v_drag_depth`: the barotropic
  vegetation drag on v used the u-point depth average (< 0.04 mm/s here).
- Thickness enters only `VEG_TURB`; drag and SWAN's dissipation use
  diameter, density and height.

## Decision / outcome

> **VEGETATION ELEMENTS ARE CYLINDERS: set plant_thickness = (pi/4) x
> plant_diameter** (author, 2026-10-21). (the project conventions)

`cases/Reef_Ideal_A15_veg/init_reef.nc`: thickness 0.5 -> 0.3927 m.
`VEG_FLEX` and SWAN's flexible vegetation (flat-blade bending stiffness
D t^3/12) stay off for rigid cylinders. When choosing coral parameters,
match frontal area D h n and bottom coverage pi D^2 n / 4 separately.

## Open questions

None recorded.

## Details and links

- [`docs/Reef_Ideal_A15_veg.md`, Periodic SWAN and an open problem with the canopy](../docs/Reef_Ideal_A15_veg.md)
- coawst-cloud's patch document `roms-vegetation`
- [docs, Goal](../docs/Reef_Ideal_A15.md)
- Next: [tau_veg units](2026-10-21_veg-turb-tau-veg-units.md), [tau_free](2026-10-21_veg-turb-tau-free.md)
