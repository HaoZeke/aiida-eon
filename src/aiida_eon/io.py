"""eOn file adapters.

INI authorship is ``eon_schema.config.write_ini``, the same function
``rgpycrumbs.eon.helpers.write_eon_config`` wraps. ``results.dat`` goes
through ``eon_schema.jobs.results_dat_to_dict``. Saddle status codes
come from ``chemparseplot.parse.eon.saddle_search.EONSaddleStatus``.
"""

from __future__ import annotations

from typing import Any, Mapping

from eon_schema.config import format_ini_value, read_ini, write_ini
from eon_schema.jobs import results_dat_to_dict as _schema_results_dat_to_dict
from rgpycrumbs.eon.helpers import write_eon_config

from chemparseplot.parse.eon.saddle_search import EONSaddleStatus

IniSections = dict[str, dict[str, Any]]

_TIMING_KEYS = frozenset({"time_seconds", "user_time", "system_time"})


def results_dat_to_dict(text: str) -> dict[str, Any]:
    """Parse ``results.dat`` via eon-schema, then restore multi-word status.

    Client writers put ``describeStatus`` before the key
    (``Too many iterations termination_reason_text``). eon-schema still
    takes token[1] as the key; overlay the last-token form for that line.
    """
    parsed = _schema_results_dat_to_dict(text)
    for line in text.splitlines():
        parts = line.split()
        if len(parts) > 2 and parts[-1] == "termination_reason_text":
            parsed["termination_reason_text"] = " ".join(parts[:-1])
    return parsed


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
            extras.update(_schema_results_dat_to_dict(line))
            continue
        if header is None:
            header = parts
            continue
        try:
            rows.append([float(item) for item in parts])
        except ValueError:
            extras.update(_schema_results_dat_to_dict(line))
    out: dict[str, Any] = {"table": rows, **extras}
    if header is not None:
        out["table_header"] = header
    return out


def job_failed(parsed: Mapping[str, Any]) -> bool:
    """True when results.dat reports a failed client job.

    Saddle / process-search codes are ``EONSaddleStatus`` (GOOD == 0).
    """
    reason = parsed.get("termination_reason")
    if isinstance(reason, int) and reason != EONSaddleStatus.GOOD.value:
        return True
    good = parsed.get("good")
    if good is False:
        return True
    if isinstance(good, str) and good.lower() == "false":
        return True
    converged = parsed.get("converged")
    if converged in (False, 0):
        return True
    if isinstance(converged, str) and converged.lower() == "false":
        return True
    return False


def parse_results_dat(text: str, style: str = "value_key") -> dict[str, Any]:
    """Dispatch on the job's ``results_style``."""
    if style == "fd_table":
        return parse_fd_table(text)
    return results_dat_to_dict(text)


def job_result_scalars(parsed: Mapping[str, Any]) -> dict[str, Any]:
    """JobResult-shaped view. Missing ``termination_reason`` stays None."""
    out: dict[str, Any] = {
        "status_code": parsed.get("termination_reason"),
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


def link_label(name: str) -> str:
    """AiiDA link label: no leading underscore, no dots."""
    cleaned = name.replace(".", "_").replace("-", "_").replace("/", "_")
    cleaned = cleaned.lstrip("_")
    return cleaned or "file"


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

__all__ = [
    "EONSaddleStatus",
    "OUTPUT_CON_NAMES",
    "format_ini_value",
    "job_failed",
    "job_result_scalars",
    "link_label",
    "parse_fd_table",
    "parse_results_dat",
    "read_ini",
    "results_dat_to_dict",
    "write_eon_config",
    "write_ini",
]
