import asyncio
import importlib
import inspect
import json


def server():
    import mcp_server.server as module
    return importlib.reload(module)


def test_decision_tool_validation_and_human_only_filter():
    m = server()
    assert "record_human_decision" not in {"execute_approved_payment"}
    req = m.request_human_decision(103, "discount", "Accept?", "10% off 8 at $52.20, total $417.60", ["accept", "decline"])
    assert req["requested"] and req["requested_by"]
    assert m.request_human_decision(103, "discount", "Again", "Again", ["accept"])["duplicate"]
    assert m.list_decisions(103, "pending")[0]["decision_id"] == req["decision_id"]
    assert not m.record_human_decision(req["decision_id"], "", "accept", "terms")["decided"]
    assert not m.record_human_decision(req["decision_id"], "Rhea", "nope", "terms")["decided"]
    decided = m.record_human_decision(req["decision_id"], "Rhea", "accept", "10% for 8 units")
    assert decided["decided"] and decided["status"] == "decided"
    assert not m.record_human_decision(req["decision_id"], "Rhea", "accept", "backdated")["decided"]
    assert decided["decided_at"] >= req["created_at"]
    from backend.agents import mcp_toolset
    filtered = mcp_toolset()
    assert not filtered.filter_func(None, type("Tool", (), {"name": "record_human_decision"})())
    assert not filtered.filter_func(None, type("Tool", (), {"name": "execute_approved_payment"})())


def test_final_disposition_requires_ticket_type_specific_decisions(monkeypatch):
    import backend.main as main
    main = importlib.reload(main)
    session = main.current_session_id()
    status = {101: "open", 102: "open", 103: "open"}
    requests, decisions = [], []
    async def fake(name, args=None):
        args = args or {}
        tid = args.get("ticket_id")
        if name == "list_requests": return [r for r in requests if r["ticket_id"] == tid]
        if name == "list_decisions": return [d for d in decisions if d["ticket_id"] == tid]
        if name == "list_tickets": return [{"id": i, "status": s, "type": {101:"customer_order",102:"rent_notice",103:"price_override"}[i]} for i,s in status.items()]
        if name == "inspect_customer_order": return {"shortfall": 1}
        if name == "set_ticket_status": status[tid] = args["status"]; return {"updated": True}
        raise AssertionError(name)
    monkeypatch.setattr(main, "mcp_call", fake)
    monkeypatch.setattr(main, "_audit_runs", lambda _sid=None: {"r": {"run_id":"r", "ticket_id":101,"status":"completed"}})
    monkeypatch.setattr(main, "event", lambda *a, **k: None)
    async def go():
        run = {"run_id":"r", "ticket_id":101,"status":"completed"}
        await main.re_evaluate_ticket(101, run); assert status[101] == "awaiting_decision"
        decisions.append({"ticket_id":101,"kind":"fulfillment","status":"decided","session_id":session})
        await main.re_evaluate_ticket(101, run); assert status[101] == "resolved"
        run2 = {"run_id":"r2", "ticket_id":103,"status":"completed"}
        monkeypatch.setattr(main, "_audit_runs", lambda _sid=None: {"r2":run2})
        requests.append({"ticket_id":103,"status":"rejected","session_id":session,"kind":"purchase_order"})
        await main.re_evaluate_ticket(103, run2); assert status[103] == "awaiting_decision"
        decisions.append({"ticket_id":103,"kind":"discount","status":"decided","session_id":session})
        await main.re_evaluate_ticket(103, run2); assert status[103] == "resolved"
        run3 = {"run_id":"r3", "ticket_id":102,"status":"completed"}
        monkeypatch.setattr(main, "_audit_runs", lambda _sid=None: {"r3":run3})
        await main.re_evaluate_ticket(102, run3); assert status[102] == "awaiting_decision"
        requests.append({"ticket_id":102,"status":"used","session_id":session,"kind":"rent"})
        await main.re_evaluate_ticket(102, run3); assert status[102] == "resolved"
    asyncio.run(go())


def test_reset_clears_pending_files_and_starts_new_session(tmp_path, monkeypatch):
    import backend.reset as reset
    import backend.audit as audit
    original, working = tmp_path / "original.db", tmp_path / "working.db"
    pending, decisions, session, audit_path = (tmp_path / n for n in ("pending.json", "decisions.json", "session.json", "audit.json"))
    original.write_bytes(b"seed database")
    working.write_bytes(b"dirty database")
    pending.write_text('[{"status":"pending"}]')
    decisions.write_text('[{"status":"pending"}]')
    session.write_text('{"session_id":"old"}')
    monkeypatch.setenv("CAMPUS_CUSTOMS_ORIGINAL_DB", str(original))
    monkeypatch.setenv("CAMPUS_CUSTOMS_DB", str(working))
    monkeypatch.setenv("CAMPUS_CUSTOMS_PENDING", str(pending))
    monkeypatch.setenv("CAMPUS_CUSTOMS_DECISIONS", str(decisions))
    monkeypatch.setenv("CAMPUS_CUSTOMS_SESSION", str(session))
    monkeypatch.setattr(audit, "AUDIT_PATH", audit_path)
    monkeypatch.setattr(audit, "SESSION_PATH", session)
    session_id = reset.reset_workspace()
    assert working.read_bytes() == original.read_bytes()
    assert json.loads(pending.read_text()) == []
    assert json.loads(decisions.read_text()) == []
    assert json.loads(session.read_text())["session_id"] == session_id != "old"
    assert json.loads(audit_path.read_text())[-1]["action"] == "database_reset"


def test_duplicate_queued_run_is_rejected_atomically(monkeypatch):
    from fastapi import HTTPException
    import backend.main as main
    main = importlib.reload(main)
    monkeypatch.setattr(main, "event", lambda *a, **k: None)
    async def scenario():
        await main.start_run(101)
        try:
            await main.start_run(101)
        except HTTPException as exc:
            assert exc.status_code == 409
        else:
            raise AssertionError("second queued run should be rejected")
        for task in main.RUN_TASKS.values(): task.cancel()
        await asyncio.gather(*main.RUN_TASKS.values(), return_exceptions=True)
    asyncio.run(scenario())
