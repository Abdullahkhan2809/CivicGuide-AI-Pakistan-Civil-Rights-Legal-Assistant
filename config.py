
from pathlib import Path


APP_NAME = "CivicGuide AI"
APP_SUBTITLE = "Pakistani Legal Rights Assistant"
CASE_ID = "2024-1187"

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge" / "statute"
TEXT_DIR = BASE_DIR / "knowledge" / "texts"
TEXT_JSON_DIR = BASE_DIR / "knowledge" / "json"
PROCEDURES_DIR = BASE_DIR / "knowledge" / "procedures"
VECTOR_DB_DIR = BASE_DIR / "vector_db" / "chroma_db"
CACHE_DIR = BASE_DIR / ".cache"
PDF_CACHE_PATH = CACHE_DIR / "statute_chunks.json"

DEFAULT_MODEL = "llama-3.1-8b-instant"
MAX_CONTEXT_CHUNKS = 5

LEGAL_DOMAINS = {
    "general": {
        "label": "General Legal",
        "keywords": [],
        "laws": [],
    },
    "property": {
        "label": "Property",
        "keywords": [
            "rent",
            "tenant",
            "landlord",
            "deposit",
            "lease",
            "property",
            "transfer",
            "registry",
            "possession",
            "eviction",
            "plot",
            "land",
        ],
        "laws": [
            "THE ISLAMABAD RENT RESTRICTION ORDINANCE, 2001.pdf",
            "THE KARACHI RENT RESTRICTION ACT, 1953.pdf",
            "THE CANTONMENTS RENT RESTRICTION ACT, 1963.pdf",
            "THE TRANSFER OF PROPERTY ACT, 1882.pdf",
            "THE REGISTRATION ACT, 1908.pdf",
            "THE STAMP ACT, 1899.pdf",
            "THE ENFORCEMENT OF WOMEN'S PROPERTY RIGHTS ACT,.pdf",
            "THE ENFORCEMENT OF WOMEN’S PROPERTY RIGHTS ACT,.pdf",
        ],
    },
    "family": {
        "label": "Family",
        "keywords": [
            "marriage",
            "nikah",
            "divorce",
            "khula",
            "khulla",
            "maintenance",
            "custody",
            "guardian",
            "dowry",
            "inheritance",
            "wife",
            "husband",
            "child",
        ],
        "laws": [
            "THE FAMILY COURTS ACT, 1964.pdf",
            "THE_WEST_PAKISTAN_FAMILY_COURTS_ACT_1964.pdf",
            "Family_Courts_Rules,_19653.pdf",
            "muslim family law ordinance 1961.pdf",
            "The Dissolution of Muslim Marriages Act.pdf",
            "1527084484GuardiansWardsAct1890.pdf",
            "Dowry_and_Bridal_Gifts_(Restriction)_Rules_1976.pdf",
            "child Marriage Restraint Act, 1929.pdf",
        ],
    },
    "business": {
        "label": "Business",
        "keywords": [
            "company",
            "shareholder",
            "share",
            "shares",
            "founder",
            "cofounder",
            "co-founder",
            "secp",
            "business",
            "director",
            "financial",
            "microfinance",
            "corporate",
            "registration",
            "compliance",
        ],
        "laws": [
            "The-Company-Act-2017-updated-18.8.2022.pdf",
            "Companies-Regulations-2024-updated-upto-25.07.2025-Reviewed-14042026.pdf",
            "Company-Registration-Brochure-English.pdf",
            "Guide-on-Shareholders-Right.pdf",
            "Guide-on-Single-Member-Company.pdf",
            "Guide-on-Financial-Statements.pdf",
            "Guide-Book-on-Corporate-Governance-and-Frequently-Asked-Questions-Revised.pdf",
            "Guide on Microfinance.pdf",
        ],
    },
    "intellectual_property": {
        "label": "Intellectual Property",
        "keywords": [
            "intellectual property",
            "ipo",
            "patent",
            "copyright",
            "trademark",
            "trade mark",
            "infringement",
            "research",
            "citation",
            "citing",
            "plagiarism",
            "author",
            "inventor",
            "stole my work",
            "stolen work",
        ],
        "laws": [
            "THE INTELLECTUAL PROPERTY ORGANIZATION OF.pdf",
            "Qanun-e-Shahadat Order, 1984.pdf",
            "THE_CODE_OF_CIVIL_PROCEDURE,_1908.pdf",
        ],
    },
}

DISCLAIMER = (
    "This is general legal information, not legal advice. Please consult a licensed "
    "advocate for your specific situation."
)
