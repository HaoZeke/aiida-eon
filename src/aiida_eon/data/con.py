"""``eon.con`` data: an eOn CON geometry stored as a single file."""

from __future__ import annotations

from pathlib import Path

from aiida.orm import SinglefileData


class ConData(SinglefileData):
    """eOn CON text (readcon / ``pos.con``).

    Does not import readcon or pyeonclient. The bytes on disk are the
    contract. Optional ASE conversion lives behind ``to_ase`` if ASE
    and a CON reader are installed.
    """

    def __init__(self, file, filename: str | None = None, **kwargs):
        super().__init__(file=file, filename=filename or "pos.con", **kwargs)

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
