import os
import tempfile
import pytest

# Use a temp DB for all tests
@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    db = str(tmp_path / "test.db")
    monkeypatch.setenv("SQLITE_DB_PATH", db)
    # Re-import to pick up new env var
    import importlib
    import src.memory as mem
    importlib.reload(mem)
    mem.init_db()
    return mem


def test_init_db_creates_tables(tmp_db):
    import sqlite3, os
    db_path = os.getenv("SQLITE_DB_PATH")
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "sessions" in tables
    assert "session_meta" in tables
    conn.close()


def test_save_and_load_turns(tmp_db):
    tmp_db.save_turn("s1", "user", "Hello")
    tmp_db.save_turn("s1", "model", "Hi there")
    turns = tmp_db.load_turns("s1")
    assert len(turns) == 2
    assert turns[0] == {"role": "user", "content": "Hello"}
    assert turns[1] == {"role": "model", "content": "Hi there"}


def test_load_turns_respects_limit(tmp_db):
    for i in range(15):
        tmp_db.save_turn("s2", "user", f"msg {i}")
    turns = tmp_db.load_turns("s2", limit=10)
    assert len(turns) == 10
    # Should be the last 10 in chronological order
    assert turns[-1]["content"] == "msg 14"


def test_load_turns_empty_session(tmp_db):
    assert tmp_db.load_turns("nonexistent") == []


def test_save_and_load_session_meta(tmp_db):
    tmp_db.save_session_meta("s3", "ACME Corp", "Price war")
    meta = tmp_db.load_session_meta("s3")
    assert meta == {"context": "ACME Corp", "background": "Price war"}


def test_load_session_meta_missing(tmp_db):
    assert tmp_db.load_session_meta("does-not-exist") is None


def test_save_session_meta_does_not_overwrite(tmp_db):
    tmp_db.save_session_meta("s4", "First context", "First background")
    tmp_db.save_session_meta("s4", "Second context", "Second background")
    meta = tmp_db.load_session_meta("s4")
    assert meta["context"] == "First context"
