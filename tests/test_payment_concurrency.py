import importlib
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

ROOT = Path(__file__).resolve().parents[1]


def _load_server():
    import mcp_server.server as server

    return importlib.reload(server)


def test_competing_approvals_never_overdraw_and_ledger_matches(tmp_path, monkeypatch):
    for iteration in range(20):
        case = tmp_path / f"trial_{iteration}"
        case.mkdir()
        database = case / "db.sqlite"
        pending = case / "pending.json"
        shutil.copy2(ROOT / "data" / "campus_customs.db", database)
        pending.write_text("[]\n")
        monkeypatch.setenv("CAMPUS_CUSTOMS_DB", str(database))
        monkeypatch.setenv("CAMPUS_CUSTOMS_PENDING", str(pending))
        server = _load_server()

        invoice = server.prepare_payment("invoice", 501, 840.0, ticket_id=101)
        assert invoice["prepared"]
        paid_invoice = server.execute_approved_payment(invoice["request_id"], "Test Human")
        assert paid_invoice["paid"]
        rent = server.prepare_payment("rent", 1, 2400.0, ticket_id=102)
        order = server.prepare_purchase_order("CC-HOOD-NAVY", "M", 12, 1, ticket_id=103)
        assert rent["prepared"] and order["prepared"]

        barrier = Barrier(2)

        def approve(request_id):
            barrier.wait()
            return server.execute_approved_payment(request_id, "Concurrent Human")

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(approve, rent["request_id"]),
                pool.submit(approve, order["request_id"]),
            ]
            outcomes = [future.result() for future in futures]

        successful = [result for result in outcomes if result.get("paid")]
        assert len(successful) == 1, outcomes
        import sqlite3

        with sqlite3.connect(database) as connection:
            balance = connection.execute(
                "SELECT balance FROM cash_accounts WHERE name='checking'"
            ).fetchone()[0]
            payments = connection.execute(
                "SELECT kind, amount FROM payments ORDER BY id"
            ).fetchall()
        assert balance >= 0
        assert balance in (160.0, 2296.0)
        assert len(payments) == 2
        assert abs(sum(row[1] for row in payments) - (3400.0 - balance)) < 0.001
        saved = json.loads(pending.read_text())
        assert sum(item["status"] == "used" for item in saved) == 2
