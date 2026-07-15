from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def check_grounding(answer: str, retrieved_data: list[dict[str, Any]], query: str) -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        numbers_in_answer = re.findall(r"\$?\d+(?:\.\d+)?", answer)
        numbers_in_context = re.findall(r"\$?\d+(?:\.\d+)?", json.dumps(retrieved_data))
        passed = all(number in numbers_in_context for number in numbers_in_answer)
        return {
            "passed": passed,
            "reason": "No Groq API key available; fallback numeric consistency check used." if passed else "Answer contains numbers not found in retrieved data.",
            "query": query,
        }

    safe_data = []
    for item in retrieved_data:
        safe_item = {}
        for key, value in item.items():
            if hasattr(value, "to_pydatetime"):
                safe_item[key] = value.to_pydatetime().isoformat()
            elif isinstance(value, (dict, list)):
                safe_item[key] = value
            else:
                safe_item[key] = value
        safe_data.append(safe_item)

    prompt = (
        "You are a strict grounding checker. For the given answer and retrieved evidence, determine whether every numeric value in the answer is supported by the retrieved data. "
        "Respond with JSON: {\"passed\": true/false, \"reason\": \"...\"}.\n\n"
        f"Query: {query}\n\nAnswer: {answer}\n\nRetrieved data: {json.dumps(safe_data, indent=2)}"
    )

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a grounding checker."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 160,
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()["choices"][0]["message"]["content"].strip()
        parsed = json.loads(payload)
        return {"passed": bool(parsed.get("passed", False)), "reason": parsed.get("reason", "No reason provided."), "query": query}
    except Exception as exc:
        return {"passed": False, "reason": f"Grounding check failed: {exc}", "query": query}
