import asyncio
import importlib
import inspect
import json
import sqlite3


def test_append_ticket_note_cannot_change_status():
    import mcp_server.server as server

    server = importlib.reload(server)
    with sqlite3.connect(server.DATABASE_PATH) as connection:
        before = connection.execute("SELECT status FROM tickets WHERE id=101").fetchone()[0]
    assert "close_ticket" not in inspect.signature(server.append_ticket_note).parameters
    result = server.append_ticket_note(101, "test", "status-preserving note")
    assert result["updated"]
    with sqlite3.connect(server.DATABASE_PATH) as connection:
        after = connection.execute("SELECT status FROM tickets WHERE id=101").fetchone()[0]
    assert after == before
    try:
        server.append_ticket_note(101, "test", "attempt", close_ticket=True)
    except TypeError:
        pass
    else:
        raise AssertionError("close_ticket must no longer be accepted")


def test_run_status_lifecycle_obeys_human_requests(monkeypatch):
    import backend.main as main

    main = importlib.reload(main)
    status = {"value": "open"}
    pending = []
    reasons = []

    async def fake_mcp(name, args=None):
        if name == "list_requests":
            return list(pending)
        if name == "list_decisions": return []
        if name == "list_tickets":
            return [{"id": 101, "type": "rent_notice", "status": status["value"]}]
        if name == "set_ticket_status":
            status["value"] = args["status"]
            reasons.append(args["note"])
            return {"updated": True, "status": status["value"]}
        raise AssertionError(name)

    changes = []
    monkeypatch.setattr(main, "mcp_call", fake_mcp)
    monkeypatch.setattr(main, "event", lambda *args, **kwargs: changes.append((args, kwargs)))

    async def scenario():
        main.RUNS["run-test"] = {"run_id": "run-test", "ticket_id": 101, "status": "running"}
        pending[:] = [{"status": "pending", "ticket_id": 101, "session_id": main.current_session_id()}]
        await main.finish_run_status("run-test", 101, "Result\nSTATUS: resolved")
        assert status["value"] == "awaiting_approval"
        pending.clear()
        latest = {"run_id": "run-test", "ticket_id": 101, "status": "completed"}
        await main.re_evaluate_ticket(101, latest)
        assert status["value"] == "awaiting_decision"
        assert reasons[-1] == "no rent payment request prepared; human must decide"
        pending.append({"status": "used", "kind": "rent", "ticket_id": 101, "session_id": main.current_session_id()})
        await main.re_evaluate_ticket(101, latest)
        assert status["value"] == "resolved"
        main.RUNS["run-open"] = {"run_id": "run-open", "ticket_id": 101, "status": "running"}
        await main.finish_run_status("run-open", 101, "Review complete\nSTATUS: needs_human")
        assert status["value"] == "resolved"

    asyncio.run(scenario())
    assert sum(args[3] == "ticket_status_changed" for args, _ in changes) == 3
    assert sum(args[3] == "final_disposition" for args, _ in changes) == 2


def test_audit_events_receive_temporary_session_id(tmp_path, monkeypatch):
    import backend.audit as audit

    monkeypatch.setattr(audit, "AUDIT_PATH", tmp_path / "audit.json")
    monkeypatch.setattr(audit, "SESSION_PATH", tmp_path / "session.json")
    session = audit.current_session_id()
    audit.event("test-run", 1, "system", "test_event", 101, {"safe": True})
    rows = json.loads((tmp_path / "audit.json").read_text())
    assert rows[0]["session_id"] == session


def test_run_history_filters_current_session_by_default(monkeypatch):
    import backend.main as main

    main = importlib.reload(main)
    current = main.current_session_id()
    records = []
    for run_id, ticket, session_id in [
        ("current-run", 101, current),
        ("old-run", 102, "older-session"),
        ("legacy-run", 103, None),
    ]:
        records.append({"run_id": run_id, "ticket_id": ticket, "action": "backend_run_started", "session_id": session_id})
        records.append({"run_id": run_id, "ticket_id": ticket, "agent": "boss", "action": "final_output", "detail": {"result": "done"}, "session_id": session_id})
    monkeypatch.setattr(main, "_read_audit", lambda: records)
    assert set(main._audit_runs()) == {"current-run"}
    assert set(main._audit_runs(all_sessions=True)) == {"current-run", "old-run", "legacy-run"}


def test_run_iter_emits_live_model_and_tool_events(monkeypatch):
    import backend.agents as agents

    agents = importlib.reload(agents)
    from types import SimpleNamespace

    actions = []
    monkeypatch.setattr(
        agents,
        "event",
        lambda run_id, step, role, action, ticket_id, detail=None, outcome="completed", **kwargs: actions.append(
            (action, detail or {})
        ),
    )

    class ToolReturnPart:
        tool_name = "list_tickets"
        tool_call_id = "tool-1"
        content = {"ok": True}

    class TextPart:
        content = "A concise response"

    class ToolCallPart:
        tool_name = "list_tickets"
        args = {"ticket_id": 101}
        tool_call_id = "tool-2"

    class ModelRequestNode:
        request = SimpleNamespace(parts=[ToolReturnPart()])

    class CallToolsNode:
        model_response = SimpleNamespace(
            model_name="gpt-6-luna-2026-09-22",
            provider_name="portkey",
            parts=[TextPart(), ToolCallPart()],
        )

    class FakeRun:
        result = SimpleNamespace(output="Ticket reviewed\nSTATUS: resolved", usage=SimpleNamespace())

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        def __aiter__(self):
            async def nodes():
                yield ModelRequestNode()
                yield CallToolsNode()

            return nodes()

    class FakeAgent:
        def iter(self, *args, **kwargs):
            return FakeRun()

    monkeypatch.setitem(agents.AGENTS, "boss", FakeAgent())
    result = asyncio.run(agents.run_agent("boss", "inspect", agents.RunContextData("test-run", 101)))
    assert result.endswith("STATUS: resolved")
    assert [action for action, _ in actions] == [
        "loop_start", "model_request", "tool_result", "model_response", "tool_call", "final_output", "token_usage"
    ]
    response = next(detail for action, detail in actions if action == "model_response")
    assert response["returned_model"] == {
        "model_name": "gpt-6-luna-2026-09-22",
        "provider_name": "portkey",
    }
    final = next(detail for action, detail in actions if action == "final_output")
    assert final["returned_models"][0]["model_name"] == "gpt-6-luna-2026-09-22"
