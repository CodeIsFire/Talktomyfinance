from __future__ import annotations

import subprocess
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def speak(text: str) -> None:
    subprocess.run(["say", text], check=False)


def main() -> None:
    print("Voice loop ready. Type 'hello world' to trigger speech output.")
    while True:
        try:
            text = input("Say something (or 'quit'): ").strip()
        except KeyboardInterrupt:
            break
        if not text:
            continue
        if text.lower() in {"quit", "exit"}:
            break
        print(f"You said: {text}")
        if "hello world" in text.lower():
            speak("hello world")
            print("Spoken: hello world")


if __name__ == "__main__":
    main()
