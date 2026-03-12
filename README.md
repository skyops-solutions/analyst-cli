# analyst-cli

> Your on-demand AI business analyst. Ask a question, get a structured answer — from the command line or any automated pipeline.

Give it your company context, describe the situation, ask your question.
It thinks it through and gives you a clear, actionable response in seconds.

---

## What problem it solves

Business decisions need fast, structured thinking. Hiring a consultant takes time and money. ChatGPT gives generic answers. This tool is different — it knows your context, remembers the conversation, and gives focused responses tuned to your business situation.

Use it to:
- Draft competitive response strategies
- Analyze market shifts and risks
- Generate client-ready documents
- Get structured answers to any business question

---

## How it works

1. You provide three things: **who you are**, **what's happening**, **what you need**
2. The tool routes your query through Google Gemini 2.5 with a focused prompt
3. You get a clean, structured JSON response — ready to use or pipe into other tools
4. Follow up with more questions — it remembers the full session context

---

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
```

## Usage

### Ask a business question

```bash
python3 -m src.cli \
  --context "SaaS CRM company, EU SMB market" \
  --background "New competitor launched at half our price" \
  --request "Draft a competitive response strategy"
```

### Continue the conversation

```bash
# Start a session
python3 -m src.cli \
  --session my-session \
  --context "SaaS CRM company, EU SMB market" \
  --background "New competitor launched at half our price" \
  --request "Draft a competitive response strategy"

# Drill deeper — context is remembered
python3 -m src.cli --session my-session --request "Expand on point 2"
```

### Pipe it into other tools

```bash
echo '{"context":"...","background":"...","request":"..."}' | python3 -m src.cli
```

---

## Analysis modes

| Template | Best for |
|----------|----------|
| `default` | General business questions |
| `strategy` | Competitive response, go-to-market, positioning |
| `analysis` | Market research, risk assessment, deep analysis |
| `document` | Client-ready reports and proposals |

```bash
python3 -m src.cli --template strategy \
  --context "..." --background "..." --request "..."
```

---

## Output

```json
{"status": "ok", "response": "...", "model": "gemini-2.5-flash", "session_id": "abc123", "tokens_used": 412}
```

Errors go to stderr. Exit code `0` on success, `1` on error.

---

## Requirements

- Python 3.11+
- Google Gemini API key

```env
GEMINI_API_KEY=        # required
GEMINI_MODEL=gemini-2.5-flash
```
