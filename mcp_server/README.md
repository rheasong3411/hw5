# Campus Customs MCP Server

This FastMCP server is the only shop-data boundary for the Campus Customs agent team. By default it uses `data/campus_customs_new.db` and `output/pending_approvals.json`; `CAMPUS_CUSTOMS_DB` and `CAMPUS_CUSTOMS_PENDING` can select temporary test paths. The original `data/campus_customs.db` is never used for updates.

Problem 3 began with the three inspection tools `inspect_customer_order`, `inspect_rent_notice`, and `inspect_price_override`. Later problems added the other tools listed here for ticket reads, guarded status changes, request preparation and decisions, payments, notes, and dashboard data.

The server provides these tools:

- `inspect_customer_order(ticket_id)` — reads a customer-order ticket, its SKU/size inventory, linked invoice, and vendor details, then computes the stock shortfall, linked-invoice overdue status and days, and whether any open invoice blocks that vendor from shipping. It supports ticket 101.
- `inspect_rent_notice(ticket_id)` — reads a rent-notice ticket, linked lease, and cash-account balances, then computes days until rent is due and whether checking covers the rent. It supports ticket 102.
- `inspect_price_override(ticket_id)` — reads a price-override ticket, requested SKU/size inventory, and SKU pricing, then computes the stock shortfall, margin per unit, and margin percent. It supports ticket 103.
- `list_open_tickets()` — lists open work from `tickets`.
- `list_tickets()` — lists all tickets and statuses for the dashboard.
- `set_ticket_status(ticket_id, status, note)` — backend-only; backend may set `open`, `awaiting_approval`, `awaiting_decision`, or `resolved`, and records an optional board note. Filtered from agents.
- `get_cash_balance(account)` — returns a cash-account balance for the dashboard.
- `list_pending_requests(ticket_id)` — reads pending approval records so agents can avoid preparing a duplicate obligation.
- `list_requests(ticket_id)` — reads all payment and purchase requests, including pending, used, and rejected decisions.
- `list_payments()` — reads the completed `payments` ledger.
- `find_restock_vendors(sku)` — reads `inventory`, `pricing`, `vendors`, and `invoices` to match products to vendors using product fields, vendor specialties, or SKU-bearing invoice descriptions; returns match reasons, lead days, and shipping blocks.
- `prepare_payment(kind, ref_id, amount, account, ticket_id)` — reads `cash_accounts` plus the validating `invoices` or `leases` obligation. It accepts only an exact open invoice or exact lease rent request, writes a pending request with optional `ticket_id` to `output/pending_approvals.json`, and does not change the database. It refuses a duplicate pending obligation.
- `prepare_purchase_order(sku, size, qty, vendor_id, account, ticket_id)` — validates product/vendor, unpaid invoices, cost, cash, and arrival date, then records a pending purchase with optional `ticket_id` without changing inventory. It refuses a duplicate pending order.
- `execute_approved_payment(request_id, approved_by)` — reads the pending-request file and `cash_accounts`, `invoices`, `leases`, `pricing`, `vendors`, `inventory`, and `desk` (purchase-order validation); on success writes `payments`, updates cash and the linked obligation, and marks the pending request used. This tool is filtered from agent toolsets and is called by the separate human approval script.
- `reject_payment_request(request_id, rejected_by)` — marks a pending payment or purchase request rejected without changing cash. This human-only tool is called by the backend reject route.
- `append_ticket_note(ticket_id, agent, note)` — appends a draft/review note without changing ticket status; it never sends communications.
- `request_human_decision(ticket_id, kind, question, recommendation, options)` — agent-facing. Records a pending human decision (`discount`, `fulfillment`, or `other`) in `output/pending_decisions.json` under a file lock, with a decision id and UTC `created_at`. It refuses a duplicate pending decision of the same kind for the ticket and never changes ticket status.
- `list_decisions(ticket_id, status)` — read-only; lists pending and decided human decisions.
- `record_human_decision(decision_id, decided_by, choice, terms)` — human-only, filtered from agent toolsets and called by the backend `POST /decisions/{decision_id}` route. Marks a pending decision decided with the human's name, choice, terms, and the current UTC `decided_at` (never backdated). It refuses unknown or already-decided ids and an empty `decided_by`.

The agent-side `delegate(to_agent, task)` tool is a PydanticAI tool registered on all five agents, not an MCP tool. It permits the five role names (`boss`, `inventory`, `accounting`, `facilities`, `customer_service`), rejects self-delegation, caps depth at 3, and shares one run budget across delegations.

Run one ticket with `.venv/bin/python -m backend.run_ticket TICKET_ID`. Run the separate human approval workflow with `.venv/bin/python -m backend.approve_payment`.

All date calculations use `desk.date_today` from the working database. Margin percent is calculated as `(list_price - unit_cost) / list_price * 100`.

All database values are queried from SQLite; the tools do not invent or send customer/vendor communications. Inside the project virtual environment, install the dependency with:

Payment and purchase preparation plus approval/rejection serialize their pending-file read/check/write through an exclusive `fcntl.flock` lock beside the pending-request file. Approval uses `BEGIN IMMEDIATE`, conditionally debits cash only when the balance covers the amount, and commits the payment and linked obligation update in one database transaction; the pending request is marked used under the same file lock and restored if the transaction fails. Failed checks roll back; balances cannot be overdrawn. Status changes are backend-only, and request records carry the active session id.

```bash
pip install -r requirements.txt
```
