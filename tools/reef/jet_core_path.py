"""Time-mean path and speed of the surface jet core by distance from shore.

Usage: jet_core_path.py LABEL=FILE [LABEL=FILE ...]
FILE is either a file written by extract_jet_fields.py (top-layer fields v_sfc, v_stokes_sfc)
or a merged ROMS history with 3-D v and v_stokes (the top layer is used). For each window of
run hours (24-96, 96-168) and each row, prints the alongshore position of the largest
top-layer offshore Lagrangian velocity within 3 km of the pass, and that velocity in cm/s."""
import sys, netCDF4, numpy as np
ROWS = (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 7.0, 8.0, 10.0)


def mean_v(path, h0, h1):
    d = netCDF4.Dataset(path); d.set_auto_mask(False)
    sfc = "v_sfc" in d.variables
    vs, vss = ("v_sfc", "v_stokes_sfc") if sfc else ("v", "v_stokes")
    t = d["ocean_time"][:] / 3600; k = np.flatnonzero((t >= h0) & (t <= h1))
    L = d["h"].shape[1] - 2; x = np.array(d["x_rho"][0, 1:L + 1]); yv = d["y_v"][:, 0]
    V = 0
    for i in range(0, len(k), 24):
        kk = k[i:i + 24]
        a = d[vs][kk] if sfc else d[vs][kk, -1]
        b = d[vss][kk] if sfc else d[vss][kk, -1]
        a = np.where(np.abs(a) > 1e10, 0, a); b = np.where(np.abs(b) > 1e10, 0, b)
        V = V + (a + b).sum(0)
    return x, yv, V[:, 1:L + 1] / len(k)


for arg in sys.argv[1:]:
    lab, path = arg.split("=", 1)
    for h0, h1 in ((24, 96), (96, 168)):
        x, yv, V = mean_v(path, h0, h1)
        out = []
        for y in ROWS:
            if y * 1e3 > yv[-1] - 200:
                out.append("    -    "); continue
            j = int(np.argmin(abs(yv - y * 1e3))); w = np.abs(x) < 3000
            i = np.flatnonzero(w)[np.argmax(V[j, w])]
            out.append(f"{x[i]/1e3:+4.1f}/{V[j, i]*100:4.1f}")
        print(f"{lab:18s} h{h0}-{h1}: " + " ".join(out))
print("rows (km):", ROWS, "  entries: core x (km) / top-layer offshore velocity (cm/s), time mean")
