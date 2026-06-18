from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


URDU_RE = re.compile(r"[\u0600-\u06ff]")
URDU_REQUEST_RE = re.compile(
    r"\b(urdu|roman urdu|translate|translation|tarjuma|tarjumah|urdo)\b|"
    r"\u0627\u0631\u062f\u0648|"
    r"\u062a\u0631\u062c\u0645\u06c1",
    re.IGNORECASE,
)
ROMAN_URDU_RE = re.compile(
    r"\b(kya|kaise|kesay|kese|mujhe|mujhy|mera|meri|mere|batao|batain|karna|chahiye|haq|qanun|qanoon)\b",
    re.IGNORECASE,
)
TRANSLATION_ONLY_RE = re.compile(
    r"^\s*(please\s+)?(translate|translate this|translate it|urdu|urdu translation|is ko urdu mein|isko urdu mein|urdu mein)\s*(into|in|mein)?\s*(urdu)?\s*[\.\?!]*\s*$",
    re.IGNORECASE,
)

TRANSLATION_SYSTEM_PROMPT = (
    "Translate the supplied Pakistani legal information into clear, natural Urdu. "
    "Preserve numbered steps, document names, law names, page references, and disclaimers. "
    "Do not add new legal facts or advice. Return only the Urdu translation."
)
MAX_TRANSLATION_CHARS = 2800
URDU_WORD = "\u0627\u0631\u062f\u0648"
TRANSLATION_WORD = "\u062a\u0631\u062c\u0645\u06c1"
ROOT_DIR = Path(__file__).resolve().parents[1]


def get_groq_api_key() -> str:
    load_dotenv(ROOT_DIR / ".env", override=True)

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if api_key:
        return api_key

    try:
        import streamlit as st

        secret_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
        if secret_key:
            os.environ["GROQ_API_KEY"] = secret_key
            return secret_key
    except Exception:
        pass

    raise RuntimeError(
        "GROQ_API_KEY is missing. Add it to .env locally or Streamlit secrets in deployment."
    )


def needs_urdu_translation(prompt: str) -> bool:
    """Return true when the user explicitly asks for Urdu or appears to write in Urdu/Roman Urdu."""
    return bool(
        URDU_RE.search(prompt)
        or URDU_REQUEST_RE.search(prompt)
        or ROMAN_URDU_RE.search(prompt)
    )


def is_translation_only_request(prompt: str) -> bool:
    return bool(TRANSLATION_ONLY_RE.search(prompt) or prompt.strip() in {URDU_WORD, TRANSLATION_WORD})


def remove_existing_urdu_translation(answer: str) -> str:
    return re.split(r"\n\s*\*\*Urdu Translation:\*\*\s*\n", answer, maxsplit=1)[0].strip()


def split_translation_chunks(text: str, limit: int = MAX_TRANSLATION_CHARS) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for block in re.split(r"(\n\s*\n)", text.strip()):
        block_length = len(block)
        if current and current_length + block_length > limit:
            chunks.append("".join(current).strip())
            current = []
            current_length = 0
        if block_length > limit:
            for start in range(0, block_length, limit):
                part = block[start : start + limit].strip()
                if part:
                    chunks.append(part)
            continue
        current.append(block)
        current_length += block_length

    if current:
        chunks.append("".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def _translate_chunk(client: Groq, text: str) -> str:
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=0.1,
        max_tokens=1400,
        messages=[
            {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def translate_to_urdu(text: str) -> str:
    api_key = get_groq_api_key()
    if not text.strip():
        raise RuntimeError("answer text is empty")

    client = Groq(api_key=api_key)
    translations = [_translate_chunk(client, chunk) for chunk in split_translation_chunks(text)]
    translation = "\n\n".join(part for part in translations if part)
    if not translation:
        raise RuntimeError("translation response was empty")
    return translation


def append_urdu_translation(answer: str, prompt: str) -> str:
    if not needs_urdu_translation(prompt) or "Urdu Translation" in answer:
        return answer

    try:
        translation = translate_to_urdu(remove_existing_urdu_translation(answer))
    except Exception as exc:
        return (
            f"{answer}\n\n"
            "**Urdu Translation:**\n"
            f"Urdu translation could not be generated right now ({exc.__class__.__name__}: {exc})."
        )

    return f"{answer}\n\n**Urdu Translation:**\n{translation}"
