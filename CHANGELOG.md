# Changelog

## 0.2.1

- Parse multi-word `termination_reason_text` (key last).
- Non-zero `termination_reason` / `good=false` / `converged=false`
  exit as `ERROR_JOB_FAILED`. Missing status is not reported as 0.
- NEB retrieve `peak*_pos.con`, `peak*_mode.dat`, `neb_*.dat`.
- `extra_files` dest is the namespace key.
- Prefactor accepts `structure` as reactant. NEB drops `structure`
  after aliasing so it cannot overwrite `reactant.con`.
- AKMC searches get distinct `Main.random_seed` and
  `metadata.call_link_label`. Workchain geometry ports are required.

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
