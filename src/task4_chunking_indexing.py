"""Task 4 — Load, chunk, embed and index the three-source drug-law corpus."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from .contracts import validate_document


load_dotenv()

ROOT = Path(__file__).parent.parent
STANDARDIZED_DIR = ROOT / "data" / "standardized"
CHROMA_DIR = ROOT / "chroma_db"

# Legal provisions and news paragraphs remain readable while overlap preserves
# conditions split at boundaries.  The values are recorded for A/B evaluation.
CHUNK_SIZE = 850
CHUNK_OVERLAP = 120
CHUNKING_METHOD = "markdown_recursive"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
EMBEDDING_DIM = 384
COLLECTION_NAME = "drug_news_law_documents"


@lru_cache(maxsize=1)
def _embedding_model():
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    from sentence_transformers import SentenceTransformer
    from transformers.utils import logging as transformers_logging

    transformers_logging.set_verbosity_error()
    return SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed Vietnamese text with one shared, normalized multilingual model."""
    if not texts:
        return []
    vectors = _embedding_model().encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 64,
    )
    return vectors.tolist()


@lru_cache(maxsize=1)
def get_collection():
    """Open the persistent Chroma collection configured for cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _parse_markdown(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8").strip()
    metadata: dict = {}
    content = raw
    if raw.startswith("---\n") and "\n---\n" in raw[4:]:
        header, content = raw[4:].split("\n---\n", 1)
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            try:
                metadata[key.strip()] = json.loads(value.strip())
            except json.JSONDecodeError:
                metadata[key.strip()] = value.strip()
    return metadata, content.strip()


def load_documents() -> list[dict]:
    """Read normalized Markdown while preserving provenance metadata."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        frontmatter, content = _parse_markdown(path)
        relative = path.relative_to(STANDARDIZED_DIR).as_posix()
        doc_type = str(frontmatter.get("doc_type") or path.parent.name.rstrip("s"))
        metadata = {
            "source": str(frontmatter.get("source") or path.name),
            "title": str(frontmatter.get("title") or path.stem),
            "doc_type": doc_type,
            "url": frontmatter.get("url"),
            "knowledge_base": str(frontmatter.get("knowledge_base") or path.parent.name),
            "source_tier": str(frontmatter.get("source_tier") or "official_legal_source"),
            "claim_status": str(frontmatter.get("claim_status") or "not_applicable"),
        }
        document = {"id": relative, "content": content, "metadata": metadata}
        validate_document(document)
        documents.append(document)
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Split on Markdown/legal boundaries before falling back to characters."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## Điều ", "\n## Trang ", "\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
        keep_separator=True,
    )
    chunks = []
    for document in documents:
        for index, text in enumerate(splitter.split_text(document["content"])):
            cleaned = text.strip()
            if not cleaned:
                continue
            chunk = {
                "id": f"{document['id']}::chunk-{index:04d}",
                "content": cleaned,
                "metadata": {**document["metadata"], "chunk_index": index},
            }
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Return new chunk dictionaries containing normalized embeddings."""
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count does not match chunk count")
    return [{**chunk, "embedding": vector} for chunk, vector in zip(chunks, vectors)]


def _chroma_metadata(metadata: dict) -> dict:
    return {key: ("" if value is None else value) for key, value in metadata.items()}


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Idempotently upsert chunks into Chroma."""
    if not chunks:
        return
    collection = get_collection()
    target_ids = {chunk["id"] for chunk in chunks}
    existing_ids = set(collection.get(include=[]).get("ids", []))
    stale_ids = sorted(existing_ids - target_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)
    batch_size = 256
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in batch],
        )


def run_pipeline() -> None:
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks from {len(documents)} documents")


if __name__ == "__main__":
    run_pipeline()
