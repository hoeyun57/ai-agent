"""SQLite repositories."""

from pathlib import Path
import json
from typing import Any

from app.db.database import connect, init_db


class Repository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        init_db(database_path)

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

    def delete_document(self, document_id: str) -> None:
        with connect(self.database_path) as conn:
            conn.execute("DELETE FROM llm_events WHERE document_id = ?", (document_id,))
            conn.execute("DELETE FROM audit_logs WHERE document_id = ?", (document_id,))
            conn.execute("DELETE FROM plans WHERE document_id = ?", (document_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))

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

    def list_plans(self, limit: int = 50) -> list[dict[str, Any]]:
        with connect(self.database_path) as conn:
            rows = conn.execute(
                "SELECT * FROM plans ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def plan_status_counts(self) -> dict[str, int]:
        with connect(self.database_path) as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS count FROM plans GROUP BY status").fetchall()
            return {str(row["status"]): int(row["count"]) for row in rows}

    def document_count(self) -> int:
        with connect(self.database_path) as conn:
            row = conn.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
            return int(row["count"]) if row else 0

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

    def add_llm_event(
        self,
        task: str,
        prompt_text: str,
        document_id: str | None = None,
        model: str | None = None,
        raw_response: str | None = None,
        parsed_json: dict[str, Any] | None = None,
        error: str | None = None,
        used_fallback: bool = False,
    ) -> None:
        with connect(self.database_path) as conn:
            conn.execute(
                """
                INSERT INTO llm_events
                (document_id, task, model, prompt_text, raw_response, parsed_json, error, used_fallback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    task,
                    model,
                    prompt_text,
                    raw_response,
                    json.dumps(parsed_json, ensure_ascii=False) if parsed_json is not None else None,
                    error,
                    1 if used_fallback else 0,
                ),
            )

    def list_llm_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with connect(self.database_path) as conn:
            rows = conn.execute(
                "SELECT * FROM llm_events ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def audit_logs(self, document_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with connect(self.database_path) as conn:
            if document_id:
                rows = conn.execute(
                    "SELECT * FROM audit_logs WHERE document_id = ? ORDER BY created_at DESC LIMIT ?",
                    (document_id, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

