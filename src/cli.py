#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import select
import sys

from src.engine import run
from src.gemini import GeminiError
from src import memory
from src.output import write_error, write_success
from src.template_loader import list_templates, TemplateNotFoundError, ALLOWED_MODELS


def _read_stdin() -> dict | None:
    if select.select([sys.stdin], [], [], 0)[0]:
        raw = sys.stdin.read().strip()
        if raw:
            return json.loads(raw)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Conversational AI query engine",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--context", help="Company name, industry, product description")
    parser.add_argument("--background", help="Current situation or problem")
    parser.add_argument("--request", help="What the user needs")
    parser.add_argument("--session", help="Session ID for multi-turn conversation")
    parser.add_argument("--template", help="Template name (use --list-templates to see options)")
    parser.add_argument("--model", help="Override Gemini model for this query")
    parser.add_argument("--list-templates", action="store_true", help="List available templates and exit")
    args = parser.parse_args()

    # Handle --list-templates
    if args.list_templates:
        write_success({"status": "ok", "templates": list_templates()})
        sys.exit(0)

    # Validate --model if provided
    if args.model and args.model not in ALLOWED_MODELS:
        write_error("config_error", f"Unknown model '{args.model}'. Allowed: {sorted(ALLOWED_MODELS)}")
        sys.exit(1)

    # Attempt to read from stdin first
    stdin_data: dict | None = None
    try:
        stdin_data = _read_stdin()
    except json.JSONDecodeError:
        write_error("input_error", "Invalid JSON on stdin")
        sys.exit(1)

    if stdin_data is not None:
        context = stdin_data.get("context", "").strip()
        background = stdin_data.get("background", "").strip()
        request = stdin_data.get("request", "").strip()
        session_id = stdin_data.get("session", args.session or "").strip() or None
    else:
        context = (args.context or "").strip()
        background = (args.background or "").strip()
        request = (args.request or "").strip()
        session_id = (args.session or "").strip() or None

    # Follow-up turn: session exists, context/background may be omitted
    if session_id and not context and not background:
        memory.init_db()
        meta = memory.load_session_meta(session_id)
        if meta is None:
            write_error("input_error", f"Session '{session_id}' not found. Provide --context and --background for the first turn.")
            sys.exit(1)
        context = meta["context"]
        background = meta["background"]

    missing = [f for f, v in [("context", context), ("background", background), ("request", request)] if not v]
    if missing:
        write_error("input_error", f"Missing required fields: {', '.join(missing)}")
        parser.print_usage(sys.stderr)
        sys.exit(1)

    try:
        result = run(
            context, background, request,
            session_id=session_id,
            template_name=args.template or None,
            model_override=args.model or None,
        )
        write_success(result)
    except TemplateNotFoundError as e:
        write_error("template_error", str(e))
        sys.exit(1)
    except ValueError as e:
        write_error("template_error", str(e))
        sys.exit(1)
    except GeminiError as e:
        write_error("api_error", str(e))
        sys.exit(1)
    except Exception as e:
        write_error("internal_error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
