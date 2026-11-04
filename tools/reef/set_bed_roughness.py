#!/usr/bin/env python3
"""Set the bed roughness of an A15 initial file, in place.

Usage: ~/venv/bin/python -I tools/reef/set_bed_roughness.py INIT.nc Z0

Z0 is the bottom roughness length (m). With SSW_CALC_ZNOT, ROMS takes it from the
grain diameter (zoN = 2.5 d50 / 30, so d50 = 12 z0) and ignores Zob in ocean.in;
the coupler sends SWAN KN = 30 z0. So z0 0.01 m is KN 0.3 m and z0 0.001 m is KN
0.03 m. Two floors apply to SWAN's KN and must be below the value wanted:
FRICTION MADSEN [kn] in swan.in (set it to KN), and the coupler's own, 0.05 m without
VEG_SWAN_COUPLING and 0.0015 m with it (a smooth bare reef therefore needs the canopy
build with density 0, not the build without vegetation).
"""
import argparse

import netCDF4
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("init")
    ap.add_argument("z0", type=float)
    o = ap.parse_args()
    d50 = 12.0 * o.z0
    with netCDF4.Dataset(o.init, "r+") as d:
        v = d["grain_diameter"]
        old = np.unique(np.ma.filled(v[:], 0.0))
        v[:] = np.full(v.shape, d50)
    print(f"{o.init}: grain_diameter {old} -> {d50} m (z0 {o.z0} m, KN {30.0 * o.z0} m)")


if __name__ == "__main__":
    main()
