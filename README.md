# IssueSherpa — GitHub Issue Triage Bot

An AI agent that triages new GitHub issues. When an issue is opened, IssueSherpa reads the title and body, applies labels (`bug`, `feature`, `docs`), asks for reproduction steps if they're missing, and suggests an assignee based on `CODEOWNERS`.

Built with FastAPI, LangGraph/LangChain and Pydantic. The LLM backend is pluggable: **OpenAI**, **OpenRouter** or **Ollama**.

## How it works

```
GitHub App (installed on all your repos)
        │  issues.opened webhook
        ▼
POST /webhook ── verify HMAC signature ── 202 Accepted
        │ background task
        ▼
LangGraph: fetch_context → classify ─┬─ bug ─→ check_repro ─┐
                                     └───────────────────────┴─→ suggest_assignee → act
        │
        ▼
labels + one triage comment on the issue
```

A personal GitHub account has no account-wide webhook, so the bot runs as a **GitHub App**. Installing it on "All repositories" sends issue events from every repo (including future ones) to a single URL.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### LLM provider

Set `LLM_PROVIDER` in `.env`:

| Provider | Settings | Example model |
|---|---|---|
| `openai` | `OPENAI_API_KEY` | `gpt-4o-mini` |
| `openrouter` | `OPENROUTER_API_KEY` | `openai/gpt-4o-mini` |
| `ollama` | `OLLAMA_BASE_URL` | `llama3.1` |

New providers can be added by subclassing `LLMFactory` and calling `register()` (see `src/triage_bot/llm/`).

### GitHub App

1. Go to **Settings → Developer settings → GitHub Apps → New GitHub App**.
2. **Webhook URL:** `https://<your-host>/webhook` (a smee.io URL for local dev).
3. **Webhook secret:** any random string; put it in `GITHUB_WEBHOOK_SECRET`.
4. **Repository permissions:** Issues *Read & write*, Contents *Read-only*, Metadata *Read-only*.
5. **Subscribe to events:** Issues.
6. Create the app, note the **App ID** (`GITHUB_APP_ID`) and generate a **private key**; save it as `triage-bot.private-key.pem` (or set `GITHUB_APP_PRIVATE_KEY_PATH`).
7. **Install App** on your account and choose **All repositories**.

## Running locally

```bash
uvicorn triage_bot.main:app --app-dir src --reload
```

Forward GitHub webhooks to your machine with [smee.io](https://smee.io):

```bash
npx smee -u https://smee.io/<channel> -t http://localhost:8000/webhook
```

Set `DRY_RUN=true` to log labels and comments instead of writing them to GitHub.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai`, `openrouter` or `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for the provider |
| `LLM_TEMPERATURE` | `0` | |
| `GITHUB_APP_ID` | | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY_PATH` | `triage-bot.private-key.pem` | App private key |
| `GITHUB_WEBHOOK_SECRET` | | Webhook HMAC secret |
| `DRY_RUN` | `false` | Log instead of writing to GitHub |
| `ALLOWED_LABELS` | `bug,feature,docs` | Labels the bot may apply |

## Project layout

```
src/triage_bot/
├── main.py          FastAPI app (/webhook, /healthz)
├── config.py        Settings from .env
├── security.py      Webhook signature check
├── service.py       Runs the triage graph for an event
├── llm/             LLM factory (OpenAI, OpenRouter, Ollama)
├── github/          App auth, REST client, CODEOWNERS
├── agent/           LangGraph state, prompts, nodes, graph
└── schemas/         Pydantic models
```
