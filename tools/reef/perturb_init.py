#!/usr/bin/env python3
"""Copy an A15 initial file with tiny random noise added to the initial sea level.

    perturb_init.py IN.nc OUT.nc --amp 1e-6 [--seed 1]

For twin experiments: does a difference far too small to matter physically grow?
Noise is uniform in +-amp (m) with its mean removed; wet points only if the file holds
mask_rho (the A15 initial files don't, and land is ignored by the model anyway, so the
volume change is about amp/100 averaged over the domain at most). Nothing else changes.
"""
import argparse
import shutil

import netCDF4
import numpy as np

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("infile")
ap.add_argument("outfile")
ap.add_argument("--amp", type=float, required=True, help="noise amplitude (m)")
ap.add_argument("--seed", type=int, default=1)
args = ap.parse_args()

shutil.copyfile(args.infile, args.outfile)
with netCDF4.Dataset(args.outfile, "a") as d:
    z = d["zeta"]
    if z.ndim != 3:
        raise SystemExit("expected zeta(time, eta, xi)")
    wet = np.ones(z.shape[1:], bool)
    if "mask_rho" in d.variables:
        wet = d["mask_rho"][:] > 0
    rng = np.random.default_rng(args.seed)
    noise = rng.uniform(-args.amp, args.amp, z.shape[1:])
    noise -= noise[wet].mean()
    noise[~wet] = 0.0
    field = np.ma.filled(z[0], 0.0) + noise
    z[0] = field
    print(f"zeta noise: amp {args.amp:g} m, seed {args.seed}, rms {noise[wet].std():.3e} m, on {wet.sum()} points")
