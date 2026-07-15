from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.orchestrator import answer_query
from voice.stream_tts import stream_speak
from voice.tts_format import format_for_speech


def speak(text: str) -> None:
    stream_speak(text)


def main() -> None:
    print("Voice assistant ready. Type a finance question or 'quit'.")
    while True:
        try:
            query = input("Ask: ").strip()
        except KeyboardInterrupt:
            break
        if not query:
            continue
        if query.lower() in {"quit", "exit"}:
            break
        answer = answer_query(query)
        print(answer)
        speak(answer)


if __name__ == "__main__":
    main()
