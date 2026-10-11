export type Role =
  "boss" | "inventory" | "accounting" | "facilities" | "customer_service";
export type Ticket = {
  id: number;
  type: string;
  requester: string;
  subject: string;
  status: string;
};
export type ShopEvent = {
  id: string;
  time?: string;
  agent: string;
  action: string;
  tool?: string;
  args?: unknown;
  task?: string;
  text: string;
  to_agent?: string;
  from_agent?: string;
  returned_model?: {
    model_name?: string | null;
    provider_name?: string | null;
  };
};
export type Approval = {
  request_id: string;
  kind: string;
  amount: number;
  ref_id?: number;
  status: string;
  expected_arrival?: string;
  ticket_id?: number;
  approved_by?: string;
  rejected_by?: string;
};
export type HumanDecision = { decision_id: string; ticket_id: number; kind: string; question: string; recommendation: string; options: string[]; status: string; created_at: string; choice?: string; decided_by?: string; decided_at?: string; terms?: string };
export type Payment = {
  id: number;
  kind: string;
  ref_id: number;
  amount: number;
  account: string;
  paid_at: string;
  approved_by: string;
};
export type Run = {
  run_id: string;
  ticket_id: number;
  status: "queued" | "running" | "completed" | "stopped" | "error" | "unknown";
  answer?: string | null;
  error?: string;
};
export type SummaryAgent = {
  agent: Role;
  summary: string;
  tools: string[];
  delegated_to: string[];
};
export type TicketSummary = {
  ticket_id: number;
  run_id: string | null;
  agents: SummaryAgent[];
  delegation_attempts?: number;
  delegation_successes?: number;
  returned_models?: { model_name: string; provider_name?: string | null }[];
};
export const ROLE_NAMES: Record<string, string> = {
  boss: "Boss",
  inventory: "Inventory",
  accounting: "Accounting",
  facilities: "Facilities",
  customer_service: "Customer Service",
};
export const ROLES: Role[] = [
  "boss",
  "inventory",
  "accounting",
  "facilities",
  "customer_service",
];
