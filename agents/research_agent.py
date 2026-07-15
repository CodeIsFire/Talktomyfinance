from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

from plaid_integration.service import get_synced_transactions

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "transactions.csv"
DATA_SOURCE = os.getenv("DATA_SOURCE", "mock")

STOP_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "check",
    "compare",
    "comparison",
    "did",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "last",
    "list",
    "me",
    "month",
    "much",
    "my",
    "on",
    "show",
    "spend",
    "spending",
    "the",
    "this",
    "to",
    "top",
    "transactions",
    "transaction",
    "week",
    "what",
    "year",
    "yesterday",
    "today",
    "up",
}


def _load_dataframe() -> pd.DataFrame:
    if DATA_SOURCE == "plaid":
        transactions = get_synced_transactions()
        if transactions:
            frame = pd.DataFrame(transactions)
            frame["date"] = pd.to_datetime(frame["date"])
            return frame

    frame = pd.read_csv(DATA_PATH)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def _extract_keywords(query: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z]+", query.lower())
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 2]


def _build_date_mask(frame: pd.DataFrame, query: str) -> pd.Series:
    if "last month" in query.lower():
        latest = frame["date"].max()
        start = latest - pd.DateOffset(months=1)
        return (frame["date"] >= start) & (frame["date"] <= latest)

    if "this month" in query.lower():
        latest = frame["date"].max()
        start = latest.replace(day=1)
        return (frame["date"] >= start) & (frame["date"] <= latest)

    if "last week" in query.lower():
        latest = frame["date"].max()
        start = latest - pd.DateOffset(weeks=1)
        return (frame["date"] >= start) & (frame["date"] <= latest)

    if "this week" in query.lower():
        latest = frame["date"].max()
        start = latest - pd.DateOffset(days=latest.weekday())
        return (frame["date"] >= start) & (frame["date"] <= latest)

    if "last year" in query.lower():
        latest = frame["date"].max()
        start = latest - pd.DateOffset(years=1)
        return (frame["date"] >= start) & (frame["date"] <= latest)

    if "this year" in query.lower():
        latest = frame["date"].max()
        start = latest.replace(month=1, day=1)
        return (frame["date"] >= start) & (frame["date"] <= latest)

    if "today" in query.lower():
        latest = frame["date"].max()
        return (frame["date"] == latest)

    if "yesterday" in query.lower():
        latest = frame["date"].max()
        start = latest - pd.DateOffset(days=1)
        return (frame["date"] >= start) & (frame["date"] <= latest)

    return pd.Series(True, index=frame.index)


def _build_keyword_mask(frame: pd.DataFrame, query: str) -> tuple[pd.Series, pd.Series]:
    keywords = _extract_keywords(query)
    if not keywords:
        return pd.Series(True, index=frame.index), pd.Series(True, index=frame.index)

    category_values = frame["category"].fillna("").astype(str).str.lower()
    merchant_values = frame["merchant"].fillna("").astype(str).str.lower()

    category_mask = pd.Series(False, index=frame.index)
    merchant_mask = pd.Series(False, index=frame.index)

    for keyword in keywords:
        category_mask |= category_values.str.contains(keyword, regex=False, na=False)
        merchant_mask |= merchant_values.str.contains(keyword, regex=False, na=False)

    if any(token in {"starbucks", "uber", "amazon", "netflix", "delta", "target", "walmart", "whole", "foods", "trader", "joe", "city", "water", "verizon", "shell", "airbnb", "spotify", "cvs"} for token in keywords):
        merchant_mask = pd.Series(False, index=frame.index)
        for keyword in keywords:
            if keyword in {"starbucks", "uber", "amazon", "netflix", "delta", "target", "walmart", "whole", "foods", "trader", "joe", "city", "water", "verizon", "shell", "airbnb", "spotify", "cvs"}:
                merchant_mask |= merchant_values.str.contains(keyword, regex=False, na=False)

    return category_mask, merchant_mask


def get_transactions(query: str) -> list[dict[str, Any]]:
    frame = _load_dataframe()
    date_mask = _build_date_mask(frame, query)
    category_mask, merchant_mask = _build_keyword_mask(frame, query)

    keyword_matches = category_mask | merchant_mask
    combined_mask = date_mask & keyword_matches

    if combined_mask.any():
        filtered = frame.loc[combined_mask].copy()
        filtered = filtered.sort_values("date", ascending=False)
        return filtered.to_dict(orient="records")

    filtered = frame.loc[date_mask].copy()
    filtered = filtered.sort_values("date", ascending=False)
    return filtered.to_dict(orient="records")
