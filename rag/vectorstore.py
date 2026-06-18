
from __future__ import annotations

from functools import lru_cache

from rag.retriever import StatuteRetriever


@lru_cache(maxsize=1)
def get_retriever() -> StatuteRetriever:
    return StatuteRetriever()
