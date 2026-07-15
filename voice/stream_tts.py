from __future__ import annotations

import subprocess
import time
from typing import Iterator

from voice.tts_format import format_for_speech


def stream_speak(text: str, delay: float = 0.15) -> None:
    words = text.split()
    for index, word in enumerate(words):
        if index == len(words) - 1:
            chunk = word
        else:
            chunk = f"{word}"
        subprocess.run(["say", format_for_speech(chunk)], check=False)
        time.sleep(delay)
