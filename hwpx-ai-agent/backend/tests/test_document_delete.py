from pathlib import Path

from app.config import Settings
from app.db.repositories import Repository
from app.services import document_service
from app.services.document_service import DocumentService


def test_delete_document_removes_files_and_records(tmp_path, monkeypatch) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        originals_dir=tmp_path / "data" / "originals",
        workspaces_dir=tmp_path / "data" / "workspaces",
        outputs_dir=tmp_path / "data" / "outputs",
        database_path=tmp_path / "data" / "database" / "app.sqlite3",
    )
    settings.ensure_dirs()
    monkeypatch.setattr(document_service, "get_settings", lambda: settings)

    document_id = "doc-delete-test"
    original_path = settings.originals_dir / "doc-delete-test.hwpx"
    workspace_dir = settings.workspaces_dir / document_id
    output_path = settings.outputs_dir / "doc-delete-test-output.hwpx"
    workspace_dir.mkdir(parents=True)
    original_path.write_text("original", encoding="utf-8")
    (workspace_dir / "section.xml").write_text("workspace", encoding="utf-8")
    output_path.write_text("output", encoding="utf-8")

    repo = Repository(settings.database_path)
    repo.add_document(document_id, "delete.hwpx", original_path, workspace_dir)
    repo.set_output_path(document_id, output_path)
    repo.add_plan("plan-delete-test", document_id, {"summary": "delete"})
    repo.add_audit("document_uploaded", {"filename": "delete.hwpx"}, document_id)
    repo.add_llm_event("plan", "prompt", document_id=document_id, raw_response="{}")

    result = DocumentService().delete_document(document_id)

    assert result == {"deleted": True, "document_id": document_id}
    assert not original_path.exists()
    assert not workspace_dir.exists()
    assert not output_path.exists()
    assert repo.get_document(document_id) is None
    assert repo.list_plans() == []
    assert repo.audit_logs(document_id=document_id) == []
    assert repo.list_llm_events() == []
