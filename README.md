# aiida-eon

AiiDA 2 plugin for [eOn](https://github.com/TheochemUI/eOn).
The scheduled executable is `eonclient`. The Python server
(`job = akmc`) is not launched from this plugin; use
`WorkflowFactory("eon.akmc")` for a provenance-tracked process-search
campaign, or run the server yourself.

This replaces the 2021 cookiecutter stubs (`DiffCalculation` wrapping
`diff`). The reserved registry name `aiida-eonclient` stays unused so
the entry-point prefix stays `eon`.

File I/O is not reimplemented here. `config.ini` is
`rgpycrumbs.eon.helpers.write_eon_config` /
`eon_schema.config.write_ini`. `results.dat` is
`eon_schema.jobs.results_dat_to_dict`. Saddle codes are
`chemparseplot.parse.eon.saddle_search.EONSaddleStatus`. CON to ASE is
`chemparseplot.parse.eon.con_io`.

## Install

```shell
pip install aiida-eon
verdi plugin list aiida.calculations eon
verdi plugin list aiida.workflows
verdi devel validate-plugins
```

Register the binary on a laptop:

```shell
verdi code create core.code.installed \
  --label eonclient \
  --computer localhost \
  --filepath-executable "$(command -v eonclient)" \
  --default-calc-job-plugin eon
```

On Elja (login-node AiiDA + Slurm) see [docs/elja.md](docs/elja.md).

## Usage

```python
from aiida import orm
from aiida.engine import run
from aiida.plugins import CalculationFactory, DataFactory, WorkflowFactory

ConData = DataFactory("eon.con")
EonCalculation = CalculationFactory("eon")
result = run(
    EonCalculation,
    code=orm.load_code("eonclient@localhost"),
    parameters=orm.Dict(
        dict={
            "Main": {"job": "minimization"},
            "Potential": {"potential": "lj"},
            "Optimizer": {"opt_method": "lbfgs", "converged_force": 0.01},
        }
    ),
    structure=ConData.from_path("pos.con"),
)
print(result["results"].get_dict()["potential_energy"])
print(result["scalars"].get_dict()["force_calls"])
```

Workchains pin `Main.job` and expose the CalcJob ports under `calc`:

```python
Minimize = WorkflowFactory("eon.minimize")
Neb = WorkflowFactory("eon.neb")
Saddle = WorkflowFactory("eon.saddle")
Process = WorkflowFactory("eon.process_search")
Prefactor = WorkflowFactory("eon.prefactor")
Akmc = WorkflowFactory("eon.akmc")
```

## Job surface

`parameters["Main"]["job"]` must be a client job. Aliases:
`neb` -> `nudged_elastic_band`, `finite_differences` ->
`finite_difference`, `molecular_dynamics` -> `dynamics`.

| Token | Inputs | Outputs |
|---|---|---|
| `minimization` | `pos.con` | `min.con` |
| `point` | `pos.con` | Energy / Max_Force |
| `saddle_search` | `pos.con`, optional `displacement.con` / `direction.dat` | `saddle.con`, `mode.dat` |
| `process_search` | `pos.con`, optional displacement | `reactant.con`, `saddle.con`, `product.con` |
| `nudged_elastic_band` | `reactant.con` + `product.con` | `neb.con`, `sp.con`, `neb.dat` |
| `prefactor` | reactant + saddle + product | `freq.dat` |
| `hessian` | `pos.con` | `hessian.dat` |
| `finite_difference` | `pos.con` | curvature table |
| `dynamics` | `pos.con` | `final.con` |
| `monte_carlo` | `pos.con` | energy |
| `basin_hopping` | `pos.con` | `min.con`, `bh.dat` |
| `global_optimization` | `pos.con` | `monitoring.dat` |
| `parallel_replica` / `tad` / `safe_hyperdynamics` | `pos.con` | reactant / product |
| `replica_exchange` | `pos.con` | `pos_out.con` |
| `gp_surrogate` | reactant + product | `neb.con` (needs `WITH_GP_SURROGATE`) |
| `oh_tst` | `pos.con` + `product.con` | `oh_tst_progression.dat` |
| `structure_comparison` | `matter1.con` | (stub) |

Not CalcJobs:

- `akmc` / `escape_rate` / server PR wrappers: WorkChain or the Python server
- `eonclient --serve-*`: long-lived potential RPC
- `forceBatch`: engine path used by NEB and dimer (metatomic implements a true batch)
- geometric NEB: there is no such job. Use `nudged_elastic_band` with
  `[Nudged Elastic Band] elastic_band` or a geometric path init
  (`linear`, `idpp`, `idpp_collective`, `sidpp`, `sidpp_zbl`, `file`)

Potentials are INI sections, not jobs: `lj`, `emt`, `vasp`, `lammps`,
`metatomic`, `xtb`, `rgpot` (`[RgpotPot]` backends `nwchemc`, `cpmdc`,
`metatomic`, `xtb`). Copy potfiles through the `potfiles` `FolderData`
port.

`verdi data eon jobs` prints the catalog. Extra workdir files go in
`extra_files`.

## Registry

Package name `aiida-eon`, import `aiida_eon`, prefix `eon`. The
aiida-registry key already exists; after a PyPI upload the listing
needs `pip_url: aiida-eon` and a `plugin_info` URL. See
[docs/registry.md](docs/registry.md).

## Tests

```shell
pip install -e ".[tests]"
pytest
```

`tests/test_io.py` and `tests/test_jobs.py` do not need a profile.
Entry-point tests need `aiida-core`.

## License

MIT. Contact: rog32@hi.is
