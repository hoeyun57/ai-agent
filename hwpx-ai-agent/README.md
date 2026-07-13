# HWPX AI Agent

로컬 PC 또는 내부망에서 실행하는 HWPX 문서 업무 자동화 AI 에이전트입니다. 외부 LLM API를 사용하지 않고 Ollama 로컬 모델, FastAPI, SQLite, React/Vite로 동작합니다.

## 주요 기능

- HWPX 업로드, 안전한 ZIP/XML 분석
- 문단, 표, 셀 추출
- 텍스트 검색과 정확한 텍스트 교체
- 공문/계획서 양식의 자리표시자와 빈칸 채우기
- 기존 HWPX 양식을 유지한 초안 문단 추가
- Decimal 기반 표 합계 검산
- 본문과 표의 숫자 불일치 탐지
- AI 작업 계획 생성, 승인 후 수정 적용
- 원본 보존, 수정본 HWPX 다운로드
- 문서 삭제, 작업 이력, LLM 원문 응답 모니터링

## 필요 프로그램

| 항목 | 용도 |
| --- | --- |
| Python 3.12 이상 | FastAPI 백엔드 실행 |
| Node.js LTS | React/Vite 프론트엔드 실행 |
| pnpm | 프론트엔드 패키지 설치 |
| Git | 저장소 관리 |
| Ollama | 로컬 LLM 실행 |
| GGUF 모델 파일 또는 등록된 Ollama 모델 | Q4/Q8 모델 사용 |

Python 3.14는 일부 패키지 호환성이 불안정할 수 있으므로 Python 3.12 사용을 권장합니다.

GPU가 없어도 CPU로 실행할 수 있습니다. `.venv`는 가상머신이 아니라 Python 패키지 격리 폴더이므로 GPU 사용 여부에 직접 영향을 주지 않습니다. GPU 사용은 Ollama와 OS 드라이버 상태에 따라 결정됩니다.

## 빠른 설치

프로젝트 루트에서 실행합니다.

CMD:

```cmd
scripts\setup_windows.cmd
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
```

자동 설치 스크립트는 가능한 경우 아래 작업을 처리합니다.

- Python, Node.js, Git, Ollama 설치 확인
- pnpm 준비
- `backend\.env` 생성
- `backend\.venv` 생성
- 백엔드/프론트엔드 의존성 설치
- 기존 `qwen3.5-deepseek-q4/q8` 모델이 있으면 `hwpx-agent-q4/q8` 별칭 생성

환경만 확인하려면:

```cmd
py scripts\verify_environment.py
```

## Ollama 모델 설정

앱 기본 모델 이름은 아래와 같습니다.

```text
hwpx-agent-q4
hwpx-agent-q8
```

현재 등록된 모델 확인:

```cmd
ollama list
```

이미 등록된 모델을 기본 이름으로 복사:

```cmd
ollama cp qwen3.5-deepseek-q4:latest hwpx-agent-q4
ollama cp qwen3.5-deepseek-q8:latest hwpx-agent-q8
```

GGUF 파일에서 직접 등록:

```cmd
ollama create hwpx-agent-q4:latest -f Modelfile_q4
ollama create hwpx-agent-q8:latest -f Modelfile_q8
```

모델 이름을 다르게 쓸 경우 `backend\.env`를 수정합니다.

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_FAST_MODEL=hwpx-agent-q4
OLLAMA_QUALITY_MODEL=hwpx-agent-q8
OLLAMA_DEFAULT_MODEL=hwpx-agent-q4
MODEL_MODE=auto
```

`.env`를 수정한 뒤에는 백엔드를 다시 시작해야 반영됩니다.

## 실행

백엔드, 프론트엔드, Ollama를 한 번에 실행합니다.

CMD:

```cmd
scripts\start_all.cmd
```

PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_all.ps1
```

이 스크립트는 Ollama 실행 여부를 먼저 확인합니다. Ollama가 꺼져 있으면 새 창에서 `ollama serve`를 실행한 뒤 백엔드와 프론트엔드를 시작합니다.

실행 주소:

- 프론트엔드: `http://localhost:5173`
- 백엔드: `http://localhost:8000`
- API 문서: `http://localhost:8000/docs`
- Ollama: `http://localhost:11434`

종료하려면 열린 Ollama/백엔드/프론트엔드 창에서 `Ctrl + C`를 누르거나 창을 닫습니다.

## 수동 실행

백엔드:

```cmd
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

프론트엔드:

```cmd
cd frontend
pnpm.cmd dev
```

PowerShell에서 `pnpm.ps1` 실행 정책 오류가 나면 `pnpm` 대신 `pnpm.cmd`를 사용하세요.

## 사용 순서

1. `업로드` 화면에서 HWPX 파일을 올립니다.
2. `문서` 화면에서 문단과 표가 추출됐는지 확인합니다.
3. `AI 작업` 화면에서 문서를 선택하고 요청을 입력합니다.
4. `계획 생성`을 눌러 작업 계획을 만듭니다.
5. 수정 작업이면 `승인` 화면에서 plan ID를 승인합니다.
6. `문서` 화면에서 수정본을 다운로드합니다.

`한번에 실행`은 계획 생성과 승인을 한 번에 처리합니다. 사용자가 해당 작업을 즉시 승인한다는 의미로 동작합니다.

## 화면 설명

- `업로드`: HWPX 파일 업로드
- `문서`: 문서 구조 확인, 수정본 다운로드, 문서 삭제
- `AI 작업`: 자연어 요청으로 작업 계획 생성 또는 한 번에 실행
- `모니터링`: 문서 수, 계획 상태, Ollama 연결 상태, 최근 작업 로그 확인
- `개발자`: LLM 프롬프트, 원문 응답, 파싱 결과, 오류, fallback 여부 확인
- `승인`: 생성된 계획 승인/거절, diff 확인
- `이력`: 문서 검증 결과 확인
- `설정`: Ollama 연결과 모델 설정 확인

문서 삭제는 해당 문서의 원본, 작업 폴더, 수정본, 관련 계획/감사/LLM 이벤트 기록을 함께 삭제합니다.

## 요청 예시

텍스트 교체:

```text
2025년을 모두 2026년으로 변경해줘
```

표 합계 검산:

```text
예산 합계가 맞는지 확인해줘
```

본문과 표 숫자 비교:

```text
본문과 표의 숫자 불일치를 찾아줘
```

문서 초안 추가:

```text
이 문서 양식을 유지해서 AI 에이전트 계획서를 작성해줘
```

공문/양식 빈칸 채우기:

```text
이 공문 양식의 빈칸을 유지해서 AI 도입 안내 공문을 작성해줘
```

지원하는 자리표시자 예:

```text
{{수신}}
{{제목}}
{{본문}}
[제목]
수신: ____
○○○
```

## 문제 해결

`uvicorn`이 없다고 나올 때:

```cmd
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

`pytest`가 없다고 나올 때:

```cmd
cd backend
.venv\Scripts\python.exe -m pytest
```

의존성 재설치:

```cmd
cd backend
.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Ollama 연결 확인:

```cmd
ollama list
```

백엔드 상태 확인:

```text
http://localhost:8000/api/settings/models
```

`ollama.ok`가 `false`이면 Ollama가 꺼져 있거나 `backend\.env`의 `OLLAMA_BASE_URL`이 잘못된 상태입니다.

## 테스트

백엔드 테스트:

```cmd
cd backend
.venv\Scripts\python.exe -m pytest
```

스모크 테스트:

```cmd
backend\.venv\Scripts\python.exe scripts\smoke_test_backend.py
```

프론트엔드 빌드:

```cmd
cd frontend
pnpm.cmd build
```

## 제한

- 이미지, 수식, 차트, 도형은 수정하지 않고 보존합니다.
- 완전히 빈 새 HWPX를 처음부터 만드는 기능은 아닙니다.
- 업로드한 HWPX의 작업 사본을 수정하고 새 수정본으로 저장하는 방식입니다.

상세 API 목록은 `docs/api.md`를 확인하세요.
