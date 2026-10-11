# Campus Customs

Campus Customs is a multi-agent operations desk combining an MCP server, FastAPI backend, PydanticAI five-agent team, and React board for a campus merchandise shop. The agents call model `gpt-6-luna` through Portkey's Responses endpoint; the frontend talks only to the backend.

## Clone

```bash
git clone https://github.com/rheasong3411/hw5.git && cd hw5
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
(cd frontend && npm install)
```

Put your `PORTKEY_API_KEY` in `.env`. Never commit `.env`, and never print or share the key.

## 1. Clean run

Copy the untouched original database to the working copy before a fresh run:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

`data/campus_customs.db` is the untouched original seed. `data/campus_customs_new.db` is the working SQLite copy read by MCP and updated by its guarded database tools; approval requests live separately in `output/pending_approvals.json`. The backend reset endpoint performs the same restore and clears pending requests. For isolated tests, MCP accepts `CAMPUS_CUSTOMS_DB`, `CAMPUS_CUSTOMS_PENDING`, and `CAMPUS_CUSTOMS_DECISIONS` environment paths.

## 2. Start the MCP server

The MCP server uses stdio:

```bash
.venv/bin/python mcp_server/server.py
```

The backend and agents launch the MCP server automatically over stdio. A vibe coder can connect to it through `.mcp.json`.

## 3. Start the FastAPI backend

```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```

## 4. Start the React board

In another terminal:

```bash
cd frontend
npm run dev
```

Open <http://localhost:5173>.

## 5. Full three-ticket run

Reset before starting. Either click nothing yet and run:

```bash
curl -X POST http://localhost:8000/reset
```

or perform the clean-copy step above. Confirm the starting checking balance is `$3,400.00` with `GET /balance`. On the board, select tickets 101, 102, and 103 one at a time and click **Start agent team** for each. The team prepares payment receipts and human decision cards but does not execute payments or make those decisions. On the manager's desk, approve/reject receipts and select an option on every decision card; confirm the terms field, which starts with Boss's recommendation. The signed-in name is recorded with the decision. Ticket 101 requires a fulfillment decision, ticket 102 resolves after its rent request is decided, and ticket 103 requires a discount decision even if its purchase request is rejected. Then compare the results against `output/desk_tickets.html`. The decision routes are `GET /decisions` and `POST /decisions/{decision_id}` with `{decided_by, choice, terms}`.

Optional CLI workflow:

```bash
.venv/bin/python -m backend.run_ticket 101
.venv/bin/python -m backend.approve_payment
```

### Submitted final state

The submitted results use final session `57ca3122-cfec-4520-85e8-bbc1b3e053ae`. Problem 9 run IDs are ticket 101 `4dd82f176e0d4f69a0786497643c3982`, ticket 102 `9a9511c4c46345038c1e1878fa1a1b3a`, and ticket 103 `1ce25873405c4f9bb0056a09a0406a53`. Each run used the configured 120,000-token / 60-request budget and shared six-success delegation cap. Ticket 101 resolved after Rhea approved and paid invoice 501 and explicitly deferred the still-unfulfilled tee order, requiring customer-draft review and no delivery-date promise. Ticket 102 resolved after Rhea approved and paid lease 1 rent. For ticket 103, Rhea first rejected the $264 PO; that left the ticket awaiting a discount disposition. It resolved only after Rhea recorded 10% off the 8 in-stock hoodies ($52.20 each, $417.60 total), with no discount or delivery promise for the remaining 12 and draft review before sending. These human decisions are recorded in the audit and decision/approval ledgers. No customer or landlord message was sent and no sale or price update was recorded.

The two payments reconcile from $3,400.00 to $160.00. Rent-first leaves $1,000.00, which covers the $840 invoice and leaves $160.00; invoice-first leaves $2,560.00, which covers $2,400 rent and also leaves $160.00. Either order covers both obligations, though timing affects when Bulldog’s shipping block clears for the later ticket 103 PO. `output/desk_tickets.html`, `output/resolved_tickets.json`, and `output/resolved_board.html` contain the final session write-ups. Resetting replaces the submitted database state with the original seed.

## Tests

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q tests
```

The tests use temporary database copies (never `data/`) and cover concurrent payment approvals (cash can never go negative), `append_ticket_note` being unable to change ticket status, and the shared delegation cap of six successful delegations per run, locked human decisions and type-specific disposition, and duplicate-run rejection.

## Human approval safety

Agents may inspect records and prepare payment and human decision requests, but they cannot execute payments, record human choices, reject requests, resolve tickets, or send communications. Pending payment requests remain visible until a named human approves or rejects them. Pending decision requests remain visible until a named human selects an option and records actual terms. Approval validates the obligation, amount, account, and available cash before writing a payment and updating the linked invoice or lease; rejection records the decision without changing cash. Purchase-order approval records the payment but does not pretend that inventory has already arrived.

The append-only audit trail records session-scoped live agent events, returned model identities, delegations, usage, human decisions, and ticket outcomes. Agents call `gpt-6-luna` through Portkey's Responses endpoint. Concurrent payment approvals are serialized and debit checking only inside a guarded SQLite transaction, so cash cannot become negative. Each run has a shared limit of 60 model requests and 120,000 total tokens, increased to allow for the additional model calls required by the explicit human-decision step; a shared delegation budget also bounds each ticket. The dashboard can rebuild current-session run state from the audit trail after a backend restart.

## Folder map

```text
AI_prompts.md
requirements.txt
.env.example
.gitignore
.mcp.json
README.md
data/
mcp_server/
frontend/
backend/
├── main.py
├── models.py
└── prompts/
    ├── boss.md
    ├── inventory.md
    ├── accounting.md
    ├── facilities.md
    └── customer_service.md
output/
├── harness.md
├── mcp_smoke.json
├── desk_tickets.html
├── resolved_tickets.json
├── resolved_board.html
├── audit_trail.json
├── github_url.txt
├── design.md
└── screenshots/
```

## Problems 1–11

| Problem | Deliverable |
| --- | --- |
| 1 | `AI_prompts.md` — log of the prompts typed per problem, with follow-ups |
| 2 | `output/harness.md` — table/field documentation and the `data/campus_customs_new.db` working copy |
| 3 | `mcp_server/` — initial three tools and MCP README |
| 4 | `.mcp.json` and `output/mcp_smoke.json` |
| 5 | `backend/` agents, prompts, `models.py`, audit trail, and harness safety documentation |
| 6 | Expected sections of `output/desk_tickets.html` |
| 7 | `backend/main.py` API routes |
| 8 | `frontend/` dashboard and `output/design.md` |
| 9 | Actual and Cash tabs, `resolved_tickets.json`, `resolved_board.html`, and `audit_trail.json` |
| 10 | Reflection tab in `output/desk_tickets.html` |
| 11 | This README, `.gitignore`, `.env.example`, and `output/github_url.txt` |
