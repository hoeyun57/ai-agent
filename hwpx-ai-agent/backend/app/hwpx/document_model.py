"""Internal document model exposed to tools, APIs, and LLM context."""

from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class TextRun(BaseModel):
    id: str
    text: str
    source_xml_path: str


class Paragraph(BaseModel):
    id: str
    text: str
    runs: list[TextRun] = Field(default_factory=list)
    style_reference: str | None = None
    source_xml_path: str


class Cell(BaseModel):
    id: str
    row: int
    column: int
    text: str
    numeric_value: Decimal | None = None
    style_reference: str | None = None
    source_xml_path: str


class Table(BaseModel):
    id: str
    rows: int
    columns: int
    cells: list[Cell] = Field(default_factory=list)
    merged_ranges: list[dict[str, int]] = Field(default_factory=list)
    source_xml_path: str


class Section(BaseModel):
    id: str
    order: int
    paragraphs: list[Paragraph] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)


class Document(BaseModel):
    id: str
    filename: str
    sections: list[Section] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    unsupported_elements: list[str] = Field(default_factory=list)

    @property
    def paragraphs(self) -> list[Paragraph]:
        return [paragraph for section in self.sections for paragraph in section.paragraphs]

