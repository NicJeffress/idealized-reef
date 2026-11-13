#!/usr/bin/env python3
"""Side-by-side GIF or movie of several runs' particles: where lagoon water goes in each.

Usage: ~/venv/bin/python -I figures/make_compare_gif.py OUT TRACK_DIR:HIS.nc:LABEL [...]
           [--xlim 3.01] [--ytop 12] [--step 4] [--tail 6] [--every 8] [--fps 10]
           [--colors 128] [--title ...] [--subtitle ...] [--width 13]
           [--movie] [--dpi 200] [--depth-max 80] [--band KM]

Each TRACK_DIR is the output of tools/reef/track_particles.py, HIS.nc any history file of
that run (grid only), LABEL the panel title ("|" starts a new line). One panel per run,
drawn as in make_profile_figure.py's GIF: bathymetry, each particle's periodic copies (the
model is one period of an endless reef), a fading tail, the same random 1 in --every
particles in every panel (the runs share the seeding), one shared clock. The panels show
the inner YTOP km from shore and +-XLIM km alongshore (3.01 km: one period).

OUT ending in .gif: an animated GIF at 100 dpi, one colour, one shared palette, unchanged
pixels transparent (small file). Also writes its last frame as a PNG.
--movie (OUT ending in .mp4): H.264 at --dpi, particles and tails coloured by depth below
mean sea level (0 to --depth-max m), with a colour bar; typically --step 1 --every 1 --fps 24.
"""
import argparse
import glob
import importlib.util
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
import netCDF4                                         # noqa: E402
import numpy as np                                     # noqa: E402
from matplotlib.collections import LineCollection      # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize  # noqa: E402

spec = importlib.util.spec_from_file_location("mpf", Path(__file__).with_name("make_profile_figure.py"))
mpf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mpf)
DEPTH = LinearSegmentedColormap.from_list("depth", matplotlib.colormaps["plasma"](np.linspace(0.95, 0.0, 256)))


def load(track_dir, ymax, period):
    """Positions (km, alongshore unwrapped, cut at the open boundary) and depth (m, positive down)."""
    X, Y, Z, S = [], [], [], []
    for f in sorted(glob.glob(str(Path(track_dir) / "chunk_*" / "out" / "track.nc"))):
        d = netCDF4.Dataset(f)
        t = np.array(d["model_time"][:], float)
        X.append(np.ma.filled(d["lon"][:], np.nan)); Y.append(np.ma.filled(d["lat"][:], np.nan))
        Z.append(np.ma.filled(d["zp"][:], np.nan)); S.append(np.ma.filled(d["status"][:], 0))
    X, Y, Z, S = (np.hstack(a).astype(float) for a in (X, Y, Z, S))
    bad = S[0] == 9
    X, Y, Z = X[:, ~bad] / 1e3, Y[:, ~bad] / 1e3, -Z[:, ~bad]
    dx = np.diff(X, axis=0)
    X = X - np.vstack([np.zeros((1, X.shape[1])), np.cumsum(np.round(dx / period) * period, axis=0)])
    hit = Y > ymax - 0.1
    first = np.where(hit.any(0), hit.argmax(0), len(t))
    for p in range(X.shape[1]):
        X[first[p] + 1:, p] = np.nan
    return (t - t[0]) / 3600, X, Y, Z


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    ap.add_argument("runs", nargs="+", help="TRACK_DIR:HIS.nc:LABEL (| in LABEL starts a new line)")
    ap.add_argument("--xlim", type=float, default=3.01)
    ap.add_argument("--ytop", type=float, default=12.0)
    ap.add_argument("--step", type=int, default=4, help="one frame every STEP records")
    ap.add_argument("--tail", type=int, default=6, help="frames in each particle's fading tail")
    ap.add_argument("--every", type=int, default=8, help="draw a random 1 in EVERY particles")
    ap.add_argument("--fps", type=float, default=10)
    ap.add_argument("--colors", type=int, default=128, help="GIF palette size")
    ap.add_argument("--width", type=float, default=13.0, help="figure width, inches")
    ap.add_argument("--movie", action="store_true", help="write an MP4, particles coloured by depth")
    ap.add_argument("--dpi", type=float, default=200, help="movie resolution (dots per inch)")
    ap.add_argument("--depth-max", type=float, default=80.0)
    ap.add_argument("--band", type=float, default=None, help="mark the start of the nudging band at BAND km")
    ap.add_argument("--title", default="Where lagoon water goes, four oceans")
    ap.add_argument("--subtitle", default="Idealized coral reef, COAWST (ROMS + SWAN) + ROMSPath particles, "
                                          "1 m waves; particles released over the back reef")
    a = ap.parse_args()

    runs = []
    for r in a.runs:
        tdir, his, lab = r.split(":", 2)
        g = netCDF4.Dataset(his)
        x = mpf.periodic_x(g["x_rho"][0, :], g["pm"][0, :]) / 1e3
        L = len(x) - 2
        period = float(x[L + 1] - x[1])
        ymax = float(g["y_rho"][-2, 0] / 1e3)
        hours, X, Y, Z = load(tdir, ymax, period)
        pid = np.arange(X.shape[1])
        K = int(np.ceil(a.xlim / period)) + 1
        X = np.hstack([X + k * period for k in range(-K, K + 1)])
        Y, Z, pid = (np.hstack([v] * (2 * K + 1)) for v in (Y, Z, pid))
        keep = np.nanmin(np.abs(X), axis=0) < a.xlim + 0.5
        runs.append(dict(g=g, period=period, hours=hours, X=X[:, keep], Y=Y[:, keep], Z=Z[:, keep],
                         pid=pid[keep], lab=lab))
    n = len(runs)
    hours = runs[0]["hours"]
    nt = min(len(r["hours"]) for r in runs)
    chosen = np.random.default_rng(1).random(max(r["pid"].max() for r in runs) + 1) < 1.0 / a.every

    left_in, right_in, gap_in, top_in, bottom_in = 0.75, (1.0 if a.movie else 0.15), 0.25, 1.15, 0.5
    pw = (a.width - left_in - right_in - gap_in * (n - 1)) / n
    ph = pw * a.ytop / (2 * a.xlim)
    W, H = a.width, ph + top_in + bottom_in
    dpi = a.dpi if a.movie else 100
    fig = plt.figure(figsize=(W, H), dpi=dpi)
    base = mpf.TRACK(0.25)
    dnorm = Normalize(0, a.depth_max)
    for i, r in enumerate(runs):
        ax = fig.add_axes([(left_in + i * (pw + gap_in)) / W, bottom_in / H, pw / W, ph / H])
        mpf.background(ax, r["g"], a.xlim, r["period"])
        ax.set_xlim(-a.xlim, a.xlim); ax.set_ylim(0, a.ytop); ax.set_aspect("equal")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=9)
        ax.set_xticks([-2, 0, 2])
        if i:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel("distance from shore (km)", fontsize=10)
        ax.set_xlabel("alongshore (km)", fontsize=9)
        ax.set_title(r["lab"].replace("|", "\n"), fontsize=10, color=mpf.INK, pad=4, linespacing=1.15)
        if a.band:
            ax.axhline(a.band, color=mpf.MUTED, lw=0.8, ls=(0, (4, 3)), zorder=2)
            ax.text(a.xlim - 0.1, a.band + 0.12, "nudging band", fontsize=7.5, color=mpf.MUTED, ha="right",
                    va="bottom", zorder=2)
        lc = LineCollection([], linewidths=0.5 if a.movie else 0.6, zorder=3); ax.add_collection(lc)
        dots = ax.scatter([], [], s=1.2 if a.movie else 2.5, c="#3b0f70", lw=0, zorder=4)
        if a.movie:
            dots.set_cmap(DEPTH); dots.set_norm(dnorm)
        r.update(lc=lc, dots=dots, gsel=np.flatnonzero(chosen[r["pid"]]))
    fig.text(left_in / W, 1 - 0.18 / H, a.title, fontsize=15, fontweight="bold", color=mpf.INK, va="top")
    fig.text(left_in / W, 1 - 0.46 / H, a.subtitle, fontsize=9, color=mpf.MUTED, va="top")
    clock = fig.text(1 - right_in / W, 1 - 0.2 / H, "", fontsize=12, color=mpf.INK, va="top", ha="right")
    if a.movie:
        cax = fig.add_axes([1 - 0.75 / W, (bottom_in + 0.15 * ph) / H, 0.14 / W, 0.7 * ph / H])
        cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=dnorm, cmap=DEPTH), cax=cax, extend="max")
        cb.ax.invert_yaxis()
        cb.set_label("particle depth (m)", color=mpf.INK, fontsize=10)
        cb.ax.tick_params(labelsize=9)
        cb.outline.set_visible(False)
    tail = a.tail * a.step

    def draw(k):
        k0 = max(0, k - tail)
        rows = np.arange(k0, k + 1, a.step)
        if rows[-1] != k:
            rows = np.append(rows, k)
        m = len(rows) - 1
        for r in runs:
            gs = r["gsel"]
            X, Y, Z = r["X"][rows][:, gs], r["Y"][rows][:, gs], r["Z"][rows][:, gs]
            if m:
                p0 = np.stack([X[:-1], Y[:-1]], -1); p1 = np.stack([X[1:], Y[1:]], -1)
                seg = np.stack([p0, p1], 2).reshape(-1, 2, 2)           # (m * particles, 2, 2)
                ok = np.isfinite(seg).all((1, 2))
                age = np.repeat((np.arange(m) + 1) / max(tail / a.step, 1), len(gs))
                alpha = np.clip(age, 0.05, 1)[ok] * 0.8
                if a.movie:
                    c = DEPTH(dnorm(0.5 * (Z[:-1] + Z[1:]).reshape(-1)[ok]))
                else:
                    c = np.tile(base, (ok.sum(), 1))
                c[:, 3] = alpha
                r["lc"].set_segments(seg[ok]); r["lc"].set_color(c)
            ok = np.isfinite(X[-1])
            r["dots"].set_offsets(np.c_[X[-1][ok], Y[-1][ok]])
            if a.movie:
                r["dots"].set_array(Z[-1][ok])
        hk = hours[k]
        clock.set_text(f"{int(hk // 24)} d {hk % 24:02.0f} h {round(hk % 1 * 60):02d} min after release" if a.movie
                       else f"{int(hk // 24)} d {hk % 24:02.0f} h after release")

    frames = list(range(0, nt, a.step))
    if frames[-1] != nt - 1:
        frames.append(nt - 1)

    if a.movie:
        import imageio_ffmpeg
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
        fig.savefig(str(Path(a.out).with_suffix(".png")), dpi=dpi)
        print(f"wrote {a.out} ({Path(a.out).stat().st_size / 1e6:.1f} MB, {len(frames)} frames, {w} x {h} px, "
              f"{(len(frames) + 2 * hold - 2) / a.fps:.0f} s)")
        return

    from PIL import Image
    rgb = []
    for f in frames:
        draw(f)
        fig.canvas.draw()
        rgb.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()))
    rgb[-1].save(str(Path(a.out).with_suffix(".png")))
    # one shared palette, no dithering, unchanged pixels transparent (as make_profile_figure.py)
    w, hgt = rgb[0].size
    keys = ["#c58b3a", mpf.INK, mpf.MUTED, "#3b0f70", matplotlib.colors.to_hex(base)]
    sheet = Image.new("RGB", (w, hgt * 4))
    for i, im in enumerate((rgb[0], rgb[len(rgb) // 2], rgb[-1])):
        sheet.paste(im, (0, i * hgt))
    for i, c in enumerate(keys):
        sheet.paste(Image.new("RGB", (w // len(keys) + 1, hgt), c), (i * (w // len(keys)), 3 * hgt))
    pal = sheet.quantize(colors=a.colors - 1, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = [np.asarray(im.quantize(palette=pal, dither=Image.Dither.NONE)) for im in rgb]
    T = a.colors - 1
    pv = (pal.getpalette() or [])[:3 * T]
    pv += [0] * (3 * T - len(pv)) + [255, 0, 255]
    out = []
    for k, arr in enumerate(idx):
        arr = arr.copy()
        if k:
            arr[arr == idx[k - 1]] = T
        im = Image.fromarray(arr, "P"); im.putpalette(pv); out.append(im)
    dur = [round(1000 / a.fps)] * len(out)
    dur[0] = 1500
    dur[-1] = 2000
    out[0].save(a.out, save_all=True, append_images=out[1:], duration=dur, loop=0, optimize=False,
                disposal=1, transparency=T)
    print(f"wrote {a.out} ({Path(a.out).stat().st_size / 1e6:.1f} MB, {len(out)} frames, {w} x {hgt} px)")


if __name__ == "__main__":
    main()
