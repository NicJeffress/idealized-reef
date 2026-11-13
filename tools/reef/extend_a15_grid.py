#!/usr/bin/env python3
"""Extend a Reef_Ideal_A15 case offshore: rows added beyond the north boundary, flat bottom.

Usage: ~/venv/bin/python -I tools/reef/extend_a15_grid.py CASE_SRC CASE_DST
           [--north 20000] [--depth 400] [--fine-to 10000] [--fine-growth 1.01] [--fine-max 120]
           [--growth 1.04] [--dy-max 400] [--nudge-band M]

A15's fore-reef slope (1:10) runs to the north boundary, reaching 400 m only at the last
row (y = el, 5.04 km). This keeps every row of CASE_SRC as it is and appends rows until
the new last row (the north boundary, el) is at about --north m from the southern edge:
  spacing   starts from the last row spacing (80 m), grows by --fine-growth per row up to
            --fine-max m while y < --fine-to (the part looked at), then by --growth per row
            up to --dy-max m (a buffer). Growth of a few percent per row keeps the
            truncation error of the stretching small.
  depth     the slope continued and capped at --depth m (flat beyond). Deeper water would
            raise the barotropic Courant number (sqrt(g h) DT/NDTFAST with the 20 m
            alongshore cells): 0.81 at 400 m, about 0.9 at 500 m.
  x, pm, f, mask, lon   copied from the last row (the grid is rectilinear); lat extrapolated
            linearly; pn from the new row positions (also on the old last row, which is
            now interior); xl kept, el = the new last row's y.
Files replaced in CASE_DST (a copy of CASE_SRC):
  roms_grid_default_1.nc
  init_reef.nc          new rows are copies of the old last row (uniform fields stay
                        uniform; a stratified temperature must be rewritten afterwards
                        with tools/stratification/make_strat_init.py --case CASE_DST)
  swan_coord_default_1.grd, swan_bathy_default_1.bot   on the new grid (checked first:
                        the old files must hold the old grid's x_rho, y_rho)
  swan.in               CGRID / INPGRID dimensions and the north boundary segment
  ocean.in              Mm; with --nudge-band M, USER(3) (the width of the interior
                        nudging band of the stratified cases, ana_nudgcoef.h) set to M
Prints the new size, the spacing and the barotropic Courant number.
"""
import argparse
import re
import shutil
from pathlib import Path

import netCDF4
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--north", type=float, default=20000.0)
    ap.add_argument("--depth", type=float, default=400.0)
    ap.add_argument("--fine-to", type=float, default=10000.0)
    ap.add_argument("--fine-growth", type=float, default=1.01)
    ap.add_argument("--fine-max", type=float, default=120.0)
    ap.add_argument("--growth", type=float, default=1.04)
    ap.add_argument("--dy-max", type=float, default=400.0)
    ap.add_argument("--nudge-band", type=float)
    o = ap.parse_args()
    if o.dst.exists():
        raise SystemExit(f"{o.dst} exists")

    with netCDF4.Dataset(o.src / "roms_grid_default_1.nc") as g:
        Lp, Mp = g.dimensions["xi_rho"].size, g.dimensions["eta_rho"].size
        old = {v: np.ma.filled(g[v][:], 0.0) for v in ("h", "x_rho", "y_rho", "pm", "pn", "f", "mask_rho",
                                                        "lat_rho", "lon_rho", "angle")}
        xl = float(g["xl"][:])
        attrs = {v: {a: g[v].getncattr(a) for a in g[v].ncattrs()} for v in g.variables}
        spherical = g["spherical"][:]
    y0 = old["y_rho"][:, 0]
    if np.ptp(old["y_rho"][-1]) > 1e-6:
        raise SystemExit("the last row is not straight")

    # new row positions
    ys, dy = [float(y0[-1])], float(y0[-1] - y0[-2])
    while True:
        dy = min(dy * o.fine_growth, o.fine_max) if ys[-1] < o.fine_to else min(dy * o.growth, o.dy_max)
        if ys[-1] + dy > o.north + 0.5 * dy:
            break
        ys.append(ys[-1] + dy)
    ynew = np.array(ys[1:])
    K = len(ynew)
    Mp2 = Mp + K
    y = np.concatenate([y0, ynew])

    def rows(a, fill):
        return np.concatenate([a, np.repeat(fill[None], K, axis=0)], axis=0)
    new = {}
    for v in ("x_rho", "pm", "f", "mask_rho", "lon_rho", "angle"):
        new[v] = rows(old[v], old[v][-1])
    new["y_rho"] = np.repeat(y[:, None], Lp, axis=1)
    dlat = (old["lat_rho"][-1] - old["lat_rho"][-2]) / (y0[-1] - y0[-2])
    new["lat_rho"] = np.concatenate([old["lat_rho"], old["lat_rho"][-1][None] + (ynew - y0[-1])[:, None] * dlat[None]])
    slope = (old["h"][-1] - old["h"][-2]) / (y0[-1] - y0[-2])
    hext = np.minimum(old["h"][-1][None] + (ynew - y0[-1])[:, None] * slope[None], o.depth)
    new["h"] = np.concatenate([old["h"], hext], axis=0)
    pn = np.empty(Mp2)
    pn[:Mp - 1] = old["pn"][:Mp - 1, 0]
    pn[Mp - 1:-1] = 2.0 / (y[Mp:] - y[Mp - 2:-2])
    pn[-1] = 1.0 / (y[-1] - y[-2])
    new["pn"] = np.repeat(pn[:, None], Lp, axis=1)
    el = float(y[-1])

    m = new["mask_rho"]
    mask_u, mask_v = m[:, :-1] * m[:, 1:], m[:-1] * m[1:]
    mask_psi = m[:-1, :-1] * m[:-1, 1:] * m[1:, :-1] * m[1:, 1:]
    avg_u = lambda a: 0.5 * (a[:, :-1] + a[:, 1:])          # noqa: E731
    avg_v = lambda a: 0.5 * (a[:-1] + a[1:])                 # noqa: E731
    avg_p = lambda a: 0.25 * (a[:-1, :-1] + a[:-1, 1:] + a[1:, :-1] + a[1:, 1:])   # noqa: E731

    # SWAN coordinate file must be the old grid's rho points, else this script's layout is wrong
    c = np.loadtxt(o.src / "swan_coord_default_1.grd").ravel()
    if c.size != 2 * Lp * Mp or not (np.allclose(c[:Lp * Mp], old["x_rho"].ravel(), atol=1e-3)
                                     and np.allclose(c[Lp * Mp:], old["y_rho"].ravel(), atol=1e-3)):
        raise SystemExit("swan_coord_default_1.grd does not hold the grid's x_rho, y_rho; extend this script")

    shutil.copytree(o.src, o.dst)
    with netCDF4.Dataset(o.dst / "roms_grid_default_1.nc", "w", format="NETCDF4") as g:
        g.createDimension("xi_psi", Lp - 1); g.createDimension("xi_rho", Lp)
        g.createDimension("xi_u", Lp - 1); g.createDimension("xi_v", Lp)
        g.createDimension("eta_psi", Mp2 - 1); g.createDimension("eta_rho", Mp2)
        g.createDimension("eta_u", Mp2); g.createDimension("eta_v", Mp2 - 1)
        g.createDimension("one", 1); g.createDimension("two", 2); g.createDimension("bath", 1)

        def var(name, dims, data, dtype="f8"):
            vv = g.createVariable(name, dtype, dims)
            for a, val in attrs.get(name, {}).items():
                if a != "_FillValue":
                    vv.setncattr(a, val)
            vv[:] = data
            return vv
        var("xl", ("one",), xl); var("el", ("one",), el)
        g.createVariable("JPRJ", "S1", ("two",))
        g.createVariable("spherical", "S1", ("one",))[:] = spherical
        var("depthmin", ("one",), float(new["h"].min())); var("depthmax", ("one",), float(new["h"].max()))
        var("hraw", ("bath", "eta_rho", "xi_rho"), new["h"][None])
        var("h", ("eta_rho", "xi_rho"), new["h"])
        var("f", ("eta_rho", "xi_rho"), new["f"])
        var("pm", ("eta_rho", "xi_rho"), new["pm"]); var("pn", ("eta_rho", "xi_rho"), new["pn"])
        var("dndx", ("eta_rho", "xi_rho"), 0.0 * new["h"]); var("dmde", ("eta_rho", "xi_rho"), 0.0 * new["h"])
        for pt, fn, dims in (("rho", lambda a: a, ("eta_rho", "xi_rho")), ("psi", avg_p, ("eta_psi", "xi_psi")),
                             ("u", avg_u, ("eta_u", "xi_u")), ("v", avg_v, ("eta_v", "xi_v"))):
            var(f"x_{pt}", dims, fn(new["x_rho"])); var(f"y_{pt}", dims, fn(new["y_rho"]))
            var(f"lat_{pt}", dims, fn(new["lat_rho"])); var(f"lon_{pt}", dims, fn(new["lon_rho"]))
        var("mask_rho", ("eta_rho", "xi_rho"), m); var("mask_u", ("eta_u", "xi_u"), mask_u)
        var("mask_v", ("eta_v", "xi_v"), mask_v); var("mask_psi", ("eta_psi", "xi_psi"), mask_psi)
        var("angle", ("eta_rho", "xi_rho"), new["angle"])
        var("visc_factor", ("eta_rho", "xi_rho"), 1.0 + 0.0 * new["h"])
        var("diff_factor", ("eta_rho", "xi_rho"), 1.0 + 0.0 * new["h"])
        g.title = (f"Reef_Ideal_A15 extended offshore from {o.src.name} to el {el:.0f} m, flat {o.depth:g} m "
                   f"(tools/reef/extend_a15_grid.py)")

    # initial file: new rows copy the old last row
    with netCDF4.Dataset(o.src / "init_reef.nc") as a, netCDF4.Dataset(o.dst / "init_reef.nc", "w", format="NETCDF4") as b:
        sizes = {"erho": Mp2, "eu": Mp2, "ev": Mp2 - 1, "epsi": Mp2 - 1}
        for dn, d in a.dimensions.items():
            b.createDimension(dn, sizes.get(dn, None if d.isunlimited() else d.size))
        for vn, v in a.variables.items():
            w = b.createVariable(vn, v.dtype, v.dimensions)
            for at in v.ncattrs():
                if at != "_FillValue":
                    w.setncattr(at, v.getncattr(at))
            data = np.ma.filled(v[:], 0.0)
            ax = [k for k, dn in enumerate(v.dimensions) if dn in sizes]
            if ax:
                k = ax[0]
                last = np.take(data, [-1], axis=k)
                data = np.concatenate([data, np.repeat(last, w.shape[k] - data.shape[k], axis=k)], axis=k)
            w[:] = data
        for at in a.ncattrs():
            b.setncattr(at, a.getncattr(at))
        b.title = f"{getattr(a, 'title', 'A15 initial file')}, extended offshore to {el:.0f} m (rows copy the old last row)"

    with open(o.dst / "swan_coord_default_1.grd", "w") as f:
        for block in (new["x_rho"], new["y_rho"]):
            f.write("".join(f"{v:20.12f}\n" for v in block.ravel()))
    np.savetxt(o.dst / "swan_bathy_default_1.bot", np.where(m > 0, new["h"], 9999.0), fmt="%15.8f")

    sw = (o.dst / "swan.in").read_text()
    n = 0
    sw, k = re.subn(rf"SEGMENT IJ 0 {Mp - 1} (\d+) {Mp - 1}", lambda mm: f"SEGMENT IJ 0 {Mp2 - 1} {mm.group(1)} {Mp2 - 1}", sw); n += k
    sw, k = re.subn(rf"SEGMENT IJ (\d+) (\d+) (\d+) {Mp - 1}\b", lambda mm: f"SEGMENT IJ {mm.group(1)} {mm.group(2)} {mm.group(3)} {Mp2 - 1}", sw); n += k
    sw, k = re.subn(rf"\b{Lp - 1} {Mp - 1}\b", f"{Lp - 1} {Mp2 - 1}", sw); n += k
    (o.dst / "swan.in").write_text(sw)

    oc = (o.dst / "ocean.in").read_text()
    oc, k = re.subn(r"^( *Mm *== *)\d+", lambda mm: f"{mm.group(1)}{Mp2 - 2}", oc, count=1, flags=re.M)
    assert k == 1
    if o.nudge_band:
        mm = re.search(r"^( *USER *=+ *)(.*)$", oc, re.M)
        vals = mm.group(2).split()
        vals[2] = f"{o.nudge_band:.1f}d0"
        oc = oc[:mm.start(2)] + "  ".join(vals) + oc[mm.end(2):]
    (o.dst / "ocean.in").write_text(oc)

    dt = float(re.sub("[dD].*", "", re.search(r"^ *DT *== *([0-9.dD+-]+)", oc, re.M).group(1)))
    ndtf = int(re.search(r"^ *NDTFAST *== *([0-9]+)", oc, re.M).group(1))
    wet = m > 0
    cb = (np.sqrt(9.81 * new["h"]) * (dt / ndtf) * np.sqrt(new["pm"] ** 2 + new["pn"] ** 2))[wet].max()
    dys = np.diff(y)
    print(f"{o.dst}: rho grid {Lp} x {Mp2} (Mm {Mp2 - 2}, {K} rows added), el {el:.0f} m, "
          f"row spacing {dys[Mp - 2]:.0f} m at {y0[-1] / 1e3:.2f} km, {dys[np.argmin(abs(y[1:] - o.fine_to))]:.0f} m at "
          f"{o.fine_to / 1e3:g} km, {dys[-1]:.0f} m at the boundary (largest growth {np.max(dys[1:] / dys[:-1]):.3f}); "
          f"h max {new['h'].max():.1f} m; barotropic Courant {cb:.2f} (DT {dt:g} s, NDTFAST {ndtf}); "
          f"{n} SWAN edits" + (f"; USER(3) {o.nudge_band:g} m" if o.nudge_band else ""))


if __name__ == "__main__":
    main()
