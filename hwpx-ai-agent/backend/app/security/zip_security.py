"""Safe ZIP handling for HWPX packages."""

from pathlib import Path
from zipfile import BadZipFile, ZipFile

from app.security.file_security import SecurityError, resolve_within


class ZipSecurityError(SecurityError):
    """Raised for unsafe or invalid HWPX ZIP packages."""


def inspect_zip(path: Path, max_members: int, max_uncompressed: int) -> list[str]:
    """Validate ZIP metadata before extraction."""

    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > max_members:
                raise ZipSecurityError("too many files in HWPX package")
            total_size = 0
            names: list[str] = []
            for info in infos:
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or ".." in Path(name).parts:
                    raise ZipSecurityError(f"unsafe ZIP member path: {info.filename}")
                total_size += info.file_size
                if total_size > max_uncompressed:
                    raise ZipSecurityError("HWPX package expands beyond allowed size")
                names.append(name)
            return names
    except BadZipFile as exc:
        raise ZipSecurityError("invalid ZIP/HWPX package") from exc


def safe_extract(path: Path, target_dir: Path, max_members: int, max_uncompressed: int) -> list[Path]:
    """Extract ZIP members while preventing ZIP Slip."""

    inspect_zip(path, max_members=max_members, max_uncompressed=max_uncompressed)
    extracted: list[Path] = []
    target_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            destination = resolve_within(target_dir, target_dir / info.filename)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as sink:
                sink.write(source.read())
            extracted.append(destination)
    return extracted

