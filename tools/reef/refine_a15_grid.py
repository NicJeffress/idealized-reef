#!/usr/bin/env python3
"""Refine a Reef_Ideal_A15 case by an integer factor (grid convergence test).

Usage: ~/venv/bin/python -I tools/reef/refine_a15_grid.py CASE_SRC CASE_DST [--factor 2]
           [--band Y0 Y1]

--band Y0 Y1 refines only across the shore (the eta direction) and only the rho
rows whose y lies between Y0 and Y1 (m from the southern edge, i.e. from the
shore): each such row is split into `factor` rows, x and every other row are
kept, DT is kept (print the barotropic Courant number and check it), and the
SWAN boundary segments are renumbered. Used to resolve the breaking zone at the
top of the fore reef without refining the whole grid (2026-11-03).

Copies CASE_SRC (e.g. cases/Reef_Ideal_A15_veg) to CASE_DST and replaces:
  roms_grid_default_1.nc   every old cell split into factor x factor cells; x, y
                           and h interpolated linearly in index space (the
                           reef profile keeps its shape), pm and pn scaled by
                           the factor, masks by nearest cell, angle 0, dndx and
                           dmde 0 (the case has no CURVGRID), f, xl, el kept
  init_reef.nc             rewritten at rest on the new grid: uniform fields
                           copied, rho-point fields that vary (the stratified
                           temperature) interpolated in index space like h
  swan_{dens,hght,diam,thck}.bot   if present (bare cases), nearest cell
  swan_coord_default_1.grd, swan_bathy_default_1.bot   on the new grid, same layout
  swan.in                  CGRID / INPGRID dimensions and the boundary segments
  ocean.in                 Lm, Mm; DT divided by the factor (NDTFAST unchanged,
                           so the barotropic step is divided too: the barotropic
                           Courant number stays what it was), NTIMES and
                           N(RST|HIS|AVG|DIA) multiplied by it (same run length
                           and output interval)
The SWAN time step, coupling interval and wave boundary files are unchanged.
Prints the new dimensions and the smallest cells.
"""
import argparse
import re
import shutil
from pathlib import Path

import netCDF4
import numpy as np


def interp2(a, s, t):
    """Linear interpolation of a 2-D array at fractional index coordinates (t rows, s columns)."""
    j = np.clip(np.floor(t).astype(int), 0, a.shape[0] - 2)
    i = np.clip(np.floor(s).astype(int), 0, a.shape[1] - 2)
    ft = (t - j)[:, None]
    fs = (s - i)[None, :]
    return ((1 - ft) * (1 - fs) * a[j][:, i] + (1 - ft) * fs * a[j][:, i + 1]
            + ft * (1 - fs) * a[j + 1][:, i] + ft * fs * a[j + 1][:, i + 1])


def nearest2(a, s, t):
    return a[np.clip(np.rint(t).astype(int), 0, a.shape[0] - 1)][:, np.clip(np.rint(s).astype(int), 0, a.shape[1] - 1)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("--factor", type=int, default=2)
    ap.add_argument("--band", nargs=2, type=float, metavar=("Y0", "Y1"))
    o = ap.parse_args()
    r = o.factor
    if o.dst.exists():
        shutil.rmtree(o.dst)
    shutil.copytree(o.src, o.dst)

    with netCDF4.Dataset(o.src / "roms_grid_default_1.nc") as g:
        Lp, Mp = g.dimensions["xi_rho"].size, g.dimensions["eta_rho"].size
        old = {v: np.ma.filled(g[v][:], 0.0) for v in ("h", "x_rho", "y_rho", "pm", "pn", "f", "mask_rho", "lat_rho", "lon_rho")}
        xl, el = float(g["xl"][:]), float(g["el"][:])
        attrs = {v: {a: g[v].getncattr(a) for a in g[v].ncattrs()} for v in g.variables}
        spherical = g["spherical"][:]
    Lm, Mm = Lp - 2, Mp - 2
    if o.band:
        # rows refined only inside the band: old interior row j (cell j-0.5..j+0.5 in
        # index space) becomes rj rows with centres at j - 0.5 + (k + 0.5) / rj
        y0 = old["y_rho"][:, 0]
        rj = np.where((y0 >= o.band[0]) & (y0 <= o.band[1]), r, 1)
        rj[0] = rj[-1] = 1
        if rj[1] != 1 or rj[-2] != 1:
            raise SystemExit("--band must not include the first or last interior row")
        t = [0.0]
        newrow = np.zeros(Mp, int)
        for j in range(1, Mp - 1):
            newrow[j] = len(t) + rj[j] // 2
            t += [j - 0.5 + (k + 0.5) / rj[j] for k in range(rj[j])]
        t.append(float(Mp - 1))
        newrow[-1] = len(t) - 1
        t = np.array(t)
        s = np.arange(Lp, dtype=float)
        Lp2, Mp2 = Lp, len(t)
        rx, ry = 1, rj[np.clip(np.rint(t).astype(int), 0, Mp - 1)][:, None]
    else:
        Lp2, Mp2 = r * Lm + 2, r * Mm + 2
        # refined rho index I has old-index coordinate s = 0.5 + (I - 0.5) / r  (interior cells
        # I = 1..r*Lm cover old cells 1..Lm; the ghost cells fall between the old ghost and the first cell)
        s = 0.5 + (np.arange(Lp2) - 0.5) / r
        t = 0.5 + (np.arange(Mp2) - 0.5) / r
        newrow = None
        rx = ry = r
    new = {}
    for v in ("h", "x_rho", "y_rho", "f", "lat_rho", "lon_rho"):
        new[v] = interp2(old[v], s, t)
    new["pm"] = rx * interp2(old["pm"], s, t)
    new["pn"] = ry * interp2(old["pn"], s, t)
    new["mask_rho"] = nearest2(old["mask_rho"], s, t)
    m = new["mask_rho"]
    mask_u = m[:, :-1] * m[:, 1:]
    mask_v = m[:-1] * m[1:]
    mask_psi = m[:-1, :-1] * m[:-1, 1:] * m[1:, :-1] * m[1:, 1:]
    avg_u = lambda a: 0.5 * (a[:, :-1] + a[:, 1:])          # noqa: E731
    avg_v = lambda a: 0.5 * (a[:-1] + a[1:])                 # noqa: E731
    avg_p = lambda a: 0.25 * (a[:-1, :-1] + a[:-1, 1:] + a[1:, :-1] + a[1:, 1:])   # noqa: E731

    with netCDF4.Dataset(o.dst / "roms_grid_default_1.nc", "w", format="NETCDF4") as g:
        g.createDimension("xi_psi", Lp2 - 1); g.createDimension("xi_rho", Lp2)
        g.createDimension("xi_u", Lp2 - 1); g.createDimension("xi_v", Lp2)
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
        var("angle", ("eta_rho", "xi_rho"), 0.0 * new["h"])
        var("visc_factor", ("eta_rho", "xi_rho"), 1.0 + 0.0 * new["h"])
        var("diff_factor", ("eta_rho", "xi_rho"), 1.0 + 0.0 * new["h"])
        g.title = (f"Reef_Ideal_A15 refined {r}x across the shore for y {o.band[0]:g}-{o.band[1]:g} m from {o.src.name}"
                   if o.band else f"Reef_Ideal_A15 refined {r}x from {o.src.name}") + " (tools/reef/refine_a15_grid.py)"

    # initial file: the same uniform fields on the new grid
    with netCDF4.Dataset(o.src / "init_reef.nc") as a, netCDF4.Dataset(o.dst / "init_reef.nc", "w", format="NETCDF4") as b:
        sizes = {"xpsi": Lp2 - 1, "xrho": Lp2, "xu": Lp2 - 1, "xv": Lp2, "epsi": Mp2 - 1, "erho": Mp2, "eu": Mp2, "ev": Mp2 - 1}
        for dn, d in a.dimensions.items():
            b.createDimension(dn, sizes.get(dn, None if d.isunlimited() else d.size))
        for vn, v in a.variables.items():
            w = b.createVariable(vn, v.dtype, v.dimensions)
            for at in v.ncattrs():
                if at != "_FillValue":
                    w.setncattr(at, v.getncattr(at))
            data = v[:]
            if any(dn in sizes for dn in v.dimensions):
                vals = np.unique(np.ma.filled(data, 0.0))
                if len(vals) == 1:
                    w[:] = np.full(w.shape, vals[0])
                elif v.dimensions[-2:] == ("erho", "xrho"):
                    # e.g. the stratified temperature (a function of depth, so it varies
                    # across the slope): interpolated in index space like h, slice by slice
                    a2 = np.ma.filled(data, 0.0).reshape(-1, Mp, Lp)
                    out = np.stack([interp2(sl, s, t) for sl in a2])
                    w[:] = out.reshape(w.shape)
                else:
                    raise SystemExit(f"init_reef.nc: {vn} is not uniform and not on rho points; extend this script")
            else:
                w[:] = data
        b.title = f"{getattr(a, 'title', 'A15 initial file')} refined {r}x"

    # SWAN grid and bathymetry: the x block then the y block, one value per line (as the original)
    with open(o.dst / "swan_coord_default_1.grd", "w") as f:
        for block in (new["x_rho"], new["y_rho"]):
            f.write("".join(f"{v:20.12f}\n" for v in block.ravel()))
    bot = np.where(m > 0, new["h"], 9999.0)
    np.savetxt(o.dst / "swan_bathy_default_1.bot", bot, fmt="%15.8f")
    # SWAN plant fields read from files (the bare cases' swan_dens/hght/diam/thck.bot):
    # one value per rho point, nearest cell on the new grid
    for fn in ("swan_dens.bot", "swan_hght.bot", "swan_diam.bot", "swan_thck.bot"):
        if (o.src / fn).exists():
            a2 = np.loadtxt(o.src / fn).ravel()
            if a2.size != Lp * Mp:
                raise SystemExit(f"{fn}: {a2.size} values, expected {Lp * Mp}; extend this script")
            np.savetxt(o.dst / fn, nearest2(a2.reshape(Mp, Lp), s, t), fmt="%15.8f")

    sw = (o.dst / "swan.in").read_text()
    n = 0
    row = (lambda j: int(newrow[j])) if newrow is not None else (lambda j: r * j)
    sw, k = re.subn(rf"SEGMENT IJ 0 {Mp - 1} {Lp - 2} {Mp - 1}", f"SEGMENT IJ 0 {Mp2 - 1} {Lp2 - 2} {Mp2 - 1}", sw); n += k
    sw, k = re.subn(rf"SEGMENT IJ 0 {Mp - 1} {Lp - 1} {Mp - 1}", f"SEGMENT IJ 0 {Mp2 - 1} {Lp2 - 1} {Mp2 - 1}", sw); n += k
    sw, k = re.subn(rf"SEGMENT IJ {Lp - 1} (\d+) {Lp - 1} {Mp - 1}", lambda mm: f"SEGMENT IJ {Lp2 - 1} {row(int(mm.group(1)))} {Lp2 - 1} {Mp2 - 1}", sw); n += k
    sw, k = re.subn(rf"SEGMENT IJ 0 (\d+) 0 {Mp - 1}", lambda mm: f"SEGMENT IJ 0 {row(int(mm.group(1)))} 0 {Mp2 - 1}", sw); n += k
    # grid dimensions last, so the segment patterns above still see the old ones
    sw, k = re.subn(rf"\b{Lp - 1} {Mp - 1}\b", f"{Lp2 - 1} {Mp2 - 1}", sw); n += k
    (o.dst / "swan.in").write_text(sw)

    oc = (o.dst / "ocean.in").read_text()
    def setkey(text, key, fn):
        pat = rf"^( *{key} *== *)([0-9.dD+-]+)"
        mm = re.search(pat, text, re.M)
        assert mm, key
        return text[:mm.start(2)] + fn(mm.group(2)) + text[mm.end(2):]
    oc = setkey(oc, "Lm", lambda v: str(Lp2 - 2))
    oc = setkey(oc, "Mm", lambda v: str(Mp2 - 2))
    dt0 = float(re.sub("[dD].*", "", re.search(r"^ *DT *== *([0-9.dD+-]+)", oc, re.M).group(1)))
    ndtf = int(re.search(r"^ *NDTFAST *== *([0-9]+)", oc, re.M).group(1))
    dt_new = dt0 if o.band else dt0 / r
    if not o.band:
        oc = setkey(oc, "DT", lambda v: f"{dt_new:g}d0")
        oc = setkey(oc, "NTIMES", lambda v: str(r * int(v)))
        for key in ("NRST", "NHIS", "NAVG", "NDIA"):
            oc = setkey(oc, key, lambda v: str(r * int(v)))
    (o.dst / "ocean.in").write_text(oc)
    wet = new["mask_rho"] > 0
    cb = (np.sqrt(9.81 * new["h"]) * (dt_new / ndtf) * np.sqrt(new["pm"] ** 2 + new["pn"] ** 2))[wet].max()
    print(f"{o.dst}: rho grid {Lp2} x {Mp2} (Lm {Lp2 - 2}, Mm {Mp2 - 2}), {n} SWAN dimension edits, "
          f"DT {dt_new:g} s, barotropic Courant {cb:.2f} (NDTFAST {ndtf}); "
          f"smallest cells {1 / new['pm'].max():.1f} x {1 / new['pn'].max():.1f} m; "
          f"crest depth min {new['h'][new['h'] < 1].min():.3f} m; h range {new['h'].min():.2f}-{new['h'].max():.1f}")


if __name__ == "__main__":
    main()
