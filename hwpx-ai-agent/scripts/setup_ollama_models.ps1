param(
  [string]$Ollama = "ollama",
  [string]$Root = ".."
)

$ErrorActionPreference = "Stop"
$q4Model = Join-Path $Root "Qwen3.5-9B-DeepSeek-V4-Flash-Q4_K_M.gguf"
$q8Model = Join-Path $Root "Qwen3.5-9B-DeepSeek-V4-Flash-Q8_0.gguf"
$q4File = Join-Path $Root "Modelfile_q4"
$q8File = Join-Path $Root "Modelfile_q8"

if (!(Test-Path $q4Model)) { Write-Warning "Q4 GGUF not found: $q4Model" }
if (!(Test-Path $q8Model)) { Write-Warning "Q8 GGUF not found: $q8Model" }

& $Ollama create hwpx-agent-q4 -f $q4File
& $Ollama create hwpx-agent-q8 -f $q8File
& $Ollama list

