"""Runtime monitoring API."""

import json
from fastapi import APIRouter

from app.config import get_settings
from app.db.repositories import Repository
from app.llm.ollama_client import OllamaClient


router = APIRouter()


@router.get("/status")
async def get_status() -> dict:
    repo = Repository(get_settings().database_path)
    ollama = await OllamaClient().health()
    return {
        "ok": True,
        "documents": repo.document_count(),
        "plans": repo.plan_status_counts(),
        "ollama": ollama,
        "recent_audit": _decode_audit(repo.audit_logs(limit=10)),
        "recent_plans": _decode_plans(repo.list_plans(limit=10)),
        "recent_llm_events": _decode_llm_events(repo.list_llm_events(limit=10)),
    }


@router.get("/audit")
def get_audit(limit: int = 100) -> dict:
    repo = Repository(get_settings().database_path)
    return {"items": _decode_audit(repo.audit_logs(limit=limit))}


@router.get("/plans")
def get_plans(limit: int = 100) -> dict:
    repo = Repository(get_settings().database_path)
    return {"items": _decode_plans(repo.list_plans(limit=limit))}


@router.get("/llm")
def get_llm_events(limit: int = 100) -> dict:
    repo = Repository(get_settings().database_path)
    return {"items": _decode_llm_events(repo.list_llm_events(limit=limit))}


def _decode_audit(rows: list[dict]) -> list[dict]:
    decoded = []
    for row in rows:
        item = dict(row)
        if item.get("detail_json"):
            item["detail"] = json.loads(item.pop("detail_json"))
        decoded.append(item)
    return decoded


def _decode_plans(rows: list[dict]) -> list[dict]:
    decoded = []
    for row in rows:
        item = dict(row)
        if item.get("plan_json"):
            item["plan"] = json.loads(item.pop("plan_json"))
        if item.get("result_json"):
            item["result"] = json.loads(item.pop("result_json"))
        decoded.append(item)
    return decoded


def _decode_llm_events(rows: list[dict]) -> list[dict]:
    decoded = []
    for row in rows:
        item = dict(row)
        if item.get("parsed_json"):
            item["parsed"] = json.loads(item.pop("parsed_json"))
        item["used_fallback"] = bool(item.get("used_fallback"))
        decoded.append(item)
    return decoded
