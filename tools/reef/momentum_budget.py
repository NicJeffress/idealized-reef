#!/usr/bin/env python3
"""Depth-integrated cross-reef momentum budget of an A15 run, by zone.

Usage: momentum_budget.py RUNDIR [--t0 12] [--t1 24] [--crest-y 965]

RUNDIR holds ocean_dia.nc and ocean_his.nc. Needs an image with coawst-cloud
roms-diag-implicit-drag and Dout(M2fveg) in vegetation.in; a bare-reef build has no
vbar_fveg, which then counts as zero. Terms are vbar_* (m/s2) times the local depth,
hour by hour (depth from the nearest history record), averaged over the reef columns
(depth at --crest-y below 0.8 m, so the pass is left out) and integrated across the zone,
in m3/s2 per metre alongshore. y runs offshore, so a lagoon-ward force is negative.
Zones go by distance from shore, so the script works on any A15 grid.
"""
import argparse

import netCDF4
import numpy as np

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("rundir")
ap.add_argument("--t0", type=float, default=12.0)
ap.add_argument("--t1", type=float, default=24.0)
ap.add_argument("--crest-y", type=float, default=965.0)
args = ap.parse_args()

d = netCDF4.Dataset(f"{args.rundir}/ocean_dia.nc")
h = netCDF4.Dataset(f"{args.rundir}/ocean_his.nc")
t = d["ocean_time"][:] / 3600
recs = np.where((t >= args.t0) & (t <= args.t1))[0]
H = np.ma.filled(h["h"][:], np.nan)
y_rho = np.ma.filled(h["y_rho"][:], np.nan)[:, 0]
yv = np.ma.filled(h["y_v"][:], np.nan)[:, 0]
reef = np.where(H[np.argmin(np.abs(y_rho - args.crest_y)), :] < 0.8)[0]
t_his = h["ocean_time"][:] / 3600
zeta = np.ma.filled(h["zeta"][:], np.nan)
dy = np.gradient(yv)

TERMS = ["accel", "prsgrd", "wbrk", "wrol", "bstm", "bstr", "fveg", "sstr", "hadv", "cor", "hvisc",
         "hjvf", "kvrf", "fsco", "zeta", "zetaw", "zqsp", "zbeh"]
F = {}
for name in TERMS:
    var = "vbar_" + name
    if var not in d.variables:
        F[name] = np.zeros_like(yv)
        continue
    total = 0
    for r in recs:
        D = H + zeta[np.argmin(np.abs(t_his - t[r]))]
        total = total + np.nan_to_num(np.ma.filled(d[var][r], np.nan)) * 0.5 * (D[1:, :] + D[:-1, :])
    F[name] = np.nan_to_num(np.mean((total / len(recs))[:, reef], axis=1))


def integral(name, a, b):
    return float(np.sum((F[name] * dy)[(yv >= a) & (yv < b)]))


ZONES = [("lagoon 0-920", 0, 920), ("back of crest 920-1000", 920, 1000), ("crest front 1000-1050", 1000, 1050),
         ("top fore reef 1050-1150", 1050, 1150), ("slope 1150-1500", 1150, 1500), ("all 0-1500", 0, 1500)]
print(f"{args.rundir}: {len(recs)} records, hours {args.t0:g}-{args.t1:g}, {len(reef)} of {H.shape[1]} columns")
print(f"{'zone':25s}{'brk+rol':>9s}{'stream':>9s}{'press':>9s}{'bed':>9s}{'canopy':>9s}{'adv+VF':>9s}{'accel':>9s}{'resid':>10s}")
for z, a, b in ZONES:
    breaking = integral("wbrk", a, b) + integral("wrol", a, b)
    stream = integral("bstm", a, b)
    press = integral("prsgrd", a, b)
    bed = integral("bstr", a, b)
    canopy = integral("fveg", a, b)
    adv = sum(integral(n, a, b) for n in ("hadv", "hjvf", "kvrf"))
    other = sum(integral(n, a, b) for n in ("hvisc", "cor", "fsco", "sstr"))
    accel = integral("accel", a, b)
    print(f"{z:25s}{breaking:9.4f}{stream:9.4f}{press:9.4f}{bed:9.4f}{canopy:9.4f}{adv:9.4f}{accel:9.4f}"
          f"{breaking + stream + press + bed + canopy + adv + other - accel:10.1e}")
print("\nPressure parts")
print(f"{'zone':25s}{'zeta':>9s}{'zetaw':>9s}{'zqsp':>9s}{'zbeh':>9s}")
for z, a, b in ZONES:
    print(f"{z:25s}" + "".join(f"{integral(n, a, b):9.4f}" for n in ("zeta", "zetaw", "zqsp", "zbeh")))
