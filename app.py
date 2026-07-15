import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.orchestrator import answer_query
from plaid_integration.client import get_plaid_client
from plaid_integration.service import get_access_token, get_synced_transactions, store_access_token, sync_transactions

app = FastAPI(title="AI Finance Voice Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query_handler(payload: QueryRequest) -> QueryResponse:
    started = time.time()
    answer = answer_query(payload.query)
    elapsed_ms = int((time.time() - started) * 1000)
    return QueryResponse(answer=answer, latency_ms=elapsed_ms, grounded=True)


@app.post("/plaid/create_link_token")
def create_link_token(payload: PlaidLinkTokenRequest) -> dict[str, str]:
    client = get_plaid_client()
    token = client.create_link_token(payload.user_id)
    return {"link_token": token}


@app.post("/plaid/exchange_token")
def exchange_token(payload: PlaidPublicTokenRequest) -> dict[str, str]:
    client = get_plaid_client()
    access_token = client.exchange_public_token(payload.public_token)
    store_access_token(access_token)
    return {"status": "ok"}


@app.get("/plaid/transactions")
def plaid_transactions() -> dict[str, object]:
    access_token = get_access_token()
    if not access_token:
        return {"transactions": []}

    client = get_plaid_client()
    response = client.get_transactions(access_token, start_date="2024-01-01", end_date="2024-12-31")
    normalized = sync_transactions(response.get("transactions", []))
    return {"transactions": normalized, "connected": True}
