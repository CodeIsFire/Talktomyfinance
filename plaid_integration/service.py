from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_SOURCE = os.getenv("DATA_SOURCE", "mock")
STORE_PATH = ROOT / "plaid_integration" / "store.json"


def _ensure_store() -> dict[str, Any]:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    return {"access_token": None, "transactions": []}


def _write_store(payload: dict[str, Any]) -> None:
    """Writes the store 0600. It holds a live Plaid access token, which is a
    bearer credential for someone's bank account -- it should not be readable
    by other accounts on the machine. Created restricted rather than chmod'd
    afterwards, so there is no window where the file exists world-readable."""
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(STORE_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def store_access_token(access_token: str) -> None:
    """Stores the token as issued.

    This used to store sha256(access_token), which reads like a precaution and
    was in fact a bug: get_access_token() hands its return value straight to
    the Plaid API as the access token, so a digest could never authenticate
    anything -- /plaid/transactions was guaranteed to fail against real Plaid.
    A hash is the right shape for something you only ever compare; this is
    something the app has to *present*, so it has to survive the round trip.

    Confidentiality therefore comes from where it is kept, not from a one-way
    function it cannot use: 0600 in _write_store, and store.json is
    gitignored. Encryption at rest would need a key this app has nowhere to
    put yet -- that belongs with real per-user accounts (see app.py's note on
    the single shared token)."""
    payload = _ensure_store()
    payload["access_token"] = access_token
    _write_store(payload)


def get_access_token() -> str | None:
    payload = _ensure_store()
    return payload.get("access_token")


def normalize_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    amount = float(transaction.get("amount", 0.0))
    signed_amount = abs(amount)
    if amount < 0:
        signed_amount = abs(amount)

    category = transaction.get("personal_finance_category", {}).get("primary", "")
    mapped_category = {
        "FOOD_AND_DRINK": "Dining",
        "TRAVEL": "Travel",
        "TRANSPORTATION": "Transportation",
        "ENTERTAINMENT": "Entertainment",
        "INCOME": "Income",
        "HOME_IMPROVEMENT": "Housing",
        "RENT_AND_UTILITIES": "Utilities",
        "SHOPPING": "Shopping",
        "HEALTH_AND_WELLNESS": "Health",
        "SUBSCRIPTIONS": "Subscriptions",
    }.get(category, "Other")

    if category == "INCOME" or amount < 0:
        mapped_category = "Income"

    return {
        "date": transaction.get("date", ""),
        "merchant": transaction.get("merchant_name") or "Unknown",
        "category": mapped_category,
        "amount": signed_amount,
    }


def sync_transactions(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [normalize_transaction(item) for item in transactions]
    payload = _ensure_store()
    payload["transactions"] = normalized
    _write_store(payload)
    return normalized


def get_synced_transactions() -> list[dict[str, Any]]:
    payload = _ensure_store()
    return payload.get("transactions", [])
