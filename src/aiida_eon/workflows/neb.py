"""Nudged elastic band workchain."""

from __future__ import annotations

from aiida.engine import ToContext, WorkChain
from aiida.orm import Dict

from ..calculations import EonCalculation
from ._common import force_job


class EonNebWorkChain(WorkChain):
    """NEB: reactant + product through eonclient ``nudged_elastic_band``.

    Path init (LINEAR / IDPP / SIDPP / FILE) and ``elastic_band`` live
    in ``parameters['Nudged Elastic Band']``. There is no separate
    geometric-NEB job.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(
            EonCalculation,
            namespace="calc",
            exclude=("parameters",),
        )
        spec.input(
            "parameters",
            valid_type=Dict,
            required=False,
            help="INI sections. Main.job is forced to nudged_elastic_band.",
        )
        spec.inputs["calc"]["product"].required = True
        spec.outline(cls.setup, cls.run_client, cls.finalize)
        spec.expose_outputs(EonCalculation)
        spec.exit_code(400, "ERROR_SUBPROCESS", message="eonclient NEB failed.")
        spec.exit_code(
            410,
            "ERROR_MISSING_ENDPOINTS",
            message="NEB needs calc.reactant and calc.product (or structure + product).",
        )

    def setup(self):
        calc_in = self.exposed_inputs(EonCalculation, namespace="calc")
        has_reactant = "reactant" in calc_in or "structure" in calc_in
        if not has_reactant or "product" not in calc_in:
            return self.exit_codes.ERROR_MISSING_ENDPOINTS
        raw = self.inputs.parameters.get_dict() if "parameters" in self.inputs else {}
        self.ctx.parameters = force_job(raw, "nudged_elastic_band")

    def run_client(self):
        inputs = dict(self.exposed_inputs(EonCalculation, namespace="calc"))
        inputs["parameters"] = self.ctx.parameters
        if "reactant" not in inputs and "structure" in inputs:
            inputs["reactant"] = inputs["structure"]
        inputs.pop("structure", None)
        return ToContext(calc=self.submit(EonCalculation, **inputs))

    def finalize(self):
        node = self.ctx.calc
        if not node.is_finished_ok:
            return self.exit_codes.ERROR_SUBPROCESS
        self.out_many(self.exposed_outputs(node, EonCalculation))
