# Reef_Ideal_A15_veg_therm

Reef_Ideal_A15_veg_strat plus diurnal solar heating and a far-field ocean
column for the north boundary. Application flag `REEF_IDEAL_A15`.
**Every run needs `ocean_clm.nc` and `ocean_bndry.nc`** made for that run by
`tools/thermal/far_field.py --ocean-in ocean.in --init init_reef.nc -o RUN_DIR`.
See [docs/Reef_Ideal_A15_veg_therm.md](../../docs/Reef_Ideal_A15_veg_therm.md).
