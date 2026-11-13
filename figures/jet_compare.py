#!/usr/bin/env python3
"""Pass jet at 40°S with and without stratification (notebook 2026-11-12_coriolis-and-particles).

Usage: ~/venv/bin/python -I figures/jet_compare.py UNSTRAT_HIS.nc STRAT_HIS.nc OUT.png [--hours 120 144]

Both files: merged 15 min history of the 7-day 40°S runs (a15cor40s168, a15scor40s168).
Time mean of the Lagrangian velocity (u + u_stokes, v + v_stokes) over --hours (run hours).
Top: cross-sections of the offshore velocity 2.5 km from shore (isotherms on the stratified one).
Bottom: along the jet, its core speed at the surface, its thickness (depth where the offshore
velocity at the core falls to half its surface value) and its path (alongshore position of the
surface core); thickness and path are plotted while the core is faster than 0.02 m/s.
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import netCDF4  # noqa: E402
import numpy as np  # noqa: E402

F0 = 9.3745e-5
INK, MUTED = "#1f2a36", "#5b6b7a"
COL = {"u": "#2a6f97", "s": "#c0392b"}


def periodic_x(x, pm_row):
    x = np.array(x, float).copy()
    dx = 1.0 / np.array(pm_row, float)
    L = len(x) - 2
    x[0] = x[1] - 0.5 * (dx[0] + dx[1])
    x[L + 1] = x[L] + 0.5 * (dx[L] + dx[L + 1])
    return x


def load(path, h0, h1):
    d = netCDF4.Dataset(path)
    t = np.array(d["ocean_time"][:]) / 3600
    k = np.flatnonzero((t >= h0) & (t <= h1))
    x = periodic_x(d["x_rho"][0, :], d["pm"][0, :])
    yv = np.array(d["y_v"][:, 0], float)
    h = np.array(d["h"][:], float)
    hv = 0.5 * (h[1:] + h[:-1])
    hc = float(d["hc"][:])
    zr = hv[None] * (hc * d["s_rho"][:][:, None, None] + hv[None] * d["Cs_r"][:][:, None, None]) / (hc + hv[None])
    V = np.zeros(d["v"].shape[1:])
    T = np.zeros(d["temp"].shape[1:])
    for i0 in range(0, len(k), 24):
        kk = k[i0:i0 + 24]
        V += (np.ma.filled(d["v"][kk], 0) + np.ma.filled(d["v_stokes"][kk], 0)).sum(0)
        T += np.ma.filled(d["temp"][kk], np.nan).sum(0)
    V /= len(k)
    T /= len(k)
    Tv = 0.5 * (T[:, 1:] + T[:, :-1])
    return dict(x=x, yv=yv, hv=hv, zr=np.asarray(zr), V=V, T=Tv, hours=(t[k[0]], t[k[-1]]))


def along(r):
    x, yv, V, zr = r["x"], r["yv"], r["V"], r["zr"]
    win = np.abs(x) < 3000
    rows = np.flatnonzero((yv > 1150) & (yv < 4800))
    y, xs, us, th = [], [], [], []
    for j in rows:
        i = np.flatnonzero(win)[np.argmax(V[-1, j, win])]
        prof = V[:, j, i]
        y.append(yv[j] / 1e3)
        xs.append(x[i] / 1e3)
        us.append(prof[-1])
        th.append(-zr[:, j, i][prof > 0.5 * prof[-1]].min() if prof[-1] > 0 else np.nan)
    return np.array(y), np.array(xs), np.array(us), np.array(th)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("unstrat")
    ap.add_argument("strat")
    ap.add_argument("out")
    ap.add_argument("--hours", type=float, nargs=2, default=(120, 144))
    a = ap.parse_args()
    R = {"u": load(a.unstrat, *a.hours), "s": load(a.strat, *a.hours)}
    name = {"u": "unstratified", "s": "stratified (N² 1e-4)"}

    fig = plt.figure(figsize=(12, 8.2))
    outer = fig.add_gridspec(2, 1, height_ratios=[1, 0.9], hspace=0.38, left=0.07, right=0.97, top=0.9,
                             bottom=0.08)
    top = outer[0].subgridspec(1, 2, wspace=0.12)
    bot = outer[1].subgridspec(1, 3, wspace=0.42)
    ysec = 2500.0
    for c, key in enumerate(("u", "s")):
        ax = fig.add_subplot(top[0, c])
        r = R[key]
        j = int(np.argmin(abs(r["yv"] - ysec)))
        X = np.broadcast_to(r["x"][None] / 1e3, r["zr"][:, j].shape)
        pc = ax.pcolormesh(X, r["zr"][:, j], r["V"][:, j], cmap="RdBu_r", vmin=-0.3, vmax=0.3, shading="gouraud")
        if key == "s":
            cs = ax.contour(X, r["zr"][:, j], r["T"][:, j], levels=np.arange(20, 28.01, 0.5), colors=MUTED,
                            linewidths=0.6)
            ax.clabel(cs, cs.levels[-4::2], fontsize=8, fmt="%.1f °C")
        ax.fill_between(r["x"] / 1e3, -r["hv"][j], -400, color="#d9d2c5", zorder=3)
        ax.set_xlim(-3, 3)
        ax.set_ylim(-160, 0)
        ax.set_title(f"{name[key]}: offshore velocity {ysec / 1e3:g} km from shore", fontsize=11, color=INK,
                     loc="left")
        ax.set_xlabel("alongshore from the pass (km)")
        if c == 0:
            ax.set_ylabel("depth (m)")
    cb = fig.colorbar(pc, ax=fig.axes[:2], fraction=0.025, pad=0.015)
    cb.set_label("offshore velocity (m/s)")

    A = {k: along(R[k]) for k in R}
    ax1 = fig.add_subplot(bot[0, 0])
    ax2 = fig.add_subplot(bot[0, 1])
    ax3 = fig.add_subplot(bot[0, 2])
    for k, (y, xs, us, th) in A.items():
        ok = us > 0.02
        ax1.plot(y, us, color=COL[k], label=name[k])
        ax2.plot(y[ok], th[ok], color=COL[k])
        ax3.plot(xs[ok], y[ok], color=COL[k], marker="o", ms=2.5, lw=1)
    ax1b = ax1.twinx()
    ax1b.set_ylim(np.array(ax1.get_ylim()) / F0 / 1e3)
    ax1b.set_ylabel("turning radius U/|f| (km)", color=MUTED)
    ax1.set_xlabel("distance from shore (km)")
    ax1.set_ylabel("surface speed of the jet core (m/s)")
    ax1.legend(frameon=False, fontsize=9)
    ax2.set_xlabel("distance from shore (km)")
    ax2.set_ylabel("jet thickness (m)")
    ax2.set_yscale("log")
    ax3.axvline(0, color=MUTED, lw=0.6, ls=":")
    ax3.set_xlabel("alongshore position of the core (km)")
    ax3.set_ylabel("distance from shore (km)")
    ax3.set_xlim(-2, 2)
    ax3.set_ylim(1, 5)
    ax3.text(-1.9, 4.75, "← rotation turns flow this way", fontsize=8.5, color=MUTED)
    for ax in (ax1, ax2, ax3):
        ax.grid(alpha=0.25)
    fig.suptitle(f"Pass jet at 40°S with and without stratification (time mean, run hours "
                 f"{R['u']['hours'][0]:.0f}-{R['u']['hours'][1]:.0f}, Lagrangian velocity)",
                 x=0.07, ha="left", fontsize=13, color=INK, fontweight="bold")
    fig.savefig(a.out, dpi=150)
    for k, (y, xs, us, th) in A.items():
        for yy in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5):
            m = int(np.argmin(abs(y - yy)))
            print(f"{name[k]:22s} {y[m]:4.2f} km: core x {xs[m]:+5.2f} km, surface {us[m]:.3f} m/s "
                  f"(U/|f| {us[m] / F0 / 1e3:4.1f} km), thickness {th[m]:5.1f} m")


if __name__ == "__main__":
    main()
