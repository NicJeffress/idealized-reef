"""Make thin-crest variants of the Reef_Ideal_A15 grid (ROMS grid .nc + SWAN .bot).

    python -I make_thin_crest.py CASE_SRC CASE_DST

Copies CASE_SRC to CASE_DST and adds, next to the default grid (crest 0.50 m,
flat over 60 m: the 20 m grid's rows 31-34, flank rx0 0.34):
  thin_smooth   crest at 0.30 m over the same 60 m, flanks eased over 140 m
                either side so the slope factor rx0 stays about 0.3
  thin_steep    0.30 m crest 20 m wide, 0.71 m 20 m either side of it (on the
                20 m grid rx0 0.41: a narrow two-row crest, like a realistic
                reef grid that failed)
  steep_050     0.50 m crest 20 m wide, 1.19 m either side (rx0 0.41 on the
                20 m grid, the default depth): steepness alone

Each variant is a depth profile against the cross-shore distance from the
crest centre, in metres (PROFILES below: the 20 m grid's rows 29-39 at their
offsets from the centre of its crest). The crest is found by depth, not by
row number: the reef columns are those whose shallowest wet point is less
than 0.6 m deep (the pass is deeper and stays untouched); the crest centre is
the midpoint between the two places where the median depth over the reef
columns crosses 1 m, landward and seaward of the shallowest row. Each point
of the profile goes to the row nearest its offset, and rows between two
profile points take the linear interpolation in y; rows beyond the ends keep
their depth. On the 20 m grid (203 x 111, before 2026-11-03) every profile
point has its own row and the grids are those of the 2026-11-02 tests, bit
for bit; on the breaking-zone grid (10 m rows from 850 to 1150 m from the
shore) the rows in between are interpolated. rx0 is a per-cell number, so
the "steep" variants are less steep per cell on 10 m rows (rx0 0.26 and 0.37
instead of 0.41): the profile is the same, the numerical difficulty is not.
"""
import shutil
import sys
from pathlib import Path

import numpy as np
from netCDF4 import Dataset

# cross-shore offset from the crest centre (m) -> depth (m); the 20 m grid's rows
# 29-39 sit at offsets -70, -50, ..., 130 (row 32.5 = the centre of rows 31-34)
PROFILES = {
    "thin_smooth": ([-70, -50, -30, -10, 10, 30, 50, 70, 90, 110, 130],
                    [1.0, 0.55, 0.30, 0.30, 0.30, 0.30, 0.55, 1.0, 1.7, 2.8, 4.3]),
    "thin_steep": ([-30, -10, 10, 30], [0.71, 0.30, 0.30, 0.71]),
    "steep_050": ([-30, -10, 10, 30], [1.19, 0.50, 0.50, 1.19]),
}
REEF_DEPTH = 0.6    # a column is reef (not pass) if its shallowest wet point is above this
FLANK_DEPTH = 1.0   # the crest centre is midway between the flanks' crossings of this depth


def find_crest(h, mask, y):
    """Reef columns (bool over i), the shallowest row and the crest centre's y (m)."""
    hw = np.where(mask == 1, h, np.inf)
    reef = hw.min(axis=0) < REEF_DEPTH
    if not reef.any():
        sys.exit(f"no reef columns: no wet point shallower than {REEF_DEPTH} m")
    med = np.median(hw[:, reef], axis=1)
    jmin = int(np.argmin(med))

    def crossing(step):
        j = jmin
        while 0 <= j + step < len(med) and med[j + step] < FLANK_DEPTH:
            j += step
        k = j + step
        f = (FLANK_DEPTH - med[j]) / (med[k] - med[j])
        return y[j] + f * (y[k] - y[j])

    yc = 0.5 * (crossing(-1) + crossing(+1))
    return reef, jmin, yc


def main(src, dst):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    with Dataset(dst / "roms_grid_default_1.nc") as g:
        h0 = np.ma.filled(g["h"][:], 0.0)
        mask = np.ma.filled(g["mask_rho"][:], 0)
        y = np.ma.filled(g["y_rho"][:, 0], 0.0)
    reef, jmin, yc = find_crest(h0, mask, y)
    cols = np.flatnonzero(reef)
    i0 = cols[len(cols) // 4]
    print(f"reef columns: {reef.sum()} of {len(reef)}; shallowest row {jmin} (y {y[jmin]:.0f} m, "
          f"{h0[jmin, i0]:.2f} m at i={i0}); crest centre y {yc:.0f} m")
    for name, (off, dep) in PROFILES.items():
        variant(dst, name, h0, reef, y - yc, np.array(off, float), np.array(dep, float), i0)


def variant(dst, name, h0, reef, dy, off, dep, i0):
    h = h0.copy()
    rows = np.array([int(np.argmin(np.abs(dy - o))) for o in off])
    if len(set(rows)) < len(rows):
        sys.exit(f"{name}: two profile points fall on the same row; the grid is coarser than the profile")
    for j in range(rows.min(), rows.max() + 1):
        h[j, reef] = np.interp(dy[j], dy[rows], dep)
    gf = dst / f"roms_grid_{name}.nc"
    shutil.copy(dst / "roms_grid_default_1.nc", gf)
    with Dataset(gf, "a") as g:
        g["h"][:] = h
        if "hraw" in g.variables:
            g["hraw"][0] = h
    b = np.loadtxt(dst / "swan_bathy_default_1.bot")
    w = b < 9000
    b[w] = h[w]
    np.savetxt(dst / f"swan_bathy_{name}.bot", b, fmt="%15.8f")
    rx = np.abs(h[1:] - h[:-1]) / (h[1:] + h[:-1])
    j0, j1 = rows.min() - 1, rows.max() + 2
    print(f"{name}: rows {j0}-{j1 - 1} at i={i0} {np.round(h[j0:j1, i0], 2)}; "
          f"rx0 max {rx.max():.3f} (those rows: {rx[j0:j1 - 1].max():.3f})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python -I make_thin_crest.py CASE_SRC CASE_DST")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
