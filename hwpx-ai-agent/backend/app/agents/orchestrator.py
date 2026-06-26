"""Analyze, plan, approve, execute workflow."""

from pathlib import Path

from app.agents.planner import Planner
from app.config import get_settings
from app.db.repositories import Repository
from app.security.file_security import safe_plan_id
from app.services.document_service import DocumentService
from app.tools.registry import ToolRegistry


class Orchestrator:
    def __init__(self) -> None:
        self.documents = DocumentService()
        self.repo = Repository(get_settings().database_path)
        self.planner = Planner()

    async def plan(self, document_id: str, message: str) -> dict:
        document = self.documents.load_document(document_id)
        plan = await self.planner.create_plan(message, document)
        plan_id = safe_plan_id()
        plan_dict = plan.model_dump()
        self.repo.add_plan(plan_id, document_id, plan_dict)
        if not plan.requires_approval:
            row = self.documents.document_row(document_id)
            registry = ToolRegistry(Path(row["workspace_dir"]), document)
            results = [registry.execute_readonly(action) for action in plan.actions]
            self.repo.update_plan(plan_id, "completed_readonly", {"results": results})
            plan_dict["results"] = results
        return {"plan_id": plan_id, "plan": plan_dict}
