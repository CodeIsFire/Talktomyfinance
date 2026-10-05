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
    production_host = 'project-6apdz.vercel.app'
    custom_host = 'finance.example.com'
    preview_host = 'project-6apdz-git-main.vercel.app'
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', f'https://{production_host}, https://{custom_host} ')
    monkeypatch.setenv('VERCEL_PROJECT_PRODUCTION_URL', production_host)
    monkeypatch.setenv('VERCEL_URL', preview_host)

    origins = _allowed_origins()

    assert 'http://localhost:3000' in origins
    assert 'http://127.0.0.1:3000' in origins
    assert f'https://{production_host}' in origins
    assert f'https://{custom_host}' in origins
    assert f'https://{preview_host}' in origins
