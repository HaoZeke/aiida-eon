"""Job catalog contracts (no AiiDA)."""

import pytest

from aiida_eon.jobs import (
    CLIENT_JOBS,
    INI_SECTIONS_CLIENT,
    NOT_JOBS,
    POTENTIAL_TYPES,
    SERVER_JOBS,
    get_job_spec,
    is_client_job,
    job_from_parameters,
    normalize_job,
)
from aiida_eon.io import retrieve_list_for


def test_all_makejob_tokens_registered():
    expected = {
        "process_search",
        "saddle_search",
        "minimization",
        "point",
        "parallel_replica",
        "safe_hyperdynamics",
        "tad",
        "replica_exchange",
        "basin_hopping",
        "hessian",
        "finite_difference",
        "nudged_elastic_band",
        "dynamics",
        "prefactor",
        "global_optimization",
        "structure_comparison",
        "monte_carlo",
        "gp_surrogate",
        "oh_tst",
    }
    assert expected == set(CLIENT_JOBS)


def test_aliases():
    assert normalize_job("NEB") == "nudged_elastic_band"
    assert normalize_job("finite_differences") == "finite_difference"
    assert normalize_job("molecular_dynamics") == "dynamics"
    assert normalize_job("min") == "minimization"


def test_server_jobs_are_not_client():
    assert not is_client_job("akmc")
    with pytest.raises(ValueError, match="WorkChain"):
        get_job_spec("akmc")
    with pytest.raises(ValueError, match="RPC"):
        get_job_spec("serve")
    with pytest.raises(ValueError, match="forceBatch"):
        get_job_spec("force_batch")
    with pytest.raises(ValueError, match="geometric"):
        get_job_spec("geometric_neb")


def test_neb_requires_endpoints():
    spec = get_job_spec("nudged_elastic_band")
    assert "reactant.con" in spec.required_inputs
    assert "product.con" in spec.required_inputs
    assert "neb.dat" in retrieve_list_for(spec)


def test_fd_style():
    assert get_job_spec("finite_difference").results_style == "fd_table"


def test_job_from_parameters():
    assert job_from_parameters({"Main": {"job": "OH_TST"}}) == "oh_tst"
    with pytest.raises(ValueError):
        job_from_parameters({"Potential": {"potential": "lj"}})


def test_newer_surfaces_named():
    assert "metatomic" in POTENTIAL_TYPES
    assert "rgpot" in POTENTIAL_TYPES
    assert "Metatomic" in INI_SECTIONS_CLIENT
    assert "RgpotPot" in INI_SECTIONS_CLIENT
    assert "Serve" in INI_SECTIONS_CLIENT
    assert "OH_TST" in INI_SECTIONS_CLIENT
    assert "akmc" in SERVER_JOBS
    assert "serve" in NOT_JOBS
