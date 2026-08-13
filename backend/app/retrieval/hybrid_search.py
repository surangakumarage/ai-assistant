import asyncio
from dataclasses import dataclass

from langsmith import traceable

from app.guardrails.access_control import filter_by_access_level
from app.retrieval.embeddings import embed_texts
from app.retrieval.pinecone_client import get_pinecone_index
from app.retrieval.sparse_search import sparse_search


@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    access_level: str
    dense_score: float
    sparse_score: float
    hybrid_score: float


def _normalize(scores: list[float]) -> list[float]:
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi == lo:
        return [1.0 for _ in scores]
    return [(score - lo) / (hi - lo) for score in scores]


@traceable(run_type="retriever", name="hybrid_search")
async def hybrid_search(
    query: str,
    department: str | None = None,
    top_k: int = 5,
    dense_weight: float = 0.5,
    max_access_level: str | None = None,
) -> list[RetrievedChunk]:
    [query_embedding] = await embed_texts([query])
    index = get_pinecone_index()
    candidate_pool = top_k * 4

    dense_results, sparse_results = await asyncio.gather(
        asyncio.to_thread(
            lambda: index.query(
                vector=query_embedding,
                top_k=candidate_pool,
                namespace=department,
                include_metadata=True,
            )
        ),
        asyncio.to_thread(sparse_search, query, department, candidate_pool),
    )

    dense_matches = dense_results.get("matches", [])
    dense_by_id = {match["id"]: match for match in dense_matches}
    dense_scores_norm = dict(
        zip([match["id"] for match in dense_matches], _normalize([match["score"] for match in dense_matches]))
    )

    sparse_by_id = {chunk.chunk_id: chunk for chunk, _ in sparse_results}
    sparse_scores_norm = dict(
        zip([chunk.chunk_id for chunk, _ in sparse_results], _normalize([score for _, score in sparse_results]))
    )

    merged: list[RetrievedChunk] = []
    for chunk_id in dense_by_id.keys() | sparse_by_id.keys():
        dense_score = dense_scores_norm.get(chunk_id, 0.0)
        sparse_score = sparse_scores_norm.get(chunk_id, 0.0)

        if chunk_id in dense_by_id:
            meta = dense_by_id[chunk_id]["metadata"]
            doc_id, title, text = meta["doc_id"], meta["title"], meta["text"]
            access_level = meta.get("access_level", "internal")
        else:
            sparse_chunk = sparse_by_id[chunk_id]
            doc_id, title, text = sparse_chunk.doc_id, sparse_chunk.title, sparse_chunk.text
            access_level = sparse_chunk.access_level

        merged.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                title=title,
                text=text,
                access_level=access_level,
                dense_score=dense_score,
                sparse_score=sparse_score,
                hybrid_score=dense_weight * dense_score + (1 - dense_weight) * sparse_score,
            )
        )

    # Guardrail: drop anything above the caller's access ceiling before
    # ranking/truncation, so an inaccessible chunk can never occupy a top-k
    # slot even if it would otherwise have scored highly.
    if max_access_level is not None:
        merged = filter_by_access_level(merged, max_access_level)

    merged.sort(key=lambda chunk: chunk.hybrid_score, reverse=True)
    return merged[:top_k]
