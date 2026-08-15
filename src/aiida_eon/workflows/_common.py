"""Shared WorkChain helpers."""

from __future__ import annotations

from aiida.orm import Dict


def force_job(parameters: dict | None, job: str) -> Dict:
    """Copy INI sections and pin ``Main.job``."""
    sections = dict(parameters or {})
    main = dict(sections.get("Main") or {})
    main["job"] = job
    sections["Main"] = main
    return Dict(dict=sections)
