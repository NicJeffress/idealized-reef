# Periodic Reef_Ideal_A15, 24 h on Batch

- **Date:** 2026-10-21
- **Status:** done

## Question / why

Confirm the periodic A15 image on Batch for a full day: speed, cost,
stability of the periodic seam, reproducibility across machines, and how
much output a run makes.

## What was run

- Batch job `a15-per-batch-test`, spec
  `batch/ensemble/tests/a15-per-24h`.
- Image `reef_a15` (`sha256:85dede9b...`, periodic SWAN with every SWAN fix of the time).
- c2d-standard-16 in us-east4-a (VM on the first try), AMD EPYC 7B13;
  10 ROMS (1 x 10) + 6 SWAN; 24 h simulated (`NTIMES` 14400, DT 6 s).
- Cost: about $0.50.

## Results

- SUCCEEDED; model 1626 s (68 s per simulated hour, as benchmarked); job
  28.4 min.
- ROMS DONE, no NaN/Inf in 24 h; all 6 SWAN processes read the 6061.016 m
  period; steady 12 h tidal cycle (zeta -0.17 to +0.20 m); Hs up to
  1.8 m over the pass; pass jet 0.88 m/s; periodic seam clean all day
  (zeta within 6e-6 m, vbar within 7e-5 m/s).
- ROMS fields at 1, 2, 3 h bit-identical to the control-VM run (EPYC
  9B14, 6 + 2 processes): members can run on any machine and split
  (with 1 x N tilings).
- Output 2.85 GB per simulated day: restart 1.24 GB (a record every hour,
  `LcycleRST F`), diagnostics 0.82 GB, history 0.51 GB, averages
  0.47 GB, SWAN under 0.01 GB. About 20 GB per week-long run, 2 TB for
  100 runs, plus about $0.02/GB to copy across regions.

## Decision / outcome

Batch-measured: about $0.50 per simulated day, about $3 per week-long
run, about $300 for 100 runs (on-demand, us-east4). The tide settles into
a repeating 12 h cycle by about hour 12.

## Open questions

- Trim output before large ensembles: restart (`LcycleRST T`, 2 records),
  whether diagnostics are needed, history fields and interval (and what
  ROMSPath needs), SWAN output times. To decide with the domain.

## Details and links

- [docs, What each variation needs](../docs/Reef_Ideal_A15.md) ("Measured on Batch")
