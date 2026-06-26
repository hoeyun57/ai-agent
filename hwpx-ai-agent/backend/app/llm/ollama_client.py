"""Minimal Ollama HTTP API client with local-only defaults."""

from collections.abc import AsyncIterator
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover - exercised in minimal local smoke envs
    httpx = None

from app.config import get_settings


class OllamaError(RuntimeError):
    """Raised when the local Ollama server cannot satisfy a request."""


class OllamaClient:
    def __init__(self, base_url: str | None = None, timeout: float = 60.0) -> None:
        self.base_url = (base_url or get_settings().ollama_base_url).rstrip("/")
        self.timeout = timeout

    async def health(self) -> dict[str, Any]:
        if httpx is None:
            return {"ok": False, "error": "httpx is not installed", "models": []}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return {"ok": True, "models": response.json().get("models", [])}
        except Exception as exc:
            return {"ok": False, "error": str(exc), "models": []}

    async def list_models(self) -> list[dict[str, Any]]:
        status = await self.health()
        return list(status.get("models", [])) if status.get("ok") else []

    async def generate_json(
        self,
        model: str,
        prompt: str,
        system: str,
        temperature: float = 0.1,
        context_length: int = 8192,
    ) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature, "num_ctx": context_length},
        }
        if httpx is None:
            raise OllamaError("httpx is not installed")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return str(response.json().get("response", ""))

    async def stream_generate(self, model: str, prompt: str, system: str = "") -> AsyncIterator[str]:
        payload = {"model": model, "prompt": prompt, "system": system, "stream": True}
        if httpx is None:
            raise OllamaError("httpx is not installed")
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield line
