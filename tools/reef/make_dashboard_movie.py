#!/usr/bin/env python3
"""Dashboard movie of an A15 reef run: run name and info on top, time series with a moving
marker, then six maps.

    Hs                  velocity            transport
    sea level - offshore  surface current   vorticity

Usage:
  ~/venv/bin/python -I make_dashboard_movie.py FILE.nc OUT.mp4 [--title NAME] [--info TEXT]
      [--ymax M] [--panel-px N] [--stride K] [--frames N] [--fps 8] [--csv FILE] [--max-frame 8192x4320]
      [--run-hours]

FILE.nc: a quicksave or history file with zeta, ubar, vbar, Hwave; ubar_stokes, vbar_stokes for
Lagrangian velocity and transport; u_sur, v_sur (or 3-D u, v) for the surface current. Joined
segment files work (tools/merge_segments.py).

--ymax M shows only the first M metres from shore: the maps then go in three rows of two with colour
bars on the right. Without it, two rows of three. Every cell is drawn as one colour. Colour limits are
fixed over the movie. Sea level is drawn minus the offshore mean, so the tide leaves the map and the
set-up stays. Velocity, transport and vorticity are Eulerian + Stokes where the file has Stokes.

Time series use the regions of tests/options_compare.py by distance from shore, so they work on any
A15 grid: lagoon 233-815 m, offshore beyond 3800 m, crest v-row at 970 m, reef columns h < 0.8 m at
965 m, pass columns h > 1 m there. --csv writes them, one row per record.
"""
import argparse
import csv

import imageio_ffmpeg
import matplotlib
import netCDF4
import numpy as np

matplotlib.use("Agg")
import matplotlib.animation as animation  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
DPI = 200
DEPTHS = [1, 2, 5, 10, 20, 50, 100, 200]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("out")
    ap.add_argument("--title", default="Reef_Ideal_A15_veg")
    ap.add_argument("--info", default="")
    ap.add_argument("--ymax", type=float, help="show only this many metres from shore")
    ap.add_argument("--panel-px", type=int, help="map width (px); default as large as --max-frame allows, at most 1920")
    ap.add_argument("--max-frame", default="8192x4320")
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--stride", type=int, default=1, help="use every K-th record")
    ap.add_argument("--frames", type=int, help="only the first N frames (tests)")
    ap.add_argument("--csv", help="write the time series here")
    ap.add_argument("--run-hours", action="store_true",
                    help="label time as hours since the run started (ocean_time), not since the file's first record")
    a = ap.parse_args()

    d = netCDF4.Dataset(a.file)
    d.set_auto_mask(False)
    Lm = d.dimensions["xi_rho"].size - 2
    cols = slice(1, Lm + 1)                                  # interior columns: the ghost columns repeat them
    x, y = d["x_rho"][:, cols] / 1e3, d["y_rho"][:, cols] / 1e3
    h = d["h"][:, cols]
    y1, x1 = y[:, 0], x[0, :]
    tabs = d["ocean_time"][:].astype(float)
    th = (tabs - (0.0 if a.run_hours else tabs[0])) / 3600.0
    stokes = "ubar_stokes" in d.variables
    has_sur = "u_sur" in d.variables

    # ---- regions, as tests/options_compare.py, by distance from shore -------
    jcr = int(np.argmin(np.abs(y1 - 0.965)))
    reef = h[jcr] < 0.8
    passc = h[jcr] > 1.0
    jv = int(np.argmin(np.abs(d["y_v"][:, 0] / 1e3 - 0.970)))
    lagoon = (y1 >= 0.233) & (y1 <= 0.815)  # rows
    offshore = y1 > 3.8
    pm = d["pm"][:, cols]
    dx_v = 2.0 / (pm[jv] + pm[jv + 1])

    wet = d["mask_rho"][:, cols] > 0

    def read(name, k):                                       # record k with land fill values at zero
        f = np.array(d[name][k], dtype=float)
        f[np.abs(f) > 1e30] = 0.0
        return f

    def velocity(k, lagrangian=True):
        ub, vb = read("ubar", k), read("vbar", k)
        if lagrangian and stokes:
            ub, vb = ub + read("ubar_stokes", k), vb + read("vbar_stokes", k)
        return rho_points(ub, vb)

    def rho_points(ub, vb):
        u = 0.5 * (ub[:, 0:Lm] + ub[:, 1:Lm + 1])
        v = np.zeros_like(u)
        v[1:-1] = 0.5 * (vb[:-1, cols] + vb[1:, cols])
        return u, v

    def surface(k):
        if has_sur:
            return rho_points(read("u_sur", k), read("v_sur", k))
        return rho_points(read("u", k)[-1], read("v", k)[-1])

    def fields(k):
        z = read("zeta", k)[:, cols]
        u, v = velocity(k)
        dep = np.maximum(h + z, 0.0)
        us, vs = surface(k)
        vort = np.gradient(v, x1 * 1e3, axis=1) - np.gradient(u, y1 * 1e3, axis=0)
        land = lambda f: np.ma.masked_where(~wet, f)  # noqa: E731
        return {"hs": (land(read("Hwave", k)[:, cols]), None, None),
                "zeta": (land(z - z[offshore].mean()), None, None),
                "speed": (land(np.hypot(u, v)), u, v),
                "transport": (land(np.hypot(u, v) * dep), u * dep, v * dep),
                "surface": (land(np.hypot(us, vs)), us, vs),
                "vort": (land(vort), None, None)}

    # ---- time series ---------------------------------------------------------
    recs = np.arange(0, len(th), a.stride)
    ts = {n: np.zeros(len(th)) for n in ("tide", "setup", "qc", "qp", "hs_off", "hs_crest")}
    for k in range(len(th)):                                 # every record, for the drift curves
        z = read("zeta", k)[:, cols]
        ts["tide"][k] = z[offshore].mean()
        ts["setup"][k] = 1e3 * (z[lagoon].mean() - ts["tide"][k])
        D = 0.5 * (h[jv] + h[jv + 1] + z[jv] + z[jv + 1])
        vb = read("vbar", k)[jv, cols]
        if stokes:
            vb = vb + read("vbar_stokes", k)[jv, cols]
        q = -vb * D * dx_v                                   # lagoon-ward positive
        ts["qc"][k], ts["qp"][k] = q[reef].sum(), q[passc].sum()
        hw = read("Hwave", k)[:, cols]
        ts["hs_off"][k], ts["hs_crest"][k] = hw[offshore].mean(), hw[jcr, reef].mean()
    if a.csv:
        with open(a.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["hours", "offshore_zeta_m", "setup_mm", "crest_q_m3s", "pass_q_m3s", "hs_offshore_m", "hs_crest_m"])
            for k in range(len(th)):
                w.writerow([f"{th[k]:.4f}", f"{ts['tide'][k]:.5f}", f"{ts['setup'][k]:.3f}", f"{ts['qc'][k]:.2f}",
                            f"{ts['qp'][k]:.2f}", f"{ts['hs_off'][k]:.4f}", f"{ts['hs_crest'][k]:.4f}"])
    if a.frames:
        recs = recs[:a.frames]

    # ---- colour limits, from the part in view ---------------------------------
    ytop = (a.ymax / 1e3) if a.ymax else float(y.max())
    view = y <= ytop
    fs = [fields(k) for k in np.linspace(len(th) // 8, len(th) - 1, min(30, len(th))).astype(int)]

    def pct(key, q):
        return np.percentile(np.concatenate([f[key][0][view & wet].compressed() for f in fs]), q)
    zl = max(0.02, float(np.abs(pct("zeta", [0.5, 99.5])).max()))
    wl = max(1e-4, float(np.abs(pct("vort", [0.5, 99.5])).max()))
    lab = "Eulerian + Stokes" if stokes else "Eulerian"
    style = {"hs": dict(cmap="viridis", vmin=0, vmax=float(pct("hs", 99.9)), label="significant wave height Hs (m)"),
             "zeta": dict(cmap="RdBu_r", vmin=-zl, vmax=zl, label="sea level minus offshore mean (m)"),
             "speed": dict(cmap="Blues", vmin=0, vmax=float(pct("speed", 99.5)), label=f"depth-averaged current, {lab} (m/s)"),
             "transport": dict(cmap="Blues", vmin=0, vmax=float(pct("transport", 99.5)), label=f"transport, {lab} (m2/s)"),
             "surface": dict(cmap="Blues", vmin=0, vmax=float(pct("surface", 99.5)), label="surface current, Eulerian (m/s)"),
             "vort": dict(cmap="RdBu_r", vmin=-wl, vmax=wl, label=f"depth-averaged vorticity, {lab} (1/s)")}

    # ---- layout in pixels, packed tight ---------------------------------------
    ext = (float(x.min()), float(x.max()), float(y.min()), ytop)
    asp = (ext[3] - ext[2]) / (ext[1] - ext[0])
    L, R, G, TITLE, TS, TSLAB, GAP, CB, VG, BOT = 150, 30, 36, 205, 240, 80, 24, 150, 20, 70
    maxw, maxh = (int(v) for v in a.max_frame.lower().split("x"))
    top0 = TITLE + TS + TSLAB + GAP
    rows3 = asp < 0.5
    if rows3:                                                # wide strips: 3 rows of 2 maps, colour bars on the right
        grid = [["hs", "zeta"], ["speed", "surface"], ["transport", "vort"]]
        CBW, R, VG = 170, 110, 34
        fixed_h = top0 + 2 * VG + BOT
        pw = int(min(a.panel_px or 1e9, (maxw - L - R - G - 2 * CBW) / 2, (maxh - fixed_h) / (3 * asp)))
        ph = int(round(pw * asp))
        W, H = L + 2 * (pw + CBW) + G + R, fixed_h + 3 * ph
    else:                                                    # 2 rows of 3 maps
        grid = [["hs", "speed", "transport"], ["zeta", "surface", "vort"]]
        CBW = 0
        fixed_h = top0 + 2 * CB + VG + 20
        pw = int(min(a.panel_px or 1920, (maxw - L - R - 2 * G) / 3, (maxh - fixed_h) / (2 * asp)))
        ph = int(round(pw * asp))
        W, H = L + 3 * pw + 2 * G + R, fixed_h + 2 * ph
    W, H = W + W % 2, H + H % 2
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor("white")
    plt.rcParams.update({"font.size": 11})

    def box(px, py, w, hgt):                                 # pixel box from the top-left corner
        return [px / W, 1 - (py + hgt) / H, w / W, hgt / H]
    fig.text(0.5, 1 - 45 / H, a.title, ha="center", va="center", fontsize=20, weight="bold")
    title2 = fig.text(0.5, 1 - 105 / H, "", ha="center", va="center", fontsize=14)

    # time series: one quantity family per panel, on one axis each
    tsw = (W - L - R - 2 * 200) / 3
    axs = [fig.add_axes(box(L + i * (tsw + 200), TITLE, tsw, TS)) for i in range(3)]
    axs[0].plot(th, ts["tide"], color="#1f4e8c", lw=1.0)
    axs[0].set_ylabel("sea level (m)", fontsize=10)
    axs[0].set_title("offshore sea level (tide)", fontsize=12)
    axs[1].plot(th, ts["setup"], color="#1f4e8c", lw=1.0)
    axs[1].set_ylabel("mm", fontsize=10)
    axs[1].set_title("lagoon set-up, lagoon minus offshore", fontsize=12)
    axs[2].plot(th, ts["qc"], color="#1f4e8c", lw=1.0, label="over the crest (lagoon-ward)")
    axs[2].plot(th, -ts["qp"], color="#b5541c", lw=1.0, label="out through the pass")
    axs[2].legend(fontsize=9, loc="lower right", ncol=2, frameon=False)
    axs[2].set_ylabel("m3/s", fontsize=10)
    axs[2].set_title(f"transport, {lab}", fontsize=12)
    markers = []
    for ax in axs:
        ax.set_xlim(th[0], th[-1])
        ax.set_xlabel("hours")
        ax.grid(alpha=0.3)
        ax.spines[["top", "right"]].set_visible(False)
        markers.append(ax.axvline(th[0], color="r", lw=1.5))

    # maps
    f0 = fields(int(recs[0]))
    tdx = (ext[1] - ext[0]) / (90 if rows3 else 60)
    jj, ii = np.nonzero(view & wet)
    _, first = np.unique(np.stack([np.floor(x[jj, ii] / tdx), np.floor(y[jj, ii] / tdx)]), axis=1, return_index=True)
    aj, ai = jj[first], ii[first]

    def clip(u, v, vmax):
        fac = np.minimum(1.0, vmax / np.maximum(np.hypot(u, v), 1e-12))
        return u * fac, v * fac

    artists = {}
    for r, row in enumerate(grid):
        for c, key in enumerate(row):
            if rows3:
                px, py = L + c * (pw + CBW + G), top0 + r * (ph + VG)
                ax = fig.add_axes(box(px, py, pw, ph))
                cax = fig.add_axes(box(px + pw + 14, py + 0.05 * ph, 26, 0.9 * ph))
            else:
                px, py = L + c * (pw + G), top0 + r * (ph + CB + VG)
                ax = fig.add_axes(box(px, py, pw, ph))
                cax = fig.add_axes(box(px + 0.1 * pw, py + ph + 38, 0.8 * pw, 26))
            ax.set_xlim(ext[0], ext[1])
            ax.set_ylim(ext[2], ext[3])
            last = r == len(grid) - 1
            ax.tick_params(labelleft=(c == 0), labelbottom=bool(rows3 and last), direction="in", length=4)
            if rows3 and last:
                ax.set_xlabel("alongshore (km)")
            if c == 0:
                ax.set_ylabel("from shore (km)")
            st = dict(style[key])
            label = st.pop("label")
            fld, ue, vn = f0[key]
            pc = ax.pcolormesh(x, y, fld, shading="nearest", **st)
            cb = fig.colorbar(pc, cax=cax, orientation="vertical" if rows3 else "horizontal")
            cb.set_label(label, fontsize=12)
            ax.contour(x, y, h, levels=DEPTHS, colors="0.5", linewidths=0.4)
            q = None
            if ue is not None:
                qref = 0.25 * st["vmax"]
                ue, vn = clip(ue, vn, qref)
                q = ax.quiver(x[aj, ai], y[aj, ai], ue[aj, ai], vn[aj, ai], color="k", scale_units="xy",
                              scale=qref / (0.75 * tdx), width=0.0012, headwidth=3, headlength=3, headaxislength=2.7)
                unit = "m2/s" if key == "transport" else "m/s"
                ax.quiverkey(q, 0.74, 0.96, qref, f"{qref:.2g} {unit} (longer clipped)", labelpos="E",
                             fontproperties={"size": 10}, coordinates="axes")
            artists[key] = (pc, q)

    def update(n):
        k = int(recs[n])
        fk = fields(k)
        for key, (pc, q) in artists.items():
            fld, ue, vn = fk[key]
            pc.set_array(fld.ravel())
            if q is not None:
                ue, vn = clip(ue, vn, 0.25 * style[key]["vmax"])
                q.set_UVC(ue[aj, ai], vn[aj, ai])
        for m in markers:
            m.set_xdata([th[k], th[k]])
        now = (f"day {th[k] / 24:4.2f}, t = {th[k]:6.2f} h   |   tide {ts['tide'][k]:+.3f} m   |   set-up {ts['setup'][k]:5.1f} mm"
               f"   |   crest {ts['qc'][k]:4.0f} m3/s")
        title2.set_text(f"{a.info}   |   {now}" if a.info else now)
        return []

    print(f"frame {W} x {H} px, maps {pw} x {ph} px, {len(recs)} frames, {len(recs) / a.fps:.0f} s at {a.fps} fps")
    anim = animation.FuncAnimation(fig, update, frames=len(recs), blit=False)
    writer = animation.FFMpegWriter(fps=a.fps, codec="libx264",
                                    extra_args=["-crf", "18", "-preset", "slow", "-pix_fmt", "yuv420p"])
    anim.save(a.out, writer=writer, dpi=DPI)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
