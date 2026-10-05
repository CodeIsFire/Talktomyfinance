from fastapi.testclient import TestClient

from app import _allowed_origins, app


def test_query_endpoint_returns_answer_payload(monkeypatch):
    monkeypatch.setattr('app.answer_query', lambda _query: 'mock answer')
    client = TestClient(app)
    response = client.post('/query', json={'query': 'what counts as a subscription'})
    assert response.status_code == 200
    payload = response.json()
    assert 'answer' in payload
    assert 'latency_ms' in payload
    assert 'grounded' in payload
    assert isinstance(payload['latency_ms'], int)


def test_query_endpoint_with_api_prefix_returns_answer_payload(monkeypatch):
    monkeypatch.setattr('app.answer_query', lambda _query: 'mock answer')
    client = TestClient(app)
    response = client.post('/api/query', json={'query': 'what counts as a subscription'})
    assert response.status_code == 200


def test_health_endpoint_available_with_and_without_api_prefix():
    client = TestClient(app)
    health = client.get('/health')
    api_health = client.get('/api/health')
    assert health.status_code == 200
    assert api_health.status_code == 200
    assert health.json() == {'status': 'ok'}
    assert api_health.json() == {'status': 'ok'}


def test_allowed_origins_includes_configured_and_vercel_hosts(monkeypatch):
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', 'https://project-6apdz.vercel.app, https://finance.example.com ')
    monkeypatch.setenv('VERCEL_PROJECT_PRODUCTION_URL', 'project-6apdz.vercel.app')
    monkeypatch.setenv('VERCEL_URL', 'project-6apdz-git-main.vercel.app')

    origins = _allowed_origins()

    assert 'http://localhost:3000' in origins
    assert 'http://127.0.0.1:3000' in origins
    assert 'https://project-6apdz.vercel.app' in origins
    assert 'https://finance.example.com' in origins
    assert 'https://project-6apdz-git-main.vercel.app' in origins
