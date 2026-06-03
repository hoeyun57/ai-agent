import atexit
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from importlib import import_module
from pathlib import Path

from agent_v6.config import MODEL_FILES, MODEL_NAMES


class LLMError(RuntimeError):
    pass


_OLLAMA_PROCESS: subprocess.Popen | None = None
_OLLAMA_HOST = "http://127.0.0.1:11434"


def run_llm(model_key: str, system: str, prompt: str, response_prefix: str = "", num_predict: int | None = None) -> str:
    if model_key not in MODEL_NAMES:
        raise LLMError(f"지원하지 않는 모델입니다: {model_key}")

    ensure_ollama_server()
    model_name = MODEL_NAMES[model_key]

    try:
        ollama = import_module("ollama")
    except ModuleNotFoundError:
        ollama = None

    text = ""
    last_error: Exception | None = None

    if ollama is not None:
        try:
            response = call_without_thinking(ollama, model_name, system, prompt, response_prefix, num_predict)
            text = response_text(response)
        except Exception as exc:
            last_error = exc
            ensure_ollama_server(force=True)
            try:
                response = call_without_thinking(ollama, model_name, system, prompt, response_prefix, num_predict)
                text = response_text(response)
            except Exception as retry_exc:
                last_error = retry_exc

        if not text.strip() and not response_prefix:
            try:
                response = generate_without_thinking(ollama, model_name, system, prompt, response_prefix, num_predict)
                text = response_text(response)
            except Exception as exc:
                last_error = exc

    if not text.strip():
        try:
            text = http_generate_without_thinking(model_name, system, prompt, response_prefix, num_predict)
        except Exception as exc:
            last_error = exc

    if not text.strip():
        detail = f" 마지막 오류: {last_error}" if last_error else ""
        raise LLMError(f"Ollama 응답이 비어 있습니다.{detail}")
    if should_prepend_response_prefix(text, response_prefix):
        text = response_prefix + text
    return text


def call_without_thinking(ollama, model_name: str, system: str, prompt: str, response_prefix: str = "", num_predict: int | None = None):
    if response_prefix:
        return generate_without_thinking(ollama, model_name, system, prompt, response_prefix, num_predict)
    return chat_without_thinking(ollama, model_name, system, prompt, num_predict)


def chat_without_thinking(ollama, model_name: str, system: str, prompt: str, num_predict: int | None = None):
    options = {}
    if num_predict:
        options["num_predict"] = num_predict

    no_think_prompt = f"/no_think\n{prompt}"
    base_kwargs = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": no_think_prompt},
        ],
        "stream": False,
        "keep_alive": "30m",
    }
    if options:
        base_kwargs["options"] = options

    attempts = [
        {
            **base_kwargs,
            "think": False,
            "reasoning": "off",
            "reasoning_budget": 0,
            "chat_template_kwargs": {"enable_thinking": False},
            "jinja": True,
        },
        {**base_kwargs, "think": False},
        base_kwargs,
    ]

    last_error = None
    for kwargs in attempts:
        try:
            return ollama.chat(**kwargs)
        except TypeError as exc:
            last_error = exc
        except Exception as exc:
            if not is_unsupported_option_error(exc):
                raise
            last_error = exc
    raise last_error or LLMError("Ollama chat 호출 옵션을 구성하지 못했습니다.")


def generate_without_thinking(ollama, model_name: str, system: str, prompt: str, response_prefix: str = "", num_predict: int | None = None):
    base_kwargs = {
        "model": model_name,
        "stream": False,
        "keep_alive": "30m",
    }
    if response_prefix:
        base_kwargs.update({"prompt": build_raw_chat_prompt(system, prompt, response_prefix), "raw": True})
    else:
        base_kwargs.update({"system": system, "prompt": prompt})
    if num_predict:
        base_kwargs["options"] = {"num_predict": num_predict}

    attempts = [
        {
            **base_kwargs,
            "think": False,
            "reasoning": "off",
            "reasoning_budget": 0,
            "chat_template_kwargs": {"enable_thinking": False},
            "jinja": True,
        },
        {**base_kwargs, "think": False},
        base_kwargs,
    ]

    last_error = None
    for kwargs in attempts:
        try:
            return ollama.generate(**kwargs)
        except TypeError as exc:
            last_error = exc
        except Exception as exc:
            if not is_unsupported_option_error(exc):
                raise
            last_error = exc
    if response_prefix:
        return chat_without_thinking(ollama, model_name, system, prompt, num_predict)
    raise last_error or LLMError("Ollama 호출 옵션을 구성하지 못했습니다.")


def http_generate_without_thinking(model_name: str, system: str, prompt: str, response_prefix: str = "", num_predict: int | None = None) -> str:
    if response_prefix:
        payload = {
            "model": model_name,
            "prompt": build_raw_chat_prompt(system, prompt, response_prefix),
            "raw": True,
            "stream": False,
            "keep_alive": "30m",
        }
    else:
        payload = {
            "model": model_name,
            "system": system,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "30m",
        }
    if num_predict:
        payload["options"] = {"num_predict": num_predict}

    request = urllib.request.Request(
        f"{_OLLAMA_HOST}/api/generate",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        body = response.read().decode("utf-8", errors="replace")
    parsed = json.loads(body)
    return str(parsed.get("response", ""))


def response_text(response) -> str:
    if isinstance(response, dict):
        if "response" in response:
            return str(response.get("response", ""))
        message = response.get("message")
        if isinstance(message, dict):
            return str(message.get("content", ""))
        content = getattr(message, "content", None)
        if content is not None:
            return str(content)
        if hasattr(message, "get"):
            return str(message.get("content", ""))
        return ""

    text = getattr(response, "response", None)
    if text is not None:
        return str(text)
    message = getattr(response, "message", None)
    if isinstance(message, dict):
        return str(message.get("content", ""))
    content = getattr(message, "content", None)
    if content is not None:
        return str(content)
    if hasattr(message, "get"):
        return str(message.get("content", ""))
    return ""


def should_prepend_response_prefix(text: str, response_prefix: str) -> bool:
    if not response_prefix:
        return False
    stripped = text.lstrip()
    expected = response_prefix.strip()
    if stripped.startswith(expected):
        return False
    root_match = re.match(r"<([A-Za-z_][\w.-]*)", expected)
    if root_match and stripped.startswith(f"<{root_match.group(1)}"):
        return False
    return True


def build_raw_chat_prompt(system: str, prompt: str, response_prefix: str) -> str:
    return (
        "<|im_start|>system\n"
        f"{system}<|im_end|>\n"
        "<|im_start|>user\n"
        f"{prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
        f"{response_prefix}"
    )


def is_unsupported_option_error(exc: Exception) -> bool:
    message = str(exc).lower()
    markers = [
        "unexpected keyword",
        "unexpected argument",
        "unknown field",
        "unknown option",
        "invalid option",
        "not supported",
        "unsupported",
        "reasoning",
        "chat_template_kwargs",
        "jinja",
    ]
    return any(marker in message for marker in markers)


def ensure_ollama_server(force: bool = False) -> None:
    if not force and is_ollama_server_ready():
        return
    start_ollama_server()
    wait_for_ollama_server()


def is_ollama_server_ready() -> bool:
    try:
        with urllib.request.urlopen(f"{_OLLAMA_HOST}/api/tags", timeout=1) as response:
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def start_ollama_server() -> None:
    global _OLLAMA_PROCESS
    if _OLLAMA_PROCESS is not None and _OLLAMA_PROCESS.poll() is None:
        return

    env = os.environ.copy()
    env.setdefault("OLLAMA_HOST", _OLLAMA_HOST)
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    _OLLAMA_PROCESS = subprocess.Popen(
        [resolve_ollama(), "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        env=env,
        creationflags=creationflags,
    )
    atexit.register(stop_ollama_server)


def wait_for_ollama_server(timeout_seconds: int = 20) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_ollama_server_ready():
            return
        time.sleep(0.5)
    raise LLMError("Ollama 서버를 시작했지만 응답하지 않습니다.")


def shutdown_ollama() -> None:
    unload_models()
    stop_ollama_server()


def unload_models() -> None:
    ollama = resolve_ollama()
    for name in MODEL_NAMES.values():
        subprocess.run([ollama, "stop", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)


def stop_ollama_server() -> None:
    global _OLLAMA_PROCESS
    if _OLLAMA_PROCESS is None:
        return
    if _OLLAMA_PROCESS.poll() is None:
        _OLLAMA_PROCESS.terminate()
        try:
            _OLLAMA_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _OLLAMA_PROCESS.kill()
    _OLLAMA_PROCESS = None


def resolve_ollama() -> str:
    ollama = shutil.which("ollama")
    if ollama:
        return ollama
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
        Path(os.environ.get("PROGRAMFILES", "")) / "Ollama" / "ollama.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Ollama" / "ollama.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    raise LLMError("Ollama 실행 파일을 찾지 못했습니다.")


def create_models() -> None:
    ollama = resolve_ollama()
    for key in ("q4", "q8"):
        modelfile = MODEL_FILES[key]
        if not modelfile.exists():
            raise LLMError(f"Modelfile이 없습니다: {modelfile}")
        name = MODEL_NAMES[key]
        print(f"모델 등록 중: {name}", flush=True)
        result = subprocess.run([ollama, "create", name, "-f", str(modelfile)], text=True, encoding="utf-8")
        if result.returncode != 0:
            raise LLMError(f"모델 생성 실패: {name}")
        print(f"모델 등록 완료: {name}", flush=True)
