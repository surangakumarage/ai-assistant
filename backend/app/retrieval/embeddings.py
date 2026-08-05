from openai import AsyncOpenAI

from app.core.config import get_settings

_settings = get_settings()
_client = AsyncOpenAI(api_key=_settings.openai_api_key)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if _settings.embedding_provider != "openai":
        raise NotImplementedError(f"Unsupported embedding provider: {_settings.embedding_provider}")
    response = await _client.embeddings.create(model=_settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]
