import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Route, Routes } from "react-router-dom";
import { Check, Download, RefreshCw, Search, ShieldCheck, X } from "lucide-react";
import {
  approvePlan,
  createPlan,
  getDiff,
  getDocument,
  getLlmEvents,
  getMonitoringStatus,
  getModels,
  listDocuments,
  rejectPlan,
  runAgent,
  uploadDocument,
  validateDocument
} from "../api/client";
import type { DocumentModel, LlmEvent, PlanResponse } from "../types";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route path="/documents" element={<DocumentsPage />} />
      <Route path="/agent" element={<AgentPage />} />
      <Route path="/monitoring" element={<MonitoringPage />} />
      <Route path="/developer" element={<DeveloperPage />} />
      <Route path="/plans" element={<PlansPage />} />
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/settings" element={<SettingsPage />} />
    </Routes>
  );
}

function UploadPage() {
  const [document, setDocument] = useState<DocumentModel | null>(null);
  const mutation = useMutation({ mutationFn: uploadDocument, onSuccess: setDocument });
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>문서 업로드</h2>
        <p>HWPX 원본은 보존되고 작업 사본에서만 분석과 수정이 진행됩니다.</p>
      </div>
      <label className="drop">
        <input
          type="file"
          accept=".hwpx"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) mutation.mutate(file);
          }}
        />
        <span>HWPX 파일 선택</span>
      </label>
      {mutation.isPending && <p>업로드와 구조 분석 중...</p>}
      {mutation.error && <p className="error">{String(mutation.error)}</p>}
      {document && <DocumentSummary document={document} />}
    </section>
  );
}

function DocumentsPage() {
  const docs = useQuery({ queryKey: ["documents"], queryFn: listDocuments });
  const [selectedId, setSelectedId] = useState<string>("");
  const detail = useQuery({ queryKey: ["document", selectedId], queryFn: () => getDocument(selectedId), enabled: Boolean(selectedId) });
  return (
    <section className="split">
      <div className="panel">
        <div className="panelHeader">
          <h2>문서 목록</h2>
          <button onClick={() => docs.refetch()} title="새로고침">
            <RefreshCw size={16} />
          </button>
        </div>
        <div className="list">
          {(docs.data ?? []).map((doc) => (
            <button className={selectedId === doc.id ? "row selected" : "row"} key={doc.id} onClick={() => setSelectedId(doc.id)}>
              <strong>{doc.filename}</strong>
              <span>{doc.id}</span>
            </button>
          ))}
        </div>
      </div>
      <div className="panel wide">{detail.data ? <DocumentSummary document={detail.data} /> : <Empty label="문서를 선택하세요" />}</div>
    </section>
  );
}

function AgentPage() {
  const docs = useQuery({ queryKey: ["documents"], queryFn: listDocuments });
  const [documentId, setDocumentId] = useState("");
  const [message, setMessage] = useState("이 문서 양식을 유지해서 AI 에이전트 계획서를 작성해줘");
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [runResult, setRunResult] = useState<unknown>(null);
  const mutation = useMutation({ mutationFn: () => createPlan(documentId, message), onSuccess: setPlan });
  const runMutation = useMutation({
    mutationFn: () => runAgent(documentId, message, true),
    onSuccess: (data) => {
      setPlan(data);
      setRunResult(data);
    }
  });
  const examples = [
    "이 공문 양식의 빈칸을 유지해서 AI 도입 안내 공문을 작성해줘",
    "이 문서 양식을 유지해서 AI 에이전트 계획서를 작성해줘",
    "2025년을 모두 2026년으로 변경해줘",
    "예산 합계가 맞는지 확인해줘",
    "본문과 표의 숫자 불일치를 찾아줘"
  ];
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>AI 채팅</h2>
        <p>수정 작업은 계획 생성 후 승인 화면에서만 실행됩니다.</p>
      </div>
      <div className="formGrid">
        <select value={documentId} onChange={(event) => setDocumentId(event.target.value)}>
          <option value="">문서 선택</option>
          {(docs.data ?? []).map((doc) => (
            <option value={doc.id} key={doc.id}>
              {doc.filename}
            </option>
          ))}
        </select>
        <textarea value={message} onChange={(event) => setMessage(event.target.value)} />
        <div className="exampleBar">
          {examples.map((example) => (
            <button type="button" key={example} onClick={() => setMessage(example)}>
              {example}
            </button>
          ))}
        </div>
        <div className="toolbar compact">
          <button disabled={!documentId || mutation.isPending} onClick={() => mutation.mutate()}>
            <Search size={16} />
            계획 생성
          </button>
          <button disabled={!documentId || runMutation.isPending} onClick={() => runMutation.mutate()} title="계획 생성과 승인을 한 번에 실행">
            한번에 실행
          </button>
        </div>
      </div>
      {plan && <PlanView response={plan} />}
      {runResult ? (
        <>
          <h3>한번에 실행 결과</h3>
          <pre>{JSON.stringify(runResult, null, 2)}</pre>
        </>
      ) : null}
    </section>
  );
}

function MonitoringPage() {
  const status = useQuery({ queryKey: ["monitoring"], queryFn: getMonitoringStatus, refetchInterval: 5000 });
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>모니터링</h2>
        <p>문서 수, 계획 상태, Ollama 연결, 최근 작업 로그를 5초마다 갱신합니다.</p>
      </div>
      <div className="metrics">
        <span>문서 {status.data?.documents ?? 0}</span>
        <span>Ollama {status.data?.ollama?.ok ? "연결됨" : "확인 필요"}</span>
        {Object.entries(status.data?.plans ?? {}).map(([key, value]) => (
          <span key={key}>
            {key} {value}
          </span>
        ))}
      </div>
      <h3>최근 계획</h3>
      <pre>{status.data ? JSON.stringify(status.data.recent_plans, null, 2) : "불러오는 중..."}</pre>
      <h3>최근 작업 로그</h3>
      <pre>{status.data ? JSON.stringify(status.data.recent_audit, null, 2) : "불러오는 중..."}</pre>
    </section>
  );
}

function DeveloperPage() {
  const events = useQuery({ queryKey: ["llm-events"], queryFn: () => getLlmEvents(100), refetchInterval: 3000 });
  return (
    <section className="panel">
      <div className="panelHeader">
        <div>
          <h2>개발자 모니터링</h2>
          <p>LLM 호출의 프롬프트, 원문 응답, JSON 파싱 결과, 오류와 fallback 여부를 3초마다 갱신합니다.</p>
        </div>
        <button onClick={() => events.refetch()} title="새로고침">
          <RefreshCw size={16} />
        </button>
      </div>
      <div className="devLog">
        {(events.data?.items ?? []).map((event) => (
          <LlmEventView event={event} key={event.id} />
        ))}
        {events.isLoading ? <Empty label="LLM 이벤트를 불러오는 중입니다." /> : null}
        {events.data?.items.length === 0 ? <Empty label="아직 기록된 LLM 이벤트가 없습니다." /> : null}
      </div>
    </section>
  );
}

function LlmEventView({ event }: { event: LlmEvent }) {
  return (
    <article className="devEvent">
      <div className="devEventHeader">
        <strong>{event.task}</strong>
        <span>{event.model || "model 없음"}</span>
        <span>{event.document_id || "문서 없음"}</span>
        <span>{event.created_at}</span>
        <span>{event.used_fallback ? "fallback" : "llm"}</span>
      </div>
      {event.error ? <p className="error">오류: {event.error}</p> : null}
      <h3>프롬프트</h3>
      <pre>{event.prompt_text}</pre>
      <h3>LLM 원문 응답</h3>
      <pre>{event.raw_response || "원문 응답 없음"}</pre>
      <h3>파싱 결과</h3>
      <pre>{event.parsed ? JSON.stringify(event.parsed, null, 2) : "파싱 결과 없음"}</pre>
    </article>
  );
}

function PlansPage() {
  const [planId, setPlanId] = useState("");
  const approve = useMutation({ mutationFn: () => approvePlan(planId) });
  const reject = useMutation({ mutationFn: () => rejectPlan(planId) });
  const diff = useQuery({ queryKey: ["diff", planId, approve.isSuccess], queryFn: () => getDiff(planId), enabled: Boolean(planId) });
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>수정 승인</h2>
        <p>변경 대상, 변경 이유, 위험 수준을 확인한 뒤 실행합니다.</p>
      </div>
      <div className="toolbar">
        <input value={planId} onChange={(event) => setPlanId(event.target.value)} placeholder="plan-id 입력" />
        <button disabled={!planId} onClick={() => approve.mutate()}>
          <Check size={16} />
          승인
        </button>
        <button disabled={!planId} onClick={() => reject.mutate()}>
          <X size={16} />
          거절
        </button>
      </div>
      {approve.data ? <pre>{JSON.stringify(approve.data, null, 2)}</pre> : null}
      {reject.data ? <pre>{JSON.stringify(reject.data, null, 2)}</pre> : null}
      <h3>수정 전후 차이</h3>
      <pre>{diff.data?.diff || "승인 실행 후 diff가 표시됩니다."}</pre>
    </section>
  );
}

function HistoryPage() {
  const docs = useQuery({ queryKey: ["documents"], queryFn: listDocuments });
  const [documentId, setDocumentId] = useState("");
  const validation = useMutation({ mutationFn: () => validateDocument(documentId) });
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>검증 결과</h2>
        <p>패키지 유효성, 표 합계, 본문/표 숫자 일관성을 확인합니다.</p>
      </div>
      <div className="toolbar">
        <select value={documentId} onChange={(event) => setDocumentId(event.target.value)}>
          <option value="">문서 선택</option>
          {(docs.data ?? []).map((doc) => (
            <option value={doc.id} key={doc.id}>
              {doc.filename}
            </option>
          ))}
        </select>
        <button disabled={!documentId} onClick={() => validation.mutate()}>
          <ShieldCheck size={16} />
          검증
        </button>
      </div>
      <pre>{validation.data ? JSON.stringify(validation.data, null, 2) : "검증할 문서를 선택하세요."}</pre>
    </section>
  );
}

function SettingsPage() {
  const models = useQuery({ queryKey: ["models"], queryFn: getModels });
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>모델 설정</h2>
        <p>Ollama 연결과 Q4/Q8 모델 설정을 확인합니다.</p>
      </div>
      <pre>{models.data ? JSON.stringify(models.data, null, 2) : "Ollama 상태 확인 중..."}</pre>
    </section>
  );
}

function DocumentSummary({ document }: { document: DocumentModel }) {
  return (
    <div className="summary">
      <div className="summaryHeader">
        <h3>{document.filename}</h3>
        <a href={`/api/documents/${document.id}/download`}>
          <Download size={16} />
          다운로드
        </a>
      </div>
      <div className="metrics">
        <span>섹션 {document.sections.length}</span>
        <span>문단 {document.sections.reduce((sum, section) => sum + section.paragraphs.length, 0)}</span>
        <span>표 {document.tables.length}</span>
        <span>미지원 {document.unsupported_elements.length}</span>
      </div>
      <h4>문서 구조</h4>
      {document.sections.map((section) => (
        <div className="sectionBlock" key={section.id}>
          <strong>{section.id}</strong>
          {section.paragraphs.slice(0, 5).map((paragraph) => (
            <p key={paragraph.id}>{paragraph.text}</p>
          ))}
          {section.tables.map((table) => (
            <table key={table.id}>
              <tbody>
                {Array.from({ length: table.rows }).map((_, rowIndex) => (
                  <tr key={rowIndex}>
                    {table.cells
                      .filter((cell) => cell.row === rowIndex + 1)
                      .map((cell) => (
                        <td key={cell.id}>{cell.text}</td>
                      ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ))}
        </div>
      ))}
    </div>
  );
}

function PlanView({ response }: { response: PlanResponse }) {
  return (
    <div className="plan">
      <h3>작업 계획: {response.plan.summary}</h3>
      <div className="metrics">
        <span>계획 ID {response.plan_id}</span>
        <span>위험 {response.plan.risk_level}</span>
        <span>{response.plan.requires_approval ? "승인 필요" : "즉시 실행"}</span>
      </div>
      {response.plan.actions.map((action, index) => (
        <div className="action" key={`${action.tool}-${index}`}>
          <strong>{action.tool}</strong>
          <p>{action.reason}</p>
          {action.tool === "fill_template_fields" ? <p className="hint">감지된 양식 빈칸은 승인 후 생성된 내용으로 채워집니다.</p> : null}
          {action.tool === "append_paragraphs" ? <p className="hint">감지된 빈칸이 없으면 생성된 초안은 승인 후 문서 끝에 문단으로 추가됩니다.</p> : null}
          <pre>{JSON.stringify(action.arguments, null, 2)}</pre>
        </div>
      ))}
      {response.plan.results ? <pre>{JSON.stringify(response.plan.results, null, 2)}</pre> : null}
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return <p className="empty">{label}</p>;
}

