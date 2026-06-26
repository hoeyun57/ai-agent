"""Select Ollama model by mode, complexity, and risk."""

from app.config import get_settings


def select_model(task_type: str, risk_level: str = "low") -> str:
    settings = get_settings()
    if settings.model_mode == "fast":
        return settings.ollama_fast_model
    if settings.model_mode == "quality":
        return settings.ollama_quality_model
    if task_type in {"rule_check", "validate"} or risk_level in {"medium", "high"}:
        return settings.ollama_quality_model
    return settings.ollama_fast_model

