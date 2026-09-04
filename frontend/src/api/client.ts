/**
 * API client — all backend communication goes through here.
 *
 * React components never call fetch() directly.
 * In future milestones, swap BASE_URL or add auth headers here.
 */
import type { QueryRequest, QueryResponse } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// ── Health ────────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error("Backend health check failed");
  return res.json();
}

// ── Query ─────────────────────────────────────────────────────────────────────

export async function sendQuery(request: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `Request failed: ${res.status}`);
  }

  return res.json();
}
