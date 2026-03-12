# analyst-cli

> AI-powered query engine for structured business analysis — pipe-friendly CLI built on Google Gemini 2.5.

Feed it a business context, a situation, and a question. Get a clean JSON answer back. Chain it into any pipeline, automate it, or use it interactively across multi-turn sessions.

---

## What it does

- Accepts three inputs: **context** (who you are), **background** (the situation), **request** (what you need)
- Routes them through Google Gemini 2.5 with a focused prompt template
- Returns structured JSON to stdout — errors go to stderr
- Persists session memory in SQLite for multi-turn conversations
- Supports swappable prompt templates (strategy, analysis, document, default)

---

## Requirements

- Python 3.11+
- Google Gemini API key

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

## Usage

### Single query

```bash
python3 -m src.cli \
  --context "SaaS CRM company, EU SMB market" \
  --background "New competitor launched at half our price" \
  --request "Draft a competitive response strategy"
```

### Multi-turn session

```bash
# Start a session
python3 -m src.cli \
  --session my-session \
  --context "SaaS CRM company, EU SMB market" \
  --background "New competitor launched at half our price" \
  --request "Draft a competitive response strategy"

# Follow-up (context/background loaded from session)
python3 -m src.cli --session my-session --request "Expand on point 2"
```

### Stdin (JSON)

```bash
echo '{"context":"...","background":"...","request":"..."}' | python3 -m src.cli
```

### Templates

```bash
# List available templates
python3 -m src.cli --list-templates

# Use a specific template
python3 -m src.cli --template strategy \
  --context "..." --background "..." --request "..."

# Override model
python3 -m src.cli --model gemini-1.5-pro \
  --context "..." --background "..." --request "..."
```

---

## Output

**stdout (success):**
```json
{"status": "ok", "response": "...", "model": "gemini-2.5-flash", "session_id": "abc123", "tokens_used": 412, "template": "default"}
```

**stderr (error):**
```json
{"status": "error", "code": "api_error", "message": "..."}
```

Exit code `0` on success, `1` on error.

---

## Templates

| Name | Description | Model |
|------|-------------|-------|
| `default` | General-purpose business query | gemini-2.5-flash |
| `strategy` | Competitive response and business strategy | gemini-2.5-flash |
| `analysis` | Market and business analysis | gemini-1.5-pro |
| `document` | Client-ready document generation | gemini-2.5-flash |

---

## Configuration

```env
GEMINI_API_KEY=        # required
GEMINI_MODEL=gemini-2.5-flash
MAX_TOKENS=1024
CONTEXT_WINDOW=10
SQLITE_DB_PATH=./data/sessions.db
TEMPLATES_PATH=./src/templates
```

---

## Tests

```bash
pytest tests/ -v
# 30 tests, 0 failures
```

---

## Project structure

```
src/
  cli.py              → Entry point (argparse + stdin)
  engine.py           → Core loop (prompt + history + Gemini)
  gemini.py           → Gemini API client (retry logic)
  context.py          → Session sliding window
  memory.py           → SQLite session storage
  output.py           → JSON stdout/stderr formatter
  template_loader.py  → Template loader
  templates/          → TOML + Markdown template library
tests/                → pytest test suite
```
