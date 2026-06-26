"""Safe HWPX XML parser."""

from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from defusedxml import ElementTree as SafeET
except ImportError:  # pragma: no cover - fallback for minimal smoke environments
    SafeET = ET

from app.hwpx.document_model import Cell, Document, Paragraph, Section, Table, TextRun
from app.hwpx.namespaces import local_name
from app.tools.number_tools import parse_number


UNSUPPORTED_READONLY = {"pic", "equation", "chart", "shape", "ole"}


class HwpxParseError(ValueError):
    """Raised for XML that cannot be safely parsed."""


def parse_xml_file(path: Path) -> ET.Element:
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise HwpxParseError(f"DTD/entity declarations are disabled: {path.name}")
    try:
        return SafeET.fromstring(raw)
    except Exception as exc:  # defusedxml exposes several XML exception classes
        raise HwpxParseError(f"failed to parse XML: {path}") from exc


def parse_document(document_id: str, filename: str, workspace_dir: Path) -> Document:
    sections: list[Section] = []
    all_tables: list[Table] = []
    unsupported: set[str] = set()
    xml_files = sorted(workspace_dir.rglob("*.xml"))
    section_files = [p for p in xml_files if "section" in p.name.lower() or "bodytext" in str(p).lower()]
    targets = section_files or xml_files

    for section_index, xml_path in enumerate(targets, start=1):
        root = parse_xml_file(xml_path)
        relative = xml_path.relative_to(workspace_dir).as_posix()
        for elem in root.iter():
            lname = local_name(elem.tag).lower()
            if lname in UNSUPPORTED_READONLY:
                unsupported.add(lname)
        paragraphs = _extract_paragraphs(root, relative, section_index)
        tables = _extract_tables(root, relative, section_index)
        all_tables.extend(tables)
        sections.append(
            Section(
                id=f"sec-{section_index}",
                order=section_index,
                paragraphs=paragraphs,
                tables=tables,
            )
        )
    return Document(
        id=document_id,
        filename=filename,
        sections=sections,
        tables=all_tables,
        metadata={"xml_files": [p.relative_to(workspace_dir).as_posix() for p in xml_files]},
        unsupported_elements=sorted(unsupported),
    )


def _extract_paragraphs(root: ET.Element, source_xml_path: str, section_index: int) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    p_index = 0
    table_descendants = {
        descendant
        for table in root.iter()
        if local_name(table.tag).lower() in {"tbl", "table"}
        for descendant in table.iter()
    }
    for elem in root.iter():
        if local_name(elem.tag).lower() not in {"p", "paragraph"}:
            continue
        if elem in table_descendants:
            continue
        texts = _text_nodes(elem)
        text = "".join(node.text or "" for node in texts)
        if not text:
            continue
        p_index += 1
        runs = [
            TextRun(
                id=f"sec-{section_index}-p-{p_index}-run-{run_index}",
                text=node.text or "",
                source_xml_path=source_xml_path,
            )
            for run_index, node in enumerate(texts, start=1)
        ]
        paragraphs.append(
            Paragraph(
                id=f"sec-{section_index}-p-{p_index}",
                text=text,
                runs=runs,
                source_xml_path=source_xml_path,
            )
        )
    return paragraphs


def _extract_tables(root: ET.Element, source_xml_path: str, section_index: int) -> list[Table]:
    tables: list[Table] = []
    table_index = 0
    for tbl in root.iter():
        if local_name(tbl.tag).lower() not in {"tbl", "table"}:
            continue
        table_index += 1
        cells: list[Cell] = []
        row_index = 0
        max_columns = 0
        for row in _children_by_name(tbl, {"tr", "row"}):
            row_index += 1
            col_index = 0
            for cell in _children_by_name(row, {"tc", "cell"}):
                col_index += 1
                text = "".join(node.text or "" for node in _text_nodes(cell)).strip()
                max_columns = max(max_columns, col_index)
                cells.append(
                    Cell(
                        id=f"table-{section_index}-{table_index}-r{row_index}-c{col_index}",
                        row=row_index,
                        column=col_index,
                        text=text,
                        numeric_value=parse_number(text).value if parse_number(text) else None,
                        source_xml_path=source_xml_path,
                    )
                )
        if cells:
            tables.append(
                Table(
                    id=f"table-{section_index}-{table_index}",
                    rows=row_index,
                    columns=max_columns,
                    cells=cells,
                    source_xml_path=source_xml_path,
                )
            )
    return tables


def _children_by_name(elem: ET.Element, names: set[str]) -> list[ET.Element]:
    return [child for child in list(elem) if local_name(child.tag).lower() in names]


def _text_nodes(elem: ET.Element) -> list[ET.Element]:
    nodes = [node for node in elem.iter() if local_name(node.tag).lower() in {"t", "text"} and node.text]
    if nodes:
        return nodes
    return [elem] if elem.text else []
