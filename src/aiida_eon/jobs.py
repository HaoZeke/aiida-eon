"""Catalog of eOn job types and their workdir I/O.

Mirrors C++ ``JobType`` / ``makeJob`` and the Python server
``select_job_runner``. File-IPC (``config.ini`` + ``.con`` +
``results.dat``) is the durable contract; pyeonclient / ``JobResult``
are in-process replacements and are not scheduled by this plugin.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class JobSpec:
    """One eOn job's workdir contract."""

    name: str
    runner: str
    structure_dest: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    output_cons: tuple[str, ...]
    extra_outputs: tuple[str, ...]
    retrieve_globs: tuple[str, ...]
    results_style: str
    notes: str = ""


_ALWAYS_RETRIEVE: tuple[str, ...] = (
    "results.dat",
    "client.log",
    "_potcalls.json",
    "*.con",
)


def _client(
    name: str,
    *,
    structure_dest: str = "pos.con",
    required_inputs: tuple[str, ...] = (),
    optional_inputs: tuple[str, ...] = (),
    output_cons: tuple[str, ...] = (),
    extra_outputs: tuple[str, ...] = (),
    retrieve_globs: tuple[str, ...] = (),
    results_style: str = "value_key",
    notes: str = "",
) -> JobSpec:
    return JobSpec(
        name=name,
        runner="eonclient",
        structure_dest=structure_dest,
        required_inputs=required_inputs,
        optional_inputs=optional_inputs,
        output_cons=output_cons,
        extra_outputs=extra_outputs,
        retrieve_globs=_ALWAYS_RETRIEVE + retrieve_globs,
        results_style=results_style,
        notes=notes,
    )


CLIENT_JOBS: dict[str, JobSpec] = {
    "minimization": _client(
        "minimization",
        required_inputs=("pos.con",),
        output_cons=("min.con", "minimization.con"),
        extra_outputs=("minimization.dat",),
        retrieve_globs=("minimization.dat",),
    ),
    "point": _client(
        "point",
        required_inputs=("pos.con",),
        results_style="point",
        notes="results.dat keys are Energy / Max_Force.",
    ),
    "saddle_search": _client(
        "saddle_search",
        required_inputs=("pos.con",),
        optional_inputs=("displacement.con", "direction.dat"),
        output_cons=("saddle.con", "climb.con"),
        extra_outputs=("mode.dat", "climb.dat"),
        retrieve_globs=("mode.dat", "climb.dat", "displacement_cp.con", "mode_cp.dat"),
    ),
    "process_search": _client(
        "process_search",
        required_inputs=("pos.con",),
        optional_inputs=("displacement.con", "direction.dat"),
        output_cons=("reactant.con", "saddle.con", "product.con"),
        extra_outputs=("mode.dat",),
        retrieve_globs=("mode.dat", "neb_initial_band.con", "saddle_initial_guess.con"),
    ),
    "nudged_elastic_band": _client(
        "nudged_elastic_band",
        structure_dest="reactant.con",
        required_inputs=("reactant.con", "product.con"),
        optional_inputs=("ts.con",),
        output_cons=("neb.con", "sp.con", "neb_maximage.con"),
        extra_outputs=("neb.dat",),
        retrieve_globs=(
            "neb.dat",
            "neb_*.dat",
            "neb_path_*.con",
            "peak*_pos.con",
            "peak*_mode.dat",
        ),
        notes="structure maps to reactant.con. Geometric springs: "
        "[Nudged Elastic Band] elastic_band. Path init: LINEAR / IDPP / "
        "IDPP_COLLECTIVE / SIDPP / SIDPP_ZBL / FILE.",
    ),
    "prefactor": _client(
        "prefactor",
        structure_dest="reactant.con",
        required_inputs=("reactant.con", "saddle.con", "product.con"),
        extra_outputs=("freq.dat",),
        retrieve_globs=("freq.dat",),
        notes="results.dat key good is a string true/false.",
    ),
    "hessian": _client(
        "hessian",
        required_inputs=("pos.con",),
        extra_outputs=("hessian.dat", "hessian.ckpt"),
        retrieve_globs=("hessian.dat", "hessian.ckpt"),
    ),
    "finite_difference": _client(
        "finite_difference",
        required_inputs=("pos.con",),
        results_style="fd_table",
        notes="results.dat is a dR/curvature table, not value-key.",
    ),
    "dynamics": _client(
        "dynamics",
        required_inputs=("pos.con",),
        output_cons=("final.con",),
        results_style="empty",
        notes="No results.dat body; ClientEON still appends timing.",
    ),
    "monte_carlo": _client(
        "monte_carlo",
        required_inputs=("pos.con",),
        optional_inputs=("pos_cp.con",),
        output_cons=("out.con",),
    ),
    "basin_hopping": _client(
        "basin_hopping",
        required_inputs=("pos.con",),
        output_cons=("min.con",),
        extra_outputs=("bh.dat", "movie.xyz"),
        retrieve_globs=("bh.dat", "movie.xyz", "min_*.con", "energy_*.dat"),
    ),
    "global_optimization": _client(
        "global_optimization",
        required_inputs=("pos.con",),
        extra_outputs=("monitoring.dat", "earr.dat"),
        retrieve_globs=("monitoring.dat", "earr.dat"),
        results_style="empty",
    ),
    "parallel_replica": _client(
        "parallel_replica",
        required_inputs=("pos.con",),
        output_cons=("reactant.con", "product.con"),
    ),
    "safe_hyperdynamics": _client(
        "safe_hyperdynamics",
        required_inputs=("pos.con",),
        output_cons=("reactant.con", "product.con", "saddle.con"),
    ),
    "tad": _client(
        "tad",
        required_inputs=("pos.con",),
        output_cons=("reactant.con", "product.con", "saddle.con"),
    ),
    "replica_exchange": _client(
        "replica_exchange",
        required_inputs=("pos.con",),
        output_cons=("pos_out.con",),
    ),
    "gp_surrogate": _client(
        "gp_surrogate",
        structure_dest="reactant.con",
        required_inputs=("reactant.con", "product.con"),
        retrieve_globs=("neb_final_gpr_*.con",),
        results_style="empty",
        notes="WITH_GP_SURROGATE build. Writes neb_final_gpr_*.con; no saveData neb.con.",
    ),
    "oh_tst": _client(
        "oh_tst",
        required_inputs=("pos.con", "product.con"),
        extra_outputs=("oh_tst_progression.dat",),
        retrieve_globs=("oh_tst_progression.dat",),
        notes="Client-only. Not in the server YAML / MainConfig job list.",
    ),
    "structure_comparison": _client(
        "structure_comparison",
        structure_dest="matter1.con",
        required_inputs=("matter1.con",),
        results_style="empty",
        notes="Client stub loads matter1.con only.",
    ),
}

SERVER_JOBS: dict[str, JobSpec] = {
    "akmc": JobSpec(
        name="akmc",
        runner="server",
        structure_dest="pos.con",
        required_inputs=("pos.con",),
        optional_inputs=(),
        output_cons=(),
        extra_outputs=(),
        retrieve_globs=(),
        results_style="value_key",
        notes="Python server loop. Use WorkflowFactory('eon.akmc').",
    ),
    "escape_rate": JobSpec(
        name="escape_rate",
        runner="server",
        structure_dest="pos.con",
        required_inputs=("pos.con",),
        optional_inputs=(),
        output_cons=(),
        extra_outputs=(),
        retrieve_globs=(),
        results_style="value_key",
        notes="Server farms dynamics / PR-like searches.",
    ),
    "unbiased_parallel_replica": JobSpec(
        name="unbiased_parallel_replica",
        runner="server",
        structure_dest="pos.con",
        required_inputs=("pos.con",),
        optional_inputs=(),
        output_cons=(),
        extra_outputs=(),
        retrieve_globs=(),
        results_style="value_key",
        notes="Server wrapper around client parallel_replica jobs.",
    ),
}

NOT_JOBS: dict[str, str] = {
    "serve": "eonclient --serve-* is a long-lived potential RPC, not a CalcJob.",
    "force_batch": "Potential.forceBatch is an engine path used by NEB and dimer, not a job.",
    "displacement_sampling": "GUI / tool only; not a select_job_runner key.",
    "test": "JobType::Test is bound in pyeonclient but is not in makeJob.",
    "geometric_neb": "There is no geometric-NEB job. Use nudged_elastic_band "
    "with [Nudged Elastic Band] elastic_band, or a geometric path init.",
}

JOB_ALIASES: dict[str, str] = {
    "finite_differences": "finite_difference",
    "molecular_dynamics": "dynamics",
    "neb": "nudged_elastic_band",
    "min": "minimization",
    "saddle": "saddle_search",
    "process": "process_search",
    "bh": "basin_hopping",
    "prd": "parallel_replica",
    "parrep": "parallel_replica",
}

POTENTIAL_TYPES: tuple[str, ...] = (
    "emt",
    "ext_pot",
    "lj",
    "ljcluster",
    "morse_pt",
    "cuh2",
    "tip4p",
    "tip4p_pt",
    "tip4p_h",
    "spce",
    "eam_al",
    "edip",
    "fehe",
    "lenosky_si",
    "sw_si",
    "tersoff_si",
    "vasp",
    "lammps",
    "mpi",
    "ams",
    "ams_io",
    "gpr",
    "catlearn",
    "xtb",
    "ase_orca",
    "ase_pot",
    "ase_nwchem",
    "metatomic",
    "zbl",
    "socketnwchem",
    "rgpot",
)

RGPOT_BACKENDS: tuple[str, ...] = ("nwchemc", "cpmdc", "metatomic", "xtb")

NEB_INITIALIZERS: tuple[str, ...] = (
    "linear",
    "idpp",
    "idpp_collective",
    "sidpp",
    "sidpp_zbl",
    "file",
)

INI_SECTIONS_CLIENT: tuple[str, ...] = (
    "Main",
    "Potential",
    "AMS",
    "AMS_IO",
    "AMS_ENV",
    "XTBPot",
    "ZBLPot",
    "SocketNWChemPot",
    "RgpotPot",
    "Debug",
    "Structure Comparison",
    "Process Search",
    "Optimizer",
    "Refine",
    "LBFGS",
    "CG",
    "Dimer",
    "Surrogate",
    "CatLearn",
    "ASE_ORCA",
    "ASE_NWCHEM",
    "Metatomic",
    "Serve",
    "Lanczos",
    "Davidson",
    "ARTn",
    "IRA",
    "GPR Dimer",
    "Prefactor",
    "Hessian",
    "Nudged Elastic Band",
    "Dynamics",
    "Parallel Replica",
    "TAD",
    "Replica Exchange",
    "Hyperdynamics",
    "Saddle Search",
    "Basin Hopping",
    "Global Optimization",
    "Monte Carlo",
    "BGSD",
    "OH_TST",
)

INI_SECTIONS_SERVER: tuple[str, ...] = (
    "Paths",
    "Communicator",
    "AKMC",
    "Recycling",
    "KDB",
    "Coarse Graining",
    "amsel",
    "Distributed Replica",
)

COMMUNICATOR_TYPES: tuple[str, ...] = (
    "cluster",
    "local",
    "local_lib",
    "inprocess",
    "local_inprocess",
    "mpi",
)

PORT_TO_DEST: dict[str, str] = {
    "structure": "",  # resolved from JobSpec.structure_dest
    "reactant": "reactant.con",
    "product": "product.con",
    "saddle": "saddle.con",
    "displacement": "displacement.con",
    "direction": "direction.dat",
    "matter2": "matter2.con",
    "mode": "direction.dat",
    "ts": "ts.con",
}


def normalize_job(name: str) -> str:
    """Lowercase INI token, applying SSOT aliases."""
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    return JOB_ALIASES.get(key, key)


def get_job_spec(name: str) -> JobSpec:
    """Return the client or server spec, or raise."""
    key = normalize_job(name)
    if key in CLIENT_JOBS:
        return CLIENT_JOBS[key]
    if key in SERVER_JOBS:
        raise ValueError(
            f"{key!r} is a Python-server / WorkChain job, not an eonclient "
            f"CalcJob. Use WorkflowFactory('eon.{key}') where registered, "
            "or run the eOn server."
        )
    if key in NOT_JOBS:
        raise ValueError(NOT_JOBS[key])
    raise KeyError(
        f"unknown eOn job {name!r}. Client jobs: "
        f"{', '.join(sorted(CLIENT_JOBS))}"
    )


def is_client_job(name: str) -> bool:
    return normalize_job(name) in CLIENT_JOBS


def neb_uses_file_path(sections: Mapping) -> bool:
    """True when NEB reads ``initial_path_in`` instead of endpoints."""
    neb = sections.get("Nudged Elastic Band") or sections.get(
        "Nudged_Elastic_Band"
    ) or {}
    init = str(neb.get("initializer") or neb.get("initial_path") or "").lower()
    return init == "file" and bool(neb.get("initial_path_in"))


def required_inputs_for(spec: JobSpec, sections: Mapping | None = None) -> tuple[str, ...]:
    """Required workdir files, relaxing NEB endpoints for initializer=file."""
    if spec.name == "nudged_elastic_band" and sections and neb_uses_file_path(sections):
        return ()
    return spec.required_inputs


def canonicalize_parameters(sections: dict) -> dict:
    """Copy INI sections and rewrite Main.job to the magic_enum token."""
    out = {name: dict(options) for name, options in sections.items()}
    job = job_from_parameters(out)
    main_key = "Main" if "Main" in out else "main"
    out.setdefault(main_key, {})
    out[main_key]["job"] = job
    return out


def job_from_parameters(sections: dict) -> str:
    """Read ``[Main] job`` from a nested INI dict."""
    main = sections.get("Main") or sections.get("main") or {}
    raw = main.get("job") or main.get("Job")
    if not raw:
        raise ValueError("parameters must set Main.job")
    return normalize_job(str(raw))
