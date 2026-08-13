import asyncio
from functools import lru_cache

from langsmith import traceable
from openai import AsyncOpenAI

from app.core.config import get_settings

_settings = get_settings()
_client = AsyncOpenAI(api_key=_settings.openai_api_key)


@lru_cache
def _local_model():
    # Imported lazily so the openai-only path never pays sentence-transformers'
    # torch import cost, and the model itself loads once per process.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_settings.embedding_model)


async def _embed_local(texts: list[str]) -> list[list[float]]:
    model = _local_model()
    # SentenceTransformer.encode is a blocking, CPU-bound call - push it off
    # the event loop instead of stalling every other in-flight request.
    embeddings = await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)
    return embeddings.tolist()


async def _embed_openai(texts: list[str]) -> list[list[float]]:
    response = await _client.embeddings.create(model=_settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]


@traceable(run_type="embedding", name="embed_texts")
async def embed_texts(texts: list[str]) -> list[list[float]]:
    if _settings.embedding_provider == "local":
        return await _embed_local(texts)
    if _settings.embedding_provider == "openai":
        return await _embed_openai(texts)
    raise NotImplementedError(f"Unsupported embedding provider: {_settings.embedding_provider}")
