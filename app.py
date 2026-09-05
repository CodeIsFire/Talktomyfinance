import os
import time
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.orchestrator import answer_query
from auth import require_auth
from plaid_integration.client import get_plaid_client
from plaid_integration.service import get_access_token, get_synced_transactions, store_access_token, sync_transactions

app = FastAPI(title="AI Finance Voice Assistant")

# Any localhost/127.0.0.1/[::1] port, plus private-range LAN addresses, so the
# Vite dev server and a phone on the same wifi can both reach this API.
#
# A regex rather than allow_origins=["*"]: with allow_credentials=True
# Starlette does not send a literal "*", it echoes whichever Origin asked,
# which turns every website the user visits into an allowed credentialed
# caller of these endpoints -- and these endpoints serve bank transactions.
# The wildcard reads as "dev convenience" and behaves as "any site on the
# internet may read this", so it cannot stay even in development.
#
# Set ALLOWED_ORIGINS (comma-separated) to pin exact origins in production.
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
_LOCAL_ORIGIN_RE = (
    r"^https?://("
    r"localhost|127\.0\.0\.1|\[::1\]"
    r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3}"
    r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r")(:\d+)?$"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=None if _ALLOWED_ORIGINS else _LOCAL_ORIGIN_RE,
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


@app.post("/plaid/create_link_token", dependencies=[Depends(require_auth)])
def create_link_token(payload: PlaidLinkTokenRequest) -> dict[str, str]:
    client = get_plaid_client()
    token = client.create_link_token(payload.user_id)
    return {"link_token": token}


@app.post("/plaid/exchange_token", dependencies=[Depends(require_auth)])
def exchange_token(payload: PlaidPublicTokenRequest) -> dict[str, str]:
    client = get_plaid_client()
    access_token = client.exchange_public_token(payload.public_token)
    store_access_token(access_token)
    return {"status": "ok"}


@app.get("/plaid/transactions", dependencies=[Depends(require_auth)])
def plaid_transactions() -> dict[str, object]:
    access_token = get_access_token()
    if not access_token:
        return {"transactions": []}

    client = get_plaid_client()
    response = client.get_transactions(access_token, start_date="2024-01-01", end_date="2024-12-31")
    normalized = sync_transactions(response.get("transactions", []))
    return {"transactions": normalized, "connected": True}
