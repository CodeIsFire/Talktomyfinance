from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from rag.retrieve import retrieve

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def to_natural_language(summary_dict: dict[str, Any], query: str | None = None) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        return (
            f"You spent ${summary_dict.get('total_spend', 0):.2f} across "
            f"{summary_dict.get('transaction_count', 0)} transactions."
        )

    kb_context = ""
    if query:
        kb_chunks = retrieve(query, top_k=3)
        if kb_chunks:
            kb_context = "\n\nKB context:\n" + "\n\n".join(
                f"- {chunk['source']}: {chunk['text'][:600]}"
                for chunk in kb_chunks
            )

    prompt = (
        "You are a concise finance assistant. Turn the following summary into a short voice-friendly response. "
        "Use the provided KB context whenever it helps answer the question and mention that it is grounded in the local knowledge base. "
        "Mention the most important numbers, keep it natural, and avoid bullet points.\n\n"
        f"Question: {query or ''}\n\n"
        f"Summary: {json.dumps(summary_dict, indent=2)}{kb_context}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful finance assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 140,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content or "I could not generate a response."
    except Exception:
        return (
            f"You spent ${summary_dict.get('total_spend', 0):.2f} across "
            f"{summary_dict.get('transaction_count', 0)} transactions."
        )
