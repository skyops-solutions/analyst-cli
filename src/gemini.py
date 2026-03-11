import os
import time

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class GeminiError(Exception):
    pass


def generate(prompt: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not set")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
    client = genai.Client(api_key=api_key)
    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=max_tokens),
            )
            return {
                "response": response.text,
                "model": model_name,
                "tokens_used": response.usage_metadata.total_token_count if response.usage_metadata else 0,
            }
        except Exception as e:
            last_error = e
            status = getattr(getattr(e, "response", None), "status_code", None)
            err_str = str(e)
            if status in (429, 500, 503) or "429" in err_str or "500" in err_str or "503" in err_str:
                time.sleep(2 ** attempt)
                continue
            raise GeminiError(str(e)) from e

    raise GeminiError(str(last_error))


def generate_with_history(messages: list) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not set")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    max_tokens = int(os.getenv("MAX_TOKENS", "1024"))
    client = genai.Client(api_key=api_key)
    last_error = None

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=messages,
                config=types.GenerateContentConfig(max_output_tokens=max_tokens),
            )
            return {
                "response": response.text,
                "model": model_name,
                "tokens_used": response.usage_metadata.total_token_count if response.usage_metadata else 0,
            }
        except Exception as e:
            last_error = e
            status = getattr(getattr(e, "response", None), "status_code", None)
            err_str = str(e)
            if status in (429, 500, 503) or "429" in err_str or "500" in err_str or "503" in err_str:
                time.sleep(2 ** attempt)
                continue
            raise GeminiError(str(e)) from e

    raise GeminiError(str(last_error))
