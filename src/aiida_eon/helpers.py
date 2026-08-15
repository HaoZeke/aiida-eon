"""Presets for computers that actually run this plugin.

Elja (University of Iceland HPC) runs AiiDA on the login node with
``core.local`` + ``core.slurm``. That is the working campaign shape
from anneal_repro, not a laptop-to-Elja SSH computer.
"""

from __future__ import annotations

from typing import Any

ELJA_COMPUTER_LABEL = "elja-slurm"
ELJA_ACCOUNT = "chem-ui"
# JCC campaign and live sinfo both use s-normal (AllowGroups=HPC-Stefnir).
# any_cpu is the other 2-day CPU queue (AllowGroups=HPC-Elja).
ELJA_QUEUE = "s-normal"
ELJA_QUEUE_ANY_CPU = "any_cpu"
ELJA_POLL_INTERVAL_S = 30.0


def elja_metadata(
    *,
    wallclock_seconds: int = 7200,
    cores: int = 1,
    memory_kb: int = 4 * 1024 * 1024,
    queue: str = ELJA_QUEUE,
    account: str = ELJA_ACCOUNT,
    extra_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """CalcJob ``metadata`` for the Elja Slurm computer.

    Account and partition are per-job options, not computer-setup fields.
    """
    options: dict[str, Any] = {
        "resources": {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
            "num_cores_per_machine": cores,
        },
        "max_wallclock_seconds": wallclock_seconds,
        "queue_name": queue,
        "account": account,
        "max_memory_kb": memory_kb,
        "withmpi": False,
    }
    if extra_options:
        options.update(extra_options)
    return {"options": options}


def localhost_metadata(*, wallclock_seconds: int = 600) -> dict[str, Any]:
    """CalcJob ``metadata`` for a laptop / ``core.direct`` computer."""
    return {
        "options": {
            "resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1},
            "max_wallclock_seconds": wallclock_seconds,
            "withmpi": False,
        }
    }
