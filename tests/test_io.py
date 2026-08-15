"""Unit tests for config.ini and results.dat adapters (no AiiDA)."""

from pathlib import Path

from aiida_eon.io import read_ini, results_dat_to_dict, write_ini


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
    assert parsed["termination_reason"] == 0
    assert parsed["termination_reason_text"] == "good"
    assert parsed["job_type"] == "minimization"
    assert parsed["total_force_calls"] == 42
    assert abs(parsed["potential_energy"] - 1.234567890123) < 1e-12
    assert parsed["Energy"] == -2.5


def test_results_dat_skips_short_lines():
    assert results_dat_to_dict("\nonlyone\n") == {}
