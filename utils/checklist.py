
from __future__ import annotations

from utils.parser import extract_documents_mentioned


DOCUMENTS_BY_DOMAIN = {
    "property": [
        "Rent Agreement Copy",
        "Deposit Receipt",
        "CNIC Copy",
        "Written Notice to Landlord",
        "Photographs of Vacated Property",
    ],
    "family": [
        "CNIC Copy",
        "Nikah Nama",
        "Children's Birth Certificates",
        "Proof of Expenses or Maintenance",
        "Prior Court or Union Council Papers",
    ],
    "business": [
        "CNIC Copy",
        "Company Registration Documents",
        "Board or Shareholder Records",
        "Tax or SECP Correspondence",
        "Bank or Transaction Records",
    ],
}


def build_document_checklist(domain: str, case_text: str) -> list[dict[str, object]]:
    mentioned = extract_documents_mentioned(case_text)
    documents = DOCUMENTS_BY_DOMAIN.get(domain, DOCUMENTS_BY_DOMAIN["property"])
    return [
        {
            "name": document,
            "available": document in mentioned
            or document.replace(" to Landlord", "") in mentioned,
        }
        for document in documents
    ]
