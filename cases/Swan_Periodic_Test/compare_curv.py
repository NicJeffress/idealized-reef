"""Compare the curvilinear periodic SWAN test runs (make_curv_inputs.py,
run_curv_tests.sh).

Usage: python3 -I compare_curv.py RUN_DIR

All checks use the last output time (1 h). Prints:
  same grid     curvilinear copy of the uniform grid vs the regular grid
  shift         str-seam (seam through the pass) vs str-mid rolled by half
                a period (0 if the seam is handled like an interior point)
  np4           4 SWAN processes vs 1
  uniform       flat reef: largest alongshore range of Hs and FORCE in any
                row (0 if every column, the seam included, is the same)
  search        FRAME and POINTS output (located by CVMESH, also across the
                seam and periods away) vs bilinear interpolation of the
                COMPGRID output
  old build     runs repeated with the build without swan-periodic-curvilinear (if present)
  bad period    str-badper must stop with an error
and writes RUN_DIR/swan_periodic_curv.png.
"""
import sys
from pathlib import Path

import matplotlib
import netCDF4
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

run_dir = Path(sys.argv[1])


def field(run, fname="hsign.nc", var=None):
    """(y, x) field at the last output time, NaN where masked."""
    f = run_dir / run / "output" / fname
    if not f.exists():
        return None
    with netCDF4.Dataset(f) as d:
        if var is None:
            v = [v for v in d.variables.values() if v.ndim == 3][0]
        else:
            v = d.variables[var]
        return np.ma.filled(v[-1].astype(float), np.nan)


def worst(a, b):
    if a is None or b is None:
        return "n/a (run failed)"
    if a.shape != b.shape:
        return f"shapes differ {a.shape} {b.shape}"
    diff = np.abs(a - b)
    if np.isnan(diff).all():
        return "n/a"
    if np.nanmax(diff) == 0 and np.array_equal(np.isnan(a), np.isnan(b)):
        return "identical"
    j, i = np.unravel_index(np.nanargmax(diff), diff.shape)
    return f"max |diff| {np.nanmax(diff):.2e} at column {i}, row {j}"


def along_range(a):
    """Largest max-min along x over all rows, and where."""
    if a is None:
        return "n/a (run failed)"
    r = np.nanmax(a, axis=1) - np.nanmin(a, axis=1)
    j = int(np.nanargmax(r))
    scale = np.nanmax(np.abs(a[j]))
    return f"{r[j]:.2e} (row {j}, values ~{scale:.3g})"


print("== same grid: uniform 20 m grid, curvilinear vs regular (1 process)")
for q in ("hsign.nc", "dir.nc", "dissip.nc"):
    print(f"  {q:10s} {worst(field('uni-crv-mid-np1', q), field('uni-reg-mid-np1', q))}")

print("== shift: str-seam vs str-mid rolled by half a period")
mid1 = field("str-mid-np1")
n = mid1.shape[1]
for np_ in (1, 4):
    seam, mid = field(f"str-seam-np{np_}"), field(f"str-mid-np{np_}")
    print(f"  np{np_}: {worst(seam, None if mid is None else np.roll(mid, -n // 2, axis=1))}")

print("== np4 vs np1")
for case in ("str-mid", "str-seam", "str-flat"):
    print(f"  {case:9s} {worst(field(f'{case}-np4'), field(f'{case}-np1'))}")
for q in ("xfor", "yfor"):
    print(f"  str-flat {q}: {worst(field('str-flat-np4', 'force.nc', q), field('str-flat-np1', 'force.nc', q))}")

print("== uniform: flat reef, largest alongshore range in a row")
for case in ("str-flat-np1", "str-flat-np4", "uni-reg-flat-np1", "uni-reg-flat-np1-old"):
    if not (run_dir / case).exists():
        continue
    print(f"  {case:20s} Hs {along_range(field(case))}")
    for q in ("xfor", "yfor"):
        print(f"  {'':20s} {q} {along_range(field(case, 'force.nc', q))}")

a15 = field("a15-mid-np1")
if a15 is not None:
    na = a15.shape[1]
    print(f"== Reef_Ideal_A15 grid and bathymetry ({na} x {a15.shape[0]} points)")
    for np_ in (1, 4):
        seam, mid = field(f"a15-seam-np{np_}"), field(f"a15-mid-np{np_}")
        print(f"  shift, np{np_}: "
              f"{worst(seam, None if mid is None else np.roll(mid, -(na // 2), axis=1))}")
    print(f"  np4 vs np1: {worst(field('a15-mid-np4'), a15)}")
    a15n = field("a15-norep-np1")
    if a15n is not None:
        print(f"  shadow (norep - rep): {worst(a15n[:, :na], a15)}")

print("== shadow: str-norep vs str-mid (first columns)")
norep = field("str-norep-np1")
if norep is not None:
    print(f"  {worst(norep[:, :n], mid1)}")

print("== search: FRAME/POINTS vs bilinear interpolation of COMPGRID output")
d = run_dir / "str-search-np1"
coords = np.loadtxt(d / "coord.grd")
ny = coords.shape[0] // 2
xs, ys = coords[0], coords[ny:, 0]          # rectilinear: x per column, y per row
period = xs[-1] - xs[0]


def interp(F, xp, yp):
    """Bilinear in index space (= SWAN's for a rectilinear grid), periodic
    in x; F has n columns, column n is column 0 again."""
    Fc = np.concatenate([F, F[:, :1]], axis=1)
    xw = xs[0] + np.mod(xp - xs[0], period)
    i = np.clip(np.searchsorted(xs, xw, side="right") - 1, 0, n - 1)
    j = np.clip(np.searchsorted(ys, yp, side="right") - 1, 0, ny - 2)
    tx = (xw - xs[i]) / (xs[i + 1] - xs[i])
    ty = (yp - ys[j]) / (ys[j + 1] - ys[j])
    return ((1 - tx) * (1 - ty) * Fc[j, i] + tx * (1 - ty) * Fc[j, i + 1]
            + (1 - tx) * ty * Fc[j + 1, i] + tx * ty * Fc[j + 1, i + 1])


frm = field("str-search-np1", "hsign_frm.nc")
grid_s = field("str-search-np1")
print(f"  str-search COMPGRID vs str-mid: {worst(grid_s, mid1)}")
if frm is not None:
    with open(d / "swan.in") as f:
        line = [l for l in f if l.startswith("FRAME")][0].split()
    fx0, fy0, flen, fylen, fmx, fmy = (float(line[2]), float(line[3]), float(line[5]),
                                       float(line[6]), int(line[7]), int(line[8]))
    fx, fy = np.meshgrid(fx0 + np.arange(fmx + 1) * flen / fmx, fy0 + np.arange(fmy + 1) * fylen / fmy)
    lin = interp(mid1, fx, fy)
    sq = np.sqrt(interp(mid1 ** 2, fx, fy))
    print(f"  FRAME over 2 periods, {frm.size} points, {int(np.isnan(frm).sum())} missing")
    print(f"    vs interpolated Hs:   {worst(frm, lin)}")
    print(f"    vs interpolated Hs^2: {worst(frm, sq)}")
    print(f"    vs its own copy one period on: {worst(frm[:, :fmx // 2], frm[:, fmx // 2:fmx])}")
tab = d / "output" / "pts.tab"
if tab.exists():
    pts = np.loadtxt(d / "points.txt")
    out = np.loadtxt(tab)[-len(pts):]
    sq = np.sqrt(interp(mid1 ** 2, pts[:, 0], pts[:, 1]))
    lin = interp(mid1, pts[:, 0], pts[:, 1])
    print("  POINTS: x, y, Hs (SWAN), Hs (interpolated Hs^2), Hs (interpolated Hs)")
    for p, o, s, li in zip(pts, out, sq, lin):
        print(f"    {p[0]:10.2f} {p[1]:8.2f}  {o[2]:.5f}  {s:.5f}  {li:.5f}")

old = sorted(p.name for p in run_dir.glob("*-old"))
if old:
    print("== old build (without swan-periodic-curvilinear) vs new")
    for o in old:
        new = o[:-4]
        for q in ("hsign.nc", "dir.nc", "dissip.nc"):
            print(f"  {new:18s} {q:10s} {worst(field(new, q), field(o, q))}")
        if (run_dir / o / "output" / "force.nc").exists():
            for q in ("xfor", "yfor"):
                print(f"  {new:18s} {q:10s} {worst(field(new, 'force.nc', q), field(o, 'force.nc', q))}")

print("== bad period: str-badper")
log = (run_dir / "str-badper-np1" / "log.txt").read_text(errors="replace")
prt = "".join(p.read_text(errors="replace") for p in (run_dir / "str-badper-np1").glob("PRINT*"))
msg = [l.strip() for l in (log + prt).splitlines() if "REPeating curvilinear" in l]
print(f"  messages: {msg[:3]}")
print(f"  Hs output written: {field('str-badper-np1') is not None}")

fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
panels = [
    (mid1, "str-mid: Hs, periodic, stretched grid", "viridis", False),
    (field("str-seam-np4") - np.roll(field("str-mid-np4"), -n // 2, axis=1),
     "str-seam - rolled str-mid, 4 processes", "RdBu_r", True),
    (norep[:, :n] - mid1 if norep is not None else mid1 * np.nan,
     "non-periodic - periodic", "RdBu_r", True),
    (field("uni-crv-mid-np1") - field("uni-reg-mid-np1"),
     "uniform grid: curvilinear - regular", "RdBu_r", True),
]
X, Y = np.meshgrid(xs[:n], ys)
for ax, (f, title, cmap, sym) in zip(axes.flat, panels):
    if "uniform grid" in title:
        m = ax.pcolormesh(f, cmap=cmap, vmin=-1e-6, vmax=1e-6)
        ax.set_xlabel("alongshore index")
        ax.set_ylabel("cross-shore index")
    else:
        lim = np.nanmax(np.abs(f)) if sym else None
        if sym and not lim:
            lim = 1e-12
        m = ax.pcolormesh(X, Y, f, cmap=cmap, vmin=-lim if sym else None, vmax=lim, shading="nearest")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
    fig.colorbar(m, ax=ax, label="m")
    ax.set_title(title)
fig.savefig(run_dir / "swan_periodic_curv.png", dpi=110)
print(f"figure: {run_dir / 'swan_periodic_curv.png'}")
