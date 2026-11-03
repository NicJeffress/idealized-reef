# The wave roller: strength sweep, refined grid and restarts

- **Date:** 2026-11-03
- **Status:** done; recommendation below (the author's decision)
- **Builds:** coawst-cloud `61f8cea` (with `roms-roller-substeps`), `+ROLLER_RENIERS`;
  restart pair also with the first version of `roms-restart-roller` (below; final version coawst-cloud `3227cce`). Case defaults of
  2026-11-03 (30-degree spread, 34 frequencies, `TKE_WAVEDISS`), density-1
  canopy, 24 h, DT 6 s

## Question / why

The roller now runs at DT 6 s ([roller sub-steps](2026-11-03_roller-substeps.md)),
but the author was unsure whether it belongs in the A15 defaults. Three
checks: how strongly the answer depends on `WEC_ALPHA` (the share of the
breaking dissipation that feeds the roller); whether the roller's effect is
real or a side effect of the coarse breaking zone (20 m cells, 2-3 cells
across the surf zone, see [grid](2026-11-03_grid-10m.md)); and whether a run
with the roller can be cut into restart segments, as every Spot run is.

## What was run

- 20 m grid, `WEC_ALPHA` 0 (no roller, the baseline), 0.25, 0.5 and 1.0.
- The breaking-zone grid (10 m rows from 850 to 1150 m), `WEC_ALPHA` 0 and 0.5.
- Restart pair: `WEC_ALPHA` 0.5, 8 h straight and 2 x 4 h segments, with and
  without the new `roms-restart-roller` fix; and the same pair without the
  roller as a control.

## Results

**Strength (20 m grid).** Everything the roller changes scales linearly with
`WEC_ALPHA`:

| `WEC_ALPHA` | set-up | crest transport | pass transport | crest jet max | wall s per sim h |
|---|---|---|---|---|---|
| 0 (no roller) | 12.5 mm | 465 m³/s | 575 m³/s | 0.235 m/s | 109 |
| 0.25 | +12 % | +8 % | +6 % | +5 % | 98 |
| 0.5 | +25 % | +15 % | +13 % | +11 % | 98 |
| 1.0 | +50 % | +30 % | +25 % | +21 % | 96 |

The breaking dissipation across the reef is unchanged (1700 W/m, within 1 %):
the roller does not remove more energy, it moves where the momentum reaches
the mean flow. It stores part of the breaking wave's momentum and releases it
further shoreward, onto the crest and the reef flat instead of the fore reef,
so more of the set-up gradient sits where it pushes water over the crest. The
roller's own cost is nil (the sub-steps are cheap; the small speed-up is
machine-to-machine noise).

**Refined breaking zone.** The roller's effect does not go away when the
surf zone is resolved; it is larger:

| | 20 m, none | 20 m, 0.5 | band, none | band, 0.5 |
|---|---|---|---|---|
| set-up | 12.5 mm | 15.6 mm (+25 %) | 10.8 mm | 14.2 mm (+32 %) |
| crest transport | 465 m³/s | 536 m³/s (+15 %) | 439 m³/s | 522 m³/s (+19 %) |
| pass transport | 575 m³/s | 648 m³/s | 532 m³/s | 618 m³/s |
| crest jet max | 0.235 m/s | 0.260 m/s | 0.233 m/s | 0.264 m/s |
| Hs on the crest | 0.200 m | 0.209 m | 0.189 m | 0.199 m |

And with the roller the two grids agree better: band against 20 m, the
set-up differs by -9 % with the roller against -14 % without it, the crest
transport by -3 % against -6 %, the pass transport by -5 % against -7 %. The
roller spreads the wave forcing over more cells, so the answer depends less on
how finely the 2-3 breaking cells are drawn. (The higher Hs on the crest
follows from the set-up: deeper water lets a larger depth-limited wave
through.)

**Restarts.** Without a fix, a segmented roller run drifted away from the
straight one: 1.4e-4 m/s four hours after the restart, 400 times the control
without a roller (3.7e-7 m/s). Cause: the Reniers roller carries its own
state from step to step, the roller area `rollA`, and COAWST does not write it
to the restart file, so each restarted segment began with no roller. A first
version of the coawst-cloud fix `roms-restart-roller` wrote and read `rollA`;
on this pair it gave 2e-7 to 4e-7 m/s at hours 5-7 and 1.4e-6 m/s at hour 8.

That first version was not right: ROMS writes the restart record after the
roller update of the same step, so a restarted run that reads `rollA` and then
updates it again moves the roller forward twice. On a 4 h canopy run the
roller is close to equilibrium and one extra update barely shows; on the A15
test case 30 min after a restart, where the roller is still growing, it made
the restart worse than no fix (1.3e-3 against 6.4e-4 m/s). The final fix
also stores the roller dissipation `Dissip_roller` and skips the roller update
in the first step after a restart: the test case then restarts to 5.8e-11 m/s
(round-off), and builds without the roller are unchanged (bit-identical
output). The 3.7e-7 m/s of the no-roller control was a separate residual, since
traced and fixed ([densities frozen at the start time](2026-11-03_restart-residual-density.md)).

## What the literature says

- The roller (Svendsen 1984; the Reniers et al. 2004 evolution equation that
  `ROLLER_RENIERS` solves) delays the transfer of momentum from breaking
  waves to the mean flow, shifting set-up and longshore forcing shoreward.
  On beaches it is routinely needed to place the longshore current and the
  set-up correctly.
- On reefs, Buckley et al. (2015, "Dynamics of wave setup over a steeply
  sloping fringing reef", JPO 45, 3005-3023), in a flume with a 1:36-scale
  fringing reef: radiation-stress gradients from linear wave theory
  underpredicted both the set-down and the set-up for most conditions, most
  for large waves and low water; including a roller model improved both,
  through its correction of the wave's kinetic energy and the spatial delay
  of the forcing. The steep fore reef of A15 is the same situation.
- `WEC_ALPHA` itself (the share of the breaking dissipation that enters the
  roller) is a tuning parameter: values from 0 to 1 are used, and nothing in an
  idealized study pins it down.

## What it means

- The roller is physics the model is otherwise missing on a steep reef, not
  a numerical artefact: its effect grows when the surf zone is resolved, and
  it makes the answer less grid-sensitive.
- Its size is set by `WEC_ALPHA`, and linearly: 0.25 to 1.0 spans +12 % to
  +50 % in set-up. Any result that depends on the set-up or the crest
  transport inherits that uncertainty.
- With `roms-roller-substeps` and `roms-restart-roller` it is stable at DT 6 s,
  free in cost, and with the final `roms-restart-roller` it restarts to round-off.

## Decision / outcome

Recommendation: **turn the roller on in the A15 defaults with `WEC_ALPHA`
0.5**, the middle of the usual range, and treat `WEC_ALPHA` as an ensemble
parameter (0.25 and 1.0 as a sensitivity pair) wherever set-up or crest
transport matter. The alternative, keeping it off, leaves out a mechanism
the flume data needed on a steep reef. The author's decision.

## Details and links

- [Results summary](../results/README.md)
- coawst-cloud: `roms-roller-substeps` (sub-steps), `roms-restart-roller`
  (restart) patches and tests.
- Cost: 4 sweep runs, 1 band run, 2 restart pairs: about $3.
