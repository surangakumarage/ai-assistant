from langchain_core.tools import tool

from app.guardrails.input_validation import clamp, truncate
from app.retrieval.hybrid_search import hybrid_search

MAX_QUERY_LENGTH = 500
MAX_TOP_K = 20


@tool
async def knowledge_search(query: str, department: str | None = None, top_k: int = 5) -> list[dict]:
    """Search indexed internal documents (hybrid dense + BM25 search) for text
    relevant to `query`, optionally scoped to a department namespace. Returns
    matching chunks with doc_id, title, and text. Use this to look something
    up beyond what's already in the provided source material."""
    query = truncate(query, MAX_QUERY_LENGTH)
    top_k = clamp(top_k, 1, MAX_TOP_K)
    results = await hybrid_search(query=query, department=department, top_k=top_k)
    return [
        {
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "title": chunk.title,
            "text": chunk.text,
            "score": chunk.hybrid_score,
        }
        for chunk in results
    ]
