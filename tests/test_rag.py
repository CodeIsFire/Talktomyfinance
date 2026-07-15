from agents.orchestrator import answer_query
from rag.retrieve import retrieve


def test_retrieve_returns_relevant_kb_chunks_for_subscription_query():
    chunks = retrieve("what counts as a subscription")
    assert chunks
    assert any("subscription" in chunk["text"].lower() for chunk in chunks)


def test_orchestrator_uses_kb_context_for_grounded_answer():
    response = answer_query("what counts as a subscription")
    assert response
    assert "subscription" in response.lower() or "kb" in response.lower()
