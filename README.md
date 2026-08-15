<!-- vale proselint.Uncomparables = NO -->
# aiida-eon

AiiDA 2 plugin for [eOn](https://github.com/TheochemUI/eOn). It
schedules the `eonclient` binary. One calculation writes `config.ini`
and the job `.con` files, runs the client, and parses `results.dat`.

The Python adaptive kinetic Monte Carlo (AKMC) server is a different
process. Use `WorkflowFactory("eon.akmc")` for independent process
searches, or run `python -m eon.server` for superbasin kinetic Monte
Carlo. In-process Matter work is
[pyeonclient](https://eondocs.org/user_guide/pyeonclient.html).

The eOn user-guide page is
[user_guide/aiida.md](https://github.com/HaoZeke/eOn/blob/docs/aiida-eon/docs/source/user_guide/aiida.md)
([TheochemUI/eOn#396](https://github.com/TheochemUI/eOn/pull/396)).

`config.ini` is `rgpycrumbs.eon.helpers.write_eon_config` /
`eon_schema.config.write_ini`. Saddle codes are
`chemparseplot.parse.eon.saddle_search.EONSaddleStatus`. eOn `.con`
geometries convert to Atomic Simulation Environment (ASE) atoms
through `chemparseplot.parse.eon.con_io`.

## Install

```shell
pip install aiida-eon
verdi plugin list aiida.calculations eon
```

Register a prebuilt binary:

```shell
verdi code create core.code.installed \
  --label eonclient \
  --computer localhost \
  --filepath-executable "$(command -v eonclient)" \
  --default-calc-job-plugin eon
```

On Elja (login-node AiiDA + Slurm) see [docs/elja.md](docs/elja.md).

## Usage

<!-- vale off -->
```python
from aiida import orm
from aiida.engine import run
from aiida.plugins import CalculationFactory, DataFactory, WorkflowFactory

EonCalculation = CalculationFactory("eon")
ConData = DataFactory("eon.con")
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
```
<!-- vale on -->

Workchains pin the `job` key and expose the CalcJob ports
under `calc`:

```python
Minimize = WorkflowFactory("eon.minimize")
Neb = WorkflowFactory("eon.neb")
Saddle = WorkflowFactory("eon.saddle")
Process = WorkflowFactory("eon.process_search")
Prefactor = WorkflowFactory("eon.prefactor")
Akmc = WorkflowFactory("eon.akmc")
```

`verdi data eon jobs` prints the client catalog. The `job` key must
be a client token (`minimization`, `nudged_elastic_band`, `oh_tst`,
and the rest). Aliases such as `neb` become the magic_enum name
before `config.ini` is written.

Serve mode and `forceBatch` are not jobs. Potentials (`lj`,
`metatomic`, `rgpot`, and the rest) are configuration sections. Copy
LAMMPS or Vienna Ab initio Simulation Package (VASP) auxiliaries
through the `potfiles` port.

## Tests

```shell
pip install -e ".[tests]"
pytest
```

## License

License: Expat (MIT). Contact: rog32@hi.is
