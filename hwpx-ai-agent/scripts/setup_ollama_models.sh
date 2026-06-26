#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-..}"
OLLAMA_BIN="${OLLAMA_BIN:-ollama}"

if [[ ! -f "$ROOT/Qwen3.5-9B-DeepSeek-V4-Flash-Q4_K_M.gguf" ]]; then
  echo "Q4 GGUF not found under $ROOT" >&2
fi
if [[ ! -f "$ROOT/Qwen3.5-9B-DeepSeek-V4-Flash-Q8_0.gguf" ]]; then
  echo "Q8 GGUF not found under $ROOT" >&2
fi

"$OLLAMA_BIN" create hwpx-agent-q4 -f "$ROOT/Modelfile_q4"
"$OLLAMA_BIN" create hwpx-agent-q8 -f "$ROOT/Modelfile_q8"
"$OLLAMA_BIN" list

