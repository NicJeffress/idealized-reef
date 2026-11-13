# Reef_Ideal_A15_veg_cor: A15 canopy case with Earth's rotation

`Reef_Ideal_A15_veg` (density 1 m-2 canopy everywhere, all A15 defaults as of
2026-11-12) with a uniform Coriolis parameter at 17.5 deg S, a typical tropical South Pacific reef latitude:

    f = 2 x 7.2921e-5 x sin(-17.5 deg) = -4.3856e-5 s-1   (inertial period 39.8 h)

Southern hemisphere: a current is turned to its left (an offshore jet along +y
bends toward -x).

**Only the grid file differs from `Reef_Ideal_A15_veg`** (the `f` variable; x, y, h,
masks, the initial file, SWAN's inputs and `ocean.in` are the same). Every A15
header already compiles `UV_COR`, but the A15 grids carry f = 0, so the other
cases have no rotation and every result in the notebook before 2026-11-12 is for
f = 0. No new image is needed: the grid is read at run time. Made with

    ~/venv/bin/python -I tools/reef/set_coriolis.py cases/Reef_Ideal_A15_veg cases/Reef_Ideal_A15_veg_cor --lat -17.5

The f-plane has no beta effect. SWAN has no Coriolis term, so the waves are
unchanged except through the currents.

First run: `a15cor96`, 96 h on Spot in 6 h segments, 15 min 3-D history from
hour 48 for particle tracking (notebook 2026-11-12_coriolis-and-particles).
See `cases/Reef_Ideal_A15_veg/README.md` for everything else about the case.
