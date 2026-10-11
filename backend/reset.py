"""Restore the working shop state for a clean run."""
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent


def reset_workspace() -> str:
    original = Path(os.environ.get("CAMPUS_CUSTOMS_ORIGINAL_DB", ROOT / "data" / "campus_customs.db"))
    working = Path(os.environ.get("CAMPUS_CUSTOMS_DB", ROOT / "data" / "campus_customs_new.db"))
    pending = Path(os.environ.get("CAMPUS_CUSTOMS_PENDING", ROOT / "output" / "pending_approvals.json"))
    decisions = Path(os.environ.get("CAMPUS_CUSTOMS_DECISIONS", ROOT / "output" / "pending_decisions.json"))
    session = Path(os.environ.get("CAMPUS_CUSTOMS_SESSION", ROOT / "output" / "session.json"))
    shutil.copy2(original, working)
    for path in (pending, decisions):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[]\n")
    session_id = str(uuid4())
    session.parent.mkdir(parents=True, exist_ok=True)
    session.write_text(json.dumps({"session_id": session_id}) + "\n")
    from backend.audit import event
    event("reset", 1, "system", "database_reset", None, {"session_id": session_id}, session_id=session_id)
    return session_id


if __name__ == "__main__":
    print(json.dumps({"reset": True, "session_id": reset_workspace()}))
