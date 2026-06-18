
from __future__ import annotations

from rag.retriever import RetrievedChunk


SYSTEM_PROMPT = """You are CivicGuide AI, a Pakistani legal rights assistant.
Give practical, plain-language legal information grounded in the supplied statute excerpts.
Do not claim to be a lawyer, do not guarantee outcomes, and tell the user when a licensed advocate or relevant office should review their specific case.
Return concise, actionable guidance."""


def format_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "No matching statute excerpts were found."
    return "\n\n".join(
        f"[{idx}] {chunk.source}, page {chunk.page}: {chunk.text}"
        for idx, chunk in enumerate(chunks, start=1)
    )


def build_answer_prompt(case_text: str, question: str, chunks: list[RetrievedChunk]) -> str:
    return f"""Case details:
{case_text}

User question:
{question}

Relevant statute excerpts:
{format_context(chunks)}

Answer with:
1. Direct answer
2. Immediate next steps
3. Documents to carry
4. Relevant law references by source name and page where available"""
