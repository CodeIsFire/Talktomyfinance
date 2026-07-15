from __future__ import annotations

from typing import Any

import pandas as pd


def analyze(transactions: list[dict[str, Any]]) -> dict[str, Any]:
    if not transactions:
        return {
            "total_spend": 0.0,
            "total_income": 0.0,
            "net": 0.0,
            "transaction_count": 0,
            "category_breakdown": {},
            "top_merchants": {},
        }

    frame = pd.DataFrame(transactions)
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    frame["category"] = frame["category"].fillna("").astype(str)
    frame["merchant"] = frame["merchant"].fillna("").astype(str)

    expenses = frame[frame["category"].str.lower() != "income"].copy()
    income = frame[frame["category"].str.lower() == "income"].copy()

    category_breakdown = (
        expenses.groupby("category")["amount"].sum().sort_values(ascending=False).round(2).to_dict()
    )
    top_merchants = (
        expenses.groupby("merchant")["amount"].sum().sort_values(ascending=False).head(5).round(2).to_dict()
    )

    return {
        "total_spend": round(float(expenses["amount"].sum()), 2),
        "total_income": round(float(income["amount"].sum()), 2),
        "net": round(float(income["amount"].sum() - expenses["amount"].sum()), 2),
        "transaction_count": int(len(expenses)),
        "category_breakdown": {key: round(float(value), 2) for key, value in category_breakdown.items()},
        "top_merchants": {key: round(float(value), 2) for key, value in top_merchants.items()},
    }
