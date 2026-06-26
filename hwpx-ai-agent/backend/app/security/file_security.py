"""Filesystem safety helpers."""

from pathlib import Path
from uuid import uuid4


class SecurityError(ValueError):
    """Raised when a file operation would leave an allowed root."""


def resolve_within(root: Path, candidate: Path) -> Path:
    """Resolve candidate and ensure it remains inside root."""

    root_resolved = root.resolve()
    candidate_resolved = candidate.resolve()
    if candidate_resolved != root_resolved and root_resolved not in candidate_resolved.parents:
        raise SecurityError(f"path escapes allowed root: {candidate}")
    return candidate_resolved


def safe_document_id() -> str:
    return f"doc-{uuid4().hex}"


def safe_plan_id() -> str:
    return f"plan-{uuid4().hex}"


def safe_output_name(document_id: str, suffix: str = ".hwpx") -> str:
    cleaned = "".join(ch for ch in document_id if ch.isalnum() or ch in "-_")
    return f"{cleaned}-{uuid4().hex[:8]}{suffix}"

