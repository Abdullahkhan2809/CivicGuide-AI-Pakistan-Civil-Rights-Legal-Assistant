
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from config import LEGAL_DOMAINS, MAX_CONTEXT_CHUNKS, VECTOR_DB_DIR
from rag.ingest import StatuteChunk, load_statute_cache, load_text_json_chunks


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9']+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "been",
    "but",
    "by",
    "do",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "his",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "not",
    "of",
    "or",
    "our",
    "she",
    "so",
    "that",
    "the",
    "their",
    "them",
    "they",
    "this",
    "to",
    "was",
    "we",
    "what",
    "when",
    "where",
    "who",
    "with",
    "without",
    "you",
    "your",
}


@dataclass(frozen=True)
class RetrievedChunk:
    source: str
    page: int
    text: str
    score: float


def tokenize(text: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token.lower() not in STOPWORDS and len(token) > 2
    ]


def _domain_sources(domain: str) -> set[str]:
    return set(LEGAL_DOMAINS.get(domain, {}).get("laws", []))


class StatuteRetriever:
    def __init__(self, chunks: list[StatuteChunk] | None = None) -> None:
        self.chunks = chunks or load_text_json_chunks() or load_statute_cache()
        self.doc_tokens = [Counter(tokenize(chunk.text + " " + chunk.source)) for chunk in self.chunks]
        document_frequency: Counter[str] = Counter()
        for tokens in self.doc_tokens:
            document_frequency.update(tokens.keys())
        total = max(1, len(self.chunks))
        self.idf = {
            token: math.log((total + 1) / (count + 0.5)) + 1
            for token, count in document_frequency.items()
        }

    def search(self, query: str, domain: str = "property", limit: int = MAX_CONTEXT_CHUNKS) -> list[RetrievedChunk]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        preferred_sources = _domain_sources(domain)
        scored: list[RetrievedChunk] = []
        for chunk, tokens in zip(self.chunks, self.doc_tokens):
            score = 0.0
            for token in query_tokens:
                score += tokens[token] * self.idf.get(token, 1.0)
            if chunk.source in preferred_sources:
                score *= 2.5
            if score > 0:
                scored.append(
                    RetrievedChunk(
                        source=chunk.source,
                        page=chunk.page,
                        text=chunk.text,
                        score=round(score, 3),
                    )
                )

        scored.sort(key=lambda item: item.score, reverse=True)
        if scored:
            return scored[:limit]

        return self._search_chroma(query, limit)

    def _search_chroma(self, query: str, limit: int) -> list[RetrievedChunk]:
        if not VECTOR_DB_DIR.exists():
            return []
        try:
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings

            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"local_files_only": True},
            )
            store = Chroma(
                collection_name="civicguide_statutes",
                embedding_function=embeddings,
                persist_directory=str(VECTOR_DB_DIR),
            )
            docs = store.similarity_search_with_score(query, k=limit)
        except Exception:
            return []

        results: list[RetrievedChunk] = []
        for document, score in docs:
            metadata = document.metadata or {}
            results.append(
                RetrievedChunk(
                    source=str(metadata.get("source", "ChromaDB")),
                    page=int(metadata.get("page", 1)),
                    text=document.page_content,
                    score=round(float(score), 3),
                )
            )
        return results
