import type {
  Approval,
  HumanDecision,
  Payment,
  Run,
  ShopEvent,
  Ticket,
  TicketSummary,
} from "./types";
export const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}
export const api = {
  tickets: () => request<Ticket[]>("/tickets"),
  runs: () => request<Run[]>("/runs"),
  balance: () =>
    request<{ name: string; balance: number; date: string }>("/balance"),
  approvals: () => request<Approval[]>("/pending-approvals"),
  decisions: () => request<HumanDecision[]>("/decisions"),
  decide: (decision: HumanDecision, name: string, choice: string, terms: string) => request(`/decisions/${decision.decision_id}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decided_by: name, choice, terms }) }),
  requests: (ticketId?: number) =>
    request<Approval[]>(`/requests${ticketId ? `?ticket_id=${ticketId}` : ""}`),
  payments: () => request<Payment[]>("/payments"),
  shopDate: () => request<{ date: string }>("/balance"),
  events: (runId: string) =>
    request<ShopEvent[]>(
      `/events?run_id=${encodeURIComponent(runId)}&limit=500`,
    ),
  run: (id: number) => request<Run>(`/tickets/${id}/run`, { method: "POST" }),
  runStatus: (id: string) => request<Run>(`/runs/${id}`),
  summary: (ticketId: number, runId: string) =>
    request<TicketSummary>(`/tickets/${ticketId}/summary?run_id=${runId}`),
  approve: (a: Approval, name: string) =>
    request(`/approvals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        request_id: a.request_id,
        approved_by: name,
        approve: true,
      }),
    }),
  reject: (a: Approval, name: string) =>
    request(`/approvals/${a.request_id}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved_by: name }),
    }),
};
