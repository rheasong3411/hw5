"""Explicit human-only payment approval; agents cannot import or invoke this workflow."""
import asyncio
import json
import sys
from uuid import uuid4
from pathlib import Path
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from .config import PROJECT_ROOT
from .audit import event

PENDING = Path(__file__).resolve().parent.parent / "output" / "pending_approvals.json"

async def main() -> None:
    run_id = str(uuid4())
    records = json.loads(PENDING.read_text()) if PENDING.exists() else []
    pending = [r for r in records if r.get("status") == "pending"]
    if not pending:
        print("No pending payment requests.")
        return
    for request in pending:
        print(json.dumps(request, indent=2))
    request_id = input("Request id to approve (blank cancels): ").strip()
    if not request_id:
        event(run_id, 1, "accounting", "human_approval_attempt", None, {"request": None, "approver": None, "decision": "cancelled"}, "cancelled")
        return
    shown = next((r for r in pending if r.get("request_id") == request_id), {"request_id": request_id})
    approver = input("Your name (human approver): ").strip()
    if input("Type APPROVE to confirm: ").strip() != "APPROVE":
        event(run_id, 1, "accounting", "human_approval_attempt", None, {"request": shown, "approver": approver, "decision": "cancelled"}, "cancelled")
        print("Cancelled.")
        return
    event(run_id, 1, "accounting", "human_approval_attempt", None, {"request": shown, "approver": approver, "decision": "approved"})
    async with Client(StdioTransport(command=sys.executable, args=[str(PROJECT_ROOT / "mcp_server" / "server.py")])) as client:
        result = await client.call_tool("execute_approved_payment", {"request_id": request_id, "approved_by": approver})
    event(run_id, 2, "accounting", "human_approval_execution_result", None, {"request": shown, "approver": approver, "result": str(result)})
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
