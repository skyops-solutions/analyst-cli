import os
import sys
import uuid
from typing import Optional

from src.gemini import generate_with_history, GeminiError
from src import context as ctx
from src import memory
from src.template_loader import get_default_template, load_template, TemplateNotFoundError

_FALLBACK_SYSTEM_PROMPT = (
    "You are a senior business strategy consultant. "
    "Respond with a structured, actionable answer. "
    "Keep your response concise and professional."
)


def _build_user_message(context: str, background: str, request: str) -> str:
    return (
        f"CONTEXT: {context}\n"
        f"BACKGROUND: {background}\n"
        f"REQUEST: {request}"
    )


def run(
    context: str,
    background: str,
    request: str,
    session_id: Optional[str] = None,
    template_name: Optional[str] = None,
    model_override: Optional[str] = None,
) -> dict:
    if session_id is None:
        session_id = str(uuid.uuid4())

    memory.init_db()

    # Load template
    try:
        template = load_template(template_name) if template_name else get_default_template()
    except TemplateNotFoundError:
        raise
    except ValueError:
        raise

    system_prompt = template.get("system_prompt", _FALLBACK_SYSTEM_PROMPT)

    # model_override from CLI takes priority over template default
    model = model_override or template.get("model", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    max_tokens = template.get("max_tokens", int(os.getenv("MAX_TOKENS", "1024")))
    window = template.get("context_window", int(os.getenv("CONTEXT_WINDOW", "10")))

    # Save session meta on first turn (no-op if already exists)
    if context and background:
        try:
            memory.save_session_meta(session_id, context, background)
        except Exception as e:
            print(f'{{"status":"error","code":"db_error","message":"{e}"}}', file=sys.stderr, flush=True)

    user_message = _build_user_message(context, background, request)

    # Build messages: system instruction pair + history + new user turn
    base = [
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": "Understood. I am ready to assist."}]},
    ]
    try:
        history = ctx.build_messages(session_id, user_message, window=window)
        messages = base + history
    except Exception as e:
        print(f'{{"status":"error","code":"db_error","message":"{e}"}}', file=sys.stderr, flush=True)
        messages = base + [{"role": "user", "parts": [{"text": user_message}]}]

    # Temporarily override env model if needed
    original_model = os.environ.get("GEMINI_MODEL")
    os.environ["GEMINI_MODEL"] = model
    os.environ["MAX_TOKENS"] = str(max_tokens)
    try:
        result = generate_with_history(messages)
    finally:
        if original_model is not None:
            os.environ["GEMINI_MODEL"] = original_model
        else:
            os.environ.pop("GEMINI_MODEL", None)

    # Save turn to DB
    try:
        memory.save_turn(session_id, "user", user_message)
        memory.save_turn(session_id, "model", result["response"])
    except Exception as e:
        print(f'{{"status":"error","code":"db_error","message":"{e}"}}', file=sys.stderr, flush=True)

    return {
        "status": "ok",
        "response": result["response"],
        "model": result["model"],
        "session_id": session_id,
        "tokens_used": result["tokens_used"],
        "template": template_name or "default",
    }
