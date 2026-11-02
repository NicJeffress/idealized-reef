# Reef_Ideal_A15 benchmark: machine type, process split, tiling

- **Date:** 2026-10-21
- **Status:** done

## Question / why

Plan step 5 in the project conventions: benchmark a realistic case at different vCPU
counts (within quota) to choose cores per run.

## What was run

Batch specs, 2 simulated hours per member (`NTIMES` 1200 at DT 6 s), ROMS
tiles 1 x NOCN unless stated, one run per cell:
- `batch/ensemble/bench/a15-c3d16` (c3d-standard-16, image
  `sha256:f9ae1c6c...`) and `a15-c3d16b` (12+4 and 11+5 rerun, image
  `sha256:3b7e0961...`).
- `batch/ensemble/bench/a15-c2d16` (c2d-standard-16, `3b7e0961`).
- `batch/ensemble/bench/a15-c2d16-tiling` (tile shapes).
Cost: about $1 for the benchmark.

## Results

Wall time for 2 simulated hours (s):

| ROMS + SWAN | c3d-standard-16 (EPYC 9B14) | c2d-standard-16 (EPYC 7B13) |
|---|---|---|
| 6 + 2 | 197 | 186 |
| 5 + 3 | 197 | 150 |
| 4 + 4 | 210 | 174 |
| 10 + 6 | 194 | **139** |
| 12 + 4 | 225 | 159 |
| 11 + 5 | 213 | - |
| 8 + 8 | 218 | 194 |
| 13 + 3 | 241 | 192 |

- C2D is 25-30 % faster than C3D at almost every split.
- Tiling on c2d-16 (10 + 6): 1x10 136 s, 2x5 139 s, 5x2 140 s, 10x1
  157 s; shape barely matters except thin strips across x.
- On c3d, 12 + 4 first crashed at SWAN start-up: that was the SWAN
  plant-input-grid bug (`plant_input_grids`, coawst-cloud's `swan-vegetation-fixes`), see its entry.

## Decision / outcome

**Recommended for A15-type runs: c2d-standard-16, 10 ROMS (1 x 10) + 6
SWAN, about 68 s per simulated hour** (a week about 3.2 h wall, about
$2.6 on-demand). `batch/submit.py` now tries C2D in us-east4 and us-west4
first.

## Open questions

- Run-to-run noise not measured (one run per cell).

## Details and links

- [docs, Benchmark](../docs/Reef_Ideal_A15.md)
- `batch/README.md`, Choosing a machine
- Related: [SWAN plant input grids](2026-10-21_swan-plant-input-grid-bug.md), [24 h Batch test](2026-10-21_a15-periodic-batch-24h.md)
