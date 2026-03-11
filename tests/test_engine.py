import json
from unittest.mock import MagicMock, patch

import pytest

from src.gemini import GeminiError, generate
from src.output import write_error, write_success


# --- output.py tests ---

def test_write_success_is_valid_json(capsys):
    write_success({"status": "ok", "response": "hello", "model": "gemini-2.5-flash", "session_id": None, "tokens_used": 10})
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "ok"
    assert captured.err == ""


def test_write_error_goes_to_stderr(capsys):
    write_error("api_error", "something went wrong")
    captured = capsys.readouterr()
    assert captured.out == ""
    data = json.loads(captured.err)
    assert data["status"] == "error"
    assert data["code"] == "api_error"


# --- engine.py tests ---

@pytest.fixture
def tmp_db(monkeypatch, tmp_path):
    db = str(tmp_path / "test.db")
    monkeypatch.setenv("SQLITE_DB_PATH", db)
    import importlib
    import src.memory as mem
    importlib.reload(mem)
    mem.init_db()
    monkeypatch.setattr("src.engine.memory", mem)
    return mem


def test_run_returns_correct_shape(tmp_db):
    mock_result = {"response": "Strategic response.", "model": "gemini-2.5-flash", "tokens_used": 42}
    with patch("src.engine.generate_with_history", return_value=mock_result):
        from src.engine import run
        result = run(context="SaaS CRM", background="New competitor", request="Draft strategy")
    assert result["status"] == "ok"
    assert result["response"] == "Strategic response."
    assert result["tokens_used"] == 42
    assert result["session_id"] is not None  # auto-generated UUID


def test_run_with_explicit_session_id(tmp_db):
    mock_result = {"response": "ok", "model": "gemini-2.5-flash", "tokens_used": 1}
    with patch("src.engine.generate_with_history", return_value=mock_result):
        from src.engine import run
        result = run(context="ACME", background="Price war", request="Cut costs", session_id="my-session")
    assert result["session_id"] == "my-session"


def test_run_saves_turns_to_db(tmp_db):
    mock_result = {"response": "Answer.", "model": "gemini-2.5-flash", "tokens_used": 5}
    with patch("src.engine.generate_with_history", return_value=mock_result):
        from src.engine import run
        run(context="ACME", background="Crisis", request="Help", session_id="s-save")
    turns = tmp_db.load_turns("s-save")
    assert len(turns) == 2
    assert turns[0]["role"] == "user"
    assert turns[1]["role"] == "model"
    assert turns[1]["content"] == "Answer."


def test_run_second_turn_uses_history(tmp_db):
    mock_result = {"response": "Follow-up answer.", "model": "gemini-2.5-flash", "tokens_used": 5}
    tmp_db.save_turn("s-hist", "user", "First question")
    tmp_db.save_turn("s-hist", "model", "First answer")
    tmp_db.save_session_meta("s-hist", "ACME", "Crisis")
    with patch("src.engine.generate_with_history", return_value=mock_result) as mock_gen:
        from src.engine import run
        run(context="ACME", background="Crisis", request="Follow-up", session_id="s-hist")
        messages = mock_gen.call_args[0][0]
    # System prompt pair + 2 history turns + 1 new user turn
    roles = [m["role"] for m in messages]
    assert roles.count("user") >= 2
    assert roles.count("model") >= 1


# --- gemini.py retry tests ---

def test_gemini_retries_on_429():
    call_count = 0
    mock_response = MagicMock()
    mock_response.text = "answer"
    mock_response.usage_metadata.total_token_count = 5

    def flaky_generate(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("429 Too Many Requests")
        return mock_response

    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}), \
         patch("src.gemini.genai.Client") as mock_client_cls, \
         patch("src.gemini.time.sleep"):
        mock_client_cls.return_value.models.generate_content.side_effect = flaky_generate
        result = generate("test prompt")
    assert result["response"] == "answer"
    assert call_count == 3


def test_gemini_raises_after_3_failures():
    with patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}), \
         patch("src.gemini.genai.Client") as mock_client_cls, \
         patch("src.gemini.time.sleep"):
        mock_client_cls.return_value.models.generate_content.side_effect = Exception("500 Server Error")
        with pytest.raises(GeminiError):
            generate("test prompt")
