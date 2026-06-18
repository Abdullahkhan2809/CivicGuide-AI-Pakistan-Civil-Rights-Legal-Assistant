
from __future__ import annotations


OFFICES_BY_DOMAIN = {
    "property": {
        "name": "Rent Controller Office",
        "address": "District Courts Complex or local Rent Controller in your district",
        "hours": "Mon-Sat, 9am-2pm",
    },
    "family": {
        "name": "Family Court / Union Council",
        "address": "Family Court or Union Council office for your area",
        "hours": "Mon-Sat, 9am-2pm",
    },
    "business": {
        "name": "SECP Company Registration Office",
        "address": "Nearest SECP CRO or eServices portal",
        "hours": "Mon-Fri, 9am-5pm",
    },
}


def default_action_plan(domain: str, case_text: str) -> list[str]:
    lowered = case_text.lower()
    if domain == "property" and "deposit" in lowered:
        return [
            "Send a formal written notice demanding deposit return within a clear deadline, usually 7-15 days.",
            "Attach copies of the rent agreement, deposit receipt, and proof that you vacated the property.",
            "If ignored, file an application before the Rent Controller or relevant civil forum in your district.",
            "Carry originals plus CNIC copies and keep one complete photocopy set for filing.",
        ]
    if domain == "family":
        return [
            "Collect identity documents, Nikah Nama, expense records, and any prior notices or orders.",
            "Approach the Family Court for maintenance, custody, dissolution, or related relief as applicable.",
            "For registration or notice issues, also check the relevant Union Council record.",
            "Ask a licensed family-law advocate to review limitation, jurisdiction, and prayer clauses.",
        ]
    if domain == "business":
        return [
            "Collect incorporation, shareholder, board, tax, banking, and SECP correspondence records.",
            "Check whether the issue is a filing correction, shareholder remedy, compliance default, or dispute.",
            "Use SECP eServices/CRO for statutory filings and preserve acknowledgements.",
            "For disputes involving money or control, get counsel to review remedies under company law.",
        ]
    return [
        "Write a dated summary of facts and gather supporting documents.",
        "Send a written notice where appropriate and keep proof of delivery.",
        "Visit the relevant local office or court registry with originals and copies.",
    ]
