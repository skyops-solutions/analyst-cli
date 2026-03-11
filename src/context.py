import os
from typing import Optional

from src import memory

_WINDOW = int(os.getenv("CONTEXT_WINDOW", "10"))


def build_messages(session_id: str, new_user_message: str, window: int = _WINDOW) -> list:
    turns = memory.load_turns(session_id, limit=window)
    messages = []
    for turn in turns:
        role = "model" if turn["role"] == "model" else "user"
        messages.append({"role": role, "parts": [{"text": turn["content"]}]})
    messages.append({"role": "user", "parts": [{"text": new_user_message}]})
    return messages


def get_session_meta(session_id: str) -> Optional[dict]:
    return memory.load_session_meta(session_id)
