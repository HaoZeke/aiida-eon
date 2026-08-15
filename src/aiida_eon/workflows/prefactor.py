"""Harmonic prefactor workchain."""

from __future__ import annotations

from aiida.engine import ToContext, WorkChain
from aiida.orm import Dict

from ..calculations import EonCalculation
from ._common import force_job


class EonPrefactorWorkChain(WorkChain):
    """Vineyard prefactors from reactant + saddle + product."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(EonCalculation, namespace="calc", exclude=("parameters",))
        spec.input(
            "parameters",
            valid_type=Dict,
            required=False,
            help="INI sections. Main.job is forced to prefactor.",
        )
        spec.inputs["calc"]["saddle"].required = True
        spec.inputs["calc"]["product"].required = True
        spec.outline(cls.setup, cls.run_client, cls.finalize)
        spec.expose_outputs(EonCalculation)
        spec.exit_code(400, "ERROR_SUBPROCESS", message="eonclient prefactor failed.")
        spec.exit_code(
            410,
            "ERROR_MISSING_TRIPLET",
            message="Prefactor needs calc.reactant, calc.saddle, and calc.product.",
        )

    def setup(self):
        calc_in = self.exposed_inputs(EonCalculation, namespace="calc")
        has_reactant = "reactant" in calc_in or "structure" in calc_in
        if not has_reactant or "saddle" not in calc_in or "product" not in calc_in:
            return self.exit_codes.ERROR_MISSING_TRIPLET
        raw = self.inputs.parameters.get_dict() if "parameters" in self.inputs else {}
        self.ctx.parameters = force_job(raw, "prefactor")

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
