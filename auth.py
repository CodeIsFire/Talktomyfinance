"""Bearer-token guard for the endpoints that touch a linked bank account.

The Plaid endpoints link an account, store its access token and read its
transactions. None of them authenticated the caller, and the store holds a
single shared token rather than one per user -- so anyone who could reach
GET /plaid/transactions got whichever account was linked most recently.

This module is the stopgap: one shared operator token, checked with
compare_digest, on the three /plaid/* routes. It is deliberately NOT a user
system. Per-user accounts -- sessions, a token per user_id, transactions
scoped to the caller -- is the real fix, and until it exists this app should
be treated as single-tenant and run somewhere only its owner can reach.

Set API_TOKEN to enable. Blank leaves the routes open, which is the test
suite and a local checkout with Plaid in sandbox; blank is checked at import
of the setting rather than baked in, so turning it on needs no code change.
"""
from __future__ import annotations

import hmac
import os

from fastapi import HTTPException, Request

API_TOKEN = os.getenv("API_TOKEN", "")


def _bearer(header: str) -> str:
    """The token out of an Authorization header, or "" for anything that is
    not a well-formed Bearer. The scheme is case-insensitive, per RFC 7235."""
    scheme, _, token = (header or "").partition(" ")
    return token.strip() if scheme.lower() == "bearer" else ""


def require_auth(request: Request) -> None:
    """FastAPI dependency. Declared with
    `dependencies=[Depends(require_auth)]`, since it injects nothing."""
    if not API_TOKEN:
        return

    presented = _bearer(request.headers.get("Authorization", ""))
    if not presented or not hmac.compare_digest(presented, API_TOKEN):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
