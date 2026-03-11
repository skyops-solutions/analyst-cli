import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    db = str(tmp_path / "test.db")
    monkeypatch.setenv("SQLITE_DB_PATH", db)
    import importlib
    import src.memory as mem
    importlib.reload(mem)
    mem.init_db()
    monkeypatch.setattr("src.context.memory", mem)
    return mem


def test_build_messages_empty_history(tmp_db):
    from src.context import build_messages
    msgs = build_messages("s1", "What should I do?")
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["parts"][0]["text"] == "What should I do?"


def test_build_messages_with_history(tmp_db):
    tmp_db.save_turn("s1", "user", "First question")
    tmp_db.save_turn("s1", "model", "First answer")
    from src.context import build_messages
    msgs = build_messages("s1", "Follow-up question")
    assert len(msgs) == 3
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "model"
    assert msgs[2]["role"] == "user"
    assert msgs[2]["parts"][0]["text"] == "Follow-up question"


def test_build_messages_sliding_window(tmp_db):
    for i in range(12):
        tmp_db.save_turn("s2", "user", f"q{i}")
        tmp_db.save_turn("s2", "model", f"a{i}")
    from src.context import build_messages
    msgs = build_messages("s2", "new question", window=10)
    # 10 history turns + 1 new user message
    assert len(msgs) == 11
    assert msgs[-1]["parts"][0]["text"] == "new question"


def test_get_session_meta_missing(tmp_db):
    from src.context import get_session_meta
    assert get_session_meta("no-such-session") is None


def test_get_session_meta_exists(tmp_db):
    tmp_db.save_session_meta("s3", "ACME", "Price war")
    from src.context import get_session_meta
    meta = get_session_meta("s3")
    assert meta["context"] == "ACME"
    assert meta["background"] == "Price war"
