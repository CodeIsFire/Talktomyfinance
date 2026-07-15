from agents.orchestrator import answer_query


def test_grounding_check_flags_hallucinated_number():
    answer = "You spent $999,999 last month."
    from eval.check_grounding import check_grounding

    result = check_grounding(answer, [{"amount": 10.0, "category": "Groceries"}], "hallucination test")
    assert result["passed"] is False
    assert "not found" in result["reason"].lower() or "numbers" in result["reason"].lower()


def test_orchestrator_logs_evaluation_entry():
    answer_query("what counts as a subscription")
    with open("eval/logs.jsonl", encoding="utf-8") as handle:
        lines = [line for line in handle.read().splitlines() if line]
    assert lines
