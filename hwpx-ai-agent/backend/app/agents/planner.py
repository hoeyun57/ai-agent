"""Plan generation via local Ollama with deterministic fallback."""

from typing import Any
import re

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
        if self._is_writing_request(request):
            return await self._create_writing_plan(request=request, document=document)
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

    async def _create_writing_plan(self, request: str, document: Document) -> WorkPlan:
        paragraphs = await self._draft_paragraphs(request=request, document=document)
        source_xml_path = self._target_source_xml_path(document)
        return validate_action_arguments(
            WorkPlan(
                request_type="edit",
                requires_approval=True,
                risk_level="high",
                summary="문서 양식에 맞춘 초안 문단 추가",
                reason="사용자가 기존 HWPX 양식을 유지한 문서 작성 또는 계획서 초안 작성을 요청함",
                actions=[
                    {
                        "tool": "append_paragraphs",
                        "arguments": {
                            "document_id": document.id,
                            "source_xml_path": source_xml_path,
                            "texts": paragraphs,
                        },
                        "reason": "생성된 초안 문단을 기존 HWPX 섹션 끝에 추가",
                    },
                    {"tool": "save_as_new_document", "arguments": {"document_id": document.id}, "reason": "원본을 보존하고 새 HWPX로 저장"},
                ],
            )
        )

    async def _draft_paragraphs(self, request: str, document: Document) -> list[str]:
        prompt = (
            "다음 사용자 요청과 HWPX 문서 정보를 바탕으로 문서에 삽입할 한국어 초안 문단을 작성하라.\n"
            "반드시 JSON 객체 하나만 출력한다. 형식: {\"paragraphs\": [\"문단1\", \"문단2\"]}\n"
            "문서에 없는 확정 수치나 기관명은 만들지 말고, 필요한 경우 '사용자 확인 필요'라고 쓴다.\n"
            "각 문단은 500자 이내로 작성한다.\n\n"
            f"문서명: {document.filename}\n"
            f"문단 일부: {self._document_preview(document)}\n"
            f"사용자 요청: {request}\n"
        )
        try:
            raw = await self.llm.generate_json(
                model=select_model("edit", "high"),
                prompt=prompt,
                system=SYSTEM_PROMPT,
                temperature=0.2,
            )
            parsed: dict[str, Any] = parse_json_object(raw)
            values = parsed.get("paragraphs")
            if isinstance(values, list):
                paragraphs = [str(value).strip() for value in values if str(value).strip()]
                if paragraphs:
                    return paragraphs[:30]
        except Exception:
            pass
        return self._fallback_draft_paragraphs(request=request, document=document)

    def _fallback_draft_paragraphs(self, request: str, document: Document) -> list[str]:
        title = self._infer_title(request)
        return [
            title,
            "1. 추진 배경: 본 문서는 제공된 HWPX 양식을 기준으로 작성되는 초안입니다. 세부 수치, 기관명, 일정은 원문 또는 사용자 확인 자료에 근거해 확정해야 합니다.",
            "2. 목표: 사용자의 요청에 따라 문서 작성 목적을 명확히 하고, 핵심 추진 과제와 기대 효과를 체계적으로 정리합니다.",
            "3. 주요 내용: 현황 분석, 추진 전략, 세부 실행 과제, 일정, 예산, 위험 관리 항목을 포함해 검토 가능한 계획서 구조로 작성합니다.",
            "4. 실행 계획: 단계별 일정과 담당 주체는 사용자 확인 후 확정하며, 문서 내 표와 본문 수치가 일치하도록 검산 절차를 수행합니다.",
            "5. 기대 효과: 업무 효율 향상, 문서 품질 개선, 검토 과정의 오류 감소를 기대할 수 있습니다.",
            "6. 확인 필요 사항: 실제 제출처, 사업 기간, 예산 한도, 필수 항목, 파일명 규칙, 제출 기한은 별도 확인이 필요합니다.",
        ]

    def _is_writing_request(self, request: str) -> bool:
        keywords = ["작성", "계획서", "초안", "채워", "생성", "만들어", "써줘", "기획서"]
        return any(keyword in request for keyword in keywords)

    def _target_source_xml_path(self, document: Document) -> str:
        if document.paragraphs:
            return document.paragraphs[-1].source_xml_path
        xml_files = document.metadata.get("xml_files", [])
        if isinstance(xml_files, list) and xml_files:
            return str(xml_files[0])
        raise ValueError("document has no editable XML file")

    def _document_preview(self, document: Document) -> str:
        preview = "\n".join(paragraph.text for paragraph in document.paragraphs[:8])
        return preview[:2000]

    def _infer_title(self, request: str) -> str:
        if "계획서" in request:
            return "계획서 초안"
        if "기획서" in request:
            return "기획서 초안"
        return "문서 작성 초안"

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

