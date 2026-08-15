<!-- vale proselint.Uncomparables = NO -->
# Elja (University of Iceland HPC)

AiiDA runs on the Elja login node. Transport is `core.local`,
scheduler is `core.slurm`. Compute nodes cannot compile; register a
prebuilt `eonclient`.

Login: `slogin1.rhi.hi.is` (`ssh elja`). Slurm account `chem-ui`,
partition `s-normal` (`AllowGroups=HPC-Stefnir`). `any_cpu` is the
other two-day CPU queue (`AllowGroups=HPC-Elja`).

## Profile and computer

```shell
python3 -m venv ~/aiida-venv
~/aiida-venv/bin/pip install 'aiida-core>=2.6,<3' aiida-eon
git clone https://github.com/HaoZeke/aiida-eon.git
cd aiida-eon
verdi=~/aiida-venv/bin/verdi
$verdi presto --profile-name eon

$verdi computer setup --non-interactive --config examples/elja/computer.yml
$verdi computer configure core.local elja-slurm
$verdi computer test elja-slurm
```

`examples/elja/computer.yml` sets label `elja-slurm`, hostname
`localhost`, workdir `/users/home/{username}/aiida-eon-work`. After
setup:

```python
from aiida import orm
computer = orm.load_computer("elja-slurm")
computer.set_minimum_job_poll_interval(30)
```

Account and partition are per-job metadata, not computer-setup fields.

## Code

```shell
verdi code create core.code.installed \
  --non-interactive \
  --label eonclient \
  --computer elja-slurm \
  --filepath-executable /path/to/prebuilt/eonclient \
  --default-calc-job-plugin eon
```

Or edit `examples/elja/code.yml` and pass `--config`. There is no
site-wide `eonclient` path.

If the binary needs the OpenHPC libstdc++ or Lmod, put those exports
in `prepend_text`. Batch shells start with an empty `MODULEPATH`;
init Lmod before `module load` if you use site modules.

## Submit

<!-- vale off -->
```python
from aiida import orm
from aiida.engine import run
from aiida.plugins import CalculationFactory, DataFactory
from aiida_eon.helpers import elja_metadata

EonCalculation = CalculationFactory("eon")
ConData = DataFactory("eon.con")
result = run(
    EonCalculation,
    code=orm.load_code("eonclient@elja-slurm"),
    parameters=orm.Dict(
        dict={
            "Main": {"job": "minimization"},
            "Potential": {"potential": "lj"},
        }
    ),
    structure=ConData.from_path("pos.con"),
    metadata=elja_metadata(wallclock_seconds=7200, cores=1),
)
```
<!-- vale on -->

`elja_metadata` sets `queue_name="s-normal"` and `account="chem-ui"`.
Pass `queue=` or `account=` if your allocation differs.

Hold a long campaign in a named tmux on the login node.

This path is `CalculationFactory("eon")`. The older jump-to-converge
campaign (`aiida-shell` plus an ensemble script) is a different
product.
