# Elja (University of Iceland HPC)

AiiDA runs **on the Elja login node**, not from a laptop over SSH.
Transport is `core.local`, scheduler is `core.slurm`. That is the
shape used by the working JCC campaign (`verdi presto --profile-name
jcc` + `orm.Computer(label="elja-slurm", hostname="localhost")`).

Elja compute nodes cannot compile. Register a **prebuilt** `eonclient`.

Login host example: `slogin1.rhi.hi.is` (`ssh elja`). Substitute your
own account. The JCC campaign used user `rog32`, home
`/users/home/rog32`, Slurm account `chem-ui`, partition `s-normal`.
Live `sinfo` also lists `any_cpu`, `short`, `long`, `48cpu_*`,
`64cpu_*`, `128cpu_*`, and the `gpu-*` partitions.

## Profile and computer

```shell
python3 -m venv ~/aiida-venv
~/aiida-venv/bin/pip install 'aiida-core>=2.6,<3' 'aiida-eon'
git clone https://github.com/HaoZeke/aiida-eon.git
cd aiida-eon
VERDI=~/aiida-venv/bin/verdi
$VERDI presto --profile-name eon

$VERDI computer setup --non-interactive --config examples/elja/computer.yml
$VERDI computer configure core.local elja-slurm
$VERDI computer test elja-slurm
```

`examples/elja/computer.yml` matches the campaign `Computer(...)`
fields: label `elja-slurm`, hostname `localhost`, workdir
`$HOME/aiida-eon-work`. Set the poll interval after setup:

```python
from aiida import orm
computer = orm.load_computer("elja-slurm")
computer.set_minimum_job_poll_interval(30)
```

Account and partition are **per-job** metadata, not computer-setup
fields.

## Code

```shell
verdi code create core.code.installed \
  --non-interactive \
  --label eonclient \
  --computer elja-slurm \
  --filepath-executable /path/to/prebuilt/eonclient \
  --default-calc-job-plugin eon
```

Or `verdi code create core.code.installed --config examples/elja/code.yml`
after editing the executable path. There is no single site-wide
`eonclient` path on Elja.

Optional `prepend_text` if the binary needs OHPC libstdc++ (this is
inferred from JCC runtime scripts, not from an existing AiiDA
prepend):

```bash
export IRA_LIB_DIR=${IRA_LIB_DIR:-$HOME/ira/lib}
export LD_LIBRARY_PATH="${IRA_LIB_DIR}:/opt/ohpc/pub/compiler/gcc/12.4.0/lib64:${LD_LIBRARY_PATH:-}"
```

If you need Lmod on a batch shell (empty `MODULEPATH` otherwise):

```bash
. /opt/ohpc/admin/lmod/lmod/init/bash
export MODULEPATH=/opt/ohpc/pub/modulefiles:/hpcapps/lib-edda/modules/all/Core
```

Do not ship eOn `client/modules.sh` (`foss/2020a`) as an Elja prepend.

## Submit

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

`elja_metadata` sets `queue_name="s-normal"` (`AllowGroups=HPC-Stefnir`)
and `account="chem-ui"`, one node, one MPI rank. `any_cpu` is the
other 2-day CPU queue (`AllowGroups=HPC-Elja`); pass `queue="any_cpu"`
or `account=...` if your allocation is not `chem-ui` / Stefnir.

Hold a long campaign in a named tmux on the login node. The JCC
campaign used blocking `run` (`submit=False`), not a RabbitMQ daemon.

## What this is not

- Not a laptop `core.ssh` / `core.ssh_async` computer to Elja.
- Not Snellius. SURF notes do not apply here.
- The existing Elja AiiDA campaign (`aiida-shell` +
  `elja_jcc_lj_ensemble.sh`) is a different product. Shipping
  `eonclient@elja-slurm` does not reproduce that campaign.
