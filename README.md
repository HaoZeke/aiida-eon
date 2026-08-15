# aiida-eon

AiiDA 2 plugin for [eOn](https://github.com/TheochemUI/eOn).
One `CalcJob` writes `config.ini` and `pos.con`, runs `eonclient`, and
parses `results.dat`.

This replaces the 2021 cookiecutter stubs in `aiida-eon` / `aiida-eonclient`
(`DiffCalculation` wrapping `diff`). The client is the executable AiiDA
schedules; the Python server is not launched from this plugin.

## Install

```shell
pip install aiida-eon
verdi plugin list aiida.calculations
# eon
```

Register the binary:

```shell
verdi code create core.code.installed \
  --label eonclient \
  --computer localhost \
  --filepath-executable "$(command -v eonclient)" \
  --default-calc-job-plugin eon
```

## Usage

```python
from aiida import orm
from aiida.engine import run
from aiida.plugins import CalculationFactory

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
    structure=orm.SinglefileData(file="pos.con"),
)
print(result["results"].get_dict()["potential_energy"])
```

Optional ports `reactant`, `product`, and `displacement` are copied as
`reactant.con`, `product.con`, and `displacement.con` for saddle / NEB
jobs. Retrieved `min.con` / `saddle.con` / ... land under
`result["structures"]`.

`examples/submit_minimization.py` is the same path as a script.

## Tests

```shell
pip install -e .[tests]
pytest
```

`tests/test_io.py` does not need a profile. `tests/test_plugin.py` needs
`aiida-core` (entry-point load only, no daemon).

## License

MIT. Contact: rog32@hi.is
