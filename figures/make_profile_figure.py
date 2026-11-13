#!/usr/bin/env python3
"""Hero figure (and optional GIF) for the README: where lagoon water goes.

Usage: ~/venv/bin/python -I figures/make_profile_figure.py TRACK_DIR HIS.nc OUT_STEM
           [--lat -17.5] [--every 2] [--xlim 4.5] [--images] [--gif] [--fps 10] [--step 1]
           [--gif-every N] [--intro TEXT] [--title ...] [--subtitle ...] [--ytop KM]

TRACK_DIR: output of tools/reef/track_particles.py (chunk_*/out/track.nc, run.json).
HIS.nc:    any history file of the run (grid and bathymetry only).
Writes OUT_STEM.png (200 dpi) and OUT_STEM.svg, and with --gif OUT_STEM.gif.

What is drawn:
- Bathymetry in light blues (depth on a log scale, 0.3-400 m), the reef crest
  (depth < 1 m) outlined, land-free: the shore is the bottom edge (y = 0).
- The model domain is periodic alongshore (6 km). The background is tiled once
  to each side and each particle's alongshore position is unwrapped, so a
  particle that leaves one side keeps going into the copy next to it, instead
  of jumping. The neighbouring copies are marked faintly.
- --images draws every track also shifted by one period each way, so the copies
  of the domain show the same flow (needed when particles fill the whole
  alongshore period: otherwise the copies would be empty).
- Tracks: thin lines colored by hours since release (plasma, a perceptually
  uniform map), every --every-th particle, end positions as small dots.
  A track stops for good at its first position within 100 m of the open
  north boundary (ROMSPath's open-boundary escape is not active, so particles
  there would otherwise collect along the edge).
- --ytop KM shows only the inner KM from shore (a figure window, for runs whose
  jet reaches the open boundary or its nudging band): tracks leave the frame at
  the top and may come back into it, the top edge fades out (PNG and SVG only),
  a note under the axes says how much is shown, and the figure is shortened to
  keep the axes' aspect equal.
"""
import argparse
import glob
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
import netCDF4                                         # noqa: E402
import numpy as np                                     # noqa: E402
from matplotlib.collections import LineCollection      # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize  # noqa: E402


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

INK = "#1f2a36"
MUTED = "#5b6b7a"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "svg.fonttype": "none"})
SEA = LinearSegmentedColormap.from_list("sea", ["#f3f8fb", "#d7e8f2", "#a9cbe0", "#7aa9c8"])
TRACK = matplotlib.colormaps["plasma"].resampled(256)
TRACK = LinearSegmentedColormap.from_list("plasma_cut", TRACK(np.linspace(0.0, 0.88, 256)))


def load_tracks(track_dir, ymax, period):
    X, Y, S = [], [], []
    for f in sorted(glob.glob(str(Path(track_dir) / "chunk_*" / "out" / "track.nc"))):
        d = netCDF4.Dataset(f)
        t = np.array(d["model_time"][:], float)
        X.append(np.ma.filled(d["lon"][:], np.nan))
        Y.append(np.ma.filled(d["lat"][:], np.nan))
        S.append(np.ma.filled(d["status"][:], 0))
    X, Y, S = (np.hstack(a).astype(float) for a in (X, Y, S))
    hours = (t - t[0]) / 3600
    X, Y = X / 1e3, Y / 1e3
    bad = S[0] == 9                                   # outside the grid at release
    X, Y = X[:, ~bad], Y[:, ~bad]
    # unwrap alongshore: undo each jump of more than half a period
    dx = np.diff(X, axis=0)
    X = X - np.vstack([np.zeros((1, X.shape[1])), np.cumsum(np.round(dx / period) * period, axis=0)])
    # stop at the open boundary
    hit = Y > ymax - 0.1
    first = np.where(hit.any(0), hit.argmax(0), len(hours))
    for p in range(X.shape[1]):
        X[first[p] + 1:, p] = np.nan
        Y[first[p] + 1:, p] = np.nan
    return hours, X, Y


def background(ax, g, xlim, period):
    x = periodic_x(g["x_rho"][0, :], g["pm"][0, :]) / 1e3
    y = g["y_rho"][:, 0] / 1e3
    h = np.array(g["h"][:], float)
    L = len(x) - 2
    xi, hi = x[1:L + 2], h[:, 1:L + 2]                # one period plus the seam column (x[L+1] = x[1] + period)
    norm = LogNorm(0.3, 400)
    for k in (-1, 0, 1):
        ax.pcolormesh(xi + k * period, y, hi, cmap=SEA, norm=norm, shading="gouraud", rasterized=True, zorder=0)
        ax.contour(xi + k * period, y, hi, levels=[1.0], colors=["#c58b3a"], linewidths=1.0, zorder=1)
    for s in (-period / 2, period / 2):
        if abs(s) < xlim:
            ax.axvline(s, color=MUTED, lw=0.6, ls=(0, (2, 4)), alpha=0.6, zorder=1)
    return y[-2]


def label(ax, x, y, text, **kw):
    ax.text(x, y, text, color=kw.pop("color", INK), fontsize=kw.pop("fontsize", 12), zorder=6,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75), **kw)


def fade_top(ax, xlim, ytop, depth=0.3):
    """A white fade over the top `depth` km: the window cuts the domain here."""
    a = np.linspace(0, 0.95, 64)[:, None] ** 1.5
    rgba = np.ones((64, 1, 4))
    rgba[..., 3] = a
    ax.imshow(rgba, extent=(-xlim, xlim, ytop - depth, ytop), origin="lower", aspect="auto",
              interpolation="bilinear", zorder=5)


def frame(ax, xlim, ymax):
    ax.set_xlim(-xlim, xlim)
    ax.set_ylim(0, ymax)
    ax.set_aspect("equal")
    ax.set_xlabel("alongshore (km)")
    ax.set_ylabel("distance from shore (km)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("tracks", type=Path)
    ap.add_argument("his", type=Path)
    ap.add_argument("out")
    ap.add_argument("--lat", type=float, default=-17.5)
    ap.add_argument("--every", type=int, default=2)
    ap.add_argument("--xlim", type=float, default=4.5)
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--fps", type=float, default=10, help="GIF frames per second (one frame per record)")
    ap.add_argument("--intro", default=None,
                    help="GIF: text shown over the release positions before the particles move "
                         "(default from the seeding; '' for none)")
    ap.add_argument("--intro-s", type=float, default=2.0, help="GIF: seconds the intro is held")
    ap.add_argument("--step", type=int, default=1, help="GIF: one frame every STEP records (long runs)")
    ap.add_argument("--tail", type=int, default=8, help="GIF: frames in each particle's fading tail")
    ap.add_argument("--colors", type=int, default=128, help="GIF: palette size")
    ap.add_argument("--gif-every", type=int, default=None,
                    help="GIF: draw every N-th particle (default --every); larger N, smaller file")
    ap.add_argument("--images", action="store_true",
                    help="also draw each track's periodic copies at +-1 period (for edge-to-edge seeding)")
    ap.add_argument("--title", default="Where lagoon water goes: a wave-driven jet bent by Earth's rotation")
    ap.add_argument("--subtitle", default=None)
    ap.add_argument("--jet-label", type=float, nargs=2, default=None, metavar=("X", "Y"),
                    help="where to put the 'jet' label (km); default: near the median track end")
    ap.add_argument("--ytop", type=float, default=None,
                    help="figure window: show only the inner YTOP km from shore (default: the whole domain)")
    a = ap.parse_args()

    g = netCDF4.Dataset(a.his)
    x = periodic_x(g["x_rho"][0, :], g["pm"][0, :]) / 1e3
    L = len(x) - 2
    period = float(x[L + 1] - x[1])
    ymax = float(g["y_rho"][-2, 0] / 1e3)
    hours, X, Y = load_tracks(a.tracks, ymax, period)
    pid = np.arange(X.shape[1])                        # particle number, the same in every copy
    if a.images:                                       # the model is one period of an endless reef
        X = np.hstack([X - period, X, X + period])
        Y = np.hstack([Y, Y, Y])
        pid = np.hstack([pid, pid, pid])
        keep = np.nanmin(np.abs(X), axis=0) < a.xlim + 0.5
        X, Y, pid = X[:, keep], Y[:, keep], pid[keep]
    run = json.loads((a.tracks / "run.json").read_text()) if (a.tracks / "run.json").exists() else {}
    sub = a.subtitle or (f"Idealized coral reef, COAWST (ROMS + SWAN) with particle tracking (ROMSPath), "
                         f"1 m waves, {abs(a.lat):g}°{'S' if a.lat < 0 else 'N'}")
    sel = np.arange(0, X.shape[1], a.every)
    norm = Normalize(0, hours[-1])
    top = min(a.ytop, ymax) if a.ytop else ymax

    def sized(w, left, right, top_in, bottom_in):
        """Figure height for equal axes aspect with the window: fixed inch margins."""
        if not a.ytop:
            return None
        return (right - left) * w * top / (2 * a.xlim) + top_in + bottom_in

    H = sized(10, 0.08, 0.9, 0.87, 0.68) or 6.2
    fig, ax = plt.subplots(figsize=(10, H))
    fig.subplots_adjust(left=0.08, right=0.9, top=1 - 0.87 / H, bottom=0.68 / H)
    background(ax, g, a.xlim, period)
    segs, cols = [], []
    for p in sel:
        ok = np.isfinite(X[:, p])
        pts = np.c_[X[ok, p], Y[ok, p]]
        if len(pts) < 2:
            continue
        segs.extend(np.stack([pts[:-1], pts[1:]], 1))
        cols.extend(0.5 * (hours[ok][:-1] + hours[ok][1:]))
    # tracks and dots are rasterized inside the SVG (at 200 dpi), text and axes stay vector:
    # thousands of multi-day tracks as vector paths would make a 100 MB file
    lc = LineCollection(segs, cmap=TRACK, norm=norm, linewidths=0.45, alpha=0.8, zorder=3, rasterized=True)
    lc.set_array(np.array(cols))
    ax.add_collection(lc)
    last = np.array([np.flatnonzero(np.isfinite(X[:, p]))[-1] for p in sel])
    ax.scatter(X[last, sel], Y[last, sel], s=2.5, c=hours[last], cmap=TRACK, norm=norm, lw=0, zorder=4, rasterized=True)
    if a.ytop:
        fade_top(ax, a.xlim, top)
    frame(ax, a.xlim, top)
    label(ax, -a.xlim + 0.15, 0.22, "lagoon")
    label(ax, -a.xlim + 0.15, 1.05, "reef crest", color="#8a5a1c")
    label(ax, 0.15, 0.62, "pass")
    label(ax, -2.6, top - 0.4, "open ocean", color=MUTED)
    jx, jy = a.jet_label or (float(np.nanmedian(X[last, sel])), float(np.nanmedian(Y[last, sel])))
    label(ax, jx + 0.2, min(jy, top - 0.6), "jet", fontweight="bold")
    if a.xlim > period / 2:
        for sgn in (-1, 1):
            ax.text(sgn * (period / 2 + a.xlim) / 2, top - 0.12, "model domain\nrepeats", color=MUTED,
                    fontsize=9, va="top", ha="center", zorder=6, linespacing=1.1,
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.75) if a.ytop else None)
    if a.ytop:
        ax.text(1.0, -0.115, f"inner {top:g} of {ymax:.1f} km shown", transform=ax.transAxes, ha="right",
                va="top", fontsize=9.5, color=MUTED)
    cax = fig.add_axes([0.915, 0.68 / H + 0.15 * (1 - 1.55 / H), 0.015, 0.7 * (1 - 1.55 / H)] if a.ytop
                       else [0.915, 0.2, 0.015, 0.55])
    cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=TRACK), cax=cax)
    cb.set_label("hours since release", color=INK)
    cb.outline.set_visible(False)
    fig.text(0.08, 1 - 0.28 / H, a.title, fontsize=17, fontweight="bold", color=INK, va="top")
    fig.text(0.08, 1 - 0.59 / H, sub, fontsize=11.5, color=MUTED, va="top")
    fig.savefig(a.out + ".png", dpi=200)
    fig.savefig(a.out + ".svg", dpi=200)
    print(f"wrote {a.out}.png/.svg: {len(sel)} of {X.shape[1]} tracks, {hours[-1]:.1f} h, "
          f"{run.get('seeding', '?')} seeding")

    if a.gif:
        H2 = sized(8.3, 0.08, 0.98, 0.73, 0.62) or 5.2
        fig2, ax2 = plt.subplots(figsize=(8.3, H2), dpi=100)
        fig2.subplots_adjust(left=0.08, right=0.98, top=1 - 0.73 / H2, bottom=0.62 / H2)
        background(ax2, g, a.xlim, period)
        frame(ax2, a.xlim, top)
        if a.ytop:                                     # no fade here: its gradient takes palette colours
            ax2.text(1.0, -0.115, f"inner {top:g} of {ymax:.1f} km shown", transform=ax2.transAxes,
                     ha="right", va="top", fontsize=8.5, color=MUTED)
        label(ax2, -a.xlim + 0.15, 0.22, "lagoon")
        label(ax2, -a.xlim + 0.15, 1.05, "reef crest", color="#8a5a1c")
        tail = a.tail * a.step                         # records in the fading tail (8 frames: 2 h at 15 min)
        # a random subset (a regular every-N-th pick draws stripes in the release grid),
        # chosen by particle so the periodic copies show the same particles
        n = a.gif_every or a.every
        chosen = np.random.default_rng(1).random(pid.max() + 1) < 1.0 / n
        gsel = np.flatnonzero(chosen[pid])
        lc2 = LineCollection([], linewidths=0.6, zorder=3)
        ax2.add_collection(lc2)
        dots = ax2.scatter([], [], s=3, c="#3b0f70", lw=0, zorder=4)
        clock = ax2.text(0.98, 0.97, "", transform=ax2.transAxes, ha="right", va="top", fontsize=12, color=INK,
                         zorder=7, bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.8))
        fig2.text(0.08, 1 - 0.234 / H2, "Where lagoon water goes", fontsize=15, fontweight="bold", color=INK,
                  va="top")
        fig2.text(0.08, 1 - 0.494 / H2, sub, fontsize=8.5, color=MUTED, va="top")
        base = TRACK(0.25)

        seeding = run.get("seeding", "")
        intro = a.intro if a.intro is not None else {
            "backreef": "Particles released over the whole back reef",
            "lagoon": "Particles released in the lagoon and back reef",
            "domain": "Particles released over the whole domain"}.get(seeding, "")
        note = ax2.text(0.5, 0.55, intro, transform=ax2.transAxes, ha="center", va="center", fontsize=15,
                        color=INK, zorder=8, visible=False,
                        bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=MUTED, lw=0.8, alpha=0.92))

        def draw(f):
            k = max(f, 0)                             # f = -1: the intro (release positions, text shown)
            note.set_visible(f < 0 and bool(intro))
            k0 = max(0, k - tail)
            segs, alphas = [], []
            for p in gsel:
                xs, ys = X[k0:k + 1:a.step, p], Y[k0:k + 1:a.step, p]
                for m in range(len(xs) - 1):
                    if np.isfinite(xs[m:m + 2]).all():
                        segs.append([(xs[m], ys[m]), (xs[m + 1], ys[m + 1])])
                        alphas.append((m + 1) / (tail / a.step))
            lc2.set_segments(segs)
            c = np.tile(base, (len(segs), 1))
            c[:, 3] = np.clip(alphas, 0.05, 1) * 0.8
            lc2.set_color(c)
            ok = np.isfinite(X[k, gsel])
            dots.set_offsets(np.c_[X[k, gsel][ok], Y[k, gsel][ok]])
            hk = hours[k]
            clock.set_text(f"{hk:4.1f} h after release" if hours[-1] <= 36 else
                           f"{int(hk // 24)} d {hk % 24:02.0f} h after release")
            return lc2, dots, clock, note

        # one shared palette, no dithering: the background is then identical from frame to
        # frame and the GIF stores little more than the moving particles
        from PIL import Image
        frames = [-1] if intro else []
        frames += list(range(0, len(hours), a.step))
        if frames[-1] != len(hours) - 1:
            frames.append(len(hours) - 1)
        rgb = []
        for f in frames:
            draw(f)
            fig2.canvas.draw()
            rgb.append(Image.fromarray(np.asarray(fig2.canvas.buffer_rgba())[..., :3].copy()))
        w, hgt = rgb[0].size
        # three sample frames plus solid swatches of the line colors, so thin lines such as
        # the crest outline keep their own palette entries
        keys = ["#c58b3a", "#8a5a1c", INK, MUTED, "#3b0f70", matplotlib.colors.to_hex(base)]
        sheet = Image.new("RGB", (w, hgt * 4))
        for i, im in enumerate((rgb[0], rgb[len(rgb) // 2], rgb[-1])):
            sheet.paste(im, (0, i * hgt))
        for i, c in enumerate(keys):
            sheet.paste(Image.new("RGB", (w // len(keys) + 1, hgt), c), (i * (w // len(keys)), 3 * hgt))
        # one entry is kept free for transparency: after the first frame, every pixel that is
        # the same as in the frame before is written transparent (the earlier frame shows
        # through, disposal 1), so each frame stores little more than the moving particles
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
            im = Image.fromarray(arr, "P")
            im.putpalette(pv)
            out.append(im)
        dur = [round(1000 / a.fps)] * len(out)
        if intro:
            dur[0] = round(1000 * a.intro_s)
        dur[-1] = 1500
        out[0].save(a.out + ".gif", save_all=True, append_images=out[1:], duration=dur, loop=0,
                    optimize=False, disposal=1, transparency=T)
        print(f"wrote {a.out}.gif ({Path(a.out + '.gif').stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
