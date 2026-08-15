"""eOn file adapters: ``config.ini`` and ``results.dat``.

These match ``eon_schema.config.ini.write_ini`` and
``eon_schema.jobs.results_dat_to_dict`` so the plugin does not require
the eOn monorepo at import time.
"""

from __future__ import annotations

import configparser
from pathlib import Path
from typing import Any, Mapping

IniSections = dict[str, dict[str, Any]]


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


def results_dat_to_dict(text: str) -> dict[str, Any]:
    """Parse classic ``results.dat`` lines (``value key``) into a dict."""
    results: dict[str, Any] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        key = parts[1]
        raw = parts[0]
        if "." in raw or "e" in raw.lower():
            try:
                results[key] = float(raw)
                continue
            except ValueError:
                pass
        try:
            results[key] = int(raw)
        except ValueError:
            results[key] = raw
    return results


OUTPUT_CON_NAMES = (
    "min.con",
    "reactant.con",
    "product.con",
    "saddle.con",
    "mode.con",
    "displacement.con",
)
