"""SQLite repositories."""

from pathlib import Path
import json
from typing import Any

from app.db.database import connect


class Repository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def add_document(self, document_id: str, filename: str, original_path: Path, workspace_dir: Path) -> None:
        with connect(self.database_path) as conn:
            conn.execute(
                "INSERT INTO documents (id, filename, original_path, workspace_dir) VALUES (?, ?, ?, ?)",
                (document_id, filename, str(original_path), str(workspace_dir)),
            )

    def list_documents(self) -> list[dict[str, Any]]:
        with connect(self.database_path) as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        with connect(self.database_path) as conn:
            row = conn.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
            return dict(row) if row else None

    def set_output_path(self, document_id: str, output_path: Path) -> None:
        with connect(self.database_path) as conn:
            conn.execute("UPDATE documents SET output_path = ? WHERE id = ?", (str(output_path), document_id))

    def add_plan(self, plan_id: str, document_id: str, plan: dict[str, Any]) -> None:
        with connect(self.database_path) as conn:
            conn.execute(
                "INSERT INTO plans (id, document_id, status, plan_json) VALUES (?, ?, ?, ?)",
                (plan_id, document_id, "pending_approval", json.dumps(plan, ensure_ascii=False)),
            )

    def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        with connect(self.database_path) as conn:
            row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
            return dict(row) if row else None

    def update_plan(self, plan_id: str, status: str, result: dict[str, Any] | None = None, diff_text: str | None = None) -> None:
        with connect(self.database_path) as conn:
            conn.execute(
                "UPDATE plans SET status = ?, result_json = COALESCE(?, result_json), diff_text = COALESCE(?, diff_text) WHERE id = ?",
                (status, json.dumps(result, ensure_ascii=False) if result is not None else None, diff_text, plan_id),
            )

    def add_audit(self, event: str, detail: dict[str, Any], document_id: str | None = None) -> None:
        with connect(self.database_path) as conn:
            conn.execute(
                "INSERT INTO audit_logs (document_id, event, detail_json) VALUES (?, ?, ?)",
                (document_id, event, json.dumps(detail, ensure_ascii=False)),
            )

    def audit_logs(self, document_id: str | None = None) -> list[dict[str, Any]]:
        with connect(self.database_path) as conn:
            if document_id:
                rows = conn.execute(
                    "SELECT * FROM audit_logs WHERE document_id = ? ORDER BY created_at DESC",
                    (document_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

