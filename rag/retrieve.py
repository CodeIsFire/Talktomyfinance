from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "rag" / "kb_index.json"
MODEL_NAME = "all-MiniLM-L6-v2"


def _load_index() -> list[dict[str, Any]]:
    if not INDEX_PATH.exists():
        return []
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def retrieve(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    docs = _load_index()
    if not docs:
        return []

    try:
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError:
        query_tokens = {token for token in re.findall(r"[a-zA-Z]+", query.lower()) if len(token) > 2}
        if not query_tokens:
            return docs[:top_k]

        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in docs:
            text_tokens = set(re.findall(r"[a-zA-Z]+", doc.get("text", "").lower()))
            overlap = len(query_tokens & text_tokens)
            if overlap > 0:
                scored.append((float(overlap), doc))

        if not scored:
            return docs[:top_k]

        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query], convert_to_numpy=True)[0]

    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in docs:
        embedding = np.array(doc["embedding"], dtype=float)
        similarity = float(np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding)))
        scored.append((similarity, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]
