#!/usr/bin/env python3
"""Submit an eOn minimization on the Elja login-node computer."""

from __future__ import annotations

import argparse
from pathlib import Path

from aiida import load_profile, orm
from aiida.engine import run
from aiida.plugins import CalculationFactory, DataFactory

from aiida_eon.helpers import elja_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path, help="pos.con")
    parser.add_argument("--code", default="eonclient@elja-slurm")
    parser.add_argument("--potential", default="lj")
    parser.add_argument("--wallclock", type=int, default=7200)
    parser.add_argument("--cores", type=int, default=1)
    args = parser.parse_args()

    load_profile()
    EonCalculation = CalculationFactory("eon")
    ConData = DataFactory("eon.con")
    result = run(
        EonCalculation,
        code=orm.load_code(args.code),
        parameters=orm.Dict(
            dict={
                "Main": {"job": "minimization"},
                "Potential": {"potential": args.potential},
                "Optimizer": {"opt_method": "lbfgs", "converged_force": 0.01},
            }
        ),
        structure=ConData.from_path(args.structure),
        metadata=elja_metadata(
            wallclock_seconds=args.wallclock,
            cores=args.cores,
        ),
    )
    print(result["results"].get_dict())


if __name__ == "__main__":
    main()
