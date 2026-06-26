import type { DocumentModel, PlanResponse } from "../types";

const jsonHeaders = { "Content-Type": "application/json" };

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export async function uploadDocument(file: File): Promise<DocumentModel> {
  const form = new FormData();
  form.append("file", file);
  return parse<DocumentModel>(await fetch("/api/documents/upload", { method: "POST", body: form }));
}

export async function listDocuments(): Promise<Array<{ id: string; filename: string; created_at: string }>> {
  return parse(await fetch("/api/documents"));
}

export async function getDocument(id: string): Promise<DocumentModel> {
  return parse(await fetch(`/api/documents/${id}`));
}

export async function createPlan(documentId: string, message: string): Promise<PlanResponse> {
  return parse(
    await fetch("/api/agent/plan", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ document_id: documentId, message })
    })
  );
}

export async function approvePlan(planId: string): Promise<unknown> {
  return parse(await fetch(`/api/plans/${planId}/approve`, { method: "POST" }));
}

export async function rejectPlan(planId: string): Promise<unknown> {
  return parse(await fetch(`/api/plans/${planId}/reject`, { method: "POST" }));
}

export async function getDiff(planId: string): Promise<{ diff: string }> {
  return parse(await fetch(`/api/plans/${planId}/diff`));
}

export async function validateDocument(documentId: string): Promise<unknown> {
  return parse(await fetch(`/api/documents/${documentId}/validate`, { method: "POST" }));
}

export async function getModels(): Promise<unknown> {
  return parse(await fetch("/api/settings/models"));
}

