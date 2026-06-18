from __future__ import annotations

import os
import re

from groq import Groq


URDU_RE = re.compile(r"[\u0600-\u06ff]")
URDU_REQUEST_RE = re.compile(
    r"\b(urdu|roman urdu|translate|translation|tarjuma|tarjumah|urdo|اردو|ترجمہ)\b",
    re.IGNORECASE,
)
ROMAN_URDU_RE = re.compile(
    r"\b(kya|kaise|kesay|kese|mujhe|mujhy|mera|meri|mere|batao|batain|karna|chahiye|haq|qanun|qanoon)\b",
    re.IGNORECASE,
)


def needs_urdu_translation(prompt: str) -> bool:
    """Return true when the user explicitly asks for Urdu or appears to write in Urdu/Roman Urdu."""
    return bool(
        URDU_RE.search(prompt)
        or URDU_REQUEST_RE.search(prompt)
        or ROMAN_URDU_RE.search(prompt)
    )


def translate_to_urdu(text: str) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not text.strip():
        return None

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=0.1,
        max_tokens=900,
        messages=[
            {
                "role": "system",
                "content": (
                    "Translate the supplied Pakistani legal information into clear, natural Urdu. "
                    "Preserve numbered steps, document names, law names, page references, and disclaimers. "
                    "Do not add new legal facts or advice."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def append_urdu_translation(answer: str, prompt: str) -> str:
    if not needs_urdu_translation(prompt) or "Urdu Translation" in answer:
        return answer

    try:
        translation = translate_to_urdu(answer)
    except Exception:
        translation = None

    if not translation:
        return (
            f"{answer}\n\n"
            "**Urdu Translation:**\n"
            "Urdu translation could not be generated right now. Please ask: `translate this into Urdu` after the answer."
        )

    return f"{answer}\n\n**Urdu Translation:**\n{translation}"
