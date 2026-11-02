# Restartable segments and the first Spot Batch job

- **Date:** 2026-10-27
- **Status:** done: segment mode and Spot work end to end on the idealized reef

## Question / why

The 2026-10-24 restart work left the segment runner (`run_member.sh`
`SEGMENT_HOURS`) and the `"spot": true` option untested. The author wants
Spot VMs to cut Batch cost, and asked first for the control VM to be
downsized (c3d-standard-8 to c3d-standard-4, done by the author from Cloud
Shell this morning).

## What was run

- Image `coawst:reef_a15_veg_rst` (Reef_Ideal_A15_veg with every current
  patch, including `swan-exact-restart` and `roms-restart-wec`), pushed as
  `v3.9-26e6fb7-reef_a15_veg-rst`, digest `sha256:f9884cb4...`. Full build
  from an empty Docker cache on the c3d-standard-4: **7 min 22 s**.
- `tests/segment_test.sh` on the control VM (now takes `NOCN TI TJ NWAV`;
  2 ROMS (1x2) + 2 SWAN on 4 vCPUs): 2 h straight against 1 h segments,
  container killed 90 s into segment 2 and started again on a fresh
  `/work`. Compared with `tools/merge_segments.py` + `tests/restart_check.py`.
- Batch `a15-veg-spot-6h` (spec `batch/ensemble/tests/a15-veg-spot-6h`):
  2 identical members, 6 h in 2 h segments, c2d-standard-16 Spot in
  us-west4-a, 10 + 6 processes, `max_retries` 5.

## Results

- Local preemption test: the second start resumed after segment 1
  ("resume: after segment 1 (3600 s), restart files from restart/a") and
  finished. Against the straight run: u, v 2.3e-10 m/s, AKv 1.9e-9, SWAN
  Hs bit-identical (the 2026-10-24 restart level). The restart files' `ru`,
  `rv`, `rubar`, `rvbar` differ only in the periodic ghost columns (0 and
  Lm+1), which ROMS refills from the interior and never uses.
- Batch: both members ran on `provisioningModel: SPOT` (so Spot VMs count
  against the normal CPU quota; `PREEMPTIBLE_CPUS` 0 did not block them),
  VMs within 35 s, 3 segments each, 553-554 s wall (92 s per simulated
  hour including three model starts), no preemption. The two members are
  bit-identical in all 38 output files. Restart files deleted after the
  last segment; 1.25 GB in the bucket for both.
- Cost about $0.10 (2 x ~10 min x ~$0.18/h Spot c2d-standard-16 in
  us-west4, plus ~1.3 GB us-west4 -> us-central1 transfer); on-demand would
  have been about $0.30.

## Decision / outcome

Segments + Spot are ready for real runs. The retry-on-preemption path
(exit 50001) has not been exercised by a real preemption yet; the local
kill test covers the resume itself.

## Open questions

- Stratified idealized case: reference state resets at a restart
  (2026-10-24 entry), still a author decision.
- A real preemption on Batch (will happen by itself on longer runs).

## Details and links

- `batch/README.md`, Restartable members
- Entry [PERFECT_RESTART with waves](2026-10-24_perfect-restart-spot.md)
