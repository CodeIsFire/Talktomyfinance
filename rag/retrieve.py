from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

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

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query], convert_to_numpy=True)[0]

    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in docs:
        embedding = np.array(doc["embedding"], dtype=float)
        similarity = float(np.dot(query_embedding, embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(embedding)))
        scored.append((similarity, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]
