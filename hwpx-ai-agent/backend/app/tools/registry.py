"""Tool registry executing only validated Python operations."""

from typing import Any

from app.hwpx.document_model import Document
from app.hwpx.table_editor import update_multiple_cells, update_table_cell
from app.hwpx.text_editor import insert_paragraph_after, replace_text, update_paragraph
from app.hwpx.validator import detect_inconsistent_numbers, validate_table_sums
from app.llm.schemas import ToolAction


class ToolRegistry:
    def __init__(self, workspace_dir, document: Document) -> None:
        self.workspace_dir = workspace_dir
        self.document = document

    def execute_readonly(self, action: ToolAction) -> Any:
        if action.tool == "validate_table_sums":
            return [issue for table in self.document.tables for issue in validate_table_sums(table)]
        if action.tool == "detect_inconsistent_numbers":
            return detect_inconsistent_numbers(self.document)
        raise ValueError(f"tool requires approval or is unknown: {action.tool}")

    def execute_edit(self, action: ToolAction) -> Any:
        args = action.arguments
        if action.tool == "replace_text":
            return replace_text(self.workspace_dir, str(args["target"]), str(args["replacement"]), str(args.get("scope", "all")))
        if action.tool == "update_paragraph":
            paragraph = next((p for p in self.document.paragraphs if p.id == args["paragraph_id"]), None)
            if paragraph is None:
                raise ValueError("unknown paragraph id")
            order = int(paragraph.id.rsplit("-", 1)[1])
            return update_paragraph(self.workspace_dir, paragraph.source_xml_path, order, str(args["text"]))
        if action.tool == "update_table_cell":
            return update_table_cell(self.workspace_dir, str(args["table_id"]), int(args["row"]), int(args["column"]), str(args["value"]))
        if action.tool == "update_multiple_cells":
            return update_multiple_cells(self.workspace_dir, list(args["updates"]))
        if action.tool == "insert_paragraph":
            return insert_paragraph_after(self.workspace_dir, str(args["source_xml_path"]), int(args["after_order"]), str(args["text"]))
        if action.tool == "save_as_new_document":
            return {"status": "deferred_to_document_service"}
        raise ValueError(f"unknown edit tool: {action.tool}")

