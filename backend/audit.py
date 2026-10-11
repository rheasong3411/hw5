"""Append-only execution log for later human review."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from .models import AuditEvent

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
SESSION_PATH = AUDIT_PATH.parent / "session.json"
_lock = Lock()

def current_session_id() -> str:
    """Create and return the active session id without logging credentials or other state."""
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SESSION_PATH.exists():
        try:
            value = json.loads(SESSION_PATH.read_text()).get("session_id")
            if value:
                return str(value)
        except (json.JSONDecodeError, AttributeError):
            pass
    from uuid import uuid4
    value = str(uuid4())
    try:
        with SESSION_PATH.open("x") as session_file:
            json.dump({"session_id": value}, session_file)
        return value
    except FileExistsError:
        return str(json.loads(SESSION_PATH.read_text())["session_id"])

def append_event(event: AuditEvent, session_id: str | None = None) -> None:
    with _lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        records = []
        if AUDIT_PATH.exists():
            try:
                records = json.loads(AUDIT_PATH.read_text())
            except json.JSONDecodeError:
                records = []
        record = event.model_dump(mode="json")
        record["session_id"] = session_id or current_session_id()
        record["event_id"] = f"{event.run_id}:{len(records) + 1}"
        records.append(record)
        AUDIT_PATH.write_text(json.dumps(records, indent=2) + "\n")

def event(run_id: str, step: int, agent: str, action: str, ticket_id: int | None = None, detail=None, outcome="completed", session_id: str | None = None) -> None:
    append_event(AuditEvent(timestamp=datetime.now(timezone.utc), run_id=run_id, step=step, agent=agent, action=action, ticket_id=ticket_id, detail=detail or {}, outcome=outcome), session_id=session_id)
