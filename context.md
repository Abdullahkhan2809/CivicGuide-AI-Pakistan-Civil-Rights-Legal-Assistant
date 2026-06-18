# CivicGuide AI

**AI-Powered Legal Rights Assistant for Pakistani Citizens**

An agentic AI system that helps Pakistani citizens understand their legal rights, required procedures, and actionable next steps across Property & Land, Family & Inheritance, and Business & Financial domains.

---

## Problem Statement

Millions of Pakistani citizens face legal issues daily — property disputes, inheritance conflicts, business registration confusion — but lack access to affordable legal guidance. Existing resources are scattered across government portals in technical legal language. Most citizens don't know which law applies, which documents to gather, or which office to visit.

CivicGuide AI bridges this gap by letting users describe their situation in plain language and receiving structured, cited, actionable guidance grounded in actual Pakistani law.

---

## Scope & Boundaries

### In Scope (3 Legal Domains)

**1. Property & Land Rights**
- Property sale/purchase procedures (Bayanama, Registry)
- Land mutation (Intiqal) process
- Tenant/landlord disputes and security deposits
- Rent agreements and eviction procedures
- Land record verification (Fard)
- Property inheritance and transfer

**2. Family & Inheritance Rights**
- Islamic inheritance share calculation (Faraid)
- Succession certificate process
- Marriage registration (Nikah Nama)
- Divorce procedures (Khula, Talaq)
- Child custody (Hizanat) rights
- Dower (Haq Mehr) recovery
- Maintenance claims

**3. Business & Financial Rights**
- Company registration with SECP
- NTN registration with FBR
- Partnership deed requirements
- Sole proprietorship setup
- Trade license and NOC procedures
- Consumer complaint filing

### Out of Scope

Criminal law, tax advisory, immigration, medical malpractice, political matters, coding, general knowledge. The agent politely refuses these and explains its domain boundaries.

### Mandatory Disclaimers

- Every response includes: "This is general legal information, not legal advice. Please consult a licensed advocate for your specific case."
- The system never claims to replace a lawyer.
- The system never guarantees legal outcomes.

---

## Architecture

### High-Level Flow

```
┌──────────────────────────────────────────┐
│            Streamlit UI                  │
│   ┌─────────────┐  ┌─────────────────┐  │
│   │  Chat Panel  │  │ Sidebar:        │  │
│   │  (user/agent │  │ - Classification│  │
│   │   messages)  │  │ - Documents     │  │
│   │              │  │ - Steps         │  │
│   │              │  │ - Download PDF  │  │
│   └──────┬──────┘  └─────────────────┘  │
└──────────┼───────────────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│   LangChain AgentExecutor                │
│   (Groq + llama-3.3-70b-versatile)       │
│   with ConversationBufferMemory          │
│                                          │
│   ┌────────────────────────────────────┐ │
│   │           Agent Tools              │ │
│   │                                    │ │
│   │  1. classify_issue                 │ │
│   │  2. check_missing_info             │ │
│   │  3. lookup_procedure               │ │
│   │  4. retrieve_legal_sections (RAG)  │ │
│   │  5. generate_checklist             │ │
│   └──────────┬─────────────────────────┘ │
└──────────────┼───────────────────────────┘
               ↓
┌──────────────┴───────────────────────────┐
│          Knowledge Layer                 │
│                                          │
│  ┌─────────────────┐ ┌────────────────┐  │
│  │ procedures.json  │ │   ChromaDB     │  │
│  │ (structured      │ │ (statute text  │  │
│  │  action plans,   │ │  embeddings    │  │
│  │  documents,      │ │  for RAG       │  │
│  │  offices, costs) │ │  citations)    │  │
│  └─────────────────┘ └────────────────┘  │
└──────────────────────────────────────────┘
```

### Agent Decision Flow

```
User Input: "My landlord won't return my security deposit"
      │
      ▼
 ┌─────────────────┐
 │  classify_issue  │ → category: "property"
 │                  │   subcategory: "tenant_security_deposit"
 └────────┬────────┘
          ▼
 ┌─────────────────────┐
 │  check_missing_info  │ → missing: lease_type, deposit_receipt,
 │                      │   duration, written_agreement
 └────────┬─────────────┘
          ▼
   Agent asks user for missing details
          │
          ▼
   User provides details
          │
          ▼
 ┌────────────────────┐
 │  lookup_procedure   │ → structured steps, required documents,
 │                     │   office to visit, estimated cost/timeline
 └────────┬────────────┘
          ▼
 ┌──────────────────────────┐
 │  retrieve_legal_sections  │ → RAG pulls relevant sections from
 │                           │   Rent Restriction Ordinance
 └────────┬──────────────────┘
          ▼
   Agent synthesizes final response with:
   - Issue classification
   - Relevant law sections (cited)
   - Step-by-step procedure
   - Required documents (English + Urdu)
   - Office to contact
   - Estimated cost & timeline
   - Disclaimer
          │
          ▼
 ┌─────────────────────┐
 │  generate_checklist  │ → Downloadable PDF action plan
 └──────────────────────┘
```

---

## Tool Specifications

### Tool 1: classify_issue

**Purpose:** Determine which legal domain and subcategory the user's issue falls into.

**Input:** User's plain-language description of their situation.

**Logic:** Pattern match against category keywords defined in procedures.json. No LLM call needed — pure keyword + fuzzy matching.

**Output:**
```json
{
  "category": "property",
  "subcategory": "tenant_security_deposit",
  "confidence": "high",
  "in_scope": true
}
```

**Edge Case:** If `in_scope: false`, the agent stops here and returns a polite refusal explaining the three supported domains.

---

### Tool 2: check_missing_info

**Purpose:** Identify what information the user has NOT provided but is required to give accurate guidance.

**Input:** Classified category + subcategory + user's provided details.

**Logic:** Each procedure entry in procedures.json has a `required_inputs` field. Compare what the user mentioned against what's needed. Return the gaps.

**Output:**
```json
{
  "provided": ["city", "dispute_type"],
  "missing": [
    {
      "field": "written_lease",
      "question": "Do you have a written rent agreement/lease?"
    },
    {
      "field": "deposit_receipt",
      "question": "Do you have a receipt for the security deposit you paid?"
    },
    {
      "field": "duration",
      "question": "How long have you been renting the property?"
    }
  ]
}
```

**Why This Matters:** This is the core "agentic" behavior. The agent doesn't just answer — it reasons about what it needs to know before it can help properly.

---

### Tool 3: lookup_procedure

**Purpose:** Retrieve the structured action plan from the knowledge base.

**Input:** Category + subcategory from classification.

**Logic:** Direct JSON lookup against procedures.json.

**Output:**
```json
{
  "title": "Recovering Security Deposit from Landlord",
  "steps": [
    {
      "step": 1,
      "action": "Send a written notice to the landlord demanding return of deposit",
      "details": "Send via registered post or courier with tracking. Keep a copy.",
      "timeline": "Allow 15 days for response"
    },
    {
      "step": 2,
      "action": "File a complaint with the Rent Controller",
      "details": "Visit the Rent Controller office in your district. Submit application with supporting documents.",
      "timeline": "Filing takes 1-2 days"
    }
  ],
  "required_documents": [
    {
      "name_en": "Copy of Rent Agreement",
      "name_ur": "کرایہ نامہ کی کاپی",
      "source": "Your personal records"
    },
    {
      "name_en": "Security Deposit Receipt",
      "name_ur": "سیکیورٹی ڈپازٹ کی رسید",
      "source": "Issued by landlord at time of payment"
    },
    {
      "name_en": "CNIC Copy",
      "name_ur": "شناختی کارڈ کی کاپی",
      "source": "NADRA"
    },
    {
      "name_en": "Written Notice to Landlord (with proof of delivery)",
      "name_ur": "مالک مکان کو تحریری نوٹس",
      "source": "Drafted by you or your lawyer"
    }
  ],
  "office": {
    "name": "Rent Controller Office",
    "jurisdiction": "District-level",
    "note": "Located in the District Courts complex of your city"
  },
  "estimated_cost": "PKR 500-2000 (court fee + stamp paper)",
  "estimated_timeline": "1-6 months depending on landlord's cooperation",
  "relevant_law": "West Pakistan Urban Rent Restriction Ordinance, 1959"
}
```

---

### Tool 4: retrieve_legal_sections (RAG)

**Purpose:** Retrieve relevant statute text from ChromaDB to ground the agent's response in actual law.

**Input:** Query derived from the classified issue (e.g., "security deposit tenant rights rent restriction ordinance").

**Logic:**
1. Generate embedding for the query using HuggingFaceEmbeddings (local)
2. Similarity search against ChromaDB
3. Return top 3-4 relevant chunks with section numbers

**Output:**
```json
{
  "retrieved_sections": [
    {
      "source": "West Pakistan Urban Rent Restriction Ordinance, 1959",
      "section": "Section 15",
      "text": "No landlord shall claim or receive any premium or any sum in excess of fair rent..."
    },
    {
      "source": "West Pakistan Urban Rent Restriction Ordinance, 1959",
      "section": "Section 17",
      "text": "The Controller shall, on application made to him in the prescribed manner..."
    }
  ]
}
```

**RAG Pipeline Details:**
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace, local, free)
- Vector store: ChromaDB (persisted locally)
- Chunking strategy: Split by legal section number, not arbitrary token windows
- Retrieval: Top-k similarity search, k=4
- Documents indexed: 5-7 core Pakistani statutes (clean text only)

---

### Tool 5: generate_checklist

**Purpose:** Compile all gathered information into a downloadable PDF checklist.

**Input:** Combined output from lookup_procedure + retrieve_legal_sections + user details.

**Output:** A formatted PDF saved to `outputs/` containing:
- Issue summary
- Step-by-step action plan
- Required documents checklist (with checkboxes)
- Relevant law sections cited
- Office name and jurisdiction
- Estimated cost and timeline
- Disclaimer

**Library:** fpdf2

---

## Knowledge Base

### 1. Structured Knowledge: procedures.json

Hand-crafted entries covering common legal scenarios. Each entry follows this schema:

```json
{
  "id": "prop_001",
  "category": "property",
  "subcategory": "land_mutation",
  "title": "Land Mutation (Intiqal) Process",
  "description": "Transfer of land ownership in revenue records after sale or inheritance",
  "keywords": ["mutation", "intiqal", "land transfer", "fard", "patwari", "revenue"],
  "required_inputs": [
    "type_of_transfer",
    "relationship_to_previous_owner",
    "land_location_district",
    "existing_documents"
  ],
  "steps": [...],
  "required_documents": [...],
  "office": {...},
  "estimated_cost": "...",
  "estimated_timeline": "...",
  "relevant_law": "...",
  "province_specific_notes": {
    "punjab": "Use Punjab Land Record Authority (PLRA) online portal",
    "sindh": "Visit Mukhtiarkar office",
    "kpk": "Visit Tehsildar office",
    "balochistan": "Visit Revenue office"
  }
}
```

**Target: 15-20 entries minimum for hackathon demo.**

Priority entries to write:
1. Land mutation (Intiqal)
2. Property sale deed (Bayanama)
3. Fard (land record) verification
4. Tenant security deposit recovery
5. Rent agreement disputes
6. Eviction procedure
7. Islamic inheritance shares (Faraid)
8. Succession certificate
9. Marriage registration
10. Khula (wife-initiated divorce)
11. Child custody
12. Haq Mehr recovery
13. Company registration (SECP)
14. NTN registration (FBR)
15. Consumer complaint filing

### 2. RAG Knowledge: Statute Text Files

Clean text versions of key Pakistani laws stored in `knowledge/statutes/`:

| File | Law | Key Sections |
|------|-----|-------------|
| `transfer_of_property_act.txt` | Transfer of Property Act, 1882 | Sections 54, 58, 59, 100-104 |
| `rent_restriction_ordinance.txt` | West Pakistan Urban Rent Restriction Ordinance, 1959 | Sections 3, 10, 15, 17 |
| `muslim_family_laws.txt` | Muslim Family Laws Ordinance, 1961 | Sections 4, 5, 6, 7, 8 |
| `guardians_and_wards.txt` | Guardians and Wards Act, 1890 | Sections 7, 17, 25 |
| `secp_companies_act.txt` | Companies Act, 2017 | Sections 15-22 (registration) |

**Sources:** pakistancode.gov.pk, lawsofpakistan.com, punjablaws.gov.pk

**Ingestion pipeline (ingest.py):**
1. Read each text file
2. Split by section number using regex: `r"Section\s+\d+"`
3. Create metadata for each chunk: `{source, section_number, act_name}`
4. Embed using `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")` (runs locally)
5. Store in ChromaDB with `persist_directory="./chroma_db"`

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Agent Framework | LangChain (AgentExecutor + ReAct Agent) |
| LLM | Groq — llama-3.3-70b-versatile (responses + classification) |
| Embeddings | HuggingFace — sentence-transformers/all-MiniLM-L6-v2 (free, local) |
| Vector Store | ChromaDB |
| Memory | LangChain ConversationBufferMemory |
| PDF Generation | fpdf2 |
| Language | Python 3.11+ |

> **Why HuggingFace embeddings instead of a paid API?**
> Groq does not provide an embeddings API. Using a local HuggingFace
> sentence-transformer avoids any paid embedding dependency while still
> producing high-quality semantic search for the RAG layer. The model
> runs on CPU and requires no API key.

---

## Project Structure

```
civicguide-ai/
│
├── app.py                          # Streamlit entry point
│
├── agent/
│   ├── __init__.py
│   ├── agent.py                    # AgentExecutor setup and initialization
│   ├── prompts.py                  # System prompt, tool descriptions, disclaimer text
│   └── tools/
│       ├── __init__.py
│       ├── classify.py             # classify_issue tool
│       ├── missing_info.py         # check_missing_info tool
│       ├── procedure.py            # lookup_procedure tool
│       ├── retriever.py            # retrieve_legal_sections (RAG tool)
│       └── checklist.py            # generate_checklist (PDF output)
│
├── knowledge/
│   ├── procedures.json             # Structured legal procedures
│   └── statutes/
│       ├── transfer_of_property_act.txt
│       ├── rent_restriction_ordinance.txt
│       ├── muslim_family_laws.txt
│       ├── guardians_and_wards.txt
│       └── secp_companies_act.txt
│
├── ingestion/
│   ├── __init__.py
│   └── ingest.py                   # Script to chunk and embed statutes into ChromaDB
│
├── chroma_db/                      # ChromaDB persistent storage (auto-generated)
│
├── outputs/                        # Generated PDF checklists
│
├── .env                            # API keys (GROQ_API_KEY)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Streamlit UI Layout

```
┌──────────────────────────────────────────────────────────┐
│  🏛️ CivicGuide AI - Pakistani Legal Rights Assistant     │
├────────────────────────────┬─────────────────────────────┤
│                            │  📋 Case Summary            │
│   💬 Chat Interface        │                             │
│                            │  Category: Property         │
│   User: My landlord won't  │  Subcategory: Tenant Deposit│
│   return my deposit...     │                             │
│                            │  ─────────────────────────  │
│   Agent: Before I can help,│                             │
│   I need a few details:    │  📄 Required Documents      │
│   - Do you have a written  │  ☐ Rent Agreement Copy      │
│     lease?                 │  ☐ Deposit Receipt          │
│   - Do you have the        │  ☐ CNIC Copy                │
│     deposit receipt?       │  ☐ Written Notice            │
│                            │                             │
│   User: Yes I have both... │  ─────────────────────────  │
│                            │                             │
│   Agent: Based on your     │  📜 Relevant Law            │
│   situation, here's your   │  Rent Restriction Ordinance │
│   action plan...           │  Section 15, 17             │
│                            │                             │
│                            │  ─────────────────────────  │
│                            │                             │
│                            │  🏢 Office to Visit         │
│                            │  Rent Controller Office     │
│                            │  District Courts Complex    │
│                            │                             │
│                            │  ─────────────────────────  │
│                            │                             │
│   [Type your message...]   │  [📥 Download Action Plan]  │
│                            │                             │
├────────────────────────────┴─────────────────────────────┤
│  ⚠️ Disclaimer: This is general legal information, not   │
│  legal advice. Please consult a licensed advocate.       │
└──────────────────────────────────────────────────────────┘
```

---

## System Prompt (agent/prompts.py)

```
You are CivicGuide AI, a legal rights assistant for Pakistani citizens.

ROLE:
You help users understand their legal rights, required procedures, necessary
documents, and government offices to contact for issues related to:
1. Property and Land Rights
2. Family and Inheritance Rights
3. Business and Financial Rights

RULES:
1. ONLY answer questions within the three domains above.
2. If a question falls outside these domains (criminal law, tax advisory,
   immigration, medical, politics, coding, general knowledge, etc.), politely
   refuse and explain your scope.
3. NEVER provide legal guarantees or claim to replace a lawyer.
4. ALWAYS end substantive responses with: "This is general legal information,
   not legal advice. Please consult a licensed advocate for your specific case."
5. When citing law, always reference the specific Act name and section number.
6. Provide document names in both English and Urdu where possible.
7. Note province-specific differences when relevant (Punjab, Sindh, KPK,
   Balochistan, ICT).
8. Use simple, accessible language. Avoid unnecessary legal jargon.
9. If you don't have enough information to help, use the check_missing_info
   tool to ask clarifying questions BEFORE giving guidance.
10. After providing a complete action plan, offer to generate a downloadable
    checklist PDF.

TOOL USAGE ORDER:
1. First: classify the issue using classify_issue
2. If classified as out-of-scope: refuse politely
3. If in-scope: check for missing information using check_missing_info
4. If information is missing: ask the user (do NOT proceed without it)
5. Once sufficient info gathered: call lookup_procedure for structured steps
6. Then: call retrieve_legal_sections for statute citations
7. Finally: offer generate_checklist for a downloadable PDF

TONE:
- Empathetic and respectful
- Clear and structured
- Never condescending
- Acknowledge the difficulty of legal situations
```

---

## Demo Script (for Hackathon Presentation)

### Demo 1: Property Dispute (Primary Demo)

**User:** "I bought a plot in Karachi 2 years ago but the seller is now saying the sale was invalid and threatening to take it back. I have the sale deed. What can I do?"

**Expected Agent Behavior:**
1. Classifies as property → sale dispute
2. Asks for missing info (registered or unregistered deed? through agent or direct? payment method?)
3. Provides step-by-step procedure
4. Cites Transfer of Property Act Section 54
5. Lists required documents
6. Generates downloadable checklist

### Demo 2: Inheritance Query

**User:** "My father passed away last month. He had a house and some land. I have 2 brothers and 1 sister. How do we divide the property?"

**Expected Agent Behavior:**
1. Classifies as family → inheritance
2. Asks about mother's status, any will, property type
3. Calculates Islamic inheritance shares
4. Explains succession certificate process
5. Cites Muslim Family Laws Ordinance

### Demo 3: Out-of-Scope Refusal

**User:** "Someone stole my phone. What should I do?"

**Expected Agent Response:**
"I understand this is a stressful situation. However, CivicGuide AI currently specializes in three areas: Property & Land Rights, Family & Inheritance Rights, and Business & Financial Rights. Theft falls under criminal law, which is outside my current scope. I'd recommend visiting your nearest police station to file an FIR (First Information Report). For detailed criminal law guidance, please consult a licensed advocate."

---

## Execution Timeline (Hackathon Day)

| Time Block | Task | Deliverable |
|-----------|------|-------------|
| Night Before (3-4 hrs) | Write procedures.json (15 entries), collect statute texts, run ingest.py | Knowledge base ready |
| Hour 0-1 | Set up project structure, install dependencies, test Groq connection | Boilerplate running |
| Hour 1-3 | Build all 5 tools, wire up AgentExecutor | Agent works in terminal |
| Hour 3-5 | Build Streamlit UI (chat + sidebar) | UI functional |
| Hour 5-7 | Integration testing, fix tool-calling edge cases | End-to-end flow working |
| Hour 7-9 | PDF checklist generation, Urdu text support | Download feature working |
| Hour 9-10 | Polish UI, error handling, loading states | Demo-ready |
| Hour 10-11 | Test all 3 demo scenarios, fix bugs | Stable demo |
| Hour 11-12 | Prepare pitch, practice demo | Presentation ready |

---

## Evaluation Criteria (Self-Assessment)

| Criteria | How CivicGuide AI Addresses It |
|----------|-------------------------------|
| Real-world problem | Legal access gap affects millions of Pakistanis |
| Technical depth | LangChain agent + RAG + structured knowledge hybrid |
| Agentic behavior | Multi-turn reasoning, missing info detection, tool orchestration |
| Innovation | Bilingual (EN/UR) document names, province-specific guidance, downloadable action plans |
| Feasibility | Scoped to 3 domains, structured JSON ensures reliability |
| Demo quality | Three prepared scenarios showing different capabilities |

---

## Environment Variables (.env)

```
GROQ_API_KEY=gsk_...
```

---

## Quick Start

```bash
# Clone and setup
cd civicguide-ai
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Ingest statute documents into ChromaDB
python ingestion/ingest.py

# Run the app
streamlit run app.py
```