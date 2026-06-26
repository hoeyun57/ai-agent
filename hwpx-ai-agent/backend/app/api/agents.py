"""Agent chat and planning API."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.agents.orchestrator import Orchestrator
from app.services.document_service import DocumentService


router = APIRouter()


class AgentRequest(BaseModel):
    document_id: str
    message: str


@router.post("/plan")
async def create_plan(request: AgentRequest) -> dict:
    return await Orchestrator().plan(request.document_id, request.message)


@router.post("/chat")
async def chat(request: AgentRequest) -> dict:
    document = DocumentService().load_document(request.document_id)
    if any(word in request.message for word in ["변경", "수정", "교체", "합계", "검산", "불일치"]):
        return await Orchestrator().plan(request.document_id, request.message)
    preview = "\n".join(paragraph.text for paragraph in document.paragraphs[:8])
    return {
        "answer": preview[:1200] if preview else "문서에서 추출된 텍스트가 없습니다.",
        "document_id": request.document_id,
    }

