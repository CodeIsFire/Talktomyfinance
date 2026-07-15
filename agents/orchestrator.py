from __future__ import annotations

import json
from pathlib import Path

from agents.finance_agent import analyze
from agents.research_agent import get_transactions
from agents.editor_agent import to_natural_language
from agents.latency import LatencyLogger
from eval.check_grounding import check_grounding

LOG_PATH = Path(__file__).resolve().parents[1] / "eval" / "logs.jsonl"


def answer_query(query: str) -> str:
    logger = LatencyLogger()
    logger.mark("start")

    transactions = get_transactions(query)
    logger.mark("research")

    summary = analyze(transactions)
    logger.mark("finance")

    answer = to_natural_language(summary, query=query)
    logger.mark("editor")

    evaluation = check_grounding(answer, transactions, query)
    logger.mark("eval")

    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"query": query, "answer": answer, "latency": logger.summary(), **evaluation}) + "\n")

    print(f"[latency] {logger.summary()}")
    return answer
