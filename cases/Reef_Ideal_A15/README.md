# Reef_Ideal_A15

Idealized fringing reef with a pass, ROMS + SWAN coupled, east-west periodic.
Application flag `REEF_IDEAL_A15`. Full description, results and caveats:
[docs/Reef_Ideal_A15.md](../../docs/Reef_Ideal_A15.md).

The `.in` files name each other without paths: run the model inside a copy of
this folder; ROMS and SWAN write NetCDF output under `output/`. The
`swan_*.bot` vegetation files and `vegetation.in` are unused here
(vegetation is off in the header); `wavebc_east.txt` and `wavebc_west.txt`
are unused with periodic SWAN.
