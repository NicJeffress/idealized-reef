#!/usr/bin/env python3
"""Rewrite an A15 initial file for another number of vertical levels N.

Usage: ~/venv/bin/python -I tools/reef/set_nlevels.py IN.nc OUT.nc N

The A15 initial files are at rest, so every 3-D field is uniform along the
vertical (and in the canopy cases uniform everywhere): each field on the
rho levels (dimension sc_r) or the w levels (sc_w) takes its value from the
input's level nearest in the stretched coordinate, which for a uniform field
is simply that value. The vertical coordinate variables (s_rho, s_w, Cs_r,
Cs_w) are recomputed by ROMS from ocean.in and are not read from this file;
they are interpolated linearly here so the file stays self-consistent.
Stratified files (temperature varying with depth) need
tools/stratification/make_strat_init.py afterwards. Set N in ocean.in to
the same value. Used for the vertical-resolution test of 2026-11-03.
"""
import argparse
from pathlib import Path

import netCDF4
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("n", type=int)
    o = ap.parse_args()
    with netCDF4.Dataset(o.src) as a:
        n0 = a.dimensions["sc_r"].size
        # index of the nearest old level for each new level, in the unit interval
        pos_r = lambda n: (np.arange(n) + 0.5) / n          # noqa: E731
        pos_w = lambda n: np.arange(n + 1) / n               # noqa: E731
        near = {"sc_r": np.clip(np.rint(pos_r(o.n) * n0 - 0.5).astype(int), 0, n0 - 1),
                "sc_w": np.clip(np.rint(pos_w(o.n) * n0).astype(int), 0, n0)}
        with netCDF4.Dataset(o.dst, "w", format="NETCDF4") as b:
            for dn, d in a.dimensions.items():
                size = {"sc_r": o.n, "sc_w": o.n + 1}.get(dn, None if d.isunlimited() else d.size)
                b.createDimension(dn, size)
            for vn, v in a.variables.items():
                w = b.createVariable(vn, v.dtype, v.dimensions)
                for at in v.ncattrs():
                    if at != "_FillValue":
                        w.setncattr(at, v.getncattr(at))
                data = np.ma.filled(v[:], 0.0) if v.dtype.kind == "f" else v[:]
                vdim = [k for k, dn in enumerate(v.dimensions) if dn in near]
                if not vdim:
                    w[:] = data
                    continue
                k = vdim[0]; dn = v.dimensions[k]
                if v.ndim == 1:      # s_rho, s_w, Cs_r, Cs_w: linear in the unit interval
                    old = pos_r(n0) if dn == "sc_r" else pos_w(n0)
                    new = pos_r(o.n) if dn == "sc_r" else pos_w(o.n)
                    w[:] = np.interp(new, old, data)
                else:
                    w[:] = np.take(data, near[dn], axis=k)
            b.title = f"{getattr(a, 'title', 'A15 initial file')}, N {n0} -> {o.n} (tools/reef/set_nlevels.py)"
    print(f"{o.dst}: N {n0} -> {o.n}")


if __name__ == "__main__":
    main()
