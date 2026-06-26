"""Plan approval API."""

import json
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.db.repositories import Repository
from app.services.document_service import DocumentService


router = APIRouter()


@router.get("/{plan_id}")
def get_plan(plan_id: str) -> dict:
    row = Repository(get_settings().database_path).get_plan(plan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="plan not found")
    row["plan_json"] = json.loads(row["plan_json"])
    row["result_json"] = json.loads(row["result_json"]) if row["result_json"] else None
    return row


@router.post("/{plan_id}/approve")
def approve_plan(plan_id: str) -> dict:
    try:
        return DocumentService().execute_plan(plan_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{plan_id}/reject")
def reject_plan(plan_id: str) -> dict:
    DocumentService().reject_plan(plan_id)
    return {"status": "rejected", "plan_id": plan_id}


@router.get("/{plan_id}/diff")
def plan_diff(plan_id: str) -> dict:
    row = Repository(get_settings().database_path).get_plan(plan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return {"plan_id": plan_id, "diff": row["diff_text"] or ""}

