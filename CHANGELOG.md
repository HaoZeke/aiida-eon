# Changelog

## 0.3.2

Rewrote the 0.3.1 changelog line. No code change.

## 0.3.1

Rewrote the plugin README, Elja notes, registry page, and the 0.3.0
changelog entries.

## 0.3.0

`config.ini` is written with `eon_schema.config.write_ini`, the same
helper `rgpycrumbs.eon.helpers.write_eon_config` wraps. Saddle status
codes come from `chemparseplot.parse.eon.saddle_search.EONSaddleStatus`.
eOn `.con` geometries convert to Atomic Simulation Environment (ASE)
atoms through `chemparseplot.parse.eon.con_io`.

`results.dat` uses `eon_schema.jobs` when that module exists (0.2.3
or newer). The 0.2.2 wheel on PyPI does not include it, so the plugin
keeps a matching parser and restores multi-word
`termination_reason_text`.

Python 3.11 is the floor, because that is what `eon-schema` needs.

## 0.2.1

The parser treats a non-zero `termination_reason`, or a failing
`good` / `converged` flag, as a failed job. A missing status no
longer counts as success.

Nudged elastic band (NEB) retrieve globs match the files the client
writes (`peak*_pos.con`, `peak*_mode.dat`, `neb_*.dat`). Extra
workdir files use the `extra_files` namespace key as the destination.
Prefactor accepts `structure` as the reactant. NEB drops `structure`
after that alias so it cannot overwrite `reactant.con`. Each adaptive
kinetic Monte Carlo (AKMC) search gets its own `random_seed` and
its own `metadata.call_link_label`.

## 0.2.0

One `EonCalculation` covers every `eonclient` job type. `ConData`
(`eon.con`) stores `.con` text. Workchains pin the `job` key:
`eon.minimize`, `eon.neb`, `eon.saddle`, `eon.process_search`,
`eon.prefactor`, `eon.akmc`. Elja login-node computer YAML lives
under `examples/elja/`. `aiida-core` 2.6 is the floor.

## 0.1.0

First `EonCalculation` and `EonParser`: `config.ini`, `pos.con`,
`results.dat`.
