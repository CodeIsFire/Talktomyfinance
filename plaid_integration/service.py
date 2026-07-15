from __future__ import annotations

import hashlib
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
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def store_access_token(access_token: str) -> None:
    payload = _ensure_store()
    payload["access_token"] = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
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
