"""HWPX package operations."""

from pathlib import Path
from shutil import copy2
from zipfile import ZIP_DEFLATED, ZipFile

from app.security.zip_security import safe_extract


class HwpxPackage:
    """A safely extracted HWPX workspace."""

    def __init__(self, original_path: Path, workspace_dir: Path) -> None:
        self.original_path = original_path
        self.workspace_dir = workspace_dir

    @classmethod
    def open(
        cls,
        original_path: Path,
        workspace_dir: Path,
        max_members: int,
        max_uncompressed: int,
    ) -> "HwpxPackage":
        safe_extract(original_path, workspace_dir, max_members, max_uncompressed)
        return cls(original_path=original_path, workspace_dir=workspace_dir)

    def xml_files(self) -> list[Path]:
        return sorted(self.workspace_dir.rglob("*.xml"))

    def section_files(self) -> list[Path]:
        files = [
            path
            for path in self.xml_files()
            if "section" in path.name.lower() or "bodytext" in str(path).lower()
        ]
        return files or self.xml_files()

    def repack(self, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        with ZipFile(temp_path, "w", compression=ZIP_DEFLATED) as archive:
            for path in sorted(self.workspace_dir.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(self.workspace_dir).as_posix())
        temp_path.replace(output_path)
        return output_path


def create_backup(source: Path, backup_dir: Path, document_id: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{document_id}.hwpx"
    copy2(source, backup_path)
    return backup_path

