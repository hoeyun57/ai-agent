export type Paragraph = {
  id: string;
  text: string;
  source_xml_path: string;
};

export type Cell = {
  id: string;
  row: number;
  column: number;
  text: string;
  numeric_value?: string | null;
};

export type Table = {
  id: string;
  rows: number;
  columns: number;
  cells: Cell[];
};

export type DocumentModel = {
  id: string;
  filename: string;
  sections: { id: string; order: number; paragraphs: Paragraph[]; tables: Table[] }[];
  tables: Table[];
  unsupported_elements: string[];
};

export type PlanResponse = {
  plan_id: string;
  plan: {
    request_type: string;
    requires_approval: boolean;
    risk_level: string;
    summary: string;
    reason: string;
    actions: { tool: string; arguments: Record<string, unknown>; reason: string }[];
    results?: unknown[];
  };
};

export type RunResponse = PlanResponse & {
  phase: "planned" | "executed" | "completed_readonly";
  result?: unknown;
};

export type MonitoringStatus = {
  ok: boolean;
  documents: number;
  plans: Record<string, number>;
  ollama: { ok?: boolean; error?: string; models?: unknown[] };
  recent_audit: Array<Record<string, unknown>>;
  recent_plans: Array<Record<string, unknown>>;
};

