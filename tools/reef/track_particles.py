#!/usr/bin/env python3
"""Seed particles on a regular grid and track them with ROMSPath on this machine.

Usage: ~/venv/bin/python -I tools/reef/track_particles.py HIS.nc OUT_DIR --template ROMSPath.data
           [--seeding lagoon|domain] [--days 1] [--dt 900] [--idt 10] [--iprint 900]
           [--chunks 4] [--image coawst-romspath:latest] [--set KEY=VALUE ...]

HIS.nc: ROMS history file(s) merged into one (tools/merge_segments.py; pass --grid
to repair its grid fields), with u, v,
w, zeta, AKs, salt, temp, u_stokes, v_stokes and the grid; the particles are
released at its first record. --dt must equal its record interval.

Seeding (positions in m, the grid's x and y; mid-depth z = -h/2 below the
surface at rest, wet cells deeper than 0.3 m only):
  lagoon   regular grid 40 m alongshore x 25 m across, y 100-925 m from shore
           (lagoon and back reef, up to just inside the crest; 50 m is shoreward of
           the first interior row and ROMSPath drops it), |x| <= 1.5 km
           (the central 3 km around the pass): about 2,700 particles
  backreef regular grid 40 m alongshore x 25 m across over the whole back reef,
           y 500-925 m from shore, across the full alongshore period (edge to
           edge): about 2,700 particles
  domain   regular 100 m grid over the whole domain (like a dye-free flow
           visualization), about 3,000 particles

ROMSPath (the coawst-cloud image, built from the fork NicJeffress/ROMSPath with
periodic boundaries and -DSTOKES) runs with --template's namelist and these keys
replaced: numpar, days, dt, idt, iprint, prefix and stokesprefix (the history
file), multifile .FALSE., parfile, outpath, NCOutFile, seed (chunk number + 1),
PeriodicBoundary_X .TRUE., plus --set. Velocities are the Eulerian ones plus the
Stokes drift; vertical turbulence from AKs and horizontal turbulence from
the template (VTurbOn, HTurbOn, ConstantHTurb) unless --set changes them.
The particles are split into --chunks runs in parallel (one core each).

Writes OUT_DIR/seeds.csv, OUT_DIR/chunk_NN/ (ROMSPath.data, log, track.nc) and
OUT_DIR/run.json (settings, so the figure script can say what it shows).
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import netCDF4
import numpy as np


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


def set_keys(s, pairs):
    """Replace each key=value in the namelist text s (as moorea-runs make_romspath_data.py)."""
    s = s.replace("\r", "")
    for p in pairs:
        k, v = p.split("=", 1)
        s, n = re.subn(rf"^(\s*{re.escape(k)}\s*=\s*)(?:'[^']*'|\S+)", lambda m: m.group(1) + v, s, flags=re.M)
        if n != 1:
            raise SystemExit(f"{k}: found {n} times in the template")
    return s


def seeds(his, how):
    g = netCDF4.Dataset(his)
    x = periodic_x(g["x_rho"][0, :], g["pm"][0, :])
    y = g["y_rho"][:, 0].astype(float)
    h = g["h"][:].astype(float)
    m = g["mask_rho"][:].astype(float)
    L = len(x) - 2
    x0, x1 = x[1], x[L]                              # interior, one period
    if how == "lagoon":
        xs = np.arange(-1500, 1500 + 1, 40.0)
        ys = np.arange(100, 925 + 1, 25.0)
    elif how == "backreef":
        xs = np.arange(np.ceil(x0 / 40) * 40, x1, 40.0)
        ys = np.arange(500, 925 + 1, 25.0)
    else:
        xs = np.arange(np.ceil(x0 / 100) * 100, x1, 100.0)
        ys = np.arange(100, y[-2], 100.0)
    X, Y = np.meshgrid(xs, ys)
    X, Y = X.ravel(), Y.ravel()
    i = np.clip(np.searchsorted(x, X), 1, L)
    j = np.clip(np.searchsorted(y, Y), 1, len(y) - 2)
    hp, mp = h[j, i], m[j, i]
    ok = (mp > 0) & (hp > 0.3)
    return np.c_[X[ok], Y[ok], -0.5 * hp[ok], np.zeros(ok.sum())]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("his", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--template", type=Path, required=True)
    ap.add_argument("--seeding", choices=("lagoon", "backreef", "domain"), default="lagoon")
    ap.add_argument("--days", type=float, default=1.0)
    ap.add_argument("--dt", type=float, default=900)
    ap.add_argument("--idt", type=float, default=10)
    ap.add_argument("--iprint", type=float, default=900)
    ap.add_argument("--chunks", type=int, default=4)
    ap.add_argument("--image", default="coawst-romspath:latest")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--grid", type=Path, help="ROMS grid file: its static fields (x_*, y_*, mask_*) are "
                    "written into HIS.nc first (newer images write wrapped ghost x columns)")
    a = ap.parse_args()
    if a.grid:
        with netCDF4.Dataset(a.grid) as g, netCDF4.Dataset(a.his, "a") as h:
            fixed = []
            for v in ("x_rho", "x_u", "x_v", "x_psi", "y_rho", "y_u", "y_v", "y_psi",
                      "mask_rho", "mask_u", "mask_v", "mask_psi"):
                if v in g.variables and v in h.variables and h[v].shape == g[v].shape:
                    if not np.array_equal(np.ma.filled(h[v][:], 0), np.ma.filled(g[v][:], 0)):
                        h[v][:] = g[v][:]
                        fixed.append(v)
            print(f"grid fields replaced from {a.grid.name}: {', '.join(fixed) or 'none'}")

    t = netCDF4.Dataset(a.his)["ocean_time"][:]
    if len(t) > 1 and abs((t[1] - t[0]) - a.dt) > 1e-3:
        raise SystemExit(f"--dt {a.dt} but the history interval is {t[1] - t[0]} s")
    if (t[-1] - t[0]) < a.days * 86400 - 1e-3:
        raise SystemExit(f"history covers {(t[-1] - t[0]) / 3600:.2f} h, less than --days")
    a.out.mkdir(parents=True, exist_ok=True)
    S = seeds(a.his, a.seeding)
    np.savetxt(a.out / "seeds.csv", S, delimiter=",", fmt="%.3f")
    tmpl = a.template.read_text(encoding="latin-1")
    his = a.his.resolve()
    parts = np.array_split(np.arange(len(S)), a.chunks)
    procs = []
    for c, idx in enumerate(parts):
        d = a.out / f"chunk_{c:02d}"
        (d / "out").mkdir(parents=True, exist_ok=True)
        np.savetxt(d / "seeds.csv", S[idx], delimiter=",", fmt="%.3f")
        keys = [f"numpar={len(idx)}", f"days={a.days:.12g}", f"dt={a.dt:.12g}", f"idt={a.idt:.12g}",
                f"iprint={a.iprint:.12g}", f"prefix='/hydro/{his.name}'", f"stokesprefix='/hydro/{his.name}'",
                "multifile=.FALSE.", "parfile='seeds.csv'", "outpath='out/'", "NCOutFile='track'",
                f"seed={c + 1}", "PeriodicBoundary_X=.TRUE.", *a.set]
        (d / "ROMSPath.data").write_text(set_keys(tmpl, keys))
        cmd = ["docker", "run", "--rm", "-u", f"{os.getuid()}:{os.getgid()}", "-v", f"{d.resolve()}:/run",
               "-v", f"{his.parent}:/hydro:ro", "-w", "/run", a.image, "ROMSPath.exe", "ROMSPath.data"]
        procs.append(subprocess.Popen(cmd, stdout=open(d / "log", "w"), stderr=subprocess.STDOUT))
    rc = [p.wait() for p in procs]
    (a.out / "run.json").write_text(json.dumps({
        "his": str(a.his), "seeding": a.seeding, "particles": len(S), "days": a.days, "dt": a.dt,
        "idt": a.idt, "iprint": a.iprint, "chunks": a.chunks, "image": a.image, "set": a.set,
        "template": str(a.template), "exit_codes": rc}, indent=1))
    print(f"{len(S)} particles ({a.seeding}), {a.chunks} chunks, exit codes {rc}")
    sys.exit(max(rc))


if __name__ == "__main__":
    main()
