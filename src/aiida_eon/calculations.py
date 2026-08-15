"""CalcJob wrapping ``eonclient``.

The client reads ``config.ini`` and ``pos.con`` from the working
directory and writes ``results.dat`` plus job-specific ``.con`` files.
"""

from __future__ import annotations

from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import Dict, SinglefileData

from .io import write_ini


class EonCalculation(CalcJob):
    """Run one eOn client job (minimization, saddle, NEB, point, ...)."""

    _CONFIG_NAME = "config.ini"
    _STRUCTURE_NAME = "pos.con"
    _RESULTS_NAME = "results.dat"

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.inputs["metadata"]["options"]["resources"].default = {
            "num_machines": 1,
            "num_mpiprocs_per_machine": 1,
        }
        spec.inputs["metadata"]["options"]["parser_name"].default = "eon"
        spec.inputs["metadata"]["options"]["withmpi"].default = False

        spec.input(
            "parameters",
            valid_type=Dict,
            help="INI sections as a nested dict, e.g. "
            "{'Main': {'job': 'minimization'}, 'Potential': {'potential': 'lj'}}.",
        )
        spec.input(
            "structure",
            valid_type=SinglefileData,
            help="Geometry written as pos.con (eOn CON text).",
        )
        spec.input(
            "reactant",
            valid_type=SinglefileData,
            required=False,
            help="Optional reactant.con (saddle / process search).",
        )
        spec.input(
            "product",
            valid_type=SinglefileData,
            required=False,
            help="Optional product.con (NEB / process search).",
        )
        spec.input(
            "displacement",
            valid_type=SinglefileData,
            required=False,
            help="Optional displacement.con / mode seed.",
        )
        spec.output("results", valid_type=Dict, help="Parsed results.dat.")
        spec.output_namespace(
            "structures",
            valid_type=SinglefileData,
            dynamic=True,
            help="Retrieved .con files keyed by stem (min, saddle, ...).",
        )

        spec.exit_code(
            300,
            "ERROR_MISSING_OUTPUT_FILES",
            message="The calculation did not produce results.dat.",
        )
        spec.exit_code(
            310,
            "ERROR_PARSING_RESULTS",
            message="results.dat was present but could not be parsed.",
        )

    def prepare_for_submission(self, folder):
        sections = self.inputs.parameters.get_dict()
        if not isinstance(sections, dict) or not sections:
            raise ValueError("parameters must be a non-empty nested dict of INI sections")
        write_ini(folder.get_abs_path(self._CONFIG_NAME), sections)

        local_copy_list = [
            (
                self.inputs.structure.uuid,
                self.inputs.structure.filename,
                self._STRUCTURE_NAME,
            ),
        ]
        extra = (
            ("reactant", "reactant.con"),
            ("product", "product.con"),
            ("displacement", "displacement.con"),
        )
        for port, dest in extra:
            if port in self.inputs:
                node = self.inputs[port]
                local_copy_list.append((node.uuid, node.filename, dest))

        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = []
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list
        calcinfo.retrieve_list = [
            self._RESULTS_NAME,
            "client.log",
            "*.con",
        ]
        return calcinfo
