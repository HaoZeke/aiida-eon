"""Parser for ``EonCalculation``."""

from __future__ import annotations

from aiida.engine import ExitCode
from aiida.orm import Dict, SinglefileData
from aiida.parsers.parser import Parser

from .io import OUTPUT_CON_NAMES, results_dat_to_dict


class EonParser(Parser):
    """Read ``results.dat`` and any job ``.con`` files from the retrieved folder."""

    def parse(self, **kwargs):
        retrieved = self.retrieved.list_object_names()
        if "results.dat" not in retrieved:
            return self.exit_codes.ERROR_MISSING_OUTPUT_FILES

        try:
            with self.retrieved.open("results.dat", mode="r") as handle:
                text = handle.read()
            parsed = results_dat_to_dict(text)
        except (OSError, UnicodeError, ValueError):
            return self.exit_codes.ERROR_PARSING_RESULTS

        self.out("results", Dict(dict=parsed))

        for name in OUTPUT_CON_NAMES:
            if name not in retrieved:
                continue
            with self.retrieved.open(name, mode="rb") as handle:
                node = SinglefileData(file=handle, filename=name)
            self.out(f"structures.{name.removesuffix('.con')}", node)

        return ExitCode(0)
