#!/usr/bin/env python3
"""Rewrite an A15 initial file for another number of vertical levels N.

Usage: ~/venv/bin/python -I tools/reef/set_nlevels.py IN.nc OUT.nc N

The A15 initial files are at rest, so every 3-D field is uniform along the
vertical (and in the canopy cases uniform everywhere): each field on the
rho levels (dimension sc_r) or the w levels (sc_w) takes its value from the
input's level nearest in the stretched coordinate, which for a uniform field
is simply that value. The vertical coordinate variables (sc_r, sc_w, Cs_r,
Cs_w) are recomputed exactly for the new N from the file's Vstretching (4)
and theta_s, theta_b (ROMS's own formula); ROMS itself uses ocean.in, but
tools/stratification/make_strat_init.py reads them from this file.
Stratified files (temperature varying with depth) need
tools/stratification/make_strat_init.py afterwards. Set N in ocean.in to
the same value. Used for the vertical-resolution test of 2026-11-03.
"""
import argparse
from pathlib import Path

import netCDF4
import numpy as np


def stretching4(n, theta_s, theta_b):
    """ROMS Vstretching 4 (Shchepetkin 2010): s and C at rho (n) and w (n + 1) levels."""
    def C(sv):
        c = (1.0 - np.cosh(theta_s * sv)) / (np.cosh(theta_s) - 1.0) if theta_s > 0 else -sv ** 2
        return (np.exp(theta_b * c) - 1.0) / (1.0 - np.exp(-theta_b)) if theta_b > 0 else c
    s_r = (np.arange(1, n + 1) - n - 0.5) / n
    s_w = (np.arange(0, n + 1) - n) / n
    return s_r, C(s_r), s_w, C(s_w)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("n", type=int)
    o = ap.parse_args()
    with netCDF4.Dataset(o.src) as a:
        n0 = a.dimensions["sc_r"].size
        vc = {}
        if int(a["Vstretching"][:]) == 4:
            s_r, c_r, s_w, c_w = stretching4(o.n, float(a["theta_s"][:]), float(a["theta_b"][:]))
            # check: the formula must reproduce the input file's own levels
            assert np.allclose(stretching4(n0, float(a["theta_s"][:]), float(a["theta_b"][:]))[1],
                               np.asarray(a["Cs_r"][:], float), atol=1e-7), "Cs_r does not match Vstretching 4"
            vc = {"sc_r": s_r, "Cs_r": c_r, "sc_w": s_w, "Cs_w": c_w}
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
                if v.ndim == 1:      # sc_r, sc_w, Cs_r, Cs_w
                    w[:] = vc[vn] if vn in vc else np.interp(
                        pos_r(o.n) if dn == "sc_r" else pos_w(o.n),
                        pos_r(n0) if dn == "sc_r" else pos_w(n0), data)
                else:
                    w[:] = np.take(data, near[dn], axis=k)
            b.title = f"{getattr(a, 'title', 'A15 initial file')}, N {n0} -> {o.n} (tools/reef/set_nlevels.py)"
    print(f"{o.dst}: N {n0} -> {o.n}")


if __name__ == "__main__":
    main()
