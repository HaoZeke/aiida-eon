"""eOn file adapters: ``config.ini`` and ``results.dat``.

These match ``eon_schema.config.ini.write_ini`` and
``eon_schema.jobs.results_dat_to_dict`` so the plugin does not require
the eOn monorepo at import time.
"""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any, Mapping

from .jobs import JobSpec

IniSections = dict[str, dict[str, Any]]

_TIMING_KEYS = frozenset({"time_seconds", "user_time", "system_time"})


def format_ini_value(value: Any) -> str:
    """Format a Python value for eOn ``config.ini`` (lowercase bools)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def write_ini(path: str | Path, sections: Mapping[str, Mapping[str, Any]]) -> Path:
    """Write nested section dicts to ``config.ini``, preserving option case."""
    out = Path(path)
    parser = configparser.ConfigParser()
    parser.optionxform = str  # type: ignore[method-assign, assignment]
    for section, options in sections.items():
        if not parser.has_section(section):
            parser.add_section(section)
        for key, val in options.items():
            parser.set(section, str(key), format_ini_value(val))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        parser.write(handle)
    return out


def read_ini(path: str | Path) -> IniSections:
    """Read ``config.ini`` into a nested dict (case-preserving keys)."""
    parser = configparser.ConfigParser()
    parser.optionxform = str  # type: ignore[method-assign, assignment]
    parsed = Path(path)
    if not parser.read(parsed):
        raise FileNotFoundError(f"config.ini not found: {path}")
    return {section: dict(parser.items(section)) for section in parser.sections()}


def _parse_scalar(raw: str) -> Any:
    if "." in raw or "e" in raw.lower():
        try:
            return float(raw)
        except ValueError:
            pass
    try:
        return int(raw)
    except ValueError:
        return raw


def results_dat_to_dict(text: str) -> dict[str, Any]:
    """Parse classic ``results.dat`` lines (``value key``) into a dict."""
    results: dict[str, Any] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        key = parts[1]
        results[key] = _parse_scalar(parts[0])
    return results


def parse_fd_table(text: str) -> dict[str, Any]:
    """Parse finite_difference ``results.dat`` (header + two-column table)."""
    header: list[str] | None = None
    rows: list[list[float]] = []
    extras: dict[str, Any] = {}
    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        if len(parts) >= 2 and parts[1] in _TIMING_KEYS:
            extras[parts[1]] = _parse_scalar(parts[0])
            continue
        if header is None:
            header = parts
            continue
        try:
            rows.append([float(item) for item in parts])
        except ValueError:
            if len(parts) >= 2:
                extras[parts[1]] = _parse_scalar(parts[0])
    out: dict[str, Any] = {"table": rows, **extras}
    if header is not None:
        out["table_header"] = header
    return out


def parse_results_dat(text: str, style: str = "value_key") -> dict[str, Any]:
    """Dispatch on the job's ``results_style``."""
    if style == "fd_table":
        return parse_fd_table(text)
    return results_dat_to_dict(text)


def job_result_scalars(parsed: Mapping[str, Any]) -> dict[str, Any]:
    """Map parsed results.dat keys onto JobResult-oriented names."""
    out: dict[str, Any] = {
        "status_code": parsed.get("termination_reason", 0),
        "status_text": parsed.get("termination_reason_text", ""),
        "job_type": parsed.get("job_type", ""),
        "potential_type": parsed.get("potential_type", ""),
        "random_seed": parsed.get("random_seed", -1),
        "potential_energy": parsed.get(
            "potential_energy", parsed.get("Energy", 0.0)
        ),
        "potential_energy_saddle": parsed.get("potential_energy_saddle", 0.0),
        "potential_energy_reactant": parsed.get("potential_energy_reactant", 0.0),
        "potential_energy_product": parsed.get("potential_energy_product", 0.0),
        "barrier_reactant_to_product": parsed.get(
            "barrier_reactant_to_product", 0.0
        ),
        "barrier_product_to_reactant": parsed.get(
            "barrier_product_to_reactant", 0.0
        ),
        "prefactor_reactant_to_product": parsed.get(
            "prefactor_reactant_to_product", 0.0
        ),
        "prefactor_product_to_reactant": parsed.get(
            "prefactor_product_to_reactant", 0.0
        ),
        "displacement_saddle_distance": parsed.get(
            "displacement_saddle_distance", 0.0
        ),
        "force_calls": {
            "total": parsed.get("total_force_calls", parsed.get("force_calls", 0)),
            "minimization": parsed.get("force_calls_minimization", 0),
            "saddle": parsed.get("force_calls_saddle", 0),
            "prefactors": parsed.get("force_calls_prefactors", 0),
            "neb": parsed.get("force_calls_neb", 0),
        },
        "wall_time_seconds": parsed.get("time_seconds", 0.0),
        "user_time_seconds": parsed.get("user_time", 0.0),
        "system_time_seconds": parsed.get("system_time", 0.0),
    }
    if "simulation_time" in parsed:
        out["simulation_time"] = parsed["simulation_time"]
        out["md_temperature"] = parsed.get("md_temperature", 0.0)
        out["has_dynamics"] = True
    if "Energy" in parsed:
        out["Energy"] = parsed["Energy"]
    if "Max_Force" in parsed:
        out["Max_Force"] = parsed["Max_Force"]
    if "table" in parsed:
        out["table"] = parsed["table"]
        out["table_header"] = parsed.get("table_header")
    return out


def retrieve_list_for(spec: JobSpec) -> list[str]:
    """Deduplicated retrieve list for a job spec."""
    seen: set[str] = set()
    out: list[str] = []
    for name in spec.retrieve_globs + spec.output_cons + spec.extra_outputs:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


OUTPUT_CON_NAMES = (
    "min.con",
    "reactant.con",
    "product.con",
    "saddle.con",
    "mode.con",
    "displacement.con",
    "neb.con",
    "sp.con",
    "final.con",
    "out.con",
    "pos_out.con",
    "neb_maximage.con",
    "minimization.con",
    "climb.con",
)
