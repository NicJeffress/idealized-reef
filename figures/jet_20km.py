"""Figures for the 20 km runs. Usage: jet_20km.py DIR OUTPREFIX  (DIR holds f0, s40, ml30, ml125 .nc from extract_jet_fields.py and heads.npz from jet_head.py)
1) surface Lagrangian speed maps at a few hours, one row per run
2) jet head against time
3) sections of offshore velocity and temperature at 5 and 10 km, mean of hours 120-168"""
import sys, netCDF4, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D, OUT = sys.argv[1], sys.argv[2]
RUNS = [("f0", "f = 0, N² 1e-4"), ("s40", "40°S, N² 1e-4"), ("ml30", "40°S, 30 m mixed layer"),
        ("ml125", "40°S, 125 m mixed layer")]
HOURS = (24, 72, 120, 168)
H = np.load(f"{D}/heads.npz")


def surf_speed(d, k, L):
    u = np.array(d["u_sfc"][k], float) + np.array(d["u_stokes_sfc"][k], float)
    v = np.array(d["v_sfc"][k], float) + np.array(d["v_stokes_sfc"][k], float)
    u[np.abs(u) > 1e10] = 0; v[np.abs(v) > 1e10] = 0
    ur = np.zeros(d["h"].shape); vr = ur.copy()
    ur[:, 1:-1] = 0.5 * (u[:, 1:] + u[:, :-1]); vr[1:-1] = 0.5 * (v[1:] + v[:-1])
    return np.hypot(ur, vr)[:, 1:L + 1]


# 1) maps
fig, ax = plt.subplots(len(RUNS), len(HOURS), figsize=(13, 15), sharex=True, sharey=True,
                       constrained_layout=True)
for a, (r, lab) in enumerate(RUNS):
    d = netCDF4.Dataset(f"{D}/{r}.nc"); d.set_auto_mask(False)
    t = d["ocean_time"][:] / 3600; L = d["h"].shape[1] - 2
    x = np.array(d["x_rho"][0, 1:L + 1]) / 1e3; y = np.array(d["y_rho"][:, 0]) / 1e3
    el = float(d["y_v"][-1, 0]) / 1e3
    for b, h in enumerate(HOURS):
        k = int(np.argmin(abs(t - h)))
        s = surf_speed(d, k, L)
        xx = np.concatenate([x - 6.02, x, x + 6.02]); ss = np.tile(s, 3)
        pc = ax[a, b].pcolormesh(xx, y, ss, vmin=0, vmax=0.3, cmap="magma_r", shading="auto")
        ax[a, b].axhline(float(d["y_rho"][-1, 0]) / 1e3 - 4, color="tab:blue", lw=0.8, ls="--")
        ax[a, b].set_xlim(-6, 6); ax[a, b].set_aspect("equal")
        if a == 0: ax[a, b].set_title(f"hour {t[k]:.0f}")
        if b == 0: ax[a, b].set_ylabel(f"{lab}\ndistance from shore (km)")
        if a == len(RUNS) - 1: ax[a, b].set_xlabel("alongshore (km)")
fig.colorbar(pc, ax=ax, shrink=0.4, label="top-layer Lagrangian speed (m/s)")
fig.suptitle("Surface speed, 20 km domain (two periods wide; dashed: start of the 4 km nudging band)")
fig.savefig(f"{OUT}_maps.png", dpi=110); plt.close(fig)

# 2) heads
fig, ax = plt.subplots(2, 1, figsize=(9, 7), sharex=True, constrained_layout=True)
for r, lab in RUNS:
    t = H[f"{r}__t"]
    ax[0].plot(t, H[f"{r}__h05"] / 1e3, label=lab)
    ax[1].plot(t, H[f"{r}__h02"] / 1e3, label=lab)
band = float(H["s40__band"]) / 1e3
for a, thr in zip(ax, ("0.05", "0.02")):
    a.axhline(band, color="k", ls="--", lw=0.8); a.text(1, band + 0.2, "nudging band", fontsize=8)
    a.axhline(4.04, color="grey", ls=":", lw=0.8); a.text(1, 4.2, "band of the 5 km domain", fontsize=8, color="grey")
    a.set_ylabel(f"head, v > {thr} m/s (km)"); a.grid(alpha=0.3)
ax[0].legend(fontsize=8); ax[1].set_xlabel("run hour"); ax[1].set_xticks(range(0, 169, 24))
fig.suptitle("Surface jet head: farthest offshore point connected to the pass")
fig.savefig(f"{OUT}_heads.png", dpi=110); plt.close(fig)

# 3) sections, mean of hours 120-168
fig, ax = plt.subplots(2, len(RUNS), figsize=(16, 7), sharey="row", constrained_layout=True)
for a, (r, lab) in enumerate(RUNS):
    d = netCDF4.Dataset(f"{D}/{r}.nc"); d.set_auto_mask(False)
    t = d["ocean_time"][:] / 3600; k = np.flatnonzero((t >= 120) & (t <= 168))
    L = d["h"].shape[1] - 2; x = np.array(d["x_rho"][0, 1:L + 1]) / 1e3
    hc = float(d["hc"][:]); Cs = np.array(d["Cs_r"][:]); s = np.array(d["s_rho"][:])
    for b, js in enumerate((1, 2)):
        jv = int(d["jsec_v"][js]); jr = int(d["jsec_rho"][js])
        hv = 0.5 * (d["h"][jv, 1:L + 1] + d["h"][jv + 1, 1:L + 1])
        z = hv[None] * (hc * s[:, None] + hv[None] * Cs[:, None]) / (hc + hv[None])
        V = (np.array(d["v_sec"][k, :, js, 1:L + 1]) + np.array(d["v_stokes_sec"][k, :, js, 1:L + 1])).mean(0)
        T = np.array(d["temp_sec"][k, :, js, 1:L + 1]).mean(0)
        X = np.broadcast_to(x, z.shape)
        pc = ax[b, a].contourf(X, z, V, levels=np.linspace(-0.15, 0.15, 31), cmap="RdBu_r", extend="both")
        ax[b, a].contour(X, z, T, levels=np.arange(4, 30, 1), colors="k", linewidths=0.4)
        ax[b, a].set_ylim(-120, 0)
        ax[b, a].set_title(f"{lab}, {float(d['ysec'][js])/1e3:.0f} km offshore", fontsize=9)
        if a == 0: ax[b, a].set_ylabel("depth (m)")
        if b == 1: ax[b, a].set_xlabel("alongshore (km)")
fig.colorbar(pc, ax=ax, shrink=0.6, label="offshore Lagrangian velocity (m/s), hours 120-168")
fig.suptitle("Jet sections (black: temperature every 1 °C)")
fig.savefig(f"{OUT}_sections.png", dpi=110); plt.close(fig)
print("done")
