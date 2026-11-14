#!/usr/bin/env python3
"""Where the pass jet goes when it can bend (runs with Coriolis), hour by hour.

Usage: ~/venv/bin/python -I tools/reef/jet_bend.py HIS.nc [HIS.nc ...] --out DIR [--label NAME]
           [--speed 0.05] [--hours 0 96]

Reads ROMS history records (ubar, vbar, ubar_stokes, vbar_stokes, zeta; several
segment files are read in time order, repeated times skipped) and, for every
record, follows the jet from the pass:

- Depth-mean Lagrangian speed s = |(ubar + ubar_stokes, vbar + vbar_stokes)| at
  rho points, alongshore coordinates unwrapped across the periodic seam.
- The jet is the connected region of s > --speed (default 0.05 m/s), more than
  1.3 km from shore (the lagoon's flow toward the pass and the onshore flow over
  the upper fore reef, which runs the whole length of the reef, are excluded),
  that contains the pass mouth (the fastest point 1.30-1.45 km from shore), grown
  through the periodic seam.
- Head: the point of that region farthest from the pass mouth (path length is
  not used: straight-line distance). Reported as x (alongshore, unwrapped; +x
  east, so a southern-hemisphere jet should go to -x) and y (from shore), with
  the bearing from the mouth (0 = straight offshore, negative = turned to -x).
- Touches the north boundary: the region reaches within 3 cells of the last row.
- Wraps: the region spans more than the 6 km period alongshore.

Writes DIR/jet_bend_LABEL.csv (hour, head x, y, bearing, touches, wraps, max
speed) and prints a table every 3 h. Positions in km.
"""
import argparse
import csv
from pathlib import Path

import netCDF4
import numpy as np
from scipy import ndimage


def periodic_x(x, pm_row):
    """x_rho along a row with the two ghost columns rebuilt from the cell widths. Images
    from coawst-cloud ca5316d + roms-stokes-interval on write them already wrapped
    (x[0] = x[L], x[L+1] = x[1]), which breaks anything that assumes x increases."""
    x = np.array(x, float).copy()
    dx = 1.0 / np.array(pm_row, float)
    L = len(x) - 2
    x[0] = x[1] - 0.5 * (dx[0] + dx[1])
    x[L + 1] = x[L] + 0.5 * (dx[L] + dx[L + 1])
    return x


def rho(a, axis):
    """u or v point field to interior rho points (periodic in x for u)."""
    if axis == 1:  # u: (eta, xi-1) -> (eta, xi)
        b = np.concatenate([a[:, -1:], a, a[:, :1]], axis=1)
        return 0.5 * (b[:, 1:] + b[:, :-1])[:, : a.shape[1] + 1]
    b = np.concatenate([a[:1], a, a[-1:]], axis=0)  # v: (eta-1, xi) -> (eta, xi)
    return 0.5 * (b[1:] + b[:-1])[: a.shape[0] + 1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("his", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--label", default="run")
    ap.add_argument("--speed", type=float, default=0.05)
    ap.add_argument("--hours", type=float, nargs=2, default=(0, 1e9))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    g = netCDF4.Dataset(a.his[0])
    x = periodic_x(g["x_rho"][0, :], g["pm"][0, :]) / 1e3
    y = g["y_rho"][:, 0] / 1e3
    L = len(x) - 2                                   # ROMS period in points (Lm)
    period = x[L + 1] - x[1]
    t0 = None
    rows, seen = [], set()
    for path in a.his:
        d = netCDF4.Dataset(path)
        d.set_auto_mask(False)
        tt = d["ocean_time"][:]
        for k, tk in enumerate(tt):
            if t0 is None:
                t0 = tk
            hr = round((tk - t0) / 3600, 4)
            if hr in seen or not (a.hours[0] <= hr <= a.hours[1]):
                continue
            seen.add(hr)
            f = {n: np.array(d[n][k], float) for n in ("ubar", "ubar_stokes", "vbar", "vbar_stokes")}
            for n in f:
                f[n][np.abs(f[n]) > 1e30] = 0.0      # fill values at masked points
            u = rho(f["ubar"] + f["ubar_stokes"], 1)
            v = rho(f["vbar"] + f["vbar_stokes"], 0)
            s = np.hypot(u, v)[:, 1 : L + 1]         # interior columns: one period
            s[y < 1.3] = 0.0                         # seaward of the crest and the fore-reef band of onshore flow only
            xi = x[1 : L + 1]
            # pass mouth: fastest point 1300-1450 m from shore
            band = (y > 1.30) & (y < 1.45)
            jb, ib = np.unravel_index(np.argmax(np.where(band[:, None], s, 0)), s.shape)
            # three copies alongshore so the region can grow through the seam
            s3 = np.concatenate([s, s, s], axis=1)
            x3 = np.concatenate([xi - period, xi, xi + period])
            if s[jb, ib] <= a.speed:
                continue                             # no jet yet
            lab, _ = ndimage.label(s3 > a.speed)
            m = lab == lab[jb, ib + L]
            if not m.any():
                continue
            jj, ii = np.nonzero(m)
            x0, y0 = x3[ib + L], y[jb]
            dist = np.hypot(x3[ii] - x0, y[jj] - y0)
            h = np.argmax(dist)
            hx, hy = x3[ii[h]] - x0, y[jj[h]]
            bearing = np.degrees(np.arctan2(hx, hy - y0))
            touches = jj.max() >= len(y) - 4
            wraps = (x3[ii].max() - x3[ii].min()) > period
            rows.append(dict(hour=hr, head_x_km=round(hx, 3), head_y_km=round(hy, 3),
                             bearing_deg=round(bearing, 1), touches_north=int(touches),
                             wraps=int(wraps), max_speed=round(float(s[m[:, L:2 * L]].max()), 3),
                             mouth_x_km=round(x0, 3)))
        d.close()
    rows.sort(key=lambda r: r["hour"])
    out = a.out / f"jet_bend_{a.label}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{a.label}: jet = connected s > {a.speed} m/s from the pass mouth; head relative to the mouth")
    print(" hour  head x km  head y km  bearing  north  wraps  max m/s")
    for r in rows:
        if abs(r["hour"] / 3 - round(r["hour"] / 3)) < 1e-6:
            print(f"{r['hour']:5.0f}  {r['head_x_km']:9.2f}  {r['head_y_km']:9.2f}  {r['bearing_deg']:7.1f}"
                  f"  {'yes' if r['touches_north'] else 'no':>5}  {'yes' if r['wraps'] else 'no':>5}  {r['max_speed']:7.2f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
