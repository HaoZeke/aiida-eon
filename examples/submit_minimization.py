#!/usr/bin/env python3
"""Submit an eOn minimization through AiiDA.

Requires a configured profile, a computer, and a Code for ``eonclient``
with entry point ``eon``. The structure file is raw CON text.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from aiida import load_profile, orm
from aiida.engine import run
from aiida.plugins import CalculationFactory, DataFactory

from aiida_eon.helpers import localhost_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path, help="pos.con (or any .con)")
    parser.add_argument("--code", default="eonclient@localhost", help="AiiDA code label")
    parser.add_argument("--potential", default="lj", help="[Potential] potential")
    parser.add_argument("--job", default="minimization", help="[Main] job")
    args = parser.parse_args()

    load_profile()
    EonCalculation = CalculationFactory("eon")
    ConData = DataFactory("eon.con")
    inputs = {
        "code": orm.load_code(args.code),
        "parameters": orm.Dict(
            dict={
                "Main": {"job": args.job},
                "Potential": {"potential": args.potential},
                "Optimizer": {"opt_method": "lbfgs", "converged_force": 0.01},
            }
        ),
        "structure": ConData.from_path(args.structure),
        "metadata": localhost_metadata(wallclock_seconds=600),
    }
    result = run(EonCalculation, **inputs)
    print(result["results"].get_dict())


if __name__ == "__main__":
    main()
