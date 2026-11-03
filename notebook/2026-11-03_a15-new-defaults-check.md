# A15 new defaults: check runs (AB3-AM4, implicit bottom stress, implicit canopy drag)

- **Date:** 2026-11-03 (just after midnight UTC)
- **Status:** done: the defaults adopted on 2026-11-02 run cleanly and agree
  with the earlier settings within a few per cent, 20 % faster
- **Builds:** coawst-cloud `f62dff3` (triads acting), case headers as committed
  on 2026-11-02 (`v3.9-ccf62dff3-reef_a15_veg{,_strat}-def1102`)

## Question / why

The author adopted, for every A15 case, the AB3-AM4 barotropic kernel, the
implicit bottom stress and `SPLINES_VVISC` off, and for the canopy cases the
implicit canopy drag ([triads-on entry](2026-11-02_options-triads-on.md)).
Do the four work together, and how far do they move the answer? The
implicit stress had been compared with the explicit one only with triads off
(forereef shear -17 % then).

## What was run

24 h, triads on, 10 + 6 processes, c2d-standard-16 Spot, DT 6 s, NDTFAST 24:
the vegetated case with a bare reef, the constant canopy and the patchy
canopy, and the stratified case (constant canopy, N² 1e-4).

## Results

**Bare reef**, new defaults against the old settings (explicit stress, LF-AM3,
`SPLINES_VVISC` on; both with triads), next to the noise floor (DT 3 s):

| | set-up | set-up range | crest transport | crest jet p99 / max | pass jet max | surface/mean forereef | breaking dissipation | wall s per sim h |
|---|---|---|---|---|---|---|---|---|
| old settings (values) | 62.0 mm | 11.6 mm | 1396 m³/s | 0.62 / 0.83 m/s | 1.03 m/s | 1.36 | 3044 W/m | 81 |
| new defaults | +1.3 % | -6.1 % | +0.4 % | +3.3 / 0.0 % | +1.1 % | -6.1 % | -0.8 % | **65** |
| noise floor (DT 3 s) | -0.2 % | -0.1 % | -0.1 % | +0.6 / -1.6 % | 0.0 % | +3.4 % | -0.6 % | 126 |

**Constant canopy**, new defaults against the implicit canopy drag alone
(LF-AM3, explicit stress, `SPLINES_VVISC` off; both with triads): every
metric within 2.3 % except the mean set-up, -6.7 % (3.64 against 3.90 mm;
the implicit bottom stress, since AB3-AM4 alone changes nothing); wall time
66 against 84 s per simulated hour.

**Patchy canopy at DT 6 s** (the case that blew up with the explicit drag
before 2026-10-27): stable; set-up 24.5 mm, crest transport 856 m³/s, crest
jet 0.84 m/s, largest Courant numbers 0.12 / 0.22 / 0.69; 66 s per simulated
hour.

**Stratified case**: stable; set-up 3.3 mm, crest transport 203 m³/s, crest
jet 0.11 m/s, reef-flat SST range 0.03 C in 24 h without heating; 75 s per
simulated hour.

## Decision / outcome

The defaults stand. The implicit stress's effect on the forereef shear ratio
shrinks from -17 % (triads off) to -6 % with triads; the other differences
are a few per cent, mostly at the level of the noise floor, and every A15
run is now about 20 % cheaper.

## Details and links

- [Results summary](../results/README.md), [triads-on entry](2026-11-02_options-triads-on.md)
- Cost: 4 runs x ~0.45 h of c2d-standard-16 Spot, about $0.35.
