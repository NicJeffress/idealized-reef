"""Surface jet head and core in the 20 km runs. Usage: jet_head.py DIR RUN [RUN ...]  (DIR/RUN.nc from extract_jet_fields.py; writes DIR/heads.npz)
For each record: head = farthest offshore v-point whose top-layer Lagrangian offshore velocity
(v + v_stokes) exceeds THR and is connected to the pass mouth; core = per row, x and speed of the
largest such velocity. Periodic in x (the field is tiled three periods for connectivity)."""
import sys, netCDF4, numpy as np
from scipy import ndimage
D = sys.argv[1]; runs = sys.argv[2:]
THR = (0.05, 0.02)
res = {}
for r in runs:
    d = netCDF4.Dataset(f"{D}/{r}.nc"); d.set_auto_mask(False)
    t = d["ocean_time"][:] / 3600
    yv = d["y_v"][:, 0]; xv = d["x_v"][0, :]
    L = len(xv) - 2
    x = np.array(d["x_rho"][0, 1:L + 1], float)  # interior columns (ghosts may be wrapped)
    jp = int(np.argmin(abs(yv - 1300)))
    el = float(d["y_rho"][-1, 0]); band = el - 4000.0  # ana_nudgcoef: el - y_rho
    heads = {thr: np.zeros(len(t)) for thr in THR}
    xhead = np.zeros(len(t)); core = np.zeros((len(t), len(yv))); xcore = core.copy()
    for k in range(len(t)):
        v = np.array(d["v_sfc"][k], float) + np.array(d["v_stokes_sfc"][k], float)
        v[np.abs(v) > 1e10] = 0
        vi = v[:, 1:L + 1]
        for thr in THR:
            m = np.tile(vi > thr, (1, 3))
            lab, n = ndimage.label(m)
            i0 = L + int(np.argmax(vi[jp]))
            c = lab[jp, i0]
            if c == 0:
                heads[thr][k] = np.nan; continue
            rows = np.flatnonzero((lab == c).any(1))
            heads[thr][k] = yv[rows.max()]
            if thr == THR[0]:
                jj = rows.max(); cols = np.flatnonzero(lab[jj] == c)
                xhead[k] = x[cols[np.argmax(np.tile(vi[jj], 3)[cols])] % L]
        ic = np.argmax(vi, 1); core[k] = vi[np.arange(len(yv)), ic]; xcore[k] = x[ic]
    res[r] = dict(t=t, yv=yv, h05=heads[0.05], h02=heads[0.02], xhead=xhead, core=core, xcore=xcore,
                  band=band, el=el)
    print(f"\n== {r}: {len(t)} records, hours {t[0]:.0f}-{t[-1]:.0f}, nudging band from {band/1e3:.2f} km, f {float(d['f'][0,0]):.3e}")
    print(" hour | head 0.05 m/s km | head 0.02 m/s km | head x km")
    for h in (2, 4, 6, 8, 12, 18, 24, 36, 48, 72, 96, 120, 144, 168):
        k = int(np.argmin(abs(t - h)))
        print(f" {t[k]:4.0f} | {res[r]['h05'][k]/1e3:6.2f} | {res[r]['h02'][k]/1e3:6.2f} | {xhead[k]/1e3:+5.2f}")
    for thr, hh in (("0.05", res[r]["h05"]), ("0.02", res[r]["h02"])):
        inb = np.flatnonzero(hh >= band)
        print(f" head {thr} first reaches band: {'hour %.1f' % t[inb[0]] if len(inb) else 'never'}; "
              f"max {np.nanmax(hh)/1e3:.2f} km at hour {t[np.nanargmax(hh)]:.1f}")
np.savez_compressed(f"{D}/heads.npz", **{f"{r}__{k}": v for r in res for k, v in res[r].items()})
