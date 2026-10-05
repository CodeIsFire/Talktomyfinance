import os
import time
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.orchestrator import answer_query
from plaid_integration.client import get_plaid_client
from plaid_integration.service import get_access_token, get_synced_transactions, store_access_token, sync_transactions


def _allowed_origins() -> list[str]:
    origins = {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }

    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
    for origin in configured_origins.split(","):
        normalized = origin.strip()
        if normalized:
            origins.add(normalized)

    for vercel_host_env in ("VERCEL_PROJECT_PRODUCTION_URL", "VERCEL_BRANCH_URL", "VERCEL_URL"):
        host = os.getenv(vercel_host_env, "").strip()
        if host:
            if host.startswith("http://") or host.startswith("https://"):
                origins.add(host)
            else:
                origins.add(f"https://{host}")

    return sorted(origins)


app = FastAPI(title="AI Finance Voice Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    latency_ms: int
    grounded: bool


class PlaidLinkTokenRequest(BaseModel):
    user_id: str


class PlaidPublicTokenRequest(BaseModel):
    public_token: str


@app.get("/health")
@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
@app.post("/api/query", response_model=QueryResponse)
def query_handler(payload: QueryRequest) -> QueryResponse:
    started = time.time()
    answer = answer_query(payload.query)
    elapsed_ms = int((time.time() - started) * 1000)
    return QueryResponse(answer=answer, latency_ms=elapsed_ms, grounded=True)


@app.post("/plaid/create_link_token")
@app.post("/api/plaid/create_link_token")
def create_link_token(payload: PlaidLinkTokenRequest) -> dict[str, str]:
    try:
        client = get_plaid_client()
        token = client.create_link_token(payload.user_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"link_token": token}


@app.post("/plaid/exchange_token")
@app.post("/api/plaid/exchange_token")
def exchange_token(payload: PlaidPublicTokenRequest) -> dict[str, str]:
    try:
        client = get_plaid_client()
        access_token = client.exchange_public_token(payload.public_token)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    store_access_token(access_token)
    return {"status": "ok"}


@app.get("/plaid/transactions")
@app.get("/api/plaid/transactions")
def plaid_transactions() -> dict[str, object]:
    access_token = get_access_token()
    if not access_token:
        return {"transactions": []}

    try:
        client = get_plaid_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    response = client.get_transactions(access_token, start_date="2024-01-01", end_date="2024-12-31")
    normalized = sync_transactions(response.get("transactions", []))
    return {"transactions": normalized, "connected": True}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
