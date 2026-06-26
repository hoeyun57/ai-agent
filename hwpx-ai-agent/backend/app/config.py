"""Application configuration for local-only HWPX AI Agent."""

from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path


@dataclass
class Settings:
    """Runtime settings loaded from environment or .env."""

    app_name: str = "HWPX AI Agent"
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", "../data")))
    originals_dir: Path = field(default_factory=lambda: Path(os.getenv("ORIGINALS_DIR", "../data/originals")))
    workspaces_dir: Path = field(default_factory=lambda: Path(os.getenv("WORKSPACES_DIR", "../data/workspaces")))
    outputs_dir: Path = field(default_factory=lambda: Path(os.getenv("OUTPUTS_DIR", "../data/outputs")))
    database_path: Path = field(default_factory=lambda: Path(os.getenv("DATABASE_PATH", "../data/database/app.sqlite3")))
    max_upload_bytes: int = 80 * 1024 * 1024
    max_uncompressed_bytes: int = 250 * 1024 * 1024
    max_zip_members: int = 3000
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_fast_model: str = field(default_factory=lambda: os.getenv("OLLAMA_FAST_MODEL", "hwpx-agent-q4"))
    ollama_quality_model: str = field(default_factory=lambda: os.getenv("OLLAMA_QUALITY_MODEL", "hwpx-agent-q8"))
    ollama_default_model: str = field(default_factory=lambda: os.getenv("OLLAMA_DEFAULT_MODEL", "hwpx-agent-q4"))
    model_mode: str = field(default_factory=lambda: os.getenv("MODEL_MODE", "auto"))

    def ensure_dirs(self) -> None:
        """Create local runtime directories."""

        for path in [
            self.data_dir,
            self.originals_dir,
            self.workspaces_dir,
            self.outputs_dir,
            self.database_path.parent,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
