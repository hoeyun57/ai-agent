from pathlib import Path

import pytest

from app.agents.planner import Planner
from app.hwpx.package import HwpxPackage
from app.hwpx.parser import parse_document
from app.hwpx.template_fields import detect_template_fields
from app.llm.schemas import WorkPlan, validate_action_arguments


class FailingLlm:
    async def generate_json(self, *args, **kwargs) -> str:
        raise RuntimeError("offline")


@pytest.mark.asyncio
async def test_fallback_replace_plan(sample_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(sample_hwpx, workspace, 100, 10_000_000)
    document = parse_document("doc-test", "sample.hwpx", workspace)
    plan = await Planner().create_plan("2025년을 모두 2026년으로 변경해줘", document)
    assert plan.requires_approval is True
    assert plan.actions[0].tool == "replace_text"


@pytest.mark.asyncio
async def test_writing_request_creates_append_plan(sample_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(sample_hwpx, workspace, 100, 10_000_000)
    document = parse_document("doc-test", "sample.hwpx", workspace)
    plan = await Planner(llm=FailingLlm()).create_plan("이 문서 양식을 유지해서 AI 에이전트 계획서를 작성해줘", document)
    assert plan.request_type == "edit"
    assert plan.requires_approval is True
    assert plan.risk_level == "high"
    assert plan.actions[0].tool == "append_paragraphs"
    assert "계획서" in plan.actions[0].arguments["texts"][0]


@pytest.mark.asyncio
async def test_writing_request_fills_template_fields(template_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(template_hwpx, workspace, 100, 10_000_000)
    document = parse_document("doc-template", "template.hwpx", workspace)
    fields = detect_template_fields(document)
    assert {field.label for field in fields} >= {"수신", "제목", "본문"}
    plan = await Planner(llm=FailingLlm()).create_plan("이 공문 양식을 유지해서 AI 도입 안내 공문을 작성해줘", document)
    assert plan.request_type == "edit"
    assert plan.requires_approval is True
    assert plan.actions[0].tool == "fill_template_fields"
    replacements = plan.actions[0].arguments["replacements"]
    assert any(item["target"] == "{{제목}}" for item in replacements)
    assert any("AI 도입 안내 공문" in item["replacement"] for item in replacements)


def test_unknown_tool_blocked() -> None:
    plan = WorkPlan(
        request_type="edit",
        requires_approval=True,
        risk_level="high",
        summary="bad",
        reason="bad",
        actions=[{"tool": "replace_text", "arguments": {"document_id": "doc", "target": "a", "replacement": "b", "extra": "x"}, "reason": "x"}],
    )
    with pytest.raises(Exception):
        validate_action_arguments(plan)

