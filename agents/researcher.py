
from __future__ import annotations

from rag.vectorstore import get_retriever


def research_case(query: str, domain: str):
    return get_retriever().search(query=query, domain=domain)
