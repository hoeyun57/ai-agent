"""Rule analysis extension points."""

from typing import Any


def parse_rules(text: str) -> list[dict[str, Any]]:
    """Return user-reviewable rule candidates.

    MVP keeps this deterministic and conservative. Local LLM-assisted extraction can be layered here.
    """

    candidates = []
    for keyword in ["제출", "기한", "필수", "금액", "서류", "금지"]:
        if keyword in text:
            candidates.append({"type": keyword, "source_text": text[:300], "confidence": 0.4})
    return candidates


def check_rule_compliance(rules: list[dict[str, Any]], document_text: str) -> list[dict[str, Any]]:
    return [
        {
            "rule": rule,
            "result": "needs_review",
            "evidence": document_text[:300],
            "suggestion": "MVP에서는 사용자 확인이 필요합니다.",
            "confidence": rule.get("confidence", 0.3),
        }
        for rule in rules
    ]


def list_rule_violations(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [result for result in results if result.get("result") != "pass"]

