"""Robust JSON extraction for local model responses."""

import json
import re
from typing import Any


class JsonPlanParseError(ValueError):
    """Raised when an LLM response cannot be parsed as JSON."""


def parse_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object after removing common markdown wrappers."""

    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise JsonPlanParseError("model response did not contain a JSON object")
        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise JsonPlanParseError("model response JSON could not be parsed") from exc
    if not isinstance(value, dict):
        raise JsonPlanParseError("model response JSON must be an object")
    return value

