"""Job catalog contracts (no AiiDA)."""

import pytest

from aiida_eon.jobs import (
    CLIENT_JOBS,
    INI_SECTIONS_CLIENT,
    NOT_JOBS,
    POTENTIAL_TYPES,
    SERVER_JOBS,
    canonicalize_parameters,
    get_job_spec,
    is_client_job,
    job_from_parameters,
    normalize_job,
    required_inputs_for,
)
from aiida_eon.io import link_label
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


def test_canonicalize_rewrites_aliases():
    out = canonicalize_parameters({"Main": {"job": "neb"}, "Potential": {"potential": "lj"}})
    assert out["Main"]["job"] == "nudged_elastic_band"


def test_oh_tst_and_comparison_require_files():
    assert "product.con" in get_job_spec("oh_tst").required_inputs
    assert "matter1.con" in get_job_spec("structure_comparison").required_inputs
    assert "pos.con" in get_job_spec("minimization").required_inputs


def test_neb_file_initializer_drops_endpoints():
    spec = get_job_spec("nudged_elastic_band")
    sections = {
        "Main": {"job": "nudged_elastic_band"},
        "Nudged Elastic Band": {"initializer": "file", "initial_path_in": "path.list"},
    }
    assert required_inputs_for(spec, sections) == ()
    assert "reactant.con" in required_inputs_for(spec, {"Main": {"job": "neb"}})


def test_link_label_strips_leading_underscore():
    assert link_label("_potcalls.json") == "potcalls_json"
    assert link_label("neb.dat") == "neb_dat"


def test_newer_surfaces_named():
    assert "metatomic" in POTENTIAL_TYPES
    assert "rgpot" in POTENTIAL_TYPES
    assert "Metatomic" in INI_SECTIONS_CLIENT
    assert "RgpotPot" in INI_SECTIONS_CLIENT
    assert "Serve" in INI_SECTIONS_CLIENT
    assert "OH_TST" in INI_SECTIONS_CLIENT
    assert "akmc" in SERVER_JOBS
    assert "serve" in NOT_JOBS
