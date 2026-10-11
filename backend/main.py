"""FastAPI routes and human-side ticket lifecycle management."""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.agents import RunStoppedError, run_ticket
from backend.audit import current_session_id, event

SESSION_PATH = ROOT / "output" / "session.json"
RUNS: dict[str, dict[str, Any]] = {}
RUN_TASKS: dict[str, asyncio.Task] = {}
RUN_LOCK = asyncio.Lock()

app = FastAPI(title="Campus Customs Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def mcp_call(name: str, args: dict[str, Any] | None = None):
    try:
        async with Client(
            StdioTransport(
                command=sys.executable,
                args=[str(ROOT / "mcp_server" / "server.py")],
            )
        ) as client:
            result = await client.call_tool(name, args or {})
            if hasattr(result, "data") and result.data is not None:
                return result.data
            return result
    except Exception as exc:
        raise HTTPException(
            502, {"error": "MCP call failed", "tool": name, "detail": str(exc)}
        ) from exc


class Approval(BaseModel):
    request_id: str
    approved_by: str = Field(min_length=1)
    approve: bool


class Rejection(BaseModel):
    approved_by: str = Field(min_length=1)


def _read_audit() -> list[dict[str, Any]]:
    path = ROOT / "output" / "audit_trail.json"
    return json.loads(path.read_text()) if path.exists() else []


def _session_matches(record: dict[str, Any], session_id: str, all_sessions: bool) -> bool:
    return all_sessions or record.get("session_id", "legacy") == session_id


def _audit_runs(session_id: str | None = None, all_sessions: bool = False) -> dict[str, dict[str, Any]]:
    session_id = session_id or current_session_id()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in _read_audit():
        run_id = record.get("run_id")
        if (
            run_id
            and run_id not in {"reset", "human-approval"}
            and _session_matches(record, session_id, all_sessions)
        ):
            grouped.setdefault(run_id, []).append(record)

    rebuilt: dict[str, dict[str, Any]] = {}
    for run_id, run_records in grouped.items():
        start = next(
            (record for record in run_records if record.get("action") == "backend_run_started"),
            None,
        )
        if not start or start.get("ticket_id") is None:
            continue
        final = next(
            (
                record
                for record in reversed(run_records)
                if record.get("action") == "final_output"
                and record.get("agent") == "boss"
            ),
            None,
        )
        stopped = any(
            record.get("action") in {"run_stopped", "usage_limit_exceeded"}
            or record.get("outcome") in {"stopped", "usage_limit_exceeded"}
            for record in run_records
        )
        resolved_event = any(record.get("action") == "ticket_resolved" for record in run_records)
        final_text = str((final or {}).get("detail", {}).get("result", "")) if final else ""
        status = (
            "stopped"
            if stopped
            else "completed"
            if resolved_event or final
            else "error"
            if any(record.get("action") in {"run_error", "loop_error"} for record in run_records)
            else "unknown"
        )
        rebuilt[run_id] = {
            "run_id": run_id,
            "ticket_id": start["ticket_id"],
            "session_id": start.get("session_id", "legacy"),
            "status": status,
            "answer": final_text or None,
        }
    return rebuilt


async def change_ticket_status(ticket_id: int, status: str, reason: str, run_id: str):
    tickets = await mcp_call("list_tickets")
    old = next((ticket.get("status") for ticket in tickets if ticket.get("id") == ticket_id), None)
    if old == status:
        return {"changed": False, "status": status}
    result = await mcp_call(
        "set_ticket_status",
        {"ticket_id": ticket_id, "status": status, "note": reason},
    )
    if not isinstance(result, dict) or not result.get("updated"):
        raise RuntimeError(f"Could not set ticket {ticket_id} to {status}: {result}")
    event(
        run_id,
        900,
        "system",
        "ticket_status_changed",
        ticket_id,
        {"from": old, "to": status, "reason": reason},
        session_id=RUNS.get(run_id, {}).get("session_id", current_session_id()),
    )
    return {"changed": True, "from": old, "status": status, "reason": reason}


async def re_evaluate_ticket(ticket_id: int, run: dict[str, Any] | None = None):
    """Resolve only after the latest current-session run, requests, and required dispositions are complete."""
    current_id = current_session_id()
    if run is None:
        candidates = [item for item in _audit_runs(current_id).values() if item["ticket_id"] == ticket_id]
        run = candidates[-1] if candidates else None
    if not run or run.get("status") != "completed":
        return None
    requests = [r for r in await mcp_call("list_requests", {"ticket_id": ticket_id}) if r.get("session_id", "legacy") == current_id]
    pending_payments = [r for r in requests if r.get("status") == "pending"]
    decisions = [d for d in await mcp_call("list_decisions", {"ticket_id": ticket_id}) if d.get("session_id", "legacy") == current_id]
    pending_decisions = [d for d in decisions if d.get("status") == "pending"]
    tickets = await mcp_call("list_tickets")
    ticket = next((t for t in tickets if t.get("id") == ticket_id), {})
    outstanding = []
    if pending_payments: outstanding.append(f"{len(pending_payments)} payment/purchase request(s) pending")
    if pending_decisions: outstanding.append(f"{len(pending_decisions)} human decision(s) pending")
    required_kind = None
    if ticket.get("type") == "price_override": required_kind = "discount"
    elif ticket.get("type") == "rent_notice":
        rent_requests = [r for r in requests if r.get("kind") == "rent"]
        if not rent_requests:
            outstanding.append("no rent payment request prepared; human must decide")
        elif any(r.get("status") == "pending" for r in rent_requests):
            outstanding.append("rent payment request pending")
    elif ticket.get("type") == "customer_order":
        inspected = await mcp_call("inspect_customer_order", {"ticket_id": ticket_id})
        if (inspected.get("shortfall") or 0) > 0: required_kind = "fulfillment"
    if required_kind and not any(d.get("kind") == required_kind and d.get("status") == "decided" for d in decisions):
        outstanding.append(f"required {required_kind} disposition not decided")
    if outstanding:
        status = "awaiting_approval" if pending_payments else "awaiting_decision"
        reason = "no rent payment request prepared; human must decide" if "no rent payment request prepared; human must decide" in outstanding else "Run complete; outstanding: " + "; ".join(outstanding) + "."
        return await change_ticket_status(ticket_id, status, reason, run["run_id"])
    result = await change_ticket_status(ticket_id, "resolved", "Run complete; all requests and required dispositions are decided.", run["run_id"])
    event("human-decision", 900, "system", "final_disposition", ticket_id, {
        "payments_decided": [r for r in requests if r.get("status") != "pending"],
        "decisions_decided": [d for d in decisions if d.get("status") == "decided"],
    }, session_id=current_id)
    return result


async def finish_run_status(run_id: str, ticket_id: int, answer: str):
    RUNS[run_id]["status"] = "completed"
    await re_evaluate_ticket(ticket_id, RUNS[run_id])


async def do_run(run_id: str, ticket_id: int, session_id: str):
    RUNS[run_id]["status"] = "running"
    try:
        answer = await run_ticket(
            ticket_id,
            run_id=run_id,
            session_id=session_id,
        )
        RUNS[run_id]["answer"] = answer
        await finish_run_status(run_id, ticket_id, answer)
    except RunStoppedError as exc:
        event(run_id, 1000, "system", "run_stopped", ticket_id, {"reason": str(exc)}, "limit", session_id)
        RUNS[run_id].update(status="stopped", error=str(exc))
        await change_ticket_status(ticket_id, "open", f"Run stopped: {exc}", run_id)
    except Exception as exc:
        RUNS[run_id].update(status="error", error=str(exc))
        event(run_id, 1001, "system", "run_error", ticket_id, {"reason": str(exc)}, "error", session_id)
    finally:
        RUN_TASKS.pop(run_id, None)


@app.get("/tickets")
async def tickets():
    return await mcp_call("list_tickets")


@app.get("/balance")
async def balance():
    return await mcp_call("get_cash_balance")


@app.get("/pending-approvals")
async def pending_approvals():
    path = Path(os.environ.get("CAMPUS_CUSTOMS_PENDING", ROOT / "output" / "pending_approvals.json"))
    records = json.loads(path.read_text()) if path.exists() else []
    session_id = current_session_id()
    return [
        request
        for request in records
        if request.get("status") == "pending"
        and request.get("session_id", "legacy") == session_id
    ]

@app.get("/decisions")
async def decisions(ticket_id: int | None = Query(None), status: str | None = Query(None), all_sessions: bool = Query(False)):
    records = await mcp_call("list_decisions", {"ticket_id": ticket_id, "status": status})
    if all_sessions: return records
    session_id = current_session_id()
    return [d for d in records if d.get("session_id", "legacy") == session_id]

class HumanDecision(BaseModel):
    decided_by: str = Field(min_length=1)
    choice: str
    terms: str

@app.post("/decisions/{decision_id}")
async def decide_human(decision_id: str, body: HumanDecision):
    before = await mcp_call("list_decisions")
    target = next((d for d in before if d.get("decision_id") == decision_id), None)
    result = await mcp_call("record_human_decision", {"decision_id": decision_id, **body.model_dump()})
    if not isinstance(result, dict) or not result.get("decided"):
        raise HTTPException(400, result.get("message", "Decision refused."))
    event("human-decision", 1, "system", "human_decision", result.get("ticket_id"), result, session_id=current_session_id())
    if target: await re_evaluate_ticket(target["ticket_id"])
    return result


@app.get("/requests")
async def requests(
    ticket_id: int | None = Query(None),
    all_sessions: bool = Query(False),
):
    records = await mcp_call("list_requests", {"ticket_id": ticket_id})
    if all_sessions:
        return records
    session_id = current_session_id()
    return [r for r in records if r.get("session_id", "legacy") == session_id]


@app.get("/payments")
async def payments():
    return await mcp_call("list_payments")


@app.post("/tickets/{ticket_id}/run", status_code=202)
async def start_run(ticket_id: int):
    async with RUN_LOCK:
      session_id = current_session_id()
      if any(run["ticket_id"] == ticket_id and run.get("session_id") == session_id and run["status"] in {"queued", "running"} for run in RUNS.values()):
        raise HTTPException(409, "A run for this ticket is already queued or running.")
      run_id = str(uuid4()).replace("-", "")
      RUNS[run_id] = {
        "run_id": run_id,
        "ticket_id": ticket_id,
        "session_id": session_id,
        "status": "queued",
        "answer": None,
      }
      event(run_id, 1, "boss", "backend_run_started", ticket_id, {}, session_id=session_id)
      RUN_TASKS[run_id] = asyncio.create_task(do_run(run_id, ticket_id, session_id))
    return RUNS[run_id]


@app.get("/runs/{run_id}")
async def run_status(run_id: str, all_sessions: bool = Query(False)):
    if run_id in RUNS and (
        all_sessions or RUNS[run_id].get("session_id") == current_session_id()
    ):
        return RUNS[run_id]
    rebuilt = _audit_runs(all_sessions=all_sessions)
    if run_id not in rebuilt:
        raise HTTPException(404, "Run not found in the current session.")
    return rebuilt[run_id]


@app.get("/runs")
async def latest_runs(all_sessions: bool = Query(False)):
    merged = _audit_runs(all_sessions=all_sessions)
    merged.update(
        {
            run_id: run
            for run_id, run in RUNS.items()
            if all_sessions or run.get("session_id") == current_session_id()
        }
    )
    latest: dict[tuple[str, int], dict[str, Any]] = {}
    for run in merged.values():
        session_id = run.get("session_id", "legacy") if all_sessions else current_session_id()
        latest[(session_id, run["ticket_id"])] = run
    return list(latest.values())


@app.get("/events")
async def events(
    limit: int = Query(50, ge=1, le=500),
    ticket_id: int | None = None,
    run_id: str | None = None,
    all_sessions: bool = Query(False),
):
    session_id = current_session_id()
    records = [
        record
        for record in _read_audit()
        if (ticket_id is None or record.get("ticket_id") == ticket_id)
        and (run_id is None or record.get("run_id") == run_id)
        and _session_matches(record, session_id, all_sessions)
    ]
    output = []
    for record in records[-limit:]:
        detail = record.get("detail", {})
        output.append(
            {
                "id": record.get("event_id", f"{record.get('run_id')}:{record.get('step')}"),
                "time": record.get("timestamp"),
                "run_id": record.get("run_id"),
                "session_id": record.get("session_id", "legacy"),
                "ticket_id": record.get("ticket_id"),
                "agent": record.get("agent"),
                "action": record.get("action"),
                "tool": detail.get("tool_name"),
                "args": detail.get("args"),
                "task": detail.get("task"),
                "from_agent": record.get("agent") if record.get("action") == "delegation_requested" else None,
                "to_agent": detail.get("to_agent"),
                "text": str(detail.get("text", detail.get("content", detail.get("result", detail.get("message", "")))))[:500],
                "usage": detail.get("usage"),
                "returned_model": detail.get("returned_model"),
            }
        )
    return output


async def _record_human_decision(request_id: str, decision: str, actor: str, result: dict[str, Any]):
    path = Path(os.environ.get("CAMPUS_CUSTOMS_PENDING", ROOT / "output" / "pending_approvals.json"))
    requests = json.loads(path.read_text()) if path.exists() else []
    request = next((item for item in requests if item.get("request_id") == request_id), None)
    ticket_id = request.get("ticket_id") if request else None
    event(
        "human-approval",
        1,
        "system",
        f"human_{decision}",
        ticket_id,
        {"request_id": request_id, "actor": actor, "result": result},
        session_id=current_session_id(),
    )
    if ticket_id is not None:
        await re_evaluate_ticket(ticket_id)


@app.post("/approvals")
async def approve(body: Approval):
    if not body.approve:
        raise HTTPException(400, "Approval flag must be true to execute a request.")
    result = await mcp_call(
        "execute_approved_payment",
        {"request_id": body.request_id, "approved_by": body.approved_by},
    )
    if isinstance(result, dict) and not result.get("paid"):
        raise HTTPException(400, result.get("message", "Approval refused."))
    await _record_human_decision(body.request_id, "approval", body.approved_by, result)
    return result


@app.post("/approvals/{request_id}/reject")
async def reject(request_id: str, body: Rejection):
    result = await mcp_call(
        "reject_payment_request",
        {"request_id": request_id, "rejected_by": body.approved_by},
    )
    if isinstance(result, dict) and not result.get("rejected"):
        raise HTTPException(400, result.get("message", "Rejection refused."))
    await _record_human_decision(request_id, "rejection", body.approved_by, result)
    return result


@app.get("/tickets/{ticket_id}/summary")
async def summary(
    ticket_id: int,
    run_id: str | None = None,
    all_sessions: bool = Query(False),
):
    session_id = current_session_id()
    records = [
        record
        for record in _read_audit()
        if record.get("ticket_id") == ticket_id
        and (run_id is None or record.get("run_id") == run_id)
        and _session_matches(record, session_id, all_sessions)
    ]
    run_ids = [
        record.get("run_id")
        for record in records
        if record.get("action") == "backend_run_started"
    ]
    selected = run_id or (run_ids[-1] if run_ids else None)
    records = [record for record in records if record.get("run_id") == selected]
    agents: dict[str, dict[str, Any]] = {}
    run_summary: dict[str, Any] = {}
    for record in records:
        agent = record.get("agent")
        if agent == "system":
            continue
        item = agents.setdefault(
            agent, {"agent": agent, "outcome": "", "run_end_status": "", "full_answer": "", "tools": [], "delegated_to": []}
        )
        detail = record.get("detail", {})
        if record.get("agent") == "boss" and record.get("action") == "final_output":
            run_summary = {
                "delegation_attempts": detail.get("delegation_attempts", 0),
                "delegation_successes": detail.get("delegation_successes", 0),
                "returned_models": detail.get("returned_models", []),
            }
        if record.get("action") == "final_output":
            item["full_answer"] = str(detail.get("result", ""))
        if record.get("action") == "tool_call" and detail.get("tool_name"):
            item["tools"].append(detail["tool_name"])
        if record.get("action") == "delegation_requested" and detail.get("to_agent"):
            item["delegated_to"].append(detail["to_agent"])
    for item in agents.values():
        item["outcome"], item["run_end_status"] = _agent_outcome(item["full_answer"], item["agent"])
    requests = [r for r in await mcp_call("list_requests", {"ticket_id": ticket_id}) if r.get("session_id", "legacy") == session_id]
    decisions = [d for d in await mcp_call("list_decisions", {"ticket_id": ticket_id}) if d.get("session_id", "legacy") == session_id]
    ticket_rows = await mcp_call("list_tickets")
    ticket = next((t for t in ticket_rows if t.get("id") == ticket_id), {})
    remaining = [f"Request {r.get('request_id')} is pending" for r in requests if r.get("status") == "pending"]
    remaining += [f"Decision {d.get('decision_id')} is pending" for d in decisions if d.get("status") == "pending"]
    if "boss" in agents:
        boss = agents["boss"]
        refs = [str(r.get("request_id")) for r in requests if r.get("request_id")]
        refs += [str(d.get("decision_id")) for d in decisions if d.get("decision_id")]
        if refs:
            boss["outcome"] = f"{boss['outcome']} Reported ids: {', '.join(ref[:8] for ref in refs)}."
    status_events = [r for r in _read_audit() if r.get("ticket_id") == ticket_id and r.get("action") == "ticket_status_changed" and _session_matches(r, session_id, all_sessions)]
    final_status = (status_events[-1].get("detail", {}).get("to") if status_events else ticket.get("status"))
    return {"ticket_id": ticket_id, "run_id": selected, "agents": list(agents.values()), "disposition": {
        "requests": [{"id": r.get("request_id"), "kind": r.get("kind"), "amount": r.get("amount"), "status": r.get("status"), "decided_by": r.get("approved_by") or r.get("rejected_by")} for r in requests],
        "decisions": [{"id": d.get("decision_id"), "kind": d.get("kind"), "choice": d.get("choice"), "terms": d.get("terms"), "decided_by": d.get("decided_by"), "decided_at": d.get("decided_at")} for d in decisions],
        "final_status": final_status, "remaining_actions": remaining}, **run_summary}


def _agent_outcome(answer: str, agent: str) -> tuple[str, str]:
    import re

    lines = answer.splitlines()
    status_lines = [re.sub(r"^\s*(?:[-*+]\s*)?", "", line).strip() for line in lines if re.match(r"^\s*(?:[-*+]\s*)?STATUS\s*:", line, re.I)]
    status_match = re.search(r"STATUS\s*:\s*([\w.-]+)", status_lines[-1], re.I) if status_lines else None
    run_end_status = status_match.group(1) if status_match else ""
    lines = [line for line in lines if not re.match(r"^\s*(?:[-*+]\s*)?STATUS\s*:", line, re.I)]
    text = "\n".join(lines)

    # Markdown headings and standalone bold labels delimit sections. Keep underscores
    # intact because they can be meaningful inside identifiers and status values.
    targets = re.compile(r"\b(recommendation|recommended|decision|outcome|result|findings)\b", re.I)
    heading_re = re.compile(r"(?m)^\s{0,3}(?:#{1,6}\s+[^\n]*|\*\*[^*\n]+\*\*\s*:?[ \t]*|[A-Za-z][^\n:]{0,70}:)[ \t]*$")
    label_re = re.compile(
        r"(?im)^\s{0,3}(?:#{1,6}\s*)?(?:\*\*)?(?P<label>[^\n:*]+)(?:\*\*)?\s*:\s*(?P<inline>[^\n]*)$"
    )
    candidates = [
        (m.start(), m.end(), m.group("label"), m.group("inline"))
        for m in label_re.finditer(text)
        if targets.search(m.group("label")) and not m.group("label").lstrip().startswith(("- ", "+ "))
    ]
    bold_inline_re = re.compile(
        r"(?m)^\s{0,3}(?:[-*+]\s+)?\*\*(?P<label>[^*:\n]+):\*\*\s*(?P<inline>[^\n]*)$"
    )
    candidates.extend(
        (m.start(), m.end(), m.group("label"), m.group("inline"))
        for m in bold_inline_re.finditer(text)
        if targets.search(m.group("label"))
    )
    bold_heading_re = re.compile(r"(?m)^\s{0,3}\*\*(?P<label>[^*\n]+)\*\*\s*:?[ \t]*$")
    candidates.extend(
        (m.start(), m.end(), m.group("label").rstrip(":"), "")
        for m in bold_heading_re.finditer(text)
        if targets.search(m.group("label"))
    )
    markdown_heading_re = re.compile(r"(?m)^\s{0,3}#{1,6}\s+(?P<label>[^\n]+)$")
    candidates.extend(
        (m.start(), m.end(), m.group("label"), "")
        for m in markdown_heading_re.finditer(text)
        if targets.search(m.group("label"))
    )
    recommendations = [
        candidate for candidate in candidates
        if re.search(r"\b(recommendation|recommended)\b", candidate[2], re.I)
    ]
    selected = max(recommendations or candidates, key=lambda candidate: candidate[0]) if candidates else None
    section = ""
    if selected:
        _, end, _, inline = selected
        section = (inline + "\n" if inline else "") + text[end:]
        next_heading = heading_re.search(section)
        if next_heading:
            section = section[:next_heading.start()]
    else:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        substantive = [p for p in paragraphs if not all(heading_re.fullmatch(line.strip()) for line in p.splitlines() if line.strip())]
        section = ""
        for paragraph in reversed(substantive):
            first_line = paragraph.splitlines()[0].strip()
            if re.match(r"^(?:\*\*)?[\w /-]{1,70}(?:\*\*)?:\s*$", first_line):
                continue
            cleaned = re.sub(r"`([^`]*)`", r"\1", paragraph)
            cleaned = re.sub(r"\*\*|__|[*#>`~]", "", cleaned)
            cleaned = re.sub(r"(?<!\w)_(?!\w)", "", cleaned)
            cleaned = re.sub(r"(?m)^\s*[-+]\s+", "", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip()
            if re.search(r"[.!?][\"')\]]*$", cleaned):
                section = paragraph
                break

    # Strip markdown punctuation while preserving underscores within words.
    section = re.sub(r"`([^`]*)`", r"\1", section)
    section = re.sub(r"\*\*|__|[*#>`~]", "", section)
    section = re.sub(r"(?<!\w)_(?!\w)", "", section)
    section = re.sub(r"(?m)^\s*[-+]\s+", "", section)
    section = re.sub(r"\s+", " ", section).strip()
    sentences = _split_outcome_sentences(section)
    limit = 4 if selected else 3
    chosen: list[str] = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or not re.search(r"[.!?][\"')\]]*$", sentence):
            continue
        if len(" ".join(chosen + [sentence])) > 450:
            break
        chosen.append(sentence)
        if len(chosen) >= limit:
            break
    if not chosen and selected:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        for paragraph in reversed(paragraphs):
            if all(heading_re.fullmatch(line.strip()) for line in paragraph.splitlines() if line.strip()):
                continue
            if re.match(r"^(?:[-*+]\s+)?\*\*[^*]+:\*\*\s*$", paragraph.splitlines()[0].strip()):
                continue
            fallback = re.sub(r"`([^`]*)`", r"\1", paragraph)
            fallback = re.sub(r"\*\*|__|[*#>`~]", "", fallback)
            fallback = re.sub(r"(?<!\w)_(?!\w)", "", fallback)
            fallback = re.sub(r"(?m)^\s*[-+*]\s+", "", fallback)
            fallback = re.sub(r"\s+", " ", fallback).strip()
            fallback_sentences = _split_outcome_sentences(fallback)
            fallback_chosen = [
                s.strip() for s in fallback_sentences
                if s.strip() and re.search(r"[.!?][\"')\]]*$", s.strip())
            ]
            if fallback_chosen:
                chosen = fallback_chosen[:3]
                break
    return " ".join(chosen), run_end_status


def _split_outcome_sentences(text: str) -> list[str]:
    """Split at sentence punctuation followed by whitespace and a capital."""
    import re

    abbreviations = re.compile(r"(?:\bi\.e|\be\.g|\bco)\.$", re.I)
    boundaries = []
    for match in re.finditer(r"[.!?](?:[\"')\]]*)\s+(?=[A-Z\"'“])", text):
        punctuation = match.start()
        if text[punctuation] == ".":
            before = text[:punctuation + 1]
            if (punctuation > 0 and text[punctuation - 1].isdigit()
                    and punctuation + 1 < len(text) and text[punctuation + 1].isdigit()):
                continue
            if abbreviations.search(before):
                continue
        boundaries.append(match.end())
    return [
        text[start:end].strip()
        for start, end in zip([0] + boundaries, boundaries + [len(text)])
    ]


@app.post("/reset")
async def reset():
    active = list(RUN_TASKS.values())
    for task in active:
        task.cancel()
    if active:
        await asyncio.gather(*active, return_exceptions=True)
    RUN_TASKS.clear()
    RUNS.clear()
    from backend.reset import reset_workspace
    session_id = reset_workspace()
    return {"reset": True, "session_id": session_id}
