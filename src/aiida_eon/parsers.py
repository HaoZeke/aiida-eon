"""Parser for ``EonCalculation``."""

from __future__ import annotations

from pathlib import PurePosixPath

from aiida.engine import ExitCode
from aiida.orm import Dict, SinglefileData
from aiida.parsers.parser import Parser

from .data import ConData
from .io import job_result_scalars, link_label, parse_results_dat
from .jobs import get_job_spec, is_client_job, job_from_parameters

_SIDECAR_SUFFIXES = (".dat", ".xyz", ".json", ".log", ".ckpt")


class EonParser(Parser):
    """Read ``results.dat``, geometries, and job sidecars."""

    def parse(self, **kwargs):
        retrieved = set(self.retrieved.list_object_names())
        if "results.dat" not in retrieved:
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        style = "value_key"
        try:
            params = self.node.inputs.parameters.get_dict()
            job = job_from_parameters(params)
            if is_client_job(job):
                style = get_job_spec(job).results_style
        except (AttributeError, KeyError, ValueError):
            style = "value_key"

        try:
            with self.retrieved.open("results.dat", mode="r") as handle:
                text = handle.read()
            parsed = parse_results_dat(text, style=style)
        except (OSError, UnicodeError, ValueError):
            return self.exit_codes.ERROR_PARSING_RESULTS

        self.out("results", Dict(dict=parsed))
        self.out("scalars", Dict(dict=job_result_scalars(parsed)))

        for name in sorted(retrieved):
            if name in {"results.dat"}:
                continue
            path = PurePosixPath(name)
            if path.suffix == ".con":
                with self.retrieved.open(name, mode="rb") as handle:
                    node = ConData(file=handle, filename=path.name)
                key = link_label(path.stem)
                dest = f"structures.{key}"
                if dest not in self.outputs:
                    self.out(dest, node)
                continue
            if path.suffix in _SIDECAR_SUFFIXES or path.name == "client.log":
                with self.retrieved.open(name, mode="rb") as handle:
                    node = SinglefileData(file=handle, filename=path.name)
                key = link_label(path.name)
                dest = f"files.{key}"
                if dest not in self.outputs:
                    self.out(dest, node)

        return ExitCode(0)
