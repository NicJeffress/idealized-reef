# Debug and sensitivity patches

One-off changes to COAWST made for single tests in this notebook: a hard-coded
constant or formula swapped for a sensitivity run, or a trace to find a bug. They
are not part of **coawst-cloud**'s patch series and never go into a default build.
They are kept here, next to the entries that used them, so those tests can be
repeated.

| Patch | What it changes | Entry and result |
|---|---|---|
| `streaming-kwd5.patch`, `streaming-kwd200.patch` | Bottom streaming (`wec_streaming.F`): the cap `KWDmax` on the inverse streaming-layer thickness, 20 (stock) to 5 or 200 | [Force shapes](../2026-11-04_force-shapes-and-budget.md): set-up +6.1 % (cap 5) and -1.8 % (cap 200) against the stock cap |
| `streaming-ks03.patch` | Bottom streaming: the hard-coded roughness `ks` in the streaming-layer thickness, 0.03 m to 0.30 m | [All the A15 defaults](../2026-11-04_all-defaults.md), streaming roughness: flow within 1.2 % |
| `wec-break-kumar.patch` | Vertical shape of the breaking force (`wec_vf.F`): Kumar et al. 2012, Eq. 30, cosh[2 pi (z+h)/H] with H = Hs/sqrt(2), instead of stock COAWST's length | [Force shapes](../2026-11-04_force-shapes-and-budget.md): set-up within 0.7 %, fore-reef shear -5.4 % |
| `swan-bkd-gamma-live.patch` | SWAN (`swancom1.ftn`): the BKD breaker index is never frozen (stock SWAN freezes it once, when the accuracy first reaches 95 %) | [All the A15 defaults](../2026-11-04_all-defaults.md): within 2e-6 mm of set-up; the basis for coawst-cloud's `swan-bkd-exact-restart` |
| `rst-trace.patch` | ROMS (`main3d.F`, `initial.F`): bit-exact checksums of the main arrays after each phase of steps 301-410, one file per MPI rank | [Restart residual](../2026-11-03_restart-residual-density.md): found the mismatches fixed by `roms-restart-roller` and `roms-ts-fixed-density` |

## Building with one

coawst-cloud's `build.sh` takes a patch folder and a series file. Copy its patch
folder, add the debug patch, and append it to a copy of the series (one patch at
a time: the three streaming patches edit the same lines):

```bash
cd coawst-cloud
d=$(mktemp -d)
cp -r build/coawst/patches/. "$d"/
cp ../idealized-reef/notebook/patches/streaming-kwd5.patch "$d"/
cp "$d"/series "$d"/series.kwd5
echo streaming-kwd5.patch >> "$d"/series.kwd5
build/coawst/build.sh --case cases/<Case> --app <FLAG> --tag kwd5 \
    --patch-dir "$d" --series "$d"/series.kwd5
```

All six apply after coawst-cloud's full series as of 2026-11-12 (`6235874`,
checked on the files they touch). Two depend on series patches:
`wec-break-kumar.patch` edits next to `wec-break-uniform`, and
`swan-bkd-gamma-live.patch` removes the log line that `swan-bkd-exact-restart`
adds. A later change to the same files may need them refreshed.
