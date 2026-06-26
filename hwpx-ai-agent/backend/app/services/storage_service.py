"""Local-only document storage."""

from pathlib import Path
from shutil import copy2

from app.config import get_settings
from app.security.file_security import resolve_within, safe_document_id


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def store_upload(self, source_path: Path, filename: str | None = None) -> tuple[str, Path, Path]:
        document_id = safe_document_id()
        suffix = Path(filename or source_path.name).suffix or ".hwpx"
        original_path = resolve_within(self.settings.originals_dir, self.settings.originals_dir / f"{document_id}{suffix}")
        workspace_dir = resolve_within(self.settings.workspaces_dir, self.settings.workspaces_dir / document_id)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        copy2(source_path, original_path)
        return document_id, original_path, workspace_dir

