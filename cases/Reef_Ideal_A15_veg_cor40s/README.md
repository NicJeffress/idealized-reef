# Reef_Ideal_A15_veg_cor40s: A15 canopy case with exaggerated rotation (40 S)

`Reef_Ideal_A15_veg` (density 1 m-2 canopy everywhere, all A15 defaults as of
2026-11-12) with a uniform Coriolis parameter at 40 deg S, more than twice that of a tropical reef at 17.5 deg S (a test of how rotation bends the pass jet; no reef sits this far south):

    f = 2 x 7.2921e-5 x sin(-40 deg) = -9.3745e-5 s-1   (inertial period 18.6 h)

Southern hemisphere: a current is turned to its left (an offshore jet along +y
bends toward -x).

**Only the grid file differs from `Reef_Ideal_A15_veg`** (the `f` variable; x, y, h,
masks, the initial file, SWAN's inputs and `ocean.in` are the same). Every A15
header already compiles `UV_COR`, but the A15 grids carry f = 0, so the other
cases have no rotation and every result in the notebook before 2026-11-12 is for
f = 0. No new image is needed: the grid is read at run time. Made with

    ~/venv/bin/python -I tools/reef/set_coriolis.py cases/Reef_Ideal_A15_veg cases/Reef_Ideal_A15_veg_cor40s --lat -40

The f-plane has no beta effect. SWAN has no Coriolis term, so the waves are
unchanged except through the currents.

First run: `a15cor40s96`, 96 h on Spot in 6 h segments, 15 min 3-D history from
hour 48 for particle tracking.
See `cases/Reef_Ideal_A15_veg/README.md` for everything else about the case.
