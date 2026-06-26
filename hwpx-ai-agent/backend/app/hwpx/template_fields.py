"""Template placeholder detection for form-like HWPX documents."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.hwpx.document_model import Document


BRACED_FIELD_RE = re.compile(r"(\{\{\s*([^{}]{1,30}?)\s*\}\}|\[\s*([^\[\]]{1,30}?)\s*\])")
BLANK_RE = re.compile(r"(_{3,}|○{2,}|□{2,}|\.{3,})")
LABEL_RE = re.compile(r"^\s*([가-힣A-Za-z0-9 ]{1,20})\s*[:：]\s*(_{2,}|○{2,}|□{2,}|$)")


@dataclass(frozen=True)
class TemplateField:
    """A user-fillable placeholder found in text."""

    label: str
    target: str
    source_id: str
    source_xml_path: str
    context: str


def detect_template_fields(document: Document) -> list[TemplateField]:
    """Find simple form placeholders in body paragraphs and table cells."""

    fields: list[TemplateField] = []
    seen: set[tuple[str, str, str]] = set()

    for paragraph in document.paragraphs:
        fields.extend(
            _fields_from_text(
                text=paragraph.text,
                source_id=paragraph.id,
                source_xml_path=paragraph.source_xml_path,
                seen=seen,
            )
        )
    for table in document.tables:
        for cell in table.cells:
            fields.extend(
                _fields_from_text(
                    text=cell.text,
                    source_id=cell.id,
                    source_xml_path=cell.source_xml_path,
                    seen=seen,
                )
            )
    return fields[:80]


def _fields_from_text(text: str, source_id: str, source_xml_path: str, seen: set[tuple[str, str, str]]) -> list[TemplateField]:
    fields: list[TemplateField] = []
    for match in BRACED_FIELD_RE.finditer(text):
        label = (match.group(2) or match.group(3) or "항목").strip()
        fields.append(_make_field(label, match.group(1), source_id, source_xml_path, text, seen))

    label_match = LABEL_RE.search(text)
    if label_match:
        label = label_match.group(1).strip()
        target = label_match.group(2) or f"{label}:"
        fields.append(_make_field(label, target, source_id, source_xml_path, text, seen))
    else:
        for index, match in enumerate(BLANK_RE.finditer(text), start=1):
            fields.append(_make_field(f"빈칸{index}", match.group(1), source_id, source_xml_path, text, seen))
    return [field for field in fields if field is not None]


def _make_field(
    label: str,
    target: str,
    source_id: str,
    source_xml_path: str,
    context: str,
    seen: set[tuple[str, str, str]],
) -> TemplateField | None:
    key = (source_id, label, target)
    if key in seen:
        return None
    seen.add(key)
    return TemplateField(
        label=label,
        target=target,
        source_id=source_id,
        source_xml_path=source_xml_path,
        context=context[:300],
    )

