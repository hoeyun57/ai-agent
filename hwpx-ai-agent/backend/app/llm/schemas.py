"""Strict schemas for model-produced work plans."""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReplaceTextArgs(StrictModel):
    document_id: str
    target: str
    replacement: str
    scope: Literal["all", "first"] = "all"


class UpdateParagraphArgs(StrictModel):
    document_id: str
    paragraph_id: str
    text: str


class UpdateTableCellArgs(StrictModel):
    document_id: str
    table_id: str
    row: int = Field(ge=1)
    column: int = Field(ge=1)
    value: str


class UpdateMultipleCellsArgs(StrictModel):
    document_id: str
    updates: list[UpdateTableCellArgs]


class InsertParagraphArgs(StrictModel):
    document_id: str
    source_xml_path: str
    after_order: int = Field(ge=0)
    text: str


class SaveAsNewDocumentArgs(StrictModel):
    document_id: str


class ToolAction(StrictModel):
    tool: Literal[
        "replace_text",
        "update_paragraph",
        "update_table_cell",
        "update_multiple_cells",
        "insert_paragraph",
        "save_as_new_document",
        "validate_table_sums",
        "detect_inconsistent_numbers",
    ]
    arguments: dict
    reason: str


class WorkPlan(StrictModel):
    request_type: Literal["read", "summarize", "edit", "validate", "rule_check"]
    requires_approval: bool
    risk_level: Literal["low", "medium", "high"]
    summary: str
    reason: str
    actions: list[ToolAction]


ACTION_SCHEMAS = {
    "replace_text": ReplaceTextArgs,
    "update_paragraph": UpdateParagraphArgs,
    "update_table_cell": UpdateTableCellArgs,
    "update_multiple_cells": UpdateMultipleCellsArgs,
    "insert_paragraph": InsertParagraphArgs,
    "save_as_new_document": SaveAsNewDocumentArgs,
}


def validate_action_arguments(plan: WorkPlan) -> WorkPlan:
    for action in plan.actions:
        schema = ACTION_SCHEMAS.get(action.tool)
        if schema is None:
            continue
        schema.model_validate(action.arguments)
    return plan

