from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID", "")
PLAID_SECRET = os.getenv("PLAID_SECRET", "")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox").lower()


class PlaidClientWrapper:
    def __init__(self) -> None:
        self.client_id = PLAID_CLIENT_ID
        self.secret = PLAID_SECRET
        self.base_url = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com",
        }.get(PLAID_ENV, "https://sandbox.plaid.com")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.client_id or not self.secret:
            raise RuntimeError("Plaid credentials are not configured")

        response = requests.post(f"{self.base_url}{path}", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def create_link_token(self, user_id: str) -> str:
        payload = {
            "client_id": self.client_id,
            "secret": self.secret,
            "user": {"client_user_id": user_id},
            "client_name": "AI Finance Voice Assistant",
            "products": ["transactions"],
            "country_codes": ["US"],
            "language": "en",
        }
        data = self._post("/link/token/create", payload)
        return data["link_token"]

    def exchange_public_token(self, public_token: str) -> str:
        payload = {
            "client_id": self.client_id,
            "secret": self.secret,
            "public_token": public_token,
        }
        data = self._post("/item/public_token/exchange", payload)
        return data["access_token"]

    def get_transactions(self, access_token: str, start_date: str, end_date: str) -> dict[str, Any]:
        payload = {
            "client_id": self.client_id,
            "secret": self.secret,
            "access_token": access_token,
            "start_date": start_date,
            "end_date": end_date,
        }
        return self._post("/transactions/get", payload)


def get_plaid_client() -> PlaidClientWrapper:
    return PlaidClientWrapper()
