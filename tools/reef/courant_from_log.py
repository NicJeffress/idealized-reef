#!/usr/bin/env python3
"""Courant numbers from ROMS logs: the check behind the A15 rule "stay below the CFL limits".

Usage: ~/venv/bin/python -I tools/reef/courant_from_log.py RUNDIR [RUNDIR ...]

Each RUNDIR holds coawst.log (a Batch member's output folder, downloaded). Prints the largest Cu,
Cv and Cw with Cw's location and hour, the share of steps with Cw above 1, the 99th percentile and
median of Cw, and the fastest current. A segmented run's top-level log covers its last segment only.
"""
import re,sys
step=re.compile(r"^\s+(\d+) \d{4}-\d\d-\d\d (\d\d):(\d\d):\S+\s+\S+\s+\S+\s+\S+\s+\S+\s*$")
loc=re.compile(r"^\s+\((\d+),(\d+),(\d+)\)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")
for m in sys.argv[1:]:
    rows=[];last=None
    for l in open(f"{m}/coawst.log",errors="replace"):
        a=step.match(l)
        if a: last=a; continue
        b=loc.match(l)
        if b and last:
            try: rows.append((int(last[1]),int(last[2])+int(last[3])/60,int(b[1]),int(b[2]),int(b[3]),float(b[4]),float(b[5]),float(b[6]),float(b[7])))
            except ValueError: pass
            last=None
    import numpy as np
    r=np.array(rows); i=r[:,7].argmax(); over=(r[:,7]>1).mean()*100; h=r[r[:,7]>1,1]
    print(f"{m:5s} steps {len(r)}: max Cu {r[:,5].max():.3f} Cv {r[:,6].max():.3f} Cw {r[i,7]:.2f} at ({int(r[i,2])},{int(r[i,3])},{int(r[i,4])}) hour {r[i,1]:.1f}; Cw>1 on {over:.2f} % of steps (hours {h.min() if len(h) else 0:.1f}-{h.max() if len(h) else 0:.1f}); p99 Cw {np.percentile(r[:,7],99):.2f}, median {np.median(r[:,7]):.2f}; fastest {r[:,8].max():.2f} m/s")
