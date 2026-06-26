"""Validated text editing tools for extracted HWPX XML."""

from pathlib import Path
from xml.etree import ElementTree as ET

from app.hwpx.namespaces import local_name
from app.hwpx.parser import parse_xml_file


def replace_text(workspace_dir: Path, target: str, replacement: str, scope: str = "all") -> list[dict[str, str]]:
    """Replace exact text in XML text nodes and return changed snippets."""

    if not target:
        raise ValueError("target text must not be empty")
    changes: list[dict[str, str]] = []
    for xml_path in sorted(workspace_dir.rglob("*.xml")):
        root = parse_xml_file(xml_path)
        changed = False
        for node in _editable_text_nodes(root):
            before = node.text or ""
            if target not in before:
                continue
            after = before.replace(target, replacement, 1 if scope == "first" else -1)
            if after != before:
                node.text = after
                changed = True
                changes.append(
                    {
                        "source_xml_path": xml_path.relative_to(workspace_dir).as_posix(),
                        "before": before,
                        "after": after,
                    }
                )
                if scope == "first":
                    break
        if changed:
            ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
        if scope == "first" and changes:
            break
    return changes


def update_paragraph(workspace_dir: Path, source_xml_path: str, paragraph_order: int, text: str) -> dict[str, str]:
    xml_path = workspace_dir / source_xml_path
    root = parse_xml_file(xml_path)
    paragraphs = _body_paragraphs(root)
    if paragraph_order < 1 or paragraph_order > len(paragraphs):
        raise ValueError("paragraph_order is out of range")
    paragraph = paragraphs[paragraph_order - 1]
    text_nodes = _editable_text_nodes(paragraph)
    before = "".join(node.text or "" for node in text_nodes)
    if not text_nodes:
        paragraph.text = text
    else:
        text_nodes[0].text = text
        for node in text_nodes[1:]:
            node.text = ""
    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    return {"source_xml_path": source_xml_path, "before": before, "after": text}


def insert_paragraph_after(workspace_dir: Path, source_xml_path: str, after_order: int, text: str) -> dict[str, str]:
    xml_path = workspace_dir / source_xml_path
    root = parse_xml_file(xml_path)
    paragraphs = _body_paragraphs(root)
    if not paragraphs:
        new_p = ET.SubElement(root, "p")
        ET.SubElement(new_p, "t").text = text
    else:
        index = min(max(after_order, 0), len(paragraphs) - 1)
        parent = _find_parent(root, paragraphs[index])
        if parent is None:
            raise ValueError("cannot find paragraph parent")
        new_p = ET.Element(paragraphs[index].tag, paragraphs[index].attrib)
        ET.SubElement(new_p, "t").text = text
        children = list(parent)
        parent.insert(children.index(paragraphs[index]) + 1, new_p)
    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    return {"source_xml_path": source_xml_path, "before": "", "after": text}


def append_paragraphs(workspace_dir: Path, source_xml_path: str, texts: list[str]) -> list[dict[str, str]]:
    """Append multiple generated paragraphs near the end of a section XML."""

    if not texts:
        raise ValueError("texts must not be empty")
    xml_path = workspace_dir / source_xml_path
    root = parse_xml_file(xml_path)
    paragraphs = _body_paragraphs(root)
    changes: list[dict[str, str]] = []
    if paragraphs:
        anchor = paragraphs[-1]
        parent = _find_parent(root, anchor)
        if parent is None:
            raise ValueError("cannot find paragraph parent")
        paragraph_tag = anchor.tag
        text_nodes = _editable_text_nodes(anchor)
        text_tag = text_nodes[0].tag if text_nodes else "t"
        insert_at = list(parent).index(anchor) + 1
        for offset, text in enumerate(texts):
            new_p = ET.Element(paragraph_tag, anchor.attrib)
            ET.SubElement(new_p, text_tag).text = text
            parent.insert(insert_at + offset, new_p)
            changes.append({"source_xml_path": source_xml_path, "before": "", "after": text})
    else:
        for text in texts:
            new_p = ET.SubElement(root, "p")
            ET.SubElement(new_p, "t").text = text
            changes.append({"source_xml_path": source_xml_path, "before": "", "after": text})
    ET.ElementTree(root).write(xml_path, encoding="utf-8", xml_declaration=True)
    return changes


def _editable_text_nodes(root: ET.Element) -> list[ET.Element]:
    nodes = [node for node in root.iter() if local_name(node.tag).lower() in {"t", "text"}]
    return nodes or [node for node in root.iter() if node.text]


def _body_paragraphs(root: ET.Element) -> list[ET.Element]:
    table_descendants = {
        descendant
        for table in root.iter()
        if local_name(table.tag).lower() in {"tbl", "table"}
        for descendant in table.iter()
    }
    return [
        node
        for node in root.iter()
        if local_name(node.tag).lower() in {"p", "paragraph"} and node not in table_descendants
    ]


def _find_parent(root: ET.Element, child: ET.Element) -> ET.Element | None:
    for node in root.iter():
        if child in list(node):
            return node
    return None

