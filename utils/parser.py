
from __future__ import annotations

import re

from config import LEGAL_DOMAINS


def detect_domain(text: str) -> str:
    lowered = text.lower()
    scores = {
        key: sum(1 for keyword in spec["keywords"] if keyword in lowered)
        for key, spec in LEGAL_DOMAINS.items()
    }
    return max(scores, key=scores.get) if max(scores.values(), default=0) else "general"


def has_domain_signal(text: str) -> bool:
    lowered = text.lower()
    return any(
        keyword in lowered
        for spec in LEGAL_DOMAINS.values()
        for keyword in spec["keywords"]
    )


def detect_subcategory(text: str, domain: str) -> str:
    lowered = text.lower()
    if domain == "property" and (
        "deposit" in lowered
        or "security" in lowered
        or "landlord" in lowered
        or "rent agreement" in lowered
    ):
        return "security_deposit_recovery"
    if domain == "property" and ("evict" in lowered or "possession" in lowered):
        return "tenant_eviction_response"
    if domain == "property" and ("register" in lowered or "registry" in lowered or "mutation" in lowered):
        return "property_registration"
    if domain == "family" and ("khula" in lowered or "khulla" in lowered or "divorce" in lowered or "dissolution" in lowered):
        return "khula_or_dissolution"
    if domain == "family" and ("maintenance" in lowered or "monthly expense" in lowered):
        return "maintenance_claim"
    if domain == "family" and ("custody" in lowered or "guardian" in lowered):
        return "child_custody_guardianship"
    if domain == "business" and (
        "register" in lowered
        or "registration" in lowered
        or "incorporat" in lowered
        or "single member" in lowered
    ):
        return "company_registration"
    if domain == "business" and (
        "shareholder" in lowered
        or "shares" in lowered
        or "share" in lowered
        or "director" in lowered
        or "founder" in lowered
        or "cofounder" in lowered
        or "co-founder" in lowered
    ):
        return "shareholder_rights"
    if domain == "business" and ("financial statement" in lowered or "accounts" in lowered or "annual" in lowered):
        return "financial_statement_filing"
    if domain == "intellectual_property":
        return "general_guidance"
    return "general_guidance"


def short_case_title(text: str, domain: str) -> str:
    lowered = text.lower()
    if "khula" in lowered or "khulla" in lowered or "divorce" in lowered or "dissolution" in lowered:
        return "Khula / Dissolution Procedure"
    if "deposit" in lowered and ("rent" in lowered or "landlord" in lowered):
        return "Tenant Deposit Dispute"
    if "evict" in lowered or "eviction" in lowered:
        return "Tenant Eviction Concern"
    if "custody" in lowered:
        return "Child Custody Matter"
    if "maintenance" in lowered:
        return "Family Maintenance Claim"
    if any(word in lowered for word in ["patent", "copyright", "trademark", "research", "citation", "citing"]):
        return "Intellectual Property Concern"
    if any(word in lowered for word in ["shareholder", "shares", "share", "founder", "cofounder", "co-founder"]):
        return "Shareholder / Founder Dispute"
    if "company" in lowered or "secp" in lowered:
        return "Business Compliance Matter"
    return f"{LEGAL_DOMAINS.get(domain, LEGAL_DOMAINS['general'])['label']} Matter"


def extract_documents_mentioned(text: str) -> set[str]:
    checks = {
        "Rent Agreement Copy": ["rent agreement", "lease", "tenancy agreement"],
        "Deposit Receipt": ["deposit receipt", "receipt"],
        "CNIC Copy": ["cnic", "id card", "identity card"],
        "Written Notice": ["notice", "written notice", "legal notice"],
        "Photographs or Evidence": ["photo", "picture", "evidence", "screenshot"],
        "Nikah Nama": ["nikah", "marriage certificate", "nikahnama"],
        "Company Documents": ["incorporation", "form", "secp", "memorandum", "articles"],
    }
    lowered = text.lower()
    return {
        label
        for label, keywords in checks.items()
        if any(keyword in lowered for keyword in keywords)
    }


def compact_case_text(messages: list[dict[str, str]], limit: int = 1800) -> str:
    user_text = "\n".join(message["content"] for message in messages if message.get("role") == "user")
    return re.sub(r"\s+", " ", user_text).strip()[-limit:]
