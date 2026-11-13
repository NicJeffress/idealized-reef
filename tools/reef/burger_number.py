#!/usr/bin/env python3
"""Deformation radius, Burger and Rossby numbers of the pass jet, and eddy sizes, per run.

Usage: ~/venv/bin/python -I tools/reef/burger_number.py LABEL=FIELDS.nc [...] [--hours 48 168]
           [--tcoef 1.7e-4] [--f-other -4.39e-5] [--smooth 250] [--min-area 0.2]

FIELDS.nc: a run's file from tools/reef/extract_jet_fields.py (top-layer fields at every
record, full-depth sections at 2.5, 5, 10 and 15 km from shore). Over the run hours given,
every hour:

Jet, at the 2.5 and 5 km sections (instantaneous, then the median over time):
  core   the column with the largest top-layer offshore Lagrangian velocity (v + v_stokes)
         within 3 km of the pass; U is that velocity;
  H      jet thickness: depth at which the core's offshore velocity falls to half its
         top-layer value;
  W      jet width: full width over which the velocity averaged over the top H is above
         half its core value;
  N      ambient buoyancy frequency over the top H: from the temperature step between the
         surface and depth H, averaged over the columns more than 1 km from the core
         (N^2 = g * tcoef * dT/dz; linear equation of state, temperature only);
  Rd     = N H / |f|, the deformation radius of a jet that thick in that stratification;
  Bu     = (Rd / W)^2 at the jet's own width; Ro = U / (|f| W).
Eddies, from the top-layer Lagrangian velocity between 1.5 and 12 km from shore, every 2 h,
  interpolated to a uniform 50 m grid and smoothed (Gaussian, --smooth m): Okubo-Weiss
  W_ow = s_n^2 + s_s^2 - zeta^2; eddy cores are connected regions (periodic alongshore) with
  W_ow < -0.2 standard deviations of W_ow; radius = sqrt(area / pi); regions under
  --min-area km^2 dropped. Reported: median and area-weighted mean radius, count,
  share that are anticyclonic (zeta of the sign opposite to f; f = 0: none defined).
Bu at the eddy scale uses Rd from the 2.5 km section and L = eddy radius.
--f-other also prints Rd at another Coriolis parameter (default 17.5 S) for the same N and H.
"""
import argparse

import netCDF4
import numpy as np
from scipy import ndimage

G = 9.81


def rd(v, k):
    a = np.array(v[k], float)
    a[np.abs(a) > 1e10] = 0.0
    return a


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--hours", type=float, nargs=2, default=(48, 168))
    ap.add_argument("--tcoef", type=float, default=1.7e-4)
    ap.add_argument("--f-other", type=float, default=-4.3856e-5)
    ap.add_argument("--smooth", type=float, default=250.0, help="Gaussian smoothing of the surface velocity, m")
    ap.add_argument("--min-area", type=float, default=0.2, help="smallest eddy core kept, km^2")
    a = ap.parse_args()
    rows = []
    for spec in a.runs:
        lab, path = spec.rsplit("=", 1)
        d = netCDF4.Dataset(path); d.set_auto_mask(False)
        t = np.array(d["ocean_time"][:]) / 3600
        ks = [int(np.argmin(abs(t - h))) for h in np.arange(a.hours[0], a.hours[1] + 0.1, 1.0)]
        L = d["h"].shape[1] - 2
        x = np.array(d["x_rho"][0, 1:L + 1], float)
        dx = 1 / np.array(d["pm"][0, 1:L + 1], float)
        f = float(d["f"][0, 0])
        hc = float(d["hc"][:]); Cs = np.array(d["Cs_r"][:]); s = np.array(d["s_rho"][:])
        out = {"run": lab, "f": f}
        for js, tag in ((0, "2.5"), (1, "5")):
            jv = int(d["jsec_v"][js]); jr = int(d["jsec_rho"][js])
            hv = float(0.5 * (d["h"][jv, 1:L + 1] + d["h"][jv + 1, 1:L + 1]).mean())
            z = hv * (hc * s + hv * Cs) / (hc + hv)                 # bottom to top, negative
            Us, Hs, Ws, Ns = [], [], [], []
            for k in ks:
                V = rd(d["v_sec"], k)[:, js, 1:L + 1] + rd(d["v_stokes_sec"], k)[:, js, 1:L + 1]
                T = rd(d["temp_sec"], k)[:, js, 1:L + 1]
                w = np.abs(x) < 3000
                ic = np.flatnonzero(w)[np.argmax(V[-1, w])]
                U = V[-1, ic]
                if U < 0.03:
                    continue
                prof = V[:, ic]
                below = np.flatnonzero(prof < 0.5 * U)
                below = below[below < len(z) - 1]
                if not len(below):
                    continue
                kb = below[-1]                                        # deepest-upward first level below half
                H = -np.interp(0.5 * U, [prof[kb], prof[kb + 1]], [z[kb], z[kb + 1]])
                top = z > -H
                vm = (V[top] * 1).mean(0) if top.any() else V[-1]
                half = vm > 0.5 * vm[ic]
                lab_, _ = ndimage.label(half)
                W = dx[lab_ == lab_[ic]].sum()
                far = np.abs(x - x[ic]) > 1000
                Tz = T[:, far].mean(1)
                dT = Tz[-1] - np.interp(-H, z, Tz)
                N = np.sqrt(max(G * a.tcoef * dT / H, 0.0))
                Us.append(U); Hs.append(H); Ws.append(W); Ns.append(N)
            if not Us:
                continue
            U, H, W, N = (float(np.median(v)) for v in (Us, Hs, Ws, Ns))
            Rd = N * H / abs(f) if f else np.inf
            out[tag] = dict(U=U, H=H, W=W, N=N, Rd=Rd, Bu=(Rd / W) ** 2 if f else np.inf,
                            Ro=U / (abs(f) * W) if f else np.inf, Rd_other=N * H / abs(a.f_other), n=len(Us))
        # eddies (Okubo-Weiss on the top-layer Lagrangian velocity, interpolated to a uniform
        # 50 m grid and smoothed with a Gaussian of --smooth m, so the measure sees the
        # kilometre-scale eddies rather than the small vortices on the jet's edges)
        y = np.array(d["y_rho"][:, 0], float)
        P = float(x[-1] - x[0] + dx[-1])
        gx = np.arange(0, P, 50.0) + x[0]
        gy = np.arange(1500.0, 12000.0 + 1, 50.0)
        sig = a.smooth / 50.0
        out["eddy"] = {}
        for k in ks[::2]:
            u = rd(d["u_sfc"], k) + rd(d["u_stokes_sfc"], k)
            v = rd(d["v_sfc"], k) + rd(d["v_stokes_sfc"], k)
            ur = np.zeros(d["h"].shape); vr = np.zeros(d["h"].shape)
            ur[:, 1:-1] = 0.5 * (u[:, 1:] + u[:, :-1]); vr[1:-1] = 0.5 * (v[1:] + v[:-1])
            ur, vr = ur[:, 1:L + 1], vr[:, 1:L + 1]
            U2 = np.array([np.interp(gx, x, row, period=P) for row in ur])
            V2 = np.array([np.interp(gx, x, row, period=P) for row in vr])
            U2 = np.array([np.interp(gy, y, col) for col in U2.T]).T
            V2 = np.array([np.interp(gy, y, col) for col in V2.T]).T
            if sig > 0:
                U2 = ndimage.gaussian_filter(U2, sig, mode=("nearest", "wrap"))
                V2 = ndimage.gaussian_filter(V2, sig, mode=("nearest", "wrap"))
            ux = (np.roll(U2, -1, 1) - np.roll(U2, 1, 1)) / 100.0
            vx = (np.roll(V2, -1, 1) - np.roll(V2, 1, 1)) / 100.0
            uy = np.gradient(U2, 50.0, axis=0); vy = np.gradient(V2, 50.0, axis=0)
            zeta = vx - uy
            ow = (ux - vy) ** 2 + (vx + uy) ** 2 - zeta ** 2
            core = ow < -0.2 * ow.std()
            nx = len(gx)
            lab_, _ = ndimage.label(np.tile(core, (1, 3)))
            mid = lab_[:, nx:2 * nx]
            for c in np.unique(mid[mid > 0]):
                m = mid == c
                A = m.sum() * 2500.0
                if A < a.min_area * 1e6:
                    continue
                out["eddy"].setdefault("r", []).append(np.sqrt(A / np.pi))
                out["eddy"].setdefault("A", []).append(A)
                if f:
                    out["eddy"].setdefault("anti", []).append(np.sign(zeta[m].mean()) != np.sign(f))
        r_ = np.array(out["eddy"].get("r", [])); A_ = np.array(out["eddy"].get("A", []))
        an = out["eddy"].get("anti", [])
        out["eddy"] = dict(med=float(np.median(r_)) if len(r_) else np.nan,
                           wmean=float((r_ * A_).sum() / A_.sum()) if len(r_) else np.nan,
                           n=len(r_) / max(len(ks[::2]), 1), anti=float(np.mean(an)) if an else np.nan)
        rows.append(out)

    print(f"Hours {a.hours[0]:g}-{a.hours[1]:g}, medians of hourly values. U m/s, H m, W and Rd km, N 1/s.")
    print("| run | section | U | H | W | N | Rd | Bu = (Rd/W)^2 | Ro = U/(fW) | Rd at --f-other |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for o in rows:
        for tag in ("2.5", "5"):
            if tag not in o:
                continue
            q = o[tag]
            rdtxt = f"{q['Rd'] / 1e3:.2f}" if np.isfinite(q["Rd"]) else "inf"
            print(f"| {o['run']} | {tag} km | {q['U']:.2f} | {q['H']:.0f} | {q['W'] / 1e3:.2f} | {q['N']:.4f} | {rdtxt} | "
                  f"{q['Bu']:.2g} | {q['Ro']:.2g} | {q['Rd_other'] / 1e3:.2f} |")
    print("\n| run | eddy radius median / area-weighted (km) | eddies per snapshot | anticyclonic | Rd at 2.5 km (km) | Bu at eddy scale (Rd/r)^2 |")
    print("|---|---|---|---|---|---|")
    for o in rows:
        e = o["eddy"]; Rd = o.get("2.5", {}).get("Rd", np.nan)
        bu = (Rd / (e["wmean"])) ** 2 if np.isfinite(Rd) else np.inf
        print(f"| {o['run']} | {e['med'] / 1e3:.2f} / {e['wmean'] / 1e3:.2f} | {e['n']:.1f} | "
              f"{e['anti'] * 100:.0f} % | {Rd / 1e3 if np.isfinite(Rd) else np.inf:.2f} | {bu:.2g} |")


if __name__ == "__main__":
    main()
