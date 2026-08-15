"""Process-search workchain (saddle + both minima + optional prefactors)."""

from __future__ import annotations

from aiida.engine import ToContext, WorkChain
from aiida.orm import Dict

from ..calculations import EonCalculation
from ._common import force_job


class EonProcessSearchWorkChain(WorkChain):
    """One eonclient ``process_search`` from a reactant."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.expose_inputs(EonCalculation, namespace="calc", exclude=("parameters",))
        spec.input(
            "parameters",
            valid_type=Dict,
            required=False,
            help="INI sections. Main.job is forced to process_search.",
        )
        spec.outline(cls.setup, cls.run_client, cls.finalize)
        spec.expose_outputs(EonCalculation)
        spec.exit_code(
            400,
            "ERROR_SUBPROCESS",
            message="eonclient process search failed.",
        )

    def setup(self):
        raw = self.inputs.parameters.get_dict() if "parameters" in self.inputs else {}
        self.ctx.parameters = force_job(raw, "process_search")

    def run_client(self):
        inputs = dict(self.exposed_inputs(EonCalculation, namespace="calc"))
        inputs["parameters"] = self.ctx.parameters
        return ToContext(calc=self.submit(EonCalculation, **inputs))

    def finalize(self):
        node = self.ctx.calc
        if not node.is_finished_ok:
            return self.exit_codes.ERROR_SUBPROCESS
        self.out_many(self.exposed_outputs(node, EonCalculation))
