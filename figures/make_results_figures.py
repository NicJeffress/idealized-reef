#!/usr/bin/env python3
"""Make the results figures in figures/ (results_*.png) from the notebook.

Usage (from the repository root):
    python3 -I figures/make_results_figures.py [--only NAME ...]

The numbers are those recorded in the notebook entries (notebook/*.md) and in
the CSV tables next to them; each figure's docstring names its sources. The
cross-reef depth profile comes from cases/Reef_Ideal_A15_veg. Needs numpy,
matplotlib and netCDF4. Nothing in cases/ or notebook/ is changed.
"""
import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import netCDF4  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebook"
OUT = ROOT / "figures"
A15_VEG = ROOT / "cases" / "Reef_Ideal_A15_veg"

# the same categorical slots and inks as make_figures.py (validated palette)
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
DPI = 110

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "lines.linewidth": 2,
    "figure.facecolor": "white", "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False,
})


def save(fig, name):
    fig.savefig(OUT / name, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"{name}: {(OUT / name).stat().st_size / 1024:.0f} KB")


def read_csv(name):
    """notebook CSV (metric column, one column per member) -> {metric: {member: value}}."""
    with open(NOTEBOOK / name, newline="") as f:
        rows = list(csv.reader(f))
    members = rows[0][1:]
    return {r[0]: {m: float(v) for m, v in zip(members, r[1:])} for r in rows[1:]}


def label_bars(ax, bars, fmt, horizontal=False, pad=0.01, inside_frac=None):
    for b in bars:
        if horizontal:
            w = b.get_width()
            x = w + (pad if w >= 0 else -pad)
            ax.text(x, b.get_y() + b.get_height() / 2, fmt(w), va="center",
                    ha="left" if w >= 0 else "right", fontsize=7.5, color=INK)
        else:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h, fmt(h), ha="center",
                    va="bottom", fontsize=7.5, color=INK)


# --------------------------------------------------------------------------
def fig_ladder():
    """What moves the lagoon set-up and the cross-crest transport.

    Percent differences between 24 h runs (hours 12-24) from the notebook:
    spread-30 entry (triads, directions, frequencies), results/README.md and
    the triads-on and density-1 entries (canopies), wave-streaming, roller
    checks, density-1 (breaking, TKE_WAVEDISS), grid-10m, vertical-resolution,
    results p0-p2 (bottom-stress cap, implicit stress).
    """
    # (label, set-up %, crest transport %, kind)
    rows = [
        ("Triads off (SWAN TRIAD), density-1 canopy", -58, -37, "physics"),
        ("Dense canopy (4 per m2) instead of bare", -94, -85, "physics"),
        ("Density-1 canopy instead of bare", -71, -60, "physics"),
        ("Wave streaming, bottom + canopy", +95, +32, "physics"),
        ("Wave streaming, bottom only", +57, +22, "physics"),
        ("Reniers roller, WEC_ALPHA 0.5", +25, +15, "physics"),
        ("30 deg spread + TKE_WAVEDISS + 34 freq. (vs 4 deg swell)", -31, -17, "physics"),
        ("Breaking BKD instead of CON 0.73", +8, +7, "physics"),
        ("TKE_WAVEDISS + ZOS_HSIG", -9, -5, "physics"),
        ("Breaking TG instead of CON 0.73", -3, -2, "physics"),
        ("Bottom-stress cap LIMIT_BSTRESS (bare reef)", +15, +8, "numerics"),
        ("10 m grid instead of 20 m", -16, -11, "numerics"),
        ("20 vertical levels instead of 10", -10, +3, "numerics"),
        ("15 vertical levels instead of 10", -7, +2, "numerics"),
        ("36 SWAN directions instead of 72 (30 deg spread)", -3, -2, "numerics"),
        ("20 SWAN frequencies instead of 34", -3, -2, "numerics"),
        ("Implicit bottom stress (bare reef)", +0.4, 0.0, "numerics"),
        ("DT 3 s instead of 6 s", -0.1, 0.0, "numerics"),
        ("Coupling every 240 s instead of 600 s", +0.1, +0.1, "numerics"),
    ]
    col = {"physics": C1, "numerics": C2}
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 6.6), sharey=True,
                               gridspec_kw={"width_ratios": [1, 1]})
    y = np.arange(len(rows))[::-1]
    for ax, idx, title in [(a, 1, "lagoon set-up"), (b, 2, "cross-crest transport")]:
        vals = [r[idx] for r in rows]
        bars = ax.barh(y, vals, color=[col[r[3]] for r in rows], height=0.62)
        ax.axvline(0, color=INK2, lw=0.8)
        label_bars(ax, bars, lambda v: f"{v:+.0f} %" if abs(v) >= 1 else f"{v:+.1f} %",
                   horizontal=True, pad=1.5)
        ax.set_title(f"Change in {title}")
        ax.set_xlabel("percent of the reference run")
        ax.set_xlim(-135, 125)
        ax.grid(axis="y", visible=False)
    a.set_yticks(y)
    a.set_yticklabels([r[0] for r in rows], fontsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=col[k]) for k in ("physics", "numerics")]
    fig.legend(handles, ["physics choice", "numerical choice"], loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("What moves the reef circulation: 24 h runs of Reef_Ideal_A15_veg, hours 12-24, "
                 "each against its own reference run (notebook, November 2026)", fontsize=9, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    save(fig, "results_what_moves_setup.png")


# --------------------------------------------------------------------------
def fig_wave_budget():
    """Where the waves lose their energy across the reef, and which share
    pushes water. Dissipation by zone (W per metre of reef, alongshore mean,
    end of the 24 h density-1 run) from the wave-streaming entry; depth from
    the band grid of cases/Reef_Ideal_A15_veg (reef column).
    """
    zones = [("lagoon and\nback reef", 0, 950, 83, 5, 34),
             ("crest", 950, 1050, 741, 1545, 476),
             ("top of the\nfore reef", 1050, 1150, 520, 94, 542),
             ("fore-reef slope,\noffshore", 1150, 1600, 63, 0, 38)]
    with netCDF4.Dataset(A15_VEG / "roms_grid_default_1.nc") as g:
        y = np.asarray(g["y_rho"][:, 50])
        h = np.asarray(g["h"][:, 50])
        wet = np.asarray(g["mask_rho"][:, 50]) == 1
    fig, (a, b) = plt.subplots(2, 1, figsize=(8.5, 6.4), gridspec_kw={"height_ratios": [1, 1.3]})
    a.fill_between(y[wet], -h[wet], -30, color="#dfe9f5", lw=0)
    a.plot(y[wet], -h[wet], color=INK, lw=1.5)
    shade = ["#f0efec", "#fde6d9", "#dff3ea", "#f0efec"]
    for (name, y0, y1, *_), c, yt in zip(zones, shade, (1.2, 1.2, -29, 1.2)):
        a.axvspan(y0, y1, color=c, alpha=0.8, lw=0, zorder=0)
        a.text((y0 + y1) / 2, yt, name.replace("\n", " "), ha="center", va="bottom", fontsize=7.5, color=INK2)
    a.set_xlim(0, 1600)
    a.set_ylim(-30, 4)
    a.set_ylabel("z (m)")
    a.set_xlabel("distance from the shore (m)")
    a.set_title("Cross-reef profile of Reef_Ideal_A15 (reef section) and the four zones", loc="left")
    a.grid(False)
    names = [z[0] for z in zones]
    fric = np.array([z[3] for z in zones], float)
    brk = np.array([z[4] for z in zones], float)
    veg = np.array([z[5] for z in zones], float)
    x = np.arange(len(zones))
    w = 0.55
    gap = 8
    b.bar(x, brk, w, color=C1, label="breaking (always forces the flow)")
    b.bar(x, fric, w, bottom=brk + gap, color=C2, label="bottom friction (forces the flow only with BOTTOM_STREAMING)")
    b.bar(x, veg, w, bottom=brk + fric + 2 * gap, color=C3, label="canopy (only with VEG_STREAMING)")
    for i in range(len(zones)):
        tot = brk[i] + fric[i] + veg[i]
        share = 100 * (fric[i] + veg[i]) / tot
        b.text(x[i], tot + 2 * gap + 40, f"{tot:.0f} W/m\n{share:.0f} % not breaking",
               ha="center", va="bottom", fontsize=7.5, color=INK)
    b.set_xticks(x)
    b.set_xticklabels(names, fontsize=8)
    b.set_ylabel("wave energy dissipated (W per metre of reef)")
    b.set_ylim(0, 3400)
    b.set_title("Wave energy lost in each zone, by process (density-1 canopy, 24 h)", loc="left")
    b.legend(loc="upper right", fontsize=7.5)
    b.grid(axis="x", visible=False)
    fig.text(0.01, -0.01,
             "Over the whole reef about 40 % of the dissipation is breaking, 34 % bottom friction and 26 % canopy. "
             "Giving the mean flow the momentum of the non-breaking 60 % (the two streaming options, A15 defaults\n"
             "since 2026-11-03) nearly doubles the lagoon set-up (14 to 28 mm) and raises the crest transport by a third. "
             "Source: notebook/2026-11-03_wave-streaming.md.",
             fontsize=7.5, color=INK2, va="top")
    fig.tight_layout()
    save(fig, "results_wave_budget.png")


# --------------------------------------------------------------------------
def fig_canopy_triads():
    """The canopy and SWAN's triads set the size of the circulation.

    24 h runs of Reef_Ideal_A15_veg on the 20 m grid, hours 12-24, defaults
    of 2026-11-02 (4-degree swell, 20 frequencies): bare reef and dense
    canopy from the triads-on entry, density-1 canopy from the density-1
    entry (the "no triads" members of each, or the unpatched runs).
    """
    canopies = ["bare reef", "density 1 per m2\n(frontal area 0.2)", "dense, 4 per m2\n(frontal area 0.8)"]
    setup = {"triads on": [62.0, 18.2, 3.90], "triads off": [42.3, 7.1, 0.70]}
    crest = {"triads on": [1396, 563, 203], "triads off": [1127, 343, 62]}
    jet = {"triads on": [0.83, 0.29, 0.10], "triads off": [0.73, 0.19, 0.036]}
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.9))
    x = np.arange(3)
    w = 0.36
    for ax, data, title, fmt in [(axs[0], setup, "lagoon set-up (mm)", lambda v: f"{v:.3g}"),
                                 (axs[1], crest, "cross-crest transport (m3/s per 6 km of reef)", lambda v: f"{v:.0f}"),
                                 (axs[2], jet, "crest jet, max depth-mean speed (m/s)", lambda v: f"{v:.2g}")]:
        b1 = ax.bar(x - w / 2 - 0.02, data["triads on"], w, color=C1, label="triads on (SWAN fix)")
        b2 = ax.bar(x + w / 2 + 0.02, data["triads off"], w, color=C2, label="triads off (as COAWST v3.9 ran)")
        label_bars(ax, b1, fmt)
        label_bars(ax, b2, fmt)
        ax.set_yscale("log")
        ax.set_xticks(x)
        ax.set_xticklabels(canopies, fontsize=8)
        ax.set_title(title, fontsize=9)
        ax.grid(axis="x", visible=False)
        lo, hi = min(min(v) for v in data.values()), max(max(v) for v in data.values())
        ax.set_ylim(lo / 1.6, hi * 2.2)
    axs[0].legend(loc="upper right", fontsize=7.5)
    fig.suptitle("Canopy density and SWAN's triad interactions set the size of the reef circulation "
                 "(log scale; 24 h runs, hours 12-24, 20 m grid, 4-degree swell)", fontsize=9, color=INK2)
    fig.tight_layout()
    save(fig, "results_canopy_triads.png")


# --------------------------------------------------------------------------
def fig_roller():
    """The Reniers roller: linear in WEC_ALPHA, larger on the refined grid.
    Numbers from the roller-checks entry (20 m grid sweep and the
    breaking-zone grid pair), density-1 canopy, defaults of 2026-11-03.
    """
    alpha = np.array([0, 0.25, 0.5, 1.0])
    series = [("lagoon set-up", [0, 12, 25, 50], C1, 32),
              ("cross-crest transport", [0, 8, 15, 30], C2, 19),
              ("pass transport", [0, 6, 13, 25], C3, 16),
              ("crest jet (max)", [0, 5, 11, 21], C4, 13)]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for name, v, c, band in series:
        ax.plot(alpha, v, "-o", color=c, ms=6, label=name)
        ax.text(1.02, v[-1], name, color=INK, fontsize=8, va="center")
        ax.plot([0.5], [band], marker="s", ms=8, mfc="white", mec=c, mew=2, ls="none")
    ax.plot([], [], marker="s", ms=8, mfc="white", mec=INK2, mew=2, ls="none",
            label="breaking-zone grid (10 m rows), WEC_ALPHA 0.5")
    ax.set_xlim(-0.03, 1.32)
    ax.set_ylim(-3, 56)
    ax.set_xticks(alpha)
    ax.set_xlabel("WEC_ALPHA: share of the breaking dissipation that feeds the roller")
    ax.set_ylabel("change against no roller (%)")
    ax.set_title("The surface roller moves breaking momentum shoreward: its effect is linear in WEC_ALPHA\n"
                 "and larger once the breaking zone is resolved (A15 default: 0.5)", fontsize=9)
    ax.legend(loc="upper left", fontsize=7.5)
    fig.text(0.01, -0.02, "20 m grid unless marked; density-1 canopy, 24 h, hours 12-24. The breaking dissipation "
             "itself is unchanged (within 1 %). Source: notebook/2026-11-03_roller-checks.md.",
             fontsize=7.5, color=INK2, va="top")
    fig.tight_layout()
    save(fig, "results_roller.png")


# --------------------------------------------------------------------------
def fig_resolution():
    """Grid convergence across the shore and in the vertical.
    Horizontal: grid-10m entry (20 m, breaking-zone grid, uniform 10 m;
    density-1 canopy, 4-degree swell). Vertical: the vertical-resolution CSV
    (band grid, roller, density-1 canopy; N 20 at DT 3 s, which it needs).
    """
    v = read_csv("2026-11-03_vertical-resolution.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    # horizontal
    labels = ["20 m\n(203 x 111)", "breaking-zone grid\n(203 x 126; 10 m rows\n850-1150 m from shore)", "uniform 10 m\n(404 x 220)"]
    setup = np.array([18.2, 15.4, 15.3])
    crest = np.array([563, 522, 500])
    cost = [1.0, 1.16, 8.0]
    x = np.arange(3)
    a.plot(x, 100 * setup / setup[0], "-o", color=C1, ms=7, label="lagoon set-up")
    a.plot(x, 100 * crest / crest[0], "-o", color=C2, ms=7, label="cross-crest transport")
    for i in range(3):
        a.text(x[i], 100 * setup[i] / setup[0] - 2.2, f"{setup[i]:.1f} mm", ha="center", va="top", fontsize=7.5, color=INK)
        a.text(x[i], 100 * crest[i] / crest[0] + 1.2, f"{crest[i]:.0f} m3/s", ha="center", va="bottom", fontsize=7.5, color=INK)
        a.text(x[i], 78.5, f"cost x{cost[i]:.3g}", ha="center", fontsize=7.5, color=INK2)
    a.set_xticks(x)
    a.set_xticklabels(labels, fontsize=7.5)
    a.set_ylabel("percent of the coarsest grid")
    a.set_title("Across the shore: the 20 m grid under-resolves\nthe 2-3 cell breaking zone", fontsize=9)
    a.legend(loc="upper right", fontsize=7.5)
    a.set_xlim(-0.4, 2.4)
    # vertical
    mem = ["N10", "N15", "N20-DT3"]
    su = np.array([v["set-up mean (mm)"][m] for m in mem])
    ct = np.array([v["crest transport (m3/s)"][m] for m in mem])
    wall = np.array([v["wall s per sim h"][m] for m in mem])
    b.plot(x, 100 * su / su[0], "-o", color=C1, ms=7, label="lagoon set-up")
    b.plot(x, 100 * ct / ct[0], "-o", color=C2, ms=7, label="cross-crest transport")
    for i in range(3):
        b.text(x[i], 100 * su[i] / su[0] - 2.2, f"{su[i]:.1f} mm", ha="center", va="top", fontsize=7.5, color=INK)
        b.text(x[i], 100 * ct[i] / ct[0] + 1.2, f"{ct[i]:.0f} m3/s", ha="center", va="bottom", fontsize=7.5, color=INK)
        b.text(x[i], 78.5, f"cost x{wall[i] / wall[0]:.3g}", ha="center", fontsize=7.5, color=INK2)
    b.set_xticks(x)
    b.set_xticklabels(["10 levels\n(5 cm layers on the crest)", "15 levels\n(A15 default)", "20 levels\n(needs DT 3 s)"], fontsize=7.5)
    b.set_title("In the vertical: the set-up falls with more levels,\nthe transport rises slightly", fontsize=9)
    b.set_xlim(-0.4, 2.4)
    a.set_ylim(76, 110)
    fig.suptitle("Grid convergence of Reef_Ideal_A15_veg (density-1 canopy, 24 h, hours 12-24). "
                 "Sources: notebook/2026-11-03_grid-10m.md, 2026-11-03_vertical-resolution.csv",
                 fontsize=9, color=INK2)
    fig.tight_layout()
    save(fig, "results_resolution.png")


# --------------------------------------------------------------------------
def fig_mixing():
    """Vertical mixing: the GLS TKE floor at rest and when heated, and the
    turbulence closures. Left: the GLS_Kmin-at-rest entry (medians after
    24 h at rest, stratified case). Middle: the kmin-heated-72h CSV (day 3).
    Right: the turbulence-closure CSV / entry (heated case, 24 h).
    """
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.2))
    zones = ["lagoon and\nback reef", "fore reef", "offshore"]
    x = np.arange(3)
    # at rest
    rest76 = [7.4e-4, 5.1e-5, 4.7e-5]
    rest8 = [5.1e-6, 5.1e-6, 5.1e-6]
    w = 0.36
    b1 = axs[0].bar(x - w / 2 - 0.02, rest76, w, color=C1, label="GLS_Kmin 7.6e-6 (ROMS's k-epsilon suggestion)")
    b2 = axs[0].bar(x + w / 2 + 0.02, rest8, w, color=C2, label="GLS_Kmin 1e-8 (A15 default)")
    axs[0].set_title("At rest (no waves, no tide): the TKE floor\nis the mixing, most in the shallow lagoon", fontsize=9)
    # heated day 3
    k = read_csv("2026-11-03_kmin-heated-72h.csv")
    h76 = [k[m]["Kmin 7.6e-6"] for m in ("lagoon AKt median day 3 (m2/s)", "forereef AKt median day 3 (m2/s)", "offshore AKt median day 3 (m2/s)")]
    h8 = [k[m]["Kmin 1e-8"] for m in ("lagoon AKt median day 3 (m2/s)", "forereef AKt median day 3 (m2/s)", "offshore AKt median day 3 (m2/s)")]
    b3 = axs[1].bar(x - w / 2 - 0.02, h76, w, color=C1)
    b4 = axs[1].bar(x + w / 2 + 0.02, h8, w, color=C2)
    axs[1].set_title("Heated, waves and tide, day 3: on the reef the flow\nmakes its own turbulence; offshore the floor shows", fontsize=9)
    for ax, bars in [(axs[0], (b1, b2)), (axs[1], (b3, b4))]:
        for bb in bars:
            label_bars(ax, bb, lambda v: f"{v:.1e}".replace("e-0", "e-"))
    # closures (heated case, VEG_TURB off except the last)
    clos = ["k-epsilon\nKantha-Clayson", "k-epsilon\nCanuto-A", "k-omega\nCanuto-A", "gen\nCanuto-A", "k-epsilon KC\n+ VEG_TURB\n(default)"]
    lag = [1.6e-3, 1.3e-3, 6.9e-6, 6.8e-4, 1.7e-3]
    flat = [3.4e-3, 3.1e-3, 2.2e-3, 2.0e-3, 5.5e-3]
    top = [2.3e-3, 1.7e-3, 3.4e-4, 1.4e-3, 2.9e-3]
    xc = np.arange(5)
    wc = 0.26
    axs[2].bar(xc - wc - 0.02, lag, wc, color=C1, label="lagoon")
    axs[2].bar(xc, flat, wc, color=C2, label="reef flat and crest")
    axs[2].bar(xc + wc + 0.02, top, wc, color=C3, label="top of the fore reef")
    axs[2].set_xticks(xc)
    axs[2].set_xticklabels(clos, fontsize=7)
    axs[2].set_title("Turbulence closure (heated, 24 h): k-epsilon and gen\nagree within 5-10 % in the flow; k-omega is odd", fontsize=9)
    axs[2].legend(loc="upper left", fontsize=7)
    for ax in axs:
        ax.set_yscale("log")
        ax.set_ylim(2e-6, 3e-2)
        ax.grid(axis="x", visible=False)
    axs[2].set_ylim(2e-6, 1e-1)
    for ax in axs[:2]:
        ax.set_xticks(x)
        ax.set_xticklabels(zones, fontsize=8)
    axs[0].set_ylabel("vertical eddy diffusivity AKt, median (m2/s)")
    axs[0].legend(loc="upper right", fontsize=7)
    fig.suptitle("Vertical mixing on the stratified and heated reef (Reef_Ideal_A15_veg_strat, _veg_therm). "
                 "Sources: notebook/2026-11-03_gls-kmin-at-rest.md, _kmin-heated-72h.csv, _turbulence-closure.md",
                 fontsize=9, color=INK2)
    fig.tight_layout()
    save(fig, "results_mixing.png")


FIGS = {"ladder": fig_ladder, "wave_budget": fig_wave_budget, "canopy_triads": fig_canopy_triads,
        "roller": fig_roller, "resolution": fig_resolution, "mixing": fig_mixing}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="*", choices=sorted(FIGS), help="make only these figures")
    args = ap.parse_args()
    for name in args.only or FIGS:
        FIGS[name]()


if __name__ == "__main__":
    main()
