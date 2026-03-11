import os
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def tmp_templates(tmp_path, monkeypatch):
    """Create a minimal template dir structure for testing."""
    monkeypatch.setenv("TEMPLATES_PATH", str(tmp_path))

    # default template
    default = tmp_path / "default"
    default.mkdir()
    (default / "system.md").write_text("You are a default assistant.")
    (default / "query.toml").write_text(
        '[meta]\nname = "default"\n\n[model]\ndefault = "gemini-2.5-flash"\nmax_tokens = 1024\ncontext_window = 10\n'
    )

    # strategy template
    strategy = tmp_path / "strategy"
    strategy.mkdir()
    (strategy / "system.md").write_text("You are a strategy consultant.")
    (strategy / "query.toml").write_text(
        '[meta]\nname = "strategy"\n\n[model]\ndefault = "gemini-2.5-flash"\nmax_tokens = 1500\ncontext_window = 10\n'
    )

    # incomplete template (missing query.toml)
    incomplete = tmp_path / "incomplete"
    incomplete.mkdir()
    (incomplete / "system.md").write_text("Only system prompt.")

    return tmp_path


def test_list_templates_returns_complete_only(tmp_templates):
    from src.template_loader import list_templates
    result = list_templates()
    assert "default" in result
    assert "strategy" in result
    assert "incomplete" not in result


def test_list_templates_sorted(tmp_templates):
    from src.template_loader import list_templates
    result = list_templates()
    assert result == sorted(result)


def test_load_template_default(tmp_templates):
    from src.template_loader import load_template
    t = load_template("default")
    assert t["name"] == "default"
    assert t["system_prompt"] == "You are a default assistant."
    assert t["model"] == "gemini-2.5-flash"
    assert t["max_tokens"] == 1024
    assert t["context_window"] == 10


def test_load_template_strategy(tmp_templates):
    from src.template_loader import load_template
    t = load_template("strategy")
    assert t["name"] == "strategy"
    assert t["system_prompt"] == "You are a strategy consultant."
    assert t["max_tokens"] == 1500


def test_load_template_not_found(tmp_templates):
    from src.template_loader import load_template, TemplateNotFoundError
    with pytest.raises(TemplateNotFoundError, match="not found"):
        load_template("nonexistent")


def test_load_template_incomplete(tmp_templates):
    from src.template_loader import load_template, TemplateNotFoundError
    with pytest.raises(TemplateNotFoundError, match="incomplete"):
        load_template("incomplete")


def test_load_template_malformed_toml(tmp_templates):
    bad = tmp_templates / "bad"
    bad.mkdir()
    (bad / "system.md").write_text("System prompt.")
    (bad / "query.toml").write_text("this is not valid toml ][[[")
    from src.template_loader import load_template
    with pytest.raises(ValueError, match="Failed to parse template config"):
        load_template("bad")


def test_get_default_template(tmp_templates):
    from src.template_loader import get_default_template
    t = get_default_template()
    assert t["name"] == "default"


def test_list_templates_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TEMPLATES_PATH", str(tmp_path))
    from src.template_loader import list_templates
    assert list_templates() == []


def test_list_templates_nonexistent_dir(monkeypatch):
    monkeypatch.setenv("TEMPLATES_PATH", "/nonexistent/path")
    from src.template_loader import list_templates
    assert list_templates() == []
