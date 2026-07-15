from agents.finance_agent import analyze
from agents.research_agent import get_transactions


def test_last_year_query_returns_rows_in_last_year_window():
    rows = get_transactions("top merchant last year")
    assert rows


def test_category_query_filters_transactions():
    rows = get_transactions("how much did I spend on subscriptions last month")
    assert rows
    assert all(row["category"] == "Subscriptions" for row in rows)


def test_merchant_query_filters_transactions():
    rows = get_transactions("show me spending at Starbucks this month")
    assert rows
    assert all("Starbucks" in row["merchant"] for row in rows)


def test_analysis_returns_summary_shape():
    rows = get_transactions("what did I spend on groceries")
    summary = analyze(rows)
    assert summary["transaction_count"] == len(rows)
    assert summary["total_spend"] >= 0
    assert summary["category_breakdown"]
