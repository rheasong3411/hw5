"""MCP tools for the Campus Customs agent team.

All shop facts and mutations go through this server; agents never open SQLite directly.
"""

from pathlib import Path
import sqlite3
import json
from uuid import uuid4
from typing import Any
from datetime import date, datetime, timezone
from contextlib import contextmanager
import fcntl
import os

from fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_DB", PROJECT_ROOT / "data" / "campus_customs_new.db"))
PENDING_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_PENDING", PROJECT_ROOT / "output" / "pending_approvals.json"))
DECISIONS_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_DECISIONS", PROJECT_ROOT / "output" / "pending_decisions.json"))
LOCK_PATH = PENDING_PATH.with_name(PENDING_PATH.name + ".lock")

mcp = FastMCP(
    "Campus Customs MCP",
    instructions="Controlled read and write access to the Campus Customs working database; all payment execution is guarded for humans.",
)


def _query(sql: str, parameters: tuple[Any, ...]) -> list[dict[str, Any]]:
    """Run a parameterized read query against the working database."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, parameters).fetchall()]


def _shop_date() -> str:
    """Return the database-defined current date, never the system clock."""
    rows = _query("SELECT date_today FROM desk LIMIT 1", ())
    if not rows:
        raise RuntimeError("desk.date_today is missing")
    return rows[0]["date_today"]


def _message(messages: list[str]) -> str | None:
    return "; ".join(messages) if messages else None

def _pending() -> list[dict[str, Any]]:
    if not PENDING_PATH.exists():
        return []
    try:
        return json.loads(PENDING_PATH.read_text())
    except json.JSONDecodeError:
        return []

def _save_pending(records: list[dict[str, Any]]) -> None:
    PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = PENDING_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(records, indent=2) + "\n")
    temporary.replace(PENDING_PATH)

def _session_id() -> str:
    session_path = Path(os.environ.get("CAMPUS_CUSTOMS_SESSION", PENDING_PATH.parent / "session.json"))
    if session_path.exists():
        try:
            return str(json.loads(session_path.read_text())["session_id"])
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session = {"session_id": str(uuid4())}
    try:
        with session_path.open("x") as session_file:
            json.dump(session, session_file)
    except FileExistsError:
        return str(json.loads(session_path.read_text())["session_id"])
    return session["session_id"]

@contextmanager
def _pending_lock():
    lock_path = PENDING_PATH.with_name(PENDING_PATH.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

def _decisions() -> list[dict[str, Any]]:
    if not DECISIONS_PATH.exists(): return []
    try: return json.loads(DECISIONS_PATH.read_text())
    except json.JSONDecodeError: return []

@contextmanager
def _decision_lock():
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DECISIONS_PATH.with_name(DECISIONS_PATH.name + ".lock").open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

def _save_decisions(records: list[dict[str, Any]]) -> None:
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = DECISIONS_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(records, indent=2) + "\n")
    temporary.replace(DECISIONS_PATH)

def _execute(sql: str, parameters: tuple[Any, ...]) -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(sql, parameters)
        connection.commit()

@mcp.tool
def list_open_tickets() -> list[dict[str, Any]]:
    """List the tickets currently needing work."""
    return _query("SELECT * FROM tickets WHERE status = 'open' ORDER BY id", ())

@mcp.tool
def list_tickets() -> list[dict[str, Any]]:
    """Return the ticket board, including each ticket's current status."""
    return _query("SELECT id, type, requester, subject, status FROM tickets ORDER BY id", ())

@mcp.tool
def set_ticket_status(ticket_id: int, status: str, note: str = "") -> dict[str, Any]:
    """Set a ticket status after a successful run, preserving a concise board note."""
    if status not in {"open", "awaiting_approval", "awaiting_decision", "resolved"}:
        return {"updated": False, "message": "Ticket status must be open, awaiting_approval, awaiting_decision, or resolved."}
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute("SELECT id, notes FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if not row:
            return {"updated": False, "message": "Ticket not found."}
        notes = row[1] or ""
        if note:
            notes += ("\n" if notes else "") + f"[{_shop_date()}] System: {note}"
        connection.execute("UPDATE tickets SET status=?, notes=? WHERE id=?", (status, notes, ticket_id))
        connection.commit()
    return {"updated": True, "ticket_id": ticket_id, "status": status}

@mcp.tool
def get_cash_balance(account: str = "checking") -> dict[str, Any]:
    """Return the current balance for a cash account."""
    rows = _query("SELECT name, balance, date FROM cash_accounts WHERE name=?", (account,))
    return rows[0] if rows else {"found": False, "message": "Cash account does not exist."}

@mcp.tool
def list_pending_requests(ticket_id: int | None = None) -> list[dict[str, Any]]:
    """Read pending human approval requests so agents can avoid duplicates."""
    records = [record for record in _pending() if record.get("status") == "pending"]
    if ticket_id is not None:
        records = [record for record in records if record.get("ticket_id") == ticket_id]
    return records

@mcp.tool
def list_requests(ticket_id: int | None = None) -> list[dict[str, Any]]:
    """Read every payment or purchase request and its decision state."""
    records = _pending()
    if ticket_id is not None:
        records = [record for record in records if record.get("ticket_id") == ticket_id]
    return records

@mcp.tool
def request_human_decision(ticket_id: int, kind: str, question: str, recommendation: str, options: list[str]) -> dict[str, Any]:
    """Record a human decision request without changing ticket status."""
    if kind not in {"discount", "fulfillment", "other"}: return {"requested": False, "message": "kind must be discount, fulfillment, or other."}
    if not question.strip() or not recommendation.strip() or not options or any(not x.strip() for x in options): return {"requested": False, "message": "Question, recommendation, and non-empty options are required."}
    with _decision_lock():
        records = _decisions()
        duplicate = next((d for d in records if d.get("ticket_id") == ticket_id and d.get("kind") == kind and d.get("status") == "pending"), None)
        if duplicate: return {"requested": False, "duplicate": True, "decision_id": duplicate["decision_id"], "message": "A pending decision already exists for this ticket and kind."}
        decision = {"decision_id": str(uuid4()), "ticket_id": ticket_id, "kind": kind, "question": question, "recommendation": recommendation, "options": options, "created_at": datetime.now(timezone.utc).isoformat(), "requested_by": os.environ.get("CAMPUS_CUSTOMS_AGENT", "agent"), "session_id": _session_id(), "status": "pending"}
        records.append(decision); _save_decisions(records)
        return {"requested": True, **decision}

@mcp.tool
def list_decisions(ticket_id: int | None = None, status: str | None = None) -> list[dict[str, Any]]:
    """Read decision requests and outcomes, optionally filtered."""
    records = _decisions()
    if ticket_id is not None: records = [d for d in records if d.get("ticket_id") == ticket_id]
    if status is not None: records = [d for d in records if d.get("status") == status]
    return records

@mcp.tool
def record_human_decision(decision_id: str, decided_by: str, choice: str, terms: str) -> dict[str, Any]:
    """Human-only: record the actual choice and terms for a pending decision."""
    with _decision_lock():
        records = _decisions(); decision = next((d for d in records if d.get("decision_id") == decision_id), None)
        if not decision or decision.get("status") != "pending": return {"decided": False, "message": "Unknown or already-decided decision id."}
        if not decided_by.strip(): return {"decided": False, "message": "A human decision maker name is required."}
        if choice not in decision.get("options", []) and choice != "custom": return {"decided": False, "message": "Choice must be one of the listed options or 'custom'."}
        decision.update(status="decided", decided_by=decided_by.strip(), choice=choice, terms=terms, decided_at=datetime.now(timezone.utc).isoformat())
        _save_decisions(records)
        return {"decided": True, **decision}

@mcp.tool
def list_payments() -> list[dict[str, Any]]:
    """Read completed payment rows from the payments ledger."""
    return _query("SELECT * FROM payments ORDER BY id", ())

@mcp.tool
def find_restock_vendors(sku: str) -> list[dict[str, Any]]:
    """Match a product to vendor specialties or SKU-bearing invoice descriptions."""
    products = _query("SELECT sku, name FROM inventory WHERE sku=? UNION SELECT sku, sku FROM pricing WHERE sku=?", (sku, sku))
    if not products:
        return [{"found": False, "sku": sku, "message": "No product row exists for this SKU."}]
    product = products[0]
    words = set((product["name"] + " " + product["sku"]).lower().replace("-", " ").split())
    category = "mugs" if "mug" in words else "apparel" if words & {"tee", "shirt", "hoodie", "hat", "apparel"} else None
    matches = []
    for vendor in _query("SELECT * FROM vendors", ()):
        specialty = vendor["specialty"].lower()
        invoices = _query("SELECT * FROM invoices WHERE vendor_id=?", (vendor["id"],))
        reasons = []
        if category and category in specialty:
            reasons.append(f"product category '{category}' matches vendors.specialty")
        if any(word in specialty for word in words if len(word) >= 4):
            reasons.append("product name/SKU keyword matches vendors.specialty")
        if any(sku.lower() in (inv.get("description") or "").lower() for inv in invoices):
            reasons.append("invoice description mentions SKU")
        if reasons:
            matches.append({"vendor": vendor, "match_reason": "; ".join(reasons), "lead_days": vendor["lead_days"], "shipping_blocked": any(inv["status"] == "open" for inv in invoices)})
    return matches or [{"found": False, "sku": sku, "message": "No database-backed vendor match found."}]

@mcp.tool
def prepare_payment(kind: str, ref_id: int, amount: float, account: str = "checking", ticket_id: int | None = None) -> dict[str, Any]:
    """Prepare only an invoice or rent payment request; execution is human-only."""
    if amount <= 0:
        return {"prepared": False, "message": "Payment amount must be positive."}
    with _pending_lock():
        cash = _query("SELECT * FROM cash_accounts WHERE name=?", (account,))
        if not cash:
            return {"prepared": False, "message": "Cash account does not exist."}
        if kind == "invoice":
            obligations = _query("SELECT id, amount FROM invoices WHERE id=? AND status='open'", (ref_id,))
        elif kind == "rent":
            obligations = _query("SELECT id, monthly_rent AS amount FROM leases WHERE id=?", (ref_id,))
        else:
            return {"prepared": False, "message": "Payment kind must be 'invoice' or 'rent'."}
        if not obligations:
            return {"prepared": False, "message": f"No valid open {kind} obligation exists for ref_id {ref_id}."}
        if float(obligations[0]["amount"]) != float(amount):
            return {"prepared": False, "message": "Payment amount does not match the database obligation."}
        records = _pending()
        duplicate = next((record for record in records if record.get("status") == "pending" and record.get("kind") == kind and record.get("ref_id") == ref_id), None)
        if duplicate:
            return {"prepared": False, "duplicate": True, "request_id": duplicate["request_id"], "message": "A pending request already exists for this obligation."}
        request = {"request_id": str(uuid4()), "kind": kind, "ref_id": ref_id, "amount": amount, "account": account, "ticket_id": ticket_id, "session_id": _session_id(), "status": "pending", "available_cash_at_request": cash[0]["balance"]}
        records.append(request)
        _save_pending(records)
        return {"prepared": True, **request, "account": account, "available_cash": cash[0]["balance"], "requires_human_approval": True}

@mcp.tool
def prepare_purchase_order(sku: str, size: str, qty: int, vendor_id: int, account: str = "checking", ticket_id: int | None = None) -> dict[str, Any]:
    """Prepare a vendor purchase order; it records a pending request only."""
    if qty <= 0:
        return {"prepared": False, "message": "Quantity must be positive."}
    with _pending_lock():
        return _prepare_purchase_order_locked(sku, size, qty, vendor_id, account, ticket_id)

def _prepare_purchase_order_locked(sku: str, size: str, qty: int, vendor_id: int, account: str, ticket_id: int | None) -> dict[str, Any]:
    product = _query("SELECT i.sku, i.size, p.unit_cost FROM inventory i JOIN pricing p ON p.sku=i.sku WHERE i.sku=? AND i.size=?", (sku, size))
    vendor = _query("SELECT * FROM vendors WHERE id=?", (vendor_id,))
    if not product or not vendor:
        return {"prepared": False, "message": "Unknown product, size, or vendor."}
    matches = find_restock_vendors(sku)
    match = next((m for m in matches if m.get("vendor", {}).get("id") == vendor_id), None)
    if not match:
        return {"prepared": False, "message": "Vendor does not match this product."}
    open_invoice = _query("SELECT id FROM invoices WHERE vendor_id=? AND status='open' LIMIT 1", (vendor_id,))
    if open_invoice:
        return {"prepared": False, "message": "Vendor has an open unpaid invoice and will not ship."}
    cash = _query("SELECT balance FROM cash_accounts WHERE name=?", (account,))
    if not cash:
        return {"prepared": False, "message": "Cash account does not exist."}
    amount = float(product[0]["unit_cost"]) * qty
    arrival = _query("SELECT date(?, '+' || ? || ' days') AS expected_arrival FROM desk", (_shop_date(), vendor[0]["lead_days"]))[0]["expected_arrival"]
    records = _pending()
    duplicate = next((record for record in records if record.get("status") == "pending" and record.get("kind") == "purchase_order" and record.get("sku") == sku and record.get("size") == size and record.get("vendor_id") == vendor_id), None)
    if duplicate:
        return {"prepared": False, "duplicate": True, "request_id": duplicate["request_id"], "message": "A pending request already exists for this purchase order."}
    request = {"request_id": str(uuid4()), "kind": "purchase_order", "sku": sku, "size": size, "vendor_id": vendor_id, "amount": amount, "account": account, "ticket_id": ticket_id, "session_id": _session_id(), "expected_arrival": arrival, "status": "pending", "available_cash_at_request": cash[0]["balance"]}
    records.append(request); _save_pending(records)
    return {"prepared": True, **request, "requires_human_approval": True}

@mcp.tool
def execute_approved_payment(request_id: str, approved_by: str) -> dict[str, Any]:
    """Execute a pending request after a human confirms; filtered from all agent toolsets."""
    with _pending_lock():
        records = _pending()
        request = next((r for r in records if r["request_id"] == request_id), None)
        if not request or request["status"] != "pending":
            return {"paid": False, "message": "Unknown or already-used payment request id."}
        if not approved_by.strip():
            return {"paid": False, "message": "A human approver name is required."}
        kind, amount, account = request["kind"], float(request["amount"]), request["account"]
        ref_id = request.get("ref_id")
        old_records = json.loads(json.dumps(records))
        with sqlite3.connect(DATABASE_PATH, timeout=30, isolation_level=None) as connection:
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("BEGIN IMMEDIATE")
                if amount <= 0:
                    connection.rollback()
                    return {"paid": False, "message": "Payment amount must be positive."}
                if kind == "purchase_order":
                    product = connection.execute("SELECT unit_cost FROM pricing WHERE sku=?", (request["sku"],)).fetchone()
                    vendor = connection.execute("SELECT * FROM vendors WHERE id=?", (request["vendor_id"],)).fetchone()
                    if not product or not vendor:
                        connection.rollback()
                        return {"paid": False, "message": "Purchase order product or vendor no longer exists."}
                    if not any(m.get("vendor", {}).get("id") == request["vendor_id"] for m in find_restock_vendors(request["sku"])):
                        connection.rollback()
                        return {"paid": False, "message": "Purchase order vendor no longer matches the product."}
                    if connection.execute("SELECT 1 FROM invoices WHERE vendor_id=? AND status='open' LIMIT 1", (request["vendor_id"],)).fetchone():
                        connection.rollback()
                        return {"paid": False, "message": "Vendor has an open unpaid invoice and will not ship."}
                    if float(product["unit_cost"]) * request["qty"] != amount:
                        connection.rollback()
                        return {"paid": False, "message": "Purchase order amount no longer matches unit cost times quantity."}
                    ref_id = request["vendor_id"]
                elif kind == "invoice":
                    obligation = connection.execute("SELECT amount FROM invoices WHERE id=? AND status='open'", (ref_id,)).fetchone()
                    if not obligation or float(obligation["amount"]) != amount:
                        connection.rollback()
                        return {"paid": False, "message": "Payment does not match an open database obligation."}
                elif kind == "rent":
                    obligation = connection.execute("SELECT monthly_rent AS amount FROM leases WHERE id=?", (ref_id,)).fetchone()
                    if not obligation or float(obligation["amount"]) != amount:
                        connection.rollback()
                        return {"paid": False, "message": "Payment does not match a database obligation."}
                else:
                    connection.rollback()
                    return {"paid": False, "message": "Payment kind must be invoice, rent, or purchase_order."}
                debit = connection.execute("UPDATE cash_accounts SET balance=balance-?, date=? WHERE name=? AND balance>=?", (amount, _shop_date(), account, amount))
                if debit.rowcount != 1:
                    connection.rollback()
                    return {"paid": False, "message": "Payment refused: missing account or insufficient cash."}
                connection.execute("INSERT INTO payments(kind, ref_id, amount, account, paid_at, approved_by) VALUES(?,?,?,?,?,?)", (kind, ref_id, amount, account, _shop_date(), approved_by.strip()))
                if kind == "invoice":
                    updated = connection.execute("UPDATE invoices SET status='paid' WHERE id=? AND status='open'", (request["ref_id"],))
                    if updated.rowcount != 1:
                        raise RuntimeError("Invoice was no longer open.")
                elif kind == "rent":
                    updated = connection.execute("UPDATE leases SET next_due=date(next_due, '+1 month') WHERE id=?", (ref_id,))
                    if updated.rowcount != 1:
                        raise RuntimeError("Lease no longer exists.")
                request["status"] = "used"
                request["approved_by"] = approved_by.strip()
                remaining_cash = connection.execute(
                    "SELECT balance FROM cash_accounts WHERE name=?", (account,)
                ).fetchone()["balance"]
                _save_pending(records)
                try:
                    connection.commit()
                except Exception:
                    _save_pending(old_records)
                    raise
                result = {"paid": True, "request_id": request_id, "kind": kind, "ref_id": ref_id, "amount": amount, "remaining_cash": remaining_cash}
                if kind == "purchase_order":
                    result["expected_arrival"] = request["expected_arrival"]
                return result
            except Exception as exc:
                connection.rollback()
                if _pending() != old_records:
                    _save_pending(old_records)
                return {"paid": False, "message": f"Payment transaction rolled back: {exc}"}

@mcp.tool
def reject_payment_request(request_id: str, rejected_by: str) -> dict[str, Any]:
    """Reject a pending payment or purchase request without changing cash."""
    with _pending_lock():
        records = _pending()
        request = next((record for record in records if record.get("request_id") == request_id), None)
        if not request or request.get("status") != "pending":
            return {"rejected": False, "message": "Unknown or already-used payment request id."}
        if not rejected_by.strip():
            return {"rejected": False, "message": "A human rejector name is required."}
        request["status"] = "rejected"
        request["rejected_by"] = rejected_by.strip()
        _save_pending(records)
        return {"rejected": True, "request_id": request_id, "rejected_by": rejected_by.strip()}

@mcp.tool
def append_ticket_note(ticket_id: int, agent: str, note: str) -> dict[str, Any]:
    """Append a draft/review note to the ticket board; never sends communications."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute("SELECT notes FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        if not row:
            return {"updated": False, "message": "Ticket not found."}
        prefix = f"[{_shop_date()}] {agent}: "
        notes = (row[0] or "") + ("\n" if row[0] else "") + prefix + note
        connection.execute("UPDATE tickets SET notes=? WHERE id=?", (notes, ticket_id))
        status = connection.execute("SELECT status FROM tickets WHERE id=?", (ticket_id,)).fetchone()[0]
        return {"updated": True, "ticket_id": ticket_id, "draft_only": True, "status": status}


@mcp.tool
def inspect_customer_order(ticket_id: int) -> dict[str, Any]:
    """Inspect a customer-order ticket, its requested item, stock, and linked invoice."""
    tickets = _query("SELECT * FROM tickets WHERE id = ? AND type = 'customer_order'", (ticket_id,))
    if not tickets:
        return {
            "found": False, "ticket_id": ticket_id,
            "message": "No customer_order ticket exists for this ticket_id.",
        }

    ticket = tickets[0]
    inventory = _query(
        "SELECT * FROM inventory WHERE sku = ? AND size = ?",
        (ticket["sku"], ticket["size"]),
    )
    invoices = _query("SELECT * FROM invoices WHERE id = ?", (ticket["invoice_id"],))
    vendor = []
    if invoices:
        vendor = _query("SELECT * FROM vendors WHERE id = ?", (invoices[0]["vendor_id"],))
    messages = []
    on_hand = inventory[0]["qty"] if inventory else None
    if not inventory:
        messages.append(f"No inventory row exists for sku {ticket['sku']} and size {ticket['size']}.")
    requested_qty = ticket["qty"] or 0
    invoice = invoices[0] if invoices else None
    overdue_days = None
    invoice_overdue = None
    if invoice and invoice["status"] == "open":
        overdue_days = max(
            0,
            int(_query(
                "SELECT CAST(julianday(?) - julianday(?) AS INTEGER) AS days",
                (_shop_date(), invoice["due_date"]),
            )[0]["days"]),
        )
        invoice_overdue = overdue_days > 0
    vendor_record = vendor[0] if vendor else None
    if not invoice:
        messages.append(f"No invoice row exists for linked invoice_id {ticket['invoice_id']}.")
    elif not vendor_record:
        messages.append(f"No vendor row exists for vendor_id {invoice['vendor_id']}.")
    shipping_blocked = None if not vendor_record else bool(
        _query(
            "SELECT 1 FROM invoices WHERE vendor_id = ? AND status = 'open' LIMIT 1",
            (vendor_record["id"],),
        )
    )
    result = {
        "found": True, "ticket_id": ticket_id, "shop_today": _shop_date(),
        "ticket": ticket,
        "inventory": inventory,
        "invoice": invoice,
        "vendor": vendor_record,
        "shortfall": None if on_hand is None else max(0, requested_qty - on_hand),
        "invoice_overdue": invoice_overdue,
        "invoice_overdue_days": overdue_days,
        "shipping_blocked": shipping_blocked,
    }
    if messages:
        result["message"] = _message(messages)
    return result


@mcp.tool
def inspect_rent_notice(ticket_id: int) -> dict[str, Any]:
    """Inspect a rent-notice ticket, its lease, and the current cash account."""
    tickets = _query("SELECT * FROM tickets WHERE id = ? AND type = 'rent_notice'", (ticket_id,))
    if not tickets:
        return {
            "found": False, "ticket_id": ticket_id,
            "message": "No rent_notice ticket exists for this ticket_id.",
        }

    ticket = tickets[0]
    leases = _query("SELECT * FROM leases WHERE id = ?", (ticket["lease_id"],))
    cash_accounts = _query("SELECT * FROM cash_accounts", ())
    lease = leases[0] if leases else None
    checking = next((account for account in cash_accounts if account["name"] == "checking"), None)
    days_until_due = None
    messages = []
    checking_covers_rent = None
    if not lease:
        messages.append(f"No lease row exists for linked lease_id {ticket['lease_id']}.")
    if lease:
        days_until_due = int(_query(
            "SELECT CAST(julianday(?) - julianday(?) AS INTEGER) AS days",
            (lease["next_due"], _shop_date()),
        )[0]["days"])
        if checking:
            checking_covers_rent = checking["balance"] >= lease["monthly_rent"]
        else:
            messages.append("No checking cash_accounts row exists.")
    result = {
        "found": True, "ticket_id": ticket_id, "shop_today": _shop_date(),
        "ticket": ticket,
        "lease": lease,
        "cash_accounts": cash_accounts,
        "days_until_due": days_until_due,
        "checking_covers_rent": checking_covers_rent,
    }
    if messages:
        result["message"] = _message(messages)
    return result


@mcp.tool
def inspect_price_override(ticket_id: int) -> dict[str, Any]:
    """Inspect a price-override ticket, requested stock, and product pricing."""
    tickets = _query("SELECT * FROM tickets WHERE id = ? AND type = 'price_override'", (ticket_id,))
    if not tickets:
        return {
            "found": False, "ticket_id": ticket_id,
            "message": "No price_override ticket exists for this ticket_id.",
        }

    ticket = tickets[0]
    inventory = _query(
        "SELECT * FROM inventory WHERE sku = ? AND size = ?",
        (ticket["sku"], ticket["size"]),
    )
    pricing = _query("SELECT * FROM pricing WHERE sku = ?", (ticket["sku"],))
    price = pricing[0] if pricing else None
    messages = []
    on_hand = inventory[0]["qty"] if inventory else None
    if not inventory:
        messages.append(f"No inventory row exists for sku {ticket['sku']} and size {ticket['size']}.")
    requested_qty = ticket["qty"] or 0
    margin_per_unit = None
    margin_percent = None
    if price:
        margin_per_unit = price["list_price"] - price["unit_cost"]
        if price["list_price"]:
            margin_percent = margin_per_unit / price["list_price"] * 100
    else:
        messages.append(f"No pricing row exists for sku {ticket['sku']}.")
    result = {
        "found": True, "ticket_id": ticket_id, "shop_today": _shop_date(),
        "ticket": ticket,
        "inventory": inventory,
        "pricing": price,
        "shortfall": None if on_hand is None else max(0, requested_qty - on_hand),
        "margin_per_unit": margin_per_unit,
        "margin_percent": margin_percent,
    }
    if messages:
        result["message"] = _message(messages)
    return result


if __name__ == "__main__":
    mcp.run()
