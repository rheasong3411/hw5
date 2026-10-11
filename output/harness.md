# Campus Customs Agent Harness

This harness documents the database schema and the information agents use while resolving tickets.

## Database reference

The original database is `data/campus_customs.db`. The working copy for later updates is `data/campus_customs_new.db`.

The shop's current date is stored in `desk.date_today` (`2026-08-31` in the original database). Agents should use it when determining overdue invoices, rent, or other deadlines.

## Tables

### `desk`

Fields:

- `date_today` — the shop's authoritative current date.
- `notes` — general desk notes.

Why it matters: Agents use the shop date to determine what is due or overdue and can consult shared operational notes.

### `tickets`

Fields:

- `id` — unique ticket identifier.
- `type` — ticket category, such as `customer_order`, `rent_notice`, or `price_override`.
- `requester` — person or organization making the request.
- `subject` — short ticket subject.
- `sku` — optional product SKU connected to the ticket.
- `size` — optional product size connected to the ticket.
- `qty` — optional requested quantity.
- `lease_id` — optional reference to `leases.id`.
- `invoice_id` — optional reference to `invoices.id`.
- `status` — ticket state, including `open`.
- `notes` — operational details and requested context.
- `created_at` — timestamp when the ticket was created.

Why it matters: The Boss starts here, routes work to agents, and records the resolution state; ticket references connect requests to leases and invoices.

### `inventory`

Fields:

- `sku` — product identifier; part of the composite primary key.
- `name` — product name.
- `size` — product size or option; part of the composite primary key.
- `qty` — available quantity.
- `location` — store location for the item.

Why it matters: Inventory checks whether customer orders can be fulfilled by SKU and size and identifies shortfalls.

### `pricing`

Fields:

- `sku` — product identifier and primary key.
- `unit_cost` — shop cost per unit.
- `list_price` — standard selling price.

Why it matters: Accounting and the Boss use cost and list price to evaluate margins, discounts, and replenishment economics.

### `vendors`

Fields:

- `id` — unique vendor identifier.
- `name` — vendor name.
- `specialty` — products or services the vendor provides.
- `lead_days` — expected vendor lead time in days.

Why it matters: Inventory uses vendor specialties and lead times to identify feasible restocking options.

### `invoices`

Fields:

- `id` — unique invoice identifier.
- `vendor_id` — reference to `vendors.id`.
- `amount` — amount owed.
- `due_date` — payment due date.
- `status` — invoice state, including `open`.
- `description` — reason or details for the invoice.

Why it matters: Accounting monitors vendor obligations, determines overdue status, and checks whether an unpaid invoice blocks new shipments.

### `leases`

Fields:

- `id` — unique lease identifier.
- `space_name` — leased space.
- `landlord` — landlord or property manager.
- `monthly_rent` — recurring rent amount.
- `next_due` — next rent due date.
- `notes` — lease-related notes.

Why it matters: Facilities tracks the shop's space obligations and prepares rent actions for approval.

### `cash_accounts`

Fields:

- `name` — cash account name and primary key.
- `balance` — current available balance.
- `date` — date of the recorded balance.

Why it matters: Accounting checks available cash before requesting or executing an approved payment and must prevent negative balances.

### `payments`

Fields:

- `id` — unique payment identifier.
- `kind` — payment category.
- `ref_id` — optional identifier for the related lease, invoice, or other obligation.
- `amount` — payment amount.
- `account` — cash account used.
- `paid_at` — payment timestamp or date.
- `approved_by` — human approver recorded for the payment.

Why it matters: This is the audit trail for cash outflows; every payment requires human approval and must be reflected here.

## Open ticket links in the original database

- Ticket `101` (`customer_order`) requests one `CC-TEE-WHITE` in size `S`. It links to invoice `501` through `invoice_id`; inventory shows zero size-S tees, and invoice `501` is an open, overdue vendor invoice for the reprint.
- Ticket `102` (`rent_notice`) concerns rent for lease `1`. Lease `1` is for the Chapel Street shop, with `$2,400` due on `2026-09-02`, two days after the shop date of `2026-08-31`.
- Ticket `103` (`price_override`) requests 20 `CC-HOOD-NAVY` hoodies in size `M` at a bulk discount. Inventory has 8 available, and pricing lists a `$22` unit cost and `$58` list price.

## Initial ticket inspection tools

These three read tools were introduced for the initial ticket inspections. The complete current MCP tool inventory, including write and human-only tools, is listed in the table below. MCP reads and writes target `data/campus_customs_new.db` and the pending-request file as described per tool.

### `inspect_customer_order(ticket_id)`

- Tables read: `tickets`, `inventory`, `invoices`, `vendors`, and `desk`.
- Ticket unlocked: `101`.
- Why this is the right tool: For ticket 101, the tool returns 0 size-S tees on hand, invoice 501 for $840 from Bulldog Print Co open and 3 days overdue, and shipping blocked.
- Computed values: `shortfall`; `invoice_overdue`; `invoice_overdue_days`; `shipping_blocked` (true when the vendor has any open invoice).

### `inspect_rent_notice(ticket_id)`

- Tables read: `tickets`, `leases`, `cash_accounts`, and `desk`.
- Ticket unlocked: `102`.
- Why this is the right tool: For ticket 102, the tool returns $2,400 due 2026-09-02, 2 days out, and the checking balance of $3,400.
- Computed values: `days_until_due`; `checking_covers_rent`.

### `inspect_price_override(ticket_id)`

- Tables read: `tickets`, `inventory`, `pricing`, and `desk`.
- Ticket unlocked: `103`.
- Why this is the right tool: For ticket 103, the tool returns 8 size-M hoodies on hand, a shortfall of 12, and a $36 margin per unit (about 62%).
- Computed values: `shortfall`; `margin_per_unit`; `margin_percent`, calculated as `(list_price - unit_cost) / list_price * 100`.

## Agent team

The five PydanticAI agents are in `backend/agents.py`, with one detailed prompt per role in `backend/prompts/`. They call model `gpt-6-luna` through Portkey's Responses endpoint and connect to this MCP server over stdio. Every agent also has the agent-side `delegate(to_agent, task)` PydanticAI tool; it is not an MCP tool, supports all five role names, rejects self-delegation, delegation cycles, and duplicate requests, and shares one mutable, locked run budget with at most six successful delegations. The audit trail records events as each PydanticAI graph node occurs, including each returned model identity, rather than bulk logging after the agent finishes.

- **Boss:** routes tickets and reconciles reports; uses `tickets`, `desk`, and all inspection tools.
- **Inventory:** checks SKU/size stock, vendors, lead times, and shipping blocks; uses `inventory`, `vendors`, `invoices`.
- **Accounting:** checks cash, invoices, leases, margins, and prepares payment requests; uses `cash_accounts`, `invoices`, `leases`, `payments`, `pricing`.
- **Facilities:** handles rent and lease timing; uses `leases`, `cash_accounts`, `desk`, `tickets`.
- **Customer service:** writes truthful customer drafts only; uses order inspection and `tickets`.

Delegation targets: Boss may delegate to Inventory, Accounting, Facilities, or Customer Service. Inventory may delegate to Accounting or Customer Service when evidence is needed. Accounting may delegate to Inventory or Facilities for product or lease evidence. Facilities may delegate to Accounting for rent preparation. Customer Service may delegate to Inventory or Accounting for customer-safe fact checks. The shared runtime rejects self-delegation, current-path cycles, duplicate sender/recipient/task requests, and more than six delegations in one run.

## Complete MCP tool table

| Tool | Tables used | Purpose / safety boundary |
|---|---|---|
| `list_open_tickets()` | `tickets` | Boss/agents may call it to get the current open queue. |
| `list_tickets()` | `tickets` | Backend/dashboard may call it to show all ticket statuses. |
| `set_ticket_status(ticket_id, status, note)` | `tickets`, `desk` | Backend-only; sets open, awaiting_approval, or resolved status and records an optional reason note. Filtered from agents. |
| `get_cash_balance(account)` | `cash_accounts` | Backend/dashboard and agents may call it to read available cash. |
| `list_pending_requests(ticket_id)` | `output/pending_approvals.json` | Agents may read pending requests, optionally by ticket, to avoid duplicate preparations. |
| `list_requests(ticket_id)` | `output/pending_approvals.json` | Agents and dashboard may read all pending, used, and rejected requests, optionally by ticket. |
| `list_payments()` | `payments` | Dashboard and human reviewers may read the completed payment ledger. |
| `find_restock_vendors(sku)` | `inventory`, `pricing`, `vendors`, `invoices` | Agents may call it to match products, lead time, and shipping blocks. |
| `prepare_payment(kind, ref_id, amount, account, ticket_id)` | `cash_accounts`, `invoices`, `leases`; writes `output/pending_approvals.json` | Agents must prepare a human request for a valid ticket obligation, recording optional `ticket_id`; it does not change cash and refuses duplicate pending obligations. |
| `prepare_purchase_order(sku, size, qty, vendor_id, account, ticket_id)` | `inventory`, `pricing`, `vendors`, `invoices`, `cash_accounts`, `desk`; writes `output/pending_approvals.json` | Agents must prepare a human purchase request for an unblocked shortfall, recording optional `ticket_id`; it does not change inventory or cash and refuses duplicate pending orders. |
| `execute_approved_payment(request_id, approved_by)` | `payments`, `cash_accounts`, `invoices`, `leases`, `desk`; updates `output/pending_approvals.json` | Human/backend-only; executes an approved request. Filtered from agents. |
| `reject_payment_request(request_id, rejected_by)` | `output/pending_approvals.json` | Human/backend-only; rejects a pending request without changing cash. Filtered from agents. |
| `request_human_decision(ticket_id, kind, question, recommendation, options)` | `output/pending_decisions.json` | Agent-facing; creates a locked pending discount, fulfillment, or other decision request without changing ticket status; refuses duplicate pending ticket/kind. |
| `list_decisions(ticket_id, status)` | `output/pending_decisions.json` | Agent/dashboard read of decision requests and outcomes. |
| `record_human_decision(decision_id, decided_by, choice, terms)` | `output/pending_decisions.json` | Human/backend-only; records an allowed option or `custom`, actual terms, and UTC decision time. Filtered from agents. |
| `append_ticket_note(ticket_id, agent, note)` | `tickets`, `desk` | Agents may append drafts/review notes only; it cannot change status or contact anyone. |
| `inspect_customer_order(ticket_id)` | `tickets`, `inventory`, `invoices`, `vendors`, `desk` | Agents may inspect ticket 101 evidence. |
| `inspect_rent_notice(ticket_id)` | `tickets`, `leases`, `cash_accounts`, `desk` | Agents may inspect ticket 102 evidence. |
| `inspect_price_override(ticket_id)` | `tickets`, `inventory`, `pricing`, `desk` | Agents may inspect ticket 103 evidence. |

### Agent-side delegation tool

`delegate(to_agent, task)` is a PydanticAI tool registered separately on every agent, not an MCP server tool. Valid roles are `boss`, `inventory`, `accounting`, `facilities`, and `customer_service`. It normalizes role names, rejects self-delegation, current-path cycles, duplicate sender/recipient/task requests, and more than 6 delegations per run. It also caps delegation depth at 3 and passes one shared 60-request/120,000-token budget through all delegated runs. The larger budget accounts for the additional model calls required by the explicit human-decision step. Specialists are instructed to return findings rather than delegate onward unless another specialist's data is strictly required. A usage-limit exception unwinds to the top-level run, which becomes `stopped` and leaves the ticket open.

### Run and approval commands

- `.venv/bin/python -m backend.run_ticket TICKET_ID` — run one ticket through the Boss and delegated agents.
- `.venv/bin/python -m backend.approve_payment` — list pending requests and perform the separate human approval step before calling the guarded payment tool.

## FastAPI backend routes

- `GET /tickets` — returns all tickets and status through MCP.
- `POST /tickets/{ticket_id}/run` — starts a background agent run and returns its run ID.
- `GET /runs/{run_id}` — returns run status and final answer from memory or audit history, scoped to the current session by default.
- `GET /runs` — merges in-memory and audit-rebuilt runs, returning the latest run per ticket in the current session by default.
- `GET /events` — returns recent compact audit events with run/ticket filters and current-session filtering by default.
- `GET /pending-approvals` — lists pending human approval requests.
- `GET /decisions?ticket_id=...&status=...` — returns current-session decisions by default; `all_sessions=true` includes history.
- `POST /decisions/{decision_id}` — JSON `{ "decided_by": "...", "choice": "...", "terms": "..." }`; records the human decision through MCP and audits all fields.
- `GET /requests` — lists all pending, used, and rejected requests, optionally filtered by ticket.
- `GET /payments` — returns the completed payments ledger.
- `POST /approvals` — executes an explicitly approved payment or purchase order through MCP.
- `POST /approvals/{request_id}/reject` — rejects a pending request through the human-only MCP rejection tool.
- `GET /tickets/{ticket_id}/summary` — summarizes the latest run's agents, outputs, tools, and delegation recipients.
- `GET /balance` — returns the current checking balance through MCP.
- `POST /reset` — restores the working DB, clears pending approvals, and appends a reset event.

The dashboard polls `/runs/{run_id}`, `/events`, `/pending-approvals`, and `/balance` while a run is active. On initial load and ticket selection it calls `/runs`, then restores the latest current-session run's events and summary. Add `?all_sessions=true` to history routes to inspect older sessions. Resolution requires the latest current-session run to complete, no pending payment/purchase or human decision requests, and all type-specific dispositions: short customer orders need a decided fulfillment choice, price overrides need a decided discount, and rent notices need their rent request decided. Pending payments produce `awaiting_approval`; other outstanding items produce `awaiting_decision`. The backend records exact outstanding reasons and re-evaluates after every payment or human decision; resolution writes a `final_disposition` audit summary.

`prepare_purchase_order(sku, size, qty, vendor_id)` validates matching vendors, unpaid invoices, pricing, cash, and arrival date; approval records a `purchase_order` payment without increasing inventory. MCP paths may be overridden for isolated test copies with `CAMPUS_CUSTOMS_DB`, `CAMPUS_CUSTOMS_PENDING`, and `CAMPUS_CUSTOMS_DECISIONS`.

## Dashboard

The frontend is a React + Vite + TypeScript desk in `frontend/`. Start the backend from `backend/` with `../.venv/bin/uvicorn main:app --reload --port 8000`, then run `npm run dev` in `frontend/`; Vite serves the dashboard on `:5173` and calls the backend on `:8000`.

The left corkboard calls `GET /tickets` and shows the three paper ticket cards, selection, and `RESOLVED`, `AWAITING APPROVAL`, and `AWAITING DECISION` stamps, plus outstanding request counts. The central shop floor has the five stations; `POST /tickets/{ticket_id}/run`, `GET /runs/{run_id}`, and `GET /events` drive station status, speech bubbles, delegation notes, and the activity feed. The feed is populated from real event records, while `GET /tickets/{ticket_id}/summary` supplies the run summary.

The manager's desk calls `GET /balance` for checking and `GET /pending-approvals` for receipt-style requests and `GET /decisions` for human decision cards; the cards post the signed-in name, choice, and terms to `POST /decisions/{decision_id}`. Approve uses `POST /approvals` and Reject uses `POST /approvals/{request_id}/reject`. `GET /runs` restores the latest run, events, status, and summary after reload or ticket selection. `POST /reset` is available for the documented reset procedure.

Every audit entry written by the application carries the active `session_id`; pre-session events are treated as `legacy`. Reset creates a new UUID session, persists it to `output/session.json`, clears in-memory runs, restores the seed database, and records the reset under the new session. Run, event, summary, and request endpoints default to the current session and accept `all_sessions=true` for historical inspection. The model response event stores `returned_model` with Portkey's returned model and provider names; the Boss final-output record lists the distinct models observed in that run.

## Safety and limits

Agents cannot resolve tickets, approve or reject payments, execute payments, create negative cash, send communications, or invent database facts. `set_ticket_status`, `record_human_decision`, `execute_approved_payment`, and `reject_payment_request` are filtered from every agent toolset; only backend human-controlled routes call them through MCP. Human reviewers verify the obligation, recipient, amount, and remaining cash before approval or rejection. Request preparation, approval, and rejection serialize their pending-file read/check/write path with one exclusive cross-process file lock. Every approved payment runs in one `BEGIN IMMEDIATE` SQLite transaction with a conditional balance debit (`balance >= amount`), checked row count, a conditional open-invoice update, and payment insertion; any failed validation rolls back all database writes. Each run shares at most 60 model requests and 120,000 total tokens, delegation depth 3, and six successful delegations. These request and token limits include headroom for the extra model calls from the explicit human-decision step. When a shared limit is reached, the run logs `usage_limit_exceeded` and `run_stopped`, returns status `stopped`, and leaves the ticket open. `append_ticket_note` only writes a note; all ticket status changes stay in backend/human code and are audit-logged with a reason.

## Problem 9 full run (final reset session)

The final submitted run used session `57ca3122-cfec-4520-85e8-bbc1b3e053ae`; all tickets returned `gpt-6-luna-global` via OpenAI. The configured run budget was 120,000 total tokens / 60 requests per ticket. Each run shared a cap of six successful delegations; self-delegation, path-cycle, and over-cap attempts were refused. This section uses only the final session and its run IDs.

| Ticket | Run ID | Model requests / tokens | Delegation attempts / successes | Human action and explicit disposition |
|---|---|---:|---:|---|
| 101 | `4dd82f176e0d4f69a0786497643c3982` | 33 / 78,243 | 11 / 6 | Rhea approved invoice 501 request `b2e78b94-6e1b-43fd-b449-8176eab7c7b1` ($840.00), then accepted fulfillment decision `17ebdc44-133d-435b-a44e-8a6669b714cf`: defer the unfulfilled tee until Bulldog Print Co restock is confirmed, review the customer draft before sending, and promise no delivery date. Resolution covers both the paid invoice issue and explicit deferral; it is not shipment. |
| 102 | `9a9511c4c46345038c1e1878fa1a1b3a` | 30 / 66,460 | 7 / 5 | Rhea approved lease 1 rent request `85a18ef3-76ca-4aaa-bcde-30eb6735e893` ($2,400.00). No separate decision request was needed. |
| 103 | `1ce25873405c4f9bb0056a09a0406a53` | 37 / 94,452 | 12 / 6 | Rhea rejected PO request `7eeaac61-92c0-4bb6-92f5-4cfbf2d521dd` ($264.00), then recorded discount decision `e8a4d9b5-e742-4e58-8f07-6b1ea438492c`: 10% off 8 in-stock hoodies at $52.20 each ($417.60 total), no discount or delivery promise for the remaining 12, and review the customer draft before sending. The PO rejection alone left the ticket `awaiting_decision`; it resolved after the discount disposition. |

The human decision flow records payment approvals separately from typed fulfillment and discount dispositions. Status therefore remains `awaiting_decision` when a payment or PO request is decided but the required customer-order/discount question remains open. Invoice 501 and lease 1 payments were executed through the serialized approval path; the rejected ticket 103 PO had no cash or inventory effect. No customer or landlord communication was sent and no sale or price change was recorded. The working database ends with checking at $160.00, payment rows 1 and 2 totaling $3,240.00, size-S tees at 0, and size-M hoodies at 8. Lease 1 next_due is 2026-10-02.

Cash order does not affect affordability of the two payments: rent first leaves $1,000.00, enough for the $840 invoice and leaving $160.00; invoice first leaves $2,560.00, enough for $2,400 rent and the same $160.00 end balance. The order affects when Bulldog’s shipping block clears, which matters to the later ticket 103 PO. Individual delegation attempts, refusal reasons, audit timestamps, requests, and final dispositions are documented in `output/audit_trail.json`, `output/pending_approvals.json`, and `output/pending_decisions.json`.

