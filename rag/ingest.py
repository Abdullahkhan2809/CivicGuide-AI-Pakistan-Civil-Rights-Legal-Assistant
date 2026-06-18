from __future__ import annotations

import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import CACHE_DIR, KNOWLEDGE_DIR, PDF_CACHE_PATH, TEXT_DIR, TEXT_JSON_DIR, VECTOR_DB_DIR


CHUNK_SIZE = 2400
CHUNK_OVERLAP = 240
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass(frozen=True)
class StatuteChunk:
    source: str
    page: int
    text: str


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> Iterable[str]:
    if not text:
        return
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            yield chunk
        if end == len(text):
            break
        start = max(0, end - overlap)


def extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
        if text:
            pages.append((page_number, text))
    return pages


def write_pdf_texts() -> list[Path]:
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    text_paths: list[Path] = []
    for pdf_path in sorted(KNOWLEDGE_DIR.glob("*.pdf")):
        output_path = TEXT_DIR / f"{pdf_path.stem}.txt"
        try:
            pages = extract_pdf_pages(pdf_path)
            body = "\n\n".join(
                f"--- Page {page_number} ---\n{text}"
                for page_number, text in pages
            )
        except Exception as exc:
            body = f"Unable to extract {pdf_path.name}: {exc}"
        output_path.write_text(body, encoding="utf-8")
        text_paths.append(output_path)
    return text_paths


def parse_text_pages(text: str) -> list[dict[str, str | int]]:
    matches = list(re.finditer(r"--- Page (\d+) ---\s*", text))
    if not matches:
        cleaned = _clean_text(text)
        return [{"page": 1, "text": cleaned}] if cleaned else []

    pages: list[dict[str, str | int]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        cleaned = _clean_text(text[start:end])
        if cleaned:
            pages.append({"page": int(match.group(1)), "text": cleaned})
    return pages


def write_text_jsons() -> list[Path]:
    TEXT_JSON_DIR.mkdir(parents=True, exist_ok=True)
    json_paths: list[Path] = []
    index: list[dict[str, object]] = []

    for text_path in sorted(TEXT_DIR.glob("*.txt")):
        raw_text = text_path.read_text(encoding="utf-8", errors="replace")
        pages = parse_text_pages(raw_text)
        law = {
            "source": f"{text_path.stem}.pdf",
            "text_file": text_path.name,
            "title": text_path.stem,
            "page_count": len(pages),
            "pages": pages,
        }
        output_path = TEXT_JSON_DIR / f"{text_path.stem}.json"
        output_path.write_text(json.dumps(law, ensure_ascii=False, indent=2), encoding="utf-8")
        json_paths.append(output_path)
        index.append(
            {
                "source": law["source"],
                "title": law["title"],
                "json_file": output_path.name,
                "text_file": text_path.name,
                "page_count": len(pages),
            }
        )

    (TEXT_JSON_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return json_paths


def extract_pdf_chunks(pdf_path: Path) -> list[StatuteChunk]:
    chunks: list[StatuteChunk] = []
    for page_number, page_text in extract_pdf_pages(pdf_path):
        for chunk in _chunk_text(page_text):
            chunks.append(StatuteChunk(source=pdf_path.name, page=page_number, text=chunk))
    return chunks


def build_statute_cache(force: bool = False) -> list[StatuteChunk]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if PDF_CACHE_PATH.exists() and not force:
        return load_statute_cache()

    chunks: list[StatuteChunk] = []
    for pdf_path in sorted(KNOWLEDGE_DIR.glob("*.pdf")):
        try:
            chunks.extend(extract_pdf_chunks(pdf_path))
        except Exception as exc:
            chunks.append(
                StatuteChunk(
                    source=pdf_path.name,
                    page=1,
                    text=f"Unable to extract this PDF automatically: {exc}",
                )
            )

    PDF_CACHE_PATH.write_text(
        json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=True, indent=2),
        encoding="utf-8",
    )
    return chunks


def load_statute_cache() -> list[StatuteChunk]:
    if not PDF_CACHE_PATH.exists():
        return build_statute_cache(force=True)
    raw = json.loads(PDF_CACHE_PATH.read_text(encoding="utf-8"))
    return [StatuteChunk(**item) for item in raw]


def load_text_json_chunks() -> list[StatuteChunk]:
    if not TEXT_JSON_DIR.exists() or not any(TEXT_JSON_DIR.glob("*.json")):
        if TEXT_DIR.exists():
            write_text_jsons()
        else:
            return []

    chunks: list[StatuteChunk] = []
    for json_path in sorted(TEXT_JSON_DIR.glob("*.json")):
        if json_path.name == "index.json":
            continue
        law = json.loads(json_path.read_text(encoding="utf-8"))
        source = str(law.get("source") or f"{json_path.stem}.pdf")
        for page in law.get("pages", []):
            page_number = int(page.get("page", 1))
            for chunk in _chunk_text(str(page.get("text", ""))):
                chunks.append(StatuteChunk(source=source, page=page_number, text=chunk))
    return chunks


def build_chroma_db(chunks: list[StatuteChunk], force: bool = True) -> int:
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    if force and VECTOR_DB_DIR.exists():
        shutil.rmtree(VECTOR_DB_DIR)
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading embedding model: {EMBEDDING_MODEL}", flush=True)
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    print(f"Embedding {len(chunks)} chunks into ChromaDB...", flush=True)
    store = Chroma(
        collection_name="civicguide_statutes",
        embedding_function=embeddings,
        persist_directory=str(VECTOR_DB_DIR),
    )

    texts = [chunk.text for chunk in chunks]
    metadatas = [
        {"source": chunk.source, "page": chunk.page}
        for chunk in chunks
    ]
    ids = [
        f"{Path(chunk.source).stem}-{index}-{chunk.page}"
        for index, chunk in enumerate(chunks)
    ]

    batch_size = 128
    for start in range(0, len(texts), batch_size):
        end = start + batch_size
        print(f"Adding chunks {start + 1}-{min(end, len(texts))} of {len(texts)}", flush=True)
        store.add_texts(
            texts=texts[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end],
        )
    if hasattr(store, "persist"):
        store.persist()
    return len(texts)


def run_ingestion() -> None:
    print("Extracting PDF text files...", flush=True)
    text_paths = write_pdf_texts()
    print("Writing structured JSON law files...", flush=True)
    json_paths = write_text_jsons()
    print("Building statute chunk cache...", flush=True)
    chunks = build_statute_cache(force=True)
    vector_count = build_chroma_db(chunks, force=True)
    print(f"Wrote {len(text_paths)} text files to {TEXT_DIR}")
    print(f"Wrote {len(json_paths)} JSON law files to {TEXT_JSON_DIR}")
    print(f"Built {len(chunks)} chunks from {KNOWLEDGE_DIR}")
    print(f"Persisted {vector_count} vectors to {VECTOR_DB_DIR}")


if __name__ == "__main__":
    run_ingestion()
