"""Model settings API."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.llm.ollama_client import OllamaClient


router = APIRouter()


class ModelSettings(BaseModel):
    mode: str
    fast_model: str
    quality_model: str
    default_model: str
    ollama_base_url: str


@router.get("/models")
async def get_models() -> dict:
    settings = get_settings()
    return {
        "settings": {
            "mode": settings.model_mode,
            "fast_model": settings.ollama_fast_model,
            "quality_model": settings.ollama_quality_model,
            "default_model": settings.ollama_default_model,
            "ollama_base_url": settings.ollama_base_url,
        },
        "ollama": await OllamaClient().health(),
    }


@router.put("/models")
def put_models(payload: ModelSettings) -> dict:
    return {"status": "accepted_for_runtime_env", "settings": payload.model_dump()}

