"""Document lifecycle service."""

from pathlib import Path
import json

from app.config import get_settings
from app.db.repositories import Repository
from app.hwpx.diff import generate_document_diff
from app.hwpx.document_model import Document
from app.hwpx.package import HwpxPackage
from app.hwpx.parser import parse_document
from app.hwpx.validator import validate_hwpx_package
from app.security.file_security import safe_output_name
from app.services.audit_service import AuditService
from app.services.storage_service import StorageService
from app.tools.registry import ToolRegistry


class DocumentNotFoundError(ValueError):
    pass


class DocumentService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.repo = Repository(self.settings.database_path)
        self.storage = StorageService()
        self.audit = AuditService()

    def upload_from_path(self, path: Path, filename: str | None = None) -> Document:
        document_id, original_path, workspace_dir = self.storage.store_upload(path, filename)
        HwpxPackage.open(original_path, workspace_dir, self.settings.max_zip_members, self.settings.max_uncompressed_bytes)
        self.repo.add_document(document_id, filename or path.name, original_path, workspace_dir)
        document = parse_document(document_id, filename or path.name, workspace_dir)
        self.audit.record("document_uploaded", {"filename": filename or path.name}, document_id)
        return document

    def list_documents(self) -> list[dict]:
        return self.repo.list_documents()

    def load_document(self, document_id: str) -> Document:
        row = self.repo.get_document(document_id)
        if row is None:
            raise DocumentNotFoundError(document_id)
        return parse_document(document_id, row["filename"], Path(row["workspace_dir"]))

    def document_row(self, document_id: str) -> dict:
        row = self.repo.get_document(document_id)
        if row is None:
            raise DocumentNotFoundError(document_id)
        return row

    def execute_plan(self, plan_id: str) -> dict:
        plan_row = self.repo.get_plan(plan_id)
        if plan_row is None:
            raise ValueError("unknown plan")
        if plan_row["status"] != "pending_approval":
            raise ValueError("plan is not pending approval")
        plan = json.loads(plan_row["plan_json"])
        if not plan.get("requires_approval"):
            raise ValueError("readonly plan does not need approval execution")
        document_id = plan_row["document_id"]
        row = self.document_row(document_id)
        before = Path(row["original_path"])
        workspace_dir = Path(row["workspace_dir"])
        document = self.load_document(document_id)
        registry = ToolRegistry(workspace_dir, document)
        results = []
        for action in plan["actions"]:
            if action["tool"] == "save_as_new_document":
                continue
            results.append(registry.execute_edit(type("Action", (), action)))
        output_path = self.settings.outputs_dir / safe_output_name(document_id)
        HwpxPackage(Path(row["original_path"]), workspace_dir).repack(output_path)
        validation = validate_hwpx_package(output_path, self.settings.max_zip_members, self.settings.max_uncompressed_bytes)
        diff_text = generate_document_diff(before, output_path)
        result = {"output_path": str(output_path), "validation": validation, "changes": results}
        self.repo.set_output_path(document_id, output_path)
        self.repo.update_plan(plan_id, "approved_executed", result=result, diff_text=diff_text)
        self.audit.record("plan_executed", {"plan_id": plan_id, "output_path": str(output_path)}, document_id)
        return result

    def reject_plan(self, plan_id: str) -> None:
        self.repo.update_plan(plan_id, "rejected")
        self.audit.record("plan_rejected", {"plan_id": plan_id})

