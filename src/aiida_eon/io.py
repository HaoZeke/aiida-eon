"""eOn file adapters.

INI authorship is ``eon_schema.config.write_ini``, the same function
``rgpycrumbs.eon.helpers.write_eon_config`` wraps. ``results.dat`` goes
through ``eon_schema.jobs.results_dat_to_dict``. Saddle status codes
come from ``chemparseplot.parse.eon.saddle_search.EONSaddleStatus``.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from eon_schema.config import format_ini_value, read_ini, write_ini
from rgpycrumbs.eon.helpers import write_eon_config

from chemparseplot.parse.eon.saddle_search import EONSaddleStatus

try:
    from eon_schema.jobs import results_dat_to_dict as _schema_results_dat_to_dict
except ImportError:  # eon-schema < 0.2.3 (PyPI 0.2.2 has no jobs module)
    _schema_results_dat_to_dict = None

IniSections = dict[str, dict[str, Any]]

RESULTS_SCHEMA = "eon.results.v1"
COMPATIBILITY_SCHEMA = "eon.compatibility.v1"
RESULTS_COMPATIBILITY = {
    "con_spec_version": 3,
    "readcon_min_version": "0.14.7",
    "eon_schema_min_version": "0.2.0",
    "rgpycrumbs_min_version": "1.10.4",
    "chemparseplot_min_version": "1.9.17",
}


def compatibility_record(parsed: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the versioned stack identity carried by an eOn result.

    The raw ``results.dat`` keys remain at the top level. This nested record is
    the queryable provenance surface for consumers that need to reject an
    artifact without inspecting filenames or the execution environment.
    Missing engine build fields stay ``None`` rather than being inferred from
    package versions.
    """
    values = parsed or {}
    return {
        "schema": COMPATIBILITY_SCHEMA,
        "readcon": {
            "spec_version": RESULTS_COMPATIBILITY["con_spec_version"],
            "min_version": RESULTS_COMPATIBILITY["readcon_min_version"],
        },
        "eon_schema": {"min_version": RESULTS_COMPATIBILITY["eon_schema_min_version"]},
        "rgpycrumbs": {"min_version": RESULTS_COMPATIBILITY["rgpycrumbs_min_version"]},
        "chemparseplot": {
            "min_version": RESULTS_COMPATIBILITY["chemparseplot_min_version"]
        },
        "engine": {
            "id": values.get("potential_type", ""),
            "version": values.get("engine_version"),
            "abi_version": values.get("engine_abi_version"),
            "build_identity": values.get("engine_build_identity"),
        },
    }

_TIMING_KEYS = frozenset({"time_seconds", "user_time", "system_time"})
_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


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


def _local_results_dat_to_dict(text: str) -> dict[str, Any]:
    """Same contract as eon_schema.jobs.results_dat_to_dict plus last-token keys."""
    results: dict[str, Any] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        if _KEY_RE.match(parts[-1]) and (
            len(parts) > 2 or not _KEY_RE.match(parts[0])
        ):
            key = parts[-1]
            raw = " ".join(parts[:-1])
        else:
            key = parts[1]
            raw = parts[0]
        results[key] = raw if " " in raw else _parse_scalar(raw)
    return results


def results_dat_to_dict(text: str) -> dict[str, Any]:
    """Parse ``results.dat``.

    Prefers ``eon_schema.jobs.results_dat_to_dict`` (0.2.3+). PyPI 0.2.2
    has no jobs module, so the local implementation matches that
    contract and restores multi-word ``termination_reason_text``.
    """
    if _schema_results_dat_to_dict is None:
        parsed = _local_results_dat_to_dict(text)
    else:
        parsed = _schema_results_dat_to_dict(text)
        for line in text.splitlines():
            parts = line.split()
            if len(parts) > 2 and parts[-1] == "termination_reason_text":
                parsed["termination_reason_text"] = " ".join(parts[:-1])
    if not parsed:
        return {}
    return {
        "schema": RESULTS_SCHEMA,
        "compatibility": dict(RESULTS_COMPATIBILITY),
        "compatibility_record": compatibility_record(parsed),
        **parsed,
    }


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
            extras.update(results_dat_to_dict(line))
            continue
        if header is None:
            header = parts
            continue
        try:
            rows.append([float(item) for item in parts])
        except ValueError:
            extras.update(results_dat_to_dict(line))
    out: dict[str, Any] = {
        "schema": RESULTS_SCHEMA,
        "compatibility": dict(RESULTS_COMPATIBILITY),
        "compatibility_record": compatibility_record(extras),
        "table": rows,
        **extras,
    }
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
        "compatibility": parsed.get("compatibility_record", compatibility_record(parsed)),
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
    "compatibility_record",
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
