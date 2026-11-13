"""Stream a segmented member's ocean_his.nc files from the bucket and keep only what the
jet analysis needs: surface-layer and depth-mean fields at every record, plus full-depth
sections across the jet at a few distances from shore.
Usage: extract_jet_fields.py GS_MEMBER_FOLDER OUT.nc [NSEG]  (folder holding seg_001 ... seg_NNN)"""
import subprocess, sys, os, netCDF4, numpy as np
gs, out = sys.argv[1], sys.argv[2]
nseg = int(sys.argv[3]) if len(sys.argv) > 3 else 28
SURF = ["u", "v", "u_stokes", "v_stokes", "temp", "AKv"]
BAR = ["zeta", "ubar", "vbar", "ubar_stokes", "vbar_stokes"]
SEC = ["v", "v_stokes", "temp", "AKv", "u"]
YSEC = [2500.0, 5000.0, 10000.0, 15000.0]
tmp = out + ".seg.nc"
dst = None; last_t = -1e30
for k in range(1, nseg + 1):
    subprocess.run(["gcloud", "storage", "cp", "-q", f"{gs}/seg_{k:03d}/ocean_his.nc", tmp], check=True)
    src = netCDF4.Dataset(tmp); src.set_auto_mask(False)
    if dst is None:
        yr = src["y_rho"][:, 0]; yv = src["y_v"][:, 0]
        jr = [int(np.argmin(abs(yr - y))) for y in YSEC]
        jv = [int(np.argmin(abs(yv - y))) for y in YSEC]
        dst = netCDF4.Dataset(out, "w", format="NETCDF4")
        dst.createDimension("t", None)
        for n in ("xi_rho", "eta_rho", "xi_u", "eta_u", "xi_v", "eta_v", "s_rho", "s_w"):
            dst.createDimension(n, len(src.dimensions[n]))
        dst.createDimension("sec", len(YSEC))
        for n in ("h", "x_rho", "y_rho", "x_v", "y_v", "x_u", "y_u", "pm", "pn", "f", "mask_rho",
                  "hc", "Cs_r", "Cs_w", "s_rho", "s_w"):
            v = src[n]; o = dst.createVariable(n, "f8", v.dimensions); o[:] = v[:]
        dst.createVariable("ocean_time", "f8", ("t",))
        dst.createVariable("jsec_rho", "i4", ("sec",))[:] = jr
        dst.createVariable("jsec_v", "i4", ("sec",))[:] = jv
        dst.createVariable("ysec", "f8", ("sec",))[:] = YSEC
        for n in SURF:
            d = src[n].dimensions; d2 = tuple(x for x in d[1:] if x not in ("s_rho", "s_w"))
            dst.createVariable(n + "_sfc", "f4", ("t",) + d2, zlib=True, complevel=1, shuffle=True)
        for n in BAR:
            dst.createVariable(n, "f4", ("t",) + src[n].dimensions[1:],
                               zlib=True, complevel=1, shuffle=True)
        for n in SEC:
            d = src[n].dimensions  # (ocean_time, s, eta, xi)
            dst.createVariable(n + "_sec", "f4", ("t", d[1], "sec", d[3]), zlib=True, complevel=1, shuffle=True)
    t = src["ocean_time"][:]
    new = np.nonzero(t > last_t + 1e-6)[0]
    n0 = len(dst["ocean_time"])
    for i, r in enumerate(new):
        dst["ocean_time"][n0 + i] = t[r]
        for n in SURF:
            dst[n + "_sfc"][n0 + i] = src[n][r, -2 if src[n].dimensions[1] == "s_w" else -1]
        for n in BAR:
            dst[n][n0 + i] = src[n][r]
        for n in SEC:
            jj = jv if src[n].dimensions[2] == "eta_v" else jr
            dst[n + "_sec"][n0 + i] = src[n][r][:, jj, :]
    last_t = t[new[-1]]
    src.close(); os.remove(tmp)
    print(f"seg_{k:03d}: +{len(new)} records, total {len(dst['ocean_time'])}, hour {last_t/3600:.2f}, "
          f"{os.path.getsize(out)/1e9:.2f} GB", flush=True)
dst.close()
