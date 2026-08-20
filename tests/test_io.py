"""Unit tests for config.ini and results.dat adapters (no AiiDA)."""

from pathlib import Path

from aiida_eon.io import (
    EONSaddleStatus,
    job_failed,
    job_result_scalars,
    link_label,
    parse_fd_table,
    parse_results_dat,
    read_ini,
    results_dat_to_dict,
    write_eon_config,
    write_ini,
)


def test_io_delegates_to_ecosystem():
    from eon_schema.config import write_ini as schema_write
    from rgpycrumbs.eon.helpers import write_eon_config as official

    assert write_ini is schema_write
    assert write_eon_config is official
    assert EONSaddleStatus.GOOD.value == 0
    assert link_label("_potcalls.json") == "potcalls_json"
    assert link_label("neb.dat") == "neb_dat"


def test_write_ini_preserves_section_and_option_case(tmp_path: Path):
    path = tmp_path / "config.ini"
    write_ini(
        path,
        {
            "Main": {"job": "minimization"},
            "Potential": {"potential": "lj"},
            "Optimizer": {"opt_method": "lbfgs", "converged_force": 0.01},
        },
    )
    text = path.read_text(encoding="utf-8")
    assert "[Main]" in text
    assert "job = minimization" in text
    assert "[Potential]" in text
    assert "potential = lj" in text
    assert "converged_force = 0.01" in text
    loaded = read_ini(path)
    assert loaded["Main"]["job"] == "minimization"
    assert loaded["Optimizer"]["opt_method"] == "lbfgs"


def test_write_ini_lowercase_bools(tmp_path: Path):
    path = tmp_path / "config.ini"
    write_ini(path, {"Dimer": {"improved": True, "remove_rotation": False}})
    text = path.read_text(encoding="utf-8")
    assert "improved = true" in text
    assert "remove_rotation = false" in text


def test_results_dat_to_dict_scalars():
    sample = (
        "0 termination_reason\n"
        "good termination_reason_text\n"
        "minimization job_type\n"
        "lj potential_type\n"
        "42 total_force_calls\n"
        "1.234567890123e+00 potential_energy\n"
        "-2.5 Energy\n"
    )
    parsed = results_dat_to_dict(sample)
    assert parsed["schema"] == "eon.results.v1"
    assert parsed["compatibility"]["con_spec_version"] == 3
    assert parsed["compatibility"]["readcon_min_version"] == "0.14.7"
    assert parsed["compatibility_record"]["schema"] == "eon.compatibility.v1"
    assert parsed["compatibility_record"]["readcon"]["spec_version"] == 3
    assert parsed["compatibility_record"]["readcon"]["min_version"] == "0.14.7"
    assert parsed["compatibility_record"]["engine"]["id"] == "lj"
    assert parsed["termination_reason"] == 0
    assert parsed["termination_reason_text"] == "good"
    assert parsed["job_type"] == "minimization"
    assert parsed["total_force_calls"] == 42
    assert abs(parsed["potential_energy"] - 1.234567890123) < 1e-12
    assert parsed["Energy"] == -2.5


def test_results_dat_uses_explicit_compatibility_fields():
    parsed = results_dat_to_dict(
        """0 termination_reason
metatomic engine_id
0.14.8 compatibility_readcon_min_version
2.0.0 engine_version
abc123 engine_build_identity
"""
    )
    assert parsed["compatibility_record"]["readcon"]["min_version"] == "0.14.8"
    assert parsed["compatibility_record"]["engine"] == {
        "id": "metatomic",
        "version": "2.0.0",
        "abi_version": None,
        "build_identity": "abc123",
    }


def test_results_dat_preserves_complete_engine_compatibility_stamp():
    parsed = results_dat_to_dict(
        """eon.compatibility.v1 compatibility_schema
eon engine_id
eon.objective compatibility_engine_protocol_family
1 compatibility_engine_protocol_major
0 compatibility_engine_protocol_minor
1 compatibility_engine_abi_major
0 compatibility_engine_abi_minor
2 compatibility_engine_layout_revision
eon-2.11.1+abc123 engine_build_identity
3 compatibility_readcon_spec_version
0.14.7 compatibility_readcon_min_version
0.2.0 compatibility_eon_schema_min_version
1.10.4 compatibility_rgpycrumbs_min_version
1.9.17 compatibility_chemparseplot_min_version
"""
    )
    assert parsed["compatibility_record"]["engine_compatibility"] == {
        "schema": "eon.compatibility.v1",
        "engineId": "eon",
        "protocolFamily": "eon.objective",
        "protocolMajor": 1,
        "protocolMinor": 0,
        "abiMajor": 1,
        "abiMinor": 0,
        "layoutRevision": 2,
        "buildIdentity": "eon-2.11.1+abc123",
        "readconSpecVersion": 3,
        "readconMinVersion": "0.14.7",
        "eonSchemaMinVersion": "0.2.0",
        "rgpycrumbsMinVersion": "1.10.4",
        "chemparseplotMinVersion": "1.9.17",
    }


def test_results_dat_skips_short_lines():
    assert results_dat_to_dict("\nonlyone\n") == {}


def test_parse_fd_table_and_timing_footer():
    text = (
        "dR curvature\n"
        "0.001 1.23\n"
        "0.002 1.24\n"
        "1.5 time_seconds\n"
    )
    parsed = parse_fd_table(text)
    assert parsed["schema"] == "eon.results.v1"
    assert parsed["table_header"] == ["dR", "curvature"]
    assert parsed["table"][0] == [0.001, 1.23]
    assert parsed["time_seconds"] == 1.5
    assert parse_results_dat(text, style="fd_table")["table"][1] == [0.002, 1.24]


def test_job_result_scalars_energy_fallback():
    parsed = results_dat_to_dict(" -2.5 Energy\n 12 total_force_calls\n")
    scalars = job_result_scalars(parsed)
    assert scalars["potential_energy"] == -2.5
    assert scalars["force_calls"]["total"] == 12
    assert scalars["status_code"] is None
    assert scalars["compatibility"]["schema"] == "eon.compatibility.v1"


def test_results_dat_multiword_status_text():
    parsed = results_dat_to_dict(
        "3 termination_reason\n"
        "Too many iterations termination_reason_text\n"
    )
    assert parsed["termination_reason"] == 3
    assert parsed["termination_reason_text"] == "Too many iterations"
    assert job_result_scalars(parsed)["status_code"] == 3
    assert job_failed(parsed)
    assert not job_failed({"termination_reason": 0})
    assert job_failed({"good": "false"})
    assert job_failed({"converged": False})
