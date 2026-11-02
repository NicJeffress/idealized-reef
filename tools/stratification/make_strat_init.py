"""Write a constant stratification (constant N^2) into a ROMS initial file.

Usage:
  python3 -I tools/stratification/make_strat_init.py N2 -o OUT.nc
      [--case cases/Reef_Ideal_A15_veg_strat] [--base INIT.nc]
      [--t-surface 28] [--t-min 2] [--salt 35] [--mixed-layer H]

N2 is the buoyancy frequency squared (s^-2). Reef_Ideal_A15 uses ROMS's
linear equation of state (NONLIN_EOS is not defined):
    rho = R0 (1 - Tcoef (T - T0) + Scoef (S - S0)),
so N^2 = -(g/rho0) drho/dz = g (R0/rho0) Tcoef dT/dz, and a constant N^2
is a linear temperature profile; salinity stays uniform. R0, TCOEF and
RHO0 are read from the case's ocean.in. Temperature is T_surface + dT/dz z
at the rest-state depths of the rho levels (zeta = 0, the case's
Vtransform/Vstretching from the initial file), 28 C at the surface by
default; if that would put the deepest point below --t-min, the whole
profile is shifted up (the equation of state is linear, so only dT/dz
matters; temperatures stay positive for MPDATA advection).
--mixed-layer H: uniform T_surface down to H m, the constant N^2 below
(still horizontally uniform, so a true rest state).

--base: the initial file to start from (default: the case's initial
file, ININAME in its ocean.in), e.g. one written by tools/vegetation/make_veg_init.py, so
vegetation patterns and stratification combine. Everything except temp
and salt is copied unchanged.

Also prints the first-mode internal wave speed c = N H / pi at the
deepest point and its Courant number c DT / dx_min with the case's DT:
the baroclinic step is explicit, so expect trouble near or above 1.
"""
import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import netCDF4
import numpy as np

G = 9.81                      # ROMS g (mod_scalars)


def ocean_in_value(text, key):
    m = re.search(rf"^\s*{key}\s*==?\s*([-+0-9.dDeE]+)", text, re.M)
    if not m:
        sys.exit(f"ocean.in: {key} not found")
    return float(m.group(1).lower().replace("d", "e"))


def ocean_in_name(text, key):
    """A file name from ocean.in (e.g. GRDNAME, ININAME)."""
    m = re.search(rf"^\s*{key}\s*==?\s*(\S+)", text, re.M)
    if not m:
        raise SystemExit(f"ocean.in: {key} not found")
    return m.group(1)


def z_rho(base, h):
    """Rest-state depths (m, negative) of the rho levels, Vtransform 2."""
    with netCDF4.Dataset(base) as d:
        vt = int(d["Vtransform"][:].ravel()[0])
        hc = float(d["hc"][:].ravel()[0])
        s = d["sc_r" if "sc_r" in d.variables else "s_rho"][:].astype(float)
        cs = d["Cs_r"][:].astype(float)
    if vt != 2:
        sys.exit(f"{base}: Vtransform {vt}; only 2 is implemented")
    z0 = (hc * s[:, None, None] + h[None] * cs[:, None, None]) / (hc + h[None])
    return h[None] * z0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("n2", type=float, help="N^2 (s^-2), >= 0")
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--case", type=Path,
                    default=Path(__file__).resolve().parents[2] / "cases/Reef_Ideal_A15_veg_strat")
    ap.add_argument("--base", type=Path, help="initial file to start from (default: the case's)")
    ap.add_argument("--t-surface", type=float, default=28.0)
    ap.add_argument("--t-min", type=float, default=2.0)
    ap.add_argument("--salt", type=float, default=35.0)
    ap.add_argument("--mixed-layer", type=float, default=0.0, metavar="H",
                    help="surface mixed layer depth (m): uniform T down to H, constant N^2 below")
    a = ap.parse_args()
    if a.n2 < 0:
        sys.exit("N2 must be >= 0 (a stable stratification)")
    if a.mixed_layer < 0:
        sys.exit("--mixed-layer must be >= 0")
    text = (a.case / "ocean.in").read_text()
    base = a.base or a.case / ocean_in_name(text, "ININAME")
    header = a.case / (ocean_in_name(text, "MyAppCPP").lower() + ".h")
    if re.search(r"^#\s*define\s+NONLIN_EOS", header.read_text(), re.M):
        sys.exit("the case defines NONLIN_EOS: this tool assumes the linear equation of state")
    r0, tcoef, rho0 = (ocean_in_value(text, k) for k in ("R0", "TCOEF", "RHO0"))
    dt = ocean_in_value(text, "DT")
    with netCDF4.Dataset(a.case / ocean_in_name(text, "GRDNAME")) as g:
        h = g["h"][:].astype(float)
        mask = g["mask_rho"][:] > 0.5
        dxmin = float(min((1 / g["pm"][:])[mask].min(), (1 / g["pn"][:])[mask].min()))

    dtdz = a.n2 * rho0 / (G * r0 * tcoef)          # C per m
    z = z_rho(base, h)
    temp = a.t_surface + dtdz * np.minimum(z + a.mixed_layer, 0.0)
    shift = max(0.0, a.t_min - float(temp[:, mask].min()))
    temp += shift
    hmax = float(h[mask].max())
    c1 = np.sqrt(a.n2) * hmax / np.pi

    shutil.copy(base, a.out)
    with netCDF4.Dataset(a.out, "r+") as d:
        if d["temp"].shape[1:] != temp.shape:
            sys.exit(f"{base}: temp has shape {d['temp'].shape}, expected (time, {temp.shape})")
        d["temp"][:] = np.broadcast_to(temp, d["temp"].shape)
        d["salt"][:] = a.salt
        d.stratification = json.dumps({"N2_s-2": a.n2, "dTdz_C_per_m": dtdz, "salt": a.salt,
                                       "mixed_layer_m": a.mixed_layer,
                                       "T_surface": a.t_surface + shift, "R0": r0, "Tcoef": tcoef,
                                       "rho0": rho0})
        d.stratification_history = (f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ} "
                                    "tools/stratification/make_strat_init.py (linear EOS, constant N^2"
                                    + (f" below a {a.mixed_layer:g} m mixed layer)" if a.mixed_layer else ")"))
    print(f"{a.out}: N^2 {a.n2:g} s^-2 (N {np.sqrt(a.n2):.4g} s^-1), dT/dz {dtdz:.4g} C/m, "
          f"S {a.salt:g}; T {temp[:, mask].min():.2f}..{temp[:, mask].max():.2f} C over 0..{hmax:.0f} m"
          + (f" (shifted up {shift:.2f} C to keep T >= {a.t_min:g})" if shift > 0 else "")
          + (f"; mixed layer {a.mixed_layer:g} m" if a.mixed_layer else ""))
    print(f"  first-mode internal wave speed N H / pi = {c1:.2f} m/s at {hmax:.0f} m; "
          f"Courant number c DT / dx_min = {c1 * dt / dxmin:.2f} (DT {dt:g} s, dx_min {dxmin:.1f} m)")


if __name__ == "__main__":
    main()
