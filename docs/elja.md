# Elja (University of Iceland HPC)

AiiDA runs **on the Elja login node**, not from a laptop over SSH.
Transport is `core.local`, scheduler is `core.slurm`. That is the
shape used by the working JCC campaign (`verdi presto --profile-name
jcc` + `orm.Computer(label="elja-slurm", hostname="localhost")`).

Elja compute nodes cannot compile. Register a **prebuilt** `eonclient`.

Login host example: `slogin1.rhi.hi.is` (`ssh elja`). Substitute your
own account. The JCC campaign used user `rog32`, home
`/users/home/rog32`, Slurm account `chem-ui`, partition `s-normal`.

## Profile and computer

```shell
python3 -m venv ~/aiida-venv
~/aiida-venv/bin/pip install 'aiida-core>=2.6,<3' 'aiida-eon'
~/aiida-venv/bin/verdi presto --profile-name eon

verdi computer setup --config examples/elja/computer.yml
verdi computer configure core.local elja-slurm
verdi computer test elja-slurm
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

`elja_metadata` sets `queue_name="s-normal"`, `account="chem-ui"`,
one node, one MPI rank. Older notes mention `any_cpu` and
`48cpu_*` / `64cpu_*` / `128cpu_*`; those are not the JCC default.

Hold a long campaign in a named tmux on the login node. The JCC
campaign used blocking `run` (`submit=False`), not a RabbitMQ daemon.

## What this is not

- Not a laptop `core.ssh` / `core.ssh_async` computer to Elja.
- Not Snellius. SURF notes do not apply here.
- The existing Elja AiiDA campaign (`aiida-shell` +
  `elja_jcc_lj_ensemble.sh`) is a different product. Shipping
  `eonclient@elja-slurm` does not reproduce that campaign.
