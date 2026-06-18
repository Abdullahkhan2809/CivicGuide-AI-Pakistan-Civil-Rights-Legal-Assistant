
from __future__ import annotations

from config import DISCLAIMER


def append_disclaimer(answer: str) -> str:
    if "legal advice" in answer.lower():
        return answer
    return f"{answer}\n\n_{DISCLAIMER}_"
