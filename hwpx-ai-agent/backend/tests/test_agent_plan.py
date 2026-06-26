from pathlib import Path

import pytest

from app.agents.planner import Planner
from app.hwpx.package import HwpxPackage
from app.hwpx.parser import parse_document
from app.llm.schemas import WorkPlan, validate_action_arguments


@pytest.mark.asyncio
async def test_fallback_replace_plan(sample_hwpx: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    HwpxPackage.open(sample_hwpx, workspace, 100, 10_000_000)
    document = parse_document("doc-test", "sample.hwpx", workspace)
    plan = await Planner().create_plan("2025년을 모두 2026년으로 변경해줘", document)
    assert plan.requires_approval is True
    assert plan.actions[0].tool == "replace_text"


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

