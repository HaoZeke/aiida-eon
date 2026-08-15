#!/usr/bin/env python3
"""Submit an eOn NEB through the eon.neb workchain."""

from __future__ import annotations

import argparse
from pathlib import Path

from aiida import load_profile, orm
from aiida.engine import run
from aiida.plugins import DataFactory, WorkflowFactory

from aiida_eon.helpers import localhost_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reactant", type=Path)
    parser.add_argument("product", type=Path)
    parser.add_argument("--code", default="eonclient@localhost")
    parser.add_argument("--potential", default="lj")
    parser.add_argument("--images", type=int, default=5)
    args = parser.parse_args()

    load_profile()
    Neb = WorkflowFactory("eon.neb")
    ConData = DataFactory("eon.con")
    result = run(
        Neb,
        parameters=orm.Dict(
            dict={
                "Potential": {"potential": args.potential},
                "Nudged Elastic Band": {
                    "images": args.images,
                    "initializer": "idpp",
                },
            }
        ),
        calc={
            "code": orm.load_code(args.code),
            "reactant": ConData.from_path(args.reactant),
            "product": ConData.from_path(args.product),
            "metadata": localhost_metadata(wallclock_seconds=1800),
        },
    )
    print(result["results"].get_dict())


if __name__ == "__main__":
    main()
