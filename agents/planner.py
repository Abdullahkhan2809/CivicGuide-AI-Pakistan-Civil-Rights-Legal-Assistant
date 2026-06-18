
from __future__ import annotations

import os

from groq import Groq

from agents.reviewer import append_disclaimer
from rag.prompts import SYSTEM_PROMPT, build_answer_prompt
from rag.retriever import RetrievedChunk
from utils.roadmap import default_action_plan


def _groq_answer(case_text: str, question: str, chunks: list[RetrievedChunk]) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=0.2,
        max_tokens=700,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_answer_prompt(case_text, question, chunks)},
        ],
    )
    return response.choices[0].message.content


def _fallback_answer(case_text: str, question: str, domain: str, chunks: list[RetrievedChunk]) -> str:
    plan = default_action_plan(domain, case_text + " " + question)
    references = "\n".join(
        f"- {chunk.source}, page {chunk.page}" for chunk in chunks[:3]
    ) or "- No statute excerpt matched strongly; verify with the relevant office."
    steps = "\n".join(f"{idx}. {step}" for idx, step in enumerate(plan, start=1))
    return (
        "Based on the facts you shared, start with the lowest-friction written record and "
        "then escalate to the relevant forum if the other party does not respond.\n\n"
        f"{steps}\n\n"
        "For filing fees, local offices often charge a nominal amount and the exact figure "
        "can vary by district, so confirm at the filing counter before submission.\n\n"
        f"Relevant references:\n{references}"
    )


def answer_question(case_text: str, question: str, domain: str, chunks: list[RetrievedChunk]) -> str:
    try:
        answer = _groq_answer(case_text, question, chunks)
    except Exception:
        answer = None
    return append_disclaimer(answer or _fallback_answer(case_text, question, domain, chunks))
