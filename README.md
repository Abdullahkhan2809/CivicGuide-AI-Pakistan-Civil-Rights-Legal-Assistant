# CivicGuide AI - Pakistani Civil Rights Legal Assistant

CivicGuide AI is a Streamlit legal information assistant for Pakistani civil-rights issues across property, family, inheritance, and business matters. It uses the PDFs in `knowledge/statute` as a local statute corpus, retrieves relevant excerpts, and turns a user's situation into a practical checklist and action plan.

## Features

- Dark split-pane chat UI matching the supplied CivicGuide AI mockup.
- Local statute retrieval from `knowledge/statute/*.pdf`.
- Groq-powered responses when `GROQ_API_KEY` is configured.
- Offline fallback guidance when no API key is available.
- Deterministic procedure lookup from `knowledge/procedures/{category}.json`.
- PDF to TXT to ChromaDB ingestion at `vector_db/chroma_db`.
- Dynamic case summary with required documents, relevant laws, and office guidance.
- Downloadable PDF action plan.

## Run

```powershell
python -m pip install -r requirement.txt
python rag/ingest.py
streamlit run app.py
```

Optional `.env`:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
```

Procedure JSON files live in `knowledge/procedures/`. Generated text files live in `knowledge/texts/`, and the vector database is persisted in `vector_db/chroma_db/`.
