#!/usr/bin/env python3
"""Where tracked particles went: reach, depth, return over the crest, time near the crest.

Usage: ~/venv/bin/python -I tools/reef/particle_fates.py LABEL=TRACK_DIR [LABEL=TRACK_DIR ...]
           [--band KM] [--crest 0.95] [--off 1.2]

TRACK_DIR is the output of tools/reef/track_particles.py (chunk_*/out/track.nc). For each run:
- farthest distance from shore reached, share of particles that ever entered the nudging band
  (--band, km from shore; omit to skip);
- share beyond 4 and 8 km from shore at day 1 and at the last record;
- median and 90th-percentile depth (m below mean sea level) of particles off the reef
  (more than --off km from shore) at day 1 and at the last record;
- share that came back over the crest: had been more than --off km from shore and later
  came back shoreward of --crest km;
- after first leaving the reef, the share of particle time spent 0.2-0.55 km off the
  crest (1.15-1.5 km from shore, where the crest draws its inflow from) and the chance that
  a particle there crosses back over the crest within 6 h.
Distances in km from shore; particles outside the grid at release (status 9) are dropped.
"""
import argparse
import glob
from pathlib import Path

import netCDF4
import numpy as np


def load(track_dir):
    Y, Z, S, t = [], [], [], None
    for f in sorted(glob.glob(str(Path(track_dir) / "chunk_*" / "out" / "track.nc"))):
        d = netCDF4.Dataset(f)
        t = np.array(d["model_time"][:], float)
        Y.append(np.ma.filled(d["lat"][:], np.nan)); Z.append(np.ma.filled(d["zp"][:], np.nan))
        S.append(np.ma.filled(d["status"][:], 0))
    Y, Z, S = (np.hstack(a).astype(float) for a in (Y, Z, S))
    ok = S[0] != 9
    return (t - t[0]) / 3600, Y[:, ok] / 1e3, -Z[:, ok]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--band", type=float, default=None)
    ap.add_argument("--crest", type=float, default=0.95)
    ap.add_argument("--off", type=float, default=1.2)
    a = ap.parse_args()
    hdr = ("run", "farthest km", "into band", ">4 km d1/end", ">8 km end", "depth off reef d1 (p90)",
           "depth end (p90)", "back over crest", "time 1.15-1.5 km", "cross in 6 h")
    print("| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr))
    for r in a.runs:
        lab, tdir = r.rsplit("=", 1)
        hours, Y, Z = load(tdir)
        nt, n = Y.shape
        k1 = int(np.argmin(abs(hours - 24)))
        cols = [lab, f"{np.nanmax(Y):.1f}",
                f"{(np.nanmax(Y, 0) > a.band).mean() * 100:.0f} %" if a.band else "-",
                f"{(Y[k1] > 4).mean() * 100:.0f} / {(Y[-1] > 4).mean() * 100:.0f} %",
                f"{(Y[-1] > 8).mean() * 100:.0f} %"]
        for k in (k1, nt - 1):
            off = Y[k] > a.off
            cols.append(f"{np.nanmedian(Z[k][off]):.2g} ({np.nanpercentile(Z[k][off], 90):.2g}) m")
        left = np.maximum.accumulate(Y > a.off, axis=0)
        back = (left & (Y < a.crest)).any(0)
        cols.append(f"{back.mean() * 100:.0f} %")
        H = int(round(6 / (hours[1] - hours[0])))
        below = np.vstack([np.zeros((1, n)), np.cumsum(Y < a.crest, 0)])
        k = np.arange(nt - H)
        fut = (below[k + H + 1] - below[k + 1]) > 0
        zone = left[k] & (Y[k] > 1.15) & (Y[k] < 1.5)
        after = left[k].sum()
        cols.append(f"{zone.sum() / max(after, 1) * 100:.1f} %")
        cols.append(f"{fut[zone].mean() * 100:.0f} %" if zone.any() else "-")
        print("| " + " | ".join(cols) + " |")


if __name__ == "__main__":
    main()
