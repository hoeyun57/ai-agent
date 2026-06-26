"""Validated table editing helpers."""

from pathlib import Path
from xml.etree import ElementTree as ET

from app.hwpx.namespaces import local_name
from app.hwpx.parser import parse_xml_file


def update_table_cell(workspace_dir: Path, table_id: str, row: int, column: int, value: str) -> dict[str, str]:
    """Update a table cell by parsed table coordinates."""

    section_idx, table_idx = _parse_table_id(table_id)
    table_xml_files = sorted(workspace_dir.rglob("*.xml"))
    section_files = [p for p in table_xml_files if "section" in p.name.lower() or "bodytext" in str(p).lower()]
    targets = section_files or table_xml_files
    if section_idx < 1 or section_idx > len(targets):
        raise ValueError("table section is out of range")
    xml_path = targets[section_idx - 1]
    root = parse_xml_file(xml_path)
    tables = [node for node in root.iter() if local_name(node.tag).lower() in {"tbl", "table"}]
    if table_idx < 1 or table_idx > len(tables):
        raise ValueError("table id is out of range")
    rows = [child for child in list(tables[table_idx - 1]) if local_name(child.tag).lower() in {"tr", "row"}]
    if row < 1 or row > len(rows):
        raise ValueError("row is out of range")
    cells = [child for child in list(rows[row - 1]) if local_name(child.tag).lower() in {"tc", "cell"}]
    if column < 1 or column > len(cells):
        raise ValueError("column is out of range")
    cell = cells[column - 1]
    text_nodes = [node for node in cell.iter() if local_name(node.tag).lower() in {"t", "text"}]
    before = "".join(node.text or "" for node in text_nodes)
    if text_nodes:
        text_nodes[0].text = value
        for node in text_nodes[1:]:
            node.text = ""
    else:
        ET.SubElement(cell, "t").text = value
    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    return {
        "source_xml_path": xml_path.relative_to(workspace_dir).as_posix(),
        "cell": f"{table_id}-r{row}-c{column}",
        "before": before,
        "after": value,
    }


def update_multiple_cells(workspace_dir: Path, updates: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        update_table_cell(
            workspace_dir=workspace_dir,
            table_id=str(update["table_id"]),
            row=int(update["row"]),
            column=int(update["column"]),
            value=str(update["value"]),
        )
        for update in updates
    ]


def _parse_table_id(table_id: str) -> tuple[int, int]:
    parts = table_id.split("-")
    if len(parts) != 3 or parts[0] != "table":
        raise ValueError("invalid table id")
    return int(parts[1]), int(parts[2])

