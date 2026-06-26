"""Rule extraction and compliance API placeholders for MVP."""

from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class RuleUploadRequest(BaseModel):
    document_id: str


class RuleCheckRequest(BaseModel):
    rule_document_id: str
    target_document_id: str


@router.post("/upload")
def upload_rules(request: RuleUploadRequest) -> dict:
    return {
        "status": "parsed_for_review",
        "document_id": request.document_id,
        "rules": [],
        "message": "MVP exposes the review interface; full rule extraction is an extension task.",
    }


@router.post("/check")
def check_rules(request: RuleCheckRequest) -> dict:
    return {
        "status": "checked",
        "rule_document_id": request.rule_document_id,
        "target_document_id": request.target_document_id,
        "violations": [],
    }

