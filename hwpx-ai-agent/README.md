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

## 처음 설치 순서

아래 예시는 프로젝트가 다음 위치에 있다고 가정합니다.

```text
C:\Users\OPENCC\Desktop\ai-agent-master\
└─ hwpx-ai-agent\
```

다른 위치에 압축을 풀었다면 명령의 경로만 본인 PC에 맞게 바꾸면 됩니다.

## 1. Ollama 모델 확인

먼저 Ollama가 실행 중인지 확인합니다.

```cmd
ollama list
```

아래처럼 모델이 보이면 이미 준비된 상태입니다.

```text
hwpx-agent-q4:latest
hwpx-agent-q8:latest
```

이미 다른 이름으로 등록된 모델이 있다면 그대로 써도 됩니다. 예를 들어:

```text
qwen3.5-deepseek-q4:latest
qwen3.5-deepseek-q8:latest
```

이 경우 `backend\.env`에서 모델 이름만 맞추면 됩니다.

## 2. 모델을 새 이름으로 맞추기

앱 기본값은 `hwpx-agent-q4`, `hwpx-agent-q8`입니다. 이미 등록된 모델을 복사해서 이름만 맞추려면:

```cmd
ollama cp qwen3.5-deepseek-q4:latest hwpx-agent-q4
ollama cp qwen3.5-deepseek-q8:latest hwpx-agent-q8
ollama list
```

GGUF 파일에서 직접 등록해야 한다면, GGUF 파일과 Modelfile이 있는 폴더에서 실행합니다.

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master
ollama create hwpx-agent-q4:latest -f Modelfile_q4
ollama create hwpx-agent-q8:latest -f Modelfile_q8
```

`invalid model name`이 나오면 Modelfile의 `FROM` 줄을 확인하세요. GGUF 파일을 직접 가리킬 때는 보통 아래처럼 상대 경로를 씁니다.

```text
FROM ./Qwen3.5-9B-DeepSeek-V4-Flash-Q4_K_M.gguf
```

## 3. 백엔드 설정 파일 만들기

`backend\.env` 파일은 직접 만들어야 합니다.

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\backend
copy .env.example .env
notepad .env
```

기본 모델 이름을 쓸 경우:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_FAST_MODEL=hwpx-agent-q4
OLLAMA_QUALITY_MODEL=hwpx-agent-q8
OLLAMA_DEFAULT_MODEL=hwpx-agent-q4
MODEL_MODE=auto
```

이미 등록된 기존 모델 이름을 그대로 쓸 경우:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_FAST_MODEL=qwen3.5-deepseek-q4:latest
OLLAMA_QUALITY_MODEL=qwen3.5-deepseek-q8:latest
OLLAMA_DEFAULT_MODEL=qwen3.5-deepseek-q4:latest
MODEL_MODE=auto
```

`.env`를 수정한 뒤에는 백엔드를 껐다가 다시 켜야 반영됩니다.

## 4. 백엔드 설치와 실행

Python 3.14에서는 일부 패키지 호환성이 불안정할 수 있으므로 Python 3.12 사용을 권장합니다.

CMD에서 실행:

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\backend
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

정상 실행되면 아래와 비슷하게 표시됩니다.

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

브라우저에서 백엔드 상태를 확인할 수 있습니다.

```text
http://localhost:8000/api/settings/models
http://localhost:8000/docs
```

`/api/settings/models`에서 `ollama.ok`가 `true`면 Ollama 연결이 정상입니다.

## 5. 프론트엔드 설치와 실행

새 CMD 창을 열고 실행합니다.

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\frontend
pnpm.cmd install
pnpm.cmd dev
```

PowerShell에서 `pnpm.ps1` 실행 정책 오류가 나면 `pnpm` 대신 `pnpm.cmd`를 쓰면 됩니다.

정상 실행 후 브라우저에서 접속합니다.

```text
http://localhost:5173
```

## 실제 사용 순서

1. 백엔드 CMD 창을 켜둡니다.
2. 프론트엔드 CMD 창을 켜둡니다.
3. 브라우저에서 `http://localhost:5173`을 엽니다.
4. `업로드` 화면에서 HWPX 파일을 선택합니다.
5. `문서` 화면에서 문단과 표가 추출됐는지 확인합니다.
6. `AI 작업` 화면에서 문서를 선택합니다.
7. 예시 요청을 입력합니다.

```text
2025년을 모두 2026년으로 변경해줘
```

8. `계획 생성`을 누릅니다.
9. 화면에 `계획 ID`가 표시되면 복사합니다.
10. `승인` 화면으로 이동합니다.
11. plan ID를 붙여넣고 `승인`을 누릅니다.
12. 수정본이 생성되고 diff가 표시됩니다.
13. 문서 화면 또는 다운로드 링크에서 결과 파일을 받습니다.

문서 수정은 계획 생성만으로 바로 적용되지 않습니다. 반드시 `승인` 화면에서 승인해야 실제 HWPX 수정본이 생성됩니다.

## 프론트엔드 화면별 사용법

프론트엔드는 브라우저에서 아래 주소로 접속합니다.

```text
http://localhost:5173
```

왼쪽 메뉴에서 화면을 이동합니다.

### 업로드

HWPX 파일을 처음 넣는 화면입니다.

1. 왼쪽 메뉴에서 `업로드`를 누릅니다.
2. `HWPX 파일 선택` 영역을 클릭합니다.
3. `.hwpx` 파일을 선택합니다.
4. 업로드가 끝나면 파일명, 섹션 수, 문단 수, 표 수가 표시됩니다.

업로드한 원본 파일은 직접 수정되지 않습니다. 수정 작업은 서버의 작업 사본에서 진행되고, 승인 후 새 HWPX 파일로 저장됩니다.

### 문서

업로드한 문서의 구조와 내용을 확인하는 화면입니다.

1. 왼쪽 메뉴에서 `문서`를 누릅니다.
2. 문서 목록에서 확인할 파일을 클릭합니다.
3. 오른쪽에서 문단 텍스트와 표 셀 내용을 확인합니다.
4. `다운로드` 버튼을 누르면 현재 문서 파일을 받을 수 있습니다.

아직 수정본이 생성되지 않았다면 다운로드는 원본을 내려받습니다. 수정 승인 후에는 수정본을 내려받습니다.

### AI 작업

자연어 요청으로 작업 계획을 만드는 화면입니다.

1. 왼쪽 메뉴에서 `AI 작업`을 누릅니다.
2. `문서 선택` 드롭다운에서 대상 문서를 선택합니다.
3. 요청 문장을 입력합니다.
4. `계획 생성` 버튼을 누릅니다.
5. 아래에 `작업 계획`과 `계획 ID`가 표시되는지 확인합니다.

예시 요청:

```text
2025년을 모두 2026년으로 변경해줘
```

```text
예산 합계가 맞는지 확인해줘
```

계획 생성 단계에서는 수정이 바로 적용되지 않습니다. 수정 작업은 반드시 `승인` 화면에서 실행해야 합니다.

### 승인

AI가 만든 수정 계획을 실제 문서에 적용하거나 거절하는 화면입니다.

1. `AI 작업` 화면에서 나온 `계획 ID`를 복사합니다.
2. 왼쪽 메뉴에서 `승인`을 누릅니다.
3. 입력칸에 plan ID를 붙여넣습니다.
4. 적용하려면 `승인`을 누릅니다.
5. 적용하지 않으려면 `거절`을 누릅니다.
6. 승인 후 아래의 `수정 전후 차이` 영역에서 diff를 확인합니다.

승인을 누르면 새 HWPX 파일이 생성됩니다. 원본 파일은 그대로 보존됩니다.

### 이력

문서 검증 결과를 확인하는 화면입니다.

1. 왼쪽 메뉴에서 `이력`을 누릅니다.
2. `문서 선택`에서 검사할 문서를 고릅니다.
3. `검증` 버튼을 누릅니다.
4. 패키지 유효성, 표 합계 검산, 본문/표 숫자 불일치 결과를 확인합니다.

현재 MVP에서는 감사 로그 목록 화면이라기보다 검증 결과 확인 화면에 가깝습니다.

### 설정

Ollama 연결 상태와 모델 설정을 확인하는 화면입니다.

1. 왼쪽 메뉴에서 `설정`을 누릅니다.
2. `ollama.ok` 값이 `true`인지 확인합니다.
3. `fast_model`, `quality_model`, `default_model` 이름이 `ollama list`에 있는 모델 이름과 맞는지 확인합니다.

`ollama.ok`가 `false`이면 Ollama 앱이 꺼져 있거나 `.env`의 `OLLAMA_BASE_URL`이 잘못된 상태입니다.

## 프론트엔드에서 자주 헷갈리는 부분

- `계획 생성`은 수정 실행이 아닙니다. 변경은 `승인` 화면에서 승인해야 적용됩니다.
- 모델이 잠깐 실행됐다가 멈추는 것은 정상일 수 있습니다. 계획 JSON 생성 요청이 끝났다는 뜻입니다.
- plan ID는 `AI 작업` 화면의 결과 카드에 표시됩니다.
- diff는 `승인` 이후에 표시됩니다.
- 문서 목록이 비어 있으면 먼저 `업로드` 화면에서 HWPX 파일을 올려야 합니다.
- 화면이 반응하지 않으면 백엔드 CMD 창에 `POST /api/agent/plan 200 OK` 같은 로그가 찍히는지 확인하세요.

## 자주 쓰는 요청 예시

텍스트 전체 교체:

```text
2025년을 모두 2026년으로 변경해줘
```

예산 합계 검산:

```text
예산 합계가 맞는지 확인해줘
```

본문과 표 숫자 비교:

```text
본문과 표의 숫자 불일치를 찾아줘
```

현재 MVP에서는 텍스트 교체, 표 추출, 표 합계 검산, 숫자 불일치 탐지가 중심 기능입니다. 이미지, 수식, 차트, 도형 수정은 아직 지원하지 않습니다.

## 기존 PowerShell 기준 빠른 실행

PowerShell을 쓰는 경우에는 아래처럼 실행할 수도 있습니다.

```powershell
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

다른 PowerShell 창:

```powershell
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\frontend
pnpm.cmd dev
```

## 문제 해결

### `uvicorn`이 없다고 나올 때

아래처럼 `python -m uvicorn` 방식으로 실행하세요.

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

그래도 안 되면 의존성을 다시 설치합니다.

```cmd
.venv\Scripts\python.exe -m pip install -e ".[test]"
```

### `pytest`가 없다고 나올 때

전역 `pytest`가 아니라 가상환경 안의 Python으로 실행하세요.

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\backend
.venv\Scripts\python.exe -m pytest
```

`No module named pytest`가 나오면:

```cmd
.venv\Scripts\python.exe -m pip install -e ".[test]"
```

### `pnpm.ps1` 실행 정책 오류

PowerShell에서 이런 오류가 날 수 있습니다.

```text
이 시스템에서 스크립트를 실행할 수 없으므로 pnpm.ps1 파일을 로드할 수 없습니다.
```

이때는 `pnpm.cmd`를 사용하세요.

```cmd
pnpm.cmd install
pnpm.cmd dev
```

### 계획 생성 시 모델이 잠깐 실행됐다가 멈출 때

정상일 수 있습니다. 계획 생성은 긴 대화가 아니라 JSON 계획을 한 번 만들고 끝나는 요청입니다. 백엔드 CMD 창에 아래처럼 나오면 성공입니다.

```text
POST /api/agent/plan HTTP/1.1" 200 OK
```

프론트 화면에 계획이 표시되지 않으면 브라우저 개발자 도구의 Console/Network 오류를 확인하세요.

### Ollama 연결이 안 될 때

Ollama 모델 목록을 확인합니다.

```cmd
ollama list
```

백엔드 상태 API도 확인합니다.

```text
http://localhost:8000/api/settings/models
```

`ollama.ok`가 `false`이면 Ollama 앱이 실행 중인지, `.env`의 `OLLAMA_BASE_URL`이 맞는지 확인하세요.

### Python 3.14를 쓰고 있을 때

패키지 설치가 실패하면 Python 3.12로 가상환경을 다시 만드는 것을 권장합니다.

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\backend
rmdir /s /q .venv
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[test]"
```

## 테스트

pytest가 설치된 개발 환경:

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent\backend
.venv\Scripts\python.exe -m pytest
```

pytest가 없는 최소 환경에서는 smoke test를 실행할 수 있습니다.

```cmd
cd C:\Users\OPENCC\Desktop\ai-agent-master\hwpx-ai-agent
backend\.venv\Scripts\python.exe scripts\smoke_test_backend.py
```

## API 문서

상세 목록은 `docs/api.md`를 확인하세요. FastAPI 실행 중에는 `/docs`에서 OpenAPI UI를 볼 수 있습니다.

## 제한과 향후 작업

MVP는 이미지, 수식, 차트, 도형을 수정하지 않고 보존합니다. 규정 추출은 API와 도구 확장 지점을 제공하며, 실제 고정밀 규정 분석은 로컬 Q8 모델 프롬프트와 사용자 검토 UI를 추가해 확장합니다.

