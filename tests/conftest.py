import shutil
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def temporary_shop_paths(tmp_path, monkeypatch):
    database = tmp_path / "campus_customs_test.db"
    pending = tmp_path / "pending_test.json"
    decisions = tmp_path / "decisions_test.json"
    shutil.copy2(ROOT / "data" / "campus_customs.db", database)
    pending.write_text("[]\n")
    decisions.write_text("[]\n")
    monkeypatch.setenv("CAMPUS_CUSTOMS_DB", str(database))
    monkeypatch.setenv("CAMPUS_CUSTOMS_PENDING", str(pending))
    monkeypatch.setenv("CAMPUS_CUSTOMS_DECISIONS", str(decisions))
    monkeypatch.setenv("CAMPUS_CUSTOMS_SESSION", str(tmp_path / "session_test.json"))
    monkeypatch.setenv("PORTKEY_API_KEY", "test-key-not-used-for-model-calls")
    import backend.audit as audit

    monkeypatch.setattr(audit, "AUDIT_PATH", tmp_path / "audit_test.json")
    monkeypatch.setattr(audit, "SESSION_PATH", tmp_path / "session_test.json")
    return database, pending
