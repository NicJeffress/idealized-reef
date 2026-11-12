#!/usr/bin/env python3
"""Copy an A15 case folder and give its grid a uniform Coriolis parameter.

Usage: ~/venv/bin/python -I tools/reef/set_coriolis.py CASE_SRC CASE_DST --lat -17.5

The A15 grids are Cartesian and carry f = 0, so `UV_COR` (compiled in every A15
header) has no effect. This writes f = 2 Omega sin(lat) at every rho point of
CASE_DST/roms_grid_default_1.nc (Omega = 7.2921e-5 s-1, an f-plane: no beta)
and leaves everything else as it is: x, y, h, masks, lat_rho and lon_rho, the
initial file, SWAN's inputs (SWAN has no Coriolis term) and ocean.in. No new
image is needed: the grid file is read at run time.

Prints f and the inertial period. Refuses to overwrite an existing CASE_DST.
"""
import argparse
import shutil
from pathlib import Path

import netCDF4
import numpy as np

OMEGA = 7.2921e-5  # Earth's rotation rate, s-1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--lat", type=float, required=True, help="latitude in degrees (south negative)")
    ap.add_argument("--grid", default="roms_grid_default_1.nc")
    a = ap.parse_args()
    if a.dst.exists():
        raise SystemExit(f"{a.dst} exists; remove it first")
    shutil.copytree(a.src, a.dst)
    f = 2 * OMEGA * np.sin(np.radians(a.lat))
    with netCDF4.Dataset(a.dst / a.grid, "a") as g:
        old = np.ma.filled(g["f"][:], 0.0)
        g["f"][:] = np.full(old.shape, f)
        g.setncattr("coriolis", f"uniform f = 2 * {OMEGA} * sin({a.lat} deg) = {f:.6e} s-1 "
                                f"(tools/reef/set_coriolis.py; was {old.min():g} to {old.max():g})")
    print(f"{a.dst / a.grid}: f = {f:.6e} s-1 at {a.lat} deg "
          f"(was {old.min():g} to {old.max():g}); inertial period {2 * np.pi / abs(f) / 3600:.1f} h")


if __name__ == "__main__":
    main()
