from __future__ import annotations

import time
from typing import Any


class LatencyLogger:
    def __init__(self) -> None:
        self.steps: list[tuple[str, float]] = []

    def mark(self, step: str) -> None:
        self.steps.append((step, time.time()))

    def elapsed(self, start: float, end: float) -> float:
        return round(end - start, 3)

    def summary(self) -> str:
        if len(self.steps) < 2:
            return ""
        total = self.elapsed(self.steps[0][1], self.steps[-1][1])
        parts = [f"{name}: {self.elapsed(prev, current):.3f}s" for (name, current), (_, prev) in zip(self.steps[1:], self.steps)]
        return f"round_trip={total:.3f}s | " + " | ".join(parts)
