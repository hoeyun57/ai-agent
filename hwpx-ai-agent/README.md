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

