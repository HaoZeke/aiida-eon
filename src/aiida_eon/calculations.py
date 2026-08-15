"""CalcJob wrapping ``eonclient``.

The client reads ``config.ini`` and job-specific ``.con`` / ``.dat``
files from the working directory and writes ``results.dat`` plus the
outputs listed on the job spec.
"""

from __future__ import annotations

from aiida.common import datastructures
from aiida.engine import CalcJob
from aiida.orm import Dict, FolderData, SinglefileData

from .data import ConData
from .io import retrieve_list_for, write_ini
from .jobs import (
    PORT_TO_DEST,
    canonicalize_parameters,
    get_job_spec,
    is_client_job,
    job_from_parameters,
    normalize_job,
    required_inputs_for,
)

_STRUCTURE_TYPES = (SinglefileData, ConData)


class EonCalculation(CalcJob):
    """Run one eOn client job (any ``makeJob`` type).

    ``parameters['Main']['job']`` selects the workdir contract. Server
    jobs (``akmc``, ``escape_rate``, ...) raise in
    ``prepare_for_submission``; use the matching WorkChain.
    """

    _CONFIG_NAME = "config.ini"
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
            help="INI sections as a nested dict. Must set Main.job to a "
            "client job (minimization, saddle_search, nudged_elastic_band, "
            "oh_tst, ...). Potential backends (lj, metatomic, rgpot, xtb) "
            "are [Potential] / [RgpotPot] / [Metatomic] keys, not jobs.",
        )
        spec.input(
            "structure",
            valid_type=_STRUCTURE_TYPES,
            required=False,
            help="Primary geometry. Destination is job-dependent "
            "(pos.con, reactant.con, or matter1.con).",
        )
        spec.input(
            "reactant",
            valid_type=_STRUCTURE_TYPES,
            required=False,
            help="reactant.con (NEB, prefactor, process/saddle extras).",
        )
        spec.input(
            "product",
            valid_type=_STRUCTURE_TYPES,
            required=False,
            help="product.con (NEB, prefactor, OH-TST).",
        )
        spec.input(
            "saddle",
            valid_type=_STRUCTURE_TYPES,
            required=False,
            help="saddle.con (prefactor).",
        )
        spec.input(
            "displacement",
            valid_type=_STRUCTURE_TYPES,
            required=False,
            help="displacement.con (saddle / process search).",
        )
        spec.input(
            "direction",
            valid_type=SinglefileData,
            required=False,
            help="direction.dat (saddle / process search mode seed).",
        )
        spec.input(
            "mode",
            valid_type=SinglefileData,
            required=False,
            help="Mode seed written as direction.dat (client reads direction.dat).",
        )
        spec.input(
            "ts",
            valid_type=_STRUCTURE_TYPES,
            required=False,
            help="ts.con when [Nudged Elastic Band] initializer=file.",
        )
        spec.input(
            "matter2",
            valid_type=_STRUCTURE_TYPES,
            required=False,
            help="matter2.con for structure_comparison.",
        )
        spec.input_namespace(
            "extra_files",
            valid_type=SinglefileData,
            required=False,
            dynamic=True,
            help="Arbitrary extra workdir files. Destination is the node "
            "filename (or the namespace key if you set filename).",
        )
        spec.input(
            "potfiles",
            valid_type=FolderData,
            required=False,
            help="Flattened into the client CWD (in.lammps, POTCAR, ...).",
        )
        spec.output("results", valid_type=Dict, help="Parsed results.dat.")
        spec.output(
            "scalars",
            valid_type=Dict,
            required=False,
            help="JobResult-shaped view of the same scalars.",
        )
        spec.output_namespace(
            "structures",
            valid_type=SinglefileData,
            dynamic=True,
            help="Retrieved .con files keyed by stem (min, saddle, neb, ...).",
        )
        spec.output_namespace(
            "files",
            valid_type=SinglefileData,
            dynamic=True,
            help="Retrieved sidecars (mode.dat, neb.dat, hessian.dat, ...).",
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
        spec.exit_code(
            320,
            "ERROR_UNSUPPORTED_JOB",
            message="parameters.Main.job is not an eonclient CalcJob.",
        )

    def prepare_for_submission(self, folder):
        raw = self.inputs.parameters.get_dict()
        if not isinstance(raw, dict) or not raw:
            raise ValueError("parameters must be a non-empty nested dict of INI sections")
        sections = canonicalize_parameters(raw)
        job = job_from_parameters(sections)
        if not is_client_job(job):
            raise ValueError(
                f"{job!r} is not an eonclient CalcJob. "
                "Use a WorkChain or the eOn Python server."
            )
        spec = get_job_spec(job)
        write_ini(folder.get_abs_path(self._CONFIG_NAME), sections)

        local_copy_list = []
        copied_dests: set[str] = set()

        if "structure" in self.inputs:
            dest = spec.structure_dest or "pos.con"
            node = self.inputs.structure
            local_copy_list.append((node.uuid, node.filename, dest))
            copied_dests.add(dest)

        for port, dest in PORT_TO_DEST.items():
            if port == "structure" or not dest:
                continue
            if port not in self.inputs:
                continue
            if dest in copied_dests:
                continue
            node = self.inputs[port]
            local_copy_list.append((node.uuid, node.filename, dest))
            copied_dests.add(dest)

        if "extra_files" in self.inputs:
            extras = self.inputs.extra_files
            for key, node in extras.items():
                dest = node.filename or key
                if dest in copied_dests:
                    continue
                local_copy_list.append((node.uuid, node.filename, dest))
                copied_dests.add(dest)

        if "potfiles" in self.inputs:
            folder_node: FolderData = self.inputs.potfiles
            for rel in folder_node.list_object_names():
                # Client potentials open CWD files (in.lammps, POTCAR).
                dest = rel
                if dest in copied_dests:
                    continue
                local_copy_list.append((folder_node.uuid, rel, dest))
                copied_dests.add(dest)

        missing = [
            name
            for name in required_inputs_for(spec, sections)
            if name not in copied_dests
        ]
        if missing:
            raise ValueError(
                f"job {job!r} requires workdir files {missing}. "
                "Pass structure / reactant / product / extra_files."
            )

        codeinfo = datastructures.CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = []
        codeinfo.withmpi = self.inputs.metadata.options.withmpi

        calcinfo = datastructures.CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list
        calcinfo.retrieve_list = retrieve_list_for(spec)
        return calcinfo


def parameters_job(sections: dict) -> str:
    """Public helper: normalize Main.job."""
    return normalize_job(job_from_parameters(sections))
