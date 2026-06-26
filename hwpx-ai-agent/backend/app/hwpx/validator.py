"""HWPX package and content validators."""

from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

from app.hwpx.document_model import Document, Table
from app.hwpx.parser import parse_xml_file
from app.security.zip_security import inspect_zip
from app.tools.number_tools import parse_number


def validate_hwpx_package(path: Path, max_members: int = 3000, max_uncompressed: int = 250 * 1024 * 1024) -> dict[str, object]:
    names = inspect_zip(path, max_members=max_members, max_uncompressed=max_uncompressed)
    xml_errors: list[str] = []
    with ZipFile(path) as archive:
        for name in names:
            if not name.lower().endswith(".xml"):
                continue
            data = archive.read(name)
            temp = path.parent / f".validate-{Path(name).name}"
            temp.write_bytes(data)
            try:
                parse_xml_file(temp)
            except Exception as exc:
                xml_errors.append(f"{name}: {exc}")
            finally:
                temp.unlink(missing_ok=True)
    return {
        "valid": not xml_errors,
        "xml_errors": xml_errors,
        "member_count": len(names),
        "has_section": any("section" in name.lower() for name in names),
    }


def validate_required_fields(document: Document, fields: list[str]) -> list[dict[str, str]]:
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return [
        {"field": field, "status": "missing", "reason": "required text was not found"}
        for field in fields
        if field not in text
    ]


def validate_table_sums(table: Table) -> list[dict[str, object]]:
    """Detect simple rows/columns where a total cell differs from preceding values."""

    issues: list[dict[str, object]] = []
    by_row: dict[int, list] = {}
    for cell in table.cells:
        by_row.setdefault(cell.row, []).append(cell)
    for row, cells in by_row.items():
        numeric = [cell for cell in sorted(cells, key=lambda item: item.column) if cell.numeric_value is not None]
        if len(numeric) < 3:
            continue
        declared = numeric[-1].numeric_value or Decimal(0)
        sources = numeric[:-1]
        calculated = sum((cell.numeric_value or Decimal(0) for cell in sources), Decimal(0))
        if declared != calculated:
            issues.append(
                {
                    "status": "mismatch",
                    "table_id": table.id,
                    "row": row,
                    "declared_total": str(declared),
                    "calculated_total": str(calculated),
                    "difference": str(calculated - declared),
                    "source_cells": [cell.id for cell in sources],
                }
            )
    return issues


def detect_inconsistent_numbers(document: Document) -> list[dict[str, object]]:
    body_numbers = {
        str(parsed.value)
        for paragraph in document.paragraphs
        if (parsed := parse_number(paragraph.text)) is not None
    }
    issues: list[dict[str, object]] = []
    for table in document.tables:
        for cell in table.cells:
            if cell.numeric_value is None:
                continue
            if str(cell.numeric_value) not in body_numbers:
                issues.append(
                    {
                        "status": "not_found_in_body",
                        "cell": cell.id,
                        "value": str(cell.numeric_value),
                        "reason": "table number was not found in body text",
                    }
                )
    return issues

