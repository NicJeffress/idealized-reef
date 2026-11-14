#!/usr/bin/env python3
"""Dashboard movie of several runs side by side: particles, flow, temperature and a section.

Usage: ~/venv/bin/python -I figures/make_compare_dashboard.py OUT.mp4 TRACK_DIR:FIELDS.nc:LABEL [...]
           [--xmax 12] [--step 1] [--tail 8] [--every 1] [--fps 24] [--dpi 120] [--width 14]
           [--depth-max 80] [--still HOUR] [--band KM] [--title ...] [--subtitle ...]

One column per run; rows:
  1. particles (tools/reef/track_particles.py output in TRACK_DIR), coloured by depth below
     mean sea level (0 to --depth-max m), with a fading tail;
  2. depth-averaged Lagrangian speed (ubar + ubar_stokes, vbar + vbar_stokes), with arrows;
  3. top-layer Lagrangian speed (u + u_stokes, v + v_stokes), with arrows;
  4. surface temperature minus the run's initial surface temperature;
  5. section across the jet 2.5 km from shore: offshore Lagrangian velocity, isotherms every 1 C.
FIELDS.nc is the run's file from tools/reef/extract_jet_fields.py (top-layer and depth-mean
fields at every record, sections). Maps are upright as in the other figures: shore at the
bottom, 0 to --xmax km offshore, one alongshore period with the pass in the middle, so the
movie is about twice as tall as wide. Arrows are capped at 0.15 m/s so the jet's do not cover
the panel. Time runs from the particle release (the first track record).
--still HOUR writes one PNG at that many hours after release instead of the movie.
"""
import argparse
import importlib.util
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
import netCDF4                                         # noqa: E402
import numpy as np                                     # noqa: E402
from matplotlib.collections import LineCollection      # noqa: E402
from matplotlib.colors import Normalize               # noqa: E402

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("mcg", HERE / "make_compare_gif.py")
mcg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcg)
mpf = mcg.mpf
INK, MUTED = mpf.INK, mpf.MUTED


def rd(v, k):
    a = np.array(v[k], float)
    a[np.abs(a) > 1e10] = 0.0
    return a


def to_rho(u, v):
    ur = np.zeros((u.shape[0], u.shape[1] + 1)); vr = np.zeros((v.shape[0] + 1, v.shape[1]))
    ur[:, 1:-1] = 0.5 * (u[:, 1:] + u[:, :-1]); vr[1:-1] = 0.5 * (v[1:] + v[:-1])
    return ur, vr


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("runs", nargs="+", help="TRACK_DIR:FIELDS.nc:LABEL (| in LABEL starts a new line)")
    ap.add_argument("--xmax", type=float, default=12.0, help="km from shore shown")
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--tail", type=int, default=8)
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--fps", type=float, default=24)
    ap.add_argument("--dpi", type=float, default=120)
    ap.add_argument("--width", type=float, default=14.0, help="figure width, inches")
    ap.add_argument("--depth-max", type=float, default=80.0)
    ap.add_argument("--still", type=float, default=None)
    ap.add_argument("--band", type=float, default=None, help="mark the start of the nudging band at BAND km")
    ap.add_argument("--title", default="Where lagoon water goes, four oceans")
    ap.add_argument("--subtitle", default="Idealized coral reef, COAWST (ROMS + SWAN) + ROMSPath particles, "
                                          "1 m waves; particles released over the back reef at hour 24")
    a = ap.parse_args()

    runs = []
    for r in a.runs:
        tdir, fld, lab = r.split(":", 2)
        d = netCDF4.Dataset(fld); d.set_auto_mask(False)
        x = mpf.periodic_x(d["x_rho"][0, :], d["pm"][0, :]) / 1e3
        L = len(x) - 2
        period = float(x[L + 1] - x[1])
        ymax = float(d["y_rho"][-2, 0] / 1e3)
        hours, X, Y, Z = mcg.load(tdir, ymax, period)
        pid = np.arange(X.shape[1])
        X = np.hstack([X + k * period for k in (-1, 0, 1)])
        Y, Z, pid = (np.hstack([v] * 3) for v in (Y, Z, pid))
        keep = np.nanmin(np.abs(X), axis=0) < period / 2 + 0.5
        t = np.array(d["ocean_time"][:]) / 3600
        t0 = 24.0                                       # particle release, run hour
        runs.append(dict(d=d, x=x[1:L + 1], y=np.array(d["y_rho"][:, 0]) / 1e3, L=L, period=period, t=t, t0=t0,
                         hours=hours, X=X[:, keep], Y=Y[:, keep], Z=Z[:, keep], pid=pid[keep], lab=lab,
                         T0=rd(d["temp_sfc"], 0)[:, 1:L + 1]))
    n = len(runs)
    hours = runs[0]["hours"]
    nt = min(len(r["hours"]) for r in runs)
    chosen = np.random.default_rng(1).random(max(r["pid"].max() for r in runs) + 1) < 1.0 / a.every
    half = runs[0]["period"] / 2

    # layout (inches)
    W = a.width
    left, right, gapx, top, bottom, gapy = 1.85, 1.05, 0.18, 0.95, 0.5, 0.42
    pw = (W - left - right - gapx * (n - 1)) / n
    mh = pw * a.xmax / (2 * half)
    sh = 2.2
    H = top + 4 * mh + sh + 4 * gapy + bottom
    fig = plt.figure(figsize=(W, H), dpi=a.dpi)

    def axpos(col, row):
        y_top = H - top - sum([mh] * min(row, 4)) - gapy * row - (sh if row > 4 else 0)
        h = mh if row < 4 else sh
        return [(left + col * (pw + gapx)) / W, (y_top - h) / H, pw / W, h / H]

    dnorm = Normalize(0, a.depth_max)
    rowlab = ["particles\n(colour: depth)", "depth-averaged\ncurrent", "surface\ncurrent",
              "surface\ntemperature\nchange", "section 2.5 km\nfrom shore"]
    cm = dict(bar=("magma_r", 0, 0.2), sfc=("magma_r", 0, 0.3), temp=("RdBu_r", -0.5, 0.5),
              sec=("RdBu_r", -0.15, 0.15))
    arts = []
    for c, r in enumerate(runs):
        d, L = r["d"], r["L"]
        art = {}
        hh = np.array(d["h"][:, 1:L + 1], float)
        for row in range(5):
            ax = fig.add_axes(axpos(c, row))
            if row < 4:
                xs, ys = r["x"], r["y"]
                for k in (-1, 0, 1):
                    ax.contour(xs + k * r["period"], ys, hh, levels=[1.0], colors=["#c58b3a"], linewidths=0.8,
                               zorder=4)
                ax.set_xlim(-half, half); ax.set_ylim(0, a.xmax); ax.set_aspect("equal")
                if a.band:
                    ax.axhline(a.band, color=MUTED, lw=0.7, ls=(0, (4, 3)), zorder=5)
                    if row == 0:
                        ax.text(half - 0.1, a.band + 0.12, "nudging band", fontsize=7, color=MUTED, ha="right",
                                va="bottom", zorder=5)
                ax.set_xticks([-2, 0, 2]); ax.tick_params(labelsize=8)
                if row == 3:
                    ax.set_xlabel("alongshore (km)", fontsize=8.5)
                else:
                    ax.set_xticklabels([])
                if c == 0:
                    ax.set_ylabel("distance from shore (km)", fontsize=8)
                else:
                    ax.set_yticklabels([])
            if row == 0:
                ax.set_facecolor("#dfeaf1")
                ax.set_title(r["lab"].replace("|", "\n"), fontsize=10, color=INK, pad=4, linespacing=1.1)
                lc = LineCollection([], linewidths=0.4, zorder=3); ax.add_collection(lc)
                dots = ax.scatter([], [], s=0.8, c=[], cmap=mcg.DEPTH, norm=dnorm, lw=0, zorder=4)
                art.update(lc=lc, dots=dots, gsel=np.flatnonzero(chosen[r["pid"]]))
            elif row in (1, 2):
                name = "bar" if row == 1 else "sfc"
                cmap, lo, hi = cm[name]
                xx = np.concatenate([r["x"] - r["period"], r["x"], r["x"] + r["period"]])
                pc = ax.pcolormesh(xx, r["y"], np.zeros((len(r["y"]), len(xx))), cmap=cmap, vmin=lo, vmax=hi,
                                   shading="auto", rasterized=True, zorder=1)
                jq = np.flatnonzero((r["y"] > 1.15) & (r["y"] < a.xmax))[::5]; iq = np.arange(0, L, 6)   # no arrows over the reef
                q = ax.quiver(r["x"][iq], r["y"][jq], np.zeros((len(jq), len(iq))), np.zeros((len(jq), len(iq))),
                              scale=2.0, width=0.003, color="k", alpha=0.6, zorder=3)
                art[name] = (pc, q, jq, iq)
            elif row == 3:
                cmap, lo, hi = cm["temp"]
                xx = np.concatenate([r["x"] - r["period"], r["x"], r["x"] + r["period"]])
                art["temp"] = ax.pcolormesh(xx, r["y"], np.zeros((len(r["y"]), len(xx))), cmap=cmap, vmin=lo,
                                            vmax=hi, shading="auto", rasterized=True, zorder=1)
            else:
                js = 0
                jv = int(d["jsec_v"][js])
                hv = 0.5 * (d["h"][jv, 1:L + 1] + d["h"][jv + 1, 1:L + 1])
                hc = float(d["hc"][:]); Cs = np.array(d["Cs_r"][:]); s = np.array(d["s_rho"][:])
                z = hv[None] * (hc * s[:, None] + hv[None] * Cs[:, None]) / (hc + hv[None])
                Xs = np.broadcast_to(r["x"], z.shape)
                art["sec"] = dict(ax=ax, Xs=Xs, z=z, js=js)
                ax.set_xlim(-half, half); ax.set_ylim(-150, 0); ax.tick_params(labelsize=8)
                ax.set_xticks([-2, 0, 2]); ax.set_xlabel("alongshore (km)", fontsize=8.5)
                if c == 0:
                    ax.set_ylabel("depth (m)", fontsize=8)
                else:
                    ax.set_yticklabels([])
            for sp in ("top", "right"):
                ax.spines[sp].set_visible(False)
            if c == 0:
                p = axpos(0, row)
                fig.text(0.08 / W, p[1] + p[3] / 2, rowlab[row], fontsize=9.5, color=INK, va="center", ha="left",
                         linespacing=1.15)
        arts.append(art)

    # colour bars
    def cbar(row, mappable, label, extend="max"):
        p = axpos(n - 1, row)
        cax = fig.add_axes([1 - (right - 0.25) / W, p[1] + 0.1 * p[3], 0.1 / W, 0.8 * p[3]])
        cb = fig.colorbar(mappable, cax=cax, extend=extend)
        cb.set_label(label, fontsize=8, color=INK); cb.ax.tick_params(labelsize=7); cb.outline.set_visible(False)
        return cb
    cb = cbar(0, matplotlib.cm.ScalarMappable(norm=dnorm, cmap=mcg.DEPTH), "particle depth (m)")
    cb.ax.invert_yaxis()
    for row, name, lab in ((1, "bar", "speed (m/s)"), (2, "sfc", "speed (m/s)"), (3, "temp", "°C"),
                           (4, "sec", "offshore (m/s)")):
        cmap, lo, hi = cm[name]
        cbar(row, matplotlib.cm.ScalarMappable(norm=Normalize(lo, hi), cmap=cmap), lab,
             "both" if name in ("temp", "sec") else "max")
    fig.text(left / W, 1 - 0.18 / H, a.title, fontsize=15, fontweight="bold", color=INK, va="top")
    fig.text(left / W, 1 - 0.46 / H, a.subtitle, fontsize=9, color=MUTED, va="top")
    clock = fig.text(1 - 0.2 / W, 1 - 0.2 / H, "", fontsize=12, color=INK, va="top", ha="right")
    tail = a.tail * a.step

    def draw(k):
        hk = hours[k]
        k0 = max(0, k - tail)
        rows_ = np.arange(k0, k + 1, a.step)
        if rows_[-1] != k:
            rows_ = np.append(rows_, k)
        m = len(rows_) - 1
        for r, art in zip(runs, arts):
            d, L = r["d"], r["L"]
            # particles
            gs = art["gsel"]
            X, Y, Z = r["X"][rows_][:, gs], r["Y"][rows_][:, gs], r["Z"][rows_][:, gs]
            if m:
                p0 = np.stack([X[:-1], Y[:-1]], -1); p1 = np.stack([X[1:], Y[1:]], -1)
                seg = np.stack([p0, p1], 2).reshape(-1, 2, 2)
                ok = np.isfinite(seg).all((1, 2))
                age = np.repeat((np.arange(m) + 1) / max(tail / a.step, 1), len(gs))
                col = mcg.DEPTH(dnorm(0.5 * (Z[:-1] + Z[1:]).reshape(-1)[ok]))
                col[:, 3] = np.clip(age, 0.05, 1)[ok] * 0.8
                art["lc"].set_segments(seg[ok]); art["lc"].set_color(col)
            ok = np.isfinite(X[-1])
            art["dots"].set_offsets(np.c_[X[-1][ok], Y[-1][ok]]); art["dots"].set_array(Z[-1][ok])
            # fields at the matching record
            kf = int(np.argmin(abs(r["t"] - (r["t0"] + hk))))
            for name, (un, vn, us, vs) in (("bar", ("ubar", "vbar", "ubar_stokes", "vbar_stokes")),
                                           ("sfc", ("u_sfc", "v_sfc", "u_stokes_sfc", "v_stokes_sfc"))):
                u = rd(d[un], kf) + rd(d[us], kf); v = rd(d[vn], kf) + rd(d[vs], kf)
                ur, vr = to_rho(u, v)
                ur, vr = ur[:, 1:L + 1], vr[:, 1:L + 1]
                sp = np.hypot(ur, vr)                    # (y, x)
                pc, q, jq, iq = art[name]
                pc.set_array(np.hstack([sp, sp, sp]))
                cap = np.minimum(1.0, 0.15 / np.maximum(sp[np.ix_(jq, iq)], 1e-9))   # arrows capped at 0.15 m/s
                q.set_UVC(ur[np.ix_(jq, iq)] * cap, vr[np.ix_(jq, iq)] * cap)
            T = rd(d["temp_sfc"], kf)[:, 1:L + 1] - r["T0"]
            art["temp"].set_array(np.hstack([T, T, T]))
            sec = art["sec"]; ax = sec["ax"]
            for coll in list(ax.collections):
                coll.remove()
            V = rd(d["v_sec"], kf)[:, sec["js"], 1:L + 1] + rd(d["v_stokes_sec"], kf)[:, sec["js"], 1:L + 1]
            Ts = rd(d["temp_sec"], kf)[:, sec["js"], 1:L + 1]
            ax.contourf(sec["Xs"], sec["z"], V, levels=np.linspace(-0.15, 0.15, 25), cmap="RdBu_r", extend="both")
            ax.contour(sec["Xs"], sec["z"], Ts, levels=np.arange(4, 30, 1), colors="k", linewidths=0.4)
        clock.set_text(f"{int(hk // 24)} d {hk % 24:02.0f} h {round(hk % 1 * 60):02d} min after release")

    if a.still is not None:
        draw(int(np.argmin(abs(hours - a.still))))
        fig.savefig(a.out, dpi=a.dpi)
        print(f"wrote {a.out}")
        return

    import imageio_ffmpeg
    frames = list(range(0, nt, a.step))
    if frames[-1] != nt - 1:
        frames.append(nt - 1)
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height(physical=True)
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-r", f"{a.fps:g}", "-i", "-", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2:color=white",
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
           a.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    hold = int(round(a.fps * 1.5))
    for j, f in enumerate(frames):
        draw(f)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[..., :3].tobytes()
        for _ in range(hold if j in (0, len(frames) - 1) else 1):
            ff.stdin.write(buf)
        if j % 50 == 0:
            print(f"frame {j}/{len(frames)}", flush=True)
    ff.stdin.close(); ff.wait()
    print(f"wrote {a.out} ({Path(a.out).stat().st_size / 1e6:.1f} MB, {len(frames)} frames, {w} x {h} px)")


if __name__ == "__main__":
    main()
