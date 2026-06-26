"""Plan generation via local Ollama with deterministic fallback."""

import re

from pydantic import ValidationError

from app.agents.model_router import select_model
from app.agents.prompts import PLAN_PROMPT, SYSTEM_PROMPT
from app.hwpx.document_model import Document
from app.llm.json_parser import parse_json_object
from app.llm.ollama_client import OllamaClient
from app.llm.schemas import WorkPlan, validate_action_arguments


class Planner:
    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    async def create_plan(self, request: str, document: Document) -> WorkPlan:
        fallback = self._fallback_plan(request=request, document=document)
        prompt = (
            f"{PLAN_PROMPT}\n\n"
            f"문서 ID: {document.id}\n"
            f"문서명: {document.filename}\n"
            f"문단 수: {len(document.paragraphs)}\n"
            f"표 수: {len(document.tables)}\n"
            f"사용자 요청: {request}\n"
        )
        try:
            raw = await self.llm.generate_json(
                model=select_model(fallback.request_type, fallback.risk_level),
                prompt=prompt,
                system=SYSTEM_PROMPT,
            )
            plan = WorkPlan.model_validate(parse_json_object(raw))
            return validate_action_arguments(plan)
        except Exception:
            return fallback

    def _fallback_plan(self, request: str, document: Document) -> WorkPlan:
        replace_match = re.search(r"(.+?)(?:을|를)\s*모두\s*(.+?)(?:으로|로)\s*변경", request)
        if replace_match:
            target = replace_match.group(1).strip(" \"'")
            replacement = replace_match.group(2).strip(" \"'")
            return validate_action_arguments(
                WorkPlan(
                    request_type="edit",
                    requires_approval=True,
                    risk_level="medium",
                    summary=f"{target} 텍스트를 {replacement} 텍스트로 모두 변경",
                    reason="사용자가 전체 텍스트 교체를 요청함",
                    actions=[
                        {
                            "tool": "replace_text",
                            "arguments": {
                                "document_id": document.id,
                                "target": target,
                                "replacement": replacement,
                                "scope": "all",
                            },
                            "reason": "정확히 일치하는 텍스트만 검증된 편집기로 교체",
                        },
                        {"tool": "save_as_new_document", "arguments": {"document_id": document.id}, "reason": "원본 보존"},
                    ],
                )
            )
        if "합계" in request or "예산" in request:
            return WorkPlan(
                request_type="validate",
                requires_approval=False,
                risk_level="low",
                summary="표 합계 검산",
                reason="사용자가 예산 또는 합계 검산을 요청함",
                actions=[
                    {
                        "tool": "validate_table_sums",
                        "arguments": {"document_id": document.id},
                        "reason": "Decimal 기반으로 표 행의 합계를 검산",
                    }
                ],
            )
        if "불일치" in request or "숫자" in request:
            return WorkPlan(
                request_type="validate",
                requires_approval=False,
                risk_level="low",
                summary="본문과 표의 숫자 일관성 검사",
                reason="사용자가 수치 일관성 검사를 요청함",
                actions=[
                    {
                        "tool": "detect_inconsistent_numbers",
                        "arguments": {"document_id": document.id},
                        "reason": "본문 숫자와 표 숫자를 비교",
                    }
                ],
            )
        return WorkPlan(
            request_type="summarize",
            requires_approval=False,
            risk_level="low",
            summary="문서 요약 및 질의응답",
            reason="수정 의도가 명확하지 않아 읽기 작업으로 처리",
            actions=[],
        )

