"""Island_A15: Reef_Ideal_A15's reef wrapped round a round island, with N passes.

Usage:
  python3 -I tools/island/make_island_a15.py --passes N [OUTDIR]
      (default OUTDIR: cases/Island_A15_<N>pass)

The round counterpart of Reef_Ideal_A15: the same cross-reef profile (the
10 m channel along the shore, the 2.2 m reef flat, the crest about 1 km
offshore, the fore reef down to 400 m) and the same pass (360 m wide, 10 m
deep), but closing round an island 600 m in radius, with N passes evenly
spaced round the reef (pass 1 centred at north, the others every 360/N
degrees clockwise).

Bathymetry: A15's own 2-D bathymetry (cases/Reef_Ideal_A15/roms_grid_default_1.nc),
read in the frame of its pass: alongshore distance from the pass centre x
and distance from the shore y. A point of the island at radius r and
bearing b gets A15's depth at y = r - 600 m and x = the arc length r * db to
the nearest pass centre (db its angular distance), capped at half of A15's
6061 m period (where A15 is reef again). So the pass keeps its width in
metres at every radius, and the reef between passes is A15's reef.

Grid: closed log-polar O-grid as Circle_Island (square cells; the grid
closes on itself), Lm = 360 columns (1 degree each: SWAN's CIRCLE 72 bins
are 5 columns), Mm rows out to A15's 5 km offshore: cells 10.5 m at the
shore, 28 m on the crest, about 100 m at the outer ring. Waves and physics
as Reef_Ideal_A15 (Hs 1 m, Tp 10 s from the north, ramped over 30 min with
A15's wavebc_north.txt; 0.15 m, 12 h tide on the outer ring; no canopy),
case files from cases/Circle_Island (header CIRCLE_ISLAND, CURVGRID).

Writes into OUTDIR: island_grid.nc, island_init.nc, swan_coord.grd,
swan_bathy.bot, wavebc_ring.txt, swan.in, ocean.in, coupling.in,
circle_island.h, ana_fsobc.h, README.md.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

import netCDF4
import numpy as np
from scipy.interpolate import RegularGridInterpolator

ROOT = Path(__file__).resolve().parents[2]
A15 = ROOT / "cases/Reef_Ideal_A15"
CIRCLE = ROOT / "cases/Circle_Island"

LM, N = 360, 10                        # columns round the island (1 degree each), levels
DTH = 2 * np.pi / LM
R_SHORE = 600.0                        # island radius (m): A15's y = 0 (its land row)
R_B = 590.0                            # radius of rho row 0 (land)
Y_MAX = 5040.0                         # A15's outermost rho row (m from the shore)
PASS_I = 101                           # A15 rho column at the centre of its pass (columns 92-110)
NDIR = 72                              # SWAN direction bins, as A15 (5 degrees = 5 columns)
DT, NDTFAST = 4.0, 10                  # ROMS steps (10.5 m cells at the shore)
THETA_S, THETA_B, HC = 3.0, 2.0, 20.0  # vertical grid as Reef_Ideal_A15
MM = int(np.ceil(np.log((R_SHORE + Y_MAX) / R_B) / DTH))   # rows 0..MM+1 reach past Y_MAX


def a15_depth():
    """Interpolator h(y, x) of A15 in its pass frame (x = 0 at the pass centre)."""
    with netCDF4.Dataset(A15 / "roms_grid_default_1.nc") as d:
        x, y, h = d["x_rho"][0, :], d["y_rho"][:, 0], d["h"][:]
    x = np.asarray(x - x[PASS_I], float)
    period = float(x[-1] - x[0] + (x[1] - x[0]))
    f = RegularGridInterpolator((np.asarray(y, float), x), np.asarray(h, float),
                                bounds_error=False, fill_value=None)
    return f, period, float(np.asarray(y)[1])


def bearings(n):
    return np.arange(n) * 360.0 / n                       # pass centres, degrees from north


def depth(R, B, n):
    """Depth at radius R, bearing B (radians, clockwise from north) with n passes."""
    f, period, y1 = a15_depth()
    centres = np.deg2rad(bearings(n))
    db = np.min(np.abs(np.angle(np.exp(1j * (B[..., None] - centres)))), axis=-1)
    x = np.minimum(R * db, 0.5 * period - 1.0)             # arc length to the nearest pass
    y = np.clip(R - R_SHORE, 0.0, Y_MAX)
    h = f(np.stack([y, x], axis=-1))
    land = (R - R_SHORE) < 0.5 * y1                        # A15's land row is y = 0
    return np.where(land, 10.0, h), land


def periodic(inner, kind):
    """Add the periodic copies to columns 1..Lm (rho/v: 0..Lm+1; u/psi: 0..Lm, 0 = Lm)."""
    if kind in ("rho", "v"):
        return np.concatenate([inner[..., -1:], inner, inner[..., :1]], axis=-1)
    return np.concatenate([inner[..., -1:], inner], axis=-1)


def make_grid(n):
    i = np.arange(1, LM + 1)
    b_rho, b_u = (i - 0.5) * DTH, i * DTH
    r_rho = R_B * np.exp(np.arange(0, MM + 2) * DTH)
    r_v = R_B * np.exp((np.arange(1, MM + 2) - 0.5) * DTH)
    g = {}
    for k, (r, b) in {"rho": (r_rho, b_rho), "u": (r_rho, b_u), "v": (r_v, b_rho), "psi": (r_v, b_u)}.items():
        R, B = np.meshgrid(r, b, indexing="ij")
        g[f"x_{k}"] = periodic(R * np.sin(B), k)
        g[f"y_{k}"] = periodic(R * np.cos(B), k)
    R, B = np.meshgrid(r_rho, b_rho, indexing="ij")
    g["pm"] = periodic(1.0 / (R * DTH), "rho")
    g["pn"] = periodic(1.0 / (R * 2 * np.sinh(DTH / 2)), "rho")
    dm = R * DTH
    dmde = np.zeros_like(R)
    dmde[1:-1] = 0.5 * (dm[2:] - dm[:-2])
    dmde[0], dmde[-1] = dm[1] - dm[0], dm[-1] - dm[-2]
    g["dmde"] = periodic(dmde, "rho")
    g["dndx"] = periodic(0 * R, "rho")
    g["angle"] = periodic(np.angle(np.exp(-1j * B)), "rho")
    g["f"] = periodic(0 * R, "rho")
    h, land = depth(R, B, n)
    g["h"] = periodic(h, "rho")
    m = periodic((~land).astype(float), "rho")
    g["mask_rho"] = m
    g["mask_u"] = m[:, :-1] * m[:, 1:]
    g["mask_v"] = m[:-1, :] * m[1:, :]
    g["mask_psi"] = g["mask_u"][:-1, :] * g["mask_u"][1:, :]
    return g


def write_grid(g, path, n):
    with netCDF4.Dataset(path, "w", format="NETCDF4_CLASSIC") as d:
        d.type = "ROMS GRID file"
        d.title = f"Island_A15: Reef_Ideal_A15's reef round a round island, {n} passes, closed log-polar O-grid"
        d.history = f"tools/island/make_island_a15.py --passes {n}"
        for name, size in (("xi_rho", LM + 2), ("eta_rho", MM + 2), ("xi_u", LM + 1), ("eta_u", MM + 2),
                           ("xi_v", LM + 2), ("eta_v", MM + 1), ("xi_psi", LM + 1), ("eta_psi", MM + 1),
                           ("one", 1)):
            d.createDimension(name, size)
        v = d.createVariable("spherical", "S1", ("one",))
        v[:] = np.array([b"F"])
        r_out, r_in = R_B * np.exp((MM + 1.5) * DTH), R_B * np.exp(0.5 * DTH)
        for name, val in (("xl", 2 * np.pi * r_out), ("el", r_out - r_in)):
            v = d.createVariable(name, "f8", ("one",))
            v.units = "meter"
            v[:] = val
        dims = {"rho": ("eta_rho", "xi_rho"), "u": ("eta_u", "xi_u"), "v": ("eta_v", "xi_v"),
                "psi": ("eta_psi", "xi_psi")}
        units = {"pm": "meter-1", "pn": "meter-1", "dmde": "meter", "dndx": "meter",
                 "angle": "radians", "f": "second-1", "h": "meter"}
        for name, a in g.items():
            kind = name.split("_")[-1] if name.startswith(("x_", "y_", "mask_")) else "rho"
            v = d.createVariable(name, "f8", dims[kind], zlib=True)
            if name in units:
                v.units = units[name]
            elif name.startswith(("x_", "y_")):
                v.units = "meter"
            v[:] = a


def write_swan_grids(g, out):
    cols = slice(1, LM + 2)                         # ROMS columns 1..Lm+1 (Lm+1 = 1)
    x, y, h, m = g["x_rho"], g["y_rho"], g["h"], g["mask_rho"]
    with open(out / "swan_coord.grd", "w") as f:
        for a in (x[:, cols], y[:, cols]):
            for row in a:
                f.write(" ".join(f"{v:.4f}" for v in row) + "\n")
    with open(out / "swan_bathy.bot", "w") as f:
        for row in np.where(m[:, cols] > 0.5, h[:, cols], 9999.0):
            f.write(" ".join(f"{v:.4f}" for v in row) + "\n")


def stretching4(s):
    c = (1 - np.cosh(THETA_S * s)) / (np.cosh(THETA_S) - 1)
    return (np.exp(THETA_B * c) - 1) / (1 - np.exp(-THETA_B))


def write_init(path, n):
    sc_w = np.linspace(-1, 0, N + 1)
    sc_r = (np.arange(1, N + 1) - N - 0.5) / N
    Lp, Mp = LM + 2, MM + 2
    with netCDF4.Dataset(path, "w", format="NETCDF4_CLASSIC") as d:
        d.type = "ROMS initial file"
        d.title = "Island_A15: rest, uniform T/S, bed properties as Reef_Ideal_A15"
        d.history = f"tools/island/make_island_a15.py --passes {n}"
        for name, size in (("xi_rho", Lp), ("eta_rho", Mp), ("xi_u", Lp - 1), ("eta_u", Mp),
                           ("xi_v", Lp), ("eta_v", Mp - 1), ("s_rho", N), ("s_w", N + 1),
                           ("ocean_time", 1)):
            d.createDimension(name, size)

        def var(name, dims, value, units=None, dtype="f8"):
            v = d.createVariable(name, dtype, dims, zlib=True)
            if units:
                v.units = units
            v[:] = value
        var("spherical", (), 0, dtype="i4")
        var("Vtransform", (), 2, dtype="i4")
        var("Vstretching", (), 4, dtype="i4")
        var("theta_s", (), THETA_S)
        var("theta_b", (), THETA_B)
        var("Tcline", (), HC, "meter")
        var("hc", (), HC, "meter")
        var("s_rho", ("s_rho",), sc_r)
        var("s_w", ("s_w",), sc_w)
        var("Cs_r", ("s_rho",), stretching4(sc_r))
        var("Cs_w", ("s_w",), stretching4(sc_w))
        var("ocean_time", ("ocean_time",), 0.0, "seconds since 2000-01-01 00:00:00")
        t, r2, u2, v2 = ("ocean_time",), ("eta_rho", "xi_rho"), ("eta_u", "xi_u"), ("eta_v", "xi_v")
        var("zeta", t + r2, 0.0, "meter")
        var("ubar", t + u2, 0.0, "meter second-1")
        var("vbar", t + v2, 0.0, "meter second-1")
        var("u", t + ("s_rho",) + u2, 0.0, "meter second-1")
        var("v", t + ("s_rho",) + v2, 0.0, "meter second-1")
        var("temp", t + ("s_rho",) + r2, 27.0, "Celsius")
        var("salt", t + ("s_rho",) + r2, 36.0, "1")
        var("grain_diameter", t + r2, 0.12, "meter")
        var("grain_density", t + r2, 2650.0, "kilogram meter-3")
        var("settling_vel", t + r2, 0.15, "meter second-1")
        var("erosion_stress", t + r2, 0.2, "meter2 second-2")


def sub1(text, pattern, repl, what):
    new, k = re.subn(pattern, repl, text, flags=re.M)
    if k != 1:
        sys.exit(f"{what}: {pattern!r} matched {k} times")
    return new


def write_swan_in(out, n):
    s = (CIRCLE / "swan.in").read_text()
    s = sub1(s, r"^ 'Circle_Island'$", " 'Island_A15'", "swan.in")
    s = sub1(s, r"^ 'Round island.*'$", f" 'Reef_Ideal_A15 round an island, {n} passes'", "swan.in")
    s = sub1(s, r"^ 'cases/Circle_Island/make_case.py'$", f" 'tools/island/make_island_a15.py --passes {n}'", "swan.in")
    for a, b in ((r"CURVILINEAR 216 81 ", f"CURVILINEAR {LM} {MM + 1} "),
                 (r"CURVILINEAR 0 0 216 81 ", f"CURVILINEAR 0 0 {LM} {MM + 1} ")):
        s = re.sub(a, b, s)
    s = re.sub(r"(ROMS column k \(k = 1\.\.)216(\), rows = ROMS rows 0\.\.)81", rf"\g<1>{LM}\g<2>{MM + 1}", s)
    s = sub1(s, r"CIRCLE 36 0\.04 1\.0 20", f"CIRCLE {NDIR} 0.04 1.0 20", "swan.in")
    s = sub1(s, r"\(row 81\)", f"(row {MM + 1})", "swan.in")
    # waves on the outer ring from A15's time series (ramp 0.125 -> 1 m over 30 min);
    # Circle_Island's inactive "$INWARD" alternative is dropped
    keep = []
    for l in s.splitlines(keepends=True):
        if l.startswith("$INWARD") or l.startswith("$ Alternative: waves aimed") or \
           l.startswith("$ same all around the island") or l.startswith("$ the BOUNDSPEC line above"):
            continue
        if l.startswith("BOUND SHAPESPEC"):
            keep.append("BOUND SHAPESPEC JONSWAP 3.3 PEAK DSPR DEGREES\n")
            continue
        if l.startswith("BOUNDSPEC SEGMENT IJ"):
            keep.append(f"BOUNDSPEC SEGMENT IJ 0 {MM + 1} {LM - 1} {MM + 1} CONSTANT FILE 'wavebc_ring.txt' 1\n")
            continue
        keep.append(l)
    s = "".join(keep)
    s = sub1(s, r"^COMPUTE NONSTATIONARY 20000101\.000000 60 SEC .*$",
             "COMPUTE NONSTATIONARY 20000101.000000 120 SEC 20000102.000000", "swan.in")
    if re.search(r"\b216\b|\b81\b", s):
        sys.exit("swan.in: Circle_Island dimensions left")
    (out / "swan.in").write_text(s)
    shutil.copy(A15 / "wavebc_north.txt", out / "wavebc_ring.txt")


def write_ocean_in(out, n):
    o = (CIRCLE / "ocean.in").read_text()
    for pat, rep in ((r"^(\s*Lm ==) 216", rf"\1 {LM}"), (r"^(\s*Mm ==) 80", rf"\1 {MM}"),
                     (r"^(\s*NtileI ==) 6", r"\1 10"), (r"^(\s*NTIMES ==) 900", rf"\1 {int(24 * 3600 / DT)}"),
                     (r"^(\s*DT ==) 4\.0d0", rf"\g<1> {DT:.1f}d0"), (r"^(\s*NDTFAST ==) 10", rf"\1 {NDTFAST}"),
                     (r"^(\s*GRDNAME ==) circle_grid\.nc", r"\1 island_grid.nc"),
                     (r"^(\s*ININAME ==) circle_init\.nc", r"\1 island_init.nc")):
        o = sub1(o, pat, rep, "ocean.in")
    every = int(3600 / DT)
    for k in ("NRST", "NHIS", "NAVG", "NDIA"):
        o = sub1(o, rf"^(\s*{k} ==) 150", rf"\1 {every}", "ocean.in")
    o = f"! Island_A15 ({n} passes): tools/island/make_island_a15.py from cases/Circle_Island/ocean.in\n" + o
    (out / "ocean.in").write_text(o)
    c = (CIRCLE / "coupling.in").read_text()
    c = sub1(c, r"^(\s*NnodesWAV =)\s+2 ", r"\1  6 ", "coupling.in")
    c = sub1(c, r"^(\s*NnodesOCN =)\s+6 ", r"\1 10 ", "coupling.in")
    (out / "coupling.in").write_text(c)
    for f in ("circle_island.h", "ana_fsobc.h"):
        shutil.copy(CIRCLE / f, out / f)


def courant(g):
    wet = g["mask_rho"] > 0
    c = np.sqrt(9.81 * g["h"]) * (DT / NDTFAST) * np.sqrt(g["pm"] ** 2 + g["pn"] ** 2)
    return float(c[wet].max())


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--passes", type=int, required=True)
    ap.add_argument("outdir", nargs="?", type=Path)
    a = ap.parse_args()
    n = a.passes
    if n < 1 or LM % n:
        sys.exit(f"--passes must divide {LM}")
    out = a.outdir or ROOT / f"cases/Island_A15_{n}pass"
    out.mkdir(parents=True, exist_ok=True)
    g = make_grid(n)
    for v in g.values():
        if v.shape[1] == LM + 2:
            assert np.array_equal(v[:, 0], v[:, LM]) and np.array_equal(v[:, LM + 1], v[:, 1])
    write_grid(g, out / "island_grid.nc", n)
    write_swan_grids(g, out)
    write_init(out / "island_init.nc", n)
    write_swan_in(out, n)
    write_ocean_in(out, n)
    r = R_B * np.exp(np.arange(MM + 2) * DTH)
    h = g["h"][:, 1:LM + 1]
    wet = g["mask_rho"][:, 1:LM + 1] > 0
    crest = np.where(wet, h, np.inf).min()
    summary = (f"Island_A15, {n} passes (at {', '.join(f'{b:g}' for b in bearings(n))} deg): "
               f"Lm {LM}, Mm {MM}; radius {R_SHORE:.0f}-{r[-1]:.0f} m; cells {r[1] * DTH:.1f}-"
               f"{r[-1] * DTH:.1f} m; depth {crest:.2f}-{h[wet].max():.0f} m; barotropic Courant "
               f"{courant(g):.2f} at DT {DT:g} s, NDTFAST {NDTFAST}")
    (out / "README.md").write_text(
        f"# Island_A15_{n}pass\n\nGenerated by `tools/island/make_island_a15.py --passes {n}`; "
        f"see that script's docstring and docs/Island_A15.md. Do not edit by hand: change the "
        f"script and regenerate.\n\n{summary}\n\nBuild: `build.sh --case cases/Island_A15_{n}pass "
        f"--app CIRCLE_ISLAND`; run with 10 ROMS (10 x 1 tiles) + 6 SWAN processes.\n")
    print(summary)


if __name__ == "__main__":
    main()
