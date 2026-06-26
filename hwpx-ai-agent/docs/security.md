# Security Design

- 외부 LLM API 호출 금지: AI 호출은 `OLLAMA_BASE_URL`의 로컬 Ollama HTTP API만 사용한다.
- ZIP Slip 방지: 압축 멤버명에 절대 경로 또는 `..`가 있으면 거부한다.
- 압축 폭탄 방지: 멤버 수와 전체 해제 용량을 제한한다.
- XXE 방지: `<!DOCTYPE`과 `<!ENTITY`가 있는 XML은 거부하고 `defusedxml`로 파싱한다.
- 원본 보존: 업로드 원본은 `data/originals`에 보관하며 편집은 `data/workspaces` 사본에만 적용한다.
- 승인 게이트: 문서 변경 계획은 `pending_approval` 상태로 저장되고 승인 API 호출 전에는 실행되지 않는다.
- 로그 최소화: 감사 로그에는 문서 전체 원문을 저장하지 않는다.

