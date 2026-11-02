"""Far-field open ocean for the thermal case: a 1-D water column under the
same surface heating, written as ROMS climatology and boundary files.

Usage:
  python3 -I tools/thermal/far_field.py [--case cases/Reef_Ideal_A15_veg_therm]
      [--ocean-in OCEAN.in] [--init INIT.nc] [--hours H] [--kbg 5e-5]
      [--dz 0.5] [--dt 60] [--out-dt 1800] [-o DIR] [--png FIG]

The column is as deep as the deepest grid point (400 m in A15) and starts
from the initial file's temperature and salinity at that point. It uses
the case's own forcing and parameters (its ocean.in, or --ocean-in when a
run changes them, e.g. USER(9)):
  shortwave   USER(6) W/m2 at noon, half sine over USER(8) h centred on
              noon, USER(9) = hour of day at time 0 (as ana_srflux.h),
              absorbed with depth by Paulson & Simpson's two-band law for
              Jerlov type WTYPE (ROMS's lmd_swfrac coefficients); light
              reaching the bed heats the bottom cell (ROMS default)
  non-solar   USER(7) W/m2 at the surface (as ana_stflux.h); with 11 USER
              values (a linear SST feedback; the A15 thermal case has 9
              and a constant flux) it feels the surface temperature: USER(7) - USER(10) (T_top - USER(11)), T_top the
              mean over the thickness of ROMS's top layer at the column
  heat to T   rho0 (RHO0) and Cp = 3985 J/kg/C (ROMS)
  mixing      a constant background diffusivity --kbg (m2/s; GLS's
              resting value offshore in the A15 runs is about 5e-5),
              implicit, plus convective adjustment after every step
              (unstable water mixes at once: temperature never increases
              with depth; salinity stays uniform, linear equation of
              state, so temperature alone sets the stability)
This replaces ROMS's GLS turbulence model in the far field, where there
is no wind and currents are weak: heating stratifies the top metres by
day, cooling convects at night.

Writes into DIR (default: the case directory):
  ocean_clm.nc    temp(temp_time, s_rho, eta_rho, xi_rho) and salt: the
                  initial file's temperature plus the column's change
                  since time 0 averaged over each ROMS cell (between its
                  rest-state w depths): exactly the model's initial state
                  at time 0, and the surface heating added in a
                  heat-conserving way (cell-centre samples of the column
                  differ from the initial file by up to 0.04 C in the
                  thick deep cells); for the interior nudging band, which
                  acts only near the north boundary
  ocean_bndry.nc  temp_north / salt_north at the north boundary row (used
                  by RadNud)
every --out-dt seconds from 0 to the run length (--hours, default NTIMES
x DT from ocean.in) plus one record, so ROMS can interpolate in time.
"""
import argparse
import re
from pathlib import Path

import netCDF4
import numpy as np
from scipy.linalg import solve_banded

CP = 3985.0                                    # ROMS Cp, J/kg/C
JERLOV = {  # ROMS lmd_swfrac: (r1, mu1 m, mu2 m) for WTYPE 1..9
    1: (0.58, 0.35, 23.0), 2: (0.62, 0.6, 20.0), 3: (0.67, 1.0, 17.0), 4: (0.77, 1.5, 14.0),
    5: (0.78, 1.4, 7.9), 6: (0.57, 0.42, 5.13), 7: (0.57, 0.37, 3.54), 8: (0.57, 0.33, 2.34),
    9: (0.55, 0.00468592, 1.51)}


def ocean_in(text, key, n=1):
    m = re.search(rf"^\s*{key}\s*==?\s*(.+?)(!|$)", text, re.M)
    if not m:
        raise SystemExit(f"ocean.in: {key} not found")
    vals = [float(v.lower().replace("d", "e")) for v in m.group(1).split()[:n]]
    return vals if n > 1 else vals[0]


def ocean_in_name(text, key):
    """A file name from ocean.in (e.g. GRDNAME, ININAME)."""
    m = re.search(rf"^\s*{key}\s*==?\s*(\S+)", text, re.M)
    if not m:
        raise SystemExit(f"ocean.in: {key} not found")
    return m.group(1)


def shortwave(t, user):
    """W/m2 entering the water at model time t (s); same as ana_srflux.h."""
    peak, length, hour0 = user[5], user[7], user[8]
    hday = np.mod(hour0 + t / 3600.0, 24.0)
    tday = hday - (12.0 - 0.5 * length)
    return np.where((tday > 0) & (tday < length), peak * np.sin(np.pi * tday / length), 0.0)


def swfrac(depth, wtype):
    """Fraction of the surface shortwave reaching depth (m, positive)."""
    r1, mu1, mu2 = JERLOV[int(wtype)]
    return r1 * np.exp(-depth / mu1) + (1 - r1) * np.exp(-depth / mu2)


def adjust(T):
    """Convective adjustment: the closest profile (equal cell weights)
    whose temperature never increases with depth (index 0 = top), by
    pooling adjacent violators. Mixes unstable stretches completely and
    conserves heat."""
    vals, counts = [], []
    for x in T:
        vals.append(x)
        counts.append(1)
        while len(vals) > 1 and vals[-1] > vals[-2]:      # warmer below: mix
            n = counts[-1] + counts[-2]
            v = (vals[-1] * counts[-1] + vals[-2] * counts[-2]) / n
            vals[-2:], counts[-2:] = [v], [n]
    return np.repeat(vals, counts)


def column(T0, H, dz, dt, hours, out_dt, kbg, rho0, user, wtype, top=None):
    """Integrate the column; returns output times (s) and T (time, cell),
    cell centres depth (m) and the heat budget check. top: thickness (m) of
    ROMS's top layer, over which the surface temperature for the non-solar
    feedback (USER(10:11)) is averaged."""
    nz = int(round(H / dz))
    dz = H / nz
    fb = len(user) >= 11 and user[9] != 0
    ntop = max(1, int(round((top or dz) / dz)))
    zf = np.arange(nz + 1) * dz                                  # face depths, 0 at the surface
    absorbed = swfrac(zf[:-1], wtype) - swfrac(zf[1:], wtype)    # per cell
    absorbed[-1] += swfrac(zf[-1], wtype)                        # light at the bed heats the bottom cell
    # implicit diffusion, banded matrix (no flux through top and bottom)
    a = kbg * dt / dz ** 2
    ab = np.zeros((3, nz))
    ab[0, 1:] = -a
    ab[1, :] = 1 + 2 * a
    ab[1, 0] = ab[1, -1] = 1 + a
    ab[2, :-1] = -a
    T = T0.copy()
    nsteps = int(round(hours * 3600 / dt))
    every = int(round(out_dt / dt))
    times, out = [0.0], [T.copy()]
    heat_in = 0.0                                                # J/m2 from the surface
    for n in range(1, nsteps + 1 + every):
        t_mid = (n - 0.5) * dt
        sw = float(shortwave(t_mid, user))
        q = sw * absorbed
        qns = user[6] - (user[9] * (T[:ntop].mean() - user[10]) if fb else 0.0)
        q[0] += qns
        heat_in += (sw + qns) * dt
        T = solve_banded((1, 1), ab, T + q * dt / (rho0 * CP * dz))
        if np.any(np.diff(T) > 0):                               # warmer below somewhere
            T = adjust(T)
        if n % every == 0:
            times.append(n * dt)
            out.append(T.copy())
    zc = 0.5 * (zf[:-1] + zf[1:])
    budget = (rho0 * CP * dz * (out[-1].sum() - out[0].sum()), heat_in)
    return np.array(times), np.array(out), zc, budget


def rest_depths(init, h, level="rho"):
    """Rest-state depths (m, positive down) of the rho levels, or of the
    w levels (cell faces, bottom first) with level='w'."""
    with netCDF4.Dataset(init) as d:
        hc = float(d["hc"][:].ravel()[0])
        if level == "rho":
            s, cs = d["sc_r" if "sc_r" in d.variables else "s_rho"][:].astype(float), d["Cs_r"][:].astype(float)
        else:
            s, cs = d["sc_w" if "sc_w" in d.variables else "s_w"][:].astype(float), d["Cs_w"][:].astype(float)
    return -h[None] * (hc * s[:, None, None] + h[None] * cs[:, None, None]) / (hc + h[None])


def cell_means(T, H, faces):
    """Average of the column profile T (time, cell; uniform cells over 0..H)
    over the depth intervals between consecutive faces (positive down,
    bottom first), from the column's cumulative heat."""
    nz = T.shape[1]
    zf = np.arange(nz + 1) * H / nz
    cum = np.concatenate([np.zeros((T.shape[0], 1)), np.cumsum(T, axis=1) * H / nz], axis=1)
    shape = faces.shape
    f = np.clip(faces.reshape(shape[0], -1), 0, H)
    out = np.empty((T.shape[0], shape[0] - 1, f.shape[1]))
    for r in range(T.shape[0]):
        c = np.interp(f, zf, cum[r])                     # cumulative heat at each face
        out[r] = (c[:-1] - c[1:]) / (f[:-1] - f[1:])     # faces bottom first: deeper minus shallower
    return out.reshape((T.shape[0], shape[0] - 1) + shape[1:])


def main():
    here = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--case", type=Path, default=here / "cases/Reef_Ideal_A15_veg_therm")
    ap.add_argument("--ocean-in", type=Path, help="ocean.in with the run's parameters (default: the case's)")
    ap.add_argument("--init", type=Path)
    ap.add_argument("--hours", type=float)
    ap.add_argument("--kbg", type=float, default=5e-5)
    ap.add_argument("--dz", type=float, default=0.5)
    ap.add_argument("--dt", type=float, default=60.0)
    ap.add_argument("--out-dt", type=float, default=1800.0)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--png", type=Path)
    a = ap.parse_args()
    text = (a.ocean_in or a.case / "ocean.in").read_text()
    rho0, wtype = ocean_in(text, "RHO0"), ocean_in(text, "WTYPE")
    user = ocean_in(text, "USER", int(ocean_in(text, "NUSER")))
    if len(user) < 9:
        raise SystemExit("ocean.in: USER needs 9 values (heating in 6-9)")
    hours = a.hours or ocean_in(text, "NTIMES") * ocean_in(text, "DT") / 3600
    init = a.init or a.case / ocean_in_name((a.case / "ocean.in").read_text(), "ININAME")
    out = a.out or a.case

    with netCDF4.Dataset(a.case / ocean_in_name((a.case / "ocean.in").read_text(), "GRDNAME")) as g:
        h = g["h"][:].astype(float)
        wet = g["mask_rho"][:] > 0.5
    depth = rest_depths(init, h)                                 # (N, eta, xi), positive down
    j, i = np.unravel_index(np.argmax(np.where(wet, h, -1)), h.shape)
    with netCDF4.Dataset(init) as d:
        tcol = d["temp"][0, :, j, i].astype(float)
        salt = float(np.mean(d["salt"][0][:, wet]))
    H = h[j, i]
    nz = int(round(H / a.dz))
    zc = (np.arange(nz) + 0.5) * H / nz                          # column cell centres (m, down)
    dcol, tcol = depth[::-1, j, i], tcol[::-1]                   # top first, increasing depth
    T0 = np.interp(zc, dcol, tcol)
    for sel, (k0, k1) in ((zc < dcol[0], (0, 1)), (zc > dcol[-1], (-2, -1))):   # extend linearly
        T0[sel] = tcol[k1] + (tcol[k1] - tcol[k0]) / (dcol[k1] - dcol[k0]) * (zc[sel] - dcol[k1])

    wf = rest_depths(init, h, "w")                               # (N+1, eta, xi), bottom first
    top = float(wf[-2, j, i] - wf[-1, j, i])                     # ROMS's top layer at the column
    times, T, zc, (dheat, heat_in) = column(T0, H, a.dz, a.dt, hours, a.out_dt, a.kbg, rho0, user, wtype, top)
    sst = T[:, 0]
    print(f"far-field column: {H:.0f} m, dz {H / len(zc):.2f} m, dt {a.dt:g} s, kbg {a.kbg:g} m2/s, "
          f"{hours:g} h (+1 output step); WTYPE {int(wtype)}, shortwave peak {user[5]:g} W/m2 over "
          f"{user[7]:g} h, non-solar {user[6]:g} W/m2, hour at t=0 {user[8]:g}"
          + (f"; feedback {user[9]:g} W/m2/C about {user[10]:g} C over the top {top:.1f} m"
             if len(user) >= 11 and user[9] else ""))
    print(f"  heat budget: content change {dheat / 1e6:.3f} MJ/m2, surface input {heat_in / 1e6:.3f} MJ/m2 "
          f"(difference {abs(dheat - heat_in) / max(abs(heat_in), 1):.1e} relative)")
    print(f"  surface cell temperature {sst.min():.3f}..{sst.max():.3f} C (start {sst[0]:.3f}); "
          f"temperature at 50 m {np.interp(50, zc, T[0]):.3f} -> {np.interp(50, zc, T[-1]):.3f} C")

    # average over each ROMS cell (rest-state w depths) and write the ROMS files;
    # times in the initial file's reference (A15: "days", model time 0;
    # cases with a calendar start: "seconds since 2000-01-01 00:00:00")
    with netCDF4.Dataset(init) as d:
        tunits = getattr(d["ocean_time"], "units", "days")
        tinit = float(d["ocean_time"][:].ravel()[0])
    tdays = tinit / 86400.0 if tunits.startswith("second") else tinit
    tunits = "days since " + tunits.split("since", 1)[1].strip() if "since" in tunits else "days"
    days = tdays + times / 86400.0
    change = cell_means(T, H, rest_depths(init, h, "w"))
    with netCDF4.Dataset(init) as d:
        tinit = d["temp"][0].astype(float)
    temp = tinit[None] + change - change[:1]                    # (time, N, eta, xi)
    N, ny, nx = depth.shape
    with netCDF4.Dataset(out / "ocean_clm.nc", "w") as d:
        d.createDimension("xi_rho", nx)
        d.createDimension("eta_rho", ny)
        d.createDimension("s_rho", N)
        d.createDimension("temp_time", len(days))
        d.createDimension("salt_time", 2)
        v = d.createVariable("temp_time", "f8", ("temp_time",))
        v.units, v.long_name = tunits, "far-field temperature time"
        v[:] = days
        v = d.createVariable("salt_time", "f8", ("salt_time",))
        v.units, v.long_name = tunits, "far-field salinity time"
        v[:] = [days[0], days[-1]]
        v = d.createVariable("temp", "f4", ("temp_time", "s_rho", "eta_rho", "xi_rho"))
        v.units, v.long_name, v.time = "Celsius", "far-field temperature climatology", "temp_time"
        v[:] = temp
        v = d.createVariable("salt", "f4", ("salt_time", "s_rho", "eta_rho", "xi_rho"))
        v.units, v.long_name, v.time = "nondimensional", "far-field salinity climatology", "salt_time"
        v[:] = salt
        d.history = "tools/thermal/far_field.py: 1-D column (background mixing + convective adjustment)"
    with netCDF4.Dataset(out / "ocean_bndry.nc", "w") as d:
        d.createDimension("xi_rho", nx)
        d.createDimension("s_rho", N)
        d.createDimension("temp_time", len(days))
        d.createDimension("salt_time", 2)
        v = d.createVariable("temp_time", "f8", ("temp_time",))
        v.units = tunits
        v[:] = days
        v = d.createVariable("salt_time", "f8", ("salt_time",))
        v.units = tunits
        v[:] = [days[0], days[-1]]
        v = d.createVariable("temp_north", "f4", ("temp_time", "s_rho", "xi_rho"))
        v.units, v.time = "Celsius", "temp_time"
        v[:] = temp[:, :, -1, :]
        v = d.createVariable("salt_north", "f4", ("salt_time", "s_rho", "xi_rho"))
        v.units, v.time = "nondimensional", "salt_time"
        v[:] = salt
        d.history = "tools/thermal/far_field.py: 1-D column at the north boundary row"
    print(f"  wrote {out / 'ocean_clm.nc'} and {out / 'ocean_bndry.nc'} ({len(days)} records to "
          f"{(days[-1] - days[0]) * 24:.1f} h)")
    np.savez(out / "far_field_column.npz", times=times, z=zc, T=T)

    if a.png:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.6), constrained_layout=True)
        hrs = times / 3600
        ax1.plot(hrs, sst, color="#e66767", lw=2, label="surface cell")
        ax1.plot(hrs, [np.interp(5, zc, x) for x in T], color="#3987e5", lw=2, label="5 m")
        ax1.plot(hrs, [np.interp(20, zc, x) for x in T], color="#184f95", lw=2, label="20 m")
        ax1.set_xlabel("hours", fontsize=8)
        ax1.set_ylabel("T (C)", fontsize=8)
        ax1.legend(fontsize=8, frameon=False)
        ax1.set_title("far-field column temperature", fontsize=9)
        for r in range(0, len(hrs), max(1, len(hrs) // 8)):
            ax2.plot(T[r], -zc, lw=1.5, label=f"{hrs[r]:.0f} h")
        ax2.set_ylim(-60, 0)
        top = T[:, zc <= 60]
        ax2.set_xlim(float(top.min()) - 0.1, float(top.max()) + 0.1)
        ax2.set_xlabel("T (C)", fontsize=8)
        ax2.set_ylabel("z (m)", fontsize=8)
        ax2.legend(fontsize=7, frameon=False, ncol=2)
        ax2.set_title("profiles, top 60 m", fontsize=9)
        fig.savefig(a.png, dpi=120)
        print(f"  figure {a.png}")


if __name__ == "__main__":
    main()
