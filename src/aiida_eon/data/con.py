"""``eon.con`` data: an eOn CON geometry stored as a single file."""

from __future__ import annotations

from pathlib import Path

from aiida.orm import SinglefileData


CON_COMPATIBILITY = {
    "schema": "eon.compatibility.v1",
    "readcon": {"spec_version": 3, "min_version": "0.14.7"},
    "eon_schema": {"min_version": "0.2.0"},
    "rgpycrumbs": {"min_version": "1.10.4"},
    "chemparseplot": {"min_version": "1.9.17"},
}


class ConData(SinglefileData):
    """eOn CON text (readcon / ``pos.con``).

    Does not import readcon or pyeonclient. The bytes on disk are the
    contract. Optional ASE conversion lives behind ``to_ase`` if ASE
    and a CON reader are installed.
    """

    def __init__(self, file, filename: str | None = None, **kwargs):
        super().__init__(file=file, filename=filename or "pos.con", **kwargs)
        self.base.attributes.set("compatibility", CON_COMPATIBILITY)

    @property
    def compatibility(self) -> dict:
        """Versioned CON and stack compatibility metadata."""
        return self.base.attributes.get("compatibility")

    @classmethod
    def from_path(cls, path: str | Path, filename: str | None = None) -> ConData:
        resolved = Path(path).expanduser().resolve(strict=True)
        return cls(file=str(resolved), filename=filename or resolved.name)

    def get_text(self) -> str:
        """UTF-8 CON text."""
        content = self.get_content()
        if isinstance(content, bytes):
            return content.decode("utf-8")
        return content

    def write_file(self, path: str | Path) -> Path:
        out = Path(path)
        out.write_text(self.get_text(), encoding="utf-8")
        return out

    def to_ase(self):
        """ASE Atoms list via chemparseplot (readcon)."""
        import tempfile

        from chemparseplot.parse.eon.con_io import read_con_as_ase

        with tempfile.NamedTemporaryFile(
            "w", suffix=".con", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(self.get_text())
            tmp = Path(handle.name)
        try:
            return read_con_as_ase(tmp)
        finally:
            tmp.unlink(missing_ok=True)

    @classmethod
    def from_ase(cls, atoms, filename: str = "pos.con") -> ConData:
        """Write ASE Atoms (or a list) as CON via chemparseplot."""
        import tempfile

        from chemparseplot.parse.eon.con_io import write_atoms_as_con

        series = atoms if isinstance(atoms, (list, tuple)) else [atoms]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / filename
            write_atoms_as_con(path, series)
            return cls.from_path(path, filename=filename)
