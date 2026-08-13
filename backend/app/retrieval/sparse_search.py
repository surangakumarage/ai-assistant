from dataclasses import dataclass
from functools import lru_cache

from langsmith import traceable
from rank_bm25 import BM25Okapi

from app.retrieval.chunking import chunk_document
from app.retrieval.loader import load_documents


@dataclass
class SparseChunk:
    chunk_id: str
    doc_id: str
    title: str
    document_type: str
    department: str
    access_level: str
    created_date: str
    chunk_index: int
    text: str


@dataclass
class BM25Corpus:
    chunks: list[SparseChunk]
    index: BM25Okapi


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


@lru_cache
def get_bm25_corpus() -> BM25Corpus:
    # Pinecone has no efficient "list every vector" API, so the sparse index is
    # built by re-running the same load+chunk steps as ingest.py rather than
    # reading the corpus back out of the vector DB. Cached for the process
    # lifetime since docs/manifest.json only changes on re-ingest.
    chunks: list[SparseChunk] = []
    for doc in load_documents():
        for chunk in chunk_document(doc.doc_id, doc.text):
            chunks.append(
                SparseChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc.doc_id,
                    title=doc.title,
                    document_type=doc.document_type,
                    department=doc.department,
                    access_level=doc.access_level,
                    created_date=doc.created_date,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                )
            )
    tokenized_corpus = [_tokenize(chunk.text) for chunk in chunks]
    return BM25Corpus(chunks=chunks, index=BM25Okapi(tokenized_corpus))


@traceable(run_type="retriever", name="bm25_sparse_search")
def sparse_search(
    query: str, department: str | None = None, top_k: int = 10
) -> list[tuple[SparseChunk, float]]:
    corpus = get_bm25_corpus()
    scores = corpus.index.get_scores(_tokenize(query))
    ranked = sorted(zip(corpus.chunks, scores), key=lambda pair: pair[1], reverse=True)
    if department:
        ranked = [pair for pair in ranked if pair[0].department == department]
    return ranked[:top_k]
