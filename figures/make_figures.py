#!/usr/bin/env python3
"""Make the figures in figures/ from the case files in cases/.

Usage (from the repository root):
    python3 -I figures/make_figures.py [--only NAME ...]

Needs numpy, scipy, netCDF4 and matplotlib. The thin-crest grids, the canopy
patterns and the 10 m grid are generated on the fly into a temporary folder
with the scripts in tools/, so every figure comes from files anyone can
regenerate. Nothing in cases/ is changed.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import netCDF4  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap, LogNorm  # noqa: E402
from matplotlib.ticker import NullFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases"
OUT = ROOT / "figures"
A15 = CASES / "Reef_Ideal_A15"
CIRCLE = CASES / "Circle_Island"

# categorical slots (fixed order) and text inks
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
LAND = "#c9c2b0"
DPI = 110

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "lines.linewidth": 2,
    "figure.facecolor": "white", "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False,
})


def run(*args):
    subprocess.run([sys.executable, "-I", *map(str, args)], check=True,
                   stdout=subprocess.DEVNULL)


def grid(path):
    with netCDF4.Dataset(path) as g:
        return {k: np.asarray(g[k][:]) for k in ("x_rho", "y_rho", "h", "mask_rho", "pm", "pn")}


def save(fig, name):
    fig.savefig(OUT / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"{name}: {(OUT / name).stat().st_size / 1024:.0f} KB")


def depth_map(ax, g, norm, ylim=None, mesh_every=0, shading="nearest"):
    x, y = g["x_rho"] / 1000, g["y_rho"] / 1000
    h = np.ma.masked_where(g["mask_rho"] == 0, g["h"])
    ax.set_facecolor(LAND)
    pc = ax.pcolormesh(x, y, h, cmap="Blues", norm=norm, shading=shading, rasterized=True)
    if mesh_every:
        for j in range(0, x.shape[0], mesh_every):
            ax.plot(x[j], y[j], color="white", lw=0.3, alpha=0.7)
        for i in range(0, x.shape[1], mesh_every):
            ax.plot(x[:, i], y[:, i], color="white", lw=0.3, alpha=0.7)
    ax.contour(x, y, g["h"], levels=[1.0], colors=C2, linewidths=1.0)
    ax.set_aspect("equal")
    ax.grid(False)
    if ylim:
        ax.set_ylim(*ylim)
    return pc


# --------------------------------------------------------------------------
def fig_a15_bathymetry():
    g = grid(A15 / "roms_grid_default_1.nc")
    norm = LogNorm(0.5, 400)
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"width_ratios": [1, 1.3]})
    pc = depth_map(a, g, norm)
    a.set_title("Reef_Ideal_A15: whole domain")
    a.set_xlabel("x, alongshore (km; periodic)")
    a.set_ylabel("y, cross-shore (km)")
    depth_map(b, g, norm, ylim=(0, 1.8), mesh_every=2)
    b.set_xlim(-1.2, 1.2)
    b.set_title("Reef and pass (every 2nd grid line)")
    b.set_xlabel("x (km)")
    for txt, (xx, yy) in {"lagoon 10 m": (-0.9, 0.25), "backreef ~2 m": (-0.9, 0.7),
                          "crest 0.5 m": (-0.9, 1.0), "forereef": (-0.9, 1.45),
                          "pass 10 m": (0.0, 0.55)}.items():
        b.text(xx, yy, txt, color=INK, fontsize=8, ha="center",
               bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.5))
    cb = fig.colorbar(pc, ax=[a, b], shrink=0.85, pad=0.02)
    cb.set_label("depth h (m)")
    save(fig, "a15_bathymetry.png")


def fig_a15_profile():
    g = grid(A15 / "roms_grid_default_1.nc")
    y = g["y_rho"][:, 50] / 1000
    reef, pas = g["h"][:, 50], g["h"][:, 101]
    wet = g["mask_rho"][:, 50] == 1
    fig, ax = plt.subplots(2, 2, figsize=(10, 6.2))
    a, b, c, d = ax.ravel()
    for axx in (a, b):
        axx.plot(y[wet], reef[wet], color=C1, label="reef section (x = -1.2 km)")
        axx.plot(y[wet], pas[wet], color=C2, label="through the pass (x = 0)")
        axx.invert_yaxis()
        axx.set_xlabel("y, cross-shore (km)")
        axx.set_ylabel("depth (m)")
    a.set_title("Cross-reef depth profile")
    a.legend(loc="lower left")
    b.plot(y[wet], reef[wet], "o", color=C1, ms=3)
    b.set_xlim(0, 1.6)
    b.set_ylim(12, -0.3)
    b.axhspan(-0.15, 0.15, color=C4, alpha=0.25, lw=0)
    b.text(0.05, 0.05, "tide range ±0.15 m", color=INK2, fontsize=8, va="center")
    b.annotate("crest 0.50 m\n(rows 31-34)", xy=(0.97, 0.5), xytext=(1.15, 4),
               color=INK, fontsize=8, arrowprops=dict(arrowstyle="-", color=INK2))
    b.set_title("Reef zoom (dots = rho rows)")
    dy = 1 / g["pn"][:, 50]
    dx = 1 / g["pm"][50, :]
    c.plot(y, dy, color=C1)
    c.set_xlabel("y (km)")
    c.set_ylabel("dy (m)")
    c.set_title("Cross-shore spacing: 20 m at the crest, 80 m offshore")
    d.plot(g["x_rho"][50] / 1000, dx, color=C1)
    d.set_xlabel("x (km)")
    d.set_ylabel("dx (m)")
    d.set_title("Alongshore spacing: 20 m at the pass, 40 m at the seam")
    fig.tight_layout()
    save(fig, "a15_profile.png")


def fig_circle():
    g = grid(CIRCLE / "circle_grid.nc")
    x, y = g["x_rho"] / 1000, g["y_rho"] / 1000
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"width_ratios": [1, 1.2]})
    norm = LogNorm(0.8, 50)
    pc = depth_map(a, g, norm, mesh_every=4, shading="gouraud")
    a.set_xlim(-3, 3)
    a.set_ylim(-3, 3)
    a.plot([0, 0], [0.55, 3], color=C4, lw=1.5)
    a.text(0.08, 2.6, "seam", color=INK, fontsize=8,
           bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.5))
    a.set_title("Circle_Island: O-grid (every 4th line), inner 3 km")
    a.set_xlabel("x (km)")
    a.set_ylabel("y (km)")
    cb = fig.colorbar(pc, ax=a, shrink=0.85, pad=0.02)
    cb.set_label("depth h (m)")
    r = np.hypot(x[:, 5], y[:, 5]) * 1000
    wet = g["mask_rho"][:, 5] == 1
    b.plot(r[wet] / 1000, g["h"][wet, 5], "-o", color=C1, ms=2.5, lw=1.5)
    b.invert_yaxis()
    b.set_xscale("log")
    b.set_xticks([0.6, 1, 1.15, 2, 3, 5.8])
    b.set_xticklabels(["0.6", "1", "1.15", "2", "3", "5.8"])
    b.xaxis.set_minor_formatter(NullFormatter())
    b.set_xlabel("radius (km, log scale; dots = rho rings)")
    b.set_ylabel("depth (m)")
    b.set_title("Radial profile (same at every bearing)")
    b.annotate("crest 0.8 m at r = 1150 m", xy=(1.15, 0.83), xytext=(1.6, 12),
               fontsize=8, color=INK, arrowprops=dict(arrowstyle="-", color=INK2))
    b.text(0.62, 6, "lagoon 3 m", fontsize=8, color=INK)
    fig.tight_layout()
    save(fig, "circle_island_grid.png")


def fig_canopy(tmp):
    pats = [("const", "constant canopy (case default)"), ("reef", "dense on the whole reef"),
            ("zones", "by zone"), ("patchy", "patchy (~150 m patches)")]
    g = grid(A15 / "roms_grid_default_1.nc")
    x, y = g["x_rho"] / 1000, g["y_rho"] / 1000
    cmap = ListedColormap(["#f0efec", "#9fd3a0", "#1e6b1e"])
    norm = BoundaryNorm([-0.1, 0.1, 0.5, 1.0], 3)
    fig, axs = plt.subplots(2, 2, figsize=(10, 5.2), sharex=True, sharey=True)
    for ax, (p, title) in zip(axs.ravel(), pats):
        out = tmp / f"init_{p}.nc"
        run(ROOT / "tools/vegetation/make_veg_init.py", ROOT / f"tools/vegetation/patterns/{p}.json",
            "-o", out, "--case", CASES / "Reef_Ideal_A15_veg")
        with netCDF4.Dataset(out) as d:
            lam = (np.asarray(d["plant_density"][0, 0]) * np.asarray(d["plant_diameter"][0, 0])
                   * np.asarray(d["plant_height"][0, 0]))
        lam = np.ma.masked_where(g["mask_rho"] == 0, lam)
        ax.set_facecolor(LAND)
        ax.pcolormesh(x, y, lam, cmap=cmap, norm=norm, shading="nearest", rasterized=True)
        ax.contour(x, y, g["h"], levels=[1.0], colors=C2, linewidths=0.8)
        ax.set_title(f"{p}.json: {title}")
        ax.set_ylim(0, 1.8)
        ax.set_xlim(-1.5, 1.5)
        ax.set_aspect("equal")
        ax.grid(False)
    for ax in axs[1]:
        ax.set_xlabel("x (km)")
    for ax in axs[:, 0]:
        ax.set_ylabel("y (km)")
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c, ec=INK2, lw=0.4) for c in cmap.colors]
    fig.legend(handles, ["bare", "sparse: n 1 m-2, lambda_f 0.2", "dense: n 4 m-2, lambda_f 0.8"],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("Canopy patterns (tools/vegetation/patterns), frontal area lambda_f = n D h; "
                 "D 0.5 m, h 0.4 m, thickness pi/4 x D; central 3 km of 6", fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, "canopy_patterns.png")


def fig_thin_crest(tmp):
    dst = tmp / "A15_thin"
    run(ROOT / "tools/reef/make_thin_crest.py", A15, dst)
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    names = [("default_1", "default_1: 0.50 m, 4 rows", C1),
             ("thin_smooth", "thin_smooth: 0.30 m, eased flanks", C2),
             ("thin_steep", "thin_steep: 0.30 m, 2 rows, rx0 0.41", C3),
             ("steep_050", "steep_050: 0.50 m, 2 rows, rx0 0.41", C4)]
    rows = slice(25, 43)
    for n, lab, col in names:
        g = grid(dst / f"roms_grid_{n}.nc")
        ax.plot(g["y_rho"][rows, 50], g["h"][rows, 50], "-o", color=col, ms=4, label=lab)
    ax.axhline(0.15, color=INK2, lw=1, ls="--")
    ax.text(870, 0.12, "low tide (-0.15 m)", color=INK2, fontsize=8, va="bottom")
    ax.invert_yaxis()
    ax.set_ylim(6, 0)
    ax.set_xlabel("y, cross-shore (m); dots = rho rows 25-42 (20 m apart)")
    ax.set_ylabel("depth (m)")
    ax.set_title("Thin-crest variants of Reef_Ideal_A15 (reef columns; the pass is unchanged)")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    save(fig, "a15_thin_crest_profiles.png")


def zr(d, h):
    """Rest-state z of the rho levels (Vtransform 2)."""
    sc, cs, hc = np.asarray(d["sc_r"][:]), np.asarray(d["Cs_r"][:]), float(d["hc"][:])
    return h * (hc * sc + h * cs) / (hc + h)


def fig_strat_therm():
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.9), gridspec_kw={"width_ratios": [1, 1.6]})
    g = grid(A15 / "roms_grid_default_1.nc")
    j, i = np.unravel_index(np.argmax(g["h"]), g["h"].shape)
    for case, lab, col in [("Reef_Ideal_A15_veg_strat", "Reef_Ideal_A15_veg_strat (TCOEF 1.7e-4 /C)", C1),
                           ("Reef_Ideal_A15_veg_therm", "Reef_Ideal_A15_veg_therm (TCOEF 3.2e-4 /C)", C2)]:
        with netCDF4.Dataset(CASES / case / "init_reef.nc") as d:
            t = np.asarray(d["temp"][0, :, j, i])
            z = zr(d, g["h"][j, i])
        a.plot(t, z, "-o", color=col, ms=4, label=lab)
    a.set_xlabel("initial temperature (C)")
    a.set_ylabel("z (m)")
    a.set_title(f"N² = 1e-4 s⁻² at the deepest point ({g['h'][j, i]:.0f} m)")
    a.legend(loc="upper left", fontsize=8)
    hrs = np.linspace(0, 48, 961)
    hday = np.mod(hrs, 24)
    tday = hday - (12 - 0.5 * 12)
    sw = np.where((tday > 0) & (tday < 12), 1000 * np.sin(np.pi * tday / 12), 0)
    ns = np.full_like(hrs, -318.31)
    b.plot(hrs, sw, color=C4, label="shortwave, USER(6) = 1000 W/m² peak, 12 h day")
    b.plot(hrs, ns, color=C1, label="non-solar, USER(7) = -318.31 W/m²")
    b.plot(hrs, sw + ns, color=INK2, lw=1.2, ls="--", label="net (zero over a day)")
    b.set_xlabel("model hours (USER(9) = 0: start at midnight)")
    b.set_ylabel("surface heat flux (W/m²)")
    b.set_xticks(range(0, 49, 6))
    b.set_title("Reef_Ideal_A15_veg_therm: default surface forcing (ana_srflux.h, ana_stflux.h)")
    b.legend(loc="upper right", fontsize=7.5)
    b.set_ylim(-400, 1250)
    fig.tight_layout()
    save(fig, "a15_strat_therm.png")


def fig_refined(tmp):
    dst = tmp / "A15_veg_10m"
    run(ROOT / "tools/reef/refine_a15_grid.py", CASES / "Reef_Ideal_A15_veg", dst)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    norm = LogNorm(0.5, 60)
    for ax, (path, title) in zip(axs, [(A15 / "roms_grid_default_1.nc", "20 m (Reef_Ideal_A15_veg), 203 x 111"),
                                       (dst / "roms_grid_default_1.nc", "10 m (refined 2x), 404 x 220")]):
        g = grid(path)
        pc = depth_map(ax, g, norm, mesh_every=1)
        ax.set_xlim(-0.35, 0.35)
        ax.set_ylim(0.8, 1.25)
        ax.set_title(title)
        ax.set_xlabel("x (km)")
    axs[0].set_ylabel("y (km)")
    cb = fig.colorbar(pc, ax=list(axs), shrink=0.85, pad=0.02)
    cb.set_label("depth h (m)")
    save(fig, "a15_refined_10m.png")


def fig_island():
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4), gridspec_kw={"width_ratios": [1, 1, 1.25]})
    norm = LogNorm(0.5, 400)
    for a, n in zip(axs[:2], (2, 4)):
        g = grid(CASES / f"Island_A15_{n}pass" / "island_grid.nc")
        pc = depth_map(a, g, norm, shading="gouraud")
        x, y = g["x_rho"] / 1000, g["y_rho"] / 1000
        a.contour(x, y, np.where(g["mask_rho"] == 1, g["h"], 99), [1.0], colors=C2, linewidths=0.9)
        a.set_xlim(-2.6, 2.6)
        a.set_ylim(-2.6, 2.6)
        a.set_title(f"Island_A15_{n}pass: inner 2.6 km (orange: h = 1 m)")
        a.set_xlabel("x (km)")
    axs[0].set_ylabel("y (km)")
    cb = fig.colorbar(pc, ax=axs[1], shrink=0.85, pad=0.02)
    cb.set_label("depth h (m)")
    b = axs[2]
    a15 = grid(A15 / "roms_grid_default_1.nc")
    ya = a15["y_rho"][:, 0]
    b.plot(ya, a15["h"][:, 112], color=INK, lw=3, label="A15, reef")
    b.plot(ya, a15["h"][:, 101], color=INK, lw=3, ls=(0, (2, 1.5)), label="A15, pass centre")
    g = grid(CASES / "Island_A15_2pass" / "island_grid.nc")
    r = np.hypot(g["x_rho"][:, 91], g["y_rho"][:, 91]) - 600
    rp = np.hypot(g["x_rho"][:, 1], g["y_rho"][:, 1]) - 600
    b.plot(r, g["h"][:, 91], color=C2, lw=1.4, label="island, between passes")
    b.plot(rp, g["h"][:, 1], color=C1, lw=1.4, ls=(0, (2, 1.5)), label="island, pass centre")
    b.set_xlim(0, 2000)
    b.set_ylim(60, -1)
    b.set_xlabel("distance from the shore (m)")
    b.set_ylabel("depth (m)")
    b.set_title("Cross-reef profiles: A15 and the island")
    b.legend(fontsize=8)
    fig.tight_layout()
    save(fig, "island_a15_grid.png")


FIGS = {"a15_bathymetry": fig_a15_bathymetry, "a15_profile": fig_a15_profile,
        "circle": fig_circle, "canopy": fig_canopy, "thin_crest": fig_thin_crest,
        "strat_therm": fig_strat_therm, "refined": fig_refined, "island": fig_island}
NEEDS_TMP = {"canopy", "thin_crest", "refined"}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="*", choices=sorted(FIGS), help="make only these figures")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        for name in args.only or FIGS:
            f = FIGS[name]
            f(Path(td)) if name in NEEDS_TMP else f()


if __name__ == "__main__":
    main()
