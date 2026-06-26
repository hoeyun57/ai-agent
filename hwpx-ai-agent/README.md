# HWPX AI Agent

로컬 PC 또는 내부망에서만 동작하는 HWPX 문서 업무 자동화 AI 에이전트입니다. 외부 LLM API를 호출하지 않고 Ollama 로컬 모델, FastAPI, SQLite, React/Vite를 사용합니다.

## 현재 MVP

- HWPX 업로드와 안전한 ZIP/XML 분석
- 문단/표/셀 추출
- 텍스트 검색과 정확한 텍스트 교체
- 표 셀 수정
- Decimal 기반 표 합계 검산
- 본문과 표의 숫자 불일치 탐지
- JSON 작업 계획 생성
- 승인 후 수정 적용
- 원본 보존, 새 HWPX 생성, XML diff 저장
- Ollama Q4/Q8 모델 선택 구조
- 한국어 React UI

## Windows 실행

## 다른 컴퓨터에서 먼저 확인할 것

새 PC에 프로젝트를 옮긴 뒤 아래 명령으로 필요한 프로그램이 있는지 확인하세요.

```powershell
python --version
py -0p
node --version
pnpm --version
ollama --version
git --version
```

또는 프로젝트의 환경 점검 스크립트를 실행할 수 있습니다.

```powershell
cd C:\path\to\hwpx-ai-agent
py scripts\verify_environment.py
```

`MISSING`이 표시되면 해당 항목을 설치해야 합니다.

| 항목 | 필요한 이유 | 없을 때 설치/조치 |
| --- | --- | --- |
| Python 3.12 이상 | FastAPI 백엔드 실행, 테스트 실행 | https://www.python.org/downloads/ 또는 `winget install Python.Python.3.12` |
| Node.js | React/Vite 프론트엔드 실행 | https://nodejs.org/ 또는 `winget install OpenJS.NodeJS.LTS` |
| pnpm | 프론트엔드 패키지 설치 | `corepack enable` 후 `corepack prepare pnpm@latest --activate`, 또는 `npm install -g pnpm` |
| Git | 저장소 복제와 업데이트 | https://git-scm.com/download/win 또는 `winget install Git.Git` |
| Ollama | 로컬 LLM 추론 | https://ollama.com/download |
| GGUF 모델 파일 | Q4/Q8 로컬 모델 등록 | `Qwen3.5-9B-DeepSeek-V4-Flash-Q4_K_M.gguf`, `Qwen3.5-9B-DeepSeek-V4-Flash-Q8_0.gguf`를 준비 |
| NVIDIA 드라이버 | GPU 가속 사용 시 필요 | NVIDIA 최신 드라이버 설치 후 Ollama 재시작 |

GPU가 없어도 CPU로 실행은 가능하지만, 문서 요약이나 규정 분석은 느릴 수 있습니다. Python의 `.venv`는 가상머신이 아니라 패키지 격리 폴더이므로 GPU 사용 여부에 직접 영향을 주지 않습니다. 실제 GPU 사용은 Ollama가 설치된 호스트 OS와 드라이버 상태에 따라 결정됩니다.

필수 프로그램 설치 후 다음 순서로 실행합니다.

```powershell
cd C:\models\hwpx-ai-agent\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[test]"
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

다른 터미널:

```powershell
cd C:\models\hwpx-ai-agent\frontend
pnpm install
pnpm dev
```

프론트엔드는 `http://localhost:5173`, 백엔드는 `http://localhost:8000`에서 실행됩니다.

## Ollama 모델 등록

상위 폴더 `C:\models`에 GGUF와 `Modelfile_q4`, `Modelfile_q8`가 있다고 가정합니다.

```powershell
cd C:\models\hwpx-ai-agent
.\scripts\setup_ollama_models.ps1 -Root ..
```

환경변수:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_FAST_MODEL=hwpx-agent-q4
OLLAMA_QUALITY_MODEL=hwpx-agent-q8
OLLAMA_DEFAULT_MODEL=hwpx-agent-q4
MODEL_MODE=auto
```

## 테스트

pytest가 설치된 개발 환경:

```powershell
cd C:\models\hwpx-ai-agent\backend
pytest
```

pytest가 없는 최소 환경에서는 smoke test를 실행할 수 있습니다.

```powershell
cd C:\models\hwpx-ai-agent
py scripts\smoke_test_backend.py
```

## API 문서

상세 목록은 `docs/api.md`를 확인하세요. FastAPI 실행 중에는 `/docs`에서 OpenAPI UI를 볼 수 있습니다.

## 제한과 향후 작업

MVP는 이미지, 수식, 차트, 도형을 수정하지 않고 보존합니다. 규정 추출은 API와 도구 확장 지점을 제공하며, 실제 고정밀 규정 분석은 로컬 Q8 모델 프롬프트와 사용자 검토 UI를 추가해 확장합니다.

