from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def format_for_speech(text: str) -> str:
    formatted = text
    formatted = re.sub(r"\$(\d+(?:,\d{3})*(?:\.\d+)?)", lambda m: f"{m.group(1)} dollars", formatted)
    formatted = re.sub(r"\b(\d{4}-\d{2}-\d{2})\b", lambda m: _format_date(m.group(1)), formatted)
    formatted = re.sub(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", lambda m: m.group(1).replace("@", " at "), formatted)
    return formatted


def _format_date(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.strftime("%B %-d, %Y")
    except ValueError:
        return value
