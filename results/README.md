# Results

Results of the **options test campaign** on the A15 cases will be added here:
which physics and numerics choices matter, measured against the baseline's own
convergence noise.

- **Phase 0**, the baseline's own noise (`Reef_Ideal_A15_veg`, constant canopy,
  24 h): DT 3 s, NDTFAST, SWAN time step and iterations, coupling interval,
  spectral resolution, tiling, the 10 m grid, the AB3-AM4 kernel, the vertical
  spline operators, `VISC2`. Submitted 2026-11-02; setup in
  [the notebook](../notebook/2026-11-02_options-campaign-phase0.md).
- **Phase 1**, the physics that drives the reef: wave-breaking formulations,
  wave-generated turbulence, triads, roller, stratified and thermal variants.
- **Phase 2**, bottom-stress and canopy numerics: implicit bottom stress and
  canopy drag, the stress cap, canopy-edge viscosity.

Metrics (computed over hours 12-24, the second tidal cycle): lagoon set-up
(mean and range), cross-crest and pass transport, crest and pass jet speeds,
surface-to-depth-mean speed ratio on the crest and forereef, Hs on the crest and
reef flat, SWAN surface dissipation across the reef, reef-flat temperature
(thermal cases), lagoon flushing time, Courant numbers and the fastest current,
wall time per simulated hour.

No results yet.
