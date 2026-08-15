# Changelog

## 0.2.0

- Client job catalog for every `makeJob` type, including `oh_tst`,
  `gp_surrogate`, replica dynamics, and NEB path-init notes.
- `ConData` (`eon.con`) and `verdi data eon` commands.
- Workchains: `eon.minimize`, `eon.neb`, `eon.saddle`,
  `eon.process_search`, `eon.prefactor`, `eon.akmc`.
- Parser emits JobResult-shaped `scalars`, sidecars, and finite-
  difference tables.
- `potfiles` / `extra_files` ports. Elja computer + code YAML and
  `elja_metadata()`. Registry block documented.
- `aiida-core` floor raised to 2.6.

## 0.1.0

- First `EonCalculation` / `EonParser` cut (`config.ini` + `pos.con`
  + `results.dat`).
