"""Verify local runtime prerequisites."""

from pathlib import Path
import importlib.util
import sys


ROOT = Path(__file__).resolve().parents[1]


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    checks = {
        "python>=3.12": sys.version_info >= (3, 12),
        "fastapi": has_module("fastapi"),
        "pydantic": has_module("pydantic"),
        "httpx": has_module("httpx"),
        "defusedxml": has_module("defusedxml"),
        "model_q4": (ROOT.parent / "Qwen3.5-9B-DeepSeek-V4-Flash-Q4_K_M.gguf").exists(),
        "model_q8": (ROOT.parent / "Qwen3.5-9B-DeepSeek-V4-Flash-Q8_0.gguf").exists(),
    }
    for name, ok in checks.items():
        print(f"{name}: {'OK' if ok else 'MISSING'}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

