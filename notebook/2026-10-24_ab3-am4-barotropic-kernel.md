# AB3-AM4 barotropic kernel made usable (STEP2D_FB_AB3_AM4)

- **Date:** 2026-10-24
- **Status:** done; switching cases to it is a decision for the author

## Question / why

ROMS's generalized forward-backward AB3-AM4 barotropic kernel (the scheme
UCLA ROMS uses) needs one kernel call per fast step instead of LF-AM3's
two. The author chose on 2026-10-23 to port it "later, as a separate job"
(after a review of ROMS's numerical schemes).

## What was run

- New patch, now coawst-cloud's `roms-step2d-fb`, off unless the case defines
  `STEP2D_FB_AB3_AM4` (`--build-arg CPP_OPTIONS="+STEP2D_FB_AB3_AM4"`).
  The shipped `step2d_FB.h` was unfinished and never compiled (in COAWST
  v3.9 and in Rutgers ROMS of September 2026): three time levels allocated
  for four, undeclared arrays, wrong density factor, no halo exchange of
  the time averages, linear-drag assumption, no COAWST wave or vegetation
  terms. Rewritten for 3-D runs; `mod_ocean.F`, `step3d_uv.F`, `wetdry.F`
  adapted.
- Checks: compile with every case option set in use (periodic, WEC_VF,
  vegetation, `WET_DRY`, `SED_MORPH`, evolving T/S); builds without the
  option preprocess to byte-identical Fortran; 2-D momentum diagnostics
  close (acceleration = sum of terms to 1e-10 m/s2).
- Reef_Ideal_A15_veg, control VM, 6 + 2 processes, 3 h each
  (`tests/veg_spatial_tests.sh`, images `coawst:reef_a15_veg_fb` local and
  `coawst:reef_a15_veg`): constant canopy at DT 6 s, patchy canopy at
  DT 3 s.
- Linear stability: `tools/fb_stability.py`.

## Results

| A15 vegetation, 3 h | wall AB3-AM4 / LF-AM3 | largest difference from LF-AM3 |
|---|---|---|
| constant canopy, DT 6 s | 432 / 444 s | currents 4e-6 m/s, sea level 0.5 um, Hs 2.4 um |
| patchy canopy, DT 3 s | 558 / 930 s (-40 %) | currents 0.34 mm/s (largest 0.83 m/s), sea level 6 um, Hs 0.25 mm |

- Canopy TKE, epsilon and eddy viscosity: ratios 1.00 (10/50/90 %);
  explicit-drag number unchanged (1.26 for the patchy canopy at DT 3 s);
  periodic seam clean.
- Linear Courant limit of AB3-AM4: 0.890 (alpha_max 1.78); A15 runs at 0.81.
- Design: the port keeps the forcing at time n and recomputes the 2-D advection,
  Coriolis, curvilinear and vortex-force terms each fast step, as LF-AM3.

## Decision / outcome

Usable and tested; LF-AM3 stays the default until the author decides.

## Open questions

- Switch the cases to AB3-AM4? A15 gains little at DT 6 s with 6 + 2 on
  the control VM (balanced), more with a shorter DT; Batch splits not
  benchmarked for A15.
- Not ported (the build stops with a message): 2-D-only runs, `NESTING`,
  `STEP2D_CORIOLIS`, `STEP2D_FB_LF_AM3`. `SED_MORPH` compiled, not run;
  restarts (`PERFECT_RESTART`) untested at the time (later exact on the
  thermal case, [restart entry](2026-10-24_perfect-restart-spot.md)).

## Details and links

- coawst-cloud's patch document `roms-step2d-fb`
