"""Audit logging service."""

from typing import Any

from app.config import get_settings
from app.db.repositories import Repository


class AuditService:
    def __init__(self) -> None:
        self.repo = Repository(get_settings().database_path)

    def record(self, event: str, detail: dict[str, Any], document_id: str | None = None) -> None:
        redacted = {key: value for key, value in detail.items() if key not in {"document_text", "raw_content"}}
        self.repo.add_audit(event=event, detail=redacted, document_id=document_id)

    def list(self, document_id: str | None = None) -> list[dict[str, Any]]:
        return self.repo.audit_logs(document_id=document_id)

