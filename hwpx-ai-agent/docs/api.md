# API

- `POST /api/documents/upload`: HWPX 업로드
- `GET /api/documents`: 문서 목록
- `GET /api/documents/{document_id}`: 내부 문서 모델 조회
- `GET /api/documents/{document_id}/outline`: 섹션 개요
- `GET /api/documents/{document_id}/tables`: 표 목록
- `POST /api/documents/{document_id}/search`: 텍스트 검색
- `POST /api/documents/{document_id}/validate`: 패키지/표/숫자 검증
- `GET /api/documents/{document_id}/download`: 수정본 또는 원본 다운로드
- `POST /api/agent/chat`: 읽기형 응답 또는 작업 계획 생성
- `POST /api/agent/plan`: 작업 계획 생성
- `GET /api/plans/{plan_id}`: 계획 조회
- `POST /api/plans/{plan_id}/approve`: 승인 후 실행
- `POST /api/plans/{plan_id}/reject`: 거절
- `GET /api/plans/{plan_id}/diff`: 수정 전후 diff
- `GET /api/settings/models`: Ollama 상태와 모델 설정
- `PUT /api/settings/models`: 모델 설정 갱신 요청

