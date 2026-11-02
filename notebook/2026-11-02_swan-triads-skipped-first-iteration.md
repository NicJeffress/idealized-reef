# SWAN skips triads in the first iteration whenever currents are present: `TRIAD` was off in every coupled A15 run

- **Date:** 2026-11-02 (evening)
- **Status:** found; fix not decided (see Decision)
- **Found by:** options campaign phase 0 (p0-swanit2) and phase 1 (p1-notriad)

## Question / why

The phase 0 member with two SWAN iterations per time step
(`NUM STOPC 0.005 0.01 0.005 99.5 NONSTAT 2`) moved the reef far more than
any other numerical choice: SWAN surface-breaking dissipation across the reef
-73 %, lagoon set-up -41 %, cross-crest transport -51 %, while Hs on the crest
changed by only 4 %. Halving SWAN's time step (60 s instead of 120 s, still
one iteration) changed nothing (1e-5). Why should a second iteration matter so
much?

## What was found

- SWAN's dissipation breakdown at hour 24 (reef rows 20-45, mean / max):

  | term | 1 iteration (baseline) | 2 iterations |
  |---|---|---|
  | Hs (m) | 0.429 / 0.986 | 0.430 / 0.969 |
  | total dissipation | 8.07 / 54.1 | 7.58 / 52.8 |
  | surface breaking (`dissurf`) | 0.147 / 2.38 | 0.035 / 1.03 |
  | vegetation (`disveg`) | 6.34 / 42.9 | 5.98 / 43.8 |
  | bottom friction (`disbot`) | 1.58 / 8.75 | 1.56 / 8.59 |
  | **triad transfer (`redtriad`)** | **0 / 0** | **3.24 / 35.8** |

  With one iteration the triad term is exactly zero everywhere.
- p1-notriad (the baseline without the `TRIAD` line) is **bit-identical** to
  the baseline in every metric: the `TRIAD` command had no effect.
- The cause, in SWAN 41.51 (`swancom1.ftn`, routine `SOURCE`):

  ```fortran
  !  *** compute the 3 wave-wave interactions if in each geographical gridpoint
  !  *** a continuous spectrum is present, i.e., after first iteration
  IF ( ICUR .EQ. 0 .OR. ITER .GT. 1 ) THEN
  ```

  The guard is meant for stationary runs, whose first iteration starts from an
  empty spectrum. A coupled run always has currents (`ICUR` = 1), and
  nonstationary SWAN does one iteration per time step by default, so the
  triad source is **never** computed. The spectrum carried over from the
  previous time step is continuous, so the guard is not needed there.
- With two iterations SWAN's convergence check passes at only 86.6-87.2 % of
  wet points per step (99.5 % required), so two iterations are not converged
  either.

## Consequences

- Every coupled A15 run made so far ran without triads, although `swan.in`
  has `TRIAD`. The phase 0 and phase 1 members that were meant to test triads
  (p1-notriad) or frequency resolution "with triads" (p0-msc34) tested
  nothing of the kind.
- The large p0-swanit2 effect is mostly triads switching on (energy moved to
  higher frequencies before breaking, so less surface-breaking dissipation and
  a weaker breaking-driven set-up and crest flow), plus the second iteration
  itself.
- The breaking comparisons of phase 1 (gamma 0.80, `BKD`, `TG`) were made
  without triads; their spread may change once triads act.

## Decision / outcome

Open, for the author:
1. **Patch SWAN** so that nonstationary runs compute triads from the first
   iteration (the guard becomes `ICUR.EQ.0 .OR. ITER.GT.1 .OR. NSTATC.EQ.1`),
   as a coawst-cloud patch with a before/after test; then rerun the baseline,
   the triad and breaking members.
2. **Or run two or more iterations per step** (wall time +38 % for two; still
   not converged).
3. Either way, an iteration-convergence check (1, 2, 5 iterations) with
   triads active, before the baseline is fixed.

## Details and links

- [Phase 0-2 results](2026-11-02_options-campaign-results-p0-p2.md)
- SWAN source: COAWST v3.9, `SWAN/src/swancom1.ftn` (the `IF ( ICUR .EQ. 0 .OR. ITER .GT. 1 )` before `CALL SWLTA`)
