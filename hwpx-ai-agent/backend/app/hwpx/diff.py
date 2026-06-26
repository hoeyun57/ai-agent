"""Small document diff helpers."""

from difflib import unified_diff
from pathlib import Path
from zipfile import ZipFile


def generate_document_diff(before_hwpx: Path, after_hwpx: Path) -> str:
    before = _collect_xml_text(before_hwpx)
    after = _collect_xml_text(after_hwpx)
    return "\n".join(
        unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile=before_hwpx.name,
            tofile=after_hwpx.name,
            lineterm="",
        )
    )


def _collect_xml_text(path: Path) -> str:
    lines: list[str] = []
    with ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if name.lower().endswith(".xml"):
                lines.append(f"--- {name}")
                lines.append(archive.read(name).decode("utf-8", errors="replace"))
    return "\n".join(lines)

