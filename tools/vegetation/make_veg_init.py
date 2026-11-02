"""Write spatially varying vegetation (coral) fields into a ROMS initial file.

Usage:
  python3 -I tools/vegetation/make_veg_init.py PATTERN.json -o OUT.nc
      [--case cases/Reef_Ideal_A15_veg] [--png OUT.png]

PATTERN.json says which plant class goes where (full description in
tools/vegetation/README.md):

  {"description": "dense crest, patchy backreef",
   "classes": {"sparse": {"density": 1, "diameter": 0.5, "height": 0.4},
               "dense":  {"density": 4, "diameter": 0.5, "height": 0.4}},
   "layers": [{"where": "crest", "class": "dense"},
              {"where": "backreef",
               "patches": {"size_m": 150, "seed": 1,
                           "cover": {"dense": 0.3, "sparse": 0.3}}}]}

Everything starts bare (no plants: density, diameter, height and thickness
0). Layers are applied in order, later ones overwrite earlier ones where
they overlap. Plants are cylinders: thickness = pi/4 x diameter (project
convention), so classes give density, diameter and height only.

The case directory provides the grid (roms_grid_default_1.nc, for h, mask,
x, y, pm, pn) and the initial file whose plant fields are replaced
(init_reef.nc); everything else in it is copied unchanged. The domain is
taken as EW periodic: fields are built on the interior columns 1..Lm and
copied to the ghost columns (0 = Lm, Lm+1 = 1), because ROMS reads the
ghost columns from the file and sends columns 0..Lm to SWAN.

Closed O-grids (an island ring grid such as Circle_Island: xi runs round the
island with zero period, eta from the island outwards): give the files with --grid and
--init, and the reef crest with --crest-mask, a .npz holding the grid
script's boolean crest_g (Mm+2, Lm) over the interior columns. The crest
zone is then that mask (crest and nearshore reef are equally shallow, so
depth cannot tell them apart) and the crest line its middle row in each
column; passes and bays have no separate zone (they are lagoon or deep by
depth); patches are drawn on a plain 2-D box around the island.
"""
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import netCDF4
import numpy as np
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator

# Reef zones from depth and the side of the reef crest (see zone_map)
ZONE_DEFAULTS = {
    "crest_depth": 1.0,      # crest: h <= this (outside the pass)
    "backreef_depth": 5.0,   # landward of the crest: backreef up to this depth, lagoon below
    "forereef_depth": 20.0,  # seaward of the crest: forereef up to this depth, deep below
    "pass_excess": 1.0,      # pass: more than this deeper than the reef's typical profile
}
ZONES = ["land", "lagoon", "backreef", "crest", "forereef", "deep", "pass"]
GROUPS = {"reef": ["backreef", "crest", "forereef"],
          "all": ["lagoon", "backreef", "crest", "forereef", "deep", "pass"]}
FIELDS = ("density", "diameter", "height", "thickness")
LOW_TIDE_M = 0.17            # A15: lowest sea level in the 24 h Batch run


def load_grid(path):
    with netCDF4.Dataset(path) as g:
        grid = {k: np.ma.filled(g[k][:], np.nan).astype(float)
                for k in ("h", "mask_rho", "x_rho", "y_rho", "pm", "pn")}
    grid["area"] = 1.0 / (grid["pm"] * grid["pn"])
    x = grid["x_rho"]
    grid["period"] = float(np.mean(x[:, -1] - x[:, 1]))   # x(Lm+1) - x(1); 0 on a closed O-grid
    return grid


def periodic_ghosts(a):
    """Columns 0 and Lm+1 are copies of Lm and 1 (EW periodic)."""
    a[..., 0] = a[..., -2]
    a[..., -1] = a[..., 1]
    return a


def zone_map(grid, params, crest_mask=None):
    """Integer zone index (into ZONES) at every rho point.

    The crest line is the middle row of the shallowest band in each column;
    columns without a crest (the pass) take it from the nearest column that
    has one. The reef's typical cross-shore profile is the median depth of
    each row; cells more than pass_excess deeper are the pass. Elsewhere:
    h <= crest_depth is crest, seaward cells are forereef down to
    forereef_depth and deep below it, landward cells backreef down to
    backreef_depth and lagoon below it.

    With crest_mask (closed O-grids, see the module docstring) the crest is
    the mask and there is no pass zone.
    """
    p = {**ZONE_DEFAULTS, **params}
    unknown = set(params) - set(ZONE_DEFAULTS)
    if unknown:
        sys.exit(f"zones: unknown settings {sorted(unknown)}; known: {sorted(ZONE_DEFAULTS)}")
    h, wet = grid["h"], grid["mask_rho"] > 0.5
    ny, nx = h.shape
    if crest_mask is not None:
        return ring_zone_map(h, wet, crest_mask, p)
    hw = np.where(wet, h, np.nan)
    profile = np.full(ny, np.nan)
    has_wet = wet[:, 1:-1].any(axis=1)
    profile[has_wet] = np.nanmedian(hw[has_wet, 1:-1], axis=1)
    deeper = hw - profile[:, None] > p["pass_excess"]
    rows = np.arange(ny)[:, None]
    hmin = np.nanmin(np.where(deeper, np.nan, hw), axis=0)
    has_crest = hmin <= p["crest_depth"]
    if not has_crest.any():
        sys.exit("zones: no column is shallower than crest_depth; set zones.crest_depth")
    band = (np.abs(hw - hmin[None]) < 1e-6) & ~deeper
    crest_row = np.array([rows[band[:, i], 0].mean() if has_crest[i] else np.nan for i in range(nx)])
    have = np.where(has_crest)[0]
    for i in np.where(~has_crest)[0]:
        crest_row[i] = crest_row[have[np.argmin(np.abs(have - i))]]
    seaward = rows > crest_row[None]

    z = np.full(h.shape, ZONES.index("land"))
    z[wet & seaward] = ZONES.index("deep")
    z[wet & seaward & (h <= p["forereef_depth"])] = ZONES.index("forereef")
    z[wet & ~seaward] = ZONES.index("lagoon")
    z[wet & ~seaward & (h <= p["backreef_depth"])] = ZONES.index("backreef")
    z[wet & (h <= p["crest_depth"])] = ZONES.index("crest")
    z[wet & deeper] = ZONES.index("pass")
    return periodic_ghosts(z)


def ring_zone_map(h, wet, crest_mask, p):
    """zone_map for a closed O-grid with the crest given as a mask."""
    ny, nx = h.shape
    crest = np.zeros((ny, nx), bool)
    crest[:, 1:-1] = crest_mask
    crest = periodic_ghosts(crest) & wet
    rows = np.arange(ny)[:, None]
    has = crest.any(axis=0)
    crest_row = np.array([rows[crest[:, i], 0].mean() if has[i] else np.nan for i in range(nx)])
    have = np.where(has)[0]
    for i in np.where(~has)[0]:            # nearest column with a crest, round the ring
        d = np.abs(have - i)
        crest_row[i] = crest_row[have[np.argmin(np.minimum(d, nx - 2 - d))]]
    seaward = rows > crest_row[None]
    z = np.full(h.shape, ZONES.index("land"))
    z[wet & seaward] = ZONES.index("deep")
    z[wet & seaward & (h <= p["forereef_depth"])] = ZONES.index("forereef")
    z[wet & ~seaward] = ZONES.index("lagoon")
    z[wet & ~seaward & (h <= p["backreef_depth"])] = ZONES.index("backreef")
    z[crest] = ZONES.index("crest")
    return periodic_ghosts(z)


def select(where, zones, grid):
    """Boolean mask for a layer's "where": a zone or group name, a list of
    them, or a dict {"zone": ..., "x_m": [x0, x1], "y_m": [y0, y1],
    "depth_m": [h0, h1]} whose conditions must all hold (x ranges may
    extend past the seam: x is tested at x and x +- period)."""
    if isinstance(where, (str, list)):
        where = {"zone": where}
    unknown = set(where) - {"zone", "x_m", "y_m", "depth_m"}
    if unknown:
        sys.exit(f"where: unknown keys {sorted(unknown)}")
    mask = grid["mask_rho"] > 0.5
    if "zone" in where:
        names = [where["zone"]] if isinstance(where["zone"], str) else where["zone"]
        expanded = [z for n in names for z in GROUPS.get(n, [n])]
        bad = [n for n in expanded if n not in ZONES]
        if bad:
            sys.exit(f"where: unknown zones {bad}; zones are {ZONES[1:]}, groups {sorted(GROUPS)}")
        mask &= np.isin(zones, [ZONES.index(n) for n in expanded])
    if "x_m" in where:
        x0, x1 = where["x_m"]
        x, P = grid["x_rho"], grid["period"]
        mask &= ((x >= x0) & (x <= x1)) | ((x + P >= x0) & (x + P <= x1)) | ((x - P >= x0) & (x - P <= x1))
    if "y_m" in where:
        y0, y1 = where["y_m"]
        mask &= (grid["y_rho"] >= y0) & (grid["y_rho"] <= y1)
    if "depth_m" in where:
        h0, h1 = where["depth_m"]
        mask &= (grid["h"] >= h0) & (grid["h"] <= h1)
    return mask


def random_field(grid, size_m, seed):
    """Smooth Gaussian random field at the rho points, periodic in x.

    White noise on an auxiliary uniform grid (spacing sigma/3, exactly
    periodic in x, padded by 4 sigma in y) smoothed with a Gaussian of
    sigma = size_m / 3, then interpolated to the (stretched) ROMS grid, so
    patch sizes are in metres whatever the grid spacing.
    """
    sigma = size_m / 3.0
    step = sigma / 3.0
    x, y, P = grid["x_rho"], grid["y_rho"], grid["period"]
    if abs(P) < 1.0:                       # closed O-grid: a plain box round the island
        xa = np.arange(np.nanmin(x) - 4 * sigma, np.nanmax(x) + 4 * sigma + step, step)
        ya = np.arange(np.nanmin(y) - 4 * sigma, np.nanmax(y) + 4 * sigma + step, step)
        noise = np.random.default_rng(seed).standard_normal((ya.size, xa.size))
        f = ndimage.gaussian_filter(noise, sigma=sigma / step, mode="nearest")
        return RegularGridInterpolator((ya, xa), f)(np.stack([y, x], axis=-1))
    x0 = float(x[0, 1])
    nxa = int(np.ceil(P / step))
    xa = x0 + np.arange(nxa) * (P / nxa)
    ya = np.arange(np.nanmin(y) - 4 * sigma, np.nanmax(y) + 4 * sigma + step, step)
    noise = np.random.default_rng(seed).standard_normal((ya.size, nxa))
    f = ndimage.gaussian_filter(noise, sigma=(sigma / step, sigma / (P / nxa)), mode=("nearest", "wrap"))
    f = np.concatenate([f, f[:, :1]], axis=1)                    # x0 + P = x0
    interp = RegularGridInterpolator((ya, np.append(xa, x0 + P)), f)
    pts = np.stack([y, x0 + np.mod(x - x0, P)], axis=-1)
    return interp(pts)


def patch_classes(field, eligible, area, cover, rest):
    """Class name per eligible cell: the highest field values get the first
    class in `cover` until its area fraction is reached, the next ones the
    second class, and so on (so the second class rings the first, like the
    sparse edge of a dense patch); the remaining area gets `rest`."""
    names, fracs = list(cover), np.array(list(cover.values()), float)
    if (fracs < 0).any() or fracs.sum() > 1 + 1e-9:
        sys.exit(f"patches: cover fractions {cover} must be >= 0 and sum to at most 1")
    v, w = field[eligible], area[eligible]
    order = np.argsort(-v, kind="stable")
    cum_mid = (np.cumsum(w[order]) - 0.5 * w[order]) / w.sum()
    k = np.searchsorted(np.cumsum(fracs), cum_mid, side="right")
    labels = np.empty(v.size, dtype=object)
    labels[order] = [names[i] if i < len(names) else rest for i in k]
    return labels


def mean_patch_diameter(vegetated, area):
    """Mean equivalent diameter (m) of connected vegetated patches."""
    lab, n = ndimage.label(vegetated[:, 1:-1])
    if n == 0:
        return 0.0, 0
    a = ndimage.sum(area[:, 1:-1], lab, index=np.arange(1, n + 1))
    return float(np.mean(np.sqrt(4 * a / np.pi))), n


def build(pattern, grid, crest_mask=None):
    classes = {"bare": {"density": 0.0, "diameter": 0.0, "height": 0.0}}
    for name, c in pattern.get("classes", {}).items():
        if "thickness" in c:
            sys.exit(f"class {name}: give density, diameter and height only; "
                     "thickness is pi/4 x diameter (plants are cylinders)")
        missing = {"density", "diameter", "height"} - set(c)
        if missing or set(c) - {"density", "diameter", "height"}:
            sys.exit(f"class {name}: needs exactly density (m-2), diameter (m), height (m)")
        if c["density"] < 0 or (c["density"] > 0 and (c["diameter"] <= 0 or c["height"] <= 0)):
            sys.exit(f"class {name}: density >= 0, and diameter and height > 0 where there are plants")
        solid = np.pi / 4 * c["diameter"] ** 2 * c["density"]
        if solid >= 1:
            sys.exit(f"class {name}: plants cover {solid:.2f} of the bed (pi/4 D^2 n >= 1); "
                     "ROMS's VEG_TURB gap between plants would be zero")
        if solid > 0.8:
            print(f"warning: class {name} covers {solid:.2f} of the bed; the VEG_TURB gap between "
                  "plants shrinks as this approaches 1", file=sys.stderr)
        classes[name] = {k: float(v) for k, v in c.items()}

    zones = zone_map(grid, pattern.get("zones", {}), crest_mask)
    cls = np.full(grid["h"].shape, "bare", dtype=object)
    reports = []
    for n, layer in enumerate(pattern["layers"]):
        sel = select(layer["where"], zones, grid)
        sel[:, [0, -1]] = False                               # ghosts follow the interior
        if ("class" in layer) == ("patches" in layer):
            sys.exit(f"layer {n}: give either class or patches")
        if "class" in layer:
            if layer["class"] not in classes:
                sys.exit(f"layer {n}: unknown class {layer['class']}")
            cls[sel] = layer["class"]
            continue
        p = layer["patches"]
        unknown = set(p) - {"size_m", "seed", "cover", "rest"}
        if unknown:
            sys.exit(f"layer {n}: unknown patches keys {sorted(unknown)}")
        rest = p.get("rest", "bare")
        for c in list(p["cover"]) + [rest]:
            if c not in classes:
                sys.exit(f"layer {n}: unknown class {c}")
        if sel.any():
            f = random_field(grid, float(p["size_m"]), int(p["seed"]))
            cls[sel] = patch_classes(f, sel, grid["area"], p["cover"], rest)
            sizes = []
            for c in p["cover"]:
                d, k = mean_patch_diameter(sel & (cls == c), grid["area"])
                sizes.append(f"{c} {k} patches, {d:.0f} m")
            reports.append(f"layer {n} (size_m {p['size_m']}): mean equivalent diameter: " + "; ".join(sizes))
    cls = periodic_ghosts(cls)

    fields = {}
    for f in ("density", "diameter", "height"):
        fields[f] = np.zeros(grid["h"].shape)
        for name, c in classes.items():
            fields[f][cls == name] = c[f]
    fields["thickness"] = np.pi / 4 * fields["diameter"]
    return fields, cls, zones, classes, reports


def summary(fields, cls, zones, classes, grid):
    """Lines: per zone, area and the share of each class; mean frontal area
    lambda_f = density x diameter x height (area-weighted, bare included)."""
    inner = (slice(None), slice(1, -1))
    a = grid["area"][inner]
    lam = (fields["density"] * fields["diameter"] * fields["height"])[inner]
    names = [c for c in classes]
    out = [f"{'zone':9s} {'area ha':>8s} " + " ".join(f"{c:>8s}" for c in names) + "  lambda_f"]
    for zi, zn in enumerate(ZONES[1:], start=1):
        m = zones[inner] == zi
        if not m.any():
            continue
        A = a[m].sum()
        shares = [a[m & (cls[inner] == c)].sum() / A for c in names]
        out.append(f"{zn:9s} {A / 1e4:8.1f} " + " ".join(f"{s:8.2f}" for s in shares)
                   + f"  {np.sum(lam[m] * a[m]) / A:8.3f}")
    veg = fields["density"][inner] > 0
    if veg.any():
        depth_low = grid["h"][inner] - LOW_TIDE_M
        reach = veg & (fields["height"][inner] >= depth_low)
        out.append(f"plants reach the surface at low tide (depth h - {LOW_TIDE_M} m) on "
                   f"{a[reach].sum() / a[veg].sum():.1%} of the vegetated area")
    return out


def write(out, base, fields, cls, zones, classes, pattern):
    shutil.copy(base, out)
    with netCDF4.Dataset(out, "r+") as d:
        for f in FIELDS:
            v = d[f"plant_{f}"]
            if v.shape[-2:] != fields[f].shape or v.shape[-3] != 1:
                sys.exit(f"{base}: plant_{f} has shape {v.shape}, expected (time, 1, "
                         f"{fields[f].shape[0]}, {fields[f].shape[1]})")
            v[:] = np.broadcast_to(fields[f], v.shape)
        # Extra variables for analysis (ROMS ignores them)
        names = list(classes)
        for var, codes, meanings, long in (
                ("veg_class", np.vectorize(names.index)(cls), names, "vegetation class"),
                ("reef_zone", zones, ZONES, "reef zone")):
            if var not in d.variables:
                d.createVariable(var, "i1", d["plant_density"].dimensions[-2:])
            d[var][:] = codes
            d[var].long_name = long
            d[var].flag_values = np.arange(len(meanings), dtype="i1")
            d[var].flag_meanings = " ".join(meanings)
        d.vegetation_pattern = json.dumps(pattern)
        d.vegetation_classes = json.dumps(classes)
        d.vegetation_history = (f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%MZ} "
                                "tools/vegetation/make_veg_init.py; thickness = pi/4 x diameter")


# Sequential blue ramp (light -> dark) for frontal area; bare cells neutral gray
RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
BARE, INK, INK2 = "#e4e3df", "#0b0b0b", "#52514e"


def draw_zones(ax, grid, zones, xk, yk):
    """Thin outlines of the reef zones plus their names (identity is never
    color alone)."""
    for zi in range(1, len(ZONES)):
        m = (zones == zi).astype(float)
        if m.any():
            ax.contour(xk, yk, m, levels=[0.5], colors=INK2, linewidths=0.6)
    xc = np.nanmedian(xk[0])
    col = int(np.argmin(np.abs(xk[0] - (np.nanmin(xk) + 0.15 * (np.nanmax(xk) - np.nanmin(xk))))))
    for zi, zn in enumerate(ZONES):
        rows = np.where(zones[:, col] == zi)[0]
        if zn in ("land", "pass") or rows.size == 0:
            continue
        ax.text(xk[0, col], np.median(yk[rows, col]), zn, color=INK, fontsize=8, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    rows, cols = np.where(zones == ZONES.index("pass"))
    if rows.size:
        ax.text(xc, np.median(yk[rows, cols]), "pass", color=INK, fontsize=8, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))


def plot_pattern(png, grid, fields, cls, zones, classes, title):
    """Frontal area per bed area lambda_f = n D h on the reef, zone outlines."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    lam = fields["density"] * fields["diameter"] * fields["height"]
    reef = np.isin(zones, [ZONES.index(z) for z in ("lagoon", "backreef", "crest", "forereef", "pass")])
    rows = np.where(reef.any(axis=1) | (lam > 0).any(axis=1))[0]
    j1 = min(rows.max() + 4, lam.shape[0])
    sl = (slice(0, j1), slice(1, -1))
    xk, yk = grid["x_rho"][sl] / 1e3, grid["y_rho"][sl] / 1e3
    lmax = max(float(lam.max()), 1e-6)
    cmap = LinearSegmentedColormap.from_list("blue", RAMP)
    cmap.set_under(BARE)
    cmap.set_bad("white")
    a = np.ma.masked_where(grid["mask_rho"][sl] < 0.5, lam[sl])
    a = np.ma.where(a > 0, a, -1.0)
    fig, ax = plt.subplots(figsize=(11, 1.4 + 9.0 * (yk.max() - yk.min()) / (xk.max() - xk.min())),
                           constrained_layout=True)
    m = ax.pcolormesh(xk, yk, a, cmap=cmap, vmin=1e-9, vmax=lmax, shading="nearest")
    if abs(grid["period"]) >= 1.0:              # labels assume a straight coast
        draw_zones(ax, grid, zones[sl], xk, yk)
    else:                                       # closed O-grid: outlines only
        for zi in range(1, len(ZONES)):
            zm = (zones[sl] == zi).astype(float)
            if zm.any():
                ax.contour(xk, yk, zm, levels=[0.5], colors=INK2, linewidths=0.4)
    cb = fig.colorbar(m, ax=ax, pad=0.01, extend="min")
    cb.set_label("frontal area $\\lambda_f = n D h$", color=INK2)
    cb.ax.tick_params(colors=INK2, labelsize=8)
    ax.set_aspect("equal")
    ring = abs(grid["period"]) < 1.0           # closed O-grid: map coordinates
    ax.set_xlabel("x (km)" if ring else "alongshore x (km); periodic", color=INK2)
    ax.set_ylabel("y (km)" if ring else "cross-shore y (km)", color=INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#c3c2b7")
    veg = [f"{c}: n {v['density']:g} m$^{{-2}}$, D {v['diameter']:g} m, h {v['height']:g} m"
           for c, v in classes.items() if v["density"] > 0]
    ax.set_title(f"{title}\n" + ";  ".join(veg) + ";  gray = bare", fontsize=9, color=INK, loc="left")
    fig.savefig(png, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pattern", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=True)
    ap.add_argument("--case", type=Path, default=Path(__file__).resolve().parents[2] / "cases/Reef_Ideal_A15_veg")
    ap.add_argument("--grid", type=Path, help="ROMS grid (default CASE/roms_grid_default_1.nc)")
    ap.add_argument("--init", type=Path, help="initial file to copy (default CASE/init_reef.nc)")
    ap.add_argument("--crest-mask", type=Path, help="closed O-grid: .npz with boolean crest_g (Mm+2, Lm)")
    ap.add_argument("--png", type=Path, help="map of zones and frontal area")
    a = ap.parse_args()
    pattern = json.loads(a.pattern.read_text())
    grid = load_grid(a.grid or a.case / "roms_grid_default_1.nc")
    crest = np.load(a.crest_mask)["crest_g"].astype(bool) if a.crest_mask else None
    fields, cls, zones, classes, reports = build(pattern, grid, crest)
    write(a.out, a.init or a.case / "init_reef.nc", fields, cls, zones, classes, pattern)
    print(f"{a.out}: {pattern.get('description', a.pattern.name)}")
    for line in reports + summary(fields, cls, zones, classes, grid):
        print("  " + line)
    if a.png:
        plot_pattern(a.png, grid, fields, cls, zones, classes, pattern.get("description", a.pattern.stem))
        print(f"  figure {a.png}")


if __name__ == "__main__":
    main()
