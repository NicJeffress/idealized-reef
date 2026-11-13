"""Time-mean (run hours in the file) cross-shore Lagrangian velocity v + v_stokes against depth at rows
offshore of the crest, alongshore mean over the crest (|x| > XP km from the pass). Usage: crest_inflow_profile.py HIS..."""
import sys, netCDF4, numpy as np
XP = 0.4
ROWS = (0.97, 1.05, 1.15, 1.3, 1.5, 2.0)
for path in sys.argv[1:]:
    d = netCDF4.Dataset(path); d.set_auto_mask(False)
    yv = d["y_v"][:, 0]; L = d["h"].shape[1] - 2
    x = np.array(d["x_rho"][0, 1:L + 1]) / 1e3
    w = np.abs(x) > XP
    js = [int(np.argmin(abs(yv - y * 1e3))) for y in ROWS]
    nt = len(d["ocean_time"])
    V = np.zeros((len(js), len(d["s_rho"]), L)); Zm = np.zeros(d["zeta"].shape[1:])
    for k0 in range(0, nt, 48):
        kk = slice(k0, min(nt, k0 + 48))
        for a, j in enumerate(js):
            v = d["v"][kk, :, j, 1:L + 1] + d["v_stokes"][kk, :, j, 1:L + 1]
            V[a] += np.where(np.abs(v) > 1e10, 0, v).sum(0)
    V /= nt
    h = d["h"][:]; hc = float(d["hc"][:]); Cs = d["Cs_r"][:]; s = d["s_rho"][:]
    print(f"\n== {path.split('/')[-2]}  (alongshore mean over |x| > {XP} km; cm/s, + offshore)")
    for a, j in enumerate(js):
        hv = 0.5 * (h[j, 1:L + 1] + h[j + 1, 1:L + 1])[w].mean()
        z = hv * (hc * s + hv * Cs) / (hc + hv)
        vp = V[a][:, w].mean(1) * 100
        dz = np.diff(np.r_[-hv, 0.5 * (z[1:] + z[:-1]), 0.0])
        q = vp / 100 * dz
        on = np.clip(q, None, 0); tot_on = on.sum()
        top5 = on[z > -5].sum() / tot_on * 100 if tot_on < 0 else np.nan
        topH = on[z > -0.3 * hv].sum() / tot_on * 100 if tot_on < 0 else np.nan
        prof = " ".join(f"{zz:6.1f}:{vv:+5.1f}" for zz, vv in list(zip(z, vp))[::-1][::2])
        print(f" y {ROWS[a]:.2f} km, h {hv:5.1f} m: net {q.sum()*1e3:+6.1f} L/s/m, onshore {tot_on*1e3:6.1f} L/s/m, "
              f"share of onshore in top 5 m {top5:4.0f}%, top 30% of depth {topH:4.0f}%\n    z:v {prof}")
