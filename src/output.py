import json
import sys


def write_success(data: dict) -> None:
    print(json.dumps(data), file=sys.stdout, flush=True)


def write_error(code: str, message: str) -> None:
    print(json.dumps({"status": "error", "code": code, "message": message}), file=sys.stderr, flush=True)
