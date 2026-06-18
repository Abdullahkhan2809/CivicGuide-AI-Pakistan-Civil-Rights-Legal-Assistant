from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from config import PROCEDURES_DIR


Procedure = dict[str, Any]


@lru_cache(maxsize=8)
def load_procedure_file(category: str) -> dict[str, Any]:
    safe_category = category.strip().lower()
    path = PROCEDURES_DIR / f"{safe_category}.json"
    if not path.exists():
        return {"category": safe_category, "procedures": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def get_procedure(category: str, subcategory: str) -> Procedure | None:
    data = load_procedure_file(category)
    procedure = data.get("procedures", {}).get(subcategory)
    if isinstance(procedure, dict):
        return procedure
    return None


def list_procedure_paths() -> list[Path]:
    if not PROCEDURES_DIR.exists():
        return []
    return sorted(PROCEDURES_DIR.glob("*.json"))


def procedure_to_answer(procedure: Procedure) -> str:
    steps = "\n".join(
        f"{item['step']}. {item['action']} ({item['timeline']})\n   {item['details']}"
        for item in procedure.get("steps", [])
    )
    docs = "\n".join(
        f"- {item['name_en']} - {item['source']}"
        for item in procedure.get("required_documents", [])
    )
    office = procedure.get("office", {})
    return (
        f"{procedure['title']}\n\n"
        f"Steps:\n{steps}\n\n"
        f"Required documents:\n{docs}\n\n"
        f"Office: {office.get('name', 'Relevant local office')} "
        f"({office.get('jurisdiction', 'local jurisdiction')})\n"
        f"Estimated cost: {procedure.get('estimated_cost', 'Confirm locally')}\n"
        f"Estimated timeline: {procedure.get('estimated_timeline', 'Varies by case')}\n"
        f"Relevant law: {procedure.get('relevant_law', 'Verify with the relevant forum')}"
    )


def answer_procedure_question(procedure: Procedure, question: str) -> str:
    lowered = question.lower()
    office = procedure.get("office", {})

    if any(word in lowered for word in ["fee", "fees", "cost", "price", "expense", "stamp"]):
        return (
            f"The estimated cost is {procedure.get('estimated_cost', 'not specified in the procedure file')}. "
            "Confirm the exact filing fee at the relevant office because district charges can vary."
        )

    if any(word in lowered for word in ["time", "timeline", "long", "days", "months", "duration"]):
        return f"The estimated timeline is {procedure.get('estimated_timeline', 'not specified in the procedure file')}."

    if any(word in lowered for word in ["office", "where", "visit", "go", "file", "submit"]):
        return (
            f"You should visit the {office.get('name', 'relevant local office')}. "
            f"Jurisdiction: {office.get('jurisdiction', 'local jurisdiction')}. "
            f"{office.get('note', '')}"
        ).strip()

    if any(word in lowered for word in ["document", "documents", "bring", "required", "paper", "papers"]):
        docs = "\n".join(
            f"- {item['name_en']}: {item['source']}"
            for item in procedure.get("required_documents", [])
        )
        return f"Required documents:\n{docs}" if docs else "No required documents are listed for this procedure yet."

    if any(word in lowered for word in ["law", "section", "ordinance", "act", "legal"]):
        return f"Relevant law: {procedure.get('relevant_law', 'not specified in the procedure file')}."

    if any(word in lowered for word in ["step", "steps", "next", "do", "process", "procedure"]):
        steps = "\n".join(
            f"{item['step']}. {item['action']} - {item['details']} Timeline: {item['timeline']}"
            for item in procedure.get("steps", [])
        )
        return (
            f"Based on your situation, here is the action plan for {procedure['title']}:\n{steps}"
            if steps
            else "No steps are listed for this procedure yet."
        )

    if any(word in lowered for word in ["notice", "letter", "landlord"]):
        matching_steps = [
            item for item in procedure.get("steps", [])
            if "notice" in item.get("action", "").lower() or "notice" in item.get("details", "").lower()
        ]
        if matching_steps:
            item = matching_steps[0]
            return f"{item['action']}. {item['details']} Timeline: {item['timeline']}."

    return procedure_to_answer(procedure)
