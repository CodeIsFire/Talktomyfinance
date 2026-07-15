from fastapi.testclient import TestClient

from app import app


def test_query_endpoint_returns_answer_payload():
    client = TestClient(app)
    response = client.post('/query', json={'query': 'what counts as a subscription'})
    assert response.status_code == 200
    payload = response.json()
    assert 'answer' in payload
    assert 'latency_ms' in payload
    assert 'grounded' in payload
    assert isinstance(payload['latency_ms'], int)
