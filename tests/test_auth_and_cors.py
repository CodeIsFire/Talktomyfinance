"""The two controls in front of the bank-account endpoints.

CORS first, because the failure it prevents is the non-obvious one: with
allow_credentials=True, allow_origins=["*"] does not make Starlette send a
literal "*" -- it echoes whichever Origin asked. Any site the user browsed
could then call GET /plaid/transactions with credentials and read the reply.
The regex below is what keeps "reachable from my phone on the same wifi" from
also meaning "reachable from every website on the internet".

Then the bearer token, which is a stopgap rather than a user system: one
shared secret, no per-user scoping. The single-shared-token limitation is
asserted here too, so the day someone adds real accounts these tests fail
loudly instead of passing over a design that changed underneath them.
"""
import importlib

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app

EVIL = "https://evil.example"
LOCAL = "http://localhost:3000"
LAN = "http://192.168.1.42:5173"


@pytest.fixture
def client():
    return TestClient(app)


def _cors_origin(client, origin):
    """The Access-Control-Allow-Origin the server answers a preflight with,
    or None when it declines to allow the origin at all."""
    resp = client.options(
        "/plaid/transactions",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    return resp.headers.get("access-control-allow-origin")


def test_a_third_party_origin_is_not_allowed(client):
    """The regression that matters: an arbitrary site must not be echoed back
    as an allowed credentialed origin."""
    assert _cors_origin(client, EVIL) is None


@pytest.mark.parametrize("origin", [LOCAL, "http://127.0.0.1:5173", LAN])
def test_local_and_lan_origins_are_allowed(client, origin):
    """The dev-server and same-wifi cases the wildcard was reaching for."""
    assert _cors_origin(client, origin) == origin


def test_credentials_are_allowed_only_alongside_a_specific_origin(client):
    """If the response ever carries credentials plus a literal "*", browsers
    reject it and the combination is meaningless -- assert we never emit it."""
    resp = client.options(
        "/plaid/transactions",
        headers={"Origin": LOCAL, "Access-Control-Request-Method": "GET"},
    )
    assert resp.headers.get("access-control-allow-credentials") == "true"
    assert resp.headers.get("access-control-allow-origin") != "*"


PLAID_ROUTES = [
    ("post", "/plaid/create_link_token", {"user_id": "u1"}),
    ("post", "/plaid/exchange_token", {"public_token": "public-sandbox-x"}),
    ("get", "/plaid/transactions", None),
]


@pytest.fixture
def token_configured(monkeypatch):
    """auth.API_TOKEN is read at import, so the module is reloaded with the
    variable set and app.py is re-imported to rebind the dependency onto the
    reloaded function. Reverted afterwards so the rest of the suite still
    sees the open, no-token app."""
    monkeypatch.setenv("API_TOKEN", "operator-token")
    import auth
    importlib.reload(auth)
    reloaded = importlib.reload(app_module)
    yield TestClient(reloaded.app)
    monkeypatch.delenv("API_TOKEN", raising=False)
    importlib.reload(auth)
    importlib.reload(app_module)


@pytest.mark.parametrize("method,path,body", PLAID_ROUTES)
def test_plaid_routes_reject_a_missing_token(token_configured, method, path, body):
    resp = getattr(token_configured, method)(path, **({"json": body} if body else {}))
    assert resp.status_code == 401
    assert resp.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("method,path,body", PLAID_ROUTES)
def test_plaid_routes_reject_a_wrong_token(token_configured, method, path, body):
    kwargs = {"headers": {"Authorization": "Bearer nope"}}
    if body:
        kwargs["json"] = body
    resp = getattr(token_configured, method)(path, **kwargs)
    assert resp.status_code == 401


def test_the_right_token_is_not_rejected(token_configured):
    """Not 401. What /plaid/transactions then does depends on whether an
    account is linked, which is test_plaid.py's subject, not this file's."""
    resp = token_configured.get(
        "/plaid/transactions", headers={"Authorization": "Bearer operator-token"}
    )
    assert resp.status_code != 401


def test_health_is_not_behind_the_token(token_configured):
    assert token_configured.get("/health").status_code == 200


def test_routes_stay_open_when_no_token_is_configured(client):
    """A local checkout against Plaid sandbox is not asked for a credential;
    this is what the rest of the suite relies on."""
    assert client.get("/plaid/transactions").status_code != 401
