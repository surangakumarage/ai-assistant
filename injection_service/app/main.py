from fastapi import FastAPI
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from app.core.config import get_settings
from app.retrieval.embeddings import embed_texts
from app.retrieval.pinecone_client import get_pinecone_index

app = FastAPI(title="Injection Test Service")

SYSTEM_PROMPT = "You are an enterprise knowledge assistant. Answer the user's question using the provided context."


class QueryRequest(BaseModel):
    question: str
    department: str | None = None
    top_k: int = 5


class Source(BaseModel):
    chunk_id: str
    doc_id: str
    title: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    settings = get_settings()

    [query_embedding] = await embed_texts([request.question])
    index = get_pinecone_index()
    results = index.query(
        vector=query_embedding,
        top_k=request.top_k,
        namespace=request.department,
        include_metadata=True,
    )

    matches = results.get("matches", [])
    context = "\n\n".join(match["metadata"]["text"] for match in matches)

    llm = ChatAnthropic(model=settings.llm_model, api_key=settings.anthropic_api_key)
    prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context}\n\nQuestion: {request.question}"
    response = await llm.ainvoke(prompt)

    return QueryResponse(
        answer=response.content,
        sources=[
            Source(
                chunk_id=match["id"],
                doc_id=match["metadata"]["doc_id"],
                title=match["metadata"]["title"],
            )
            for match in matches
        ],
    )
