"""Courant numbers of a ROMS case before running it, and as observed in runs.

Usage:
  python3 -I tools/cfl_check.py [--case cases/Reef_Ideal_A15_veg_strat]
      [--dt S] [--ndtfast N] [--n2 N2 ...] [--init INIT.nc ...] [--logs RUN_DIR ...]

From the case's grid and ocean.in (DT, NDTFAST, R0, TCOEF, RHO0, tide
amplitude USER(1) when NUSER >= 2), for each grid point:
  barotropic  external gravity wave c = sqrt(g (h + tide)), stepped with the
              fast step DT/NDTFAST:  C2D = c (DT/NDTFAST) sqrt(1/dx^2 + 1/dy^2)
  baroclinic  first-mode internal wave c1 = (1/pi) * integral of N dz (WKB;
              N H / pi for a constant N^2), stepped with DT:
              C3D = c1 DT sqrt(1/dx^2 + 1/dy^2)
Prints the largest values and where they occur (row, column, depth, dx).
Limits (A. Shchepetkin, myroms.org forum "CFL condition", 2017): barotropic
about 0.87 for generalized forward-backward stepping, 0.9-something for
LF-AM3 (this build: LF-AM3 by default, AB3-AM4 with the cpp option
STEP2D_FB_AB3_AM4, whose linear limit is 0.890, tools/fb_stability.py;
ROMS prints the same number at startup);
the internal-wave and advective limits add up, so --u U adds an advection
speed to c1 (C3D+adv). In the A15 tests the internal-wave number alone had
to stay below about 0.4-0.5. Also printed: the aspect ratio stratified
depth / dx; above about 1 the hydrostatic model sharpens internal waves
into fronts with large vertical velocities (same post).
--n2: constant N^2 values to evaluate; --init: initial files whose
temperature/salinity profile (linear equation of state) gives N(z) at each
point. --logs: run folders (with coawst.log) whose ROMS step reports give
the largest advective Courant numbers Cu, Cv, Cw seen, and how the run
ended.
"""
import argparse
import re
from pathlib import Path

import netCDF4
import numpy as np

G = 9.81


def ocean_in(text, key, n=1):
    m = re.search(rf"^\s*{key}\s*==?\s*(.+?)(!|$)", text, re.M)
    if not m:
        return None
    vals = [float(v.lower().replace("d", "e")) for v in m.group(1).split()[:n]]
    return vals if n > 1 else vals[0]


def ocean_in_name(text, key):
    """A file name from ocean.in (e.g. GRDNAME, ININAME)."""
    m = re.search(rf"^\s*{key}\s*==?\s*(\S+)", text, re.M)
    if not m:
        raise SystemExit(f"ocean.in: {key} not found")
    return m.group(1)


def main():
    here = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--case", type=Path, default=here / "cases/Reef_Ideal_A15_veg_strat")
    ap.add_argument("--dt", type=float)
    ap.add_argument("--ndtfast", type=int)
    ap.add_argument("--n2", type=float, nargs="*", default=[])
    ap.add_argument("--init", type=Path, nargs="*", default=[])
    ap.add_argument("--logs", type=Path, nargs="*", default=[])
    ap.add_argument("--u", type=float, default=0.0, help="advection speed (m/s) added to c1")
    a = ap.parse_args()

    text = (a.case / "ocean.in").read_text()
    dt = a.dt or ocean_in(text, "DT")
    ndtfast = a.ndtfast or int(ocean_in(text, "NDTFAST"))
    r0, tcoef, rho0 = ocean_in(text, "R0"), ocean_in(text, "TCOEF"), ocean_in(text, "RHO0")
    nuser = ocean_in(text, "NUSER")
    tide = ocean_in(text, "USER", 2)[0] if nuser and nuser >= 2 else 0.15
    with netCDF4.Dataset(a.case / ocean_in_name(text, "GRDNAME")) as g:
        h = g["h"][:].astype(float)
        wet = g["mask_rho"][:] > 0.5
        dx, dy = 1 / g["pm"][:].astype(float), 1 / g["pn"][:].astype(float)
    geom = np.sqrt(1 / dx ** 2 + 1 / dy ** 2)
    print(f"{a.case.name}: DT {dt:g} s, NDTFAST {ndtfast} (fast step {dt / ndtfast:g} s), "
          f"tide amplitude {tide:g} m; dx {dx[wet].min():.0f}-{dx[wet].max():.0f} m, "
          f"dy {dy[wet].min():.0f}-{dy[wet].max():.0f} m, h {h[wet].min():.2f}-{h[wet].max():.0f} m")

    def where(c):
        j, i = np.unravel_index(np.nanargmax(np.where(wet, c, np.nan)), c.shape)
        return f"row {j}, col {i}, h {h[j, i]:.0f} m, dx {dx[j, i]:.0f} m, dy {dy[j, i]:.0f} m"

    c2d = np.sqrt(G * (h + tide)) * (dt / ndtfast) * geom
    print(f"  barotropic Courant number (fast step): max {np.nanmax(c2d[wet]):.2f} at {where(c2d)}")

    rows = []
    for n2 in a.n2:
        c1 = np.sqrt(n2) * h / np.pi
        rows.append((f"N^2 {n2:g}", c1 * dt * geom))
    for f in a.init:
        with netCDF4.Dataset(f) as d:
            T = d["temp"][0].astype(float)
            S = d["salt"][0].astype(float)
            hc = float(d["hc"][:].ravel()[0])
            s_r, cs_r = d["sc_r"][:].astype(float), d["Cs_r"][:].astype(float)
        zr = h[None] * (hc * s_r[:, None, None] + h[None] * cs_r[:, None, None]) / (hc + h[None])
        rho = -r0 * tcoef * T + r0 * ocean_in(text, "SCOEF") * S       # linear EOS, constants dropped
        n2z = -G / rho0 * np.diff(rho, axis=0) / np.diff(zr, axis=0)
        nz = np.sqrt(np.clip(n2z, 0, None))
        c1 = np.sum(nz * np.diff(zr, axis=0), axis=0) / np.pi   # N at w levels x rho spacing
        rows.append((f"{f.name}", c1 * dt * geom))
    for label, c3d in rows:
        line = f"  baroclinic Courant number, {label}: max {np.nanmax(c3d[wet]):.2f} at {where(c3d)}"
        if a.u:
            cadv = c3d + a.u * dt * geom
            line += f"; with {a.u:g} m/s advection {np.nanmax(cadv[wet]):.2f}"
        print(line)
    if rows:
        ar = h / np.minimum(dx, dy)
        print(f"  stratified depth / grid spacing (N^2 over the whole column): up to {np.nanmax(ar[wet]):.0f} "
              f"at {where(ar)}; about 1 or less keeps hydrostatic internal waves smooth")

    for run in a.logs:
        log = run / "coawst.log"
        if not log.exists():
            log = run / "per" / "coawst.log"
        txt = log.read_text(errors="replace")
        rep = re.findall(r"^ +\((\d+),(\d+),(\d+)\) +([-0-9.E+]+) +([-0-9.E+]+) +([-0-9.E+]+) +([-0-9.E+]+)\s*$",
                         txt, re.M)
        blow = re.findall(r"REASON: (.*)", txt)
        steps = re.findall(r"^ +(\d+) \d{4}-\d\d-\d\d (\d\d:\d\d:\d\d)", txt, re.M)
        m = re.search(r"Maximum barotropic Courant Number =\s*([0-9.E+-]+)", txt)
        if not rep:
            print(f"  {run}: no step reports")
            continue
        arr = np.array([[float(x) for x in r[3:]] for r in rep])
        ok = arr[:-3] if blow else arr               # before the last (blowing-up) reports
        ok = ok if len(ok) else arr
        end = f"blew up at {steps[-1][1]} ({blow[0].strip()})" if blow else f"ran to {steps[-1][1]}"
        print(f"  {run.name}: {end}; largest Cu {ok[:, 0].max():.2f}, Cv {ok[:, 1].max():.2f}, "
              f"Cw {ok[:, 2].max():.2f}, speed {ok[:, 3].max():.2f} m/s"
              + (" (before the last 3 reports)" if blow else "")
              + (f"; ROMS's barotropic Courant number {float(m.group(1)):.3f}" if m else ""))


if __name__ == "__main__":
    main()
