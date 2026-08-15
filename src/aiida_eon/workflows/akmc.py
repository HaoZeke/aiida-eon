"""AiiDA-native process-search campaign (not the Python AKMC server)."""

from __future__ import annotations

from aiida.engine import ToContext, WorkChain, while_
from aiida.orm import Dict, Int

from ..calculations import EonCalculation
from ._common import force_job


class EonAkmcWorkChain(WorkChain):
    """Submit ``n_searches`` client ``process_search`` jobs from one reactant.

    Superbasin KMC, recycling, and KDB stay on the eOn Python server
    (``[Main] job = akmc``). This workchain is the provenance-tracked
    explorer half: many independent saddles from the same basin.
    """

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
        spec.input(
            "n_searches",
            valid_type=Int,
            default=lambda: Int(4),
            help="How many independent process searches to launch.",
        )
        spec.input(
            "max_concurrent",
            valid_type=Int,
            default=lambda: Int(4),
            help="Maximum searches in flight at once.",
        )
        spec.outline(
            cls.setup,
            while_(cls.should_submit)(
                cls.submit_batch,
                cls.inspect_batch,
            ),
            cls.finalize,
        )
        spec.output("summary", valid_type=Dict)
        spec.output_namespace("searches", dynamic=True)
        spec.exit_code(
            400,
            "ERROR_NO_SUCCESS",
            message="No process_search job finished successfully.",
        )

    def setup(self):
        raw = self.inputs.parameters.get_dict() if "parameters" in self.inputs else {}
        self.ctx.parameters = force_job(raw, "process_search")
        self.ctx.n_searches = int(self.inputs.n_searches)
        self.ctx.max_concurrent = max(1, int(self.inputs.max_concurrent))
        self.ctx.submitted = 0
        self.ctx.finished = []
        self.ctx.ok = []
        self.ctx.batch_keys = []

    def should_submit(self):
        return self.ctx.submitted < self.ctx.n_searches

    def submit_batch(self):
        remaining = self.ctx.n_searches - self.ctx.submitted
        batch = min(self.ctx.max_concurrent, remaining)
        running = {}
        keys = []
        base = dict(self.exposed_inputs(EonCalculation, namespace="calc"))
        base["parameters"] = self.ctx.parameters
        for _ in range(batch):
            key = f"search_{self.ctx.submitted:04d}"
            running[key] = self.submit(EonCalculation, **base)
            keys.append(key)
            self.ctx.submitted += 1
        self.ctx.batch_keys = keys
        return ToContext(**running)

    def inspect_batch(self):
        for key in self.ctx.batch_keys:
            node = self.ctx[key]
            if key in self.ctx.finished:
                continue
            self.ctx.finished.append(key)
            if node.is_finished_ok:
                self.ctx.ok.append(key)
                self.out(f"searches.{key}", node.outputs.results)

    def finalize(self):
        if not self.ctx.ok:
            return self.exit_codes.ERROR_NO_SUCCESS
        barriers = []
        for key in self.ctx.ok:
            data = self.ctx[key].outputs.results.get_dict()
            if "barrier_reactant_to_product" in data:
                barriers.append(data["barrier_reactant_to_product"])
        self.out(
            "summary",
            Dict(
                dict={
                    "n_requested": self.ctx.n_searches,
                    "n_ok": len(self.ctx.ok),
                    "n_finished": len(self.ctx.finished),
                    "ok_keys": list(self.ctx.ok),
                    "barriers_reactant_to_product": barriers,
                }
            ),
        )
