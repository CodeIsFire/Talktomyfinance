# AI Finance Voice Assistant

A voice-ready finance assistant that combines a multi-agent backend, retrieval-grounded answers, and a lightweight React frontend. The project is designed as a demo-friendly portfolio system for finance queries such as spending summaries, subscription analysis, and account-linking workflows.

## What it does

- Accepts finance questions through a FastAPI backend
- Uses a research agent to filter transactions, a finance agent to compute summaries, and an editor agent to turn results into conversational answers
- Grounds responses with a small knowledge-base retrieval layer
- Includes a simple React + TypeScript chat UI
- Supports a Plaid sandbox flow for connecting a bank account
- Offers a voice loop for spoken interaction

## Project structure

- app.py — FastAPI entrypoint and API routes
- agents/ — research, finance, editor, and orchestration logic
- rag/ — knowledge-base indexing and retrieval
- eval/ — grounding checks and logging
- voice/ — speech input/output helpers and voice loop
- frontend/ — Vite + React + TypeScript UI
- plaid_integration/ — Plaid sandbox adapter and local token/transaction storage
- data/ — synthetic transactions and knowledge-base markdown docs

## Quick start

1. Create a Python virtual environment and install dependencies:
   - python3 -m venv .venv
   - ./.venv/bin/pip install -r requirements.txt
2. Copy the environment example and fill in your credentials:
   - cp .env.example .env
3. Run the backend:
   - ./.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
4. Run the frontend:
   - cd frontend && npm install && npm run dev

## Environment variables

The project uses the following environment variables:

- GROQ_API_KEY
- GROQ_MODEL
- PLAID_CLIENT_ID
- PLAID_SECRET
- PLAID_ENV
- DATA_SOURCE
- CORS_ALLOWED_ORIGINS (comma-separated list, optional)

See [.env.example](.env.example) for the expected shape.

## Vercel deployment

This repository is configured for Vercel with:

- static frontend build from `frontend/` (`npm run build`, output `frontend/dist`)
- Python serverless API function at `api/index.py` (imports FastAPI `app` from `app.py`)
- routing:
  - `/api/*` -> FastAPI backend
  - `/health` -> FastAPI backend
  - all other routes -> frontend SPA (`index.html`)

### Vercel project settings

- Framework Preset: **Other**
- Root Directory: repository root (do not set to `frontend`)
- Build and Output settings: managed by `vercel.json`

### Required environment variables

- `GROQ_API_KEY` (required for LLM responses; app falls back to deterministic local responses when missing)

### Optional environment variables

- `GROQ_MODEL` (default: `llama-3.1-8b-instant`)
- `DATA_SOURCE` (`mock` by default; set `plaid` only when Plaid tokens are configured)
- `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV` (only needed for Plaid endpoints)
- `CORS_ALLOWED_ORIGINS` (comma-separated production origins, for example `https://project-6apdz.vercel.app`)

`/health` and mock-data operation do not require Plaid credentials.

## Plaid sandbox setup

1. Create a Plaid account and obtain sandbox credentials from the Plaid dashboard.
2. Add your client ID and secret to .env.
3. Use sandbox credentials such as username user_good and password pass_good when testing the link flow.
4. Set DATA_SOURCE=plaid after exchanging a public token and syncing transactions.

## Testing

Run the unit tests with:

- ./.venv/bin/python -m pytest -q

## Notes

This project is intended as a portfolio/demo application and uses synthetic data by default. The Plaid integration is optional and only activates when credentials are configured.
