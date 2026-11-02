"""Compare the SWAN periodic test runs (see make_inputs.py, run_tests.sh).

Usage: python3 -I compare.py RUN_DIR

Prints, for each grid, using Hs at the last output time:
  shift   periodic run with the pass across the seam vs the mid-pass run
          shifted by half a period (0 if the seam is handled like any
          interior point)
  np4     4 SWAN processes vs 1
  shadow  non-periodic vs periodic run (what lateral boundaries do)
and writes RUN_DIR/swan_periodic_test.png.
"""
import sys
from pathlib import Path

import matplotlib
import netCDF4
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

run_dir = Path(sys.argv[1])


def hs(name):
    """Hs at the last output time, (y, x); all NaN if the run has no output."""
    f = run_dir / name / "output" / "hsign.nc"
    if not f.exists():
        print(f"  ({name}: no output, run failed)")
        return np.full_like(hs("tall-rep-mid-np1") if "wide" not in name
                            else hs("wide-rep-mid-np1"), np.nan)
    with netCDF4.Dataset(f) as d:
        v = [v for v in d.variables.values() if v.ndim == 3][0]
        return np.ma.filled(v[-1].astype(float), np.nan)


def worst(a, b):
    diff = np.abs(a - b)
    if np.isnan(diff).all():
        return "n/a"
    j, i = np.unravel_index(np.nanargmax(diff), diff.shape)
    return f"max |diff| {np.nanmax(diff):.2e} m at column {i}, row {j}"


fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
for row, grid in enumerate(("tall", "wide")):
    mid1 = hs(f"{grid}-rep-mid-np1")
    shift = mid1.shape[1] // 2
    print(f"== {grid}: {mid1.shape[1]} alongshore x {mid1.shape[0]} cross-shore points")
    for np_ in (1, 4):
        seam = hs(f"{grid}-rep-seam-np{np_}")
        print(f"  shift, np{np_}: {worst(seam, np.roll(hs(f'{grid}-rep-mid-np{np_}'), -shift, axis=1))}")
    for case in ("rep-mid", "rep-seam", "norep-mid"):
        print(f"  np4 vs np1, {case}: {worst(hs(f'{grid}-{case}-np4'), hs(f'{grid}-{case}-np1'))}")
    cg = run_dir / f"{grid}-rep-mid-np1" / "output" / "hsign_compgrid.nc"
    if cg.exists():
        with netCDF4.Dataset(cg) as d:
            v = [v for v in d.variables.values() if v.ndim == 3][0]
            print(f"  COMPGRID vs frame output, rep-mid np1: "
                  f"{worst(np.ma.filled(v[-1].astype(float), np.nan), mid1)}, "
                  f"{int(np.isnan(np.ma.filled(v[-1].astype(float), np.nan)).sum())} missing")
    norep = hs(f"{grid}-norep-mid-np1")
    print(f"  shadow (norep - rep), np1: {worst(norep, mid1)}")

    panels = [
        (mid1, f"{grid}: Hs, periodic, 1 process", "viridis", None),
        (hs(f"{grid}-rep-seam-np4") - np.roll(hs(f"{grid}-rep-mid-np4"), -shift, axis=1),
         f"{grid}: seam - shifted mid, 4 processes", "RdBu_r", "sym"),
        (norep - mid1, f"{grid}: non-periodic - periodic", "RdBu_r", "sym"),
    ]
    for ax, (field, title, cmap, sym) in zip(axes[row], panels):
        lim = np.nanmax(np.abs(field)) if sym else None
        m = ax.pcolormesh(field, cmap=cmap, vmin=-lim if sym else None, vmax=lim)
        fig.colorbar(m, ax=ax, label="m")
        ax.set_title(title)
        ax.set_xlabel("alongshore index")
        ax.set_ylabel("cross-shore index")
fig.savefig(run_dir / "swan_periodic_test.png", dpi=110)
print(f"figure: {run_dir / 'swan_periodic_test.png'}")
