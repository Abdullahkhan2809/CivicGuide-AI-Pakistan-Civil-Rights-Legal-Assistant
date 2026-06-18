from __future__ import annotations

import json
import os
import re
import textwrap
from datetime import datetime
from functools import lru_cache
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from groq import Groq

from agents.translator import append_urdu_translation
from config import APP_NAME, APP_SUBTITLE, DISCLAIMER, LEGAL_DOMAINS
from memory.memory import init_session
from rag.prompts import SYSTEM_PROMPT, build_answer_prompt
from rag.retriever import RetrievedChunk, StatuteRetriever
from utils.parser import detect_domain, detect_subcategory, short_case_title
from utils.procedures import Procedure, answer_procedure_question, get_procedure


load_dotenv()
st.set_page_config(page_title=APP_NAME, page_icon="CG", layout="wide")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #080b11; color: #f0f2f8; }
        [data-testid="stSidebar"] {
            background: #121722;
            border-right: 1px solid #2b3140;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding: 3rem 2rem 2rem;
        }
        [data-testid="stSidebar"] * { color: #e7e9f0; }
        .block-container {
            max-width: 100%;
            padding: 1rem 1.75rem 5.5rem;
        }
        .app-topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            border-bottom: 1px solid #2b3140;
            padding: 0.25rem 0 1rem;
            margin-bottom: 0;
        }
        .app-title {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            font-weight: 800;
        }
        .mini-logo {
            width: 24px;
            height: 24px;
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0) 42%),
                linear-gradient(135deg, #4f8df7 0%, #11b7a4 100%);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            position: relative;
            box-shadow: 0 8px 22px rgba(79, 141, 247, 0.28);
            overflow: hidden;
        }
        .mini-logo::before {
            content: "⚖";
            color: #ffffff;
            font-size: 0.9rem;
            line-height: 1;
            transform: translateY(-1px);
        }
        .top-actions {
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }
        .case-strip {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            background: #191f32;
            border-bottom: 1px solid #2b3140;
            padding: 0.65rem 0.75rem;
            margin: 0 -0.25rem 1rem;
        }
        .pill {
            background: #4f8df7;
            color: #fff;
            border-radius: 5px;
            padding: 0.22rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 800;
        }
        .subpill {
            background: #242b42;
            color: #9da6bf;
            border-radius: 5px;
            padding: 0.22rem 0.7rem;
            font-size: 0.78rem;
            margin-left: 0.5rem;
        }
        .chat-panel {
            min-height: calc(100vh - 250px);
            border-left: 1px solid #1e2432;
            border-right: 1px solid #1e2432;
            padding: 1rem 1.2rem 2rem;
            background: #080b11;
        }
        [data-testid="stChatMessage"] {
            background: #20263a;
            border: 1px solid #2c344d;
            border-radius: 12px;
            padding: 1rem 1.35rem;
            margin: 0 auto 1rem;
            max-width: 850px;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li {
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        [data-testid="stChatInput"] {
            padding: 0.75rem 2rem 1rem !important;
            background: rgba(8, 11, 17, 0.96);
        }
        [data-testid="stChatInput"] > div {
            width: min(850px, 100%) !important;
            max-width: 850px !important;
            margin: 0 auto !important;
            padding: 0.55rem 0.7rem !important;
            border-radius: 14px !important;
            background: #242734 !important;
            border: 1px solid #30384d !important;
        }
        [data-testid="stChatInput"] > div > div {
            display: flex !important;
            align-items: center !important;
            gap: 0.7rem !important;
            width: 100% !important;
        }
        [data-testid="stChatInput"] textarea {
            width: 100% !important;
            min-height: 46px !important;
            max-height: 120px !important;
            background-color: #151923 !important;
            color: #f0f2f8 !important;
            border: 1px solid #30384d !important;
            border-radius: 10px !important;
            padding: 11px 14px !important;
            font-size: 15px !important;
            resize: none !important;
        }
        [data-testid="stChatInput"] button {
            flex: 0 0 44px !important;
            width: 44px !important;
            height: 44px !important;
            margin: 0 !important;
            align-self: center !important;
        }
        .suggestions {
            max-width: 850px;
            margin: 0.75rem auto 0;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        .suggestion-chip {
            background: #171d2d;
            color: #8f9ab7;
            border: 1px solid #29304b;
            border-radius: 999px;
            padding: 0.28rem 0.65rem;
            font-size: 0.78rem;
        }
        div[data-testid="stButton"] button[kind="secondary"] {
            background: #171d2d;
            color: #9da6bf;
            border: 1px solid #29304b;
            border-radius: 999px;
            min-height: 34px;
            padding: 0.25rem 0.7rem;
            font-size: 0.86rem;
            font-weight: 500;
        }
        div[data-testid="stButton"] button[kind="secondary"]:hover {
            color: #f0f2f8;
            border-color: #4f8df7;
            background: #20263a;
        }
        .title-row {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 0.25rem;
        }
        .logo {
            width: 64px;
            height: 64px;
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0) 42%),
                linear-gradient(135deg, #4f8df7 0%, #11b7a4 100%);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 64px;
            position: relative;
            box-shadow: 0 18px 44px rgba(79, 141, 247, 0.3);
            overflow: hidden;
        }
        .logo::before {
            content: "⚖";
            color: #ffffff;
            font-size: 2rem;
            line-height: 1;
            transform: translateY(-2px);
        }
        .logo::after {
            content: "";
            position: absolute;
            left: 18px;
            right: 18px;
            bottom: 13px;
            height: 3px;
            border-radius: 99px;
            background: rgba(255, 255, 255, 0.78);
        }
        .subtitle { color: #8b94ad; font-weight: 600; }
        .status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #35d08a;
            background: #1d2542;
            border-radius: 10px;
            padding: 8px 11px;
            font-weight: 700;
            margin: 1rem 0 0.9rem;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] { margin-bottom: 2rem; }
        .dot {
            width: 9px;
            height: 9px;
            border-radius: 99px;
            background: #35d08a;
            display: inline-block;
        }
        .sidebar-card {
            background: #20263a;
            border: 1px solid #29304b;
            border-radius: 12px;
            padding: 12px 14px;
            margin: 10px 0;
        }
        .muted { color: #8b94ad; font-size: 0.88rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def procedure_or_default() -> Procedure:
    procedure = st.session_state.get("procedure")
    if isinstance(procedure, dict):
        return procedure
    return {
        "title": "No Procedure Selected",
        "steps": [],
        "required_documents": [],
        "office": {"name": "Relevant local office", "jurisdiction": "Local", "note": "Submit a query to classify your issue."},
        "estimated_cost": "Submit a query",
        "estimated_timeline": "Submit a query",
        "relevant_law": "Submit a query to find relevant law",
    }


def classify_query(prompt: str) -> tuple[str, str, str]:
    domain = detect_domain(prompt)
    subcategory = detect_subcategory(prompt, domain)
    title = short_case_title(prompt, domain)
    return domain, subcategory, title


def document_available(case_text: str, document_name: str) -> bool:
    lowered = case_text.lower()
    name = document_name.lower()
    aliases = {
        "rent agreement": ["rent agreement", "lease", "lease agreement", "tenancy agreement"],
        "security deposit receipt": ["deposit receipt", "security deposit receipt", "receipt"],
        "cnic": ["cnic", "identity card", "id card"],
        "written notice": ["written notice", "legal notice", "notice"],
        "nikah nama": ["nikah nama", "nikahnama", "marriage certificate"],
        "birth certificate": ["birth certificate", "children's birth certificate", "b-form"],
        "company registration": ["company registration", "incorporation", "certificate of incorporation"],
        "shareholder": ["shareholder", "shares", "members register"],
    }
    for key, values in aliases.items():
        if key in name and any(value in lowered for value in values):
            return True
    return any(part in lowered for part in re.findall(r"[a-zA-Z]{4,}", name))


def default_documents_for_domain(domain: str) -> list[dict[str, str]]:
    common = [
        {"name_en": "CNIC Copy", "name_ur": "شناختی کارڈ", "source": "NADRA"},
        {"name_en": "Written Timeline of Facts", "name_ur": "واقعات کی تحریری تفصیل", "source": "Prepared by user"},
        {"name_en": "Evidence and Correspondence", "name_ur": "ثبوت اور خط و کتابت", "source": "Messages, emails, notices, receipts, screenshots"},
    ]
    domain_docs = {
        "business": [
            {"name_en": "Company Registration Documents", "name_ur": "کمپنی رجسٹریشن دستاویزات", "source": "SECP / company records"},
            {"name_en": "Proof of Shareholding", "name_ur": "شیئر ہولڈنگ کا ثبوت", "source": "Share certificate, Form/SECP record, CDC record, or company register"},
        ],
        "intellectual_property": [
            {"name_en": "Proof of Authorship or Invention", "name_ur": "تصنیف یا ایجاد کا ثبوت", "source": "Drafts, lab notes, files, dated records, publication/submission records"},
            {"name_en": "Registration or Application Record", "name_ur": "رجسٹریشن یا درخواست کا ریکارڈ", "source": "IPO Pakistan / Patent, Copyright, or Trademark office"},
            {"name_en": "Copy of Infringing Material", "name_ur": "خلاف ورزی شدہ مواد کی کاپی", "source": "Screenshots, publication, product, copied filing, or website"},
        ],
        "property": [
            {"name_en": "Ownership or Tenancy Documents", "name_ur": "ملکیت یا کرایہ داری دستاویزات", "source": "Registry, mutation, tenancy agreement, allotment, or receipts"},
            {"name_en": "Possession or Payment Proof", "name_ur": "قبضہ یا ادائیگی کا ثبوت", "source": "Receipts, photos, utility bills, bank records"},
        ],
        "family": [
            {"name_en": "Family Relationship Documents", "name_ur": "خاندانی تعلق کے کاغذات", "source": "Nikah nama, birth certificate, family registration certificate"},
            {"name_en": "Financial or Custody Evidence", "name_ur": "مالی یا تحویل کا ثبوت", "source": "Expense records, school/medical records, messages"},
        ],
    }
    return common + domain_docs.get(domain, [])


def forum_for_domain(domain: str) -> dict[str, str]:
    forums = {
        "business": {
            "name": "Company Registered Office, SECP, or competent court",
            "jurisdiction": "Company registration jurisdiction / Pakistan",
            "note": "Use company records first; escalate through SECP complaint channels or court where needed.",
        },
        "intellectual_property": {
            "name": "IPO Pakistan / Intellectual Property Tribunal",
            "jurisdiction": "Pakistan / territorial tribunal jurisdiction",
            "note": "Check the relevant Patent, Copyright, or Trademark office record and preserve proof before filing.",
        },
        "property": {
            "name": "Relevant revenue, rent, civil, or registration forum",
            "jurisdiction": "Local property jurisdiction",
            "note": "Forum depends on whether the issue is rent, title, possession, registration, or transfer.",
        },
        "family": {
            "name": "Family Court or Guardian Court",
            "jurisdiction": "Where the family matter is legally filed",
            "note": "Forum depends on the relief: dissolution, maintenance, custody, guardianship, or dowry.",
        },
    }
    return forums.get(
        domain,
        {
            "name": "Relevant legal forum or regulator",
            "jurisdiction": "Depends on the law and facts",
            "note": "Use the cited law/source to confirm the correct filing forum.",
        },
    )


def build_statute_procedure(prompt: str, domain: str, chunks: list[RetrievedChunk]) -> Procedure:
    law_refs = chunk_references(chunks) or "No matching source reference found yet."
    title = short_case_title(prompt, domain)
    return {
        "title": title,
        "steps": [
            {
                "step": 1,
                "action": "Preserve evidence",
                "details": "Save originals and copies of documents, screenshots, messages, dates, names, and any official records connected to the issue.",
                "timeline": "Immediately",
            },
            {
                "step": 2,
                "action": "Confirm the exact legal right and forum",
                "details": "Use the cited statute pages and the relevant office or regulator to confirm which filing route applies.",
                "timeline": "1-3 days",
            },
            {
                "step": 3,
                "action": "Send written notice or file a complaint/petition",
                "details": "Prepare a written request, legal notice, complaint, or petition with the evidence and cited law references.",
                "timeline": "Varies by forum",
            },
        ],
        "required_documents": default_documents_for_domain(domain),
        "office": forum_for_domain(domain),
        "estimated_cost": "Varies by forum, filing route, and advocate fees",
        "estimated_timeline": "Urgent evidence preservation; formal proceedings vary from weeks to months",
        "relevant_law": law_refs,
    }


def groq_answer(prompt: str, procedure: Procedure) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.session_state.llm_status = "Groq key missing"
        return None

    client = Groq(api_key=api_key)
    domain = st.session_state.get("domain", detect_domain(prompt))
    law_query = expand_legal_query(
        f"{prompt} {procedure.get('title', '')} {procedure.get('relevant_law', '')}",
        domain,
    )
    chunks = statute_retriever().search(law_query, domain, limit=5)
    statute_context = "\n\n".join(
        f"[{idx}] {chunk.source}, page {chunk.page}: {chunk.text}"
        for idx, chunk in enumerate(chunks, start=1)
    ) or "No matching statute excerpts were found."

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=0.1,
        max_tokens=650,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are CivicGuide AI, a Pakistani legal information assistant. "
                    "Answer the user's question using only the supplied procedure JSON and statute excerpts. "
                    "Do not invent legal steps, fees, offices, or laws. "
                    "If the JSON does not contain the answer, say what is missing and suggest confirming locally. "
                    "Keep the answer concise and practical. Cite source names and pages when using statute excerpts. "
                    "This is legal information, not legal advice."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": prompt,
                        "procedure": procedure,
                        "statute_excerpts": statute_context,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            },
        ],
    )
    st.session_state.llm_status = "Groq answered"
    return response.choices[0].message.content or ""


@lru_cache(maxsize=1)
def statute_retriever() -> StatuteRetriever:
    return StatuteRetriever()


def expand_legal_query(prompt: str, domain: str) -> str:
    lowered = prompt.lower()
    additions: list[str] = []
    if domain == "business" and any(word in lowered for word in ["share", "founder", "cofounder", "co-founder"]):
        additions.append("shareholder member register share certificate transfer shares company member rights SECP")
    if domain == "intellectual_property":
        additions.append("intellectual property patent copyright trademark infringement IPO Pakistan evidence civil procedure")
    return " ".join([prompt, *additions]).strip()


def groq_statute_answer(prompt: str, chunks: list[RetrievedChunk]) -> str | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=0.1,
        max_tokens=750,
        messages=[
            {
                "role": "system",
                "content": (
                    f"{SYSTEM_PROMPT}\n"
                    "If the user's issue concerns patent, copyright, trademark, research, authorship, plagiarism, or invention, "
                    "treat it as an intellectual-property issue. Do not answer under ordinary theft/property law unless the supplied excerpts specifically support that route."
                ),
            },
            {"role": "user", "content": build_answer_prompt(prompt, prompt, chunks)},
        ],
    )
    st.session_state.llm_status = "Groq answered from statutes"
    return response.choices[0].message.content or ""


def chunk_references(chunks: list[RetrievedChunk]) -> str:
    unique_refs: list[str] = []
    seen: set[tuple[str, int]] = set()
    for chunk in chunks:
        key = (chunk.source, chunk.page)
        if key in seen:
            continue
        seen.add(key)
        unique_refs.append(f"- {chunk.source}, page {chunk.page}")
    return "\n".join(unique_refs)


def extractive_statute_answer(prompt: str, domain: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        st.session_state.llm_status = "No statute match"
        return (
            "I could not find a strong matching procedure or statute excerpt in the local law texts for this question. "
            "Try adding the forum, document name, company name, or right involved so I can search the extracted laws more precisely."
        )

    st.session_state.llm_status = "Answered from statute extracts"
    first_points = "\n".join(
        f"- {chunk.text[:420].strip()}..."
        for chunk in chunks[:3]
    )
    docs = {
        "business": "Proof of shareholding or founder agreement, company incorporation documents, Form/SECP records, share certificate or CDC record, written messages, notices, and CNIC.",
        "intellectual_property": "Proof of authorship/invention, dated drafts or lab notes, publication/submission records, registration/application records, communications, copied material, and witness/evidence records.",
    }.get(
        domain,
        "CNIC, written correspondence, proof of the right claimed, notices, receipts, and any official records connected to the issue.",
    )
    forum = {
        "business": "Start with the company secretary/registered office for records, then use SECP complaint channels or a civil/company-law advocate if the dispute continues.",
        "intellectual_property": "Preserve evidence first, then check registration/status with IPO Pakistan and speak with an intellectual-property advocate about notice, complaint, or civil action.",
    }.get(domain, "Preserve evidence and consult the relevant office or a licensed advocate for forum-specific filing.")

    return (
        "I did not find a prepared step-by-step procedure for this exact issue, but the extracted law texts do contain relevant material.\n\n"
        "Direct answer:\n"
        f"{forum}\n\n"
        "Immediate next steps:\n"
        "1. Collect and preserve the documents/evidence before confronting the other party further.\n"
        "2. Send a written request or legal notice that clearly states the right you claim and the remedy you want.\n"
        "3. If they do not respond, take the documents to the relevant regulator/forum or a licensed advocate for filing.\n\n"
        f"Documents to carry:\n{docs}\n\n"
        f"Relevant extracted law snippets:\n{first_points}\n\n"
        f"Source references:\n{chunk_references(chunks)}"
    )


def statute_answer(prompt: str, domain: str) -> str:
    query = expand_legal_query(prompt, domain)
    chunks = statute_retriever().search(query, domain, limit=5)
    st.session_state.procedure = build_statute_procedure(prompt, domain, chunks)
    try:
        answer = groq_statute_answer(prompt, chunks)
    except Exception as exc:
        st.session_state.llm_status = f"Groq statute fallback failed: {exc.__class__.__name__}"
        answer = None
    return answer or extractive_statute_answer(prompt, domain, chunks)


def answer_user(prompt: str, procedure: Procedure | None) -> str:
    if not procedure:
        answer = statute_answer(prompt, st.session_state.get("domain", detect_domain(prompt)))
        return append_urdu_translation(answer, prompt)

    try:
        answer = groq_answer(prompt, procedure)
    except Exception as exc:
        st.session_state.llm_status = f"Groq failed: {exc.__class__.__name__}"
        answer = None

    if answer:
        return append_urdu_translation(answer, prompt)

    fallback = answer_procedure_question(procedure, prompt)
    domain = st.session_state.get("domain", detect_domain(prompt))
    chunks = statute_retriever().search(
        expand_legal_query(f"{prompt} {procedure.get('relevant_law', '')}", domain),
        domain,
        limit=3,
    )
    refs = chunk_references(chunks)
    if refs:
        fallback = f"{fallback}\n\nRelevant extracted law references:\n{refs}"
    return append_urdu_translation(fallback, prompt)


def sanitize_pdf_text(text: str) -> str:
    ascii_text = text.encode("latin-1", "replace").decode("latin-1")
    ascii_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", ascii_text)
    wrapped: list[str] = []
    for line in ascii_text.splitlines() or [""]:
        wrapped.extend(
            textwrap.wrap(line, width=90, break_long_words=True, break_on_hyphens=True)
            or [""]
        )
    return "\n".join(wrapped)


def create_action_plan_pdf(case_text: str, procedure: Procedure, answer: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "CivicGuide AI Action Plan", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.cell(0, 8, f"Case: {procedure.get('title', 'Procedure')}", ln=True)
    pdf.ln(4)

    def write_section(title: str, body: str) -> None:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(
            pdf.epw,
            6,
            sanitize_pdf_text(body),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        pdf.ln(3)

    write_section("Facts Shared", case_text or "No case facts entered yet.")
    write_section("Assistant Guidance", answer or "No answer generated yet.")
    write_section("Relevant Law", procedure.get("relevant_law", "Confirm locally."))
    write_section("Disclaimer", DISCLAIMER)
    return bytes(pdf.output())


def reset_document_checks() -> None:
    for key in list(st.session_state.keys()):
        if str(key).startswith("doc_"):
            del st.session_state[key]


def handle_prompt(prompt: str) -> None:
    reset_document_checks()
    domain, subcategory, case_title = classify_query(prompt)
    procedure = get_procedure(domain, subcategory)

    st.session_state.current_query = prompt
    st.session_state.case_text = prompt
    st.session_state.domain = domain
    st.session_state.subcategory = subcategory
    st.session_state.case_title = case_title
    if procedure:
        st.session_state.procedure = procedure
    st.session_state.last_answer = answer_user(prompt, procedure)


def render_suggestion_buttons() -> None:
    suggestions = [
        "How do I write a legal notice?",
        "What documents do I need?",
        "How long does the process take?",
    ]
    cols = st.columns([0.24, 0.24, 0.28, 0.24], gap="small")
    for col, suggestion in zip(cols, suggestions):
        with col:
            if st.button(suggestion, key=f"suggestion_{suggestion}", use_container_width=True):
                handle_prompt(suggestion)
                st.rerun()


def render_sidebar(procedure: Procedure) -> None:
    with st.sidebar:
        st.markdown(
            f'<div class="title-row"><span class="logo"></span><div><strong>{APP_NAME}</strong><br>'
            f'<span class="subtitle">{APP_SUBTITLE}</span></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="status"><span class="dot"></span>Active Session</div>', unsafe_allow_html=True)
        if st.button("New Chat", use_container_width=True):
            for key in [
                "current_query",
                "case_text",
                "last_answer",
                "procedure",
                "llm_status",
            ]:
                st.session_state.pop(key, None)
            reset_document_checks()
            st.rerun()

        st.divider()
        st.subheader("Case Summary")
        st.caption(f"{LEGAL_DOMAINS.get(st.session_state.domain, {}).get('label', 'Category')} / {st.session_state.case_title}")
        st.caption(st.session_state.get("llm_status", "Waiting for input"))

        st.markdown("**Required Documents**")
        for item in procedure.get("required_documents", []):
            name = item.get("name_en", "Document")
            source = item.get("source", "")
            key = f"doc_{st.session_state.domain}_{st.session_state.subcategory}_{name}"
            if key not in st.session_state:
                st.session_state[key] = document_available(st.session_state.case_text, name)
            st.checkbox(name, key=key)
            st.caption(source)

        st.divider()
        st.markdown("**Relevant Law**")
        st.markdown(
            f'<div class="sidebar-card">{procedure.get("relevant_law", "Submit a query to find relevant law")}</div>',
            unsafe_allow_html=True,
        )

        office = procedure.get("office", {})
        st.markdown("**Office to Visit**")
        st.markdown(
            f'<div class="sidebar-card"><strong>{office.get("name", "Relevant local office")}</strong><br>'
            f'<span class="muted">{office.get("jurisdiction", "Local")}</span><br>'
            f'<span class="muted">{office.get("note", "")}</span></div>',
            unsafe_allow_html=True,
        )

        st.markdown("**Cost and Timeline**")
        st.markdown(
            f'<div class="sidebar-card"><strong>{procedure.get("estimated_cost", "Submit a query")}</strong><br>'
            f'<span class="muted">{procedure.get("estimated_timeline", "Submit a query")}</span></div>',
            unsafe_allow_html=True,
        )

        st.download_button(
            "Download Action Plan",
            data=create_action_plan_pdf(
                st.session_state.case_text,
                procedure,
                st.session_state.last_answer,
            ),
            file_name="civicguide-action-plan.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


def main() -> None:
    inject_css()
    init_session()
    st.session_state.setdefault("current_query", "")
    st.session_state.setdefault("last_answer", "")
    st.session_state.setdefault("case_text", "")
    st.session_state.setdefault("domain", "property")
    st.session_state.setdefault("subcategory", "security_deposit_recovery")
    st.session_state.setdefault("case_title", "Tenant Deposit Dispute")
    st.session_state.setdefault("llm_status", "Waiting for input")

    procedure = procedure_or_default()
    render_sidebar(procedure)

    domain_label = LEGAL_DOMAINS.get(st.session_state.domain, {}).get("label", "Category")
    st.markdown(
        f"""
        <div class="app-topbar">
          <div class="app-title">
            <span class="mini-logo"></span>
            <span>{APP_NAME}</span>
            <span class="subtitle">{APP_SUBTITLE}</span>
          </div>
          <div class="top-actions">
            <span class="status"><span class="dot"></span>Active Session</span>
            <span class="sidebar-card" style="margin:0;padding:8px 13px;">New Chat</span>
          </div>
        </div>
        <div class="case-strip">
          <div><span class="pill">{domain_label}</span><span class="subpill">{st.session_state.case_title}</span></div>
          <div class="muted">Procedure: {st.session_state.subcategory}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="chat-panel">', unsafe_allow_html=True)
    if st.session_state.current_query:
        with st.chat_message("user"):
            st.write(st.session_state.current_query)
        with st.chat_message("assistant", avatar="⚖"):
            st.write(st.session_state.last_answer)
    else:
        with st.chat_message("assistant", avatar="⚖"):
            st.write("Tell me your issue, for example: `khulla procedure`, `landlord not returning deposit`, or `company registration`.")
    render_suggestion_buttons()
    st.markdown("</div>", unsafe_allow_html=True)

    prompt = st.chat_input("Type your legal issue or question...")
    if prompt:
        handle_prompt(prompt)
        st.rerun()

    st.caption(f"Warning: {DISCLAIMER}")


if __name__ == "__main__":
    main()
