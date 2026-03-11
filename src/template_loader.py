import os
import tomllib
from pathlib import Path

_TEMPLATES_PATH = Path(os.getenv("TEMPLATES_PATH", Path(__file__).parent / "templates"))

ALLOWED_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
}


class TemplateNotFoundError(Exception):
    pass


def list_templates() -> list:
    templates_dir = Path(os.getenv("TEMPLATES_PATH", str(_TEMPLATES_PATH)))
    if not templates_dir.exists():
        return []
    return sorted(
        d.name
        for d in templates_dir.iterdir()
        if d.is_dir() and (d / "system.md").exists() and (d / "query.toml").exists()
    )


def load_template(name: str) -> dict:
    templates_dir = Path(os.getenv("TEMPLATES_PATH", str(_TEMPLATES_PATH)))
    template_dir = templates_dir / name

    if not template_dir.exists():
        raise TemplateNotFoundError(
            f"Template '{name}' not found. Use --list-templates."
        )

    system_md = template_dir / "system.md"
    query_toml = template_dir / "query.toml"

    if not system_md.exists() or not query_toml.exists():
        raise TemplateNotFoundError(
            f"Template '{name}' is incomplete (missing system.md or query.toml)."
        )

    system_prompt = system_md.read_text().strip()

    try:
        config = tomllib.loads(query_toml.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Failed to parse template config: {e}") from e

    return {
        "name": name,
        "system_prompt": system_prompt,
        "config": config,
        "model": config.get("model", {}).get("default", "gemini-2.5-flash"),
        "max_tokens": config.get("model", {}).get("max_tokens", 1024),
        "context_window": config.get("model", {}).get("context_window", 10),
    }


def get_default_template() -> dict:
    return load_template("default")
