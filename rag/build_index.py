from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
KB_DIR = ROOT / "data" / "kb"
INDEX_PATH = ROOT / "rag" / "kb_index.json"


def build_index() -> list[dict[str, Any]]:
    model = SentenceTransformer("all-MiniLM-L6-v2")
    docs: list[dict[str, Any]] = []
    for path in sorted(KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append({"id": path.stem, "source": path.name, "text": text})

    embeddings = model.encode([doc["text"] for doc in docs], convert_to_numpy=True)
    for doc, embedding in zip(docs, embeddings):
        doc["embedding"] = embedding.tolist()

    INDEX_PATH.write_text(json.dumps(docs, indent=2), encoding="utf-8")
    return docs


if __name__ == "__main__":
    build_index()
    print(f"Built index with {len(build_index())} documents")
