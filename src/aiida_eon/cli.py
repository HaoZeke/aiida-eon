"""verdi data eon ..."""

from __future__ import annotations

from pathlib import Path

import click
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import decorators, echo


@click.group("eon")
def data_cli():
    """Commands for eOn CON data and job catalog."""


@data_cli.command("export")
@arguments.DATUM()
@click.option("-o", "--output", type=click.Path(), required=True)
@decorators.with_dbenv()
def export_con(datum, output):
    """Write a stored CON node to a file."""
    if not hasattr(datum, "get_content"):
        echo.echo_critical("node has no file content")
    content = datum.get_content()
    path = Path(output)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    echo.echo_success(f"wrote {path}")


@data_cli.command("jobs")
def list_jobs():
    """Print the client / server / non-job catalog."""
    from .jobs import CLIENT_JOBS, NOT_JOBS, SERVER_JOBS

    for name in sorted(CLIENT_JOBS):
        spec = CLIENT_JOBS[name]
        echo.echo(f"{name:28} eonclient  {spec.results_style}")
    for name in sorted(SERVER_JOBS):
        echo.echo(f"{name:28} workchain/server")
    for name, reason in sorted(NOT_JOBS.items()):
        echo.echo(f"{name:28} not-a-job  {reason}")
